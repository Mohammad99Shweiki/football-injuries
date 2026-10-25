"""Phase 02: Injury cleaning. Cells in the percent format; run with `python -m analysis.run 02`, notebook built by `scripts/notebooks/build_notebook.py`."""

# %% [markdown]
# # Phase 2: Injury cleaning and body-area mapping (data cleaning + transformation)
#
# **Goal:** turn Transfermarkt's injury histories into a clean list of injuries lasting **more than 7 days**, each tied
# to the Big Five club-season the player was in, with a body area, a surgery flag and a severity band. Non-injuries
# (illness, COVID, rest, …) are taken out and kept separately; *fitness* absences are kept for Phase 5 as a secondary
# outcome. Injuries of 4–7 days (*mild*) are kept in their own file for a sensitivity check.
#
# **Steps**
# 1. Load and parse injuries; drop exact duplicates
# 2. Each player's club matches, from the raw per-match files
# 3. Season of each injury (date rule, summer-2020 exception)
# 4. Study window; drop injuries without an end date
# 5. Club on the injury date
# 6. Keep injuries at a Big Five club-season the player belongs to
# 7. Label map: proposal and reviewed file
# 8. Apply the label map: non-injuries out, body area and surgery flag in
# 9. Severity: more than 7 days (main), 4–7 days (mild, sensitivity), bands
# 10. Coverage: unknown body area per season and league
# 11. Save outputs and write the report
#
# **Inputs:** `data/tables/` (`tm_injuries`, `tm_player_stats`), raw `performance-game` files (read only),
# `data/01_entities/team_seasons.csv`. **Outputs:** `mappings/injury_label_map.csv` (reviewed, in git),
# `data/02_injuries/`, `reports/02_injuries.md`. Decisions are in `docs/DECISIONS.md`; the counts printed by the
# `log(...)` calls go to `docs/PREPROCESSING_LOG.md`.

# %%
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd().parent))  # project root, for the analysis package
from analysis.config import DATA_DIR, MAPPINGS_DIR, RAW_DIR, REPORTS_DIR, SEASONS, phase_dir
from analysis.load import read_table, season_from_date, season_key
from analysis.report import md_table, pct

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 200)

PHASE = "02_injuries"
OUT_DIR = phase_dir(PHASE)
LABEL_MAP = MAPPINGS_DIR / "injury_label_map.csv"
FIRST, LAST = SEASONS[0], SEASONS[-1]
MIN_DAYS = 7  # injuries lasting more than this many days are analysed
MILD_DAYS = 3  # 4–7 days: mild band, kept separately for the > 3-day sensitivity check
SEVERE_DAYS = 28  # > 28 days: severe; 8–28: moderate

LOG = []  # one row per preprocessing operation, for docs/PREPROCESSING_LOG.md


def log(step: str, operation: str, before: int, after: int) -> None:
    LOG.append({"step": step, "operation": operation, "rows before": before, "rows after": after, "removed": before - after})
    print(f"[{step}] {operation}: {before:,} → {after:,} ({before - after:,} removed)")

# %% [markdown]
# ## Step 1. Load and parse injuries
#
# One row per TM injury record (whole careers). Dates parsed; `days` is TM's duration, which equals end − start: the
# days from injury to return (checked in `DECISIONS.md`). Exact repeats (same player, dates and label) are dropped;
# several diagnoses on one absence are kept as separate injuries (decision of Phase 0).

# %%
raw = read_table("tm_injuries")
inj = pd.DataFrame({
    "playerId": raw.playerId,
    "label": raw.name,
    "tm_category": raw.category,
    "start": pd.to_datetime(raw.start, errors="coerce").astype("datetime64[ns]"),
    "end": pd.to_datetime(raw.end, errors="coerce").astype("datetime64[ns]"),
    "days": pd.to_numeric(raw["durationDetails.days"], errors="coerce").astype("Int64"),
    "games_missed": pd.to_numeric(raw.missedGamesCount, errors="coerce").astype("Int64"),
    "tm_season": pd.to_numeric(raw.seasonId, errors="coerce").astype("Int64"),
})
n = len(inj)
inj = inj[inj.start.notna()]
log("2.1", "drop records without a start date", n, len(inj))
n = len(inj)
inj = inj.drop_duplicates(["playerId", "start", "end", "label"]).reset_index(drop=True)
log("2.1", "drop exact repeats (player + start + end + label)", n, len(inj))

# %%
# Check: days = end − start wherever both exist; what is missing.
both = inj.end.notna() & inj.days.notna()
assert ((inj.end - inj.start).dt.days[both] == inj.days[both]).all()
pd.Series({
    "records": len(inj),
    "no end date (open)": inj.end.isna().sum(),
    "no duration": inj.days.isna().sum(),
    "no games-missed count": inj.games_missed.isna().sum(),
    "several diagnoses on one absence (records)": inj.duplicated(["playerId", "start"], keep=False).sum(),
}, name="count").to_frame()

# %% [markdown]
# ## Step 2. Each player's club matches
#
# The injury table has no club. Each player's raw `performance-game` file lists every match of his clubs while he was
# registered, with date, club, competition and his state (`played`, `injured`, `not in squad`, …). This is read once
# (about 4 minutes, raw files are only read) and cached in `data/02_injuries/player_matches.parquet`.
#
# National-team games and rows marked *played for a different team* (a club's matches after he left it) don't tell
# which club he belonged to, so they are left out of `club_matches`.

# %%
MATCHES = OUT_DIR / "player_matches.parquet"


def player_match_rows(path: Path) -> list[tuple]:
    stored = json.loads(path.read_bytes())
    body = stored["body"] if isinstance(stored["body"], dict) else json.loads(stored["body"])
    rows = []
    for g in ((body or {}).get("data") or {}).get("performance") or []:
        gi, gs = g["gameInformation"], g["statistics"]["generalStatistics"]
        rows.append((path.parent.name, gi["date"]["dateTimeUTC"][:10], g["clubsInformation"]["club"]["clubId"],
                     gi["competitionId"], gi["seasonId"], gi["isNationalGame"], gs["participationState"]))
    return rows


if MATCHES.exists():
    pm = pd.read_parquet(MATCHES)
else:
    t0 = time.time()
    files = sorted((RAW_DIR / "transfermarkt" / "player").glob("*/performance-game.json"))
    pm = pd.DataFrame([r for f in files for r in player_match_rows(f)],
                      columns=["playerId", "date", "club_id", "competition_id", "season", "national", "state"])
    pm["date"] = pd.to_datetime(pm.date).astype("datetime64[ns]")
    pm["season"] = pm.season.astype(int)
    pm.to_parquet(MATCHES)
    print(f"read {len(files):,} files in {time.time() - t0:.0f} s")

club_matches = pm[~pm.national & (pm.state != "played for a different team")]

# %%
# Check: rows per state, and how many are used to place players at clubs.
display(pm.state.value_counts().rename("rows").to_frame())
print(f"{pm.playerId.nunique():,} players, {len(pm):,} match rows; {len(club_matches):,} club rows used")

# %% [markdown]
# ## Step 3. Season of each injury
#
# Date rule: 1 July – 30 June. **Exception, summer 2020:** the 2019-20 season ran into July–August after the COVID
# restart, so an injury between 1 July and 31 August 2020 stays in 2019-20 if it starts on or before the last 2019-20
# match of the player's club (any competition, so clubs still in Europe keep August in 2019-20).

# %%
inj["season"] = season_from_date(inj.start)
last_1920 = club_matches[club_matches.season == 2019].groupby("playerId").date.max()
summer_2020 = inj.start.between("2020-07-01", "2020-08-31")
to_1920 = summer_2020 & (inj.start <= inj.playerId.map(last_1920))
inj.loc[to_1920, "season"] = 2019
print(f"{summer_2020.sum():,} records start in July–August 2020; {to_1920.sum():,} kept in 2019-20")

# %%
# Check: agreement with TM's own season label, overall and for the moved records.
agree = (inj.season == inj.tm_season)
pd.Series({"all records": f"{agree.mean():.1%}", "summer-2020 records kept in 2019-20": f"{agree[to_1920].mean():.1%}"},
          name="season = TM seasonId").to_frame()

# %% [markdown]
# ## Step 4. Study window and open injuries
#
# Seasons 2014-15 to 2025-26 only. Injuries without an end date were still open when scraped and have no expected
# return ("Return unknown"), so their severity is unknown: they are dropped.

# %%
n = len(inj)
inj = inj[inj.season.between(FIRST, LAST)]
log("2.4", f"keep seasons {season_key(FIRST)} to {season_key(LAST)}", n, len(inj))
n = len(inj)
inj = inj[inj.end.notna()].reset_index(drop=True)
log("2.4", "drop open injuries (no end date)", n, len(inj))

# %%
# Check: records per season.
inj.season.map(season_key).value_counts().sort_index().rename("records").to_frame().T

# %% [markdown]
# ## Step 5. Club on the injury date
#
# For each injury: the club of the player's last club match on or before the start date **in the same season**; if
# there is none (an injury before his first match of the season), the club of his first match after it in that season.

# %%
keys = club_matches[["playerId", "date", "club_id", "season"]].rename(columns={"season": "match_season"}).sort_values("date")
x = inj.assign(rid=np.arange(len(inj))).sort_values("start")
back = pd.merge_asof(x, keys, left_on="start", right_on="date", by="playerId", direction="backward").set_index("rid").sort_index()
fwd = pd.merge_asof(x, keys, left_on="start", right_on="date", by="playerId", direction="forward").set_index("rid").sort_index()
same_back = back.match_season.eq(back.season).fillna(False).to_numpy(dtype=bool)
same_fwd = fwd.match_season.eq(fwd.season).fillna(False).to_numpy(dtype=bool)
inj["club_id"] = np.where(same_back, back.club_id, np.where(same_fwd, fwd.club_id, None))
inj["club_from"] = np.select([same_back, same_fwd], ["last match before", "first match after"], "none")

# %%
# Check: how the club was found.
inj.club_from.value_counts().rename("records").to_frame()

# %% [markdown]
# ## Step 6. Big Five club-seasons and membership
#
# An injury is kept when the club on its date is a Big Five club-season (from Phase 1) **and** the player belongs to
# that club-season: ≥ 1 appearance for the club in the season (any competition) **or** marked *injured* in ≥ 1 of its
# matches, so players injured for the whole season stay in. The membership table is also the denominator for
# Phase 5 and is saved.

# %%
team_seasons = pd.read_csv(DATA_DIR / "01_entities" / "team_seasons.csv", dtype={"tm_club_id": str})
big5 = team_seasons[["league", "season", "season_key", "tm_club_id", "club"]].rename(columns={"tm_club_id": "club_id"})

stats = read_table("tm_player_stats")
stats = stats.assign(season=stats.season_id.astype(int), appearances=stats.appearances.astype(int),
                     minutes=stats.minutes_played.astype(int))
apps = stats.groupby(["player_id", "club_id", "season"], as_index=False)[["appearances", "minutes"]].sum()
apps = apps.rename(columns={"player_id": "playerId"})
injured_marks = (club_matches[club_matches.state == "injured"].groupby(["playerId", "club_id", "season"]).size()
                 .rename("matches_injured").reset_index())

candidates = apps.merge(injured_marks, on=["playerId", "club_id", "season"], how="outer").fillna(
    {"appearances": 0, "minutes": 0, "matches_injured": 0})
members = big5.merge(candidates, on=["club_id", "season"])
members = members[(members.appearances > 0) | (members.matches_injured > 0)].astype(
    {"appearances": int, "minutes": int, "matches_injured": int, "season": int})
members["clubs_in_season"] = members.groupby(["playerId", "season"]).club_id.transform("nunique")
members = members[["playerId", "league", "season", "season_key", "club_id", "club", "appearances", "minutes",
                   "matches_injured", "clubs_in_season"]].reset_index(drop=True)

# %%
# Check: player-seasons by how they qualify, and players at two Big Five clubs in one season.
qualifies = np.where(members.appearances > 0, "≥ 1 appearance", "injured only (no appearance)")
display(pd.Series(qualifies).value_counts().rename("player-club-seasons").to_frame())
print(f"{members[['playerId', 'season']].drop_duplicates().shape[0]:,} player-seasons; "
      f"{(members.clubs_in_season > 1).sum():,} player-club-seasons at two or more Big Five clubs in the season")

# %%
in_big5 = inj.merge(big5[["club_id", "season"]], on=["club_id", "season"], how="left", indicator="b5")["b5"].eq("both").to_numpy()
is_member = inj.merge(members[["playerId", "club_id", "season"]], on=["playerId", "club_id", "season"], how="left",
                      indicator="m")["m"].eq("both").to_numpy()
inj["scope"] = np.select(
    [inj.club_from.eq("none").to_numpy(), ~in_big5, ~is_member],
    ["no club match that season", "at a non-Big Five club", "Big Five club, not a member"],
    "kept",
)
scope_counts = inj.scope.value_counts().rename("records").to_frame()
n = len(inj)
inj = inj[inj.scope == "kept"].drop(columns="scope").reset_index(drop=True)
log("2.6", "keep injuries at a Big Five club-season the player belongs to", n, len(inj))
scope_counts

# %% [markdown]
# ## Step 7. Label map: proposal and reviewed file
#
# Each raw label gets a **class** (injury or non-injury, with a reason), a **body area** and a **surgery** flag (the
# label describes an operation, e.g. *Knee surgery*, *Arthroscopy*) and an **injury type** (tissue: muscle, ligament/joint,
# tendon, fracture/bone, impact, other; *unspecified* when the label names only a place, e.g. *Knee injury*; added
# 2026-10-25 for injury profiles per style, see `DECISIONS.md`). The proposal comes from ordered keyword rules (first match wins), listed below so each choice can be traced. It is
# written to `data/02_injuries/injury_label_map_proposed.csv`; `mappings/injury_label_map.csv` is created from it on the
# first run and is the **reviewed** file from then on (never overwritten). Labels are sorted by how many > 7-day
# injuries they cover, with the cumulative share, so the review can focus on the top 95%.

# %%
# Non-injuries, checked first: (pattern, reason).
NON_INJURY = [
    (r"^ill$|corona|^virus$|flu$|influenza|^cold$|fever|^infection$|tonsil|angina|bronchitis|pneumonia|mononucleation|"
     r"malaria|chickenpox|shingles|meningitis|tuberculosis|intestinal virus|food poisoning|stomach|quarantin", "illness"),
    (r"^fitness$", "fitness"),
    (r"^rest$", "rest"),
    (r"heart|append|dental|tooth|kidney|cancer|tumor|circulation|allergic|pancreas|intestinal surgery|vein occlusion|"
     r"stroke|blood clots|blood poisoning|cerebral hemorrhage|skin disease|leg skin|abscess|nerval disease|"
     r"balance disorder|hearing damage|cyst on jaw|depression|umbilical", "medical condition"),
    (r"traffic accident|combustion|insect bite", "not from football"),
]
# Body area, first match wins. Ankle before knee (ligament labels name the joint); upper body before head ("humeral head").
BODY_AREA = [
    (r"hamstring|biceps tendon in the thigh", "hamstring"),
    (r"ankle|syndesm", "ankle"),
    (r"knee|cruciate|menisc|patell|tibial head|inner ligament|internal ligament|collateral ligament", "knee"),
    (r"achilles|calf|shin|tibia|fibula|lower leg|peroneus|compartment|broken leg", "calf/achilles/lower leg"),
    (r"foot|\btoe|metatars|tarsus|heel|plantar|arch problems|sole", "foot/toe"),
    (r"femoral neck", "groin/adductor/hip"),
    (r"adductor|groin|pubalg|pubic|inguinal|\bhip\b|pelvi|testic", "groin/adductor/hip"),
    (r"thigh|dead leg|femoral|gluteal", "thigh"),
    (r"shoulder|collarbone|\barm\b|forearm|elbow|wrist|hand|finger|thumb|metacarp|scaphoid|\bribs?\b|chest|abdom|"
     r"lung|pneumothorax|acromio|humer|splen", "upper body"),
    (r"cervical|neck|head|concussion|skull|face|facial|nose|cheek|jaw|eye|whiplash|eardrum|petrous|frontal", "head/neck"),
    (r"back|lumb|spine|vertebra|disc|sciatica|coccyx", "back/spine"),
    (r"muscle|muscular|strain|contracture|stiffness|overstretching", "unspecified muscle"),
]
# Injury type (tissue), first match wins. Groin conditions and bone before the rest ("Pubic bone irritation", "Bone sprain"),
# impact before tendon ("Achilles tendon contusion"), tendon before muscle groups ("biceps tendon in the thigh"). A
# label naming only a muscle group (Hamstring injury, Calf problems, Adductor pain) counts as muscle.
INJURY_TYPE = [
    (r"pubalg|pubic|hernia|inguinal|groin surgery", "other"),
    (r"fractur|broken|crack|fissure|\bbone|stress reaction|splinter|screws", "fracture/bone"),
    (r"bruise|contusion|knock|dead leg|wound|^cut$|lacerat|concussion|whiplash", "impact"),
    (r"tendon|tendin|achilles|bursitis|plantar|heel spur", "tendon"),
    (r"ligament|cruciate|menisc|sprain|syndesm|capsul|cartilage|disloc|contortion", "ligament/joint"),
    (r"muscle|muscular|strain|fiber|contracture|stiffness|overstretching|hamstring|calf|thigh|adductor|groin|"
     r"hip flexor|abdominal", "muscle"),
    (r"lumbago|disc|sciatica|nerve|blockage|inflammation|cyst|edema|pneumothorax|lung|eardrum|obliquity|"
     r"compartment|appendectomy|rupture", "other"),
]
# Labels that describe an operation rather than an injury; the body area is still taken from the label.
SURGERY = r"surgery|arthroscopy|screws"


def first_match(label: str, rules: list[tuple[str, str]], default: str) -> tuple[str, str]:
    for pattern, value in rules:
        if re.search(pattern, label, flags=re.IGNORECASE):
            return value, pattern
    return default, ""


def propose(label: str) -> dict:
    reason, rule = first_match(label, NON_INJURY, "")
    if reason:
        return {"class": "non_injury", "non_injury_reason": reason, "body_area": "", "injury_type": "", "surgery": "",
                "rule": rule}
    area, area_rule = first_match(label, BODY_AREA, "unknown")
    surgery = "yes" if re.search(SURGERY, label, flags=re.IGNORECASE) else "no"
    injury_type, type_rule = first_match(label, INJURY_TYPE, "unspecified")
    return {"class": "injury", "non_injury_reason": "", "body_area": area, "injury_type": injury_type,
            "surgery": surgery, "rule": f"{area_rule} / {type_rule}"}


counts = inj.groupby("label").agg(records=("label", "size"), over_7_days=("days", lambda d: int((d > MIN_DAYS).sum())))
counts = counts.sort_values(["over_7_days", "records"], ascending=False)
counts["share_over_7_days"] = (counts.over_7_days / counts.over_7_days.sum()).round(4)
counts["cum_share_over_7_days"] = counts.share_over_7_days.cumsum().round(4)
proposal = pd.concat([counts.reset_index(), pd.DataFrame([propose(lbl) for lbl in counts.index])], axis=1)
proposal["notes"] = ""
proposal = proposal[["label", "records", "over_7_days", "share_over_7_days", "cum_share_over_7_days", "class",
                     "non_injury_reason", "body_area", "injury_type", "surgery", "rule", "notes"]]
proposal.to_csv(OUT_DIR / "injury_label_map_proposed.csv", index=False)

# %%
# Check: the proposal by class and body area (records over 7 days), and the top labels.
display(proposal.groupby(["class", "non_injury_reason"]).over_7_days.sum().rename("injuries > 7 days").to_frame())
display(proposal[proposal["class"] == "injury"].groupby("body_area").over_7_days.sum().sort_values(ascending=False).to_frame())
display(proposal[proposal["class"] == "injury"].pivot_table(index="body_area", columns="injury_type", values="over_7_days",
                                                            aggfunc="sum", fill_value=0, margins=True))
proposal.head(30)

# %%
def load_reviewed_label_map(proposal: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    """The reviewed label map (created from the proposal on the first run) and labels where it differs."""
    created = not LABEL_MAP.exists()
    if created:
        proposal.to_csv(LABEL_MAP, index=False)
    reviewed = pd.read_csv(LABEL_MAP, dtype=str, keep_default_na=False)
    blank = (reviewed[["label", "class"]] == "").any(axis=1)
    if blank.any():
        raise ValueError(f"{LABEL_MAP.name}: {blank.sum()} rows have no label or class. "
                         "Restore it from git or delete it to recreate it from the proposal.")
    cols = ["label", "class", "non_injury_reason", "body_area", "injury_type", "surgery"]
    diff = proposal[cols].astype(str).merge(reviewed[cols], on="label", how="outer", suffixes=("_proposed", "_reviewed"))
    differs = np.logical_or.reduce([diff[f"{c}_proposed"].fillna("") != diff[f"{c}_reviewed"].fillna("") for c in cols[1:]])
    return reviewed, diff[differs], created


label_map, label_diff, label_map_created = load_reviewed_label_map(proposal)
print("created from proposal" if label_map_created else "reviewed file used as is", "|",
      len(label_diff), "labels differ from the proposal")
label_diff

# %% [markdown]
# ## Step 8. Apply the label map
#
# Every label must be in the reviewed map. Non-injuries are removed from the injury data and kept in their own file,
# so they can be counted separately.

# %%
missing = sorted(set(inj.label) - set(label_map.label))
assert not missing, f"labels missing from {LABEL_MAP.name}: {missing}"
inj = inj.merge(label_map[["label", "class", "non_injury_reason", "body_area", "injury_type", "surgery"]], on="label", how="left")
inj["surgery"] = inj.surgery.eq("yes")
non_injuries = inj[inj["class"] == "non_injury"].reset_index(drop=True)
n = len(inj)
inj = inj[inj["class"] == "injury"].drop(columns=["class", "non_injury_reason"]).reset_index(drop=True)
log("2.8", "remove non-injuries (illness, fitness, rest, medical, not from football)", n, len(inj))

# Fitness absences that start within 3 days after one of the player's injuries ended: reconditioning after injury.
ends = inj[["playerId", "end"]].rename(columns={"end": "injury_end"})
gaps = non_injuries.reset_index().merge(ends, on="playerId")
gaps = gaps[(gaps.start - gaps.injury_end).dt.days.between(0, 3)]
non_injuries["after_injury"] = non_injuries.index.isin(gaps["index"])

# %%
# Check: non-injuries removed, by reason (all durations and > 7 days), and how many start right after an injury.
non_injury_counts = non_injuries.groupby("non_injury_reason").agg(
    records=("label", "size"), over_7_days=("days", lambda d: int((d > MIN_DAYS).sum())),
    right_after_an_injury=("after_injury", "sum"))
non_injury_counts

# %% [markdown]
# ## Step 9. Severity
#
# Injuries lasting **more than 7 days** are the main data (Transfermarkt reports short injuries unevenly across
# leagues). Bands: **moderate** 8–28 days, **severe** more than 28 days. Injuries of **4–7 days** (**mild**) are kept
# in a separate file so Phase 5 can rerun the comparisons with more than 3 days as a sensitivity check.
#
# Some absences of one player overlap (a new injury recorded while the previous one is still running). Their days would
# be counted twice in "days lost", so each injury also gets **`days_merged`**: its days not already covered by an
# earlier-starting injury of the same player. Days lost in Phase 5 use `days_merged`; `days` (the injury's own length)
# still sets the severity band.

# %%
def add_context(df: pd.DataFrame) -> pd.DataFrame:
    """Severity band, league, season key, club name and the multi-club flag."""
    df = df.assign(severity=np.select([df.days > SEVERE_DAYS, df.days > MIN_DAYS],
                                      ["severe (> 28 d)", "moderate (8–28 d)"], "mild (4–7 d)"))
    df = df.merge(big5[["club_id", "season", "league", "season_key", "club"]], on=["club_id", "season"], how="left")
    multi = df.merge(members[["playerId", "season", "club_id", "clubs_in_season"]], on=["playerId", "season", "club_id"], how="left")
    return df.assign(multi_club_season=multi.clubs_in_season.gt(1).to_numpy())


mild = add_context(inj[inj.days.between(MILD_DAYS + 1, MIN_DAYS)].reset_index(drop=True))
n = len(inj)
inj = add_context(inj[inj.days > MIN_DAYS].reset_index(drop=True))
log("2.9", f"keep injuries lasting more than {MIN_DAYS} days ({len(mild):,} of 4–7 days kept separately as mild)", n, len(inj))


def merged_days(df: pd.DataFrame) -> pd.Series:
    """Days of each absence not covered by an earlier-starting absence of the same player (end exclusive, as `days`)."""
    d = df.sort_values(["playerId", "start", "end"])
    covered_until = d.groupby("playerId").end.transform(lambda e: e.cummax().shift())
    start = d.start.where(covered_until.isna() | (d.start >= covered_until), covered_until)
    return (d.end - start).dt.days.clip(lower=0).reindex(df.index)


inj["days_merged"] = merged_days(inj)
overlap = inj.days > inj.days_merged
log("2.9b", f"days lost without double counting: {overlap.sum():,} overlapping injuries lose "
    f"{int((inj.days - inj.days_merged).sum()):,} of {int(inj.days.sum()):,} days", len(inj), len(inj))
assert (inj.days_merged <= inj.days).all() and (inj.days_merged >= 0).all()

# %%
# Check: bands (mild kept separately), duration quantiles, and a sample row.
display(pd.concat([inj, mild]).severity.value_counts().rename("injuries").to_frame())
display(inj[["days", "days_merged"]].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(1).T)
display(inj[overlap].sort_values("days", ascending=False)[["playerId", "start", "end", "days", "days_merged", "label"]].head(5))
inj.head(3)

# %% [markdown]
# ## Step 10. Coverage
#
# The share of injuries without a known body area per season and league. It rises over time in the raw data
# (Phase 0), so every body-area trend must be read next to it.

# %%
def shares(df: pd.DataFrame, by: str) -> pd.DataFrame:
    g = df.groupby(by)
    return pd.DataFrame({
        "injuries > 7 d": g.size(),
        "severe": g.severity.apply(lambda s: (s.str.startswith("severe")).sum()),
        "unknown body area": g.body_area.apply(lambda s: f"{(s == 'unknown').mean():.1%}"),
        "unspecified muscle": g.body_area.apply(lambda s: f"{(s == 'unspecified muscle').mean():.1%}"),
        "surgery": g.surgery.sum(),
    })


by_season = shares(inj, "season_key")
by_league = shares(inj, "league")
body_areas = inj.body_area.value_counts().rename("injuries").to_frame().assign(share=lambda d: (d.injuries / d.injuries.sum()).map("{:.1%}".format))
types = pd.crosstab(inj.body_area, inj.injury_type, margins=True, margins_name="all")
surgeries = inj[inj.surgery].groupby("body_area").size().sort_values(ascending=False).rename("injuries with surgery").to_frame()
display(by_season, by_league, body_areas, types, surgeries)

# %% [markdown]
# ## Step 11. Save outputs and write the report

# %%
cols = ["playerId", "league", "season", "season_key", "club_id", "club", "start", "end", "days", "days_merged", "games_missed",
        "severity", "label", "body_area", "injury_type", "surgery", "multi_club_season", "club_from", "tm_season"]
inj[cols].to_parquet(OUT_DIR / "injuries_clean.parquet", index=False)
mild.assign(days_merged=mild.days)[cols].to_parquet(OUT_DIR / "injuries_mild.parquet", index=False)
non_injuries.to_parquet(OUT_DIR / "non_injuries.parquet", index=False)
members.to_parquet(OUT_DIR / "player_club_seasons.parquet", index=False)
log_table = pd.DataFrame(LOG)
log_table.to_csv(OUT_DIR / "preprocessing_counts.csv", index=False)
log_table

# %%
reviewed_note = ("Created from the proposal on this run: **not reviewed yet**." if label_map_created
                 else f"Reviewed file used; {len(label_diff)} labels differ from the proposal.")
top95 = proposal[proposal.cum_share_over_7_days.shift(fill_value=0) < 0.95]
out = [
    "# Phase 2: Injury cleaning and body-area mapping",
    "",
    f"Generated {date.today().isoformat()} by `notebooks/02_injuries.ipynb`, where each step is shown with its checks.",
    "",
    "## Key findings",
    "",
    f"- **{len(inj):,} injuries lasting more than 7 days** remain, tied to {inj[['playerId', 'season']].drop_duplicates().shape[0]:,} "
    f"player-seasons at Big Five clubs; {(inj.severity.str.startswith('severe')).mean():.1%} are severe (> 28 days).",
    f"- **Membership:** {len(members):,} player-club-seasons belong to a Big Five club-season "
    f"({(members.appearances == 0).sum():,} of them only through matches marked injured).",
    f"- **Non-injuries removed:** {len(non_injuries):,} records ({int(non_injury_counts.over_7_days.sum()):,} over 7 days), "
    "kept separately below. *Fitness* absences stay out of the injury count and are a secondary outcome in Phase 5; "
    f"{int(non_injury_counts.loc['fitness', 'right_after_an_injury'])} of {int(non_injury_counts.loc['fitness', 'records'])} "
    "start within 3 days after an injury ended (reconditioning).",
    f"- **Mild injuries (4–7 days):** {len(mild):,} kept separately for the > 3-day sensitivity check in Phase 5.",
    f"- **Unknown body area:** {(inj.body_area == 'unknown').mean():.1%} of injuries overall; per season below.",
    f"- **Label map:** {len(proposal)} labels; {len(top95)} labels cover 95% of injuries over 7 days. {reviewed_note}",
    "",
    "## 1. Steps and row counts",
    "",
    md_table(log_table[["step", "operation", "rows before", "rows after", "removed"]], index=False),
    "",
    "Records by where the injury happened (step 6, all durations):",
    "",
    md_table(scope_counts.rename_axis("scope")),
    "",
    "## 2. Non-injuries",
    "",
    md_table(non_injury_counts.rename_axis("reason")),
    "",
    "## 3. Body areas (injuries > 7 days)",
    "",
    md_table(body_areas.rename_axis("body area")),
    "",
    "Injury type (tissue) by body area, injuries over 7 days (*unspecified*: the label names only a place):",
    "",
    md_table(types.rename_axis("body area")),
    "",
    f"Injuries whose label describes an operation (surgery flag): {int(inj.surgery.sum()):,}, by body area:",
    "",
    md_table(surgeries.rename_axis("body area")),
    "",
    "## 4. Coverage per season",
    "",
    md_table(by_season.rename_axis("season")),
    "",
    "## 5. Coverage per league",
    "",
    md_table(by_league.rename_axis("league")),
    "",
    "## 6. Outputs",
    "",
    f"- `mappings/injury_label_map.csv`: the reviewed label map (in git). {reviewed_note}",
    f"- `data/{PHASE}/injuries_clean.parquet`: {len(inj):,} injuries > 7 days with club-season, severity, body area and surgery flag.",
    f"- `data/{PHASE}/injuries_mild.parquet`: {len(mild):,} injuries of 4–7 days (sensitivity check only).",
    f"- `data/{PHASE}/non_injuries.parquet`: {len(non_injuries):,} removed non-injury records with reason and `after_injury` flag.",
    f"- `data/{PHASE}/player_club_seasons.parquet`: {len(members):,} player-club-seasons (membership, appearances, minutes), "
    "the denominator for Phase 5.",
    f"- `data/{PHASE}/player_matches.parquet`: every player's club matches from the raw files (cache).",
    f"- `data/{PHASE}/preprocessing_counts.csv`: the row counts above.",
    "",
]
(REPORTS_DIR / "02_injuries.md").write_text("\n".join(out), encoding="utf-8")
print("wrote", REPORTS_DIR / "02_injuries.md")
