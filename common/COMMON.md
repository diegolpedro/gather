#### Logger (tools.py)
###### Configuracion Basica / Basic Config
Llamar a logger con el nombre del archivo como parametro y el nivel de logueo. Por defecto el nivel será WARNING y pueden utilizarse DEBUG, INFO, WARNING, ERROR y CRITICAL. [Ver Link](https://docs.python.org/es/3/howto/logging.html) para mas detalles.
```
from common.tools import logger

logger = logger(<log_file>:str)
```
###### Utilizacion / Basic Usage
Llamar a los siguientes metodos segun nivel requerido.
```
logger.debug('message')
logger.info('message')
logger.warning('message')
logger.error('message')
```

#### Azure Secrets: get_azure_secret_client (tools.py)
###### Configuracion Basica / Basic Config
Autenticación Mediante Azure Active Directory (Azure AD) con un Service Principal.
Pasos:
<ol>
<li>Crear un Service Principal en Azure AD.</li>
<li>Asignar permisos al Service Principal en el Key Vault.</li>
<li>Utilizar Azure SDK para autenticarse y obtener los secretos.</li>
<li>Almacenar los siguientes datos en variables de entorno (.env).</li>
</ol>
```
AZURE_CLIENT_ID: ''
AZURE_TENANT_ID: ''
AZURE_CLIENT_SECRET: ''
AZURE_VAULT_URL: ''
```
###### Utilizacion / Basic Usage
Llamar a los siguientes metodos.
```
from tools import get_azure_secret_client

client = get_azure_secret_client()
secret_value = client.get_secret(<secret_name>:str)
```
