from __future__ import annotations

from typing import Any
from fg_audit.client import FortiGateClient

CMDB_POLICY_ENDPOINT = "/api/v2/cmdb/firewall/policy"


def fetch_policies_cmdb(client: FortiGateClient, vdom: str = "root") -> dict[str, Any]:
    """
    Trae policies desde CMDB. Como es un lab lo hacemos en una sola llamada. 
    """
    return client.get(CMDB_POLICY_ENDPOINT, params={"vdom": vdom})


def _names_from_list(lst: Any) -> str:
    """
    Convierte listas del estilo [{"name":"port4"}, ...] a "port4,port2".
    Si viene vacío o None => "N/A".
    """
    if not isinstance(lst, list) or not lst:
        return "N/A"
    names = []
    for x in lst:
        if isinstance(x, dict) and "name" in x:
            names.append(str(x["name"]))
    return ",".join(names) if names else "N/A"


def normalize_policies_cmdb(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Devuelve filas "limpias" para CSV/merge.
    """
    results = payload.get("results", [])
    rows: list[dict[str, Any]] = []

    for item in results:
        policy_id = item.get("policyid")
        rows.append({
            "policy_id": int(policy_id) if policy_id is not None else None,
            "policy_name": item.get("name") or "N/A",
            "status": item.get("status") or "N/A",
            "action": item.get("action") or "N/A",
            "nat": item.get("nat") or "N/A",
            "schedule": item.get("schedule") or "N/A",
            "srcintf": _names_from_list(item.get("srcintf")),
            "dstintf": _names_from_list(item.get("dstintf")),
            "srcaddr": _names_from_list(item.get("srcaddr")),
            "dstaddr": _names_from_list(item.get("dstaddr")),
            "services": _names_from_list(item.get("service")),
        })

    rows.sort(key=lambda r: (r["policy_id"] is None, r["policy_id"]))
    return rows
