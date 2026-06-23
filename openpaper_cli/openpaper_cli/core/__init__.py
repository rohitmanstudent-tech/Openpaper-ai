import os
import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "openpaper-ai"


def get_config_dir(instance: str = "default") -> Path:
    base = Path(user_config_dir(APP_NAME))
    return base / instance


def get_data_dir(instance: str = "default") -> Path:
    base = Path(user_data_dir(APP_NAME))
    return base / instance


CONFIG_DEFAULTS = {
    "instance": "default",
    "api_host": "localhost",
    "api_port": 8000,
    "frontend_port": 3000,
    "postgres_port": 5432,
    "redis_port": 6379,
    "qdrant_port": 6333,
    "ollama_port": 11434,
    "postgres_user": "openpaper",
    "postgres_password": "",
    "postgres_db": "openpaper",
    "ollama_base_url": "http://localhost:11434",
    "secret_key": "",
    "openai_api_key": "",
    "anthropic_api_key": "",
    "google_api_key": "",
    "xai_api_key": "",
    "deepseek_api_key": "",
    "openrouter_api_key": "",
    "nvidia_api_key": "",
    "local_first": False,
    "auto_start": True,
    "telemetry": False,
}


class ConfigManager:
    def __init__(self, instance: str = "default"):
        self.instance = instance
        self.config_dir = get_config_dir(instance)
        self.config_file = self.config_dir / "config.json"
        self._config: dict[str, Any] = {}
        self.load()

    def ensure_dirs(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "secrets").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "state").mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        self._config = dict(CONFIG_DEFAULTS)
        self._config["instance"] = self.instance
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except (json.JSONDecodeError, OSError):
                pass
        return self._config

    def save(self) -> None:
        self.ensure_dirs()
        with open(self.config_file, "w") as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get_all(self) -> dict[str, Any]:
        return dict(self._config)

    def get_compose_env(self) -> dict[str, str]:
        return {
            "POSTGRES_USER": self.get("postgres_user", "openpaper"),
            "POSTGRES_PASSWORD": self.get("postgres_password", ""),
            "POSTGRES_DB": self.get("postgres_db", "openpaper"),
            "OLLAMA_BASE_URL": self.get("ollama_base_url", "http://localhost:11434"),
            "OPENAI_API_KEY": self.get("openai_api_key", ""),
            "ANTHROPIC_API_KEY": self.get("anthropic_api_key", ""),
            "GOOGLE_API_KEY": self.get("google_api_key", ""),
            "XAI_API_KEY": self.get("xai_api_key", ""),
            "DEEPSEEK_API_KEY": self.get("deepseek_api_key", ""),
            "OPENROUTER_API_KEY": self.get("openrouter_api_key", ""),
            "NVIDIA_API_KEY": self.get("nvidia_api_key", ""),
        }

    def list_instances(self) -> list[str]:
        base = Path(user_config_dir(APP_NAME))
        if not base.exists():
            return ["default"]
        instances = [d.name for d in base.iterdir() if d.is_dir()]
        if "default" not in instances:
            instances.insert(0, "default")
        return instances

    @staticmethod
    def generate_secret_key() -> str:
        import secrets
        return secrets.token_hex(32)
