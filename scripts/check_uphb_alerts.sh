#!/usr/bin/env bash
set -u

DOCKER_BIN="${DOCKER_BIN:-/usr/bin/docker}"
CURL_BIN="${CURL_BIN:-/usr/bin/curl}"
ALERT_URL="${ALERT_URL:-http://localhost:8500/alerts}"
CHAT_ID="${CHAT_ID:-1384905495}"
STATE_DIR="${STATE_DIR:-/tmp/gather-alert-state}"
SEND_RECOVERY_ALERT="${SEND_RECOVERY_ALERT:-true}"

mkdir -p "$STATE_DIR"

send_alert() {
  local message="$1"
  local response

  response="$("$CURL_BIN" -fsS -X POST "$ALERT_URL" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"$message\",\"telegram\":{\"chat_id\":\"$CHAT_ID\"}}" \
    2>/dev/null)" || return 1

  printf '%s\n' "$response" | grep -q '"success":true'
}

inspect_field() {
  local container_name="$1"
  local template="$2"

  "$DOCKER_BIN" inspect -f "$template" "$container_name" 2>/dev/null || true
}

check_container() {
  local service_name="$1"
  local container_name="$2"
  local status
  local exit_code
  local state_file

  state_file="$STATE_DIR/${container_name}.down"
  status="$(inspect_field "$container_name" "{{.State.Status}}")"

  if [ -z "$status" ]; then
    status="missing"
    exit_code="unknown"
  else
    exit_code="$(inspect_field "$container_name" "{{.State.ExitCode}}")"
  fi

  if [ "$status" != "running" ]; then
    if [ ! -f "$state_file" ]; then
      if send_alert "ALERTA gather: $service_name no esta corriendo. container=$container_name status=$status exit_code=$exit_code"; then
        date -Iseconds >"$state_file"
      fi
    fi
    return
  fi

  if [ -f "$state_file" ]; then
    rm -f "$state_file"
    if [ "$SEND_RECOVERY_ALERT" = "true" ]; then
      send_alert "OK gather: $service_name volvio a estar corriendo. container=$container_name" || true
    fi
  fi
}

check_container "upsec" "upload-securities"
check_container "upopt" "upload-options"
check_container "upbon" "upload-bonds"
