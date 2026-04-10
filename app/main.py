from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import models as _models  # noqa: F401
from fastapi import FastAPI

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, debug=settings.app_debug, version="0.1.0")
app.include_router(api_router)
