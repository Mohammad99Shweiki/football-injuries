# Design brief: Analysis Studio

Paste everything below the line into Claude Design. Attach `scraper/dashboard/src/styles/tokens.css` and, if possible,
screenshots of the existing run console (`/`) and validation report (`/validation`) so the new screens match them.

---

## What to design

**Step 2 · Analysis** of an existing local web app. The app already has **Step 1 · Scraping** (a live "Run console"
and a "Validation report" for the data collection). Step 2 adds, in the same app: the **project progress** (where the
study stands, phase by phase), the **Analysis Studio** where one analyst (a master's student) walks the data mining
project **step by step** from parsed tables to the final report (runs each step, **inspects what it produced through
tables and charts**, reviews and approves the hand-checked inputs, finalises), and the **results explorer** that
presents the findings. It replaces reading Jupyter notebooks and two separate web pages. It must use the **same
visual language** as Step 1: a tactics-board / chalkboard theme (dark board, chalk-white text, coloured magnets as status
markers, hand-drawn chalk annotations and arrows, a small mascot "Chalky"). Use the attached `tokens.css` for every
colour, font, spacing, radius, shadow and duration.

**Project in one line:** playing style × injuries in Europe's Big Five football leagues, 2014/15–2025/26. Clubs are
clustered by how they attack and how they defend; players inherit their team's style; injuries are compared across
styles, seasons and leagues.

## Who and how

- One user, on a laptop (1280–1440 px), sometimes a tablet (768 px); must still work at 375 px.
- Goes phase by phase, often stops to check numbers, re-runs a step after changing something, and approves review
  points. Also uses it to **present** the work to a supervisor, so finished results must look clean and readable.
- Every number is real and reproducible; the UI never invents or edits results, it runs the steps and shows them.
  **Every number on screen comes from a run record or the Phase 6 export; the sample values below are placeholders.**
- Course constraint: clustering is the only data mining method. Use the words "cluster membership", "shrunk rate
  ratio", "association"; never "prediction", "model", "risk score" or "probability of injury".

## The pipeline the UI walks (real structure)

| Phase | Steps | Review point |
|---|---|---|
| 0 Data audit | inventory, coverage grids (league × season), missingness, injury records | – |
| 1 Entity resolution | 11 steps: team-seasons per source → name normalising → scoring → matching → club map → reviewed map → team-season table → match tables → fixture verification → season labels → report | **Team map** (168 clubs; 8 flagged) |
| 2 Injury cleaning | 11 steps: parse → per-match records → season rule → window → club on date → Big Five membership → label map → apply → severity → coverage → report | **Injury label map** (315 labels → class, body area, surgery) |
| 3 Features | 12 steps: keys → Understat → team statistics → Football-Data → workload → rotation → join → season/league means → correlations → standardise → phase dimensions → report | – |
| 4 Clustering | k = 2…10 per phase (attack, defence): quality measures, stability, Ward, GMM; profiles; names; combinations | **Choose k and names** |
| 5 Injury analysis | ~18 steps: rates, attack × defence grid, body areas, seasons, leagues, adjustments, sensitivity, style cards, evolution, decomposition, stories | – |
| 6 Report | summary text, consistency checks, figures, results dashboard data | **Finalise** |

Each **step** has: a short note (what and why), a status (not run / running / passed / failed / stale because
something upstream changed), checks (assertions with pass/fail and the numbers they test), outputs (tables, charts,
files), a log row (rows before → after, e.g. "82,075 → 24,581 injuries"), and links to the decisions that shaped it.

## Screens (frames to produce)

0. **App navigation** across both steps: a top-level switch "1 · Scraping" (Run console, Validation report: existing
   screens, unchanged) and "2 · Analysis" (Progress, Studio, Results, Logs). It must read as one product: Scraping is
   finished and feeds Analysis, so show that hand-off (e.g. Scraping marked done with its headline "27,197 files ·
   0 failed", an arrow into Analysis). Deep-linkable routes (/scraping, /scraping/validation, /analysis,
   /analysis/studio/phase-2/step-7, /analysis/results).
1. **Pipeline overview / Progress** (home of Step 2). It doubles as the project's progress page shown to the
   supervisor: the research question in two sentences, key numbers (1,170 team-seasons, 24,581 injuries > 7 days,
   4 × 4 styles), the headline as an association with its adjustments ("Positional possession: league-adjusted rate
   ratio 1.24; 1.11 after team strength; 1.04 per match played — association, not cause") and a caveat chip
   ("Transfermarkt under-reports injuries; leagues record differently"), then all 7 phases as a horizontal play diagram (like set-piece arrows on a board), each
   phase a magnet showing status and its headline count (e.g. "1,170 team-seasons", "24,581 injuries > 7 days").
   Review points shown as flags on the path. Actions: Run all, Run from here, Open phase. **Run all** reruns only stale phases in order, stops at the first failed
   check or unapproved review point, never writes to the hand-reviewed mappings, and is disabled while a scrape or
   another run is in progress (one run at a time). A "what changed since last
   run" strip (e.g. "label map edited → phases 2, 5, 6 stale").
2. **Phase view**. Left: the step list as a vertical sequence (numbered, status magnets, duration). Main: the selected
   step. Sticky header with phase name, progress, Run phase / Run step. The flow is linear: Next step and Previous
   step at the bottom, so the user can go through the whole phase without the list.
3. **Step inspector** (the core screen), in tabs or stacked panels:
   - **Note**: what the step does and why (2–4 sentences), decisions that apply (chips linking to the decision log).
   - **Checks**: each assertion as a row: pass/fail magnet, plain-language statement, the tested values
     ("21,589 of 21,589 matches found in Transfermarkt"). A failed check is the loudest thing on the page.
   - **Output tables**: a data grid: sortable, filterable, column types shown, numbers right-aligned with tabular
     figures, pagination or virtual scroll for 40k-row tables, row count and "showing x of y", copy/download CSV.
     A **summary diff** when a table changed since the last run (rows, columns and key counts vs the previous run).
   - **Charts**: the step's charts rendered large, with hover values; a toggle to see the table behind each chart.
   - **Log**: rows before → after with a small funnel/waterfall (e.g. 82,075 → 71,374 → 37,554 → 32,088 → 24,581,
     each drop labelled with why).
4. **Review & approve** (one per review point). Example: the injury label map: 315 rows, columns label, injuries,
   share, cumulative share, class, body area, surgery, rule, notes. Inline editing with dropdowns (body area from 12
   values), filters ("only labels covering 95%", "only flagged"), a side panel explaining the rule that produced each
   suggestion, an estimated summary of what changes downstream from label counts ("3 labels moved to knee → about 41
   injuries"), and an **Approve** button that records the date, the file hash and the diff against the proposal, adds
   a decision-log row and marks downstream phases stale. Results change only when the user reruns. Also the team map (168 clubs, 8 flagged with name
   scores 54–75 and fixture evidence "all 21,589 matches confirmed").
5. **Clustering studio** (Phase 4, needs the most visual care). For each phase of play (attack / defence switch):
   - metric small multiples vs k (elbow, silhouette, Davies–Bouldin, Calinski–Harabasz, weakest-cluster stability),
     the chosen k marked;
   - the **cluster map** (2-D scatter of 1,170 team-seasons, coloured by cluster, hover shows club and season; click a
     dot to open its profile);
   - **centroid heatmap** (clusters × 4 dimensions, diverging colour);
   - **algorithm agreement**: K-means vs Ward vs Gaussian mixture (independent checks: agreement scores and a matrix
     showing how clusters map) and the consensus as a stability summary; sensitivity clusterings (k = 3, style
     relative to the league-season) shown as alternatives;
   - **fuzzy membership**: per team-season membership bars (e.g. Napoli 2022-23: 0.82 Positional possession, 0.11
     Build-up into the box);
   - **style cards** (name, how it plays, key numbers vs average, typical teams per era). Names are **generated by a
     naming rule** (shown, e.g. "highest possession → Positional possession"); changing the rule or k is a review edit
     with an approval, never free text. **Confirm k and names** records the choice in a tracked file and a decision
     row.
6. **Results explorer** (Phase 5–6, presentation quality). Tabs Styles / Evolution / Injuries / Trends / Leagues;
   filters at top: phase of play (attack / defence), league, and the selected style (chip, clearable). Cards:
   - cluster map (dots shaded by fuzzy membership: faint = borderline; hover: "Napoli 2022-23 · Positional possession
     0.82 · next: Build-up 0.11");
   - style cards (how it plays in football words, key numbers vs average, clear members, typical teams per era,
     injury RR and "+12.4 injuries per 100 player-seasons");
   - style shares over time (stacked area) and the 8 style dimensions over seasons (small multiples);
   - rate ratios with 95% CIs (dot + whisker) next to the absolute excess, with an adjustment switch showing the
     nested versions side by side (league × season → + team strength → + age × position) and an exposure switch
     (per player-season / per team match);
   - attack × defence grid (heatmap, shrunk values with raw on hover, small cells greyed);
   - body areas (heatmap, "x/5 leagues", ★ for patterns that survive the permutation test with multiple-testing
     correction);
   - who carries the excess: RR by position and age band per style (heatmap);
   - injury trend: single seasons as dots with CI band plus a 3-season rolling line, calendar events annotated
     (COVID restart, five substitutes, mid-season World Cup, new Champions League format);
   - decomposition bars (style mix vs within styles) and one story per league.
   Clicking a style anywhere (legend, card, dot, cell) filters every card.
7. **Logs**: Decisions (date, decision, reason; searchable, linked from steps) and Preprocessing log (step, type,
   input, operation, rows before → after, output). Timeline layout.
8. **Finalise** (Phase 6): checklist of everything the report needs (all checks passed, review points approved,
   numbers in the summary match the data, figures present), report preview (markdown rendered), figure gallery, and a
   "Finalise" action that writes a release manifest (date, every phase's run id and input hashes, git commit, seed).

## States and behaviour to show

- Running: progress per step (current step, elapsed time); the rest of the UI stays usable.
- Blocked: "a scrape is running: analysis runs are disabled" and "analysis dependencies missing: start with
  `uv run --group analysis`".
- Failed step: what failed (assertion and values), the traceback collapsed, "Open in notebook" escape hatch.
- Stale: a phase or step whose inputs changed since its last run, with the reason.
- Empty: a phase never run ("Run phase 2 to see its outputs").
- Long tables: 632,170 rows (player stats) must stay responsive (server-side pages, virtualised).
- At 375 px the clustering studio and review screens are read-only.
- Light theme optional; the board theme is primary. Respect reduced motion.

## Data contracts (what each screen reads)

All JSON over a local API (`/api/analysis/...`). Shapes, simplified:
- **Phase list:** `[{id: "02", title, status: "passed"|"failed"|"stale"|"not_run"|"running", stale_reason, run_id,
  finished, duration_s, headline: {label, value}, review: {name, approved, approved_at} | null, steps: [...]}]`
- **Step:** `{id: "2.7", title, note (markdown), status, duration_s, decisions: [{date, decision}], checks: [{id,
  statement, passed, values: {…}}], log: [{op, type, before, after, unit}], outputs: [{name, kind: "table"|"figure",
  rows, columns}], figures: [url]}`
- **Table page:** `{columns: [{name, type}], rows: [[…]], total, offset, limit}` with sort and filter parameters.
- **Mapping:** `{rows, columns, proposal_diff: [{key, field, proposed, reviewed}], approval: {date, hash} | null}`.
- **Run record:** `{run_id, started, finished, git_sha, dirty, seed, inputs: {name: hash}, steps: [...]}`.
- **Results:** the ten-plus Phase 6 files (`cluster_map`, `styles`, `style_shares`, `dimension_trends`, `injury_rr`,
  `grid`, `body_areas`, `breakdown`, `season_trend`, `decomposition`, `league_stories`): arrays of flat records.
- **Logs:** decisions `[{date, decision, reason}]`, preprocessing `[{id, date, type, input, operation, rows, output,
  where}]`.

## Sample real data to use in mocks

- Phase 2 funnel: 82,075 records → 82,068 parsed → 71,374 in window → 71,195 closed → 37,554 at a Big Five club →
  32,088 injuries (5,466 non-injuries) → 24,581 lasting more than 7 days (13,588 moderate, 10,993 severe).
- Attacking styles (placeholders, being recomputed): Positional possession (174 team-seasons, injury rate ratio 1.24,
  1.11 after strength, 1.04 per match), Build-up into
  the box (355, 1.01), Counter-attack (279, 0.90), Direct play (362, 0.95).
- Defensive styles: High press, high line (245, 1.14), Compact mid-block (289, 1.03), Aggressive duel press (286,
  0.93), Low block (350, 0.94).
- Clustering, attack phase: k = 4, silhouette 0.22, weakest-cluster stability 0.64; defence: 0.21, 0.80.
- Style shift 2014–18 → 2022–26: Positional possession 6% → 25%, Direct play 40% → 18%, Low block 19% → 41%.

## Deliverables

Frames for screens 0–8 at 1440 px, plus the step inspector and clustering studio at 768 and 375 px; a component sheet
(magnet status badge, check row, data grid, CI dot-whisker, heatmap cell, step list item, review row with inline
editor, approve bar, stale banner); and notes on interactions. Keep the tactics-board identity; make data screens
calm and legible (results are presented to a supervisor), with the playful elements (chalk arrows, Chalky) limited to
the overview and empty/finished states.
