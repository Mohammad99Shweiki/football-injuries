"""Run analysis phases step by step and record what each step did.

    uv run --group analysis python -m analysis.run status        # every phase: last run, status, stale or not
    uv run --group analysis python -m analysis.run 05            # run phase 05 (all steps)
    uv run --group analysis python -m analysis.run 05 --until 7  # run phase 05 up to and including step 7
    uv run --group analysis python -m analysis.run all           # run every stale phase in order, stop at a failure
    uv run --group analysis python -m analysis.run all --force   # run every phase

A phase is its script in `analysis/phases/` (percent-format cells, the same cells as its notebook). The cells run in
one namespace, top to bottom, as in Jupyter. For each step the runner records:
- **checks**: every `assert` (rewritten on the fly into a recorded check; a failed one still stops the run),
- **log rows** the phase appends to its `LOG` list (the preprocessing log),
- **outputs**: files written or changed in the phase's data folder and in `reports/`, with rows and columns,
- **previews**: what the cell would show in a notebook (tables as their first rows, figures, text), and printed output.

The record goes to `data/<phase>/_run.json` with the inputs' fingerprint (phase script, shared code, mappings,
tables, upstream run ids), so a phase is **stale** when any of them changed since its last run.
"""

import argparse
import ast
import contextlib
import hashlib
import io
import json
import linecache
import os
import subprocess
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from analysis.config import DATA_DIR, MAPPINGS_DIR, PIPELINE, REPORTS_DIR, ROOT, SEED, TABLES_DIR, Phase, get_phase
from analysis.steps import read_cells, to_steps

RUN_FILE = "_run.json"
SHARED_CODE = ("config.py", "load.py", "report.py", "audit.py", "steps.py")
NOT_INPUTS = {"approvals.json"}  # review records in mappings/ that no phase reads
MAX_PREVIEWS = 6
MAX_ROWS = 50
MAX_TEXT = 6000


# ---- fingerprints and staleness ---------------------------------------------------------------------------------

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _git() -> dict:
    def out(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    return {"sha": out("rev-parse", "--short", "HEAD"), "dirty": bool(out("status", "--porcelain", "--", "analysis", "mappings"))}


def read_record(phase: Phase) -> dict | None:
    path = DATA_DIR / phase.folder / RUN_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def fingerprint(phase: Phase) -> dict[str, str]:
    """Hashes of everything a phase's results depend on."""
    fp = {"script": _sha(phase.script.read_bytes()),
          "shared code": _sha(b"".join((ROOT / "analysis" / f).read_bytes() for f in SHARED_CODE))}
    for f in sorted(MAPPINGS_DIR.glob("*")):
        if f.is_file() and f.name not in NOT_INPUTS:
            fp[f"mapping {f.name}"] = _sha(f.read_bytes())
    tables = sorted(TABLES_DIR.glob("*.csv"))
    fp["tables"] = _sha("".join(f"{t.name}:{t.stat().st_size}:{int(t.stat().st_mtime)}" for t in tables).encode())
    for up in PIPELINE:
        if up.id >= phase.id:
            break
        rec = read_record(up)
        fp[f"phase {up.id}"] = rec["run_id"] if rec else "never run"
    lock = ROOT / "uv.lock"
    if lock.exists():
        fp["uv.lock"] = _sha(lock.read_bytes())
    return fp


def stale_reasons(phase: Phase) -> list[str]:
    rec = read_record(phase)
    if rec is None:
        return ["never run"]
    if rec["status"] != "passed":
        return [f"last run {rec['status']}"]
    if rec.get("until") is not None:
        return [f"last run stopped after step {rec['until']}"]
    now = fingerprint(phase)
    return [f"{k} changed" for k in sorted(set(now) | set(rec["inputs"])) if now.get(k) != rec["inputs"].get(k)]


# ---- step execution ----------------------------------------------------------------------------------------------

class _Instrument(ast.NodeTransformer):
    """`assert test, msg` -> `if not __check__("test", test): raise AssertionError(msg)`; last expression -> __show__."""

    def __init__(self, source: str) -> None:
        self.source = source

    def visit_Assert(self, node: ast.Assert) -> ast.AST:
        statement = ast.get_source_segment(self.source, node.test) or ast.unparse(node.test)
        check = ast.Call(ast.Name("__check__", ast.Load()), [ast.Constant(statement), node.test], [])
        exc = ast.Call(ast.Name("AssertionError", ast.Load()), [node.msg] if node.msg else [], [])
        return ast.copy_location(ast.If(ast.UnaryOp(ast.Not(), check), [ast.Raise(exc, None)], []), node)


def _compile(source: str, filename: str):
    tree = _Instrument(source).visit(ast.parse(source, filename))
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        value = tree.body[-1].value
        tree.body[-1] = ast.copy_location(ast.Expr(ast.Call(ast.Name("__show__", ast.Load()), [value], [])), tree.body[-1])
    ast.fix_missing_locations(tree)
    linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)
    return compile(tree, filename, "exec")


def _preview(obj) -> dict | None:
    """A JSON-safe view of what a notebook would display."""
    if obj is None:
        return None
    try:
        import pandas as pd
        if isinstance(obj, pd.Series):
            obj = obj.to_frame()
        if isinstance(obj, pd.DataFrame):
            head = obj.head(MAX_ROWS)
            split = json.loads(head.to_json(orient="split", default_handler=str, date_format="iso"))
            return {"kind": "table", "columns": [" / ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in obj.columns],
                    "index_name": " / ".join(str(n) for n in obj.index.names if n is not None),
                    "index": [" / ".join(map(str, i)) if isinstance(i, tuple) else str(i) for i in head.index],
                    "rows": split["data"], "total_rows": len(obj)}
        if hasattr(pd.io.formats.style, "Styler") and isinstance(obj, pd.io.formats.style.Styler):
            return _preview(obj.data)
    except Exception:  # noqa: BLE001 - previews must never break a run
        pass
    kind = type(obj).__name__
    if kind == "Image" and getattr(obj, "filename", None):
        path = Path(obj.filename).resolve()
        return {"kind": "image", "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)}
    if kind == "Markdown":
        return {"kind": "markdown", "text": str(obj.data)[:MAX_TEXT]}
    return {"kind": "text", "text": repr(obj)[:MAX_TEXT]}


def _snapshot(phase: Phase) -> dict[Path, tuple[int, int]]:
    files = {}
    for root in (DATA_DIR / phase.folder, REPORTS_DIR):
        if root.exists():
            for f in root.rglob("*"):
                if f.is_file() and f.name != RUN_FILE:
                    st = f.stat()
                    files[f] = (st.st_mtime_ns, st.st_size)
    return files


def _describe(path: Path) -> dict:
    info = {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size}
    try:
        if path.suffix == ".parquet":
            import pyarrow.parquet as pq
            meta = pq.read_schema(path)
            info |= {"kind": "table", "rows": pq.read_metadata(path).num_rows, "columns": [n for n in meta.names if not n.startswith("__")]}
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8") as fh:
                header = fh.readline().rstrip("\n")
                rows = sum(1 for _ in fh)
            info |= {"kind": "table", "rows": rows, "columns": header.split(",")}
        elif path.suffix in (".png", ".svg"):
            info["kind"] = "figure"
        elif path.suffix == ".md":
            info["kind"] = "report"
        else:
            info["kind"] = "file"
    except Exception:  # noqa: BLE001
        info["kind"] = "file"
    return info


def run_phase(phase: Phase, until: int | None = None, echo: bool = True) -> dict:
    """Run a phase's steps in order (up to `until`), write and return its run record."""
    steps = to_steps(read_cells(phase.script))
    record = {"run_id": uuid.uuid4().hex[:12], "phase": phase.id, "title": phase.title,
              "started": datetime.now(timezone.utc).isoformat(timespec="seconds"), "finished": None,
              "status": "running", "until": until, "git": _git(), "seed": SEED, "python": sys.version.split()[0],
              "inputs": fingerprint(phase), "steps": []}
    out_dir = DATA_DIR / phase.folder
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / RUN_FILE).write_text(json.dumps(record, indent=1), encoding="utf-8")

    import IPython.core.display_functions as display_functions
    import IPython.display as ipy_display
    import matplotlib
    matplotlib.use("Agg")

    current: dict = {}

    def check(statement: str, passed) -> bool:
        ok = bool(passed)
        entry = current["checks"].setdefault(statement, {"statement": statement, "passed": 0, "failed": 0})
        entry["passed" if ok else "failed"] += 1
        return ok

    def show(*objs, **_kwargs) -> None:
        for obj in objs:
            p = _preview(obj)
            if p and len(current["previews"]) < MAX_PREVIEWS:
                current["previews"].append(p)

    namespace = {"__name__": "__main__", "__check__": check, "__show__": show, "display": show}  # display: a Jupyter built-in
    saved = (ipy_display.display, display_functions.display, os.getcwd())
    ipy_display.display = display_functions.display = show
    (ROOT / "notebooks").mkdir(exist_ok=True)  # absent in the Docker image
    os.chdir(ROOT / "notebooks")  # the phase code finds the project root as Path.cwd().parent, as in the notebook
    status = "passed"
    try:
        for step in steps:
            if until is not None and step.index > until:
                break
            current.clear()
            current |= {"index": step.index, "title": step.title, "note": step.note, "status": "running",
                        "checks": {}, "previews": [], "log": [], "outputs": [], "stdout": "", "error": None}
            if echo:
                print(f"[{phase.id}] step {step.index}: {step.title} …", flush=True)
            before, log_len = _snapshot(phase), len(namespace.get("LOG", []) or [])
            start = time.perf_counter()
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer):
                    for j, source in enumerate(step.code):
                        exec(_compile(source, f"<{phase.name} step {step.index}.{j}>"), namespace)
                current["status"] = "passed"
            except BaseException as exc:  # noqa: BLE001 - recorded, then the run stops
                current["status"] = "failed"
                current["error"] = {"type": type(exc).__name__, "message": str(exc)[:MAX_TEXT],
                                    "traceback": traceback.format_exc()[-MAX_TEXT:]}
                status = "failed"
                if isinstance(exc, KeyboardInterrupt):
                    raise
            finally:
                current["duration_s"] = round(time.perf_counter() - start, 2)
                current["stdout"] = buffer.getvalue()[-MAX_TEXT:]
                log = namespace.get("LOG")
                if isinstance(log, list):
                    current["log"] = json.loads(json.dumps(log[log_len:], default=str))
                after = _snapshot(phase)
                current["outputs"] = [_describe(f) for f in sorted(after) if before.get(f) != after[f]]
                current["checks"] = list(current["checks"].values())
                record["steps"].append(dict(current))
                (out_dir / RUN_FILE).write_text(json.dumps(record, indent=1, default=str), encoding="utf-8")
            if echo:
                c = current["checks"]
                print(f"      {current['status']} in {current['duration_s']} s; checks {sum(x['failed'] == 0 for x in c)}/{len(c)} passed; "
                      f"{len(current['outputs'])} outputs", flush=True)
                if current["error"]:
                    print(current["error"]["traceback"], file=sys.stderr)
            if status == "failed":
                break
    finally:
        ipy_display.display, display_functions.display = saved[0], saved[1]
        os.chdir(saved[2])
        import matplotlib.pyplot as plt
        plt.close("all")
    record["status"] = status
    record["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out_dir / RUN_FILE).write_text(json.dumps(record, indent=1, default=str), encoding="utf-8")
    return record


# ---- CLI ---------------------------------------------------------------------------------------------------------

def status_table() -> list[dict]:
    rows = []
    for phase in PIPELINE:
        rec = read_record(phase)
        reasons = stale_reasons(phase)
        rows.append({"phase": phase.id, "title": phase.title, "status": rec["status"] if rec else "not run",
                     "finished": rec["finished"] if rec else None, "run_id": rec["run_id"] if rec else None,
                     "stale": bool(reasons), "reasons": reasons})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="status, all, or a phase id (00–06)")
    parser.add_argument("--until", type=int, help="last step to run")
    parser.add_argument("--force", action="store_true", help="with all: run every phase, stale or not")
    args = parser.parse_args()
    if args.target == "status":
        for r in status_table():
            print(f"{r['phase']} {r['title']:<22} {r['status']:<8} {r['finished'] or '':<26} "
                  f"{'STALE: ' + '; '.join(r['reasons']) if r['stale'] else 'up to date'}")
        return
    phases = PIPELINE if args.target == "all" else (get_phase(args.target),)
    for phase in phases:
        if args.target == "all" and not args.force and not stale_reasons(phase):
            print(f"[{phase.id}] up to date, skipped")
            continue
        record = run_phase(phase, until=args.until if args.target != "all" else None)
        if record["status"] != "passed":
            sys.exit(f"[{phase.id}] failed at step {record['steps'][-1]['index']}; later phases not run")


if __name__ == "__main__":
    main()
