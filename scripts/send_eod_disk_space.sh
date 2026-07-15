#!/usr/bin/env bash
# Script para enviar espacio libre en disco al final del día vía Telegram
set -u

# Configuración de binarios y URLs
CURL_BIN="${CURL_BIN:-/usr/bin/curl}"
ALERT_URL="${ALERT_URL:-http://localhost:8500/alerts}"
CHAT_ID="${CHAT_ID:-1384905495}"
MOUNT_POINT="${MOUNT_POINT:-/}"
DEBUG="${DEBUG:-0}"

# Envía alerta al endpoint de alertas con el mensaje y chat_id de Telegram
send_alert() {
  local message="$1"
  local response
  local stderr_file
  local curl_exit
  local payload

  payload="$(python3 - "$message" "$CHAT_ID" <<'PY'
import json
import sys

data = {
    "message": sys.argv[1],
    "telegram": {"chat_id": sys.argv[2]},
}
print(json.dumps(data))
PY
)"

  stderr_file="$(mktemp)"
  response="$("$CURL_BIN" -fsS -X POST "$ALERT_URL" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    2>"$stderr_file")" || curl_exit=$?

  if [ -n "${curl_exit:-}" ]; then
    if [ "$DEBUG" = "1" ]; then
      printf 'DEBUG curl exit: %s\n' "$curl_exit" >&2
      cat "$stderr_file" >&2
    fi
    rm -f "$stderr_file"
    return 1
  fi

  if [ "$DEBUG" = "1" ]; then
    printf 'DEBUG payload: %s\n' "$payload" >&2
    printf 'DEBUG response: %s\n' "$response" >&2
  fi

  rm -f "$stderr_file"

  if ! printf '%s\n' "$response" | python3 -c 'import json,sys; data=json.load(sys.stdin); results=data.get("results",[]); sys.exit(0 if results and results[0].get("success") is True else 1)'; then
    if [ "$DEBUG" = "1" ]; then
      printf 'DEBUG response validation failed\n' >&2
    fi
    return 1
  fi
}

# Obtiene información de espacio en disco
get_disk_info() {
  local mount_point="$1"
  local disk_info

  # Ejecutar df y extraer fila del mount point
  disk_info="$(df -h "$mount_point" | tail -1)"
  echo "$disk_info"
}

# Envía reporte de espacio en disco al final del día
send_disk_report() {
  local disk_info
  local filesystem
  local total
  local used
  local available
  local percent
  local message

  disk_info="$(get_disk_info "$MOUNT_POINT")"
  
  # Parsear salida de df
  filesystem=$(echo "$disk_info" | awk '{print $1}')
  total=$(echo "$disk_info" | awk '{print $2}')
  used=$(echo "$disk_info" | awk '{print $3}')
  available=$(echo "$disk_info" | awk '{print $4}')
  percent=$(echo "$disk_info" | awk '{print $5}')

  # Construir mensaje
  message="📊 REPORTE EOD - ESPACIO EN DISCO"
  message="$message"$'\n'"Sistema: $filesystem"
  message="$message"$'\n'"Total: $total"
  message="$message"$'\n'"Usado: $used ($percent)"
  message="$message"$'\n'"Disponible: $available"
  message="$message"$'\n'"Timestamp: $(date -Iseconds)"

  # Enviar alerta
  if send_alert "$message"; then
    printf '[%s] Reporte de disco enviado exitosamente\n' "$(date -Iseconds)"
    return 0
  else
    printf '[%s] Error al enviar reporte de disco\n' "$(date -Iseconds)" >&2
    return 1
  fi
}

# Ejecutar reporte
send_disk_report
