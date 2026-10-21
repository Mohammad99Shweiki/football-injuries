"""File helpers shared by collectors, the status writer and validation."""

import os
from pathlib import Path


def atomic_write(path: Path, data: bytes) -> None:
    """Write via a temp file so an interrupted run never leaves a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def is_cached(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0
