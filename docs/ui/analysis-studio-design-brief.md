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
   4 × 4 styles, headline result "Positional possession: 24% more injuries, 95% CI 18–30%"), then all 7 phases as a horizontal play diagram (like set-piece arrows on a board), each
   phase a magnet showing status and its headline count (e.g. "1,170 team-seasons", "24,581 injuries > 7 days").
   Review points shown as flags on the path. Actions: Run all, Run from here, Open phase. A "what changed since last
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
     A **diff view** when a table changed since the last run (added / removed / changed rows highlighted).
   - **Charts**: the step's charts rendered large, with hover values; a toggle to see the table behind each chart.
   - **Log**: rows before → after with a small funnel/waterfall (e.g. 82,075 → 71,374 → 37,554 → 32,088 → 24,581,
     each drop labelled with why).
4. **Review & approve** (one per review point). Example: the injury label map: 315 rows, columns label, injuries,
   share, cumulative share, class, body area, surgery, rule, notes. Inline editing with dropdowns (body area from 12
   values), filters ("only labels covering 95%", "only flagged"), a side panel explaining the rule that produced each
   suggestion, a summary of what changes downstream ("3 labels moved to knee → 41 injuries"), and an **Approve**
   button that records who/when and marks downstream phases stale. Also the team map (168 clubs, 8 flagged with name
   scores 54–75 and fixture evidence "all 21,589 matches confirmed").
5. **Clustering studio** (Phase 4, needs the most visual care). For each phase of play (attack / defence switch):
   - metric small multiples vs k (elbow, silhouette, Davies–Bouldin, Calinski–Harabasz, weakest-cluster stability),
     the chosen k marked;
   - the **cluster map** (2-D scatter of 1,170 team-seasons, coloured by cluster, hover shows club and season; lasso
     or click a dot to open its profile);
   - **centroid heatmap** (clusters × 4 dimensions, diverging colour);
   - **algorithm agreement**: K-means vs Ward vs GMM (agreement scores, and a matrix showing how clusters map);
   - **soft membership**: per team-season probability bars (e.g. Napoli 2022-23: 0.92 Positional possession);
   - **style cards** (name, how it plays, key numbers vs average, typical teams per era); names editable with a rule
     explanation; **Confirm k and names** button.
6. **Results explorer** (Phase 5–6, presentation quality). Tabs Styles / Evolution / Injuries / Trends / Leagues;
   filters at top: phase of play (attack / defence), league, and the selected style (chip, clearable). Cards:
   - cluster map (dots shaded by fuzzy membership: faint = borderline; hover: "Napoli 2022-23 · Positional possession
     0.82 · next: Build-up 0.11");
   - style cards (how it plays in football words, key numbers vs average, clear members, typical teams per era,
     injury RR and "+12.4 injuries per 100 player-seasons");
   - style shares over time (stacked area) and the 8 style dimensions over seasons (small multiples);
   - rate ratios with 95% CIs (dot + whisker) next to the absolute excess;
   - attack × defence grid (heatmap, shrunk values with raw on hover, small cells greyed);
   - body areas (heatmap, "x/5 leagues", ★ for the 9 patterns that survive multiple-testing correction);
   - who carries the excess: RR by position and age band per style (heatmap);
   - injury trend: single seasons as dots with CI band plus a 3-season rolling line, calendar events annotated
     (COVID restart, five substitutes, mid-season World Cup, new Champions League format);
   - decomposition bars (style mix vs within styles) and one story per league.
   Clicking a style anywhere (legend, card, dot, cell) filters every card.
7. **Logs**: Decisions (date, decision, reason; searchable, linked from steps) and Preprocessing log (step, type,
   input, operation, rows before → after, output). Timeline layout.
8. **Finalise** (Phase 6): checklist of everything the report needs (all checks passed, review points approved,
   numbers in the summary match the data, figures present), report preview (markdown rendered), figure gallery, and a
   "Finalise" action that freezes a version (date, run id).

## States and behaviour to show

- Running: progress per step, elapsed time, live log lines; the rest of the UI stays usable.
- Failed step: what failed (assertion and values), the traceback collapsed, "Open in notebook" escape hatch.
- Stale: a phase or step whose inputs changed since its last run, with the reason.
- Empty: a phase never run ("Run phase 2 to see its outputs").
- Long tables: 632,170 rows (player stats) must stay responsive (virtualised).
- Light theme optional; the board theme is primary. Respect reduced motion.

## Sample real data to use in mocks

- Phase 2 funnel: 82,075 records → 82,068 parsed → 71,374 in window → 71,195 closed → 37,554 at a Big Five club →
  32,088 injuries (5,466 non-injuries) → 24,581 lasting more than 7 days (13,588 moderate, 10,993 severe).
- Attacking styles: Positional possession (174 team-seasons, injury rate ratio 1.24, 95% CI 1.18–1.30), Build-up into
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
