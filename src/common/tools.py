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
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import json
import logging
import os
import requests
import time

logger = logging.getLogger(__name__)


#  AZURE
# =======
# Azure secret client
def get_azure_secret_client():

    # Datos de autenticacion
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    vault_url = os.getenv("AZURE_VAULT_URL")

    # Autenticación usando Client ID, Client Secret y Tenant ID
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    client = SecretClient(vault_url=vault_url, credential=credential)
    return client

# Azure blob client
def get_azure_blob_client(container_name, blob_name):

    # Azure Clob Secrets
    azs_client = get_azure_secret_client()
    account_name = azs_client.get_secret('blob-account-name').value
    account_key = azs_client.get_secret('blob-account-key').value

    # Create a BlobServiceClient for Azure Blob Service
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(
        connection_string)

    # Create a container if it doesn't exist
    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.create_container()
    except Exception as e:
        logger.info(f'Container existente')

    # Create a blob client for an append blob
    blob_client = container_client.get_blob_client(blob_name)
    try:
        blob_client.get_blob_properties()
        logger.info(f'Blob existente')
    except ResourceNotFoundError:
        blob_client.create_append_blob()
    return blob_client

# Genera horario local con formato adecuado
# utc (int Ej: +3, -3)
def hora_local(utc):                                  
    c_time = time.time() + 3600 * int(utc)            
    c_time_str = time.strftime("%H:%M:%S",            
                               time.localtime(c_time))
    return c_time_str

class HttpPostHandler(logging.Handler):
    """
    Handler personalizado para enviar logs vía POST a un endpoint.
    """
    def __init__(self, url: str, chat_id: str, level=logging.INFO):
        super().__init__(level)
        self.url = url
        self.chat_id = chat_id

    def emit(self, record):
        try:
            log_entry = self.format(record)
            payload = {
                "message": log_entry,
                "telegram": {"chat_id": self.chat_id}
            }
            headers = {"Content-Type": "application/json"}
            requests.post(self.url, data=json.dumps(payload), headers=headers, timeout=5)
        except Exception as e:
            # En caso de error, no queremos romper el flujo del programa
            print(f"Error enviando log a {self.url}: {e}")

class Logger:
    """ Clase Logger que envía logs a archivo, consola y vía POST a un endpoint."""
    def __init__(self, name: str, log_file: str = "app.log", 
                 level: int = logging.INFO, 
                 alert_url: str = "http://172.18.0.3:8500/alerts",
                 chat_id: str = "1384905495"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] (%(name)s): %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # Handler para archivo
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)

            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            # Handler para API
            http_handler = HttpPostHandler(alert_url, chat_id)
            http_handler.setFormatter(formatter)

            # Agregar todos
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.addHandler(http_handler)

    def get_logger(self):
        return self.logger
