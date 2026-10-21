"""Football-Data CSVs -> `fd_matches` (union of columns across seasons)."""

import csv
import io
from collections.abc import Iterator
from pathlib import Path

from collect.config import LEAGUES
from collect.football_data import OUT_DIR
from parse.common import Row, TableBuilder, source_file

# Tried in order. Most files are UTF-8 (some with BOM); a few older ones are Windows-1252.
ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
LEAGUE_BY_DIV = {league.fd_div: league for league in LEAGUES}


def decode(raw: bytes) -> tuple[str, str]:
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise AssertionError("latin-1 decodes any byte sequence")


class FdMatches(TableBuilder):
    name = "fd_matches"

    def __init__(self, raw_dir: Path = OUT_DIR) -> None:
        self.raw_dir = raw_dir

    def rows(self) -> Iterator[Row]:
        for path in sorted(self.raw_dir.glob("*/*.csv")):
            content, encoding = decode(path.read_bytes())
            reader = csv.reader(io.StringIO(content))
            header = next(reader, [])
            for values in reader:
                if not any(v.strip() for v in values):
                    continue  # blank padding lines at the end of some files carry no data
                row = {"league": LEAGUE_BY_DIV[path.stem].name, "season_code": path.parent.name}
                for index, value in enumerate(values):
                    column = header[index] if index < len(header) and header[index] else f"_unnamed_{index}"
                    if column.startswith("_unnamed_") and not value:
                        continue  # trailing commas without a header or a value
                    row[column] = value
                row["source_file"] = source_file(path)
                row["source_encoding"] = encoding
                yield row
