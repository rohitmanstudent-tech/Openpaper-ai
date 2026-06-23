import os
import subprocess
import json
from pathlib import Path
from typing import Any

from openpaper_cli.utils.console import console
from openpaper_cli.core import get_config_dir


class DockerManager:
    def __init__(self, instance: str = "default"):
        self.instance = instance
        self.project_name = f"openpaper-{instance}"
        self.compose_dir = self._find_compose_dir()

    def _find_compose_dir(self) -> Path:
        candidates = [
            Path.cwd(),
            Path.cwd().parent,
            Path.home() / "openpaper-ai",
        ]
        for d in candidates:
            if (d / "docker-compose.yml").exists():
                return d
        return Path.cwd()

    @property
    def compose_file(self) -> Path:
        return self.compose_dir / "docker-compose.yml"

    def has_compose_file(self) -> bool:
        return self.compose_file.exists()

    def is_running(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "compose", "-p", self.project_name, "ps", "--format", "json"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.compose_dir),
            )
            if result.returncode == 0 and result.stdout.strip():
                services = json.loads(result.stdout)
                if isinstance(services, list):
                    return any(s.get("State") == "running" for s in services)
                return services.get("State") == "running"
            return False
        except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
            return False

    def get_status(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["docker", "compose", "-p", self.project_name, "ps", "--format", "json"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.compose_dir),
            )
            if result.returncode == 0 and result.stdout.strip():
                services = json.loads(result.stdout)
                if isinstance(services, list):
                    return [
                        {"name": s.get("Name", s.get("Service", "?")), "status": s.get("State", "?"), "ports": s.get("Ports", "")}
                        for s in services
                    ]
                return [{"name": services.get("Name", services.get("Service", "?")), "status": services.get("State", "?"), "ports": services.get("Ports", "")}]
            return []
        except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
            return []

    def up(self, services: list[str] | None = None, detach: bool = True) -> tuple[bool, str]:
        cmd = ["docker", "compose", "-p", self.project_name, "up", "--build"]
        if detach:
            cmd.append("-d")
        if services:
            cmd.extend(services)

        try:
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                cwd=str(self.compose_dir),
            )
            if result.returncode == 0:
                return True, "Services started successfully"
            return False, result.stderr or result.stdout
        except subprocess.TimeoutExpired:
            return False, "Timeout starting services"
        except FileNotFoundError as e:
            return False, str(e)

    def down(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["docker", "compose", "-p", self.project_name, "down"],
                capture_output=True, text=True, timeout=60,
                cwd=str(self.compose_dir),
            )
            if result.returncode == 0:
                return True, "Services stopped"
            return False, result.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)

    def logs(self, service: str | None = None, follow: bool = False) -> tuple[bool, str]:
        cmd = ["docker", "compose", "-p", self.project_name, "logs"]
        if follow:
            cmd.append("-f")
        if service:
            cmd.append(service)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                cwd=str(self.compose_dir),
            )
            return result.returncode == 0, result.stdout or result.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)

    def pull_model(self, model: str = "llama3.1") -> tuple[bool, str]:
        try:
            console.print(f"[dim]Pulling model: {model}...[/dim]")
            result = subprocess.run(
                ["docker", "compose", "-p", self.project_name, "exec", "-T", "ollama", "ollama", "pull", model],
                capture_output=True, text=True, timeout=600,
                cwd=str(self.compose_dir),
            )
            if result.returncode == 0:
                return True, f"Model '{model}' pulled successfully"
            return False, result.stderr or result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)

    def execute(self, service: str, cmd: list[str]) -> tuple[bool, str]:
        try:
            docker_cmd = ["docker", "compose", "-p", self.project_name, "exec", "-T", service] + cmd
            result = subprocess.run(
                docker_cmd, capture_output=True, text=True, timeout=60,
                cwd=str(self.compose_dir),
            )
            return result.returncode == 0, result.stdout or result.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)
