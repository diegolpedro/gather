#!/usr/bin/env bash
# Script para enviar espacio libre en disco al final del día vía Telegram
set -u

# Configuración de binarios y URLs
CURL_BIN="${CURL_BIN:-/usr/bin/curl}"
ALERT_URL="${ALERT_URL:-http://localhost:8500/alerts}"
CHAT_ID="${CHAT_ID:-1384905495}"
MOUNT_POINT="${MOUNT_POINT:-/}"

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
