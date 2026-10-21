# Decisions

| Date | Decision | Reason |
|---|---|---|
| 2026-10-21 | Analysis libraries go in a uv dependency group `analysis`, not the main dependencies. | Keeps the scraper's Docker image small; `uv run --group analysis` for all analysis work. |
| 2026-10-21 | Canonical season key `"2014-15"`; date-based season runs 1 July to 30 June (`src.load.season_key`, `season_from_date`). | Plan, Phase 1. Already used in the Phase 0 audit. TM `seasonId` agrees with the date season for 98.3% of in-window injuries. |
| 2026-10-21 | An injury event is `playerId + start + end + label`, not `injuryId`. | `injuryId` turned out to be an injury-type code shared across players. |
