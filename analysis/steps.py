"""Phase scripts: each phase is one Python file in `analysis/phases/` with cells in the percent format (`# %%`).

The same file is run step by step by `analysis.run` and turned into the phase notebook by
`scripts/notebooks/build_notebook.py`. A step starts at a markdown cell whose first line is `## Step N. Title`;
everything before the first step (title, setup imports) is step 0, "Setup".
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

CODE_MARK = "# %%"
MARKDOWN_MARK = "# %% [markdown]"
STEP_HEADING = re.compile(r"^## Step (\d+)\.\s*(.+)$")


@dataclass
class Cell:
    kind: str  # "markdown" or "code"
    source: str


@dataclass
class Step:
    index: int
    title: str
    note: str  # markdown of the step (heading excluded)
    cells: list[Cell] = field(default_factory=list)

    @property
    def code(self) -> list[str]:
        return [c.source for c in self.cells if c.kind == "code"]


def read_cells(path: Path) -> list[Cell]:
    """Parse a percent-format script; markdown lines lose their leading '# ' (or '#')."""
    cells: list[Cell] = []
    kind, lines = None, []

    def flush() -> None:
        if kind is None:
            return
        text = "\n".join(lines).strip("\n")
        if kind == "markdown":
            text = "\n".join(line[2:] if line.startswith("# ") else line[1:] if line.startswith("#") else line
                             for line in text.splitlines())
        cells.append(Cell(kind, text))

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == MARKDOWN_MARK:
            flush()
            kind, lines = "markdown", []
        elif line.strip() == CODE_MARK:
            flush()
            kind, lines = "code", []
        elif kind is not None:
            lines.append(line)
    flush()
    return cells


def write_cells(cells: list[Cell], path: Path, docstring: str) -> None:
    """Write cells in the percent format (used once to convert the notebook builders; kept for round-trip tests)."""
    out = [f'"""{docstring}"""', ""]
    for cell in cells:
        if cell.kind == "markdown":
            out.append(MARKDOWN_MARK)
            out += [f"# {line}" if line else "#" for line in cell.source.splitlines()]
        else:
            out.append(CODE_MARK)
            out += cell.source.splitlines()
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def to_steps(cells: list[Cell]) -> list[Step]:
    steps = [Step(0, "Setup", "")]
    for cell in cells:
        first = cell.source.splitlines()[0] if cell.source else ""
        match = STEP_HEADING.match(first) if cell.kind == "markdown" else None
        if match:
            note = "\n".join(cell.source.splitlines()[1:]).strip()
            steps.append(Step(int(match.group(1)), match.group(2).strip(), note, [cell]))
        else:
            steps[-1].cells.append(cell)
    if steps[0].note == "" and steps[0].cells and steps[0].cells[0].kind == "markdown":
        steps[0].note = steps[0].cells[0].source
    return steps


def to_notebook(cells: list[Cell], stem: str, metadata: dict) -> dict:
    nb_cells = []
    for i, cell in enumerate(cells):
        nb = {"cell_type": cell.kind, "id": f"{stem}-{i:02d}", "metadata": {}, "source": cell.source.splitlines(keepends=True)}
        if cell.kind == "code":
            nb |= {"execution_count": None, "outputs": []}
        nb_cells.append(nb)
    return {"cells": nb_cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
