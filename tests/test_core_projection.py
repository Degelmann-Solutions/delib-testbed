"""The cells of the core's ``Projection`` (``docs/core.md``): time axis, tariff basis, decrement
rates, policy counts, cash flows, outputs and checks, expense inflation.

- The time axis: Basis and Riester offset every clock cell by ``clock_offset_mth``, KLV
  counts from issue; RLV's derived ``age`` and ``policy_year`` follow the inception clock, BU's
  ``duration`` floors them before inception, Sofort's ``age`` reads the second life.
- The contract terms: RLV's ``smoker`` reads its codes and rejects others, and the core's
  ``prem_term`` rejects a term beyond the policy term.
- The tariff basis: KLV, RLV, BU and Pflege read their rate from the model point;
  the monthly discount factor equals the annual one on a year start; the tariff
  survivorship is 1 at issue; the net level premium is the benefit value over the annuity.
- The decrement rates: BU's and KLV's derived death rate is the table rate times 0.75; an
  annual certainty falls in the anniversary month (Basis and RV deaths at the terminal age,
  KLV's failed *Beitragsfreistellung*); FRV splits mortality linearly; Index and RLV close the lapse in the final policy year without reading the table;
  RLV's premium-shock test switches the module on through a row of a scratch copy's
  tariff-type file.
- The policy counts: RLV and BU read their count from the model point; RLV opens at it; RLV and
  Index close at exactly zero; the end-of-month count is the next month's opening count and
  an unknown timing is rejected; the survivors mature in the last month; KLV's lapses are
  taken from the survivors of the month's deaths.
- The cash flows: KLV's premium is the instalment times the in-force; RLV's claim total is its
  death claim and its lapse and maturity claims are exactly zero; RV's commutation is a further
  kind and an unknown kind is rejected; Index and RV pay exactly zero commission; KLV's net
  cash flow subtracts its claims kind by kind; RLV's liability cash flow is its net cash flow
  negated.
- The outputs and checks: every product reads ``check_tol`` from the core file ``param_core.csv``
  and a missing row raises; KLV's ``result_cf`` is the core's statement from ``t_start()``;
  RV's annual frame sums the flows and takes its two counts at the year's start; RLV's
  net-cash-flow residual is rebuilt from its frame's columns, and the residual reads the
  frame through its dict, Basis' too; KLV's ``check_net_cf`` closes to the scaled tolerance
  and fails above it.
- The expense inflation: Sofort's derived factor steps on the policy anniversary, Pflege's
  compounds continuously over ``t / 12`` years.
"""
from __future__ import annotations

import math

import modelx as mx
import pytest

from helpers import MODELS, PRODUCTS_DIR, drop_layer_rows, product_copy, raised_value_error


def test_sofort_issue_age_reads_the_second_life_from_surv_age(product_models):
    model = product_models("sofortrente")
    projection = model.Projection
    assert projection.issue_age._is_defined()
    points = model.Data.model_point_table()
    joint = points.index[points["surv_pct"] > 0]
    assert len(joint), "no joint-life model point"
    for point_id in joint:
        item = projection[point_id]
        assert item.issue_age() == int(points.at[point_id, "issue_age"])
        assert item.issue_age(1) == int(points.at[point_id, "issue_age"])
        assert item.issue_age(2) == int(points.at[point_id, "surv_age"])


def test_rlv_age_and_policy_year_follow_the_inception_clock(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.age._is_derived()
    assert projection.policy_year._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in (points.index[0], in_force[0]):
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            assert item.age(t) == item.issue_age() + t // 12, (point_id, t)
            assert item.policy_year(t) == t // 12 + 1, (point_id, t)


@pytest.mark.parametrize("product", ["basisrente", "riester_rente"])
def test_the_valuation_clock_offsets_every_clock_cell(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.clock_offset_mth._is_defined()
    for name in ("k_start", "duration_mth", "duration_y", "age_y", "age"):
        assert projection.cells[name]._is_derived(), name
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in in_force:
        item = projection[point_id]
        d = item.duration_init()
        assert item.clock_offset_mth() == 12 * d
        assert item.k_start() == 0
        for k in range(3):
            assert item.duration_y(k) == d + k, (point_id, k)
        for t in (0, 11, 12, 30):
            assert item.age(t) == item.issue_age() + d + t // 12, (point_id, t)


def test_the_inception_clock_counts_from_issue(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.clock_offset_mth._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in in_force:
        item = projection[point_id]
        assert item.clock_offset_mth() == 0
        assert item.k_start() == item.duration_init()
        for k in range(3):
            assert item.duration_y(k) == k, (point_id, k)


def test_bu_duration_is_floored_before_inception(product_models):
    model = product_models("berufsunfaehigkeit")
    projection = model.Projection
    assert projection.duration._is_defined()
    assert projection.policy_year._is_derived()
    assert projection.age._is_derived()
    points = model.Data.model_point_table()
    new = points.index[points["duration_mth_init"] == 0]
    assert len(new), "no new-business model point"
    item = projection[new[0]]
    assert item.duration(-30) == 0
    assert item.policy_year(-30) == 1
    assert item.age(-30) == item.issue_age()


def test_sofort_age_reads_the_second_life_from_surv_age(product_models):
    model = product_models("sofortrente")
    projection = model.Projection
    assert projection.age._is_defined()
    points = model.Data.model_point_table()
    joint = points.index[points["surv_pct"] > 0]
    assert len(joint), "no joint-life model point"
    for point_id in joint:
        item = projection[point_id]
        assert item.age(0) == int(points.at[point_id, "issue_age"])
        assert item.age(0, 2) == int(points.at[point_id, "surv_age"])
        assert item.age(24, 2) == int(points.at[point_id, "surv_age"]) + 2


def test_rlv_smoker_reads_its_codes_and_rejects_others(tmp_path, product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.smoker._is_derived()
    assert projection.smoker_codes._is_defined()
    points = model.Data.model_point_table().copy()
    smokers = points.index[points["smoker"] == "R"]
    assert len(smokers), "no smoker model point"
    assert projection[smokers[0]].smoker() == "R"

    folder = product_copy(tmp_path, "risikolebensversicherung")
    table = folder / "model_point_table.csv"
    points.loc[smokers[0], "smoker"] = "S"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="SmokerProbe")
    try:
        with pytest.raises(Exception, match="invalid smoker"):
            copy.Projection[smokers[0]].smoker()
    finally:
        copy.close()


def test_core_prem_term_rejects_a_term_beyond_the_policy_term(tmp_path, product_models):
    model = product_models("risikolebensversicherung")
    assert model.Projection.prem_term._is_derived()
    points = model.Data.model_point_table().copy()
    point_id = points.index[0]
    assert model.Projection[point_id].prem_term() <= model.Projection[point_id].policy_term()

    folder = product_copy(tmp_path, "risikolebensversicherung")
    points.loc[point_id, "prem_term"] = points.loc[point_id, "policy_term"] + 1
    points.to_csv(folder / "model_point_table.csv")
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="PremTermProbe")
    try:
        with pytest.raises(Exception, match="prem_term outside 1 .. policy_term"):
            copy.Projection[point_id].prem_term()
    finally:
        copy.close()


def test_klv_in_force_point_reads_its_own_rechnungszins(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.rechnungszins._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in in_force:
        assert (projection[point_id].rechnungszins()
                == float(points.at[point_id, "rechnungszins"])), point_id


@pytest.mark.parametrize("product", ["berufsunfaehigkeit", "pflegerentenversicherung",
                                     "risikolebensversicherung"])
def test_rechnungszins_is_read_from_the_model_point(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.rechnungszins._is_derived()
    points = model.Data.model_point_table()
    for point_id in points.index:
        assert projection[point_id].rechnungszins() == 0.01, point_id


def test_pflege_monthly_discount_equals_the_annual_one_on_a_year_start(product_models):
    projection = product_models("pflegerentenversicherung").Projection
    assert projection.disc_factor_mth._is_derived()
    assert projection.disc_factor._is_derived()
    item = projection[1]
    for y in range(4):
        assert item.disc_factor_mth(12 * y) == item.disc_factor(y), y


def test_rlv_tariff_survivorship_is_one_at_issue_on_an_in_force_point(product_models):
    model = product_models("risikolebensversicherung")
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    item = model.Projection[in_force[0]]
    assert item.t_start() > 0
    assert item.pols_tariff(0) == 1.0


@pytest.mark.parametrize("product", ["kapitallebensversicherung", "risikolebensversicherung"])
def test_net_level_premium_divides_benefit_pv_by_tariff_annuity(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.prem_net_level_pp._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert (item.prem_net_level_pp()
                == item.tariff_benefit_pv() / item.tariff_annuity()), point_id


@pytest.mark.parametrize("product", ["kapitallebensversicherung", "risikolebensversicherung"])
def test_annual_discount_factor_is_the_rechnungszins_power(product, product_models):
    projection = product_models(product).Projection
    assert projection.disc_factor._is_derived()
    item = projection[1]
    assert item.disc_factor(3) == (1.0 + item.rechnungszins()) ** -3


def test_bu_mort_rate_steps_its_table_by_the_factor_from_its_tariff_type_file(product_models):
    model = product_models("berufsunfaehigkeit")
    projection = model.Projection
    assert projection.mort_rate._is_derived()
    assert projection.mort_rate_at_age._is_derived()
    assert projection.mort_be_factor._is_defined()
    assert model.Data.param("mort_be_factor") == 0.75
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.mort_be_factor() == 0.75
        for t in range(item.proj_len()):
            assert item.mort_rate(t) == item.mort_rate_at_age(item.age(t)) * 0.75, (point_id, t)


def test_klv_mort_rate_steps_its_table_by_the_factor_from_its_tariff_type_file(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.mort_rate._is_derived()
    assert projection.mort_be_factor._is_defined()
    assert model.Data.param("mort_be_factor") == 0.75
    item = projection[model.Data.model_point_table().index[0]]
    assert item.mort_be_factor() == 0.75
    for t in range(item.proj_len()):
        assert item.mort_rate(t) == min(1.0, item.mort_rate_base(t) * 0.75), t


@pytest.mark.parametrize("product", ["basisrente", "klassische_rentenversicherung"])
def test_a_certain_death_falls_in_the_anniversary_month(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.mort_rate_mth._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    terminal = [t for t in range(item.proj_len()) if item.mort_rate(t) == 1.0]
    assert terminal, "no month with mort_rate = 1"
    start = terminal[0] - terminal[0] % 12
    assert all(item.mort_rate(start + m) == 1.0 for m in range(12))
    assert [item.mort_rate_mth(start + m) for m in range(12)] == [0.0] * 11 + [1.0]
    assert item.is_anniv(start + 11)


def test_frv_splits_mortality_linearly(product_models):
    model = product_models("fondsgebundene_rentenversicherung")
    projection = model.Projection
    assert projection.mort_rate_mth._is_defined()
    assert projection.mort_rate._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    for t in range(item.proj_len()):
        assert item.mort_rate_mth(t) == item.mort_rate(t) / 12.0, t


@pytest.mark.parametrize("product", ["indexpolice", "risikolebensversicherung"])
def test_lapse_is_closed_in_the_final_policy_year_without_reading_the_table(
        product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.lapse_rate._is_derived()
    assert projection.lapse_factor._is_defined()
    item = projection[model.Data.model_point_table().index[0]]
    final = 12 * (item.proj_len_y() - 1)
    for t in range(final, item.proj_len()):
        assert item.lapse_rate(t) == 0.0, t
        names = {node.obj.name for node in item.lapse_rate.precedents(t)}
        assert names == {"lapse_factor"}, (t, names)
    assert item.lapse_rate(final - 1) > 0.0


def _rebate_cut_from_policy_year_4(t):
    """The declaration cut to nothing from policy year 4: the bill rises to the guaranteed one."""
    return 0.0 if duration(t) >= 3 else prem_rebate_level_pp(t)      # noqa: F821


def test_rlv_lapse_rate_is_the_table_rate_times_the_shock_factor(tmp_path):
    """With the premium-shock module on and the declaration cut in year 4, the shock fires."""
    folder = product_copy(tmp_path, "risikolebensversicherung")
    param_file = folder / "param_tariff_type.csv"
    text = param_file.read_text(encoding="utf-8")
    assert text.count("\nshock_lapse_lambda,0.0,") == 1
    param_file.write_text(text.replace("\nshock_lapse_lambda,0.0,", "\nshock_lapse_lambda,2.0,"),
                          encoding="utf-8")
    model = mx.read_model(folder / MODELS["risikolebensversicherung"], name="ShockProbe")
    try:
        projection = model.Projection
        assert projection.lapse_rate._is_derived()
        assert model.Data.param("shock_lapse_lambda") == 2.0
        projection.new_cells("prem_rebate_level_pp", formula=projection.prem_rebate_pp.formula)
        projection.prem_rebate_pp.formula = _rebate_cut_from_policy_year_4
        item = projection[model.Data.model_point_table().index[0]]
        final = 12 * (item.proj_len_y() - 1)
        shocked = [t for t in range(item.t_start(), final) if item.shock_lapse_factor(t) > 1.0]
        assert shocked, "the premium shock never fires"
        for t in shocked:
            assert (item.lapse_rate(t)
                    == item.lapse_rate_base(t) * item.shock_lapse_factor(t)), t
            assert item.lapse_rate(t) > item.lapse_rate_base(t), t
        for t in range(final, item.proj_len()):
            assert item.lapse_rate(t) == 0.0, t
    finally:
        model.close()


def test_klv_failed_beitragsfreistellung_lapses_in_the_anniversary_month(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.lapse_rate_mth._is_derived()
    failing = [p for p in model.Data.model_point_table().index if projection[p].bfz_fails()]
    assert failing, "no model point with a failed Beitragsfreistellung"
    item = projection[failing[0]]
    start = 12 * (item.bfz_year() - 1)
    assert all(item.lapse_rate(start + m) == 1.0 for m in range(12))
    assert [item.lapse_rate_mth(start + m) for m in range(12)] == [0.0] * 11 + [1.0]
    assert item.is_anniv(start + 11)


@pytest.mark.parametrize("product", ["berufsunfaehigkeit", "risikolebensversicherung"])
def test_pols_if_init_is_read_from_the_model_point(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_if_init._is_derived()
    points = model.Data.model_point_table()
    assert (points["pols_if_init"] == 1.0).all()
    for point_id in points.index:
        assert projection[point_id].pols_if_init() == 1.0, point_id


@pytest.mark.parametrize("product", ["berufsunfaehigkeit", "kapitallebensversicherung",
                                     "pflegerentenversicherung", "risikolebensversicherung"])
def test_the_end_of_month_count_is_the_next_start_of_month_count(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_if_at._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    # BU's frame opens at t = 0, the valuation month: its pols_if guards on t < 0 and does
    # not use the t_start() it inherits from the core.
    start = 0 if product == "berufsunfaehigkeit" else item.t_start()
    for t in range(start, item.proj_len()):
        assert item.pols_if_at(t, "BEF_DECR") == item.pols_if(t), t
        assert item.pols_if_at(t, "AFT_DECR") == item.pols_if(t + 1), t
    with pytest.raises(Exception, match="invalid timing") as raised:
        item.pols_if_at(start, "END")
    # modelx re-raises a formula's error as a FormulaError without chaining it, and names
    # the original type in its message.
    chain, error = [], raised.value
    while error is not None and error not in chain:
        chain.append(error)
        error = error.__cause__ or error.__context__
    assert (any(isinstance(e, ValueError) for e in chain)
            or "ValueError: invalid timing" in str(raised.value)), raised.value


def test_klv_lapses_are_taken_from_the_survivors_of_the_deaths(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.pols_lapse._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    lapsing = [t for t in range(item.t_start(), item.proj_len()) if item.pols_lapse(t) > 0.0]
    assert lapsing, "no month with lapses"
    for t in range(item.t_start(), item.proj_len()):
        assert (item.pols_lapse(t)
                == item.pols_if_at(t, "AFT_DEATH") * item.lapse_rate_mth(t)), t
        assert (item.pols_if_at(t, "AFT_DEATH")
                == item.pols_if(t) * (1.0 - item.mort_rate_mth(t))), t


@pytest.mark.parametrize("product", ["fondsgebundene_rentenversicherung", "indexpolice",
                                     "kapitallebensversicherung", "risikolebensversicherung"])
def test_the_survivors_of_both_decrements_mature_in_the_last_month(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_maturity._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    last = item.proj_len() - 1
    for t in range(item.t_start(), last):
        assert item.pols_maturity(t) == 0.0, t
    # The lapse is closed in the last month, so the survivors of both decrements are the
    # survivors of the month's deaths.
    assert item.lapse_rate_mth(last) == 0.0
    assert item.pols_lapse(last) == 0.0
    assert item.pols_maturity(last) > 0.0
    assert item.pols_maturity(last) == item.pols_if_at(last, "AFT_DEATH")


def test_rlv_opens_at_pols_if_init_on_new_and_in_force_points(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.pols_if._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in (points.index[0], in_force[0]):
        item = projection[point_id]
        assert item.pols_if(item.t_start()) == item.pols_if_init(), point_id
        assert item.pols_if(item.t_start() - 1) == 0.0, point_id


@pytest.mark.parametrize("product", ["indexpolice", "risikolebensversicherung"])
def test_the_count_after_the_last_month_is_exactly_positive_zero(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_if._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        closing = item.pols_if(item.proj_len())
        assert closing == 0.0 and math.copysign(1.0, closing) == 1.0, point_id
        assert item.pols_maturity(item.proj_len() - 1) > 0.0, point_id


def test_klv_premium_is_the_instalment_times_the_in_force(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.premiums._is_derived()
    assert projection.pols_prem._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        paying = [t for t in range(item.t_start(), item.proj_len()) if item.premiums(t) > 0.0]
        assert paying, point_id
        for t in range(item.t_start(), item.proj_len()):
            assert item.pols_prem(t) == item.pols_if(t), (point_id, t)
            assert item.premiums(t) == item.prem_inst_pp(t) * item.pols_prem(t), (point_id, t)


def test_rlv_claim_total_is_the_death_claim_and_the_cash_values_are_zero(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.claims._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.claim_kinds() == ("DEATH", "LAPSE", "MATURITY")
        for t in range(item.t_start(), item.proj_len()):
            assert item.claims(t) == item.claims(t, "DEATH"), (point_id, t)
            for kind in ("LAPSE", "MATURITY"):
                zero = item.claims(t, kind)
                assert zero == 0.0 and math.copysign(1.0, zero) == 1.0, (point_id, t, kind)


def test_rv_commutation_is_a_further_kind_and_an_unknown_kind_is_rejected(product_models):
    model = product_models("klassische_rentenversicherung")
    projection = model.Projection
    assert projection.claims._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    commuting = [t for t in range(item.t_start(), item.proj_len())
                 if item.pols_commutation(t) > 0.0]
    assert commuting, "no month with commutations"
    for t in commuting:
        assert (item.claims(t, "COMMUTATION")
                == item.claims_other(t, "COMMUTATION")
                == item.capital_conv_pp() * item.pols_commutation(t)), t
    with pytest.raises(Exception, match="invalid kind") as raised:
        item.claims(item.t_start(), "ANNUITY")
    assert raised_value_error(raised, "invalid kind"), raised.value


@pytest.mark.parametrize("product", ["indexpolice", "klassische_rentenversicherung"])
def test_a_product_without_commission_pays_exactly_zero(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.commissions._is_derived()
    assert projection.comm_init_rate._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            zero = item.commissions(t)
            assert zero == 0.0 and math.copysign(1.0, zero) == 1.0, (point_id, t)


def test_klv_net_cf_subtracts_each_claim_kind_in_turn(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.net_cf._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            expected = (item.premiums(t) - item.claims(t, "DEATH")
                        - item.claims(t, "MATURITY") - item.claims(t, "LAPSE")
                        - item.expenses(t) - item.commissions(t))
            assert math.copysign(1.0, item.net_cf(t)) == math.copysign(1.0, expected)
            assert item.net_cf(t) == expected, (point_id, t)


def test_rlv_liability_cf_is_the_negated_net_cf(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.liability_cf._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            assert item.liability_cf(t) == -item.net_cf(t), (point_id, t)
            assert (math.copysign(1.0, item.liability_cf(t))
                    == -math.copysign(1.0, item.net_cf(t))), (point_id, t)


ROLL_FWD_TOL = {
    "basisrente": 1e-08,
    "berufsunfaehigkeit": 1e-08,
    "fondsgebundene_rentenversicherung": 1e-08,
    "indexpolice": 1e-08,
    "kapitallebensversicherung": 1e-08,
    "klassische_rentenversicherung": 1e-08,
    "pflegerentenversicherung": 1e-08,
    "riester_rente": 1e-08,
    "risikolebensversicherung": 1e-08,
    "sofortrente": 1e-08,
}


@pytest.mark.parametrize("product", sorted(MODELS))
def test_roll_fwd_tol_is_read_from_the_core_file(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.roll_fwd_tol._is_derived()
    assert "roll_fwd_tol" not in projection.refs
    assert "roll_fwd_tol" not in model.Data.param_dict()
    assert "check_tol" in model.Data.param_layers()["core"]
    point_id = model.Data.model_point_table().index[0]
    assert projection[point_id].roll_fwd_tol() == ROLL_FWD_TOL[product]


def test_roll_fwd_tol_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "kapitallebensversicherung")
    table = folder / MODELS["kapitallebensversicherung"] / "CoreData" / "param_core.csv"
    drop_layer_rows(table, "check_tol")
    copy = mx.read_model(folder / MODELS["kapitallebensversicherung"], name="TolProbe")
    try:
        point_id = copy.Data.model_point_table().index[0]
        with pytest.raises(Exception, match="check_tol") as raised:
            copy.Projection[point_id].roll_fwd_tol()
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_klv_result_cf_is_the_core_statement_from_t_start(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.result_cf._is_derived()
    assert projection.result_cf_columns._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        frame = item.result_cf()
        assert list(frame.columns) == [
            "pols_if", "premiums", "claims_death", "claims_maturity", "claims_lapse",
            "expenses", "commissions", "net_cf", "liability_cf"], point_id
        assert frame.index.name == "t"
        assert list(frame.index) == list(range(item.t_start(), item.proj_len())), point_id
        t = item.t_start()
        assert frame.loc[t, "claims_lapse"] == item.claims(t, "LAPSE")
        assert frame.loc[t, "pols_if"] == item.pols_if_init()


def test_rv_result_cf_annual_sums_flows_and_takes_counts_at_the_year_start(product_models):
    model = product_models("klassische_rentenversicherung")
    projection = model.Projection
    assert projection.result_cf_annual._is_derived()
    assert projection.result_cf_counts._is_defined()
    item = projection[model.Data.model_point_table().index[0]]
    monthly = item.result_cf()
    annual = item.result_cf_annual()
    assert annual.index.name == "policy_year"
    assert list(annual.columns[:2]) == ["pols_if", "pols_annuity"]
    assert list(annual.columns[2:]) == [c for c in monthly.columns
                                        if c not in ("pols_if", "pols_annuity")]
    for year in annual.index:
        months = [t for t in monthly.index if item.duration(t) + 1 == year]
        start = months[0]
        assert annual.loc[year, "pols_if"] == monthly.loc[start, "pols_if"], year
        assert annual.loc[year, "pols_annuity"] == monthly.loc[start, "pols_annuity"], year
        for column in annual.columns[2:]:
            assert annual.loc[year, column] == pytest.approx(
                monthly.loc[months, column].sum(), rel=1e-12, abs=1e-9), (year, column)


def test_rlv_net_cf_resid_rebuilds_net_cf_from_the_frame(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.check_net_cf_resid._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.net_cf_income_columns() == ("premiums",)
        assert item.net_cf_outgo_columns() == (
            "claims_death", "claims_lapse", "claims_maturity", "expenses", "commissions")
        frame = item.result_cf()
        for t in frame.index:
            row = frame.loc[t]
            rebuilt = (row["premiums"] - row["claims_death"] - row["claims_lapse"]
                       - row["claims_maturity"] - row["expenses"] - row["commissions"])
            resid = item.check_net_cf_resid(t)
            assert resid == float(row["net_cf"] - rebuilt), (point_id, t)
            assert resid == 0.0, (point_id, t)


@pytest.mark.parametrize("product", [
    "kapitallebensversicherung", "klassische_rentenversicherung", "riester_rente",
    "risikolebensversicherung"])
def test_net_cf_resid_reads_the_frame_through_its_dict(product_models, product):
    model = product_models(product)
    projection = model.Projection
    assert projection.check_net_cf_resid._is_derived()
    assert projection.result_cf_dict._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        frame = item.result_cf()
        columns = item.result_cf_dict()
        assert list(columns) == list(frame.columns), point_id
        for label in frame.columns:
            assert list(columns[label]) == list(frame.index), (point_id, label)
            for t in frame.index:
                assert columns[label][t] == frame.at[t, label], (point_id, label, t)
        with pytest.raises(Exception, match=f"KeyError: {item.proj_len()}\n"):
            item.check_net_cf_resid(item.proj_len())


def _resid_just_above_tolerance(t):
    """A residual a little above the month's scaled tolerance."""
    return check_net_cf_tol(t) * 1.01                                # noqa: F821


def _resid_just_below_tolerance(t):
    """A residual a little below the month's scaled tolerance."""
    return -check_net_cf_tol(t) * 0.99                               # noqa: F821


def test_klv_check_net_cf_closes_to_the_scaled_tolerance(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.check_net_cf._is_derived()
    assert projection.check_net_cf_tol._is_derived()
    assert projection.check_net_cf_scale._is_defined()
    point_id = model.Data.model_point_table().index[0]
    item = projection[point_id]
    assert item.check_net_cf() is True
    t = item.t_start()
    assert item.check_net_cf_tol(t) == item.roll_fwd_tol() * max(item.sum_assured(), 1.0)

    # A residual just below roll_fwd_tol() * check_net_cf_scale(t) passes, one just above fails.
    folder = PRODUCTS_DIR / "kapitallebensversicherung" / MODELS["kapitallebensversicherung"]
    copy = mx.read_model(folder, name="NetCfProbe")
    try:
        copy.Projection.check_net_cf_resid.formula = _resid_just_below_tolerance
        assert copy.Projection[point_id].check_net_cf() is True
        copy.Projection.check_net_cf_resid.formula = _resid_just_above_tolerance
        assert copy.Projection[point_id].check_net_cf() is False
    finally:
        copy.close()


def test_sofort_inflation_factor_steps_on_the_policy_anniversary(product_models):
    model = product_models("sofortrente")
    projection = model.Projection
    assert projection.inflation_factor._is_derived()
    assert projection.inflation_years._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.expense_infl() == 0.02
        for t in range(item.t_start(), item.proj_len()):
            assert item.inflation_factor(t) == 1.02 ** item.duration(t), (point_id, t)
            assert item.inflation_factor(t) == 1.02 ** (t // 12), (point_id, t)


def test_pflege_inflation_factor_compounds_continuously(product_models):
    model = product_models("pflegerentenversicherung")
    projection = model.Projection
    assert projection.inflation_factor._is_derived()
    assert projection.inflation_years._is_defined()
    point_id = model.Data.model_point_table().index[0]
    item = projection[point_id]
    assert item.expense_infl() == 0.02
    assert item.inflation_factor(6) == 1.02 ** 0.5
    assert item.inflation_factor(0) == 1.0


def test_basis_net_cf_resid_reads_the_frame_through_its_dict(product_models):
    model = product_models("basisrente")
    projection = model.Projection
    assert projection.check_net_cf_resid._is_defined()
    assert projection.result_cf_dict._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        frame = item.result_cf()
        columns = item.result_cf_dict()
        assert list(columns) == list(frame.columns), point_id
        for label in frame.columns:
            assert list(columns[label]) == list(frame.index), (point_id, label)
            for t in frame.index:
                assert columns[label][t] == frame.at[t, label], (point_id, label, t)
        for t in frame.index:
            row = frame.loc[t]
            expected = float(row["premiums"]
                             - row["claims_death"] - row["claims_annuity"]
                             - row["claims_survivor"] - row["expenses"]
                             - row["commissions"] - row["net_cf"])
            assert item.check_net_cf_resid(t) == expected, (point_id, t)
        with pytest.raises(Exception, match=f"KeyError: {item.proj_len()}\n"):
            item.check_net_cf_resid(item.proj_len())
