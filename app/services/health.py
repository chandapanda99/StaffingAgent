from app.domain.schemas import ReadinessCheck, ReadinessResponse
from sqlalchemy import text

from app.db.session import engine


class HealthService:
    def __init__(self, storage) -> None:
        self.storage = storage

    def readiness(self) -> ReadinessResponse:
        checks: list[ReadinessCheck] = []

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks.append(ReadinessCheck(name="database", ok=True, detail="ok"))
        except Exception as exc:  # pragma: no cover
            checks.append(ReadinessCheck(name="database", ok=False, detail=str(exc)))

        ok, detail = self.storage.readiness_check()
        checks.append(ReadinessCheck(name="object_storage", ok=ok, detail=detail))

        return ReadinessResponse(
            status="ok" if all(item.ok for item in checks) else "degraded",
            checks=checks,
        )
