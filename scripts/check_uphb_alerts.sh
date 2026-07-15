#!/usr/bin/env bash
# Script para monitorear contenedores de gather y enviar alertas por Telegram
set -u

# Configuración de binarios y URLs
DOCKER_BIN="${DOCKER_BIN:-/usr/bin/docker}"
CURL_BIN="${CURL_BIN:-/usr/bin/curl}"
ALERT_URL="${ALERT_URL:-http://localhost:8500/alerts}"
CHAT_ID="${CHAT_ID:-1384905495}"
STATE_DIR="${STATE_DIR:-/tmp/gather-alert-state}"
SEND_RECOVERY_ALERT="${SEND_RECOVERY_ALERT:-true}"

# Crear directorio para almacenar estado de alertas
mkdir -p "$STATE_DIR"

# Envía alerta al endpoint de alertas con el mensaje y chat_id de Telegram
send_alert() {
  local message="$1"
  local response

  response="$("$CURL_BIN" -fsS -X POST "$ALERT_URL" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"$message\",\"telegram\":{\"chat_id\":\"$CHAT_ID\"}}" \
    2>/dev/null)" || return 1

  printf '%s\n' "$response" | grep -q '"success":true'
}

# Obtiene información de un contenedor usando docker inspect con template
inspect_field() {
  local container_name="$1"
  local template="$2"

  "$DOCKER_BIN" inspect -f "$template" "$container_name" 2>/dev/null || true
}

# Verifica estado de un contenedor y envía alertas si cambió de estado
check_container() {
  local service_name="$1"
  local container_name="$2"
  local status
  local exit_code
  local state_file

  state_file="$STATE_DIR/${container_name}.down"
  status="$(inspect_field "$container_name" "{{.State.Status}}")"

  # Si el contenedor no existe, marcar como "missing"
  if [ -z "$status" ]; then
    status="missing"
    exit_code="unknown"
  else
    exit_code="$(inspect_field "$container_name" "{{.State.ExitCode}}")"
  fi

  # Si no está corriendo: enviar alerta y guardar estado
  if [ "$status" != "running" ]; then
    if [ ! -f "$state_file" ]; then
      if send_alert "ALERTA gather: $service_name no esta corriendo. container=$container_name status=$status exit_code=$exit_code"; then
        date -Iseconds >"$state_file"
      fi
    fi
    return
  fi

  # Si estaba down y ahora corre: enviar alerta de recuperación
  if [ -f "$state_file" ]; then
    rm -f "$state_file"
    if [ "$SEND_RECOVERY_ALERT" = "true" ]; then
      send_alert "OK gather: $service_name volvio a estar corriendo. container=$container_name" || true
    fi
  fi
}

# Monitorear los servicios principales
check_container "upsec" "upload-securities"
check_container "upopt" "upload-options"
check_container "upbon" "upload-bonds"
