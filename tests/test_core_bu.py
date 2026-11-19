"""BU's cohorts on the common core (``docs/core.md``): the claim-cohort arrays and the rates by
age.

- Ages outside its inception table hold the table's ends.
- The cohort arrays equal the list recursion and seed age and step; the cohort index and
  step sliced equal the vectors by month; the rate tuples by age equal the
  cells by claim year, and the rate arrays by age the tuples.
- The shared caches are read-only: BU's cohort index and step arrays, their slices included,
  raise on a write.
- BU's claim-year caps are the last ``dur_year`` of its claim-duration table, so a scratch
  copy with a twelfth row reads it.
"""
from __future__ import annotations

import modelx as mx
import numpy as np
import pytest

from helpers import MODELS, product_copy


def test_bu_ages_outside_the_inception_table_hold_its_ends(product_models):
    """The mortality lookups clamp nothing: they read the table factory
    (``tests/test_tables.py``)."""
    model = product_models("berufsunfaehigkeit")
    inception = model.Data.inception_table()
    item = model.Projection[model.Data.model_point_table().index[0]]
    assert (int(inception.index.min()), int(inception.index.max())) == (18, 66)
    assert item.inc_rate_at_age(10) == float(inception.at[18, "inc_rate"])
    assert item.inc_rate_at_age(80) == float(inception.at[66, "inc_rate"])


def _bu_roll_reference(qy, ry, g, ppols, pval, n):
    """The disabled ledger's roll before story 2.14: a Python loop over lists."""
    pols = [0.0] * n
    val = [0.0] * n
    for i in range(min(len(ppols), n - 1)):
        cy = min(i // 12, 10)
        keep = (1.0 - qy[cy]) * (1.0 - ry[cy])
        step = g if (i + 1) % 12 == 0 else 1.0
        pols[i + 1] = ppols[i] * keep
        val[i + 1] = pval[i] * keep * step
    return pols, val


def _bu_exits_reference(qy, ry, pols, val):
    """The disabled ledger's exits before story 2.14: three totals added left to right."""
    deaths = rec = recval = 0.0
    for i in range(len(pols)):
        cy = min(i // 12, 10)
        q, r = qy[cy], ry[cy]
        deaths += pols[i] * q
        rec += pols[i] * (1.0 - q) * r
        recval += val[i] * (1.0 - q) * r
    return deaths, rec, recval


def _bu_ledger_cells(item, first):
    """The cells of one of BU's two disabled ledgers, the best-estimate or the first-order one."""
    if first:
        return (item.first_len(), item.dis_cohorts_first, item.dis_exits_first,
                item.cohort_len_first, item.age_first, item.mort_rate_dis_first_mth_year,
                item.recov_rate_first_mth_year(), item.pols_inception_first,
                item.bu_rente_pp_first)
    return (item.proj_len(), item.dis_cohorts, item.dis_exits, item.cohort_len, item.age,
            item.mort_rate_dis_mth_year, item.recov_rate_mth_year(), item.pols_inception,
            item.bu_rente_pp)


@pytest.mark.parametrize("first", [False, True], ids=["best_estimate", "first_order"])
def test_bu_cohort_arrays_equal_the_list_recursion(product_models, first):
    """``dis_cohorts*`` and ``dis_exits*`` give the old loop's bits, as arrays and floats."""
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        end, cohorts, exits, length, age, mort_year, ry, inception, rente = (
            _bu_ledger_cells(item, first))
        g = 1.0 + item.leistungsdyn_rate()
        months = {0, 1, 13, 121, end}
        ref = None
        for t in range(end + 1):
            pols, val = cohorts(t)
            if t == 0:
                n = length(0)
                ref = ([0.0] * n, [0.0] * n)
                z0 = 0 if first else item.seed_claim_dur()
                if z0 and z0 <= n:
                    ref[0][z0 - 1] = item.pols_if_init()
                    ref[1][z0 - 1] = item.pols_if_init() * item.rente_pay_pp(0, z0)
            else:
                ref = _bu_roll_reference(mort_year(age(t - 1)), ry, g, *ref, length(t))
                ref[0][0] = inception(t - 1)
                ref[1][0] = ref[0][0] * rente(t - 1)
            if t not in months:
                continue
            assert isinstance(pols, np.ndarray) and isinstance(val, np.ndarray), (point_id, t)
            assert pols.tolist() == ref[0], (point_id, t)
            assert val.tolist() == ref[1], (point_id, t)
            got = exits(t)
            assert all(type(x) is float for x in got), (point_id, t)
            assert got == _bu_exits_reference(mort_year(age(t)), ry, ref[0], ref[1]), (
                point_id, t)


def test_bu_rate_tuples_by_age_equal_the_cells_by_claim_year(product_models):
    """The tuples keyed by attained age hold ``mort_rate_dis_mth`` and its first-order twin."""
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        for t in sorted({0, 1, 13, 121, item.proj_len() - 1}):
            year = item.mort_rate_dis_mth_year(item.age(t))
            assert len(year) == 11
            assert year == tuple(item.mort_rate_dis_mth(t, 12 * cy + 1)
                                 for cy in range(11)), (point_id, t)
        for s in sorted({0, 1, 13, 121, item.first_len() - 1}):
            year = item.mort_rate_dis_first_mth_year(item.age_first(s))
            assert year == tuple(item.mort_rate_dis_first_mth(s, 12 * cy + 1)
                                 for cy in range(11)), (point_id, s)


def test_bu_cohort_arrays_seed_age_and_step(product_models):
    """The seeded state, claim year 11, the onset anniversary, the full length, ``pols_dis_dur``."""
    model = product_models("berufsunfaehigkeit")
    points = model.Data.model_point_table()
    aktiv = model.Projection[points.index[points["status"] == "aktiv"][0]]
    pols, val = aktiv.dis_cohorts(0)
    assert aktiv.seed_claim_dur() == 0
    assert pols.tolist() == [0.0] and val.tolist() == [0.0]
    leistung = points.index[points["status"] == "leistung"]
    assert len(leistung), "no in-claim model point"
    item = model.Projection[leistung[0]]
    z0 = item.seed_claim_dur()
    assert 1 <= z0 <= item.cohort_len(0)
    pols, val = item.dis_cohorts(0)
    assert pols[z0 - 1] == item.pols_if_init()
    assert val[z0 - 1] == item.pols_if_init() * item.rente_pay_pp(0, z0)
    assert np.count_nonzero(pols) == 1 and np.count_nonzero(val) == 1

    keep = [(1.0 - q) * (1.0 - r) for q, r in zip(item.mort_rate_dis_mth_year(item.age(130)),
                                                  item.recov_rate_mth_year())]
    g = 1.0 + item.leistungsdyn_rate()
    assert g != 1.0
    ppols, pval = item.dis_cohorts(130)
    pols, val = item.dis_cohorts(131)
    for i in (119, 120, 125, len(ppols) - 1):
        cy = min(i // 12, 10)
        assert cy == (10 if i >= 120 else 9)
        step = g if (i + 1) % 12 == 0 else 1.0
        assert pols[i + 1] == ppols[i] * keep[cy], i
        assert val[i + 1] == pval[i] * keep[cy] * step, i
    assert val[120] != pval[119] * keep[9]

    end = item.proj_len()
    assert item.cohort_len(end) == item.max_claim_dur()
    pols, val = item.dis_cohorts(end)
    assert len(pols) == item.max_claim_dur()
    assert pols[-1] == 0.0 and val[-1] == 0.0
    assert item.check_dis_roll_fwd()

    for dur, cohorts, length, t in ((item.pols_dis_dur, item.dis_cohorts, item.cohort_len, 13),
                                    (item.pols_dis_dur_first, item.dis_cohorts_first,
                                     item.cohort_len_first, 13)):
        n = length(t)
        assert dur(t, 0) == 0.0 and dur(t, n + 1) == 0.0
        assert type(dur(t, 1)) is float and dur(t, 1) == cohorts(t)[0][0]
        assert type(dur(t, n)) is float
    assert type(item.pols_dis(13)) is float and type(item.pols_dis_first(13)) is float


def test_bu_cohort_index_and_step_sliced_equal_the_vectors_by_month(product_models):
    """``cohort_year_idx`` and ``cohort_anniv_step`` at full length, sliced, are the old vectors.

    Both orders: the best estimate at ``max_claim_dur()``, the first order at
    ``first_len() + 1``; every slice ``[:m]`` with ``m <= n``, the empty one included, equals
    the array the ledgers built for that month.
    """
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        g = 1.0 + item.leistungsdyn_rate()
        for n in (item.max_claim_dur(), item.first_len() + 1):
            idx, step = item.cohort_year_idx(n), item.cohort_anniv_step(n)
            assert len(idx) == len(step) == n
            for m in sorted({0, 1, 11, 12, 13, 120, 121, n - 1, n}):
                ref_idx = np.minimum(np.arange(m) // 12, 10)
                ref_step = np.where(np.arange(1, m + 1) % 12 == 0, g, 1.0)
                assert idx[:m].dtype == ref_idx.dtype
                assert idx[:m].tolist() == ref_idx.tolist(), (point_id, n, m)
                assert step[:m].tolist() == ref_step.tolist(), (point_id, n, m)
        item.result_cf()
        for n in (item.max_claim_dur(), item.first_len() + 1):
            assert item.cohort_year_idx(n).tolist() == np.minimum(np.arange(n) // 12, 10).tolist()
            assert item.cohort_anniv_step(n).tolist() == np.where(
                np.arange(1, n + 1) % 12 == 0, g, 1.0).tolist(), "a reader mutated the cache"


def test_bu_cohort_index_and_step_are_read_only(product_models):
    """A write into ``cohort_year_idx`` or ``cohort_anniv_step``, or a slice of it, raises."""
    model = product_models("berufsunfaehigkeit")
    item = model.Projection[model.Data.model_point_table().index[0]]
    for n in (item.max_claim_dur(), item.first_len() + 1):
        for array in (item.cohort_year_idx(n), item.cohort_anniv_step(n)):
            before = array.tolist()
            with pytest.raises(ValueError):
                array[0] = 5
            with pytest.raises(ValueError):
                array[:13][0] = 5
            with pytest.raises(ValueError):
                array[:13] *= 2
            assert array.tolist() == before
    assert item.cohort_year_idx(item.max_claim_dur())[0] == 0


def test_bu_claim_years_are_read_from_the_claim_duration_table(tmp_path, product_models):
    """The claim-year cap is the table's last ``dur_year``, so a twelfth row is read too."""
    data = product_models("berufsunfaehigkeit").Data
    table = data.claim_duration_table()
    last = data.claim_duration_last_year()
    assert type(last) is int and last == int(table.index.max()) == len(table) == 11
    folder = product_copy(tmp_path, "berufsunfaehigkeit")
    path = folder / "claim_duration_table.csv"
    path.write_text(path.read_text(encoding="utf-8") + '12,0.005,"[std] test fixture"\n',
                    encoding="utf-8")
    copy = mx.read_model(folder / MODELS["berufsunfaehigkeit"], name="ClaimYearProbe")
    try:
        assert copy.Data.claim_duration_last_year() == 12
        item = copy.Projection[copy.Data.model_point_table().index[0]]
        assert [item.claim_year(z) for z in (1, 12, 13, 132, 133, 144, 145, 999)] == [
            1, 1, 2, 11, 12, 12, 12, 12]
        assert item.recov_rates()[11] == 0.005 and len(item.recov_rates()) == 12
        # the mortality tuples run over the twelve claim years too, the twelfth at the
        # table factory's last select factor like every year from the sixth
        for year in (item.mort_rate_dis_mth_year(40), item.mort_rate_dis_first_mth_year(40)):
            assert len(year) == 12 and year[11] == year[5] and year[4] > year[5]
        assert item.cohort_year_idx(300).tolist() == np.minimum(np.arange(300) // 12, 11).tolist()
    finally:
        copy.close()


def test_bu_rate_arrays_by_age_equal_the_tuples(product_models):
    """``dis_keep_year*``, ``dis_q_year*`` and ``recov_year*`` hold the tuples' values as arrays.

    The keep factor is ``(1 - q)(1 - r)`` of the tuples at ``x``, element for element; the
    arrays survive a full run unmutated.
    """
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        item.result_cf()
        ages = {item.age(t) for t in range(item.proj_len() + 1)}
        ages_first = {item.age_first(s) for s in range(item.first_len() + 1)}
        for x in sorted(ages):
            qy, ry = item.mort_rate_dis_mth_year(x), item.recov_rate_mth_year()
            keep = item.dis_keep_year(x)
            assert isinstance(keep, np.ndarray) and len(keep) == 11
            assert keep.tolist() == [(1.0 - q) * (1.0 - r) for q, r in zip(qy, ry)], (point_id, x)
            assert item.dis_q_year(x).tolist() == list(qy), (point_id, x)
        assert item.recov_year().tolist() == list(item.recov_rate_mth_year())
        for x in sorted(ages_first):
            qy, ry = item.mort_rate_dis_first_mth_year(x), item.recov_rate_first_mth_year()
            assert item.dis_keep_year_first(x).tolist() == [
                (1.0 - q) * (1.0 - r) for q, r in zip(qy, ry)], (point_id, x)
            assert item.dis_q_year_first(x).tolist() == list(qy), (point_id, x)
        assert item.recov_year_first().tolist() == list(item.recov_rate_first_mth_year())
