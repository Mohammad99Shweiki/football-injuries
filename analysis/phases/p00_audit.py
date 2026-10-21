"""Phase 00: Data audit. Cells in the percent format; run with `python -m analysis.run 00`, notebook built by `scripts/notebooks/build_notebook.py`."""

# %% [markdown]
# # 00 · Data audit
#
# Phase 0 of `docs/ANALYSIS_PLAN.md`. The logic lives in `analysis/audit.py`; this notebook runs it and shows the report.
# Writes `reports/00_data_audit.md`, `reports/00_missingness.csv` and `reports/figures/00_*.png`.

# %%
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.cwd().parent))  # project root, for the analysis package

from IPython.display import Markdown
from analysis import audit

# %%
report = audit.run()
Markdown(report.replace('](figures/', '](../reports/figures/'))
