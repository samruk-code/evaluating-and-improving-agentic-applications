#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")" || exit 1

PIDFILE=".phoenix.pid"
PHOENIX_PORT="${PHOENIX_PORT:-6006}"

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    kill "$(cat "${PIDFILE}")" 2>/dev/null || true
    rm -f "${PIDFILE}"
fi
pkill -f "phoenix serve.*--port ${PHOENIX_PORT}" 2>/dev/null || true
echo "Phoenix stopped."
