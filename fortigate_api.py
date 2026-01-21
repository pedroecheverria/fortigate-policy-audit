import requests
from typing import Any, Dict, Optional


class FortiGateAPIError(Exception):
    pass


def get_json(url: str, token: str, timeout: int = 15, verify_tls: bool = True) -> Dict[str, Any]:
    """
    Performs a GET request and returns JSON payload.
    - verify_tls: set False only if you use https with self-signed cert and want to skip validation.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=verify_tls)
    except requests.RequestException as e:
        raise FortiGateAPIError(f"Request failed: {e}") from e

    if resp.status_code == 401:
        raise FortiGateAPIError("401 Unauthorized: token inválido o faltante.")
    if resp.status_code == 403:
        raise FortiGateAPIError("403 Forbidden: el token no tiene permisos para este endpoint.")
    if resp.status_code == 404:
        raise FortiGateAPIError("404 Not Found: endpoint incorrecto o API deshabilitada en esa ruta.")
    if not resp.ok:
        raise FortiGateAPIError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    try:
        return resp.json()
    except ValueError as e:
        raise FortiGateAPIError(f"Respuesta no es JSON: {resp.text[:300]}") from e
