from __future__ import annotations

from typing import Any


def merge_by_policy_id(
    monitor_rows: list[dict[str, Any]],
    cmdb_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Une monitor + cmdb por policy_id.
    - Si una policy existe en monitor pero no en cmdb, igual sale (con campos CMDB = N/A).
    - Si existe en cmdb pero no en monitor, igual sale (stats = 0 / N/A).
    """
    cmdb_map = {r.get("policy_id"): r for r in cmdb_rows if r.get("policy_id") is not None}
    monitor_map = {r.get("policy_id"): r for r in monitor_rows if r.get("policy_id") is not None}

    all_ids = sorted(set(cmdb_map.keys()) | set(monitor_map.keys()))

    merged: list[dict[str, Any]] = []
    for pid in all_ids:
        m = monitor_map.get(pid, {})
        c = cmdb_map.get(pid, {})

        merged.append({
            "policy_id": pid,

            # CMDB
            "policy_name": c.get("policy_name", "N/A"),
            "status": c.get("status", "N/A"),
            "action": c.get("action", "N/A"),
            "nat": c.get("nat", "N/A"),
            "schedule": c.get("schedule", "N/A"),
            "srcintf": c.get("srcintf", "N/A"),
            "dstintf": c.get("dstintf", "N/A"),
            "srcaddr": c.get("srcaddr", "N/A"),
            "dstaddr": c.get("dstaddr", "N/A"),
            "services": c.get("services", "N/A"),

            # MONITOR
            "bytes": m.get("bytes", 0),
            "packets": m.get("packets", 0),
            "first_used": m.get("first_used", "N/A"),
            "last_used": m.get("last_used", "N/A"),
        })

    return merged
