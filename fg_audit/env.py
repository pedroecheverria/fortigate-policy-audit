from __future__ import annotations

from pathlib import Path


def load_env(path: str = ".env") -> dict[str, str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo .env en: {p.resolve()}")

    cfg: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        cfg[k] = v

    required = ["FORTIGATE_BASE_URL", "FORTIGATE_TOKEN"]
    missing = [k for k in required if k not in cfg or not cfg[k]]
    if missing:
        raise ValueError(f"Faltan variables requeridas en .env: {', '.join(missing)}")

    return cfg


def get_env_bool(cfg: dict[str, str], key: str, default: bool = True) -> bool:
    raw = cfg.get(key, str(default)).strip().lower()
    return raw in ("1", "true", "yes", "y", "on")
