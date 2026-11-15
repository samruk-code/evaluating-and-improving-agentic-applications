#!/usr/bin/env bash
# Start Phoenix natively (pip package arize-phoenix) in the background.
#
# Configure where Phoenix stores its SQLite database and exports:
#   PHOENIX_DATA_DIR  — directory for phoenix.db and exports (default: ./phoenix-data)
#   PHOENIX_HOST      — bind address (default: 0.0.0.0)
#   PHOENIX_PORT      — HTTP + OTLP port (default: 6006)
#
# Examples:
#   bash phoenix-start.sh
#   PHOENIX_DATA_DIR=/workspace/my-traces bash phoenix-start.sh
#   PHOENIX_PORT=6007 PHOENIX_DATA_DIR=./session-1 bash phoenix-start.sh
set -euo pipefail
cd "$(dirname "$0")" || exit 1

PHOENIX_DATA_DIR="${PHOENIX_DATA_DIR:-./phoenix-data}"
PHOENIX_HOST="${PHOENIX_HOST:-0.0.0.0}"
PHOENIX_PORT="${PHOENIX_PORT:-6006}"
PIDFILE=".phoenix.pid"
LOGFILE="phoenix.log"

if ! command -v phoenix >/dev/null 2>&1; then
    echo "ERROR: phoenix CLI not found. Run: pip install -r requirements.txt" >&2
    exit 1
fi

mkdir -p "${PHOENIX_DATA_DIR}"
PHOENIX_WORKING_DIR="$(cd "${PHOENIX_DATA_DIR}" && pwd)"
export PHOENIX_WORKING_DIR

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    kill "$(cat "${PIDFILE}")" 2>/dev/null || true
    sleep 1
fi
pkill -f "phoenix serve.*--port ${PHOENIX_PORT}" 2>/dev/null || true
sleep 1

PHOENIX_WORKING_DIR="${PHOENIX_WORKING_DIR}" \
    nohup phoenix serve \
        --host "${PHOENIX_HOST}" \
        --port "${PHOENIX_PORT}" \
        >"${LOGFILE}" 2>&1 &
echo $! > "${PIDFILE}"

echo "Phoenix running in the background (pid $(cat "${PIDFILE}"))."
echo "  UI:        http://localhost:${PHOENIX_PORT}"
echo "  Data dir:  ${PHOENIX_WORKING_DIR}  (SQLite DB + exports)"
echo "  Logs:      tail -f ${LOGFILE}"
echo "  Restart:   bash phoenix-start.sh"
echo "  Stop:      bash phoenix-stop.sh"

# Wait briefly so callers (and OpenCode) can treat this as a ready signal.
for _ in $(seq 1 30); do
    if curl -fsS -o /dev/null "http://127.0.0.1:${PHOENIX_PORT}/" 2>/dev/null; then
        echo "Phoenix is ready to be used."
        exit 0
    fi
    sleep 0.5
done
echo "WARN: Phoenix process started but http://localhost:${PHOENIX_PORT} is not answering yet."
echo "Check: tail -f ${LOGFILE}"
exit 0
