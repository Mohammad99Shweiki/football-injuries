"""Build phase notebooks from their scripts in analysis/phases/ (the single source of truth).

    uv run --group analysis python scripts/notebooks/build_notebook.py          # every phase
    uv run --group analysis python scripts/notebooks/build_notebook.py 05 06    # some phases

Then execute one as before: `cd notebooks && uv run --group analysis jupyter nbconvert --to notebook --execute --inplace 05_injury_analysis.ipynb`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from analysis.config import PIPELINE, get_phase  # noqa: E402
from analysis.steps import read_cells, to_notebook  # noqa: E402

METADATA = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"}}

phases = [get_phase(k) for k in sys.argv[1:]] or list(PIPELINE)
for phase in phases:
    cells = read_cells(phase.script)
    nb = to_notebook(cells, phase.name.split("_", 1)[1], METADATA)
    phase.notebook.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{phase.notebook.relative_to(phase.notebook.parents[1])}: {len(cells)} cells from {phase.script.name}")
