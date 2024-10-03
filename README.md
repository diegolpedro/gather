# Gather - Stack Airflow sobre Docker

Todo lo expuesto en el siguiente documento puede encontrarse ampliamente explicado en la siguiente [documentación](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html).

Para comenzar, se asume que tienes familiaridad con Docker y Docker Compose. Si no es así, puedes aprender en la siguiente [página web](https://docs.docker.com/get-started/).

Las siguientes herramientas deben estar instaladas:

- Docker Community Edition (CE)
- Docker Compose v2.14.0 o superior

###### Advertencia

Si no se asigna suficiente memoria, puede provocar que el servidor web se reinicie continuamente. Deberías asignar al menos 4 GB de memoria para el Docker Engine (idealmente 8 GB).

### Componentes

Este stack contiene varios módulos:

- **airflow-scheduler**: El 'scheduler' monitorea las tareas y los DAGs, y dispara las tareas cuando se cumplen sus dependencias.
- **airflow-webserver**: Servidor web disponible en [http://localhost:8080](http://localhost:8080).
- **gather-proxy**: Proxy Nginx para dar salida al exterior.
- **airflow-worker**: Trabajadores que ejecutan tareas entregadas por el 'scheduler'.
- **airflow-triggerer**: El 'triggerer' ejecuta un bucle para tareas postergables.
- **airflow-init**: Servicio de inicialización de Airflow.
- **docker-socket-proxy**: Proxy de socket para utilizar el DockerOperator dentro de Airflow.
- **postgres**: Base de datos.
- **redis**: Manejador de mensajes del 'scheduler' hacia los trabajadores.

Opcionalmente, puedes habilitar Flower añadiendo la opción `--profile flower`, por ejemplo:

```bash
docker compose --profile flower up
```

O especificándolo explícitamente en la línea de comandos:

```bash
docker compose up flower
```

- **flower**: Servidor web para monitorear el entorno. Disponible en [http://localhost:5555](http://localhost:5555).

Más información [aquí](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html).

Algunos directorios de Airflow son compartidos fuera de los contenedores (`${AIRFLOW_PROJ_DIR:-.}:/opt/airflow`):

- `./dags`: donde se colocan los DAGs.
- `./logs`: contienen los logs de las tareas y del 'scheduler'.
- `./config`: permite adicionar 'parsers' de logs personalizados o el `airflow_local_settings.py` para configurar las políticas del clúster.
- `./plugins`: permite adicionar plugins personalizados.

Este stack utiliza la última versión slim de la imagen de Airflow (`apache/airflow:slim-2.10.2`). Para añadir bibliotecas a Airflow es necesario reconstruir la imagen generada. Más información [aquí](https://airflow.apache.org/docs/docker-stack/index.html).

### Primeros pasos

#### Generar configuración

Para iniciar el stack completo, se puede configurar mediante el script `init.py`. El script preguntará por cada una de las variables que deben inicializarse previo a su utilización. Todos los valores por defecto resultarán en un stack funcional, aunque no necesariamente listo para producción. Adicionalmente, se creará un archivo de inicialización para PostgreSQL, localizado en `postgres/init.sql`, que será ejecutado automáticamente al iniciar la base de datos. Si se utiliza otra base, esto debe realizarse manualmente.

Ejecutar el script:

```bash
./init.py
```

Verificar la existencia del archivo `.env`:

```bash
ls .env
```

#### Iniciar base de datos (PostgreSQL 14)

Este paso puede omitirse si no se configuró una base de datos PostgreSQL para Airflow. Solo realizar las partes de Redis.

```bash
docker compose up -d postgres redis
docker compose logs postgres | tail -1
# Salida esperada:
# postgres  | 2024-10-03 16:42:02.918 UTC [1] LOG:  database system is ready to accept connections

docker compose logs redis | tail -1
# Salida esperada:
# af-redis  | 1:M 03 Oct 2024 16:42:01.263 * Ready to accept connections tcp
```

#### Inicializar el resto de los contenedores

Estableciendo las siguientes dos variables en `true`, se crearán los contenedores necesarios y la base de Airflow con los parámetros proporcionados.

```bash
_AIRFLOW_DB_MIGRATE=true
_AIRFLOW_WWW_USER_CREATE=true
```

Luego, ejecutar:

```bash
docker compose up -d
docker compose ps  # Ver resultado
```

Salida esperada:

```
NAME                  IMAGE                                 COMMAND                  SERVICE               CREATED          STATUS                        PORTS
af-flower             gather-flower                         "/usr/bin/dumb-init …"   flower                2 minutes ago    Up About a minute             5555/tcp, 8080/tcp
af-redis              redis:7.2-bookworm                    "docker-entrypoint.s…"   redis                 22 minutes ago   Up 22 minutes (healthy)       6379/tcp
af-scheduler          gather-airflow-scheduler              "/usr/bin/dumb-init …"   airflow-scheduler     3 minutes ago    Up 3 minutes (unhealthy)      8080/tcp
af-triggerer          gather-airflow-triggerer              "/usr/bin/dumb-init …"   airflow-triggerer     2 minutes ago    Up About a minute (healthy)   8080/tcp
af-webserver          gather-airflow-webserver              "/usr/bin/dumb-init …"   airflow-webserver     2 minutes ago    Up About a minute (healthy)   8080/tcp
af-worker_1           gather-airflow-worker_1               "/usr/bin/dumb-init …"   airflow-worker_1      2 minutes ago    Up About a minute (healthy)   8080/tcp
af-worker_2           gather-airflow-worker_2               "/usr/bin/dumb-init …"   airflow-worker_2      2 minutes ago    Up About a minute (healthy)   8080/tcp
docker-socket-proxy   tecnativa/docker-socket-proxy:0.1.1   "/docker-entrypoint.…"   docker-socket-proxy   2 minutes ago    Up 2 minutes                  2375/tcp
gather-proxy-1        gather-proxy                          "sh -c ./start.sh"       proxy                 2 minutes ago    Up About a minute             0.0.0.0:80->80/tcp, :::80->80/tcp
postgres              postgres:14.13-alpine3.20             "docker-entrypoint.s…"   postgres              22 minutes ago   Up 22 minutes (healthy)       5432/tcp
```

#### Modificaciones para producción

Como recomendación, una vez que el stack esté funcionando, podemos cambiar algunos parámetros para mejorar la seguridad.

```bash
_AIRFLOW_DB_MIGRATE=false
_AIRFLOW_WWW_USER_CREATE=false
AIRFLOW__WEBSERVER__EXPOSE_CONFIG=non-sensitive-only  # Mostrará solo los valores no sensibles.
                                                      # También puede establecerse en 'false' para no mostrar.
AIRFLOW__CORE__LOAD_EXAMPLES=false  # Si no se quieren visualizar más los ejemplos.
```

También pueden eliminarse las siguientes variables de autenticación que ya no son necesarias:

- PostgreSQL: `PG_USER`, `PG_PASS`, `PG_DB`
- Airflow: `AF_DB`, `AF_USER`, `AF_PASS`

### Entender el stack

#### Base de datos

Para una utilización real de Airflow se recomienda configurar una base de datos PostgreSQL o MySQL. Por defecto, Airflow utiliza SQLite, pero esto solo está pensado para desarrollo.

Más información [aquí](https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html)

#### Secrets Backend

Para almacenamiento de variables y conexiones de forma segura, puede configurarse el secrets backend mediante distintos proveedores.

Más información [aquí](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html)

#### Comandos de Airflow CLI

Se pueden ejecutar comandos de Airflow, pero debe realizarse en alguno de los servicios definidos (`airflow-*`). Por ejemplo, para ejecutar `airflow info`:

```bash
docker compose run airflow-worker airflow info
```

Propuestas, dudas y consultas a [diegolpedro@gmail.com](mailto:diegolpedro@gmail.com)