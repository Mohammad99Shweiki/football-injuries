"""Shared parsing helpers: table builder interface, value-to-text conversion and CSV output."""

import csv
import json
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from collect.config import ROOT, TABLES_DIR

Row = dict[str, str]


class TableBuilder(ABC):
    """Builds one table from raw files. Values stay as their original text; every row carries `source_file`."""

    name: str

    @abstractmethod
    def rows(self) -> Iterator[Row]: ...


def text(value: Any) -> str:
    """Original value as text: strings unchanged, other JSON values in their JSON spelling, null as empty."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def flatten(obj: dict, prefix: str = "") -> Row:
    """Nested dicts become dotted columns (`ppda.att`); lists are kept as JSON text."""
    out: Row = {}
    for key, value in obj.items():
        column = f"{prefix}{key}"
        if isinstance(value, dict):
            out |= flatten(value, f"{column}.")
        else:
            out[column] = text(value)
    return out


def source_file(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_table(name: str, rows: Iterable[Row], out_dir: Path = TABLES_DIR) -> tuple[Path, int]:
    """Write rows to `<name>.csv` using the union of all columns, in order of first appearance."""
    rows = list(rows)
    columns: dict[str, None] = {}
    for row in rows:
        columns.update(dict.fromkeys(row))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)
    return path, len(rows)


def read_table(name: str, tables_dir: Path = TABLES_DIR) -> list[Row]:
    path = tables_dir / f"{name}.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
