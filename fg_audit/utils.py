from __future__ import annotations

from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


def epoch_to_local_iso(epoch: int | None, tz_name: str = "Europe/Madrid") -> str:

    if epoch is None:
        return "N/A"

    try:
        epoch_int = int(epoch)
    except (ValueError, TypeError):
        return "N/A"

    if ZoneInfo is not None:
        try:
            tz = ZoneInfo(tz_name)
            dt = datetime.fromtimestamp(epoch_int, tz=tz)
            return dt.isoformat(timespec="seconds")
        except Exception:
            pass

    # Fallback UTC
    dt = datetime.fromtimestamp(epoch_int, tz=timezone.utc)
    return dt.isoformat(timespec="seconds")
