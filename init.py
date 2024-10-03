#!/usr/bin/env python
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
# Script de inicialización del stack Apache Airflow.
#
import base64
import os
import secrets
from cryptography.fernet import Fernet


user_uid = os.getuid()				# Obtener el UID del usuario actual
fernet_key = Fernet.generate_key()  # Generar la clave Fernet
# Generar 32 bytes aleatorios (256 bits)
api_secret_key = secrets.token_bytes(32)
web_secret_key = secrets.token_bytes(32)
# Codificar en Base64 para obtener una cadena legible
api_secret_key_base64 = base64.b64encode(api_secret_key).decode()
web_secret_key_base64 = base64.b64encode(web_secret_key).decode()

# Definir las variables y sus valores por defecto
variables = {
    "PG_USER": "developer",
    "PG_PASS": "developer123",
    "PG_DB": "gather_db",
    "AF_DB": "airflow_db",
    "AF_USER": "airflow_user",
    "AF_PASS": "airflow_pass",
    "AIRFLOW_UID": f"{user_uid}",
    "AIRFLOW_GID": "0",
    "AIRFLOW_PROJ_DIR": "./airflow/persist",
    "AIRFLOW__CELERY__BROKER_URL": "redis://:@redis:6379/0",
    "AIRFLOW__CELERY__FLOWER_URL_PREFIX": "flower",
    "AIRFLOW__CORE__EXECUTOR": 'CeleryExecutor',
    "AIRFLOW__CORE__FERNET_KEY": f"{fernet_key.decode()}",
    "AIRFLOW__CORE__INTERNAL_API_SECRET_KEY": f"{api_secret_key_base64}",
    "AIRFLOW__CORE__LOAD_EXAMPLES": 'true',
    "AIRFLOW__SECRETS__BACKEND": '',
    "AIRFLOW__WEBSERVER__EXPOSE_CONFIG": 'true',
    "AIRFLOW__WEBSERVER__ENABLE_PROXY_FIX": 'true',
    "AIRFLOW__WEBSERVER__SECRET_KEY": f"{web_secret_key_base64}",
    "_AIRFLOW_DB_MIGRATE": 'true',
    "_AIRFLOW_WWW_USER_CREATE": 'true'
}

# Agregamos las variables que dependen de otras variables, usando .format() para sustituir valores
variables.update({
    "_AIRFLOW_WWW_USER_USERNAME": '{AF_USER}'.format(**variables),
    "_AIRFLOW_WWW_USER_PASSWORD": '{AF_PASS}'.format(**variables),
    "AIRFLOW__CELERY__RESULT_BACKEND": 'db+postgresql://{AF_USER}:{AF_PASS}@postgres/{AF_DB}'.format(**variables),
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": 'postgresql+psycopg2://{AF_USER}:{AF_PASS}@postgres/{AF_DB}'.format(**variables)
})

# Init SQL para Airflow
postgres_path = "postgres/init.sql"
sql = """
    CREATE USER {AF_USER} WITH PASSWORD '{AF_PASS}';
    CREATE DATABASE {AF_DB} WITH OWNER {AF_USER};
    GRANT ALL PRIVILEGES ON DATABASE {AF_DB} TO {AF_USER};
    GRANT ALL ON SCHEMA public TO {AF_USER};""".format(**variables)

# Función para preguntar si el usuario quiere usar el valor por defecto o ingresar uno


def ask_user(var_name, default_value):
    user_input = input(f"'{var_name}'\n (defecto: '{default_value}'): ")
    return user_input if user_input else default_value

# Pedir los datos de Azure si es necesario


def ask_azure_backend_details():
    print("\nConfiguración de Azure Key Vault Backend detectada.")

    vault_url = input("Ingrese el 'vault_url' de Azure: ")
    tenant_id = input("Ingrese el 'tenant_id' de Azure: ")
    client_id = input("Ingrese el 'client_id' de Azure: ")
    client_secret = input("Ingrese el 'client_secret' de Azure: ")

    # Dejar los prefijos como valores por defecto
    kwargs = {
        "connections_prefix": "af-conns",
        "variables_prefix": "af-vars",
        "vault_url": vault_url,
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_secret": client_secret
    }
    return kwargs


print("Script de configuracion inicial: ")

# Crear el archivo .env y escribir las variables
with open(".env", "w") as env_file:
    for var_name, default_value in variables.items():

        value = ask_user(var_name, default_value)
        env_file.write(f"{var_name}={value}\n")
        print(f"-> {value}\n")

        # Verificar si el backend de Azure está presente
        if "AzureKeyVaultBackend" in value:
            azure_kwargs = ask_azure_backend_details()
            # Serializar los valores de Azure y escribir en el archivo
            azure_kwargs_str = str(azure_kwargs).replace(
                "'", '"')  # Formato JSON válido
            env_file.write(f"AIRFLOW__SECRETS__BACKEND_KWARGS={azure_kwargs_str}\n")
            print(f"AIRFLOW__SECRETS__BACKEND_KWARGS configurada con los valores de Azure.\n")
        # else:
        #     env_file.write(f"AIRFLOW__SECRETS__BACKEND_KWARGS=\n")
        #     print(f"AIRFLOW__SECRETS__BACKEND_KWARGS configurada sin valores.")


with open(postgres_path, "w") as sql_file:
    sql_file.write(sql)

print("El archivo '.env' ha sido creado exitosamente.")
