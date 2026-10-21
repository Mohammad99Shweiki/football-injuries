"""Small helpers shared by the phase reports (markdown tables, percentages)."""

import pandas as pd


def md_table(df: pd.DataFrame, index: bool = True) -> str:
    """GitHub markdown table (no tabulate dependency)."""
    if index:
        df = df.reset_index()
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "–"
