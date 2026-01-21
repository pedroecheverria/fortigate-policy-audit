from __future__ import annotations

import requests


class FortiGateClient:
    def __init__(self, base_url: str, token: str, verify_ssl: bool = True, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    def get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        r = requests.get(
            url,
            headers=headers,
            params=params or {},
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        if not r.ok:
            raise RuntimeError(f"HTTP {r.status_code} al llamar {url}: {r.text[:400]}")

        return r.json()
