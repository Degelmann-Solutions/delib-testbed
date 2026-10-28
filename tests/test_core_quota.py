"""The core quota ``tools/core_quota.py`` and its lower bound (``docs/core.md``).

The tool runs once per product in separate processes started together in a session fixture,
each writing its figures with ``--json``; the tests read those figures and call the tool's
``below`` and ``report`` on them, with no second run.

- Every product's quota is at or above ``LOWER_BOUND`` (20 %, Moritz, 2026-10-28).
- A bound just above the lowest measured quota leaves a product below it; at ``LOWER_BOUND``
  none is.
- A quota exactly at the bound passes (``>=``).
- RLV's executed set holds ``model_point`` and ``result_cf``, both from the core.
- A bound above a measured quota makes the report exit 1 and name the product on stderr.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "core_quota.py"
PRODUCTS = sorted(p.name for p in (ROOT / "products").iterdir() if p.is_dir())


def load_tool():
    spec = importlib.util.spec_from_file_location("core_quota", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core_quota = load_tool()


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


@pytest.mark.parametrize("product", PRODUCTS)
def test_every_product_is_at_or_above_the_lower_bound(product, quotas):
    figures = quotas[product]
    assert figures["executed"] == len(figures["executed_cells"]) > 0
    assert figures["core"] == len(figures["core_cells"])
    assert set(figures["core_cells"]) <= set(figures["executed_cells"])
    assert figures["quota"] == figures["core"] / figures["executed"]
    assert figures["quota"] >= core_quota.LOWER_BOUND, (
        f"{product}: {figures['core']} of {figures['executed']} = {figures['quota']:.4f}")


def test_a_bound_above_the_lowest_quota_leaves_a_product_below(quotas):
    lowest = min(figures["quota"] for figures in quotas.values())
    assert core_quota.below(quotas, lowest + 0.001)
    assert core_quota.below(quotas, core_quota.LOWER_BOUND) == []


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
