#!/usr/bin/env bash
# Start the Gradio app in the BACKGROUND so it keeps serving after this command
# returns (running `python3 app.py` in the foreground gets killed as soon as the
# shell/agent command finishes, which is why the Preview shows "no response").
#
# Re-run this script to RESTART the app after you edit app.py — it stops the
# previous instance first so the port is free and your changes take effect.
cd "$(dirname "$0")" || exit 1

PIDFILE=.app.pid

# Stop a previous instance we started.
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill "$(cat "$PIDFILE")" 2>/dev/null
fi
# Belt-and-suspenders: stop any stray app process and free port 7860.
pkill -f "python3 (-u )?app.py" 2>/dev/null || true
sleep 1

# -u: unbuffered. Without it Python block-buffers stdout when it is a file,
# so app.log stays empty for a long while and the Logs panel shows nothing
# exactly when someone is trying to find out what went wrong.
# sitecustomize.py turns off FastAPI's built-in HTTP tracing before Gradio
# starts. Otherwise Gradio's startup checks are stored as Phoenix traces
# once register() installs a tracer. Agent spans are unaffected.
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"

nohup python3 -u app.py > app.log 2>&1 &
echo $! > "$PIDFILE"

echo "App running in the background (pid $(cat "$PIDFILE"))."
echo "  URL:     http://localhost:7860  (or the Preview App button)"
echo "  Logs:    tail -f app.log"
echo "  Restart: bash run.sh"
echo "  Stop:    bash stop.sh"

for _ in $(seq 1 40); do
    if curl -fsS --max-time 2 -o /dev/null "http://127.0.0.1:7860/" 2>/dev/null; then
        echo "Gradio Agent App is working now."
        exit 0
    fi
    sleep 0.5
done
echo "WARN: App process started but http://localhost:7860 is not answering yet."
echo "Check: tail -f app.log"
exit 0
