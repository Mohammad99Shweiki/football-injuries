"""Parse all raw data into `data/tables/*.csv`. Usage: python -m parse [--only TABLE ...]"""

import argparse
import time

from collect.common import log
from parse import transfermarkt
from parse.common import TableBuilder, write_table
from parse.football_data import FdMatches
from parse.understat import UsMatches, UsPlayerSeasons, UsTeamMatches, UsTeamStats


def all_builders() -> list[TableBuilder]:
    return [FdMatches(), UsTeamMatches(), UsPlayerSeasons(), UsMatches(), UsTeamStats(), *transfermarkt.builders()]


def parse_all(only: list[str] | None = None) -> None:
    for builder in all_builders():
        if only and builder.name not in only:
            continue
        started = time.monotonic()
        path, count = write_table(builder.name, builder.rows())
        log("parse", f"{builder.name}: {count} rows -> {path.name} ({time.monotonic() - started:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", metavar="TABLE")
    parse_all(parser.parse_args().only)


if __name__ == "__main__":
    main()
