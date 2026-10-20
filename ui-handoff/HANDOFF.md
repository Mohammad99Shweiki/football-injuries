# Handoff Spec: Scraper Run Console

Build brief for the coding agent. It sits next to `scraper-spec.md` (the data-collection spec). That spec says **what** to collect; this one says **how the run is shown**.

Design canvas (source of truth for visuals): https://claude.ai/artifact/3WsNh8ZBRoR1NrLqnEy184 (private to the owner; ask them to share it if you can't open it).

## 0. What's in this folder

| Path | What it is |
|---|---|
| `HANDOFF.md` | This spec. |
| `tokens.css` | Every colour, font, spacing, radius, shadow and duration as CSS custom properties. Use these, not raw values. |
| `design/run-console.dc.html` | Screen 1: live run dashboard, with the mascot built in. |
| `design/validation-report.dc.html` | Screen 2: report shown after each run. |
| `design/mascot-chalky.dc.html` | Mascot reference sheet: every state, plus a demo player. |
| `assets/photos/*.jpg` | 14 player photos (Wikimedia Commons, CC/PD). |
| `assets/logos/*.png` | 5 league logos + Transfermarkt (Wikimedia Commons, public domain). |
| `assets/credits.json` | Author, licence and source URL for every image. **Required for attribution.** |

### Reading the `.dc.html` files

They are Design Component files: plain HTML with inline styles, a `<helmet><style>` block for classes and keyframes, and a small template language:

- `{{path}}` inserts a value computed in `renderVals()` (the `<script type="text/x-dc">` at the bottom of each file).
- `<sc-for list="{{xs}}" as="x">` repeats markup once per item.
- `<sc-if value="{{flag}}">` renders markup only when the flag is true.
- `onClick="{{fn}}"` binds a handler returned by `renderVals()`.

Treat them as **pixel-exact references**, not runnable code. Port them to the stack below. All sample numbers in `renderVals()` are mock data; replace them with the live data contract in §2.

Images in the design files are referenced as `/_blob/<id>`. Map each one to the local file:

| Blob id (prefix) | Local file | | Blob id (prefix) | Local file |
|---|---|---|---|---|
| `96032199…` | logos/pl.png | | `ca7d9912…` | photos/vandijk.jpg |
| `f2af1593…` | logos/laliga.png | | `e0182480…` | photos/elliott.jpg |
| `39448aa6…` | logos/seriea.png | | `2d5371cf…` | photos/debruyne.jpg |
| `14feb8bf…` | logos/bundesliga.png | | `10cb23af…` | photos/timber.jpg |
| `d555ed1d…` | logos/ligue1.png | | `79fbfe30…` | photos/dembele.jpg |
| `77585013…` | logos/transfermarkt.png | | `c21c51bc…` | photos/fati.jpg |
| `a07f784a…` | photos/militao.jpg | | `3e64334b…` | photos/alaba.jpg |
| `68621829…` | photos/carvajal.jpg | | `675b1f14…` | photos/zaniolo.jpg |
| `a52e379d…` | photos/milik.jpg | | `c5584dcd…` | photos/chiesa.jpg |
| `87625c75…` | photos/wirtz.jpg | | `9fcc6155…` | photos/neymar.jpg |

## 1. Architecture

Keep it light and local. No build step is needed.

```
project/
  dashboard/
    index.html          # run console (screen 1)
    validation.html     # validation report (screen 2)
    styles.css          # imports ../ui-handoff/tokens.css, plus the classes/keyframes from the designs
    app.js              # polling, rendering, controls
    chalky.js           # mascot rig: mood → SVG props (port of chalky() in run-console.dc.html)
    assets/             # copy of ui-handoff/assets
  collect/status.py     # shared, thread-safe status object; writes data/status.json
  serve.py              # stdlib http.server bound to 127.0.0.1, serves dashboard/ + /api/*
```

- `run_all.py` starts `serve.py` in a background thread and prints `Dashboard: http://127.0.0.1:8765`.
- Each collector updates the shared status object on every request (counts, last manifest row, rate-limiter state). A writer flushes `data/status.json` at most once per second, **atomically** (write a temp file, then `os.replace`).
- The dashboard polls `GET /api/status` every **1 s**. It polls `GET /api/validation` once, when the run phase becomes `finished`.
- Controls: `POST /api/control` with `{"action": "pause" | "resume" | "smoke_test" | "requeue", "ids": [...]}`. Bind to 127.0.0.1 only. There is no auth because it never leaves localhost.
- `--dry-run` and `--limit N` are CLI flags (spec §2). The console **displays** them; on the controls row they can only be changed before a run starts. Disable them while a run is active.
- Fonts: Google Fonts (`IBM Plex Sans`, `IBM Plex Mono`, `Caveat`). If offline, fall back to the system stacks in `tokens.css`.

## 2. Data contract

### `GET /api/status` (run console)

```json
{
  "phase": "idle | running | paused | finished",
  "started_at": "2026-10-20T10:00:00Z",
  "elapsed_s": 2472,
  "target_s": [5400, 7200],
  "flags": {"dry_run": false, "limit": null},
  "sources": {
    "fd": {"state": "done|running|paused|queued|failed", "done": 60, "total": 60, "total_is_estimate": false,
           "rate": "1 / 2 s", "cache_hits": 0, "failed": 0, "note": "…"},
    "us": {"…": "same shape"},
    "tm": {"…": "same shape"}
  },
  "tm_steps": [
    {"id": "T1", "label": "Clubs per league-season", "call": "competition_clubs(comp_id, season_id)",
     "done": 60, "total": 60, "total_is_estimate": false, "sub": "done", "state": "done|running|queued"}
  ],
  "tm_unique_players": 9640,
  "limiter": {
    "concurrency": 8, "phase": 2, "req_per_s": 6.4, "target": "6–8 req/s",
    "clean_streak": 1284, "rampup_needs": 500,
    "history_rps": [3.8, 4.0, "… 30 values, one per minute, oldest first"],
    "backoff_until": null,
    "last_backoff": {"at_elapsed_s": 1390, "status": 429, "waf_action": "challenge", "paused_s": 60, "concurrency_from": 8, "concurrency_to": 4}
  },
  "coverage": {
    "fd": [["done", "…12 seasons"], "…5 leagues"],
    "us": [["…"]],
    "tm": [["…"]]
  },
  "manifest_tail": [
    {"fetched_at_elapsed_s": 2472, "source": "tm", "url": "…", "status": 200, "bytes": 3912, "result": "fetched|replayed|retry n/5|failed"}
  ],
  "smoke_test": [
    {"key": "t2_season", "state": "confirmed|verify|failed", "title": "…", "detail": "…"}
  ]
}
```

Rules:
- `coverage` cell values: `done | running | queued | failed`. Leagues in the order PL, LaLiga, Serie A, Bundesliga, Ligue 1; seasons 2014/15 → 2025/26.
- For Transfermarkt, a cell is a club-season's player-level work (T3–T5). It is `done` when all of its players' calls are stored.
- `manifest_tail` holds the newest **50** rows, newest first. The UI shows 8 at a time; add a "Show more" button if you have time.
- `total_is_estimate: true` renders the total with a leading `~` (for example `~21,000`).

### `GET /api/validation` (validation report)

```json
{
  "finished_at": "…", "run_time_s": 6360,
  "summary": [{"label": "Football-Data CSVs", "value": "60 / 60", "sub": "…", "state": "pass|attention"}],
  "matches": {"found": [[380, "…12"], "…5"], "expected": [[380, "…"]], "known_exceptions": [{"league": 4, "season": 5, "note": "COVID, stopped early"}]},
  "failures": [{"id": "…", "source": "tm", "url": "…", "code": 429, "why": "WAF challenge after 5 tries", "attempts": 5}],
  "clubs": [{"league": 0, "expected": "20 every season", "found_ok": 12, "of": 12}],
  "injuries_per_season": [1820, "…12"],
  "zero_injury_players": 0,
  "dod": [{"title": "…", "state": "done|open", "status": "…"}],
  "documented_quirks": ["Serie A shot counts include blocked shots from 2018/19."]
}
```

Expected counts and exceptions come straight from `scraper-spec.md` §7: 380 per season; Bundesliga 306; Ligue 1 306 from 2023/24 and about 279 in 2019/20; 20 clubs per season, but 18 for Bundesliga and 18 for Ligue 1 from 2023/24.

## 3. Screen 1: Run console (`design/run-console.dc.html`)

### Overview
A single page you watch for about 2 hours while three collectors run in parallel. It should answer "is it healthy, how far along, what broke" at a glance, and be fun to leave open.

### Layout
- Fluid page: content `max-width: var(--page-max)`, centred, side padding `var(--page-gutter)`, vertical gap `var(--space-7)` between sections.
- Rows that pair a wide and a narrow panel use flex-wrap: wide `flex: 999 1 560–640px`, narrow `flex: 1 1 340–360px`. They stack below about 940px.
- Stacking order, back to front:
  1. board (dot grid)
  2. grain
  3. cursor spotlight
  4. scattered photo prints
  5. header
  6. content panels

  Panels are semi-transparent (`--panel`), so prints show faintly through them.

### Sections, in order

| # | Section | Data | Notes |
|---|---|---|---|
| Header | Title, Chalky widget, run status pill, elapsed time | `phase`, `elapsed_s`, overall % | Chalky widget spec in §5. Elapsed time as `hh:mm:ss`; next to it, a handwritten "target 1½–2 h". |
| 01 Scope | 5 league stickers (logo + name + `E0 · EPL · GB1` codes) | static | Hover shows all three codes in a tooltip. |
| 01 Controls | `--dry-run` checkbox, `--limit N` input, Pause/Resume, Run smoke test | `flags`, `phase` | Each flag has a dashed-yellow helper note **under** it (copy in §8). |
| 02 Collectors | 3 cards: FD, US, TM | `sources.*` | Each card has a site logo tile (TM: real logo; FD and US: typeset name tile), done/total, progress bar, rate, cache hits, failed, and a note. A magnet pin at the top-left of the card shows its state colour. |
| 03 The play | T1–T5 rows with magnet badge, label, SDK call, bar, count | `tm_steps`, `tm_unique_players` | Handwritten chalk arrows between T1→T2 and T2→T3 ("60 league-seasons → 1,150 club-seasons", "dedupe → N unique players, then T3–T5 together"). |
| 04 Tempo | Concurrency, req/s, 30-bar sparkline, clean streak, last back-off | `limiter` | Bars where rps = 0 are `--warn`; others `--run`. A "WAF pause" note points at the first zero bar. |
| 05 The board | League × season grid of magnets, with source tabs FD/US/TM | `coverage` | done = `--magnet-ok`, running = `--magnet-run`, failed = `--magnet-fail` with "!", queued = dashed empty circle. The league logo sits at the start of each row. |
| 06 Match log | manifest tail table, filter tabs All/FD/US/TM | `manifest_tail` | Columns: fetched_at, Source (logo tile + name), url (ellipsis), status (200 = `--ok-text`, else `--warn-text`), bytes (right-aligned), Result. |
| 07 Scouting notes | Smoke-test findings | `smoke_test` | Pill: Confirmed = ok tint, Verify = warn tint. |
| Footer | Photo + logo credits | `assets/credits.json` | **Must stay.** CC BY-SA requires attribution. |

### Background prints (decoration)
- 14 disposable-camera prints of notable injuries in the study window. Each has: photo (sepia-toned), flash glare, vignette, grain, orange date stamp `'YY MM DD`, league logo sticker, a red body-area tag, an "again!" sticker if the injury recurred, a handwritten caption, the match and date, and a photo credit.
- Data lives in `MOMENTS` and `PHOTO` in the design file. **One print per player**, and every player is distinct.
- Placement is a seeded, jittered 4-column grid (seed 7 on the console, 31 on the report), rotation ±13°, scale 0.86–1.10. Keep the seeded generator so the layout is stable between reloads.
- **Prints start below the header** (console y ≥ 240px, report y ≥ 200px), so none sits behind Chalky or the header controls.
- **Hidden until hover.** Each print rests at opacity 0.05, a faint ghost. It fades to 1 (350 ms) when the cursor is within **190px** of its centre, or when it's hovered directly. The proximity check uses the same throttled cursor position as the board spotlight, so prints still reveal through the semi-transparent panels. With no cursor (touch screens), prints stay at 0.05; on touch, a tap reveals them. With reduced motion, keep the opacity change and drop the transition.
- `aria` group label: "Notable injuries from the 2014/15–2025/26 seasons". Each `<img>` has alt "Photo of {player}".
- ✅ All 14 injury facts were checked against news reports on 2026-10-20 (sources in §16). Two captions were corrected during the check: SPAL 2–3 Napoli (Milik) and Leverkusen 0–1 Köln (Wirtz).

## 4. Screen 2: Validation report (`design/validation-report.dc.html`)

Shown when `phase == "finished"`. It is linked from the console, and printed to the terminal as text (spec §7).

| # | Section | Data | Notes |
|---|---|---|---|
| Header | "Run finished in X — N checks need attention", Back to run console, Retry failed (n) | `run_time_s`, `failures` | Retry failed is a POST to `/api/control` `requeue` with all failure ids. |
| Summary | 4 tiles with icon, value, pass/attention pill and magnet pin | `summary` | |
| 01 Results sheet | League × season match counts | `matches` | Normal = dashed chalk cell; known exception = `--run` tint with blue border; mismatch = `--warn` tint, bold, plus "!". The cell tooltip states "found, expected (note)". A handwritten note explains the COVID exception. |
| 02 Fouls & stoppages | Failed and suspicious responses + Re-queue per row | `failures` | Re-queue deletes the stored file and re-queues the request (spec §7). |
| 03 Team sheets | Clubs per league-season with league logo | `clubs` | |
| 04 Treatment room | Injury events per season bar chart | `injuries_per_season` | 2019/20 bar is `--warn`, with a handwritten "COVID-shortened" note. Remove the "Sample values" tag once real data flows. |
| 05 Full-time whistle | Definition of done checklist | `dod` | done = green magnet with a check; open = orange magnet with a dash. Documented quirks are listed below the checklist. |
| Footer | Credits | | Same as the console. |

## 5. Chalky, the mascot

Chalky is a chalk-outlined football with arms and legs who reflects run health. The full rig is in `design/mascot-chalky.dc.html` (`M` table + SVG). The console copy is `chalky()` + the header SVG in `run-console.dc.html`. Port it once into `chalky.js` and use it on both screens.

### State machine (priority from top to bottom)

| Priority | Condition | State | Colour token |
|---|---|---|---|
| 1 | `phase == "finished"` **and** any failures remain | Red card | `--fail` |
| 2 | `phase == "paused"` **or** `limiter.backoff_until > now` | Took a knock | `--warn` |
| 3 | overall ≥ 100% | Full time | `--gold` |
| 4 | overall 90–99% | Ignited (full power-up aura) | `--power` |
| 5 | overall 50–89% | Sprinting (aura starts charging at 75%) | `--ok` |
| 6 | overall 10–49% | Jogging | `--run` |
| 7 | overall < 10% | Warming up | `#7FA7D9` |

- **Overall progress** = Σ `done` ÷ Σ `total` over the three sources, rounded down, capped at 100. Use the estimated totals until real ones are known. Never let the % go backwards: if the totals grow, hold the displayed value until it catches up.
- **Match clock**: minute = round(overall × 0.9) shown as `55′`; at 100% show `FT`.
- **Aura**: `none` below 75%. `charge` at 75–89%, with opacity 0.25 → 0.70 linear in progress and 5 embers. `ignite` at 90–99%: full aura, lightning, 14 embers, floating rocks, and a 1.5px shake on the mascot widget. `glow` at 100%: opacity 0.55. A knock or red card always switches the aura off.
- **Speech bubble**: 3 lines per state (in the `M` table). Start on line 0; each poke (click) advances to the next. Reset to 0 when the state changes. Use `role="status"` + `aria-live="polite"` so the line is announced.
- **Eyes** follow the cursor (pupil offset clamped to ±3.5px x, ±3px y), computed relative to the mascot's position on screen.
- **Poke**: click/Enter/Space spins the ball 360° (700 ms, `--ease-out`) and advances the line.
- **Ring**: a progress ring around him, `stroke-dashoffset` transition `--dur-ring`. It pulses at 90–99%.

### Placement
- **Console:** in the header, before the status pill: 140×132 widget, plus the bubble and the minute and state line.
- **Validation report:** add the same widget to its header (it isn't in the design file yet). It shows Full time if all checks pass and Red card if failures remain.
- **Mascot sheet:** a reference for design QA, not a shipped screen. Ship its demo controls only behind `?debug=mascot`.

## 6. Design tokens used (see `tokens.css` for all)

| Token | Value | Usage |
|---|---|---|
| `--board` | #0D1311 | Page background |
| `--panel` | rgba(19,26,23,.78) | Section cards |
| `--paper` | #F1ECDF | Prints, logo stickers, speech bubble |
| `--chalk` | #E4E7DE | Primary text |
| `--muted` | #97A29A | Labels, captions |
| `--annotation` | #E9D98B | Handwritten notes, section icons, active tab underline |
| `--ok` / `--run` / `--warn` / `--fail` | #45B87F / #4C8DDB / #E07B39 / #E5636B | Status everywhere |
| `--font-ui` / `--font-data` / `--font-hand` | Plex Sans / Plex Mono / Caveat | UI / numbers and codes / annotations only |
| `--space-7` | 28px | Between page sections |
| `--radius-lg` | 12px | Panels |
| `--tap` | 44px | Minimum button height |

## 7. Components

| Component | Variants | Props | Notes |
|---|---|---|---|
| Panel | default, hover | — | Border `--line`, shadow `--panel-shadow`. Hover lifts it 2px and turns the border to `--line-hover`. |
| Section eyebrow | — | number, label, icon | Mono 11px, uppercase, letter-spacing .1em, with a 16px stroke icon in `--annotation`. Icons: target, download tray, tactics play, gauge, pitch, list, clipboard, camera. |
| Magnet | ok, run, fail, queued, sizes 14/18/26/28/44 | state | Radial gradient + `--magnet-shadow`. Queued = dashed empty circle. On hover it scales to 1.12 and lifts 2px. |
| Logo sticker | league, site-logo, site-wordmark | logo, colour | Paper tile with a 2–3px bottom border in the identity colour. The image uses `object-fit: contain`. |
| Status pill | ok, run, warn | text | 12px/600, pill radius, tint bg + `*-text` fg. |
| Progress bar | ok, run | pct | 8–10px track inset in a `--well`, fill with a highlight on top. |
| Tabs | selected, idle | items | Selected: subtle chalk bg + 2px `--annotation` underline. `role="tablist"`/`tab`, `aria-selected`. |
| Handwritten note | text, arrow | — | Caveat 19–20px `--annotation`. The chalk arrow is SVG with the `#chalk` displacement filter. Decorative notes get `aria-hidden` when they repeat information shown elsewhere. |
| Print | recur on/off | photo, caption, match, date, stamp, area, league | See §3 Background prints. |
| Chalky widget | 7 states | progress, phase, backoff, failures | See §5. |

## 8. States, interactions, copy

| Element | State | Behaviour |
|---|---|---|
| Pause button | running | Label "Pause". POST `pause`. Status pill turns orange "Paused". Chalky shows Took a knock. |
| Pause button | paused | Label "Resume". |
| Run smoke test | idle only | Disabled while running (`aria-disabled`, 50% opacity). Runs spec §5 "Order and smoke test" step 1 and fills section 07. |
| `--dry-run` | — | Helper: "Plans every request and checks the cache, but sends nothing. Shows what a real run would fetch." |
| `--limit` | — | Helper: "Most requests each collector may send. Try 20 for a smoke test; leave blank for the full run." Integer ≥ 1 or empty. |
| Coverage tabs | click | Switch source. The note under the grid changes with the source. |
| Log tabs | click | Filter rows by source. |
| Re-queue / Retry failed | click | POST, then show the row as "Re-queued" until the next status poll confirms. |
| Board | mouse move | Chalk-light spotlight (460px warm glow + 240px masked brighter dot grid) follows the cursor. Throttle with requestAnimationFrame and fade out on mouse leave (`--dur-spot`). |
| Header | hover | Pitch sketch brightens to 50% and the tactic arrow redraws (1.1 s stroke-dashoffset). |
| Print | rest | Opacity 0.05 (hidden ghost). |
| Print | cursor within 190px, or hover | Fades to opacity 1. On direct hover it also straightens, scales ×1.1 and moves to the front (`--dur-print`). |

## 9. Responsive behaviour

| Breakpoint | Changes |
|---|---|
| ≥ 1280px | Layout as designed. |
| 940–1279px | Wide and narrow panel pairs stack. The collector grid becomes 2 + 1 (`auto-fit, minmax(300px, 1fr)`). |
| < 768px | Header wraps: title, then Chalky, then status. Controls stack, and the helper notes go full width. Coverage grid, log and results tables scroll horizontally inside their well (min-width 760–920px). Show only 6 prints, at 0.7 scale. |

## 10. Edge cases

- **Before the first status arrives:** show skeleton panels (well-coloured blocks) and Chalky in Warming up with the line "Lacing the boots…".
- **Stale data:** if there's no successful poll for more than 5 s, show an orange banner under the header ("Lost contact with the collectors, retrying…") and freeze the numbers. Don't change Chalky's state.
- **Idle (no run):** the collectors show "Queued", totals show `—`, Run smoke test is enabled.
- **Dry run:** add a "DRY RUN" chalk stamp across the header. Counts are planned requests; label them "planned".
- **Long URLs:** single line with an ellipsis; the full URL goes in `title`.
- **Big numbers:** use thousands separators (`en-US`) and tabular mono figures.
- **Missing image:** the print falls back to a paper-coloured block with the player's name. The logo sticker falls back to the league short code (PL, LL, SA, BL, L1).
- **Failures during a run** don't red-card Chalky. Only failures remaining **after** the run do.

## 11. Animation and motion

| Element | Trigger | Animation | Duration | Easing |
|---|---|---|---|---|
| Panel | hover | translateY(-2px), border colour | 250 ms | ease |
| Magnet | hover | scale 1.12, translateY(-2px), brightness 1.12 | 150 ms | ease |
| Print | hover | rotate → 0, scale ×1.1 | 300 ms | ease |
| Spotlight | mouse enter/leave | opacity 0 ↔ 1 | 350 ms | ease |
| Header tactic | header hover | stroke redraw | 1100 ms | ease-out |
| Chalky body | state | sway 3 s / bounce .6 s / hype .42 s / frenzy .34 s / jump .8 s / wobble 2.2 s / slump 3 s | loop | see keyframes |
| Chalky ring | progress change | stroke-dashoffset | 500 ms | ease |
| Chalky poke | click | rotate 360° | 700 ms | cubic-bezier(.2,.8,.3,1) |

All keyframes are in the `<helmet><style>` blocks of the design files. Copy them verbatim. **`prefers-reduced-motion: reduce` turns off every looping animation and hover transform** (the media query lists them). The state still reads from colour, face and text.

## 12. Accessibility

- Every control is a real `<button>`, `<a href>`, `<input>` + `<label>`, at least 44px tall (tabs at least 36px, inside a 44px bar).
- Focus order follows the DOM: header (Chalky, then back link and actions), controls, collectors, steps, tempo, coverage tabs, then grid, log tabs, then table, notes, footer links. Give everything focusable a visible focus ring (`outline: 2px solid var(--annotation); outline-offset: 2px`).
- `aria-describedby` links the dry-run and limit inputs to their helper notes.
- Chalky is a `<button>` with `aria-label="Chalky: {state}, {n}% collected. Poke him."`. His bubble is `role="status" aria-live="polite"`. Throttle announcements to state changes, not every percent.
- Charts are `role="img"` with an `aria-label` describing the trend. Decorative SVG (pitch, grain, arrows, aura) is `aria-hidden="true"`.
- Status is never colour alone: pills have text, failed magnets have "!", and mismatches are bold with "!".
- Contrast: body text ≥ 4.5:1 on `--panel`. `--muted` on `--panel` passes; don't go lighter than `--muted` for any text.

## 13. Assets and licensing (non-negotiable)

- Use only the files in `assets/`. Don't fetch other photos or logos.
- Keep the credits footer on **both** screens, generated from `assets/credits.json`. Each photo is linked to its Commons page, with author and licence.
- The logos are public-domain text logos on Commons, but they're still trademarks. Keep the footer line: "Logos and names are trademarks of their owners, used here only to identify them in a non-commercial academic project."
- Understat and Football-Data have no free logo. Keep the typeset name tiles.

## 14. Placeholders to replace

- Every number in the designs' `renderVals()`.
- The `tmapi…/…` URL shapes in the sample log and failures. Use the real endpoints the SDK hits (spec §5 says confirm these in the smoke test).
- `[COUNT]` (players with zero injuries) and the "Sample values" tag on the injury chart.
- Smoke-test findings: fill from the real smoke-test results, and copy them into the README (spec §5).

## 15. Acceptance checklist

- [ ] `python run_all.py` prints the dashboard URL. The page loads offline, apart from fonts.
- [ ] All console sections render from `/api/status` and update every second without layout jumps.
- [ ] Pause/Resume works end to end, and Chalky shows Took a knock while paused or during a WAF back-off.
- [ ] Chalky passes through all 7 states at the documented thresholds (test with a fake status feed). Aura charge starts at 75% and ignites at 90%.
- [ ] The validation report renders from `/api/validation` and flags Ligue 1 2019/20 as a known exception, not an error.
- [ ] Re-queue and Retry failed POST to the API and the rows update.
- [ ] Layout holds at 375px, 768px, 1280px and 1440px, with no horizontal page scroll.
- [ ] Reduced motion stops every loop. Keyboard-only use reaches every control with a visible focus ring.
- [ ] Credits footer present on both screens.
- [ ] Prints are hidden at rest, reveal near the cursor, and never overlap the header or Chalky.

## 16. Injury facts: sources (checked 2026-10-20)

| Print | Verified detail | Source |
|---|---|---|
| Van Dijk | ACL, Pickford challenge, Everton 2–2 Liverpool, 17 Oct 2020 | [CBS Sports](https://www.cbssports.com/soccer/news/virgil-van-dijk-injury-liverpool-star-to-undergo-surgery-after-tearing-ligaments-on-pickford-challenge) |
| Elliott | Fracture-dislocated left ankle, Leeds 0–3 Liverpool, 12 Sep 2021 | [This Is Anfield](https://thisisanfield.com/?p=254141) |
| De Bruyne | Hamstring relapse → surgery, Burnley 0–3 Man City, 11 Aug 2023 (recurrence of the June 2023 injury) | [Premier League](https://premierleague.com/news/3635555) |
| Timber | Right-knee ACL on Premier League debut, Arsenal 2–1 Forest, 12 Aug 2023 | [Premier League](https://www.premierleague.com/news/3636638) |
| Dembélé | Ruptured biceps femoris tendon, left thigh, Getafe 1–2 Barcelona, 16 Sep 2017 | [FourFourTwo](https://fourfourtwo.com/news/dembele-flies-finland-surgery) |
| Ansu Fati | Internal meniscus tear, left knee, Barcelona 5–2 Betis, 7 Nov 2020 | [SI](https://www.si.com/soccer/2020/11/09/ansu-fati-injury-barcelona-spain) |
| Militão | Left ACL v Athletic (0–2), 12 Aug 2023; right ACL v Osasuna (4–0), 9 Nov 2024 | [SI](https://www.si.com/soccer/real-madrid-eder-militao-out-for-2024-25-season-with-torn-acl) |
| Alaba | Left ACL, Real Madrid 4–1 Villarreal, 17 Dec 2023 | [Planet Sport](https://planetsport.com/soccer/news/real-madrids-defensive-woes-deepen-as-david-alaba-faces-acl-blow) |
| Carvajal | Right ACL (plus collateral ligament and popliteus tendon), Villarreal 0–2 Real Madrid, 5 Oct 2024 | [Real Madrid](https://www.realmadrid.com/en-US/news/football/first-team/latest-news/carvajal-saludo-a-sus-companeros-en-la-ciudad-real-madrid-21-10-2024) |
| Zaniolo | Right ACL, Roma 1–2 Juventus, 12 Jan 2020; left ACL with Italy, Sep 2020 | [Washington Times / AP](https://www.washingtontimes.com/news/2020/sep/8/zaniolo-to-undergo-surgery-after-rupturing-acl-aga/) |
| Milik | Right ACL (second in a year), SPAL 2–3 Napoli, 23 Sep 2017 | [SI](https://www.si.com/soccer/2017/09/25/napoli-confirm-arkadiusz-milik-will-be-out-6-months-after-successful-knee-surgery) |
| Chiesa | Left ACL, Roma 3–4 Juventus, 9 Jan 2022 | [theScore](https://www.thescore.com/news/2272573) |
| Wirtz | Left ACL, Leverkusen 0–1 Köln, 13 Mar 2022 | [Bundesliga.com](https://amp.bundesliga.com/en/bundesliga/news/florian-wirtz-season-over-after-knee-ligament-tear-bayer-leverkusen-19215) |
| Neymar | Cracked metatarsal, PSG 3–0 Marseille, 25 Feb 2018; right-ankle ligament surgery after PSG 4–3 Lille, 19 Feb 2023 | [Al Jazeera](https://www.aljazeera.com/sports/2023/3/6/neymar-out-for-rest-of-the-season-due-to-ankle-injury-psg-says) |
