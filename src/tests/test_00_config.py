import importlib

from src.shared import config


# Case1: test fixed environment variable read
def test_read_environment_variable():
    settings = config.Settings(_env_file=".env.example")

    assert settings.gemini_api_key == "gemini-api-key"
    assert settings.database_url == "database-url"
    assert settings.ono_username == "ono-username"
    assert settings.ono_password == "ono-password"
    assert settings.database_key == "your-firebase-key"


# Case2: test changed environment variable read
def test_read_changed_environment_variable(monkeypatch):
    settings_dev = config.Settings(_env_file=".env.example")

    monkeypatch.setenv("ENVIRONMENT", "production")
    importlib.reload(config)
    settings_prod = config.Settings(_env_file=".env.example")

    assert settings_dev.line_channel_access_token == "demo-line-channel-access-token"
    assert settings_dev.line_channel_secret == "demo-line-channel-secret"
    # assert settings_dev.line_user_id == "demo-line-user-id"

    assert settings_prod.line_channel_access_token == "line-channel-access-token"
    assert settings_prod.line_channel_secret == "line-channel-secret"
    # assert settings_prod.line_user_id == "line-user-id"
