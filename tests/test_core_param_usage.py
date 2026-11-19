"""The usage scan ``core/param_usage.py`` (``docs/core.md``, "The parameter files").

- Every product reads every item of its layers through a reachable literal ``param`` call,
  and a core cell counts for a product only where it is reachable.
- On a scratch copy of RLV the scan reports an unused item of either product layer, a call
  to a missing item, an undeclared indirect read, a declared item no layer holds, a declared
  cell that does not exist, a read around ``param`` and a product-defined core path, counts a
  declared indirect read, and names an unused core item; a core item read by one product is
  used.

That the core file has no unused item is checked in ``tests/test_core.py``, beside the test
that reads ``valuation_year``.
"""
from __future__ import annotations

import modelx as mx
import pytest

from helpers import (CORE_ITEMS, MODELS, add_layer_rows, drop_layer_rows, param_usage,
                     product_copy)


def _usage_copy(tmp_path, name: str, edit=None):
    """The scan of a scratch RLV copy, after ``edit(folder)`` changed its files, and the copy;
    the caller closes it."""
    folder = product_copy(tmp_path, "risikolebensversicherung")
    if edit is not None:
        edit(folder)
    return mx.read_model(folder / MODELS["risikolebensversicherung"], name=name)


def _add_cell(model, space: str, source: str) -> None:
    name = source.split("(", 1)[0].removeprefix("def ")
    model.spaces[space].new_cells(name=name, formula=source)


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_usage_scan_finds_no_problem(product, product_models):
    """Every shipped product reads every item of its layers, calls no missing item, reads
    no parameter indirectly and does not bypass ``param``."""
    model = product_models(product)
    usage = param_usage.scan(model)
    assert usage.problems == []
    assert usage.indirect == {}
    assert usage.reads and set(usage.reads) <= set(model.Data.param_dict())
    assert {"param", "param_dict", "param_layers", "param_rows",
            "param_paths"} <= usage.reachable


def test_the_usage_scan_counts_a_core_cell_only_where_it_is_reachable(product_models):
    """Pflege reads ``expense_infl`` through the core's ``expense_infl()``, RLV's
    ``omega_age()`` is inherited but reached by nothing."""
    pflege = param_usage.scan(product_models("pflegerentenversicherung"))
    assert "expense_infl" in pflege.reads["expense_infl"]
    rlv = param_usage.scan(product_models("risikolebensversicherung"))
    assert "omega_age" not in rlv.reachable and "omega_age" not in rlv.reads
    assert "expenses_claim" in rlv.reads["expense_claim_pp_once"]


def test_the_usage_scan_reports_an_unused_item_in_each_product_layer(tmp_path):
    def edit(folder):
        add_layer_rows(folder / "param_tariff_type.csv", {"probe_unused": "1.5"})
        add_layer_rows(folder / "param_tariff.csv", {"probe_unused_tariff": "2.5"})

    copy = _usage_copy(tmp_path, "UnusedProbe", edit)
    try:
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 2, problems
    assert "'probe_unused'" in problems[0] and "tariff_type layer" in problems[0]
    assert "param_tariff_type.csv" in problems[0]
    assert "'probe_unused_tariff'" in problems[1] and "tariff layer" in problems[1]
    assert "param_tariff.csv" in problems[1]


def test_the_usage_scan_reports_a_call_to_a_missing_item(tmp_path):
    def edit(folder):
        drop_layer_rows(folder / "param_tariff_type.csv", "expense_claim_pp_once")

    copy = _usage_copy(tmp_path, "MissingProbe", edit)
    try:
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "'expense_claim_pp_once'" in problems[0] and "expenses_claim" in problems[0]
    assert "no layer" in problems[0]


INDIRECT_CELL = ('def probe_indirect():\n'
                 '    name = "expense_infl"\n'
                 '    return data.param(name)\n')


def test_the_usage_scan_reports_an_undeclared_indirect_read(tmp_path):
    copy = _usage_copy(tmp_path, "IndirectProbe")
    try:
        _add_cell(copy, "Projection", INDIRECT_CELL)
        _add_cell(copy, "Projection", "def probe_reader():\n    return probe_indirect()\n")
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert "probe_indirect" in usage.reachable
    assert len(usage.problems) == 1, usage.problems
    assert "probe_indirect" in usage.problems[0] and "param_indirect()" in usage.problems[0]


def _declare(model, declared: dict) -> None:
    model.Data.cells["param_indirect"].formula = (
        f"def param_indirect():\n    return {declared!r}\n")


def test_the_usage_scan_counts_a_declared_indirect_read(tmp_path):
    copy = _usage_copy(tmp_path, "DeclaredProbe")
    try:
        _add_cell(copy, "Projection", INDIRECT_CELL)
        _declare(copy, {"probe_indirect": ("expense_infl",)})
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert usage.problems == []
    assert usage.indirect == {"probe_indirect": ("expense_infl",)}
    assert "probe_indirect" in usage.reads["expense_infl"]


def test_the_usage_scan_reports_a_declared_item_no_layer_holds(tmp_path):
    copy = _usage_copy(tmp_path, "DeclaredMissingProbe")
    try:
        _add_cell(copy, "Projection", INDIRECT_CELL)
        _declare(copy, {"probe_indirect": ("expense_infl", "probe_missing")})
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "'probe_missing'" in problems[0] and "probe_indirect" in problems[0]


def test_the_usage_scan_reports_a_declared_cell_that_does_not_exist(tmp_path):
    copy = _usage_copy(tmp_path, "DeclaredUnknownProbe")
    try:
        _declare(copy, {"probe_nowhere": ("expense_infl",)})
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "probe_nowhere" in problems[0] and "no cell" in problems[0]


@pytest.mark.parametrize("reader", ["param_dict", "param_layers", "param_rows", "param_paths"])
def test_the_usage_scan_reports_a_read_around_param(tmp_path, reader):
    copy = _usage_copy(tmp_path, "BypassProbe")
    try:
        _add_cell(copy, "Projection", f"def probe_bypass():\n    return data.{reader}()\n")
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "probe_bypass" in problems[0] and reader in problems[0]


@pytest.mark.parametrize(("source", "path"), [
    ("data.param_core_path()", "param_core_path"),
    ("data.param_tariff_path()", "param_tariff_path"),
    ("data.param_file", "param_file"),
])
def test_the_usage_scan_reports_a_read_around_param_through_a_file_path(tmp_path, source,
                                                                         path):
    copy = _usage_copy(tmp_path, "PathBypassProbe")
    try:
        _add_cell(copy, "Projection", f"def probe_path():\n    return {source}\n")
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "probe_path" in problems[0] and path in problems[0]


def test_the_usage_scan_reports_a_product_defined_core_path(tmp_path):
    copy = _usage_copy(tmp_path, "CorePathProbe")
    try:
        copy.Data.cells["param_core_path"].formula = (
            'def param_core_path():\n    return _model.path / "CoreData" / "param_core.csv"\n')
        assert copy.Data.cells["param_core_path"]._is_defined()
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "param_core_path" in problems[0] and "Data defines" in problems[0]


def test_the_usage_scan_reports_a_declared_missing_item_of_an_unreachable_cell(tmp_path):
    """RLV inherits the core's ``omega_age`` unreached; a declared item no layer holds is a
    problem there too."""
    copy = _usage_copy(tmp_path, "DeclaredUnreachableProbe")
    try:
        _declare(copy, {"omega_age": ("probe_missing",)})
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert "omega_age" not in usage.reachable
    assert len(usage.problems) == 1, usage.problems
    assert "'probe_missing'" in usage.problems[0] and "omega_age" in usage.problems[0]


def test_a_core_item_read_by_one_product_is_used():
    """``unused_core_items`` checks the core file across products: an item one product reads
    is used, one that none reads is named."""
    layers = {"core": {"probe_core": 0.125}, "tariff_type": {}}
    reader = param_usage.Usage(layers=layers, reads={"probe_core": frozenset({"cell"})},
                               reachable=frozenset({"cell"}), indirect={}, problems=[],
                               tables={}, choices={})
    other = param_usage.Usage(layers=layers, reads={}, reachable=frozenset(), indirect={},
                              problems=[], tables={}, choices={})
    assert param_usage.unused_core_items([reader, other]) == []
    assert param_usage.unused_core_items([other, other]) == ["probe_core"]


def test_an_unused_core_item_is_named(tmp_path):
    def edit(folder):
        model_dir = folder / MODELS["risikolebensversicherung"]
        add_layer_rows(model_dir / "CoreData" / "param_core.csv", {"probe_core": "0.125"})

    copy = _usage_copy(tmp_path, "UnusedCoreProbe", edit)
    try:
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert usage.problems == []
    assert usage.layers["core"] == {**CORE_ITEMS, "probe_core": 0.125}
    unread = [item for item in CORE_ITEMS if item not in usage.reads]
    assert param_usage.unused_core_items([usage]) == sorted(["probe_core", *unread])
