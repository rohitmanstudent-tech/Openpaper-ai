"""Registry API client — HTTP client for OpenPaper Hub."""

import json
from typing import Any

import httpx

from openpaper.config import get_registry_url, get_token


HEADERS = {
    "User-Agent": "openpaper-cli/0.1.0",
    "Accept": "application/json",
}


def _get_headers() -> dict[str, str]:
    headers = dict(HEADERS)
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_packages(
    query: str = "",
    package_type: str = "",
    sort: str = "downloads",
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    url = f"{get_registry_url()}/hub/packages"
    params = {"page": page, "page_size": page_size, "sort": sort}
    if query:
        params["query"] = query
    if package_type:
        params["package_type"] = package_type

    resp = httpx.get(url, params=params, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_package(package_id: str) -> dict[str, Any]:
    url = f"{get_registry_url()}/hub/packages/{package_id}"
    resp = httpx.get(url, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def resolve_package(package_id: str, version: str = "") -> dict[str, Any]:
    url = f"{get_registry_url()}/hub/packages/{package_id}/resolve"
    params = {}
    if version:
        params["version"] = version
    resp = httpx.get(url, params=params, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def publish_package(
    manifest: dict[str, Any],
    source_archive: str = "",
    changelog: str = "",
    signature: str = "",
    signature_key_id: str = "",
    visibility: str = "public",
) -> dict[str, Any]:
    url = f"{get_registry_url()}/hub/packages"
    body = {
        "manifest": manifest,
        "source_archive": source_archive,
        "changelog": changelog,
        "signature": signature,
        "signature_key_id": signature_key_id,
        "visibility": visibility,
    }
    resp = httpx.post(url, json=body, headers=_get_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def unpublish_package(package_id: str) -> dict[str, Any]:
    url = f"{get_registry_url()}/hub/packages/{package_id}"
    resp = httpx.delete(url, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def login(email: str, password: str) -> dict[str, Any]:
    url = f"{get_registry_url()}/auth/login"
    resp = httpx.post(
        url,
        json={"email": email, "password": password},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def register_user(email: str, password: str, username: str) -> dict[str, Any]:
    url = f"{get_registry_url()}/auth/register"
    resp = httpx.post(
        url,
        json={"email": email, "password": password, "username": username},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_registry_stats() -> dict[str, Any]:
    url = f"{get_registry_url()}/hub/stats"
    resp = httpx.get(url, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()
