import shutil
import subprocess
import sys
from pathlib import Path

from openpaper_cli.utils.console import console


class SystemDetector:
    @property
    def is_windows(self) -> bool:
        return sys.platform == "win32"

    @property
    def is_linux(self) -> bool:
        return sys.platform == "linux"

    @property
    def is_macos(self) -> bool:
        return sys.platform == "darwin"

    def check_docker(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
            return False, "Docker not found"
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)

    def check_docker_compose(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
            return False, "Docker Compose not found"
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)

    def check_ollama(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
            return False, "Ollama not found"
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, str(e)

    def check_ollama_models(self) -> list[str]:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                models = []
                for line in result.stdout.strip().split("\n")[1:]:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                return models
            return []
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    def check_nvidia_gpu(self) -> tuple[bool, str]:
        if self.is_windows:
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True, text=True, timeout=10
                )
                has_nvidia = "nvidia" in result.stdout.lower()
                return has_nvidia, "NVIDIA GPU detected" if has_nvidia else "No NVIDIA GPU detected"
            except Exception:
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    has_nvidia = kernel32.LoadLibraryW("nvml.dll") is not None
                    return True, "NVIDIA GPU detected (via nvml.dll)"
                except Exception:
                    return False, "No NVIDIA GPU detected"
        else:
            try:
                result = subprocess.run(
                    ["nvidia-smi"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    first_line = result.stdout.strip().split("\n")[0]
                    return True, first_line
                return False, "nvidia-smi not available"
            except FileNotFoundError:
                return False, "NVIDIA drivers not found"

    def check_python_version(self) -> tuple[bool, str]:
        v = sys.version_info
        ok = v.major >= 3 and v.minor >= 11
        version = f"{v.major}.{v.minor}.{v.micro}"
        return ok, version

    def check_ports(self, ports: list[int]) -> list[dict]:
        results = []
        for port in ports:
            in_use = self._is_port_in_use(port)
            results.append({"port": port, "in_use": in_use})
        return results

    def _is_port_in_use(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return False
            except OSError:
                return True

    def check_git(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Git not found"
        except FileNotFoundError:
            return False, "Git not found"

    def get_system_info(self) -> dict:
        import platform
        return {
            "os": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "hostname": platform.node(),
            "cpu_count": str(getattr(platform, "processor", lambda: "unknown")()),
        }

    def get_installed_models(self) -> list[dict]:
        models = []
        ollama_models = self.check_ollama_models()
        for m in ollama_models:
            models.append({"name": m, "source": "ollama", "provider": "ollama"})
        return models
