from __future__ import annotations

from typing import Any
from fg_audit.client import FortiGateClient
from fg_audit.utils import epoch_to_local_iso


MONITOR_POLICY_ENDPOINT = "/api/v2/monitor/firewall/policy"


def fetch_policy_stats(client: FortiGateClient, vdom: str = "root") -> dict[str, Any]:
    """
    Llama al endpoint monitor de policies y devuelve el JSON completo.
    """
    return client.get(MONITOR_POLICY_ENDPOINT, params={"vdom": vdom})


def normalize_policy_stats(payload: dict[str, Any], tz_name: str = "Europe/Madrid") -> list[dict[str, Any]]:
    """
    Convierte el JSON del endpoint monitor a filas listas para tabla/CSV:
    policy_id, bytes, packets, first_used, last_used (fechas en ISO local)
    """
    results = payload.get("results", [])
    rows: list[dict[str, Any]] = []

    for item in results:
        policy_id = item.get("policyid")
        bytes_ = item.get("bytes", 0)
        packets = item.get("packets", 0)

        first_used = item.get("first_used")  # puede no venir
        last_used = item.get("last_used")    # puede no venir

        rows.append({
            "policy_id": int(policy_id) if policy_id is not None else None,
            "bytes": int(bytes_) if bytes_ is not None else 0,
            "packets": int(packets) if packets is not None else 0,
            "first_used": epoch_to_local_iso(first_used, tz_name=tz_name),
            "last_used": epoch_to_local_iso(last_used, tz_name=tz_name),
        })

    # Ordena por policy_id
    rows.sort(key=lambda r: (r["policy_id"] is None, r["policy_id"]))
    return rows
