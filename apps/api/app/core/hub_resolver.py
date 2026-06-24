"""OpenPaper Hub — dependency resolver with version locking.

Supports semver constraint parsing, dependency graph resolution,
topological sort, conflict detection, and lockfile generation."""

import json
import re
from typing import Any

SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[a-zA-Z0-9.-]+))?"
    r"(?:\+(?P<build>[a-zA-Z0-9.-]+))?$"
)

CONSTRAINT_RE = re.compile(
    r"^(?P<op>>=|<=|==|!=|>|<|~=|\^)?"
    r"(?P<version>.+)$"
)


class Version:
    def __init__(self, version_str: str):
        self.raw = version_str
        m = SEMVER_RE.match(version_str)
        if not m:
            raise ValueError(f"Invalid semver: {version_str}")
        self.major = int(m.group("major"))
        self.minor = int(m.group("minor"))
        self.patch = int(m.group("patch"))
        self.prerelease = m.group("prerelease") or ""

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return f"Version({self.raw})"

    def __eq__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch, self.prerelease) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )

    def __lt__(self, other: "Version") -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return bool(self.prerelease) and not bool(other.prerelease)

    def __le__(self, other: "Version") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Version") -> bool:
        return not self <= other

    def __ge__(self, other: "Version") -> bool:
        return not self < other

    def __hash__(self):
        return hash((self.major, self.minor, self.patch, self.prerelease))


def parse_constraint(constraint_str: str) -> tuple[str, str]:
    m = CONSTRAINT_RE.match(constraint_str.strip())
    if not m:
        return ("==", constraint_str.strip())
    op = m.group("op") or "=="
    ver = m.group("version").strip()
    return (op, ver)


def satisfies(version_str: str, constraint_str: str) -> bool:
    version = Version(version_str)
    op, target_str = parse_constraint(constraint_str)
    target = Version(target_str)

    ops = {
        "==": lambda v, t: v == t,
        "!=": lambda v, t: v != t,
        ">": lambda v, t: v > t,
        ">=": lambda v, t: v >= t,
        "<": lambda v, t: v < t,
        "<=": lambda v, t: v <= t,
        "^": lambda v, t: v.major == t.major and v >= t,
        "~=": lambda v, t: v.major == t.major and v.minor == t.minor and v >= t,
    }
    return ops.get(op, lambda *_: False)(version, target)


def find_best_match(available_versions: list[str], constraint_str: str) -> str | None:
    sorted_versions = sorted(
        [v for v in available_versions if satisfies(v, constraint_str)],
        key=lambda v: Version(v),
        reverse=True,
    )
    return sorted_versions[0] if sorted_versions else None


class DependencyGraph:
    def __init__(self):
        self._nodes: dict[str, set[str]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def add_package(self, name: str, version: str, dependencies: list[str], metadata: dict[str, Any] | None = None):
        self._nodes[name] = set(dependencies)
        if metadata:
            self._metadata[name] = metadata

    def _has_cycle(self) -> bool:
        white, gray, black = 0, 1, 2
        color = {n: white for n in self._nodes}

        def dfs(node: str) -> bool:
            color[node] = gray
            for dep in self._nodes.get(node, set()):
                if dep in color:
                    if color[dep] == gray:
                        return True
                    if color[dep] == white and dfs(dep):
                        return True
            color[node] = black
            return False

        return any(color[node] == white and dfs(node) for node in list(self._nodes.keys()))

    def topological_sort(self) -> list[str]:
        if self._has_cycle():
            raise ValueError("Circular dependency detected")

        visited: set[str] = set()
        result: list[str] = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dep in self._nodes.get(node, set()):
                if dep in self._nodes:
                    dfs(dep)
            result.append(node)

        for node in list(self._nodes.keys()):
            dfs(node)
        return result

    def resolve(self) -> list[str]:
        return self.topological_sort()


class LockEntry:
    def __init__(self, name: str, version: str, resolved_version: str, dependencies: list[str], checksum: str = ""):
        self.name = name
        self.version = version
        self.resolved_version = resolved_version
        self.dependencies = dependencies
        self.checksum = checksum

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "resolved": self.resolved_version,
            "dependencies": self.dependencies,
            "checksum": self.checksum,
        }


class Lockfile:
    def __init__(self):
        self.entries: dict[str, LockEntry] = {}

    def add_entry(self, entry: LockEntry):
        self.entries[entry.name] = entry

    def to_json(self) -> str:
        data = {
            "lockfile_version": 1,
            "packages": {k: v.to_dict() for k, v in self.entries.items()},
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Lockfile":
        data = json.loads(json_str)
        lf = cls()
        for _name, entry_data in data.get("packages", {}).items():
            lf.add_entry(
                LockEntry(
                    name=entry_data["name"],
                    version=entry_data["version"],
                    resolved_version=entry_data["resolved"],
                    dependencies=entry_data.get("dependencies", []),
                    checksum=entry_data.get("checksum", ""),
                )
            )
        return lf
