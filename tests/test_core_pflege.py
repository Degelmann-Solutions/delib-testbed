"""Pflege on the common core (``docs/core.md``): its merged tariff-type file, its dict cells
and its care-grade rates.

- Pflege's tariff-type file holds upstream's two merged tables, ``basis_table.csv`` and
  ``expense_table.csv``, read from git, in their order and with their values but the renamed,
  aligned and moved ones.
- Pflege's own dict cells equal their readers; its care-grade rates are keyed by attained
  age and grade, not by month, and keep their limiting-age, recovery-damping and grade-5
  values; a missing ``recov_load_first`` row raises; its entrants and graduations are the ledger's
  own and equal the formulas they had beside it; its month-keyed rates depend on the month only
  through the attained age, as the age-keyed transitions assume.
- Its number of care grades and the states of ``status_init`` are read from its care table,
  and its surrender cap is the last policy year of its surrender table, so a scratch copy
  with a further row reads it.
"""
from __future__ import annotations

import hashlib
import io
import math
import re
import subprocess

import modelx as mx
import pandas as pd
import pytest

from helpers import (CORE_ITEMS, MODELS, PRODUCTS_DIR, ROOT, drop_layer_rows, product_copy,
                     read_layer, same_value)


# The last commit before the Pflege merge; its basis_table.csv and expense_table.csv are
# upstream's bytes (checked against the hashes in UPSTREAM.md).
PRE_MERGE_REVISION = "34938cec06fa412fe0af0c3a484f7e1551c87c89"


def upstream_table(product: str, name: str, **read_csv) -> pd.DataFrame:
    """A file phase 3 removed, read from git at ``PRE_MERGE_REVISION``, hash-checked."""
    data = subprocess.run(
        ["git", "show", f"{PRE_MERGE_REVISION}:products/{product}/{name}"],
        cwd=ROOT, check=True, capture_output=True).stdout
    upstream = (PRODUCTS_DIR / product / "UPSTREAM.md").read_text(encoding="utf-8")
    assert f"| `{name}` | `{hashlib.sha256(data).hexdigest()}` |" in upstream, name
    return pd.read_csv(io.BytesIO(data), **read_csv)


# Pflege's items renamed after the merge (docs/core.md, "Parameter names"): upstream name ->
# current name. ``acq_permille`` 25 (per mille) is the fraction ``load_acq_bsum_once`` 0.025.
PFLEGE_RENAMED = {
    "acq_permille": "load_acq_bsum_once",
    "inc_margin": "inc_load_first",
    "det_margin": "det_load_first",
    "rec_margin": "recov_load_first",
    "care_mort_margin": "mort_care_load_first",
    "act_mort_margin": "mort_actv_load_first",
    "admin_prem_pct": "load_admin_prem_inst",
    "admin_mth_pp": "load_admin_pp_mth",
    "claim_expense_pp": "load_claim_pp_inst",
    "rec_age_ref": "recov_age_ref",
    "rec_age_decay": "recov_age_decay",
    "roll_fwd_tol": "check_tol",
}

# Pflege's values that entry 12 of epic-parameter-files aligned (the acceptance of 2026-11-09):
# current item -> aligned value, against upstream's.
PFLEGE_ALIGNED = {"expense_infl": 0.02, "check_tol": 1e-08}

# Each unit of upstream's ``expense_table.csv`` (the acquisition rate's as a fraction) -> the
# words that end the row's provenance in ``param_tariff_type.csv``, which has no unit column.
PFLEGE_UNIT_WORDS = {
    "fraction_of_beitragssumme": "; a fraction of the Beitragssumme",
    "fraction_of_premium": "; a fraction of the premium",
    "eur_per_policy_per_month": "; in euros per policy a month",
    "eur_per_annuity_payment": "; in euros per annuity payment",
}


def test_pflege_tariff_type_file_holds_the_two_merged_tables(product_models):
    product = "pflegerentenversicherung"
    model = product_models(product)
    merged = read_layer(PRODUCTS_DIR / product / "param_tariff_type.csv").set_index("item")
    basis = upstream_table(product, "basis_table.csv", index_col="param")
    expense = upstream_table(product, "expense_table.csv", index_col="item")
    basis = basis.rename(index=PFLEGE_RENAMED)
    expense = expense.rename(index=PFLEGE_RENAMED)
    assert expense.at["load_acq_bsum_once", "unit"] == "permille_of_beitragssumme"
    expense.at["load_acq_bsum_once", "value"] /= 1000.0
    expense.at["load_acq_bsum_once", "unit"] = "fraction_of_beitragssumme"
    for item, value in PFLEGE_ALIGNED.items():
        table = basis if item in basis.index else expense
        table.at[item, "value"] = value
    # Items of the core file since entry 12 of epic-parameter-files leave the tariff-type file.
    basis = basis.drop([item for item in CORE_ITEMS if item in basis.index])
    expense = expense.drop([item for item in CORE_ITEMS if item in expense.index])
    # The Rechnungszins moved from the table to the model point (a contract attribute).
    moved = ["rechnungszins"]
    points = model.Data.model_point_table()
    for item in moved:
        assert (points[item] == basis.at[item, "value"]).all(), item
    basis = basis.drop(moved)
    # The terminal age went with the switch to the table factory: the end age of the table
    # of ``mort_table``; the six table choices stand first in its place.
    table = merged.at["mort_table", "value"]
    assert basis.at["omega_age", "value"] == model.CoreTables.end_age(table) == 110
    basis = basis.drop(["omega_age"])
    choices = ["mort_table"] + [f"mort_pg{grade}_table" for grade in range(1, 6)]
    assert list(merged.columns) == ["value", "basis", "provenance"]
    assert list(merged.index) == choices + list(basis.index) + list(expense.index)
    merged = merged.drop(choices).astype({"value": float})
    # Values and order are upstream's but the aligned ones; basis and provenance follow the
    # acceptance of 2026-11-09, which extended each provenance with its source or reason.
    # The expense rows' units stand in words at the end of their provenance.
    for item in basis.index:
        assert merged.at[item, "value"] == basis.at[item, "value"], item
    for item in expense.index:
        assert merged.at[item, "value"] == expense.at[item, "value"], item
        words = PFLEGE_UNIT_WORDS[expense.at[item, "unit"]]
        assert merged.at[item, "provenance"].endswith(words), item


# Pflege's own dict cells, beside the core's: reader -> the file Reference of its table.
PFLEGE_DICT_READERS = {
    "benefit_scale_table": "benefit_scale_file",
    "incidence_table": "incidence_file",
    "care_table": "care_file",
    "surrender_table": "surrender_file",
}


def test_pflege_product_dict_cells_equal_their_readers(product_models):
    data = product_models("pflegerentenversicherung").Data
    for reader, ref in PFLEGE_DICT_READERS.items():
        assert ref in data.refs, reader
        assert data.cells[reader + "_dict"]._is_defined(), reader
        df = data.cells[reader]()
        table = data.cells[reader + "_dict"]()
        assert list(table) == list(df.columns), reader
        for column, values in table.items():
            assert list(values) == list(df.index), (reader, column)
            for key in df.index:
                assert same_value(values[key], df.at[key, column]), (reader, key, column)


def test_pflege_grade_count_is_read_from_the_care_table(product_models):
    """Pflege's number of care grades is the rows of ``care_table.csv``, and no formula
    holds it as ``range(1, 6)``, ``(0.0,) * 5``, ``g < 5`` or ``min(5, ...)``."""
    data = product_models("pflegerentenversicherung").Data
    table = data.care_table()
    count = data.pflegegrad_count()
    assert type(count) is int and count == len(table) == 5
    assert list(table.index) == list(range(1, count + 1))
    path = PRODUCTS_DIR / "pflegerentenversicherung" / MODELS["pflegerentenversicherung"]
    text = (path / "Projection" / "__init__.py").read_text(encoding="utf-8")
    for literal in ("range(1, 6)", "(0.0,) * 5", "g < 5", "min(5, "):
        assert literal not in text, literal
    columns = [label for label, _ in
               product_models("pflegerentenversicherung").Projection[1].result_states_columns()]
    assert columns[:count] == ["pols_pg%d" % g for g in range(1, count + 1)]
    assert "mort_rate_care_pg%d" % count in columns


def _status_init_error(item) -> str:
    """The error line of ``status_init()``'s error, which must be a ``ValueError``; modelx
    wraps it in a ``FormulaError`` whose text also holds the formula source."""
    with pytest.raises(Exception) as raised:
        item.status_init()
    if isinstance(raised.value, ValueError):
        return f"ValueError: {raised.value}"
    head = str(raised.value).split("Formula traceback:", 1)[0]
    line = [text for text in head.splitlines() if text.strip()][-1]
    assert line.startswith("ValueError: "), str(raised.value)
    return line


def test_pflege_status_init_reads_its_states_from_the_care_table(tmp_path, product_models):
    """``status_init`` accepts ``aktiv`` and ``pg1`` up to the top grade of
    ``care_table.csv``: on a four-grade copy ``pg4`` is accepted and ``pg5`` is not."""
    shipped = product_models("pflegerentenversicherung")
    for point_id, status in shipped.Data.model_point_table()["status"].items():
        assert shipped.Projection[point_id].status_init() == status
    folder = product_copy(tmp_path, "pflegerentenversicherung")
    care = folder / "care_table.csv"
    lines = care.read_text(encoding="utf-8").splitlines(keepends=True)
    assert lines[-1].startswith("5,")
    care.write_text("".join(lines[:-1]), encoding="utf-8")
    table = folder / "model_point_table.csv"
    rows = table.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[1].startswith("1,") and ",aktiv," in rows[1]
    for status in ("pg4", "pg5", "pg0", "foo"):
        rows[1] = re.sub(r",(aktiv|pg\d|foo),", f",{status},", rows[1], count=1)
        table.write_text("".join(rows), encoding="utf-8")
        copy = mx.read_model(folder / MODELS["pflegerentenversicherung"], name="StatusProbe")
        try:
            assert copy.Data.pflegegrad_count() == 4
            item = copy.Projection[1]
            if status == "pg4":
                assert item.status_init() == "pg4"
            else:
                assert _status_init_error(item) == f"ValueError: invalid status '{status}'"
        finally:
            copy.close()


def test_pflege_surrender_cap_is_read_from_the_surrender_table(tmp_path, product_models):
    """The policy-year cap of ``rkw_pp`` is the table's last row, so a 41st row is read too."""
    data = product_models("pflegerentenversicherung").Data
    table = data.surrender_table()
    last = data.surrender_table_last_year()
    assert type(last) is int and last == int(table.index.max()) == len(table) == 40
    folder = product_copy(tmp_path, "pflegerentenversicherung")
    path = folder / "surrender_table.csv"
    path.write_text(path.read_text(encoding="utf-8") + '41,0.900000,"[std] test fixture"\n',
                    encoding="utf-8")
    copy = mx.read_model(folder / MODELS["pflegerentenversicherung"], name="SurrenderProbe")
    try:
        assert copy.Data.surrender_table_last_year() == 41
        checked = 0
        for point_id in copy.Data.model_point_table().index:
            item = copy.Projection[point_id]
            for t in range(item.t_start(), item.proj_len()):
                if item.policy_year(t) < 41 or item.prem_cum_max_pp(t) <= 0.0:
                    continue
                expected = 0.9 * item.prem_cum_max_pp(t) * (1.0 - item.stornoabzug_rate())
                assert item.rkw_pp(t) == expected, (point_id, t)
                checked += 1
        assert checked
    finally:
        copy.close()


# Pflege's care-grade rates keyed by attained age (and grade), not by month: cell -> whether
# the cell takes the grade, the age, or both.
PFLEGE_AGE_KEYED = {
    "rec_rate": ("x", "g"),
    "det_force": ("x", "g"),
    "rec_force": ("x", "g"),
    "tar_mort_rate_care": ("x", "g"),
    "tar_rec_rate": ("x", "g"),
    "tar_p_pg": ("x", "g"),
    "tar_inc_rate": ("x",),
    "tar_det_rate": ("g",),
}


def test_pflege_care_grade_rates_are_keyed_by_age():
    # A model of its own, so that the cells' caches start empty whatever ran before.
    product = "pflegerentenversicherung"
    model = mx.read_model(PRODUCTS_DIR / product / MODELS[product], name="AgeKeyProbe")
    try:
        item = model.Projection[1]
        item.result_cf()
        assert item.premium_mth() == 0.0
        item.premium_mth_pp()
        ages = {item.age(t) for t in range(item.proj_len())}
        bound = {("x", "g"): len(ages) * 5, ("x",): len(ages), ("g",): 5}
        for name, params in PFLEGE_AGE_KEYED.items():
            cell = item.cells[name]
            assert tuple(cell.parameters) == params, name
            keys = list(cell.keys())
            assert 0 < len(keys) <= bound[params], (name, len(keys))
            for key in keys:
                key = key if isinstance(key, tuple) else (key,)
                if params[0] == "x":
                    assert key[0] in ages, (name, key)
                if params[-1] == "g":
                    assert 1 <= key[-1] <= 5, (name, key)
    finally:
        model.close()


def test_pflege_entries_and_graduations_are_the_ledgers_own(product_models):
    """``pols_entry`` and ``pols_grad`` read the ledger and equal the formulas they had beside it.

    On every point and every month of the frame, the last one included, whose flows the
    ledger forms at ``proj_len()``: the entrants are ``pols_act(t)`` times the ``care``
    component of ``p_act_age`` times ``inc_share(g)``; the graduations equal the entrants
    where ``karenz_months() == 0`` and are the ``z = K`` cohort carried one month through
    ``p_pg_age`` at ``age(t)`` where it is positive (point 7).
    """
    model = product_models("pflegerentenversicherung")
    seen = set()
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        k = item.karenz_months()
        seen.add(k > 0)
        for t in range(item.t_start(), item.proj_len()):
            state = item.pols_ledger(t)
            waiting = item.duration_mth(t) < item.wartezeit_months()
            care = item.p_act_age(item.age(t), waiting)[2]
            for g in range(1, 6):
                entry = state[0] * care * item.inc_share(g)
                assert item.pols_entry(t, g) == entry, (point_id, t, g)
                if k <= 0:
                    assert item.pols_grad(t, g) == item.pols_entry(t, g), (point_id, t, g)
                    continue
                grad = 0.0
                for h in range(max(1, g - 1), min(5, g + 1) + 1):
                    w = state[3][h - 1][k - 1]
                    if w == 0.0:
                        continue
                    p = item.p_pg_age(item.age(t), h)
                    grad += w * (p[0] if h == g else p[2] if g == h + 1 else p[3])
                assert item.pols_grad(t, g) == grad, (point_id, t, g)
    assert seen == {False, True}


def test_pflege_month_keyed_rates_depend_on_the_month_only_through_the_age(product_models):
    """The age-keyed transitions read the month-keyed rates at ``age_month(age(t))``.

    ``p_act_age`` and ``p_pg_age`` are keyed by attained age and read ``inc_rate``,
    ``mort_force`` and ``mort_force_care`` at the first month of the age; that is right only
    while those rates take the same value in every month of a year of age. On every point
    and every month of the frame: ``age_month`` maps back to the age, the three rates equal
    their values at it, and ``inc_force`` is 0 in the *Wartezeit* and else
    ``inc_force_age`` at the age.
    """
    model = product_models("pflegerentenversicherung")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            m = item.age_month(x)
            assert item.age(m) == x, (point_id, t)
            assert item.inc_rate(t) == item.inc_rate(m), (point_id, t)
            assert item.mort_force(t) == item.mort_force(m), (point_id, t)
            for g in range(1, 6):
                assert item.mort_force_care(t, g) == item.mort_force_care(m, g), (point_id, t, g)
            if item.duration_mth(t) < item.wartezeit_months():
                assert item.inc_force(t) == 0.0, (point_id, t)
            else:
                assert item.inc_force(t) == item.inc_force_age(x), (point_id, t)


def test_pflege_tariff_care_mortality_is_certain_at_the_limiting_age(product_models):
    item = product_models("pflegerentenversicherung").Projection[1]
    x = item.omega_age() - 1
    for g in range(1, 6):
        assert item.tar_mort_rate_care(x, g) == 1.0
        stay, death, worse, better = item.tar_p_pg(x, g)
        assert (worse, better) == (0.0, 0.0)
        assert stay + death == pytest.approx(1.0, abs=1e-15)


def test_pflege_recovery_is_damped_only_above_the_reference_age(product_models):
    model = product_models("pflegerentenversicherung")
    item = model.Projection[1]
    care = model.Data.care_table()
    ref = item.recov_age_ref()
    decay = item.recov_age_decay()
    assert (ref, decay) == (75.0, 0.1)
    for g in range(1, 6):
        base = float(care.at[g, "rec_rate"])
        assert item.rec_rate(60, g) == base
        assert item.rec_rate(75, g) == base
        assert item.rec_rate(85, g) == base * math.exp(-decay * (85 - ref))


def test_pflege_tariff_deterioration_is_zero_at_grade_5(product_models):
    item = product_models("pflegerentenversicherung").Projection[1]
    assert item.det_rate(5) == 0.0
    assert item.tar_det_rate(5) == 0.0
    assert item.det_force(60, 5) == 0.0
    assert item.tar_det_rate(1) == min(1.0 - 1e-12, 1.15 * item.det_rate(1))


def test_pflege_recov_load_first_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "pflegerentenversicherung")
    table = folder / "param_tariff_type.csv"
    drop_layer_rows(table, "recov_load_first")
    copy = mx.read_model(folder / MODELS["pflegerentenversicherung"], name="RecProbe")
    try:
        point_id = copy.Data.model_point_table().index[0]
        with pytest.raises(Exception, match="recov_load_first") as raised:
            copy.Projection[point_id].tar_rec_rate(60, 1)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()
