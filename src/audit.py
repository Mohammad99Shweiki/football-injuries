"""Phase 0 data audit: raw inventory, table shapes, coverage, missingness, duplicates and a first look at injuries."""

from collections import Counter
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from collect.config import LEAGUES, SEASONS, expected_clubs, expected_league_matches, fd_season_code
from src.load import (
    FIGURES_DIR,
    FIRST_SEASON,
    LAST_SEASON,
    RAW_DIR,
    REPORTS_DIR,
    TABLES,
    league_by_name,
    league_from_tm,
    league_from_understat,
    read_table,
    season_from_date,
    season_key,
    table_path,
)

# Natural keys: a duplicate on these is a real duplicate, not just a repeated value.
KEYS = {
    "fd_matches": ["league", "season_code", "HomeTeam", "AwayTeam"],
    "us_matches": ["id"],
    "us_team_matches": ["league", "season", "team_id", "date"],
    "us_player_seasons": ["league", "season", "id", "team_title"],
    "tm_clubs": ["competition_id", "season_param", "club_id"],
    "tm_squads": ["season_param", "club_id", "playerId"],
    # injuryId is an injury-type code (one per label), not an event id: an event is player + dates + label.
    "tm_injuries": ["playerId", "start", "end", "name"],
    "tm_player_stats": ["player_id", "season_id", "competition_id", "club_id"],
    "tm_fixtures": ["club_id", "game_id"],
}

# Columns the later phases use; their missingness is shown in the report (all columns go to the CSV).
KEY_COLUMNS = {
    "fd_matches": ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR"],
    "us_team_matches": ["ppda.att", "ppda.def", "ppda_allowed.att", "ppda_allowed.def", "deep", "deep_allowed", "npxG", "npxGA"],
    "tm_squads": ["date_of_birth", "position", "position_group"],
    "tm_injuries": ["start", "end", "durationDetails.days", "missedGamesCount", "name"],
    "tm_player_stats": ["minutes_played", "appearances", "club_id"],
    "tm_fixtures": ["game.date.dateTimeUTC", "game.competitionTypeId"],
}


# ---- helpers ------------------------------------------------------------------------------------------------------


def md_table(df: pd.DataFrame, index: bool = True) -> str:
    """GitHub markdown table (no tabulate dependency)."""
    if index:
        df = df.reset_index()
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "–"


def coverage_grid(counts: pd.DataFrame, expected) -> tuple[pd.DataFrame, int]:
    """League × season grid of observed counts, a `!` marking each cell that differs from `expected(league, season)`."""
    grid = counts.reindex(index=[lg.name for lg in LEAGUES], columns=list(SEASONS)).fillna(0).astype(int)
    off = 0
    out = grid.astype(str)
    for name in grid.index:
        for season in grid.columns:
            if grid.at[name, season] != expected(league_by_name(name), season):
                out.at[name, season] += " !"
                off += 1
    out.columns = [season_key(s) for s in out.columns]
    return out, off


# ---- sections -----------------------------------------------------------------------------------------------------


def raw_inventory() -> pd.DataFrame:
    """Files, size and extensions per raw source folder (and per first-level folder for Transfermarkt)."""
    rows = []
    for source in sorted(p for p in RAW_DIR.iterdir() if p.is_dir()):
        groups: dict[str, list] = {}
        for f in source.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                rel = f.relative_to(source)
                group = rel.parts[0] if len(rel.parts) > 1 and source.name == "transfermarkt" else "(all)"
                if source.name == "transfermarkt" and len(rel.parts) == 1:
                    group = rel.name.split("__")[0] + "__*"
                groups.setdefault(group, []).append(f)
        for group, files in sorted(groups.items()):
            exts = Counter(f.suffix or "(none)" for f in files)
            rows.append(
                {
                    "source": source.name,
                    "folder": group,
                    "files": len(files),
                    "size_MB": round(sum(f.stat().st_size for f in files) / 1e6, 1),
                    "extensions": ", ".join(f"{e} {n}" for e, n in exts.most_common()),
                }
            )
    return pd.DataFrame(rows).set_index(["source", "folder"])


def table_overview(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in tables.items():
        body = df.drop(columns="source_file", errors="ignore")
        encodings = ", ".join(sorted(df["source_encoding"].unique())) if "source_encoding" in df else "utf-8 (JSON)"
        rows.append(
            {
                "table": name,
                "rows": len(df),
                "columns": df.shape[1],
                "size_MB": round(table_path(name).stat().st_size / 1e6, 1),
                "source encoding": encodings,
                "empty cells": pct((body == "").to_numpy().sum(), body.size),
                "exact duplicate rows": int(body.duplicated().sum()),
                "duplicates on key": int(df.duplicated(KEYS[name]).sum()),
                "key": " + ".join(KEYS[name]),
            }
        )
    return pd.DataFrame(rows).set_index("table")


def missingness(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Every column of every table: empty cells and share."""
    rows = [
        {"table": name, "column": col, "empty": int((df[col] == "").sum()), "share": round((df[col] == "").mean(), 4)}
        for name, df in tables.items()
        for col in df.columns
    ]
    return pd.DataFrame(rows)


def fd_match_coverage(fd: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    code_to_season = {fd_season_code(s): s for s in SEASONS}
    counts = fd.assign(season=fd.season_code.map(code_to_season)).groupby(["league", "season"]).size().unstack()
    return coverage_grid(counts, expected_league_matches)


def us_match_coverage(us: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Understat league matches per league-season from the team-match table (two rows per match)."""
    counts = (
        us.assign(league=us.league.map(league_from_understat), season=us.season.astype(int))
        .groupby(["league", "season"])
        .size()
        .floordiv(2)
        .unstack()
    )
    return coverage_grid(counts, expected_league_matches)


def club_coverage(tables: dict[str, pd.DataFrame]) -> dict[str, tuple[pd.DataFrame, int]]:
    """Clubs per league-season in each source."""
    fd, us, cl = tables["fd_matches"], tables["us_team_matches"], tables["tm_clubs"]
    code_to_season = {fd_season_code(s): s for s in SEASONS}
    fd_counts = (
        pd.concat([fd[["league", "season_code", "HomeTeam"]].rename(columns={"HomeTeam": "team"}),
                   fd[["league", "season_code", "AwayTeam"]].rename(columns={"AwayTeam": "team"})])
        .assign(season=lambda d: d.season_code.map(code_to_season))
        .groupby(["league", "season"]).team.nunique().unstack()
    )
    us_counts = (
        us.assign(league=us.league.map(league_from_understat), season=us.season.astype(int))
        .groupby(["league", "season"]).team_id.nunique().unstack()
    )
    tm_counts = cl.assign(season=cl.season_param.astype(int)).groupby(["league", "season"]).club_id.nunique().unstack()
    return {
        "Football-Data": coverage_grid(fd_counts, expected_clubs),
        "Understat": coverage_grid(us_counts, expected_clubs),
        "Transfermarkt": coverage_grid(tm_counts, expected_clubs),
    }


def squad_coverage(tables: dict[str, pd.DataFrame]) -> dict:
    """Squads per club-season: presence, size, and how many listed players actually played for the club that season."""
    cl, sq, ps = tables["tm_clubs"], tables["tm_squads"], tables["tm_player_stats"]
    club_seasons = cl[["league", "season_param", "club_id"]].drop_duplicates()
    sizes = sq.groupby(["season_param", "club_id"]).size().rename("listed")
    played = (
        ps[(ps.appearances != "") & (ps.appearances != "0")]
        .rename(columns={"player_id": "playerId", "season_id": "season_param"})[["playerId", "season_param", "club_id"]]
        .drop_duplicates()
    )
    used = sq.merge(played, on=["playerId", "season_param", "club_id"]).groupby(["season_param", "club_id"]).size()
    cs = club_seasons.join(sizes, on=["season_param", "club_id"]).join(used.rename("played"), on=["season_param", "club_id"])
    cs = cs.fillna({"listed": 0, "played": 0})
    by_league = cs.groupby("league")[["listed", "played"]].agg(["min", "median", "max"]).round(0).astype(int)
    by_league.columns = [f"{a} {b}" for a, b in by_league.columns]
    largest = cs.nlargest(5, "listed").assign(club=lambda d: d.club_id.map(cl.drop_duplicates("club_id").set_index("club_id").club_name))
    return {
        "club_seasons": len(club_seasons),
        "missing": int((cs.listed == 0).sum()),
        "by_league": by_league.reindex([lg.name for lg in LEAGUES]),
        "largest": largest[["league", "season_param", "club", "listed", "played"]].set_index("club"),
        "players": sq.playerId.nunique(),
        "played_by_league": cs.groupby("league").played.sum(),
    }


def injury_league_season(inj: pd.DataFrame, sq: pd.DataFrame, cl: pd.DataFrame) -> pd.DataFrame:
    """Rough league per injury for the audit only: the league(s) of the player's squad(s) in the injury's date-season.
    Phase 2 replaces this with attribution to the club on the injury date."""
    sq_league = sq.assign(league=sq.competition_id.map(league_from_tm), season=sq.season_param.astype(int))
    per_player = sq_league.groupby(["playerId", "season"]).league.agg(lambda s: s.iloc[0] if s.nunique() == 1 else "(two leagues)")
    return inj.join(per_player, on=["playerId", "date_season"])


def injury_summary(tables: dict[str, pd.DataFrame]) -> dict:
    inj = tables["tm_injuries"].copy()
    inj["date_season"] = season_from_date(inj.start)
    inj["days"] = pd.to_numeric(inj["durationDetails.days"], errors="coerce")
    window = inj[inj.date_season.between(FIRST_SEASON, LAST_SEASON)]
    window = injury_league_season(window, tables["tm_squads"], tables["tm_clubs"])

    same_start = window.duplicated(["playerId", "start"], keep=False)
    label_counts = window.name.value_counts()
    cum = label_counts.cumsum() / len(window)

    per_season = window.groupby("date_season").agg(
        records=("name", "size"),
        players=("playerId", "nunique"),
        days_missing=("days", lambda d: int(d.isna().sum())),
        over_7_days=("days", lambda d: int((d > 7).sum())),
        unknown_label=("name", lambda n: int((n == "unknown injury").sum())),
    )
    per_season["unknown label %"] = (100 * per_season.unknown_label / per_season.records).round(1)
    per_season.index = pd.Index([season_key(s) for s in per_season.index], name="season")

    per_league = (
        window.assign(league=window.league.fillna("(not in a Big Five squad)"))
        .pivot_table(index="league", columns="date_season", values="name", aggfunc="size", fill_value=0)
    )
    per_league.columns = [season_key(c) for c in per_league.columns]
    per_league["total"] = per_league.sum(axis=1)

    return {
        "all_records": len(inj),
        "window": window,
        "before_window": int((inj.date_season < FIRST_SEASON).sum()),
        "after_window": int((inj.date_season > LAST_SEASON).sum()),
        "no_start": int(inj.date_season.isna().sum()),
        "per_season": per_season,
        "per_league": per_league,
        "days_missing": int(window.days.isna().sum()),
        "ongoing": int((window.end == "").sum()),
        "unknown_label": int((window.name == "unknown injury").sum()),
        "ill_category": int((window.category == "Ill").sum()),
        "labels": int(window.name.nunique()),
        "type_ids": int(window.injuryId.nunique()),
        "labels_for_95": int((cum < 0.95).sum() + 1),
        "top_labels": label_counts.head(25),
        "same_start_records": int(same_start.sum()),
        "same_start_events": int(window[same_start].groupby(["playerId", "start"]).ngroups),
        "exact_dups": int(window.duplicated(KEYS["tm_injuries"]).sum()),
        "season_label_agree": float((window.seasonId == window.date_season.astype(str)).mean()),
        "days_quantiles": window.days.quantile([0.25, 0.5, 0.75, 0.9]).to_dict(),
        "over_7": int((window.days > 7).sum()),
        "over_28": int((window.days > 28).sum()),
    }


def injuries_figure(per_league: pd.DataFrame) -> str:
    leagues = [lg.name for lg in LEAGUES]
    data = per_league.loc[per_league.index.intersection(leagues), [c for c in per_league.columns if c != "total"]]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for league in leagues:
        if league in data.index:
            ax.plot(data.columns, data.loc[league], marker="o", label=league)
    ax.set_ylabel("Injury records (all durations)")
    ax.set_title("Transfermarkt injury records per season (raw, before cleaning)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    path = FIGURES_DIR / "00_injury_records_per_season.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


# ---- report -------------------------------------------------------------------------------------------------------


def run() -> str:
    """Run the whole audit, write reports/00_data_audit.md and reports/00_missingness.csv; return the markdown."""
    REPORTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    tables = {name: read_table(name) for name in TABLES}

    raw = raw_inventory()
    overview = table_overview(tables)
    miss = missingness(tables)
    miss.to_csv(REPORTS_DIR / "00_missingness.csv", index=False)
    fd_grid, fd_off = fd_match_coverage(tables["fd_matches"])
    us_grid, us_off = us_match_coverage(tables["us_team_matches"])
    clubs = club_coverage(tables)
    squads = squad_coverage(tables)
    inj = injury_summary(tables)
    figure = injuries_figure(inj["per_league"])

    fd = tables["fd_matches"]
    fd_stat_gaps = fd[(fd.HST == "") | (fd.HF == "") | (fd.HY == "")][["league", "season_code", "Date", "HomeTeam", "AwayTeam"]]
    um = tables["us_matches"]
    us_unplayed = um[um.isResult == "false"].groupby(["league", "season"]).size()
    us_ppda0 = int((tables["us_team_matches"]["ppda.def"] == "0").sum())
    used = pd.DataFrame([(t, c) for t, cols in KEY_COLUMNS.items() for c in cols], columns=["table", "column"])
    key_miss = miss.merge(used).query("empty > 0")
    w = inj["window"]
    big5 = inj["per_league"].loc[[lg.name for lg in LEAGUES], "total"]
    rate = (big5 / squads["played_by_league"]).round(2).sort_values(ascending=False)
    per_season = inj["per_season"]
    series = inj["per_league"].loc[[lg.name for lg in LEAGUES]].drop(columns="total")
    jumps = [
        (lg, series.columns[i - 1], series.columns[i], int(series.iat[r, i - 1]), int(series.iat[r, i]))
        for r, lg in enumerate(series.index)
        for i in range(1, series.shape[1])
        if abs(series.iat[r, i] / series.iat[r, i - 1] - 1) > 0.4
    ]
    findings = [
        "## Key findings",
        "",
        "- **Coverage is complete.** Match and club counts match the expected values in all three sources, for all "
        "60 league-seasons. All 1,170 TM club-seasons have a squad.",
        f"- **Match stats:** {len(fd_stat_gaps)} Football-Data matches lack match statistics, and Understat has no gaps. "
        f"Neither needs action beyond per-match rates over the matches that have the data.",
        f"- **Injuries:** {len(w):,} TM records fall in the study window. {pct(inj['over_7'], len(w))} last more than 7 days, "
        f"and {pct(inj['days_missing'], len(w))} have no duration (mostly 2025-26 injuries still open at scrape time).",
        f"- **The \"unknown injury\" share rises over time**, from {per_season['unknown label %'].iloc[0]}% in "
        f"{per_season.index[0]} to {per_season['unknown label %'].max()}% at its peak. The body-area analysis must "
        "report unknowns per season, because they can bias trends.",
        f"- **Recording differs by league.** Injury records per played player-season: "
        + ", ".join(f"{lg} {v}" for lg, v in rate.items())
        + ". TM's community coverage, not real injury burden, may drive part of this, so league comparisons need "
        "this caveat. Within-league comparisons are safer.",
        "- **Step changes in league series**, i.e. year-on-year changes of more than 40% in raw records: "
        + "; ".join(f"{lg} {a}→{b} ({x:,}→{y:,})" for lg, a, b, x, y in jumps)
        + ". 2020-21 jumps are plausible (COVID records, congested calendar). Others, such as the Premier League "
        "doubling in 2018-19, look like changes in TM recording. Trend charts must be read against these.",
        f"- **{pct(inj['per_league'].loc['(not in a Big Five squad)', 'total'], len(w))} of in-window records** happen "
        "while the player is outside a Big Five squad (before or after their Big Five seasons). They drop out when "
        "injuries are attributed to Big Five club-seasons in Phase 2.",
        "- **Non-injuries** (Ill, Corona virus, flu, Fitness, Rest …) have to be identified from labels, because TM's "
        "category flags only a few of them.",
        "",
    ]

    out = [
        "# Phase 0: Data audit",
        "",
        f"Generated {date.today().isoformat()} by `notebooks/00_audit.ipynb` (`src/audit.py`). Raw data is read only.",
        "",
        *findings,
        "## 1. Raw files (`data/raw/`)",
        "",
        md_table(raw),
        "",
        "## 2. Parsed tables (`data/tables/`)",
        "",
        "All values are kept as original text. Empty cells are counted as missing.",
        "",
        md_table(overview),
        "",
        f"- **Key duplicates:** only `tm_injuries`, with {overview.at['tm_injuries', 'duplicates on key']} repeats of "
        f"player + dates + label ({inj['exact_dups']} in the study window). The other tables have none on their keys.",
        "- `tm_injuries.injuryId` is an **injury-type code**: each id has one label, and some labels have several ids. "
        "It is not an event id.",
        "",
        "## 3. Coverage",
        "",
        "`!` marks a cell that differs from the expected count: 380 matches (20 clubs), Bundesliga 306 (18 clubs), "
        "Ligue 1 306 (18 clubs) from 2023-24, and Ligue 1 2019-20 279 (COVID stop).",
        "",
        f"### League matches per league-season: Football-Data ({fd_off} cells off)",
        "",
        md_table(fd_grid),
        "",
        f"### League matches per league-season: Understat ({us_off} cells off)",
        "",
        md_table(us_grid),
        "",
        f"- Understat also lists {int(us_unplayed.sum())} unplayed fixtures (`isResult = false`): "
        + ", ".join(f"{lg} {s}: {n}" for (lg, s), n in us_unplayed.items())
        + ". These are the Ligue 1 2019-20 matches cancelled for COVID, and they are absent from the team-match table.",
        "",
        "### Clubs per league-season",
        "",
    ]
    for source, (grid, off) in clubs.items():
        out += [f"**{source}** ({off} cells off)", "", md_table(grid), ""]
    out += [
        "### Squads per club-season (Transfermarkt)",
        "",
        f"- {squads['club_seasons']} club-seasons, {squads['missing']} without a squad. "
        f"{squads['players']:,} distinct players.",
        "- **listed** = players on the TM season squad page. **played** = those with ≥ 1 appearance for that club "
        "that season in any competition (from `tm_player_stats`).",
        "",
        md_table(squads["by_league"]),
        "",
        "Largest listed squads: these include youth and loaned-out players who never played.",
        "",
        md_table(squads["largest"]),
        "",
        "## 4. Missingness",
        "",
        "Full per-column list: `reports/00_missingness.csv`. Columns used later with any empty cells:",
        "",
        md_table(key_miss.set_index(["table", "column"])),
        "",
        f"- **Football-Data:** {len(fd_stat_gaps)} matches without match statistics (shots, fouls, corners or cards):",
        "",
        md_table(fd_stat_gaps, index=False),
        "",
        "- **Football-Data betting columns** vary by season (bookmakers come and go), which explains most empty cells in "
        "`fd_matches`. They aren't used.",
        f"- **Understat:** no empty style columns. {us_ppda0} team-matches have `ppda.def = 0` (an undefined match PPDA). "
        "This doesn't matter, because season PPDA = Σatt / Σdef.",
        "",
        "## 5. Injuries (Transfermarkt)",
        "",
        f"- **{inj['all_records']:,} records** cover each collected player's whole career. **{len(w):,}** start within "
        f"{season_key(FIRST_SEASON)} to {season_key(LAST_SEASON)} (season = 1 July to 30 June). "
        f"{inj['before_window']:,} are earlier, {inj['after_window']:,} are later (2026-27, in progress), and {inj['no_start']} have no start date.",
        f"- The TM `seasonId` agrees with the date-based season for **{100 * inj['season_label_agree']:.1f}%** of in-window records.",
        f"- **Days missing:** {inj['days_missing']} records ({pct(inj['days_missing'], len(w))}) have no duration "
        f"(\"Unknown\"). {inj['ongoing']} have no end date (ongoing or unknown).",
        f"- **Duration quantiles (days):** "
        + ", ".join(f"p{int(q * 100)} = {v:.0f}" for q, v in inj["days_quantiles"].items())
        + f". **> 7 days:** {inj['over_7']:,} ({pct(inj['over_7'], len(w))}). "
        f"**> 28 days:** {inj['over_28']:,} ({pct(inj['over_28'], len(w))}).",
        f"- **Labels:** {inj['labels']} distinct raw labels ({inj['type_ids']} type ids). **{inj['labels_for_95']}** labels "
        f"cover 95% of records. \"unknown injury\": {inj['unknown_label']:,} ({pct(inj['unknown_label'], len(w))}).",
        f"- **Non-injuries:** TM's `category` marks only {inj['ill_category']:,} records as \"Ill\" "
        "(Corona virus, Virus, Quarantine). Labels such as \"Ill\", \"flu\", \"cold\", \"Fitness\" and \"Rest\" sit under "
        "\"Unknown\", so the exclusion list has to be built from labels (Phase 2).",
        f"- **Several diagnoses for one absence:** {inj['same_start_records']} records share player + start date "
        f"({inj['same_start_events']} absences), e.g. Hip injury + Torn muscle fiber. Decided: each record counts "
        "as a separate injury (see DECISIONS.md).",
        "",
        "### Per season",
        "",
        md_table(inj["per_season"]),
        "",
        "### Per league (rough league: the player's squad league in that season)",
        "",
        md_table(inj["per_league"]),
        "",
        "Injury records per played player-season (Big Five squads only): "
        + ", ".join(f"{lg} {v}" for lg, v in rate.items()) + ".",
        "",
        f"![Injury records per season](figures/{figure})",
        "",
        "### Top 25 labels (in window)",
        "",
        md_table(inj["top_labels"].rename("records").to_frame().rename_axis("label")),
        "",
    ]
    text = "\n".join(out)
    (REPORTS_DIR / "00_data_audit.md").write_text(text, encoding="utf-8")
    return text
