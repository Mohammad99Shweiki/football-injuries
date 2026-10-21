"""
Local dashboard server: serves the built React app (dashboard/dist) and the run API, on 127.0.0.1 only.

  GET  /api/status       live run status (polled every second)
  GET  /api/validation   validation report (computed after each run, cached)
  POST /api/control      {"action": "start" | "smoke_test" | "pause" | "resume" | "requeue",
                          "flags": {"dry_run": bool, "limit": int | null}, "ids": [...]}

No auth: it never listens beyond localhost.
"""

import json
import os
import threading
import traceback
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pipeline
from collect import smoke
from collect.common import Manifest, PauseGate, RunContext, Selection, log
from collect.config import ROOT, SCRAPER_DIR
from collect.status import RunStatus, StatusFlusher
from validate import build_report

# 127.0.0.1 by default. The Docker image sets 0.0.0.0 and publishes the port to the host's 127.0.0.1 only.
HOST = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("DASHBOARD_PORT", "8765"))
DIST = SCRAPER_DIR / "dashboard" / "dist"


class Busy(Exception):
    """A run is already in progress."""


class RunController:
    """Owns the single run slot: starts runs in a worker thread, pauses/resumes them, re-queues failures."""

    def __init__(self, status: RunStatus) -> None:
        self.status = status
        self.gate = PauseGate()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._report: dict | None = None
        self._last_flags = {"dry_run": False, "limit": None}
        self.status.set_smoke(smoke.load())

    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, *, mode: str, dry_run: bool = False, limit: int | None = None) -> None:
        with self._lock:
            if self.busy:
                raise Busy("a run is already in progress")
            if mode == "smoke":
                plan = pipeline.RunPlan.smoke(dry_run=dry_run)
            else:
                plan = pipeline.RunPlan(Selection(limit=limit, dry_run=dry_run))
                self._last_flags = {"dry_run": dry_run, "limit": limit}
            self.gate.resume()
            self.status.begin(mode=mode, dry_run=dry_run, limit=limit)
            self._report = None
            self._thread = threading.Thread(target=self._run, args=(plan,), daemon=True, name=f"run-{mode}")
            self._thread.start()

    def _run(self, plan: pipeline.RunPlan) -> None:
        try:
            pipeline.run(RunContext(Manifest(), self.status, self.gate), plan)
            if plan.mode == "smoke" and not plan.selection.dry_run:
                findings = smoke.findings()
                smoke.save(findings)
                self.status.set_smoke(findings)
        except Exception:  # keep the server alive; the traceback is in the terminal
            traceback.print_exc()
        finally:
            self.status.set_phase("finished")
            self._report = None

    def pause(self) -> None:
        if self.busy:
            self.gate.pause()
            self.status.set_phase("paused")

    def resume(self) -> None:
        if self.busy:
            self.gate.resume()
            self.status.set_phase("running")

    def requeue(self, ids: list[str]) -> int:
        """Delete the stored files behind `f:` ids; failed requests (`m:` ids) have no file. Then re-run."""
        removed = 0
        for item in ids:
            if item.startswith("f:") and (path := (ROOT / item[2:]).resolve()).is_relative_to(ROOT / "data" / "raw"):
                path.unlink(missing_ok=True)
                removed += 1
        if not self.busy:
            self.start(mode="full", **self._last_flags)
        return removed

    def report(self) -> dict:
        """Validation JSON; computed once per finished run (it scans the raw store)."""
        if self._report is None:
            self._report = build_report(pipeline.last_run())
        return self._report


def make_handler(controller: RunController) -> type[SimpleHTTPRequestHandler]:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, directory=str(DIST), **kwargs)

        def log_message(self, format: str, *args) -> None:  # keep the terminal for collector logs
            pass

        def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/api/status":
                return self._json(controller.status.snapshot())
            if path == "/api/validation":
                return self._json(controller.report())
            if path.startswith("/api/"):
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            if not (DIST / path.lstrip("/")).is_file():
                self.path = "/index.html"  # client-side routes (e.g. /validation)
            return super().do_GET()

        def do_POST(self) -> None:
            if self.path != "/api/control":
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                action = body.get("action")
                flags = body.get("flags") or {}
                limit = flags.get("limit")
                if limit is not None and (not isinstance(limit, int) or limit < 1):
                    return self._json({"error": "limit must be an integer >= 1"}, HTTPStatus.BAD_REQUEST)
                if action in ("start", "smoke_test"):
                    controller.start(mode="smoke" if action == "smoke_test" else "full", dry_run=bool(flags.get("dry_run")), limit=limit)
                elif action == "pause":
                    controller.pause()
                elif action == "resume":
                    controller.resume()
                elif action == "requeue":
                    return self._json({"ok": True, "removed": controller.requeue(list(body.get("ids") or []))})
                else:
                    return self._json({"error": f"unknown action {action!r}"}, HTTPStatus.BAD_REQUEST)
                return self._json({"ok": True})
            except Busy as exc:
                return self._json({"error": str(exc)}, HTTPStatus.CONFLICT)
            except ValueError:
                return self._json({"error": "invalid JSON"}, HTTPStatus.BAD_REQUEST)

    return Handler


def serve(controller: RunController) -> ThreadingHTTPServer:
    """Start the server in a background thread and return it."""
    if not (DIST / "index.html").exists():
        log("serve", "dashboard/dist is missing: run `npm run build` in dashboard/ (the API still works)")
    server = ThreadingHTTPServer((HOST, PORT), make_handler(controller))
    threading.Thread(target=server.serve_forever, daemon=True, name="http").start()
    StatusFlusher(controller.status).start()
    return server


def url() -> str:
    return f"http://{'127.0.0.1' if HOST == '0.0.0.0' else HOST}:{PORT}"


if __name__ == "__main__":
    import time

    serve(RunController(RunStatus()))
    print(f"Dashboard: {url()}", flush=True)
    while True:
        time.sleep(3600)
