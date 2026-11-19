"""The premium and annuity payment frequencies and the premium form (``docs/core.md``,
"Contract data and charges" and "Formula literals").

- The nine products with a regular premium read their premium
  frequencies from one ``prem_freq_table.csv``, keyed ``annual`` to ``monthly``, with
  ``instalments`` an ``int`` a year, and every model point's ``prem_freq`` is a key; Basis'
  single premium reads no loading, Pflege's is the premium form ``single``, not a frequency.
  ``prem_form`` is ``regular`` or ``single`` in the seven products that have it, and an
  unknown form raises. Sofort's annuity frequencies are the keys of its ``ann_freq_table.csv``. A
  frequency outside its table raises (FRV, Pflege, Sofort), and a row added to a scratch copy
  admits it.
- A single premium is annual and carries no frequency loading; RV's sits in the one premium
  column, BU's stated premium is the level premium before the *Risikozuschlag*, ``prem_due``
  alone zeroes the premium after its term, and Basis' *Zuzahlung* is not bounded by the
  premium term.
"""
from __future__ import annotations

import modelx as mx
import pandas as pd
import pytest

from helpers import MODELS, PRODUCTS_DIR, product_copy, raised_value_error


def test_basis_single_premium_reads_no_loading(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "prem_freq_table.csv"
    table.write_text(table.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
    copy = mx.read_model(folder / MODELS["basisrente"], name="LoadProbe")
    try:
        points = copy.Data.model_point_table()
        single = points.index[points["prem_form"] == "single"][0]
        regular = points.index[points["prem_form"] == "regular"][0]
        assert copy.Projection[single].prem_freq_load() == 1.0
        message = "invalid prem_freq " + str(points.at[regular, "prem_freq"])
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[regular].prem_freq_load()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


# The premium payment frequencies, one name and one table in every product with a regular
# premium: key -> instalments a year.
PREM_FREQ_INSTALMENTS = {"annual": 1, "half_yearly": 2, "quarterly": 4, "monthly": 12}
PREM_FREQ_PRODUCTS = sorted(["basisrente", "berufsunfaehigkeit",
                             "fondsgebundene_rentenversicherung", "indexpolice",
                             "kapitallebensversicherung", "klassische_rentenversicherung",
                             "pflegerentenversicherung", "riester_rente",
                             "risikolebensversicherung"])


def test_the_products_with_a_premium_frequency_table_are_listed(product_models):
    having = [product for product in sorted(MODELS)
              if "prem_freq_file" in product_models(product).Data.refs]
    assert having == PREM_FREQ_PRODUCTS


@pytest.mark.parametrize("product", PREM_FREQ_PRODUCTS)
def test_premium_frequencies_are_one_table_with_instalments(product, product_models):
    """``prem_freq_table.csv`` keyed by ``prem_freq``, its ``instalments`` an ``int`` a year,
    and every model point's ``prem_freq`` one of its keys."""
    model = product_models(product)
    data = model.Data
    assert data.prem_freq_file == "prem_freq_table.csv"
    table = data.prem_freq_table()
    assert table.index.name == "prem_freq"
    assert set(table.index) <= set(PREM_FREQ_INSTALMENTS)
    assert table.columns[0] == "instalments" and table.columns[-1] == "provenance"
    assert set(table.columns) <= {"instalments", "prem_freq_load", "provenance"}
    instalments = data.prem_freq_table_dict()["instalments"]
    assert all(type(n) is int for n in instalments.values())
    assert instalments == {key: PREM_FREQ_INSTALMENTS[key] for key in table.index}
    points = data.model_point_table()
    assert not {"prem_mode", "prem_mode_months"} & set(points.columns)
    assert set(points["prem_freq"]) <= set(table.index)
    for point_id in points.index:
        item = model.Projection[point_id]
        assert type(item.instalments()) is int
        assert item.prem_cycle() == 12 // PREM_FREQ_INSTALMENTS[points.at[point_id, "prem_freq"]]


# The products with a single and a regular premium form, one model-point column prem_form.
PREM_FORM_PRODUCTS = sorted(["basisrente", "fondsgebundene_rentenversicherung", "indexpolice",
                             "klassische_rentenversicherung", "pflegerentenversicherung",
                             "risikolebensversicherung", "sofortrente"])


def test_the_premium_form_is_one_column_with_two_values(product_models):
    """``prem_form`` is ``regular`` or ``single`` wherever a product has the column, the core's
    ``prem_form()`` reads it, and no ``premium_form`` of that meaning is left (BU's
    ``premium_form``, *Dynamik* or level, is another quantity).  Sofort writes single
    premiums only, ``single`` on every point."""
    having = []
    for product in sorted(MODELS):
        model = product_models(product)
        points = model.Data.model_point_table()
        if "prem_form" not in points.columns:
            continue
        having.append(product)
        assert set(points["prem_form"]) <= {"regular", "single"}, product
        for point_id in points.index:
            assert model.Projection[point_id].prem_form() == points.at[point_id, "prem_form"]
        assert "premium_form" not in points.columns, product
    assert having == PREM_FORM_PRODUCTS
    sofort = product_models("sofortrente").Data.model_point_table()
    assert set(sofort["prem_form"]) == {"single"}
    bu = product_models("berufsunfaehigkeit").Data.model_point_table()
    assert set(bu["premium_form"]) == {"dynamik", "level"}


def test_an_unknown_premium_form_raises(tmp_path):
    folder = product_copy(tmp_path, "indexpolice")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "prem_form"] = "level"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["indexpolice"], name="FormProbe")
    try:
        message = "invalid prem_form"
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].prem_form()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


# The payment frequencies a product allows, a table of its own: product -> (keys cell, keys).
FREQUENCY_KEYS = {
    "sofortrente": ("ann_freq_table_keys", frozenset({1, 2, 4, 12})),
}

# A frequency the shipped table lacks: product -> (table file, model-point column, value,
# row that admits it, cell that checks it, its error message, the cell's value once admitted).
FREQUENCY_PROBES = {
    "fondsgebundene_rentenversicherung": (
        "prem_freq_table.csv", "prem_freq", "bimonthly", 'bimonthly,6,"[std] test fixture"',
        "prem_freq", "invalid prem_freq bimonthly", "bimonthly"),
    "pflegerentenversicherung": (
        "prem_freq_table.csv", "prem_freq", "bimonthly", 'bimonthly,6,"[std] test fixture"',
        "prem_freq", "invalid prem_freq bimonthly", "bimonthly"),
    "sofortrente": (
        "ann_freq_table.csv", "ann_freq", 3, '3,"[std] test fixture"',
        "ann_freq", "invalid ann_freq", 3),
}


def test_a_single_premium_is_annual_and_carries_no_frequency_loading(product_models):
    """Every single-premium point carries ``prem_freq = annual`` and ``prem_freq_load`` 1.0,
    the core's rule for every product; Basis no longer overrides ``prem_freq_load``.  Sofort
    has no premium frequency: its one premium is paid at ``t = 0``."""
    checked = 0
    for product in sorted(MODELS):
        model = product_models(product)
        points = model.Data.model_point_table()
        if "prem_form" not in points.columns:
            assert model.Projection[int(points.index[0])].prem_form() == "regular"
            continue
        if "prem_freq" not in points.columns:
            assert product == "sofortrente"
            continue
        for point_id in points.index[points["prem_form"] == "single"]:
            assert points.at[point_id, "prem_freq"] == "annual", (product, point_id)
            assert model.Projection[int(point_id)].prem_freq_load() == 1.0, (product, point_id)
            checked += 1
    assert checked == 6
    path = PRODUCTS_DIR / "basisrente" / MODELS["basisrente"] / "Projection" / "__init__.py"
    assert "def prem_freq_load" not in path.read_text(encoding="utf-8")


def test_pflege_single_premium_is_a_premium_form_not_a_frequency(product_models):
    """Pflege's *Einmalbeitrag* is ``prem_form = single``, paid at ``t = 0`` alone, and its
    ``prem_freq`` (shipped as ``annual``) is a key of the table; a ``regular`` premium falls
    due every ``prem_cycle()`` months, over all four frequencies."""
    model = product_models("pflegerentenversicherung")
    assert "single" not in model.Data.prem_freq_table().index
    points = model.Data.model_point_table()
    forms, freqs = set(), set()
    for point_id in points.index:
        item = model.Projection[point_id]
        forms.add(item.prem_form())
        if item.prem_form() == "single":
            assert points.at[point_id, "prem_freq"] == "annual"
            assert [t for t in range(24) if item.prem_due(t)] == [0]
        else:
            freqs.add(item.prem_freq())
            assert item.prem_cycle() == 12 // PREM_FREQ_INSTALMENTS[item.prem_freq()]
    assert forms == {"regular", "single"}
    assert freqs == set(PREM_FREQ_INSTALMENTS)


def test_rv_single_premium_sits_in_the_one_premium_column(product_models):
    """RV's *Einmalbeitrag* is in ``prem_gross_level_pp`` as every product's: point 2 pays its
    50,000.00 once, in the first year, and no column ``premium_single_pp`` is left."""
    model = product_models("klassische_rentenversicherung")
    points = model.Data.model_point_table()
    assert "premium_single_pp" not in points.columns
    assert points.at[2, "prem_form"] == "single"
    assert points.at[2, "prem_gross_level_pp"] == 50000.0
    item = model.Projection[2]
    assert item.prem_pp_sched(0) == 50000.0
    assert [item.prem_pp_sched(k) for k in range(1, 15)] == [0.0] * 14


def test_bu_stated_premium_is_the_level_premium_before_the_risikozuschlag(product_models):
    """BU's column ``prem_gross_level_std_pp`` is the level annual premium before the
    *Risikozuschlag*: point 13 states it and ``prem_gross_level_pp()`` is ``rating_factor()``
    times it; every other point carries 0 and derives its premium by equivalence."""
    model = product_models("berufsunfaehigkeit")
    points = model.Data.model_point_table()
    assert "gross_prem_ann" not in points.columns
    stated = [int(p) for p in points.index if points.at[p, "prem_gross_level_std_pp"] > 0.0]
    assert stated == [13]
    for point_id in points.index:
        item = model.Projection[int(point_id)]
        column = float(points.at[point_id, "prem_gross_level_std_pp"])
        if column > 0.0:
            assert item.prem_gross_level_pp() == item.rating_factor() * column
        else:
            assert item.prem_gross_level_pp() > 0.0, point_id


def test_prem_due_alone_zeroes_the_premium_after_its_term(product_models):
    """After the paying term or from *Rentenbeginn* the contractual annual premium is still
    its amount, ``prem_due`` is false, and every amount paid or charged is 0.0."""
    index = product_models("indexpolice").Projection[13]       # pays 12 of 22 policy years
    k = index.prem_term_y()
    assert k < index.proj_len_y()
    assert index.prem_gross_pp(k) == 3000.0 and not index.prem_due(12 * k)
    for amount in (index.prem_pp(k), index.prem_inst_pp(12 * k), index.prem_charge_acq_pp(k),
                   index.prem_charge_adm_pp(k), index.prem_to_av_pp(k)):
        assert amount == 0.0
    assert index.prem_gross_cum_pp(k + 1) == index.prem_gross_cum_pp(k)

    basis = product_models("basisrente").Projection[1]         # premiums stop at Rentenbeginn
    k = basis.k_conv()
    assert basis.prem_gross_pp(k) > 0.0 and not basis.prem_due(12 * k)
    assert basis.prem_due(12 * (k - 1)) and basis.prem_pp(k - 1) > 0.0
    for amount in (basis.prem_pp(k), basis.zuz_pp(k), basis.prem_inst_pp(12 * k)):
        assert amount == 0.0
    single = product_models("basisrente").Projection[5]        # a single premium, paid once
    assert single.prem_form() == "single" and single.prem_due(0) and not single.prem_due(12)
    assert single.prem_gross_pp(1) == 60000.0 and single.prem_pp(0) == 60000.0
    assert single.prem_pp(1) == 0.0 and single.prem_inst_pp(12) == 0.0

    rlv = product_models("risikolebensversicherung").Projection[6]   # abgekürzte Zahlungsdauer
    t = 12 * rlv.prem_term()
    assert t < rlv.proj_len() and rlv.prem_gross_level_pp() > 0.0
    assert rlv.prem_due(t - 12) and not rlv.prem_due(t)
    for amount in (rlv.prem_pp(t), rlv.prem_rebate_pp(t), rlv.prem_paid_pp(t),
                   rlv.prem_charged_inst_pp(t), rlv.prem_rebate_inst_pp(t), rlv.prem_inst_pp(t)):
        assert amount == 0.0

    rv = product_models("klassische_rentenversicherung").Projection[4]   # pays 20 of 22 years
    k = rv.prem_term_y()
    assert float(rv.model_point()["prem_gross_level_pp"]) > 0.0 and not rv.prem_due(12 * k)
    assert rv.prem_pp_sched(k - 1) > 0.0
    for amount in (rv.prem_pp_sched(k), rv.prem_pp(k), rv.prem_inst_pp(12 * k)):
        assert amount == 0.0


def test_basis_zuzahlung_is_not_bounded_by_the_premium_term(tmp_path):
    """A single-premium point pays a *Zuzahlung* after its one premium: ``zuz_pp`` ends with
    ``zuzahlung_end_dur`` and *Rentenbeginn*, not with ``prem_due``, and ``prem_inst_pp``
    collects it in the first month of the projection year."""
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    assert points.at[5, "prem_form"] == "single" and points.at[5, "duration_init"] == 0
    points.loc[5, "zuzahlung_pp"] = 2000.0
    points.loc[5, "zuzahlung_end_dur"] = 3
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["basisrente"], name="ZuzahlungProbe")
    try:
        item = copy.Projection[5]
        assert item.prem_due(0) and not item.prem_due(12)
        assert item.zuz_pp(1) > 0.0 and item.prem_pp(1) == 0.0
        assert item.prem_inst_pp(12) == item.zuz_pp(1)
        assert item.prem_inst_pp(13) == 0.0
        assert item.premiums(12) > 0.0
        assert item.zuz_pp(3) == 0.0 and item.prem_inst_pp(36) == 0.0
        assert item.zuz_pp(item.k_conv()) == 0.0
        assert item.prem_inst_pp(12 * item.k_conv()) == 0.0
    finally:
        copy.close()


@pytest.mark.parametrize("product", sorted(FREQUENCY_KEYS))
def test_annuity_frequencies_are_the_keys_of_their_table(product, product_models):
    data = product_models(product).Data
    cell, keys = FREQUENCY_KEYS[product]
    assert data.cells[cell]() == keys
    assert all(type(key) is int for key in data.cells[cell]())


@pytest.mark.parametrize("product", sorted(FREQUENCY_PROBES))
def test_a_frequency_outside_the_table_raises_and_a_row_admits_it(product, tmp_path):
    table, column, value, row, cell, message, admitted = FREQUENCY_PROBES[product]
    folder = product_copy(tmp_path, product)
    points = pd.read_csv(folder / "model_point_table.csv", dtype=str, keep_default_na=False)
    points.loc[0, column] = str(value)
    points.to_csv(folder / "model_point_table.csv", index=False)
    point_id = int(points.loc[0, "point_id"])
    copy = mx.read_model(folder / MODELS[product], name="FreqProbe")
    try:
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].cells[cell]()
        assert raised_value_error(raised, message)
    finally:
        copy.close()
    path = folder / table
    path.write_text(path.read_text(encoding="utf-8") + row + "\n", encoding="utf-8")
    copy = mx.read_model(folder / MODELS[product], name="FreqProbeAdmitted")
    try:
        assert copy.Projection[point_id].cells[cell]() == admitted
    finally:
        copy.close()
