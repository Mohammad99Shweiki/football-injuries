"""JSON API for the analysis part of the dashboard, mounted by `scraper/serve.py` under /api/analysis/.

Standard library only at import (the scraper's environment has no pandas); table pages import pandas lazily and
answer 503 without it. Runs start `python -m analysis.run` in a subprocess with the analysis dependency group, one at
a time and never while a scrape is running.

    GET  /api/analysis/phases                     phases with status, staleness and step summaries
    GET  /api/analysis/phases/{id}                one phase: its run record, steps with notes (from the script)
    GET  /api/analysis/phases/{id}/steps/{n}      one step: note, code, checks, log rows, outputs, previews, error
    GET  /api/analysis/table?path=…&offset=&limit=&sort=&desc=&q=   a page of a table under data/ or mappings/
    GET  /api/analysis/mappings                   hand-reviewed files with their approval record
    POST /api/analysis/mappings/{file}/approve    record an approval (date, file hash) and a decision-log row
    GET  /api/analysis/logs/{decisions|preprocessing}
    GET  /api/analysis/results                    names of the results-dashboard files (Phase 6 export)
    GET  /api/analysis/results/{name}             one of them
    GET  /api/analysis/figures/{file}             a figure from reports/figures
    GET  /api/analysis/reports/{file}             a phase report or summary.md (markdown)
    GET  /api/analysis/run                        the current or last run job
    POST /api/analysis/run                        {"phase": "05" | "all", "until": 7, "force": false}
"""

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import date, datetime, timezone
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, unquote

from analysis.config import DATA_DIR, FIGURES_DIR, MAPPINGS_DIR, PIPELINE, REPORTS_DIR, ROOT, get_phase
from analysis.run import read_record, stale_reasons
from analysis.steps import read_cells, to_steps

DOCS = ROOT / "docs"
RESULTS_DIR = DATA_DIR / "06_report" / "dashboard"
APPROVALS = MAPPINGS_DIR / "approvals.json"

Response = tuple[int, str, bytes]


def _json(payload: object, status: int = HTTPStatus.OK) -> Response:
    return status, "application/json", json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")


def _error(message: str, status: int) -> Response:
    return _json({"error": message}, status)


# ---- phases and steps --------------------------------------------------------------------------------------------

def _phase_summary(phase) -> dict:
    rec = read_record(phase)
    steps = to_steps(read_cells(phase.script))
    by_index = {s["index"]: s for s in rec["steps"]} if rec else {}
    reasons = stale_reasons(phase)
    return {
        "id": phase.id, "title": phase.title, "folder": phase.folder, "notebook": f"notebooks/{phase.name}.ipynb",
        "status": "running" if JOB.running_phase() == phase.id else (rec["status"] if rec else "not_run"),
        "stale": bool(reasons), "stale_reasons": reasons,
        "run_id": rec["run_id"] if rec else None, "finished": rec["finished"] if rec else None,
        "duration_s": round(sum(s.get("duration_s", 0) for s in rec["steps"]), 1) if rec else None,
        "steps": [{
            "index": s.index, "title": s.title,
            "status": by_index[s.index]["status"] if s.index in by_index else "not_run",
            "duration_s": by_index.get(s.index, {}).get("duration_s"),
            "checks": len(by_index.get(s.index, {}).get("checks", [])),
            "checks_failed": sum(c["failed"] > 0 for c in by_index.get(s.index, {}).get("checks", [])),
            "outputs": len(by_index.get(s.index, {}).get("outputs", [])),
        } for s in steps],
    }


def phases() -> Response:
    return _json([_phase_summary(p) for p in PIPELINE])


def phase(key: str) -> Response:
    p = get_phase(key)
    rec = read_record(p) or {}
    return _json(_phase_summary(p) | {"record": {k: v for k, v in rec.items() if k != "steps"}})


def step(key: str, index: int) -> Response:
    p = get_phase(key)
    script = {s.index: s for s in to_steps(read_cells(p.script))}
    if index not in script:
        return _error(f"phase {p.id} has no step {index}", HTTPStatus.NOT_FOUND)
    s = script[index]
    rec = read_record(p) or {"steps": []}
    run = next((r for r in rec["steps"] if r["index"] == index), None)
    return _json({"phase": p.id, "index": index, "title": s.title, "note": s.note, "code": s.code,
                  "run": run, "status": run["status"] if run else "not_run"})


# ---- tables ------------------------------------------------------------------------------------------------------

def _safe_path(rel: str) -> Path | None:
    path = (ROOT / rel).resolve()
    allowed = [DATA_DIR.resolve(), MAPPINGS_DIR.resolve()]
    raw = (DATA_DIR / "raw").resolve()
    if not any(path.is_relative_to(a) for a in allowed) or path.is_relative_to(raw) or not path.is_file():
        return None
    return path if path.suffix in (".parquet", ".csv") else None


_TABLE_CACHE: dict[tuple[str, int], object] = {}


def table(query: dict[str, list[str]]) -> Response:
    rel = (query.get("path") or [""])[0]
    path = _safe_path(rel)
    if path is None:
        return _error("path must be a .parquet or .csv file under data/ (not data/raw) or mappings/", HTTPStatus.BAD_REQUEST)
    try:
        import pandas as pd
    except ImportError:
        return _error("table pages need the analysis dependencies: start the server with `uv run --group analysis`",
                      HTTPStatus.SERVICE_UNAVAILABLE)
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _TABLE_CACHE:
        _TABLE_CACHE.clear()  # one table at a time: the big ones are ~100 MB in memory
        _TABLE_CACHE[key] = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, dtype=str, keep_default_na=False)
    df = _TABLE_CACHE[key]
    q = (query.get("q") or [""])[0].strip().lower()
    if q:
        df = df[df.astype(str).apply(lambda c: c.str.lower().str.contains(q, regex=False)).any(axis=1)]
    sort = (query.get("sort") or [""])[0]
    if sort in df.columns:
        df = df.sort_values(sort, ascending=(query.get("desc") or ["0"])[0] != "1", kind="stable")
    offset = max(0, int((query.get("offset") or ["0"])[0]))
    limit = min(1000, max(1, int((query.get("limit") or ["100"])[0])))
    page = df.iloc[offset:offset + limit]
    data = json.loads(page.to_json(orient="split", index=False, default_handler=str, date_format="iso"))
    return _json({"path": rel, "columns": [{"name": str(c), "type": str(t)} for c, t in df.dtypes.items()],
                  "rows": data["data"], "total": len(df), "offset": offset, "limit": limit})


# ---- mappings and approvals --------------------------------------------------------------------------------------

def _approvals() -> dict:
    return json.loads(APPROVALS.read_text(encoding="utf-8")) if APPROVALS.exists() else {}


def mappings() -> Response:
    approvals = _approvals()
    rows = []
    for f in sorted(MAPPINGS_DIR.glob("*.csv")):
        digest = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
        a = approvals.get(f.name)
        rows.append({"file": f.name, "path": f"mappings/{f.name}", "rows": max(0, f.read_text(encoding="utf-8").count("\n") - 1),
                     "hash": digest, "approval": a, "approved_current": bool(a and a["hash"] == digest)})
    return _json(rows)


PROPOSALS = {"team_map.csv": DATA_DIR / "01_entities" / "team_map_proposed.csv",
             "injury_label_map.csv": DATA_DIR / "02_injuries" / "injury_label_map_proposed.csv"}
COUNT_COLUMNS = {"records", "over_7_days", "share_over_7_days", "cum_share_over_7_days", "n_seasons", "first_season", "last_season"}


def mapping_diff(name: str) -> Response:
    """Where the reviewed file differs from what the phase proposes (key = first column; counts ignored)."""
    import csv
    reviewed, proposal = MAPPINGS_DIR / name, PROPOSALS.get(name)
    if not reviewed.is_file() or proposal is None:
        return _error(f"no proposal to compare for {name}", HTTPStatus.NOT_FOUND)
    if not proposal.is_file():
        return _error(f"run the phase that writes {proposal.name} first", HTTPStatus.NOT_FOUND)
    def rows(path: Path) -> tuple[str, dict[str, dict]]:
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            key = reader.fieldnames[0]
            return key, {r[key]: r for r in reader}
    key, rev = rows(reviewed)
    _, prop = rows(proposal)
    changes = [{"key": k, "field": f, "proposed": prop[k].get(f, ""), "reviewed": v}
               for k in rev if k in prop for f, v in rev[k].items()
               if f not in COUNT_COLUMNS and (prop[k].get(f) or "") != (v or "")]
    flagged = [k for k, r in rev.items() if str(r.get("review", "")).lower() == "true"]
    return _json({"file": name, "key": key, "proposal": str(proposal.relative_to(ROOT)), "changes": changes,
                  "only_reviewed": sorted(set(rev) - set(prop)), "only_proposed": sorted(set(prop) - set(rev)),
                  "flagged": flagged, "rows": len(rev)})


def approve(name: str, body: dict) -> Response:
    f = MAPPINGS_DIR / name
    if f.suffix != ".csv" or not f.is_file() or f.parent.resolve() != MAPPINGS_DIR.resolve():
        return _error(f"no mapping {name}", HTTPStatus.NOT_FOUND)
    digest = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    if body.get("hash") != digest:
        return _error("mapping changed since it was opened; reload and review the current version", HTTPStatus.CONFLICT)
    approvals = _approvals()
    approvals[name] = {"date": date.today().isoformat(), "hash": digest, "note": str(body.get("note") or "")[:500]}
    APPROVALS.write_text(json.dumps(approvals, indent=1) + "\n", encoding="utf-8")
    note = f" {approvals[name]['note']}" if approvals[name]["note"] else ""
    with (DOCS / "DECISIONS.md").open("a", encoding="utf-8") as fh:
        fh.write(f"| {date.today().isoformat()} | `mappings/{name}` approved (hash {digest}).{note} | Review point in the dashboard; "
                 "later phases are stale until rerun. |\n")
    return _json({"ok": True, "approval": approvals[name]})


# ---- logs, results, figures, reports -----------------------------------------------------------------------------

def _md_tables(text: str) -> list[dict]:
    """Rows of every markdown table, each with the heading it sits under."""
    rows, header, section = [], None, ""
    for line in text.splitlines():
        if line.startswith("#"):
            section, header = line.lstrip("#").strip(), None
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if header is None:
                header = cells
            elif not set("".join(cells)) <= set("-: "):
                rows.append({"section": section} | dict(zip(header, cells)))
        else:
            header = None
    return rows


def logs(kind: str) -> Response:
    files = {"decisions": DOCS / "DECISIONS.md", "preprocessing": DOCS / "PREPROCESSING_LOG.md"}
    if kind not in files:
        return _error("logs are 'decisions' or 'preprocessing'", HTTPStatus.NOT_FOUND)
    return _json(_md_tables(files[kind].read_text(encoding="utf-8")))


def results(name: str | None) -> Response:
    if name is None:
        return _json(sorted(f.stem for f in RESULTS_DIR.glob("*.json")))
    f = RESULTS_DIR / f"{name}.json"
    if not re.fullmatch(r"[a-z_]+", name) or not f.is_file():
        return _error(f"no results file {name}", HTTPStatus.NOT_FOUND)
    return HTTPStatus.OK, "application/json", f.read_bytes()


def results_bundle() -> Response:
    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        return _error("No results export yet. Run Phase 6 to produce it.", HTTPStatus.NOT_FOUND)
    return _json({f.stem: json.loads(f.read_text(encoding="utf-8")) for f in files})


def download(query: dict[str, list[str]]) -> Response:
    path = _safe_path((query.get("path") or [""])[0])
    if path is None:
        return _error("choose a table under data/ or mappings/", HTTPStatus.BAD_REQUEST)
    if path.suffix == ".csv":
        return HTTPStatus.OK, "text/csv; charset=utf-8", path.read_bytes()
    try:
        import pandas as pd
    except ImportError:
        return _error("CSV export requires the analysis dependencies", HTTPStatus.SERVICE_UNAVAILABLE)
    return HTTPStatus.OK, "text/csv; charset=utf-8", pd.read_parquet(path).to_csv(index=False).encode("utf-8")


def figures() -> Response:
    return _json([{"name": f.name, "phase": f.name[:2], "bytes": f.stat().st_size} for f in sorted(FIGURES_DIR.glob("*.png"))])


def finalise_status() -> dict:
    """Everything the report needs before a version can be frozen."""
    phases_ok = [{"phase": p.id, "title": p.title, "ok": not stale_reasons(p), "reasons": stale_reasons(p)} for p in PIPELINE]
    rec6 = read_record(get_phase("06")) or {"steps": []}
    checks = [c for s in rec6["steps"] for c in s.get("checks", [])]
    approvals = _approvals()
    maps = [{"file": f.name, "ok": bool(approvals.get(f.name)) and approvals[f.name]["hash"] == hashlib.sha256(f.read_bytes()).hexdigest()[:16]}
            for f in sorted(MAPPINGS_DIR.glob("*.csv"))]
    cited = sorted(set(re.findall(r"figures/([\w.-]+\.png)", (REPORTS_DIR / "summary.md").read_text(encoding="utf-8"))))
    missing = [f for f in cited if not (FIGURES_DIR / f).exists()]
    items = [
        {"item": "Every phase passed and is up to date", "ok": all(p["ok"] for p in phases_ok),
         "detail": "; ".join(f"{p['phase']}: {', '.join(p['reasons'])}" for p in phases_ok if not p["ok"]) or "7 of 7"},
        {"item": "Summary numbers match the data (Phase 6 checks)", "ok": bool(checks) and all(c["failed"] == 0 for c in checks),
         "detail": f"{sum(c['failed'] == 0 for c in checks)} of {len(checks)} checks passed"},
        {"item": "Hand-reviewed mappings approved in their current version", "ok": all(m["ok"] for m in maps),
         "detail": ", ".join(f"{m['file']} {'approved' if m['ok'] else 'not approved'}" for m in maps)},
        {"item": "Every figure cited by the summary exists", "ok": not missing,
         "detail": f"{len(cited)} cited" + (f"; missing {', '.join(missing)}" if missing else "")},
    ]
    releases = sorted((p.name for p in (REPORTS_DIR / "releases").glob("*") if p.is_dir()), reverse=True) if (REPORTS_DIR / "releases").exists() else []
    return {"items": items, "ready": all(i["ok"] for i in items), "phases": phases_ok, "releases": releases}


def finalise(body: dict) -> Response:
    status = finalise_status()
    if not status["ready"]:
        return _error("not ready: " + "; ".join(i["item"] for i in status["items"] if not i["ok"]), HTTPStatus.CONFLICT)
    from analysis.run import _git
    git = _git()
    name = f"{date.today().isoformat()}-{git['sha'] or 'nogit'}{'-dirty' if git['dirty'] else ''}"
    out = REPORTS_DIR / "releases" / name
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"release": name, "created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "git": git,
                "note": str(body.get("note") or "")[:500], "checklist": status["items"],
                "phases": {p.id: {k: (read_record(p) or {}).get(k) for k in ("run_id", "finished", "seed", "inputs")} for p in PIPELINE},
                "mappings": _approvals(),
                "summary_sha256": hashlib.sha256((REPORTS_DIR / "summary.md").read_bytes()).hexdigest()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, default=str) + "\n", encoding="utf-8")
    return _json({"ok": True, "release": name, "path": str((out / "manifest.json").relative_to(ROOT))})


def figure(name: str) -> Response:
    f = FIGURES_DIR / name
    if not re.fullmatch(r"[\w.-]+\.png", name) or not f.is_file():
        return _error(f"no figure {name}", HTTPStatus.NOT_FOUND)
    return HTTPStatus.OK, "image/png", f.read_bytes()


def report(name: str) -> Response:
    f = REPORTS_DIR / name
    if not re.fullmatch(r"[\w.-]+\.md", name) or not f.is_file():
        return _error(f"no report {name}", HTTPStatus.NOT_FOUND)
    return HTTPStatus.OK, "text/markdown; charset=utf-8", f.read_bytes()


# ---- run jobs ----------------------------------------------------------------------------------------------------

class Job:
    """At most one analysis run at a time, as a subprocess; keeps the tail of its output."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None
        self.info: dict = {}
        self.lines: deque[str] = deque(maxlen=200)

    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def running_phase(self) -> str | None:
        if not self.running():
            return None
        for line in reversed(self.lines):
            m = re.match(r"\[(\d\d)\] step", line)
            if m:
                return m.group(1)
        return self.info.get("phase")

    def start(self, target: str, until: int | None, force: bool) -> dict:
        with self.lock:
            if self.running():
                raise RuntimeError("an analysis run is already in progress")
            # This interpreter if it has the analysis dependencies (Docker, `uv run --group analysis`), else via uv.
            python = [sys.executable] if importlib.util.find_spec("pandas") else ["uv", "run", "--group", "analysis", "python"]
            cmd = [*python, "-m", "analysis.run", target]
            if until is not None:
                cmd += ["--until", str(until)]
            if force:
                cmd.append("--force")
            self.lines.clear()
            self.proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            self.info = {"phase": target, "until": until, "force": force, "command": " ".join(cmd),
                         "started": datetime.now(timezone.utc).isoformat(timespec="seconds"), "returncode": None}
            threading.Thread(target=self._read, daemon=True, name="analysis-run").start()
            return self.snapshot()

    def _read(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            self.lines.append(line.rstrip("\n"))
        self.info["returncode"] = self.proc.wait()
        self.info["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def snapshot(self) -> dict:
        return self.info | {"running": self.running(), "current_phase": self.running_phase(), "output": list(self.lines)[-40:]}


JOB = Job()


def start_run(body: dict, scrape_busy: bool) -> Response:
    if scrape_busy:
        return _error("a scrape is running: analysis runs are disabled until it finishes", HTTPStatus.CONFLICT)
    target = str(body.get("phase") or "")
    if target != "all":
        try:
            target = get_phase(target).id
        except ValueError as exc:
            return _error(str(exc), HTTPStatus.BAD_REQUEST)
    until = body.get("until")
    if until is not None and (not isinstance(until, int) or until < 0 or target == "all"):
        return _error("until must be a step number >= 0, for a single phase", HTTPStatus.BAD_REQUEST)
    try:
        return _json(JOB.start(target, until, bool(body.get("force"))), HTTPStatus.ACCEPTED)
    except RuntimeError as exc:
        return _error(str(exc), HTTPStatus.CONFLICT)
    except FileNotFoundError:
        return _error("`uv` not found: analysis runs need uv and the analysis dependency group", HTTPStatus.SERVICE_UNAVAILABLE)


# ---- dispatch ----------------------------------------------------------------------------------------------------

def handle(method: str, path: str, query: str, body: dict, scrape_busy: bool = False) -> Response:
    """Route /api/analysis/... to its handler; returns (status, content type, body)."""
    parts = [unquote(p) for p in path.removeprefix("/api/analysis").strip("/").split("/") if p]
    q = parse_qs(query)
    try:
        match method, parts:
            case "GET", ["phases"]:
                return phases()
            case "GET", ["phases", key]:
                return phase(key)
            case "GET", ["phases", key, "steps", n] if n.isdigit():
                return step(key, int(n))
            case "GET", ["table"]:
                return table(q)
            case "GET", ["download"]:
                return download(q)
            case "GET", ["mappings"]:
                return mappings()
            case "GET", ["mappings", name, "diff"]:
                return mapping_diff(name)
            case "POST", ["mappings", name, "approve"]:
                return approve(name, body)
            case "GET", ["logs", kind]:
                return logs(kind)
            case "GET", ["results"]:
                return results(None)
            case "GET", ["results-bundle"]:
                return results_bundle()
            case "GET", ["results", name]:
                return results(name)
            case "GET", ["figures"]:
                return figures()
            case "GET", ["finalise"]:
                return _json(finalise_status())
            case "POST", ["finalise"]:
                return finalise(body)
            case "GET", ["figures", name]:
                return figure(name)
            case "GET", ["reports", name]:
                return report(name)
            case "GET", ["run"]:
                return _json(JOB.snapshot() | {"scrape_busy": scrape_busy})
            case "POST", ["run"]:
                return start_run(body, scrape_busy)
        return _error("not found", HTTPStatus.NOT_FOUND)
    except ValueError as exc:
        return _error(str(exc), HTTPStatus.BAD_REQUEST)


if __name__ == "__main__":  # quick smoke test: python -m analysis.api
    for p in ("/api/analysis/phases", "/api/analysis/phases/05/steps/7", "/api/analysis/mappings", "/api/analysis/logs/decisions",
              "/api/analysis/results", "/api/analysis/table?path=data/05_injury_analysis/tables/same_club.csv&limit=2"):
        route, _, qs = p.partition("?")
        t0 = time.perf_counter()
        status, ctype, data = handle("GET", route, qs, {})
        print(status, ctype, len(data), "bytes", f"{time.perf_counter() - t0:.2f} s", p)
