"""What two or more test files share: paths, the products, loaders of the tools and of the
usage scan, pinned data, scratch copies, the parameter layer files as text, and helpers on
modelx errors and formula sources.

No test file imports from another test file what stands here; a helper used by one test
file alone stays in that file.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import shutil
from pathlib import Path

import modelx as mx
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT / "core"
CORE_MODEL = CORE_DIR / "Core"
PRODUCTS_DIR = ROOT / "products"
TOOLS_DIR = ROOT / "tools"
RUNNER = TOOLS_DIR / "run_baseline.py"

# Product folder -> model folder; the same ten products as tests/test_provenance.py.
MODELS = {
    "basisrente": "Basis_DE_S",
    "berufsunfaehigkeit": "BU_DE_S",
    "fondsgebundene_rentenversicherung": "FRV_DE_S",
    "indexpolice": "Index_DE_S",
    "kapitallebensversicherung": "KLV_DE_S",
    "klassische_rentenversicherung": "RV_DE_S",
    "pflegerentenversicherung": "Pflege_DE_S",
    "riester_rente": "Riester_DE_S",
    "risikolebensversicherung": "RLV_DE_S",
    "sofortrente": "Sofort_DE_S",
}


# --------------------------------------------------------------------------- loaders

def load_tool(name: str, path: Path):
    """A plain Python file loaded by path as a module of its own, not entered in
    ``sys.modules``: a tool of ``tools/`` or the usage scan beside the core model."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    """The runner ``tools/run_baseline.py``, a fresh module on every call."""
    return load_tool("run_baseline", RUNNER)


# The static usage scan ``core/param_usage.py``, a plain module beside the core model, loaded
# once for every test file.
param_usage = load_tool("param_usage", CORE_DIR / "param_usage.py")


# --------------------------------------------------------------------------- pinned data

# The items of the core file ``core/Core/Data/param_core.csv``, as their former Python literals;
# ``tests/test_core.py`` checks every product's core layer against them.
CORE_ITEMS = {
    "rate_cap_eps": 1e-12,
    "check_tol": 1e-08,
    "suicide_years": 3,
    "surr_spread_years": 5,
    "runoff_months": 3,
    "tax_step_min_year": 13,
    "tax_step_age": 62,
    "mmkt_return_ann": 0.015,
    "expense_infl": 0.02,
    "zillmer_cap_bsum": 0.025,
    "valuation_year": 2027,
    "grundzulage": 175.0,
    "kinderzulage_pre2008": 185.0,
    "kinderzulage_post2008": 300.0,
    "berufseinsteiger_bonus": 200.0,
    "mindesteigenbeitrag_rate": 0.04,
    "foerder_ceiling": 2100.0,
    "sockelbeitrag": 60.0,
    "zulage_lag": 1,
    "guar_carve_out_cap": 0.2,
    "teilkapital_cap": 0.3,
    "kleinbetrag_threshold_mth": 59.33,
}

# The items that moved from a cost table to the tariff-type file (docs/core.md, "Contract data
# and charges"), with the value the table held.
MOVED_COST_ITEMS = {
    "kapitallebensversicherung": {
        "load_acq_bsum_once": 0.025, "load_admin_prem_inst": 0.03, "load_admin_sum_ann": 0.0015,
        "expense_acq_pp_once": 300.0, "expense_admin_pp_ann": 45.0,
        "expense_claim_pp_once": 120.0, "comm_acq_bsum_once": 0.025,
        "comm_renew_prem_inst": 0.015},
    "basisrente": {
        "charge_acq_sp_once": 0.025, "charge_admin_prem_inst": 0.075,
        "charge_admin_av_ann": 0.0035, "charge_admin_pp_ann": 36.0,
        "terminal_bonus_rate": 0.04, "expense_acq_pp_once": 250.0,
        "comm_acq_bsum_once": 0.025, "comm_renew_prem_inst": 0.015,
        "expense_admin_pp_ann": 60.0, "expense_annuity_pp_ann": 36.0},
    "klassische_rentenversicherung": {
        "charge_admin_prem_inst": 0.04, "charge_admin_av_ann": 0.002,
        "charge_admin_pup_av_ann": 0.003, "min_annuity_mth": 30.0},
    "fondsgebundene_rentenversicherung": {"acq_spread_years": 5},
}


# --------------------------------------------------------------------------- folders and runs

def product_copy(tmp_path, product: str, name: str | None = None) -> Path:
    """A scratch copy of a product folder in ``tmp_path``, under the product's name or
    ``name``; ``copytree`` follows the core symlinks, so the copy holds real files."""
    folder = tmp_path / (name or product)
    shutil.copytree(PRODUCTS_DIR / product, folder)
    return folder


def folder_hashes(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def edit_point(folder: Path, point_id: int, **changes: str) -> None:
    """Change columns of one model point in a scratch copy, as text."""
    path = folder / "model_point_table.csv"
    lines = path.read_bytes().decode("ascii").split("\n")
    columns = lines[0].split(",")
    values = lines[point_id].split(",")
    assert values[0] == str(point_id)
    for column, value in changes.items():
        assert values[columns.index(column)] != value
        values[columns.index(column)] = value
    lines[point_id] = ",".join(values)
    path.write_bytes("\n".join(lines).encode("ascii"))


def parse_output(stdout: str) -> dict[str, str]:
    """The ``key: value`` lines a tool prints, as a dict."""
    return dict(line.split(": ", 1) for line in stdout.splitlines() if ": " in line)


# --------------------------------------------------------------------------- layer files

# The parameter layer files of a product folder, in the loader's order; the tariff file is
# optional.
LAYER_FILES = ("param_tariff_type.csv", "param_tariff.csv")


def read_layer(path: Path) -> pd.DataFrame:
    """A parameter layer file as the loader reads it, as text (``dtype=str``,
    ``keep_default_na=False``), under its header's columns.

    No value is typed here: the typing is the loader's, and a typed value comes from a
    model's ``Data.param_layers()``.
    """
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def drop_layer_rows(path: Path, *items: str) -> None:
    """Drop the rows of ``items`` from a parameter layer file; each must stand in it once.

    The file is rewritten from its own lines, so every other row keeps its text byte for
    byte (an integer stays ``3``, not ``3.0``).
    """
    lines = list(io.StringIO(path.read_bytes().decode("utf-8"), newline=""))
    reader = csv.reader(lines)
    kept, dropped, start = [], [], 0
    for number, row in enumerate(reader):
        if number and row and row[0] in items:
            dropped.append(row[0])
        else:
            kept += lines[start:reader.line_num]
        start = reader.line_num
    assert sorted(dropped) == sorted(items), (path, items, dropped)
    path.write_bytes("".join(kept).encode("utf-8"))


def add_layer_rows(path: Path, values: dict[str, str], basis: str = "") -> None:
    """Append one row per item to a parameter layer file, its value as text, in the file's
    columns, with ``basis`` and the provenance of a test fixture.

    A file that does not exist is created with the columns of the layer files.
    """
    text = (path.read_text(encoding="utf-8") if path.exists()
            else "item,value,basis,provenance\n")
    columns = text.splitlines()[0].split(",")
    for item, value in values.items():
        row = {"item": item, "value": value, "basis": basis,
               "provenance": "[std] test fixture"}
        text += ",".join(row.get(column, "") for column in columns) + "\n"
    path.write_text(text, encoding="utf-8")


def table_choices(folder: Path) -> dict[str, str]:
    """The table choices of a product folder's layer files: ``{item: table}`` for each
    ``*_table`` item, read as text."""
    found = {}
    for name in LAYER_FILES:
        if (folder / name).is_file():
            table = read_layer(folder / name)
            found.update({item: value for item, value in zip(table["item"], table["value"])
                          if item.endswith("_table") and value})
    return found


# --------------------------------------------------------------------------- modelx errors

def raised_value_error(raised, message: str) -> bool:
    """Whether a modelx error carries a ``ValueError`` with ``message``.

    modelx re-raises a formula's error as a FormulaError without chaining it, and names the
    original type in its message.
    """
    chain, error = [], raised.value
    while error is not None and error not in chain:
        chain.append(error)
        error = error.__cause__ or error.__context__
    return (any(isinstance(e, ValueError) for e in chain)
            or f"ValueError: {message}" in str(raised.value))


def loader_error(model_dir: Path, name: str, item: str = "check_tol") -> str:
    """The error line of the loader's error on ``param(item)`` in a scratch copy, which must be
    a ``ValueError``.

    modelx wraps it in a ``FormulaError`` whose text also holds the formula source; only the
    line before ``Formula traceback:`` is the raised error.
    """
    copy = mx.read_model(model_dir, name=name)
    try:
        with pytest.raises(Exception) as raised:
            copy.Data.param(item)
    finally:
        copy.close()
    if isinstance(raised.value, ValueError):
        return f"ValueError: {raised.value}"
    head = str(raised.value).split("Formula traceback:", 1)[0]
    line = [text for text in head.splitlines() if text.strip()][-1]
    assert line.startswith("ValueError: "), str(raised.value)
    return line


# --------------------------------------------------------------------------- sources and values

def formula_cells(path: Path):
    """The formula cells of a ``Projection``, as docs/roadmap.md, "The new M", counts them:
    module-level ``def``s and non-underscore ``name = lambda``, each with its name."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef):
            yield node.name, node
        elif (isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda)
              and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
              and not node.targets[0].id.startswith("_")):
            yield node.targets[0].id, node.value


def same_value(a, b) -> bool:
    return a == b or (pd.isna(a) and pd.isna(b))
