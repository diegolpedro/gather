# Procesos

### Construccion

#### Construcción de la imagen Docker
Construye la imagen Docker utilizando el siguiente comando:
```bash
docker build -f Dockerfile -t uphb .
```
---
### Ejecución

#### Securities
Inicia el servicio de descarga de acciones (securities):
```bash
docker compose up upsec
```
#### Options
Inicia el servicio de descarga de opciones:
```bash
docker compose up upopt
```
---
