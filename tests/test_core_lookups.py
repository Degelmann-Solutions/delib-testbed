"""The tables of the core's ``Data`` and the lookups through them (``docs/core.md``): dict
cells, shared caches, cost tables, the products' own tables and schedules.

- The dict cells: every core dict cell of a table a product has equals its reader's
  DataFrame; the lookups through them keep their clamp and errors (the lapse rate beyond the
  table, an unknown ``prem_freq``, a missing ``expense_infl`` row, an issue year outside every
  *Höchstrechnungszins* band), and a table the product lacks is never read.
- The shared caches are read-only: every product's ``model_point()`` and FRV's
  ``charge_row()`` raise on a write.
- The cost tables: Basis', RV's and FRV's ``charge_table.csv`` have the one shape, the key
  ``cost_group`` first, one column per item, ``provenance`` last, one row per group, and no
  item column equal in every row; their model points carry the key ``cost_group``, no
  ``tariff_id`` or ``charge_id``, and an unknown group raises ``KeyError``; KLV has no cost
  table, no Reference ``charge_file``, no cell or column ``cost_id``, and its eight cost items
  are rows of its tariff-type file; each moved item stands in the tariff-type layer at the
  value the table gave.
- RV's and KLV's own dict cells and scenario bounds equal their readers; their
  decrement-closure residual equals the old sum over the exit cells up to floating-point
  noise, on a new and an in-force point; their lookups keep their clamps (the declared rate
  outside the calendar range, the surplus rates and the *Stornoabzug* beyond the last policy
  year, the DeckRV ceilings outside the issue years), ``echt`` instalments carry no loading,
  and an unknown scenario raises.
- Basis' behaviour and surplus tables hold their first and last year, a short table its last
  row, and an unknown table or scenario raises ``KeyError``.
- The schedules: Index' lapse beyond its table, an unknown schedule id and RLV's schedules
  beyond their last year raise ``KeyError``; Riester reads no schedule after conversion, and
  its reference income at zero is the initial income.
"""
from __future__ import annotations

import re

import modelx as mx
import pandas as pd
import pytest

from helpers import (MODELS, MOVED_COST_ITEMS, PRODUCTS_DIR, drop_layer_rows, product_copy,
                     raised_value_error, same_value)


# The core's dict cells: reader -> the file Reference whose presence says a product has it.
DICT_READERS = {
    "model_point_table": "model_point_file",
    "lapse_table": "lapse_file",
    "rentenfaktor_table": "rentenfaktor_file",
    "prem_freq_table": "prem_freq_file",
    "surplus_table": "surplus_file",
    "charge_table": "charge_file",
    "hoechstrechnungszins_table": "hoechstrechnungszins_file",
}


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_dict_cell_equals_its_reader(product, product_models):
    data = product_models(product).Data
    readers = [r for r, ref in DICT_READERS.items() if ref in data.refs]
    assert "model_point_table" in readers
    for reader in readers:
        df = data.cells[reader]()
        table = data.cells[reader + "_dict"]()
        if reader == "model_point_table":
            assert list(table) == list(df.index), reader
            rows = table
        else:
            assert list(table) == list(df.columns), reader
            for column, values in table.items():
                assert list(values) == list(df.index), (reader, column)
            rows = {k: {c: table[c][k] for c in df.columns} for k in df.index}
        for key in df.index:
            for column in df.columns:
                assert same_value(rows[key][column], df.at[key, column]), (reader, key, column)


def test_lapse_rate_beyond_the_table_holds_its_last_row(product_models):
    model = product_models("risikolebensversicherung")
    assert model.Projection.lapse_rate_base._is_derived()
    table = model.Data.lapse_table()
    last = table.index.max()
    item = model.Projection[model.Data.model_point_table().index[0]]
    t = 12 * int(last + 5)
    assert item.policy_year(t) > last
    assert item.lapse_rate_base(t) == float(table.at[last, "lapse_rate"])


@pytest.mark.parametrize("product", sorted(MODELS))
def test_model_point_is_read_only(product, product_models):
    """``model_point()`` is the shared row of ``model_point_table_dict()``, read-only."""
    model = product_models(product)
    point_id = model.Data.model_point_table().index[0]
    row = model.Projection[point_id].model_point()
    shared = model.Data.model_point_table_dict()[point_id]
    before = dict(shared)
    column = "sex" if "sex" in row else next(iter(row))
    with pytest.raises(TypeError):
        row[column] = "M"
    with pytest.raises(TypeError):
        del row[column]
    assert shared == before and dict(row) == before


def test_frv_charge_row_is_read_only(product_models):
    """FRV's ``charge_row()`` is the shared row of ``charge_table_rows()``, read-only."""
    model = product_models("fondsgebundene_rentenversicherung")
    item = model.Projection[model.Data.model_point_table().index[0]]
    row = item.charge_row()
    shared = model.Data.charge_table_rows()[item.cost_group()]
    before = dict(shared)
    column = next(iter(row))
    with pytest.raises(TypeError):
        row[column] = 5
    assert shared == before and dict(row) == before


# The cost tables (docs/core.md, "Contract data and charges"): the products with one, and the
# items that moved from a cost table to the tariff-type file, with the value the table held.
COST_TABLE_PRODUCTS = ("basisrente", "fondsgebundene_rentenversicherung",
                       "klassische_rentenversicherung")


@pytest.mark.parametrize("product", COST_TABLE_PRODUCTS)
def test_a_cost_table_has_the_one_shape_and_no_equal_column(product, product_models):
    data = product_models(product).Data
    assert data.charge_file == "charge_table.csv"
    assert data.charge_table_index() == "cost_group"
    assert data.charge_table_index._is_derived()
    raw = pd.read_csv(data.input_dir() / data.charge_file, dtype=str, keep_default_na=False)
    columns = list(raw.columns)
    assert columns[0] == "cost_group" and columns[-1] == "provenance"
    assert len(columns) > 2
    assert raw["cost_group"].is_unique
    assert len(raw) >= 2
    for column in columns[1:-1]:
        assert data.charge_table()[column].nunique() >= 2, (product, column)
    assert set(data.charge_table_items()) == set(columns[1:-1])


@pytest.mark.parametrize("product", COST_TABLE_PRODUCTS)
def test_the_model_points_read_the_key_cost_group(tmp_path, product, product_models):
    model = product_models(product)
    points = model.Data.model_point_table()
    assert "tariff_id" not in points.columns and "charge_id" not in points.columns
    assert set(points["cost_group"]) <= set(model.Data.charge_table().index)

    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    changed = pd.read_csv(table, dtype=str, keep_default_na=False)
    changed.loc[0, "cost_group"] = "no_such_group"
    changed.to_csv(table, index=False)
    copy = mx.read_model(folder / MODELS[product], name="CostGroupProbe")
    try:
        with pytest.raises(Exception, match=r"KeyError: 'no_such_group'"):
            copy.Projection[int(changed.loc[0, "point_id"])].alpha_rate()
    finally:
        copy.close()


def test_klv_has_no_cost_table(product_models):
    model = product_models("kapitallebensversicherung")
    folder = PRODUCTS_DIR / "kapitallebensversicherung"
    assert not (folder / "cost_table.csv").exists()
    assert "charge_file" not in model.Data.refs
    assert "cost_id" not in model.Projection.cells
    assert "cost_id" not in model.Data.model_point_table().columns
    assert model.Data.charge_table_items() == {}
    assert set(MOVED_COST_ITEMS["kapitallebensversicherung"]) <= set(
        model.Data.param_layers()["tariff_type"])


@pytest.mark.parametrize("product", sorted(MOVED_COST_ITEMS))
def test_a_moved_cost_item_stands_in_the_tariff_type_layer(product, product_models):
    layers = product_models(product).Data.param_layers()
    for item, value in MOVED_COST_ITEMS[product].items():
        moved = layers["tariff_type"][item]
        assert moved == value and type(moved) is type(value), (product, item)
        assert all(item not in layers[layer] for layer in layers if layer != "tariff_type")


@pytest.mark.parametrize("product", sorted(MODELS))
def test_no_cost_item_stands_in_a_cost_table_and_a_layer(product, product_models):
    data = product_models(product).Data
    items = {item for layer in data.param_layers().values() for item in layer}
    assert not items & set(data.charge_table_items())
    assert bool(data.charge_table_items()) == (product in COST_TABLE_PRODUCTS)


def test_a_prem_freq_outside_the_table_raises(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "prem_freq"] = "weekly"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="FreqProbe")
    try:
        message = "invalid prem_freq weekly"
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].prem_freq()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


def test_expense_infl_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "klassische_rentenversicherung")
    table = folder / MODELS["klassische_rentenversicherung"] / "CoreData" / "param_core.csv"
    drop_layer_rows(table, "expense_infl")
    copy = mx.read_model(folder / MODELS["klassische_rentenversicherung"], name="InflProbe")
    try:
        assert copy.Projection.expense_infl._is_derived()
        point_id = copy.Data.model_point_table().index[0]
        with pytest.raises(Exception, match="expense_infl") as raised:
            copy.Projection[point_id].expense_infl()
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_an_issue_year_outside_every_band_raises(tmp_path):
    folder = product_copy(tmp_path, "sofortrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "issue_year"] = 1900
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["sofortrente"], name="HrzProbe")
    try:
        assert copy.Projection.hoechstrechnungszins._is_derived()
        message = "no Hoechstrechnungszins band covers issue_year"
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].hoechstrechnungszins()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


def test_a_product_without_a_table_never_builds_its_dict(product_models):
    model = product_models("risikolebensversicherung")
    assert "surplus_file" not in model.Data.refs
    model.Projection[model.Data.model_point_table().index[0]].result_cf()
    assert len(model.Data.model_point_table_dict) == 1
    assert len(model.Data.surplus_table_dict) == 0


# The products' own dict cells, beside the core's: product -> {reader: file Reference}; the
# bounds cell of a table a lookup clamps to: product -> {bounds cell: (reader, group level or
# None, bounded level, "range" for (first, last) or "last" for the last key alone)}; and the
# by-row cells: product -> {rows cell: reader}.
PRODUCT_DICT_READERS = {
    "klassische_rentenversicherung": {"decl_rate_table": "decl_rate_file"},
    "kapitallebensversicherung": {
        "surplus_rate_table": "surplus_rate_file",
        "deckrv_table": "deckrv_file",
    },
    "basisrente": {"behaviour_table": "behaviour_file", "option_table": "option_file"},
    "fondsgebundene_rentenversicherung": {"fund_scenario_table": "fund_scenario_file"},
    "indexpolice": {
        "index_return_table": "index_return_file",
        "index_param_table": "index_param_file",
        "surplus_rate_table": "surplus_rate_file",
        "election_table": "election_file",
    },
    "sofortrente": {
        "surplus_scale_table": "surplus_scale_file",
    },
    "berufsunfaehigkeit": {
        "inception_table": "inception_file",
        "claim_duration_table": "claim_duration_file",
        "occupation_table": "occupation_file",
    },
    "riester_rente": {
        "zulage_schedule": "zulage_file",
        "income_schedule": "income_file",
    },
    "risikolebensversicherung": {
        "benefit_schedule": "benefit_schedule_file",
        "nvg_schedule": "nvg_schedule_file",
    },
}
PRODUCT_BOUNDS = {
    "klassische_rentenversicherung": {
        "decl_rate_years": ("decl_rate_table", "scenario_id", "calendar_year", "range")},
    "kapitallebensversicherung": {
        "surplus_rate_years": ("surplus_rate_table", "scenario_id", "policy_year", "range")},
    "basisrente": {
        "behaviour_table_durs": ("behaviour_table", "beh_table_id", "dur", "last"),
        "surplus_table_years": ("surplus_table", "scenario_id", "t", "last"),
    },
    "berufsunfaehigkeit": {
        "inception_table_ages": ("inception_table", None, "age", "range"),
    },
}
PRODUCT_ROWS = {"fondsgebundene_rentenversicherung": {"charge_table_rows": "charge_table"}}


def _expected_bound(values, shape):
    """The bound of an index level's values: ``(first, last)`` or the last alone, as ints."""
    if shape == "range":
        return (int(values.min()), int(values.max()))
    return int(values.max())


@pytest.mark.parametrize("product", sorted(PRODUCT_DICT_READERS))
def test_product_dict_cells_equal_their_readers(product, product_models):
    data = product_models(product).Data
    for reader, ref in PRODUCT_DICT_READERS[product].items():
        assert ref in data.refs, reader
        assert data.cells[reader + "_dict"]._is_defined(), reader
        df = data.cells[reader]()
        table = data.cells[reader + "_dict"]()
        assert list(table) == list(df.columns), reader
        for column, values in table.items():
            assert list(values) == list(df.index), (reader, column)
            for key in df.index:
                assert same_value(values[key], df.at[key, column]), (reader, key, column)
    for cell, (reader, group, level, shape) in PRODUCT_BOUNDS.get(product, {}).items():
        assert data.cells[cell]._is_defined(), cell
        df = data.cells[reader]()
        bounds = data.cells[cell]()
        if group is None:
            expected = _expected_bound(df.index.get_level_values(level), shape)
            assert bounds == expected, cell
            assert all(type(b) is int for b in (bounds if shape == "range" else (bounds,))), cell
            continue
        groups = df.index.get_level_values(group).unique()
        assert sorted(bounds) == sorted(groups), cell
        for key in groups:
            values = df.loc[key].index
            assert values.name == level
            assert bounds[key] == _expected_bound(values, shape), (cell, key)
            assert all(type(b) is int for b in (
                bounds[key] if shape == "range" else (bounds[key],))), (cell, key)
    for cell, reader in PRODUCT_ROWS.get(product, {}).items():
        assert data.cells[cell]._is_defined(), cell
        df = data.cells[reader]()
        rows = data.cells[cell]()
        assert list(rows) == list(df.index), cell
        for key in df.index:
            assert list(rows[key]) == list(df.columns), (cell, key)
            for column in df.columns:
                assert same_value(rows[key][column], df.at[key, column]), (cell, key, column)


# product -> (the third exit cell the residual sums, a new point, an in-force point).
DECREMENT_CLOSURE = {
    "klassische_rentenversicherung": ("pols_commutation", 1, 6),
    "kapitallebensversicherung": ("pols_maturity", 1, 10),
}


@pytest.mark.parametrize("product", sorted(DECREMENT_CLOSURE))
def test_decrement_closure_residual_equals_the_sum_over_the_exit_cells(product, product_models):
    third, new, in_force = DECREMENT_CLOSURE[product]
    projection = product_models(product).Projection
    assert projection.cells["pols_exits_cum"]._is_defined()
    for point_id in (new, in_force):
        item = projection[point_id]
        third_exit = item.cells[third]
        start = item.t_start()
        assert (start > 0) == (point_id == in_force), point_id
        assert item.pols_exits_cum(start - 1) == 0
        index = list(item.result_cf().index)
        assert index[0] == start and index[-1] == item.proj_len() - 1
        # The running total equals the old direct sum up to floating-point noise.
        noise = 1e-12 * max(item.pols_if_init(), 1.0)
        for t in index:
            exits = sum(item.pols_death(s) + item.pols_lapse(s) + third_exit(s)
                        for s in range(start, t + 1))
            assert item.pols_exits_cum(t) == pytest.approx(exits, rel=0, abs=noise), (point_id, t)
            if product == "kapitallebensversicherung":
                carried = item.pols_if(t + 1) if t < item.proj_len() - 1 else 0.0
                old = exits + carried - item.pols_if_init()
            else:
                old = exits + item.pols_if(t + 1) - item.pols_if_init()
            assert item.check_decrement_closure_resid(t) == pytest.approx(
                old, rel=0, abs=noise), (point_id, t)
        assert item.check_decrement_closure()


def test_rv_decl_rate_holds_the_scenario_range(product_models):
    model = product_models("klassische_rentenversicherung")
    table = model.Data.decl_rate_table()
    item = model.Projection[1]
    scen = item.scenario_id()
    years = table.loc[scen].index
    first, last = int(years.min()), int(years.max())
    assert (first, last) == (2005, 2060)
    k_late = last - item.issue_year() + 5
    assert item.calendar_year_y(k_late) > last
    assert item.decl_rate(k_late) == float(table.at[(scen, last), "decl_rate"])
    k_early = first - item.issue_year() - 5
    assert item.calendar_year_y(k_early) < first
    assert item.decl_rate(k_early) == float(table.at[(scen, first), "decl_rate"])


def test_klv_surplus_rates_and_stornoabzug_hold_their_last_policy_year(product_models):
    model = product_models("kapitallebensversicherung")
    surplus = model.Data.surplus_rate_table()
    lapse = model.Data.lapse_table()
    item = model.Projection[1]
    scen = item.scenario_id()
    last = int(surplus.loc[scen].index.max())
    k = last + 5
    assert item.policy_year_y(k) > last
    for cell in ("decl_rate", "term_rate", "ans_rate"):
        assert item.cells[cell](k) == float(surplus.at[(scen, last), cell]), cell
    last_lapse = int(lapse.index.max())
    k = last_lapse + 5
    assert item.policy_year_y(k) > last_lapse
    assert item.stornoabzug_rate(k) == float(lapse.at[last_lapse, "stornoabzug_rate"])


def test_klv_echt_instalments_carry_no_loading(product_models):
    model = product_models("kapitallebensversicherung")
    loading = model.Data.prem_freq_table()
    unecht, echt = model.Projection[4], model.Projection[5]
    assert (unecht.prem_freq(), echt.prem_freq()) == ("monthly", "monthly")
    assert (unecht.unterjaehrig_form(), echt.unterjaehrig_form()) == ("unecht", "echt")
    assert unecht.prem_freq_load() == float(loading.at["monthly", "prem_freq_load"]) == 1.05
    assert echt.prem_freq_load() == 1.0


@pytest.mark.parametrize("issue_year", [1950, 2090])
def test_klv_deckrv_ceilings_clamp_the_issue_year(tmp_path, issue_year):
    product = "kapitallebensversicherung"
    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "issue_year"] = issue_year
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS[product], name=f"DeckRVProbe{issue_year}")
    try:
        deckrv = copy.Data.deckrv_table()
        assert issue_year not in deckrv.index
        edge = deckrv.index.min() if issue_year < deckrv.index.min() else deckrv.index.max()
        item = copy.Projection[point_id]
        assert item.issue_year() == issue_year
        assert item.hoechstrechnungszins() == float(deckrv.at[edge, "hoechstrechnungszins"])
        assert item.zillmer_max() == float(deckrv.at[edge, "hoechstzillmersatz"])
    finally:
        copy.close()


@pytest.mark.parametrize("product, cell", [
    ("klassische_rentenversicherung", "decl_rate"),
    ("kapitallebensversicherung", "decl_rate"),
    ("kapitallebensversicherung", "term_rate"),
    ("kapitallebensversicherung", "ans_rate"),
    ("basisrente", "decl_rate"),
    ("basisrente", "ann_bonus_rate"),
])
def test_an_unknown_scenario_raises_key_error(tmp_path, product, cell):
    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "scenario_id"] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS[product], name="ScenProbe")
    try:
        with pytest.raises(Exception, match="unbekannt") as raised:
            copy.Projection[point_id].cells[cell](0)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_basis_behaviour_holds_its_first_and_last_policy_year(product_models):
    model = product_models("basisrente")
    table = model.Data.behaviour_table()
    item = model.Projection[1]
    key = item.model_point()["beh_table_id"]
    last = int(table.loc[key].index.max())
    k_late = last + 5
    assert item.policy_year_y(k_late) > last
    assert item.zuz_take_up(k_late) == float(table.at[(key, last), "zuz_take_up"])
    k_early = -item.duration_init() - 5
    assert item.policy_year_y(k_early) < 1
    assert item.zuz_take_up(k_early) == float(table.at[(key, 1), "zuz_take_up"])


def test_basis_bf_rate_holds_the_last_row_of_a_short_table(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    path = folder / "behaviour_table.csv"
    table = pd.read_csv(path, index_col=["beh_table_id", "dur"])
    table = table[table.index.get_level_values("dur") <= 7]
    table.to_csv(path)
    copy = mx.read_model(folder / MODELS["basisrente"], name="BfProbe")
    try:
        item = copy.Projection[1]
        key = item.model_point()["beh_table_id"]
        assert copy.Data.behaviour_table_durs()[key] == 7
        t = 12 * 9
        assert item.policy_year(t) == 10 and t < min(item.t_conv(), item.proj_len())
        assert item.bf_rate(t) == float(table.at[(key, 7), "bf_rate"])
        assert item.zuz_take_up(9) == float(table.at[(key, 7), "zuz_take_up"])
    finally:
        copy.close()


def test_basis_unknown_behaviour_table_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "beh_table_id"] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["basisrente"], name="BehProbe")
    try:
        for cell in ("zuz_take_up", "bf_rate"):
            with pytest.raises(Exception, match="unbekannt") as raised:
                copy.Projection[point_id].cells[cell](0)
            assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_basis_surplus_holds_its_first_and_last_year(product_models):
    model = product_models("basisrente")
    table = model.Data.surplus_table()
    item = model.Projection[1]
    scen = item.scenario_id()
    last = int(table.loc[scen].index.max())
    for cell in ("decl_rate", "ann_bonus_rate"):
        assert item.cells[cell](last + 5) == float(table.at[(scen, last), cell]), cell
        assert item.cells[cell](-3) == float(table.at[(scen, 0), cell]), cell


def test_basis_unknown_surplus_scenario_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "scenario_id"] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["basisrente"], name="SurplusProbe")
    try:
        for cell in ("decl_rate", "ann_bonus_rate"):
            with pytest.raises(Exception, match="unbekannt") as raised:
                copy.Projection[point_id].cells[cell](0)
            assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_index_lapse_beyond_the_table_raises_key_error():
    folder = PRODUCTS_DIR / "indexpolice" / MODELS["indexpolice"]
    copy = mx.read_model(folder, name="IndexLapseProbe")
    try:
        last = int(copy.Data.lapse_table().index.max())
        item = copy.Projection[copy.Data.model_point_table().index[0]]
        t = 12 * (last + 1)
        assert item.duration(t) == last + 1
        assert item.lapse_rate_base(12 * last) == float(
            copy.Data.lapse_table().at[last, "lapse_rate"])
        with pytest.raises(Exception, match=f"KeyError: {last + 1}") as raised:
            item.lapse_rate_base(t)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_riester_after_conversion_reads_no_schedule(product_models):
    model = product_models("riester_rente")
    item = model.Projection[1]
    k = item.k_conv()
    assert k > 0
    for k_after in (k, k + 100):
        assert not item.is_accum_y(k_after)
        assert not item.is_accum(12 * k_after)
        assert item.transfer_rate(12 * k_after) == 0.0, k_after
        assert item.income_ref(k_after) == 0.0, k_after
        assert item.zulage_entitlement_pp(k_after) == 0.0, k_after
        assert item.decl_rate(k_after) == 0.0, k_after


def test_riester_income_ref_at_zero_is_the_initial_income(product_models):
    model = product_models("riester_rente")
    table = model.Data.income_schedule()
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        if not item.is_accum_y(0):
            continue
        assert item.income_ref(0) == item.income_init(), point_id
        if item.is_accum_y(1):
            assert item.income_ref(1) == float(
                table.at[(item.income_id(), 0), "income"]), point_id


@pytest.mark.parametrize("product, column, cell, arg", [
    ("riester_rente", "zulage_id", "zulage_entitlement_pp", 0),
    ("riester_rente", "income_id", "income_ref", 1),
    ("risikolebensversicherung", "benefit_schedule_id", "benefit_factor", 0),
    ("risikolebensversicherung", "nvg_schedule_id", "sum_uplift_y", 0),
])
def test_an_unknown_schedule_id_raises_key_error(tmp_path, product, column, cell, arg):
    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, column] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS[product], name="ScheduleProbe")
    try:
        with pytest.raises(Exception, match="unbekannt") as raised:
            copy.Projection[point_id].cells[cell](arg)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_rlv_schedules_beyond_their_last_year_raise_key_error():
    product = "risikolebensversicherung"
    copy = mx.read_model(PRODUCTS_DIR / product / MODELS[product], name="RlvScheduleProbe")
    try:
        item = copy.Projection[copy.Data.model_point_table().index[0]]
        benefit = copy.Data.benefit_schedule()
        sched = item.benefit_schedule_id()
        last = int(benefit.loc[sched].index.max())
        t = 12 * last
        assert item.policy_year(t) == last + 1
        assert item.benefit_factor(t - 12) == float(
            benefit.at[(sched, last), "benefit_factor"])
        with pytest.raises(Exception, match=re.escape(f"KeyError: ('{sched}', {last + 1})")) \
                as raised:
            item.benefit_factor(t)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
        nvg = copy.Data.nvg_schedule()
        nvg_id = item.nvg_schedule_id()
        last = int(nvg.loc[nvg_id].index.max())
        assert item.sum_uplift_y(last - 1) == float(nvg.at[(nvg_id, last), "sum_uplift"])
        with pytest.raises(Exception, match=re.escape(f"KeyError: ('{nvg_id}', {last + 1})")) \
                as raised:
            item.sum_uplift_y(last)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()
