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
import logging
import pandas as pd
import time
from datetime import datetime, timezone, timedelta
from common.tools import get_azure_secret_client, get_azure_blob_client, hora_local
from pyhomebroker import HomeBroker
from sqlalchemy import create_engine, insert, MetaData, select, Table
from sqlalchemy.orm import Session

import websocket

tz = -3  # UTC-3

def run_online():

    hb = HomeBroker(int(br_num),
                    on_open=on_open,
                    on_personal_portfolio=on_personal_portfolio,
                    on_securities=on_securities,
                    on_options=on_options,
                    on_repos=on_repos,
                    on_order_book=on_order_book,
                    on_error=on_error,
                    on_close=on_close)

    hb.auth.login(dni=br_dni, user=br_user,
                  password=br_pass, raise_exception=True)

    hb.online.connect()
    hb.online.subscribe_options()

    # Traemos horario de fin de rueda.
    with Session(engine) as session:
        stmt = select(parametro.c.valor).where(parametro.c.nombre == "H_FIN")
        h_fin = session.execute(stmt).scalar()

    # Verificamos que el mercado no este ya cerrado.
    while(hora_local(tz) < h_fin):
        time.sleep(300)

    hb.online.unsubscribe_options()
    hb.online.disconnect()


def on_open(online):

    print('=================== CONNECTION OPENED ====================')


def on_personal_portfolio(online, portfolio_quotes, order_book_quotes):

    print('------------------- Personal Portfolio -------------------')
    print(portfolio_quotes)
    print('------------ Personal Portfolio - Order Book -------------')
    print(order_book_quotes)


def on_securities(online, quotes):

    print('----------------------- Securities -----------------------')
    print(quotes)


def on_options(online, quotes):

    # print('------------------------ Options -------------------------')
    # bid_size, bid, ask, ask_size, last, change, open, high, low, previous_close, turnover, volume, operations, datetime, expiration, strike, kind, underlying_asset

    # TODO: Corregir el hecho de que borre el trigger al encontrar repetidos.
    # Solucion 1 (Elimina el trigger)
    # quotes = quotes.reset_index()
    # quotes.to_sql("options_data", con=engine, if_exists="replace", index=False)

    quotes = quotes.reset_index()
    quotes['datetime'] = pd.to_datetime(quotes['datetime'], errors='coerce')
    quotes = quotes.dropna()    # TODO: Revisar
    # quotes = quotes.dropna(subset=['datetime'])
    quotes['expiration'] = pd.to_datetime(
        quotes['expiration'], errors='coerce')

    for index, row in quotes.iterrows():
        print(row['symbol'], row['bid_size'], row['bid'], row['ask'],
              row['ask_size'], row['last'], row['change'], row['open'],
              row['high'], row['low'], row['previous_close'], int(
                  row['turnover']),
              row['volume'], row['operations'], row['datetime'],
              row['expiration'], row['strike'], row['kind'],
              row['underlying_asset'])
        stmt = insert(options_data).values(symbol=row['symbol'], bid_size=row['bid_size'], bid=row['bid'], ask=row['ask'],
                                           ask_size=row['ask_size'], last=row['last'], change=row['change'], open=row['open'],
                                           high=row['high'], low=row['low'], previous_close=row['previous_close'],
                                           turnover=int(row['turnover']), volume=int(row['volume']), operations=int(row['operations']),
                                           datetime=row['datetime'], expiration=row['expiration'], strike=row['strike'],
                                           kind=row['kind'], underlying_asset=row['underlying_asset'])
        with engine.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()


def on_repos(online, quotes):

    print('------------------------- Repos --------------------------')
    print(quotes)


def on_order_book(online, quotes):

    print('------------------ Order Book (Level 2) ------------------')
    print(quotes)


def on_error(online, exception, connection_lost):

    print('@@@@@@@@@@@@@@@@@@@@@@@@@ Error @@@@@@@@@@@@@@@@@@@@@@@@@@')
    print(online, exception, connection_lost)


def on_close(online):

    print('=================== CONNECTION CLOSED ====================')


if __name__ == '__main__':

    utc_minus_3 = timezone(timedelta(hours=-3))
    hoy = datetime.now(tz=utc_minus_3)

    # Azure Secrets
    azs_client = get_azure_secret_client()
    br_dni = azs_client.get_secret('br-dni').value

    db = 'market_db'
    db_user = azs_client.get_secret('db-user').value
    db_pass = azs_client.get_secret('db-pass').value

    # Cuenta principal - BCCH
    # br_num = 153
    # br_user = azs_client.get_secret('br-user').value
    # br_pass = azs_client.get_secret('br-pass').value

    # Cuenta backup
    br_num = 81
    br_user = azs_client.get_secret('br-user-back').value
    br_pass = azs_client.get_secret('br-pass-back').value

    # Database connection details
    # Conectado a base postgres del mismo stack docker
    db_url = "postgresql://%s:%s@postgres:5432/%s" % (db_user, db_pass, db)
    engine = create_engine(db_url)
    metadata = MetaData()
    options_data = Table('options_data', metadata, autoload_with=engine)
    parametro = Table('parametro', metadata, autoload_with=engine)

    run_online()
