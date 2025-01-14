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
# Uphb descarga datos en tiempo real de cotizaciones desde HB
#
# Home Broker API - Market data downloader
# https://github.com/crapher/pyhomebroker.git
#
from sqlalchemy import select, insert
from sqlalchemy.sql.expression import literal
from sqlalchemy import create_engine, insert, MetaData, select, Table, func
from common.tools import get_azure_secret_client, get_azure_blob_client, \
hora_local
import logging


logger = logging.getLogger(__name__)
tz = -3  # UTC-3


if __name__ == '__main__':

    # Azure Secrets
    azs_client = get_azure_secret_client()

    # Database connection details
    # Conectado a base postgres del mismo stack docker
    db = 'market_db'
    db_user = azs_client.get_secret('db-user').value
    db_pass = azs_client.get_secret('db-pass').value
    db_url = "postgresql://%s:%s@postgres:5432/%s" % (db_user, db_pass, db)
    engine = create_engine(db_url)
    metadata = MetaData()

    # Tablas
    cotizacion_actual = Table(
        'cotizacion_actual', metadata, autoload_with=engine)
    cotizacion_diaria = Table(
        'cotizacion_diaria', metadata, autoload_with=engine)

    # Insertar datos de "Securities" en "cotizacion_diaria"
    securities_insert = insert(cotizacion_diaria).from_select(
        [
            cotizacion_diaria.c.symbol,
            cotizacion_diaria.c.settlement,
            cotizacion_diaria.c.last,
            cotizacion_diaria.c.change,
            cotizacion_diaria.c.open,
            cotizacion_diaria.c.high,
            cotizacion_diaria.c.low,
            cotizacion_diaria.c.previous_close,
            cotizacion_diaria.c.turnover,
            cotizacion_diaria.c.volume,
            cotizacion_diaria.c.operations,
            cotizacion_diaria.c.date,
        ],
        select(
            cotizacion_actual.c.symbol,
            cotizacion_actual.c.settlement,
            cotizacion_actual.c.last,
            cotizacion_actual.c.change,
            cotizacion_actual.c.open,
            cotizacion_actual.c.high,
            cotizacion_actual.c.low,
            cotizacion_actual.c.previous_close,
            cotizacion_actual.c.turnover,
            cotizacion_actual.c.volume,
            cotizacion_actual.c.operations,
            func.date(cotizacion_actual.c.datetime).label("date"),
        ).where(
            cotizacion_actual.c.panel == 'bluechips',
            cotizacion_actual.c.last.isnot(None)
        )
    )

    # Ejecutar la consulta para "Securities"
    with engine.connect() as connection:
        connection.execute(securities_insert)

    # Insertar datos de "Options" en "cotizacion_diaria"
    options_insert = insert(cotizacion_diaria).from_select(
        [
            cotizacion_diaria.c.symbol,
            cotizacion_diaria.c.settlement,
            cotizacion_diaria.c.last,
            cotizacion_diaria.c.change,
            cotizacion_diaria.c.open,
            cotizacion_diaria.c.high,
            cotizacion_diaria.c.low,
            cotizacion_diaria.c.previous_close,
            cotizacion_diaria.c.turnover,
            cotizacion_diaria.c.volume,
            cotizacion_diaria.c.operations,
            cotizacion_diaria.c.date,
            cotizacion_diaria.c.expiration,
            cotizacion_diaria.c.strike,
            cotizacion_diaria.c.kind,
            cotizacion_diaria.c.underlying_asset,
        ],
        select(
            cotizacion_actual.c.symbol,
            # func.literal('24hs').label("settlement"),
            # Cambiar func.literal a literal
            literal('24hs').label("settlement"),
            cotizacion_actual.c.last,
            cotizacion_actual.c.change,
            cotizacion_actual.c.open,
            cotizacion_actual.c.high,
            cotizacion_actual.c.low,
            cotizacion_actual.c.previous_close,
            cotizacion_actual.c.turnover,
            cotizacion_actual.c.volume,
            cotizacion_actual.c.operations,
            func.date(cotizacion_actual.c.datetime).label("date"),
            func.date(cotizacion_actual.c.expiration).label("expiration"),
            cotizacion_actual.c.strike,
            cotizacion_actual.c.kind,
            cotizacion_actual.c.underlying_asset,
        ).where(
            cotizacion_actual.c.underlying_asset.isnot(None)
        )
    )

    # Ejecutar la consulta para "Options"
    with engine.connect() as connection:
        connection.execute(options_insert)
