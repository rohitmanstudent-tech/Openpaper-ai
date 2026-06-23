import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
from openpaper_cli.core import get_config_dir


class SecretsManager:
    def __init__(self, instance: str = "default"):
        self.secrets_dir = get_config_dir(instance) / "secrets"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.secrets_dir / ".key"
        self.store_file = self.secrets_dir / "vault.json"
        self._cipher = self._load_or_create_key()

    def _load_or_create_key(self) -> Fernet:
        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            os.chmod(self.key_file, 0o600)
        return Fernet(key)

    def _load_vault(self) -> dict[str, str]:
        if self.store_file.exists():
            try:
                encrypted = self.store_file.read_bytes()
                decrypted = self._cipher.decrypt(encrypted)
                return json.loads(decrypted.decode())
            except Exception:
                return {}
        return {}

    def _save_vault(self, vault: dict[str, str]) -> None:
        data = json.dumps(vault).encode()
        encrypted = self._cipher.encrypt(data)
        self.store_file.write_bytes(encrypted)

    def set(self, key: str, value: str) -> None:
        vault = self._load_vault()
        vault[key] = value
        self._save_vault(vault)

    def get(self, key: str) -> str | None:
        vault = self._load_vault()
        return vault.get(key)

    def delete(self, key: str) -> bool:
        vault = self._load_vault()
        if key in vault:
            del vault[key]
            self._save_vault(vault)
            return True
        return False

    def list_keys(self) -> list[str]:
        vault = self._load_vault()
        return list(vault.keys())

    def has(self, key: str) -> bool:
        vault = self._load_vault()
        return key in vault
