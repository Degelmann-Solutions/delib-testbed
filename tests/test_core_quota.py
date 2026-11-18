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
- Only a switched product executes cells of the table factory: Index, BU, RV, KLV, FRV, RLV,
  Basis and Riester do,
  the cells behind ``q`` with the law ``makeham``, listed as ``tables.<cell>`` and counted as
  core beside the hooks of their ``Projection``; the other two execute none. RLV, whose
  table depends on the life, executes no hook of the core: its hook and the cell that maps
  the smoker status to a role are product cells. BU's hook for
  its second role, ``mort_rate_dis_at_age``, is a product cell, and its tariff rates execute
  the core's unisex blend. RV, on the generational table, executes the trend cells of the
  factory too, the core's tariff rate on the unisex blend and ``omega_age_table``; its
  ``birth_year`` and ``omega_age`` are product cells. KLV executes the core's tariff rate on
  the unisex blend, which its premium and its reserves read, and no mortality cell of its
  own but the factor. FRV executes the core's tariff rate on the unisex blend below its
  *Risikobeitrag* and, of its own mortality cells, the factor and the two linear monthly
  rates. Basis, the second reader of the generational table, executes its trend cells, the
  core's best estimate on the own sex and ``omega_age_table``, and no tariff rate from the
  table; its ``birth_year``, ``omega_age`` and ``mort_be_factor`` are product cells.
  Riester, whose main role is a period table and whose second role the generational one,
  executes the trend cells, the core's best estimate of the accumulation on the own sex and
  the unisex blend of its annuity factor; its ``birth_year``, ``omega_age``, its override of
  ``mort_rate_table``, the payout hook ``annuity_mort_rate``, ``mort_rate`` and
  ``mort_be_factor`` are product cells, and ``omega_age_table`` does not run.
- A scratch copy of Index on a fixture table executes the same cells with the fixture law in
  place of ``makeham``; one with a ``mort_rate_at_age`` of its own and no choice executes
  neither the factory's cells nor the hooks, and its override counts as a product cell.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import modelx as mx
import pytest

from test_tables import SWITCHED, switched_copy, unswitched_copy

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


# What a product switched to the factory executes for a period table without selection: the
# cells of the factory behind ``q`` (the law apart) and the core's hooks in ``Projection``.
FACTORY_CELLS = {"tables." + name for name in (
    "definitions", "definition", "parameter", "first_age", "end_age", "select_factors",
    "base_rate", "q")}
FACTORY_HOOKS = {"mort_table_name", "mort_rate_table", "birth_year"}


@pytest.mark.parametrize("product", PRODUCTS)
def test_only_a_switched_product_executes_cells_of_the_table_factory(product, quotas):
    figures = quotas[product]
    executed = {name for name in figures["executed_cells"] if "." in name}
    if product not in SWITCHED:
        assert not executed
        assert not FACTORY_HOOKS - {"birth_year"} & set(figures["executed_cells"])
        return
    assert product in ("basisrente", "berufsunfaehigkeit", "fondsgebundene_rentenversicherung",
                       "indexpolice", "kapitallebensversicherung",
                       "klassische_rentenversicherung", "riester_rente",
                       "risikolebensversicherung")
    trend = {"tables.base_year", "tables.trend", "tables.trend_linear"}
    if product == "riester_rente":
        # two roles on two kinds of table: the period table of the accumulation through the
        # core's hooks but its own read without a birth year, the generational table of the
        # payout through a hook of its own; the annuity factor on the core's unisex blend
        assert executed == FACTORY_CELLS | {"tables.makeham"} | trend
        assert executed <= set(figures["core_cells"])
        assert {"mort_table_name", "mort_rate_at_age", "mort_rate_base", "mort_rate_mth",
                "unisex_blend", "unisex_mix_male", "sex"} <= set(figures["core_cells"])
        own = {"birth_year", "mort_rate_table", "annuity_mort_rate", "mort_rate",
               "mort_be_factor", "omega_age", "horizon_age", "ann_factor"}
        assert own <= set(figures["executed_cells"])
        assert not own & set(figures["core_cells"])
        assert "omega_age_table" not in figures["executed_cells"]
        assert not {"mort_rate_tariff", "mort_rate_tariff_at_age",
                    "calendar_year"} & set(figures["executed_cells"])
        assert sorted(name for name in set(figures["executed_cells"]) - set(figures["core_cells"])
                      if "mort" in name) == [
            "annuity_mort_rate", "mort_be_factor", "mort_rate", "mort_rate_table"]
        assert (figures["executed"], figures["core"]) == (174, 70)
        return
    if product == "risikolebensversicherung":
        # its table depends on the life: the hook on the factory and the cell that maps the
        # smoker status to a role are its own, no hook of the core runs, and of the core's
        # mortality derivation it executes the unisex blend and the tariff rate
        assert executed == FACTORY_CELLS | {"tables.makeham"}
        assert executed <= set(figures["core_cells"])
        assert not FACTORY_HOOKS & set(figures["executed_cells"])
        assert {"unisex_blend", "unisex_mix_male", "mort_rate_tariff", "mort_rate_mth",
                "pols_tariff"} <= set(figures["core_cells"])
        assert sorted(name for name in set(figures["executed_cells"]) - set(figures["core_cells"])
                      if "mort" in name) == [
            "mort_be_factor", "mort_load_tariff", "mort_rate", "mort_rate_at_age",
            "mort_rate_base", "mort_rate_blend", "mort_rate_tariff_base", "mort_table_smoker"]
        assert (figures["executed"], figures["core"]) == (135, 80)
        return
    # the shipped tables are on the law ``makeham``, the select and the generational one too;
    # the generational one brings its base year and its trend
    generational = product in ("basisrente", "klassische_rentenversicherung")
    assert executed == FACTORY_CELLS | {"tables.makeham"} | (trend if generational else set())
    assert executed <= set(figures["core_cells"])
    assert FACTORY_HOOKS | {"mort_rate_at_age"} <= set(figures["executed_cells"])
    # the cohort of a generational table is the product's cell, the neutral one the core's
    assert FACTORY_HOOKS - {"birth_year"} | {"mort_rate_at_age"} <= set(figures["core_cells"])
    assert ("birth_year" in figures["core_cells"]) == (not generational)
    # the best-estimate factor is a product cell, in Index the one mortality cell of its own
    assert "mort_be_factor" in figures["executed_cells"]
    assert "mort_be_factor" not in figures["core_cells"]
    blend = {"mort_rate_tariff_at_age", "unisex_blend", "unisex_mix_male"}
    if product == "berufsunfaehigkeit":
        # the hook of the second role is BU's, the unisex blend of its tariff rates the core's
        assert "mort_rate_dis_at_age" in figures["executed_cells"]
        assert "mort_rate_dis_at_age" not in figures["core_cells"]
        assert blend <= set(figures["core_cells"])
        assert (figures["executed"], figures["core"]) == (165, 48)
    elif product == "basisrente":
        # no tariff rate from the table: the best estimate on the own sex is the core's, the
        # end age the table's; the cohort, the horizon and the factor are its own cells
        assert {"omega_age_table", "mort_rate_at_age", "mort_rate_base", "mort_be_trend",
                "mort_rate", "mort_rate_mth", "sex"} <= set(figures["core_cells"])
        assert not blend & set(figures["executed_cells"])
        assert not {"mort_rate_tariff", "mort_rate_tariff_base",
                    "mort_load_tariff"} & set(figures["executed_cells"])
        assert {"omega_age", "birth_year", "horizon_age"} <= set(figures["executed_cells"])
        assert not {"omega_age", "birth_year", "horizon_age"} & set(figures["core_cells"])
        assert sorted(name for name in set(figures["executed_cells"]) - set(figures["core_cells"])
                      if name.startswith("mort")) == ["mort_be_factor"]
        assert "calendar_year" not in figures["executed_cells"]
        assert (figures["executed"], figures["core"]) == (127, 62)
    elif generational:
        # the tariff rate is the core's, on the unisex blend, and the end age the table's
        tariff = {"mort_rate_tariff", "mort_rate_tariff_base", "mort_load_tariff"}
        assert blend | tariff | {"omega_age_table", "mort_rate_base"} <= set(
            figures["core_cells"])
        assert {"omega_age", "birth_year", "horizon_age"} <= set(figures["executed_cells"])
        assert not {"omega_age", "birth_year", "horizon_age"} & set(figures["core_cells"])
        assert "improve_rate" not in figures["executed_cells"]
        assert (figures["executed"], figures["core"]) == (175, 75)
    elif product == "kapitallebensversicherung":
        # the tariff rate that prices and reserves is the core's, on the unisex blend; of
        # its own mortality cells only the factor is left
        tariff = {"mort_rate_tariff", "mort_rate_tariff_base", "mort_load_tariff"}
        assert blend | tariff | {"mort_rate_base", "mort_rate", "pols_tariff"} <= set(
            figures["core_cells"])
        assert sorted(name for name in set(figures["executed_cells"]) - set(figures["core_cells"])
                      if "mort" in name) == ["mort_be_factor"]
        assert (figures["executed"], figures["core"]) == (184, 94)
    elif product == "fondsgebundene_rentenversicherung":
        # the tariff rate below the Risikobeitrag is the core's, on the unisex blend, and the
        # base of the best estimate the core's, on the own sex; its own mortality cells are
        # the factor and the linear monthly split of both rates
        tariff = {"mort_rate_tariff", "mort_rate_tariff_base", "mort_load_tariff"}
        assert blend | tariff | {"mort_rate_base", "mort_rate", "sex"} <= set(
            figures["core_cells"])
        assert sorted(name for name in set(figures["executed_cells"]) - set(figures["core_cells"])
                      if "mort" in name) == ["mort_be_factor", "mort_rate_mth",
                                             "mort_rate_tariff_mth"]
        assert (figures["executed"], figures["core"]) == (158, 57)
    else:
        assert not blend & set(figures["executed_cells"])


def test_a_copy_on_a_fixture_table_executes_the_fixture_law(tmp_path, quotas):
    """Index on a period fixture table in place of its shipped choice: the same executed
    cells, the fixture law for ``makeham``."""
    shipped = quotas["indexpolice"]
    figures = core_quota.measure(switched_copy(tmp_path, "period_fixture"))
    swap = lambda cells: (set(cells) - {"tables.makeham"}) | {"tables.law_fixture"}  # noqa: E731
    assert {name for name in figures["executed_cells"] if "." in name} == (
        FACTORY_CELLS | {"tables.law_fixture"})
    assert set(figures["executed_cells"]) == swap(shipped["executed_cells"])
    assert set(figures["core_cells"]) == swap(shipped["core_cells"])
    assert (figures["executed"], figures["core"]) == (shipped["executed"], shipped["core"])
    assert figures["quota"] == figures["core"] / figures["executed"] == shipped["quota"]


def test_the_executed_cells_of_the_table_factory_count_as_core(tmp_path, quotas):
    """Index against a copy with a ``mort_rate_at_age`` of its own and no choice: in the
    copy the override is an executed product cell; in Index the core's hooks and the
    factory's cells are executed in its place, all core."""
    shipped = quotas["indexpolice"]
    figures = core_quota.measure(unswitched_copy(tmp_path))
    tables = FACTORY_CELLS | {"tables.makeham"}
    assert not [name for name in figures["executed_cells"] if "." in name]
    assert set(shipped["executed_cells"]) == set(figures["executed_cells"]) | tables | FACTORY_HOOKS
    assert set(shipped["core_cells"]) == (set(figures["core_cells"]) | tables | FACTORY_HOOKS
                                          | {"mort_rate_at_age"})
    assert "mort_rate_at_age" in figures["executed_cells"]
    assert "mort_rate_at_age" not in figures["core_cells"]
    assert shipped["executed"] == figures["executed"] + len(tables) + len(FACTORY_HOOKS)
    assert shipped["core"] == figures["core"] + len(tables) + len(FACTORY_HOOKS) + 1
    assert shipped["quota"] == shipped["core"] / shipped["executed"]
