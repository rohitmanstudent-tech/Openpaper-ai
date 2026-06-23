"""Local CLI configuration — auth tokens, registry URL, preferences."""

import os
import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "openpaper"
CONFIG_FILE = CONFIG_DIR / "config.json"
AUTH_FILE = CONFIG_DIR / "auth.json"


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_registry_url() -> str:
    return os.environ.get(
        "OPENPAPER_REGISTRY",
        "https://hub.openpaper.ai/api/v1",
    )


def get_config() -> dict:
    _ensure_dir()
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def set_config(key: str, value: str) -> None:
    _ensure_dir()
    cfg = get_config()
    cfg[key] = value
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def get_auth() -> dict:
    _ensure_dir()
    if AUTH_FILE.exists():
        try:
            return json.loads(AUTH_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def set_auth(token: str, refresh_token: str = "", email: str = "") -> None:
    _ensure_dir()
    AUTH_FILE.write_text(json.dumps({
        "token": token,
        "refresh_token": refresh_token,
        "email": email,
    }, indent=2))
    AUTH_FILE.chmod(0o600)


def clear_auth() -> None:
    _ensure_dir()
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()


def get_token() -> str | None:
    auth = get_auth()
    return auth.get("token")
