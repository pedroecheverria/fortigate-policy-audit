#!/usr/bin/env python3
from fg_audit.env import load_env, get_env_bool
from fg_audit.client import FortiGateClient

from fg_audit.monitor import fetch_policy_stats, normalize_policy_stats
from fg_audit.cmdb import fetch_policies_cmdb, normalize_policies_cmdb
from fg_audit.merge import merge_by_policy_id

from fg_audit.output import print_table, write_csv


def main() -> int:
    cfg = load_env(".env")

    base_url = cfg["FORTIGATE_BASE_URL"].rstrip("/")
    token = cfg["FORTIGATE_TOKEN"]
    vdom = cfg.get("FORTIGATE_VDOM", "root")
    tz = cfg.get("TIMEZONE", "Europe/Madrid")
    verify_ssl = get_env_bool(cfg, "VERIFY_SSL", default=True)

    out_monitor = cfg.get("OUT_CSV_MONITOR", "output_monitor.csv")
    out_cmdb = cfg.get("OUT_CSV_CMDB", "output_cmdb.csv")
    out_merged = cfg.get("OUT_CSV_MERGED", "pre_final.csv")

    client = FortiGateClient(base_url=base_url, token=token, verify_ssl=verify_ssl)

    # 1) MONITOR (stats)
    monitor_raw = fetch_policy_stats(client, vdom=vdom)
    monitor_rows = normalize_policy_stats(monitor_raw, tz_name=tz)

    monitor_headers = ["policy_id", "bytes", "packets", "first_used", "last_used"]
    print("\n=== MONITOR (stats) ===")
    print_table(monitor_rows, headers=monitor_headers)
    write_csv(monitor_rows, out_monitor, headers=monitor_headers)
    print(f"CSV generado: {out_monitor}")

    # 2) CMDB (config)
    cmdb_raw = fetch_policies_cmdb(client, vdom=vdom)
    cmdb_rows = normalize_policies_cmdb(cmdb_raw)

    cmdb_headers = [
        "policy_id", "policy_name", "status", "action", "nat", "schedule",
        "srcintf", "dstintf", "srcaddr", "dstaddr", "services"
    ]
    print("\n=== CMDB (config) ===")
    print_table(cmdb_rows, headers=cmdb_headers)
    write_csv(cmdb_rows, out_cmdb, headers=cmdb_headers)
    print(f"CSV generado: {out_cmdb}")

    # 3) MERGE (pre-final)
    merged_rows = merge_by_policy_id(monitor_rows, cmdb_rows)

    merged_headers = [
        "policy_id", "policy_name", "status", "action", "nat", "schedule",
        "srcintf", "dstintf", "srcaddr", "dstaddr", "services",
        "bytes", "packets", "first_used", "last_used"
    ]
    print("\n=== PRE-FINAL (merged) ===")
    print_table(merged_rows, headers=merged_headers)
    write_csv(merged_rows, out_merged, headers=merged_headers)
    print(f"CSV generado: {out_merged}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
