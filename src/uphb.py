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
import os
import pandas as pd
import time
from datetime import datetime, timezone, timedelta
from common.tools import get_azure_secret_client, get_azure_blob_client, hora_local
from pyhomebroker import HomeBroker
from sqlalchemy import create_engine, insert, MetaData, select, Table
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
tz = -3  # UTC-3


def on_open(online):

    logger.info('Connection opened')


def on_personal_portfolio(online, portfolio_quotes, order_book_quotes):

    print('------------------- Personal Portfolio -------------------')
    print(portfolio_quotes)
    print('------------ Personal Portfolio - Order Book -------------')
    print(order_book_quotes)


def on_securities(online, quotes):

    # Tabla: securities_data
    # symbol, settlement, bid_size, bid, ask, ask_size, last, change, open, high, low, previous_close, turnover, volume, operations, datetime, panel
    quotes = quotes.reset_index()
    quotes['datetime'] = pd.to_datetime(quotes['datetime'], errors='coerce')
    quotes = quotes.dropna()

    for index, row in quotes.iterrows():

        # print(row['symbol'], row['settlement'], row['bid_size'], row['bid'],
        #       row['ask'], row['ask_size'], row['last'], row['change'],
        #       row['open'], row['high'], row['low'], row['previous_close'],
        #       int(row['turnover']), row['volume'], row['operations'],
        #       row['datetime'], row['group'])

        stmt = insert(securities_data).values(
            symbol=row['symbol'], bid_size=row['bid_size'], bid=row['bid'], ask=row['ask'],
            ask_size=row['ask_size'], last=row['last'], change=row['change'], open=row['open'],
            high=row['high'], low=row['low'], previous_close=row['previous_close'],
            turnover=int(row['turnover']), volume=int(row['volume']), operations=int(row['operations']),
            datetime=row['datetime'], settlement=row['settlement'], panel=row['group'])

        with engine.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()


def on_options(online, quotes):

    # Tabla: options_data
    # bid_size, bid, ask, ask_size, last, change, open, high, low, previous_close, turnover, volume, operations, datetime, expiration, strike, kind, underlying_asset

    quotes = quotes.reset_index()
    quotes['datetime'] = pd.to_datetime(quotes['datetime'], errors='coerce')
    quotes = quotes.dropna()
    quotes['expiration'] = pd.to_datetime(
        quotes['expiration'], errors='coerce')

    for index, row in quotes.iterrows():

        # print(row['symbol'], row['bid_size'], row['bid'], row['ask'],
        #       row['ask_size'], row['last'], row['change'], row['open'],
        #       row['high'], row['low'], row['previous_close'], int(
        #       row['turnover']), row['volume'], row['operations'],
        #       row['datetime'], row['expiration'], row['strike'],
        #       row['kind'], row['underlying_asset'])

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

    print('--- Repos ---')
    print(quotes)


def on_order_book(online, quotes):

    print('--- Order Book (Level 2) ---')
    print(quotes)


def on_error(online, exception, connection_lost):

    print('@@@ Error @@@')
    logger.error(str(online), str(exception), str(connection_lost))


def on_close(online):

    logger.info('Connection closed')
    engine.dispose()  # Libera las conexiones al cerrar


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

    if down_type == 'bluechips':
        # Bluechips define HomeBroker al panel principal
        hb.online.subscribe_securities('bluechips', '24hs')
        hb.online.subscribe_securities('bluechips', 'spot')
    elif down_type == 'bonds':
        # Bonos y Corporativos (government_bonds, 
        # short_term_government_bonds, corporate_bonds)
        hb.online.subscribe_securities('government_bonds', '24hs')
        hb.online.subscribe_securities('short_term_government_bonds', '24hs')
        hb.online.subscribe_securities('corporate_bonds', '24hs')
    else:
        # Opciones
        hb.online.subscribe_options()

    # Traemos horario de fin de rueda.
    with Session(engine) as session:
        stmt = select(parametro.c.valor).where(parametro.c.nombre == "H_FIN")
        h_fin = session.execute(stmt).scalar()

    # Verificamos que el mercado no este ya cerrado.
    while(hora_local(tz) < h_fin):
        time.sleep(300)

    if down_type == 'bluechips':
        hb.online.unsubscribe_securities('bluechips', 'spot')
        hb.online.unsubscribe_securities('bluechips', '24hs')
    elif down_type == 'bonds':
        hb.online.unsubscribe_securities('government_bonds', '24hs')
        hb.online.unsubscribe_securities('short_term_government_bonds', '24hs')
        hb.online.unsubscribe_securities('corporate_bonds', '24hs')
    else:
        hb.online.unsubscribe_options()

    hb.online.disconnect()


if __name__ == '__main__':

    down_type = os.getenv("TYPE")
    if down_type is None:
        logger.warning(
            "Warn: Falta definir tipo de descarga. Se descargan opciones por defecto.")
        down_type = 'options'

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
    br_num = 81    # TM
    br_user = azs_client.get_secret('br-user-back').value
    br_pass = azs_client.get_secret('br-pass-back').value

    # Database connection details
    # Conectado a base postgres del mismo stack docker
    db_url = "postgresql://%s:%s@postgres:5432/%s" % (db_user, db_pass, db)

    # TEST: Pool pequeño
    # engine = create_engine(db_url,
    #     pool_size=2,  # Máximo de dos conexiónes a la vez
    #     max_overflow=0  # No permite conexiones adicionales
    #     )

    # No mantiene conexiones persistentes
    engine = create_engine(db_url, poolclass=NullPool)

    metadata = MetaData()
    options_data = Table('options_data', metadata, autoload_with=engine)
    securities_data = Table('securities_data', metadata, autoload_with=engine)
    parametro = Table('parametro', metadata, autoload_with=engine)

    run_online()
