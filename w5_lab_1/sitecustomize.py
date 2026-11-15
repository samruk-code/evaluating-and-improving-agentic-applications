"""Turn off FastAPI's built-in HTTP traces.

run.sh puts this directory on PYTHONPATH, so Python imports this module before
app.py. app.py also imports it before Gradio. FastAPI records a span for every
request once a global tracer exists, which is what phoenix.otel.register()
installs. Gradio's startup checks would otherwise show up in Phoenix before
anyone sends a prompt. Agent spans are not HTTP spans, so they stay.
"""

import fastapi

_FastAPI = fastapi.FastAPI


class _QuietFastAPI(_FastAPI):
    def __init__(self, *args, **kwargs):
        telemetry = dict(kwargs.pop("telemetry", None) or {})
        telemetry["tracing"] = False
        telemetry["metrics"] = False
        telemetry["logs"] = False
        super().__init__(*args, telemetry=telemetry, **kwargs)


fastapi.FastAPI = _QuietFastAPI
