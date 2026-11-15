"""The core quota ``tools/core_quota.py`` and its lower bound (``docs/core.md``).

The tool runs once per product in separate processes started together in a session fixture,
each writing its figures with ``--json``; the tests read those figures and call the tool's
``below`` and ``report`` on them, with no second run.

- Every product's quota is at or above its bound, ``bound_for(product)``: ``LOWER_BOUND``
  (20 %, Moritz, 2026-10-28), BU its own at its measured quota (epic-night-run, variant c).
- A bound just above the lowest measured quota leaves a product below it; at each product's
  own bound none is.
- A quota exactly at the bound passes (``>=``).
- RLV's executed set holds ``model_point`` and ``result_cf``, both from the core.
- A bound above a measured quota makes the report exit 1 and name the product on stderr.
- The static usage scan ``core/param_usage.py`` reaches every executed ``Projection`` cell of
  every product (``Data`` cells are not compared, the quota does not count them).
- No shipped product executes a cell of the table factory. A scratch copy that reads a
  fixture table through the core's hooks does: the factory's executed cells are listed as
  ``tables.<cell>`` and count as core, beside the hooks of its ``Projection``.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import modelx as mx
import pytest

from test_tables import switched_copy

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "core_quota.py"
PRODUCTS = sorted(p.name for p in (ROOT / "products").iterdir() if p.is_dir())


def load_tool(name: str = "core_quota", path: Path = TOOL):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core_quota = load_tool()
param_usage = load_tool("param_usage", ROOT / "core" / "param_usage.py")


@pytest.fixture(scope="session")
def quotas(tmp_path_factory):
    """Every product's figures, from one ``core_quota.py <product> --json`` run each."""
    tmp_path = tmp_path_factory.mktemp("core_quota")
    processes = {
        product: subprocess.Popen(
            [sys.executable, str(TOOL), product, "--json", str(tmp_path / f"{product}.json")],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for product in PRODUCTS}
    figures = {}
    for product, process in processes.items():
        stdout, stderr = process.communicate(timeout=900)
        assert process.returncode in (0, 1), f"{product}: exit {process.returncode}\n{stderr}"
        written = tmp_path / f"{product}.json"
        assert written.is_file(), f"{product}: no --json output, exit {process.returncode}\n{stderr}"
        figures.update(json.loads(written.read_text(encoding="utf-8")))
        assert stdout.startswith(f"{product}: executed "), stdout
    return figures


def test_the_lower_bound_is_twenty_percent():
    assert core_quota.LOWER_BOUND == 0.20


def test_only_bu_has_its_own_bound_at_its_measured_quota():
    assert core_quota.PRODUCT_BOUNDS == {"berufsunfaehigkeit": 28 / 148}
    assert core_quota.bound_for("berufsunfaehigkeit") == 28 / 148
    assert core_quota.bound_for("risikolebensversicherung") == core_quota.LOWER_BOUND


@pytest.mark.parametrize("product", PRODUCTS)
def test_every_product_is_at_or_above_the_lower_bound(product, quotas):
    figures = quotas[product]
    assert figures["executed"] == len(figures["executed_cells"]) > 0
    assert figures["core"] == len(figures["core_cells"])
    assert set(figures["core_cells"]) <= set(figures["executed_cells"])
    assert figures["quota"] == figures["core"] / figures["executed"]
    assert figures["quota"] >= core_quota.bound_for(product), (
        f"{product}: {figures['core']} of {figures['executed']} = {figures['quota']:.4f}")


def test_a_bound_above_the_lowest_quota_leaves_a_product_below(quotas):
    lowest = min(figures["quota"] for figures in quotas.values())
    assert core_quota.below(quotas, lowest + 0.001)
    assert core_quota.below(quotas) == []


def test_a_quota_exactly_at_the_bound_passes():
    at_bound = {"product": {"executed": 140, "core": 28, "quota": 28 / 140}}
    assert at_bound["product"]["quota"] == core_quota.LOWER_BOUND
    assert core_quota.below(at_bound, core_quota.LOWER_BOUND) == []


def test_rlv_executes_model_point_and_result_cf_from_the_core(quotas):
    figures = quotas["risikolebensversicherung"]
    for name in ("model_point", "result_cf"):
        assert name in figures["executed_cells"]
        assert name in figures["core_cells"]


def test_a_bound_above_a_quota_exits_1_and_names_the_product(quotas, capsys):
    product = min(quotas, key=lambda name: quotas[name]["quota"])
    bound = quotas[product]["quota"] + 0.001
    assert core_quota.report(quotas, bound) == 1
    out, err = capsys.readouterr()
    assert len(out.splitlines()) == len(quotas)
    assert f"BELOW {bound:g}: {core_quota.line(product, quotas[product])}" in err.splitlines()
    assert core_quota.report(quotas) == 0
    _out, err = capsys.readouterr()
    assert err == ""


@pytest.mark.parametrize("product", PRODUCTS)
def test_the_usage_scan_reaches_every_executed_cell(product, quotas):
    """Every ``Projection`` cell a run executes is reachable in the static usage scan; the
    ``Data`` cells are not compared, since the core quota does not record them."""
    folder = ROOT / "products" / product
    model_dir = next(p for p in sorted(folder.iterdir())
                     if p.is_dir() and (p / "_system.json").is_file())
    model = mx.read_model(model_dir)
    try:
        reachable = param_usage.scan(model).reachable
    finally:
        model.close()
    executed = {name for name in quotas[product]["executed_cells"]
                if not name.startswith(core_quota.TABLES_PREFIX)}
    assert executed
    assert sorted(executed - reachable) == []


@pytest.mark.parametrize("product", PRODUCTS)
def test_no_shipped_product_executes_a_cell_of_the_table_factory(product, quotas):
    figures = quotas[product]
    assert not [name for name in figures["executed_cells"] if "." in name]


def test_the_executed_cells_of_the_table_factory_count_as_core(tmp_path, quotas):
    """Index without its own ``mort_rate_at_age``, on a period fixture table: the override is
    gone from the executed product cells, the core's hooks and the factory's cells are in."""
    shipped = quotas["indexpolice"]
    figures = core_quota.measure(switched_copy(tmp_path, "period_fixture"))
    tables = {"tables." + name for name in (
        "definitions", "definition", "parameter", "first_age", "end_age", "select_factors",
        "base_rate", "q", "law_fixture")}
    hooks = {"mort_table_name", "mort_rate_table", "birth_year"}
    assert {name for name in figures["executed_cells"] if "." in name} == tables
    assert set(figures["executed_cells"]) == set(shipped["executed_cells"]) | tables | hooks
    assert set(figures["core_cells"]) == (set(shipped["core_cells"]) | tables | hooks
                                          | {"mort_rate_at_age"})
    assert figures["executed"] == shipped["executed"] + len(tables) + len(hooks)
    assert figures["core"] == shipped["core"] + len(tables) + len(hooks) + 1
    assert figures["quota"] == figures["core"] / figures["executed"]
