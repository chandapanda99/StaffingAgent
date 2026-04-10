import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("GRAPH_TENANT_ID", "tenant")
os.environ.setdefault("GRAPH_CLIENT_ID", "client")
os.environ.setdefault("GRAPH_CLIENT_SECRET", "secret")
os.environ.setdefault("GRAPH_USER_ID", "mailbox@example.com")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY", "minioadmin")
os.environ.setdefault("S3_SECRET_KEY", "minioadmin")
os.environ.setdefault("S3_BUCKET", "email-intake")
os.environ.setdefault("S3_REGION", "us-east-1")
os.environ.setdefault("S3_SECURE", "false")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_MODEL", "gpt-4.1-mini")

import pytest

from app.db.base import Base
from app.db import models as _models  # noqa: F401
from app.db.session import engine


@pytest.fixture(autouse=True)
def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
