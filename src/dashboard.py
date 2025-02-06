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
# Dashboard permite visualizar datos en tiempo real desde postgres
#
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from sqlalchemy.pool import NullPool
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, text
from dash.dependencies import Input, Output, State
from dash import dcc, html
import dash
from common.tools import get_azure_secret_client, get_azure_blob_client, \
hora_local


# Configuración de la base de datos
# Azure Secrets
azs_client = get_azure_secret_client()

db = 'market_db'
db_user = azs_client.get_secret('db-user').value
db_pass = azs_client.get_secret('db-pass').value

# Database connection details
# Conectado a base postgres del mismo stack docker
db_url = "postgresql://%s:%s@postgres:5432/%s" % (db_user, db_pass, db)
engine = create_engine(db_url, poolclass=NullPool)
metadata = MetaData()

# Definición de las tablas
options_data = Table('options_data', metadata, autoload_with=engine)
securities_data = Table('securities_data', metadata, autoload_with=engine)

# Inicializar la app de Dash
app = dash.Dash(__name__)


# ----------------------
## Layout del dashboard
# ----------------------
app.layout = html.Div([

    # Encabezado con título, iconos y estado
    html.Div([
        # Izquierda: Título
        html.Div("Quants", style={
            'font-size': '26px',
            'font-weight': 'bold'
        }),

        # Centro: Iconos/Imágenes
        html.Div([
            html.Img(src='assets/airflow.png',
                     style={'height': '30px', 'margin': '0 5px'}),
            html.Img(src='assets/plotly.png',
                     style={'height': '30px', 'margin': '0 5px'}),
            html.Img(src='assets/fastapi.png',
                     style={'height': '30px', 'margin': '0 5px'}),
            html.A(html.Img(
                src='https://cdn.cafecito.app/imgs/buttons/button_4.svg',
                style={'height': '30px',
                       'margin': '5px',
                       'margin-left':
                       '50px'}),
                   href='https://cafecito.app/diegolpedro', target='_blank'),

        ], style={
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center'
        }),

        # Derecha: Status
        html.Div([
            html.Div(id='data-count',
                     style={'font-size': '12px', 'margin-right': '10px'}),
            html.Div(id='server-status', style={'font-size': '12px'})
        ], style={
            'display': 'flex',
            'align-items': 'center'
        })
    ], style={
        'padding': '10px',
        'border-bottom': '1px solid #ddd',
        'background-color': '#f9f9f9',
        'display': 'flex',
        'justify-content': 'space-between',
        'align-items': 'center'
    }),

    # Solapas
    dcc.Tabs(id='tabs', value='tab-ggal', children=[
        dcc.Tab(label='GGAL', value='tab-ggal',
                style={'width': '80px', 
                       'height': '20px',
                       'display': 'flex',
                       'flex-direction': 'column',
                       'justify-content': 'center',
                       'align-items': 'center'},
                selected_style={'width': '80px',
                                'height': '20px',
                                'background-color': '#e0e0e0',
                                'justify-content': 'center',
                                'display': 'flex',
                                'flex-direction': 'column',
                                'align-items': 'center'}),
        dcc.Tab(label='Bonos', value='tab-bonos',
                style={'width': '80px', 
                       'height': '20px',
                       'display': 'flex',
                       'flex-direction': 'column',
                       'justify-content': 'center',
                       'align-items': 'center'
                       },
                selected_style={'width': '80px',
                                'height': '20px',
                                'background-color': '#e0e0e0',
                                'justify-content': 'center',
                                'display': 'flex',
                                'flex-direction': 'column',
                                'align-items': 'center'})
    ], style={
        'padding': '0px',
        'margin': '0px',
        'border-bottom': '1px solid #ddd',
        'background-color': '#f9f9f9',
        'display': 'flex',
        'justify-content': 'flex-start',
        'align-items': 'center'
    }),

    # Contenido de las solapas
    html.Div(id='tabs-content'),

    # Intervalo de actualización
    dcc.Interval(id='temporizador', interval=10*1000, n_intervals=0),
    dcc.Store(id='data-previa', data={'options': 0, 'securities': 0})
], style={
    'fontFamily': 'Open Sans'
})


# ----------------------
## Callbacks
# ----------------------

# Callback para actualizar el contenido de las solapas
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def update_tab_content(tab):
    if tab == 'tab-ggal':
        return html.Div([
            html.Div(id='cot-bancos', style={
                'padding': '10px',
                'border-bottom': '1px solid #ddd',
                'background-color': '#f0f0f0',
                'display': 'flex',
                'justify-content': 'space-around'
            }),
            dcc.Graph(id='ggal-chart')
        ])
    elif tab == 'tab-bonos':
        return html.Div([
            html.H3('Bonos - Próximamente disponible')
        ])


# Callback para actualizar la cotización de bancos
@app.callback(
    Output('cot-bancos', 'children'),
    Input('temporizador', 'n_intervals')
)
def upd_cot_bancos(n):
    with engine.connect() as conn:
        query = text("""
            SELECT symbol, last, change, high, low, volume
            FROM cotizacion_actual
            WHERE panel = 'bluechips' AND settlement = '24hs'
            AND symbol IN ('BBAR', 'BMA', 'GGAL', 'SUPV', 'VALO')
            ORDER BY symbol;
        """)
        df = pd.read_sql(query, conn)

    def get_flecha_y_color(change):
        if change > 0:
            return 'green', '↑'
        elif change < 0:
            return 'red', '↓'
        else:
            return 'blue', '→'

    vals = []
    for _, row in df.iterrows():
        color, arrow = get_flecha_y_color(row['change'])
        vals.append(
            html.Div(
                f"{row['symbol']}: {row['last']} ({arrow}{row['change']}%)",
                style={'color': color, 'margin': '5px 0'}))

    return vals


# Callback para actualizar la estadística de descargas y el estado del servidor
@app.callback(
    [Output('data-count', 'children'),
     Output('server-status', 'children'),
     Output('data-previa', 'data')],
    [Input('temporizador', 'n_intervals')],
    [State('data-previa', 'data')]
)
def update_data_count(n, cant_previa):
    with engine.connect() as conn:
        query = text("""
            SELECT 'Opciones descargadas' AS "Titulo", COUNT(1) AS "Cantidad"
            FROM options_data
            WHERE datetime >= CURRENT_DATE AND datetime < CURRENT_DATE + INTERVAL '1 day'
            UNION
            SELECT 'Acciones descargadas' AS "Titulo", COUNT(1) AS "Cantidad"
            FROM securities_data
            WHERE datetime >= CURRENT_DATE AND datetime < CURRENT_DATE + INTERVAL '1 day';
        """)
        df = pd.read_sql(query, conn)

    options_count = df[df['Titulo'] ==
                       'Opciones descargadas']['Cantidad'].values[0]
    securities_count = df[df['Titulo'] ==
                          'Acciones descargadas']['Cantidad'].values[0]

    # Determinar estado del servidor
    if (options_count > cant_previa['options'] or
            securities_count > cant_previa['securities']):
        server_status = html.Span([
            "Online ",
            html.Span(style={'background-color': 'green',
                             'border-radius': '50%',
                             'display': 'inline-block',
                             'width': '10px',
                             'height': '10px'})
        ])
    else:
        server_status = html.Span([
            "Offline ",
            html.Span(style={'background-color': 'red',
                             'border-radius': '50%',
                             'display': 'inline-block',
                             'width': '10px',
                             'height': '10px'})
        ])

    # text_display = " | ".join([f"{row['Titulo']}:
    # {row['Cantidad']}" for _, row in df.iterrows()])
    cantidades = [f"{row['Cantidad']}" for _, row in df.iterrows()]
    text_display = "( " + " | ".join(cantidades) + " )"
    new_counts = {'options': options_count, 'securities': securities_count}

    return text_display, server_status, new_counts


# Callback para actualizar el gráfico de GGAL
@app.callback(
    Output('ggal-chart', 'figure'),
    Input('temporizador', 'n_intervals')
)
def update_chart(n):
    with engine.connect() as conn:
        query = text("""
            SELECT date, last, volume
            FROM cotizacion_diaria
            WHERE settlement = '24hs'
            AND symbol = 'GGAL'
            ORDER BY date;
        """)
        df = pd.read_sql(query, conn)

    # Cálculo de la media de volumen
    df["MA10"] = df["volume"].rolling(window=10).mean()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3])

    # Gráfico de precios
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['last'],
        mode='lines', name='Cotización'), row=1, col=1)

    # Gráfico de volumen
    # fig = go.Figure()
    fig.add_trace(go.Bar(x=df["date"], y=df["volume"],
                         name="Volumen"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA10"], mode="lines",
                             name="Media 10D", line=dict(color="red")),
                  row=2, col=1)

    # Gráfico de volumen
    # fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='Volumen'), row=2, col=1)

    fig.update_layout(title="Cotización diaria de GGAL", height=500)
    return fig


# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
