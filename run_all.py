"""
Run the collection with the dashboard (default), or headless in the terminal.

  python run_all.py                       open the dashboard idle; start runs from it
  python run_all.py --start [flags]       open the dashboard and start a full run right away
  python run_all.py --headless [flags]    no dashboard: collect -> retry -> parse -> validate in the terminal

Flags: --dry-run, --limit N, --leagues ..., --seasons ..., --players N (see README).
"""

import argparse
import time

import pipeline
import serve
from collect.common import Manifest, RunContext, Selection, add_selection_args
from collect.status import RunStatus


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_selection_args(parser)
    parser.add_argument("--players", type=int, help="Transfermarkt T3/T4 for at most N players")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--start", action="store_true", help="start a full run immediately (dashboard on)")
    mode.add_argument("--headless", action="store_true", help="run in the terminal without the dashboard")
    args = parser.parse_args()

    if args.headless:
        plan = pipeline.RunPlan(Selection.from_args(args), args.players)
        pipeline.run(RunContext(Manifest()), plan)
        return

    controller = serve.RunController(RunStatus())
    serve.serve(controller)
    print(f"Dashboard: {serve.url()}", flush=True)
    if args.start:
        controller.start(mode="full", dry_run=args.dry_run, limit=args.limit)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nStopped. Everything fetched so far is saved; run again to continue.")


if __name__ == "__main__":
    main()
