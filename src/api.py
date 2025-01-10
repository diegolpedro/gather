#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Diego L. Pedro <diegolpedro@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Summary:
# API implementa la api de acceso a los datos de la base
import csv
import tempfile
import uvicorn
from datetime import date, timezone, timedelta
from common.tools import get_azure_secret_client, get_azure_blob_client
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, insert, MetaData, select, Table, func
from sqlalchemy.orm import sessionmaker, Session


# Azure Blob Secrets
azs_client = get_azure_secret_client()
br_dni = azs_client.get_secret('br-dni').value

# Configuración de la conexión a la base de datos
db = 'market_db'
db_user = azs_client.get_secret('db-user').value
db_pass = azs_client.get_secret('db-pass').value
# Replace with your credentials
db_url = "postgresql://%s:%s@postgres:5432/%s" % (db_user, db_pass, db)
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Metadata para SQLAlchemy ORM
metadata = MetaData()
CotizacionActual = Table('cotizacion_actual', metadata, autoload_with=engine)

# FastAPI app
app = FastAPI(debug=True)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas de la API
@app.get("/cotizaciones", summary="Obtener todas las cotizaciones del día", response_model=list)
def get_cotizaciones_del_dia(
    date_filter: date = Query(default=date.today(), description="Fecha a filtrar"),
    db: Session = Depends(get_db)
):
    """
    Retorna todas las cotizaciones del día indicado.
    """
    data = []
    stmt = select(CotizacionActual).where(
        func.date(CotizacionActual.c.datetime) == date_filter)
    results = db.execute(stmt)

    for row in results.all():
        data.append(dict(row._mapping))

    if not results:
        raise HTTPException(
            status_code=404, detail="No se encontraron cotizaciones para el día especificado.")
    return data


@app.get("/cotizaciones/download", summary="Descargar cotizaciones del día en CSV")
def download_cotizaciones_del_dia(
    date_filter: date = Query(default=date.today(), description="Fecha a filtrar"),
    db: Session = Depends(get_db)
):
    """
    Genera un archivo CSV con todas las cotizaciones del día indicado y lo devuelve para su descarga.
    """
    # Obtener los datos
    data = []
    stmt = select(CotizacionActual).where(
        func.date(CotizacionActual.c.datetime) == date_filter)
    results = db.execute(stmt)

    for row in results.all():
        data.append(dict(row._mapping))

    if not data:
        raise HTTPException(
            status_code=404, detail="No se encontraron cotizaciones para el día especificado.")

    # Crear un archivo CSV temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='', encoding='utf-8') as tmp:
        csv_writer = csv.DictWriter(tmp, fieldnames=data[0].keys())
        csv_writer.writeheader()  # Escribir encabezado
        csv_writer.writerows(data)  # Escribir filas
        tmp_path = tmp.name

    # Devolver el archivo para descarga
    return FileResponse(tmp_path, media_type='text/csv', filename=f"cotizaciones_{date_filter}.csv")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
