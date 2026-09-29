# Web UI integration note

This package exposes a router, not a standalone app.

Include it from the main FastAPI app with:

```python
from capra_pia.web import router as web_router

app.include_router(web_router, prefix="/ui")
```

The router mounts its own local static assets, so the UI will resolve to:

- `/ui/`
- `/ui/submit`
- `/ui/static/style.css`

`routes.py` calls the API over HTTP using `CAPRA_PIA_API_BASE_URL`
(default `http://127.0.0.1:8000`) and does not import loader/scoring directly.
