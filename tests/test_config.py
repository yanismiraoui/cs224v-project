import pytest

from langchain_agents.config import ConfigurationError, get_secret, load_secrets


def test_get_secret_prefers_environment_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("TOGETHER_API_KEY", "from-env")
    secrets_file = tmp_path / "secrets.toml"
    secrets_file.write_text('TOGETHER_API_KEY = "from-file"\n')

    assert get_secret("TOGETHER_API_KEY", secrets_path=secrets_file) == "from-env"


def test_get_secret_reads_project_secrets_file_when_env_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    secrets_file = tmp_path / "secrets.toml"
    secrets_file.write_text('TOGETHER_API_KEY = "from-file"\n')

    assert get_secret("TOGETHER_API_KEY", secrets_path=secrets_file) == "from-file"


def test_load_secrets_missing_file_returns_empty_mapping(tmp_path):
    assert load_secrets(tmp_path / "missing.toml") == {}


def test_get_secret_raises_helpful_error_when_required_secret_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)

    with pytest.raises(ConfigurationError) as exc_info:
        get_secret("TOGETHER_API_KEY", secrets_path=tmp_path / "missing.toml")

    message = str(exc_info.value)
    assert "TOGETHER_API_KEY" in message
    assert "environment variable" in message
    assert "secrets.toml" in message
