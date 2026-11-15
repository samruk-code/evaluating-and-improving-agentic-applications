#!/usr/bin/env bash
# Stop the Gradio app started by run.sh.
cd "$(dirname "$0")" || exit 1

PIDFILE=.app.pid

if [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null; then
    rm -f "$PIDFILE"
    echo "App stopped."
elif pkill -f "python3 (-u )?app.py" 2>/dev/null; then
    rm -f "$PIDFILE"
    echo "App stopped."
else
    echo "App was not running."
fi
