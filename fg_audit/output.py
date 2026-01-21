from __future__ import annotations

import csv
from typing import Any


def print_table(rows: list[dict[str, Any]], headers: list[str]) -> None:
    # calcula anchos
    cols = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            cols[h] = max(cols[h], len(str(r.get(h, ""))))

    # separadores
    sep = "+".join("-" * (cols[h] + 2) for h in headers)
    sep = f"+{sep}+"

    # header row
    header_line = "|".join(f" {h.ljust(cols[h])} " for h in headers)
    header_line = f"|{header_line}|"

    print(sep)
    print(header_line)
    print(sep)

    # data rows
    for r in rows:
        line = "|".join(f" {str(r.get(h, '')).ljust(cols[h])} " for h in headers)
        print(f"|{line}|")

    print(sep)


def write_csv(rows: list[dict[str, Any]], out_path: str, headers: list[str]) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})
