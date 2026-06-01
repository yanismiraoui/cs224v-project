"""Configuration helpers for local development and deployed apps.

Secrets can be supplied either as environment variables (recommended for
production) or via the repository's legacy ``secrets.toml`` file for local
Streamlit runs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import toml as tomllib  # type: ignore[no-redef]


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SECRETS_PATH = PROJECT_ROOT / "secrets.toml"


class ConfigurationError(RuntimeError):
    """Raised when a required configuration value is missing."""


def load_secrets(secrets_path: str | os.PathLike[str] | None = None) -> Mapping[str, Any]:
    """Load TOML secrets from disk.

    Missing files are treated as an empty mapping so callers can rely on
    environment variables without creating a local ``secrets.toml``.
    """

    path = Path(secrets_path) if secrets_path is not None else DEFAULT_SECRETS_PATH
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text())


def get_secret(
    name: str,
    *,
    secrets_path: str | os.PathLike[str] | None = None,
    required: bool = True,
) -> str | None:
    """Return a secret from the environment or ``secrets.toml``.

    Environment variables intentionally take precedence so deployment
    platforms and CI can inject credentials without writing secret files.
    """

    env_value = os.getenv(name)
    if env_value:
        return env_value

    secrets = load_secrets(secrets_path)
    file_value = secrets.get(name)
    if file_value:
        return str(file_value)

    if required:
        path = Path(secrets_path) if secrets_path is not None else DEFAULT_SECRETS_PATH
        raise ConfigurationError(
            f"Missing required secret {name!r}. Set it as an environment variable "
            f"or add it to secrets.toml at {path}."
        )
    return None
