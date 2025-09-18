# Servicio de alertas

El servicio `alerts` expone un endpoint HTTP para solicitar el envío de mensajes a través de los canales configurados (Telegram y correo electrónico). A continuación se describen los pasos para configurar los secretos requeridos y ejecutar el contenedor en Docker Compose.

## Configuración de secretos

El servicio obtiene las credenciales sensibles (tokens y contraseñas) desde Azure Key Vault o directamente desde las variables de entorno definidas en `.env`.

### Azure Key Vault

1. Cree los secretos en su Azure Key Vault con los valores reales.
2. Registre el nombre exacto de cada secreto en el archivo `.env` utilizando las siguientes variables:

| Variable | Descripción |
| --- | --- |
| `ALERTS_TELEGRAM_TOKEN_SECRET_NAME` | Nombre del secreto que contiene el token del bot de Telegram. |
| `ALERTS_SMTP_HOST` | Hostname o IP del servidor SMTP. |
| `ALERTS_SMTP_PORT` | Puerto del servidor SMTP (por ejemplo, `587`). |
| `ALERTS_SMTP_USERNAME_SECRET_NAME` | Nombre del secreto con el usuario de autenticación SMTP. |
| `ALERTS_SMTP_PASSWORD_SECRET_NAME` | Nombre del secreto con la contraseña del usuario SMTP. |
| `ALERTS_SMTP_USE_TLS` | Indica si debe usarse TLS (por ejemplo, `true` o `false`). |
| `ALERTS_EMAIL_FROM_SECRET_NAME` | Nombre del secreto que contiene la dirección de correo que aparecerá como remitente. |

Cuando el backend de secretos de Azure está configurado (ver `init.py`), el servicio resolverá automáticamente los nombres y obtendrá los valores.

### Desarrollo local (.env)

Para ejecutar el servicio sin Azure Key Vault, puede definir los valores directamente en el archivo `.env` del proyecto:

```dotenv
ALERTS_TELEGRAM_TOKEN_SECRET_NAME="<token_del_bot_de_telegram>"
ALERTS_SMTP_HOST="smtp.example.com"
ALERTS_SMTP_PORT="587"
ALERTS_SMTP_USERNAME_SECRET_NAME="usuario@example.com"
ALERTS_SMTP_PASSWORD_SECRET_NAME="contraseña-super-secreta"
ALERTS_SMTP_USE_TLS="true"
ALERTS_EMAIL_FROM_SECRET_NAME="alerts@example.com"
```

> **Nota:** aunque las variables terminan en `_SECRET_NAME`, durante el desarrollo local puede almacenar el valor real directamente para simplificar las pruebas.

## Formato del request `POST /alerts`

El endpoint acepta peticiones `POST` con cuerpo JSON utilizando el siguiente esquema:

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `subject` | `string` | No | Título opcional que se utilizará como asunto del correo electrónico. |
| `body` | `string` | Sí | Contenido del mensaje en texto plano. |
| `targets.telegram` | `array[string]` | No | Lista de `chat_id` de Telegram que recibirán el mensaje. |
| `targets.email` | `array[string]` | No | Lista de direcciones de correo electrónico destino. |

Ejemplo de petición:

```bash
curl -X POST http://localhost:8500/alerts \
  -H "Content-Type: application/json" \
  -d '{
        "subject": "Ejecución completada",
        "body": "El pipeline finalizó correctamente.",
        "targets": {
          "telegram": ["123456789"],
          "email": ["ops@example.com"]
        }
      }'
```

La respuesta confirma la recepción del mensaje:

```json
{
  "status": "queued",
  "subject": "Ejecución completada",
  "recipients": {
    "telegram": ["123456789"],
    "email": ["ops@example.com"]
  }
}
```

## Ejecución en Docker Compose

Para construir y levantar únicamente el servicio de alertas ejecute:

```bash
docker compose up alerts
```

El servicio queda disponible en `http://localhost:8500` cuando se ejecuta el contenedor localmente. Si se despliega junto al proxy Nginx, la ruta `/alerts` redirigirá las solicitudes externas hacia este backend.
