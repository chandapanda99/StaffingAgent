from app.core.config import Settings


def test_settings_from_env() -> None:
    settings = Settings()
    assert settings.database_url
    assert settings.graph_user_id
