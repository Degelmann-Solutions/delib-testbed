# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The shared by-policy cells; a product's ``Projection`` inherits them as ``CoreProjection``.

The space is parameterized by ``point_id``, like the product's ``Projection``. Its cells use
the names the product's ``Projection`` defines: ``data`` for the product's ``Data`` and
``point_id`` for the selected model point.
"""

from modelx.serialize.jsonvalues import *

_formula = lambda point_id: None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def model_point():
    """The selected model point as a Series."""
    return data.model_point_table().loc[point_id]                    # noqa: F821


def policy_id():
    """The policy identifier of the selected model point; reporting only."""
    return model_point()["policy_id"]                                # noqa: F821


def sum_assured():
    """The sum insured at issue, from the model point's ``sum_assured`` column."""
    return float(model_point()["sum_assured"])                       # noqa: F821


def rating_factor():
    """The *Risikozuschlag*, a multiplier from the model point; 1.00 at standard rates."""
    return float(model_point()["rating_factor"])                     # noqa: F821


def scenario_id():
    """The key of the model point's scenario path, from its ``scenario_id`` column."""
    return model_point()["scenario_id"]                              # noqa: F821


def karenz_months():
    """K: the *Karenzzeit*, the deferment of payment from the onset of a claim, in months."""
    return int(model_point()["karenz_months"])                       # noqa: F821


def pols_if_init():
    """The policy count the model point stands for, from its ``pols_if_init`` column.

    The opening value of ``pols_if`` at ``t_start()``: no decrement has been applied when the
    frame opens, so the first ``pols_if`` of the result equals it exactly.  A contract-book
    attribute and so data, not code; 1.0 where the projection is per policy.
    """
    return float(model_point()["pols_if_init"])                      # noqa: F821


def prem_freq():
    """The payment frequency, a key into the product's *freq_loading_table.csv*.

    Raises ``ValueError`` for a frequency the table has no row for.
    """
    v = model_point()["prem_freq"]                                   # noqa: F821
    if v not in data.freq_loading_table().index:                     # noqa: F821
        raise ValueError("no frequency loading for prem_freq " + str(v))
    return v


def prem_freq_load():
    """phi: the *Ratenzahlungszuschlag* for ``prem_freq()``, from *freq_loading_table.csv*."""
    return float(data.freq_loading_table().at[                       # noqa: F821
        prem_freq(), "prem_freq_load"])                              # noqa: F821


def instalments():
    """The number of premium instalments a year for ``prem_freq()``: 1, 2, 4 or 12."""
    return int(data.freq_loading_table().at[                         # noqa: F821
        prem_freq(), "instalments"])                                 # noqa: F821


def issue_age():
    """The age at issue of the selected model point, from its ``issue_age`` column."""
    return int(model_point()["issue_age"])                           # noqa: F821


def sex():
    """The sex of the insured life, ``M`` or ``F``, from the model point."""
    v = model_point()["sex"]                                         # noqa: F821
    if v not in ("M", "F"):
        raise ValueError("invalid sex")
    return v


def smoker_codes():
    """The model point's codes for a non-smoker and a smoker: ``N`` and ``S``."""
    return ("N", "S")


def smoker():
    """The smoker status of the insured life, one of ``smoker_codes()``, from the model point.

    Raises ``ValueError`` for a code outside them.
    """
    v = model_point()["smoker"]                                      # noqa: F821
    if v not in smoker_codes():                                      # noqa: F821
        raise ValueError("invalid smoker")
    return v


def policy_term():
    """The policy term in years, from the model point."""
    return int(model_point()["policy_term"])                         # noqa: F821


def prem_term():
    """The premium payment term in whole years, from the model point.

    Checked against ``1 <= prem_term <= policy_term()``; raises ``ValueError`` outside it.
    """
    k = int(model_point()["prem_term"])                              # noqa: F821
    if k < 1 or k > policy_term():                                   # noqa: F821
        raise ValueError("prem_term outside 1 .. policy_term")
    return k


def prem_term_y():
    """The premium payment term in whole years, from the model point's ``prem_term_y``."""
    return int(model_point()["prem_term_y"])                         # noqa: F821


def issue_year():
    """The calendar year of issue, from the model point's ``issue_year`` column."""
    return int(model_point()["issue_year"])                          # noqa: F821


def duration_init():
    """The completed policy years at the valuation date, from the model point."""
    return int(model_point()["duration_init"])                       # noqa: F821


def duration_mth_init():
    """The completed policy months at the valuation date, from the model point."""
    return int(model_point()["duration_mth_init"])                   # noqa: F821


def clock_offset_mth():
    """The months from issue to ``t = 0``: 0, ``t`` counts policy months from issue.

    The inception clock.  A product whose ``t`` counts months from the valuation date
    overrides it with the policy months completed there; every clock cell below reads it.
    """
    return 0


def k_start():
    """The first projected policy year, ``duration_init() - clock_offset_mth() // 12``.

    ``duration_init()`` on the inception clock, 0 where ``t = 0`` is the valuation date.
    """
    return duration_init() - clock_offset_mth() // 12                # noqa: F821


def t_start():
    """The first projected month, ``12 x k_start()``; ``t`` counts months from issue."""
    return 12 * k_start()                                            # noqa: F821


def proj_year(t):
    """The 0-based projection year month t falls in, ``t // 12``."""
    return t // 12


def duration_mth(t):
    """The completed policy months at the start of month t, ``clock_offset_mth() + t``."""
    return clock_offset_mth() + t                                    # noqa: F821


def duration(t):
    """The completed policy years at the start of month t, ``duration_mth(t) // 12``."""
    return duration_mth(t) // 12                                     # noqa: F821


def duration_y(k):
    """The completed policy years at the start of projection year k, ``duration(12 x k)``."""
    return duration(12 * k)                                          # noqa: F821


def policy_year(t):
    """The contractual 1-based policy year containing month t, ``duration(t) + 1``."""
    return duration(t) + 1                                           # noqa: F821


def policy_year_y(k):
    """The contractual 1-based policy year of projection year k, ``duration_y(k) + 1``."""
    return duration_y(k) + 1                                         # noqa: F821


def age_y(k):
    """The attained age at the start of projection year k, ``issue_age() + duration_y(k)``."""
    return issue_age() + duration_y(k)                               # noqa: F821


def age(t):
    """The attained age in month t, ``issue_age() + duration(t)``, stepping on the anniversary."""
    return issue_age() + duration(t)                                 # noqa: F821


def omega_age():
    """omega: the limiting age, from the product's *param_table.csv*.

    The first age nobody reaches: the death rate is 1 at ``omega_age() - 1``, so a
    projection run to it ends with no survivors.
    """
    return int(data.param_table().at["omega_age", "value"])          # noqa: F821


def ret_age():
    """The attained age at *Rentenbeginn*, from the model point's ``ret_age`` column."""
    return int(model_point()["ret_age"])                             # noqa: F821


def k_conv():
    """T: the projection year in which *Rentenbeginn* falls, ``ret_age() - age(0)``.

    Negative for a model point that opens after *Rentenbeginn*, already in payment.
    """
    return ret_age() - age(0)                                        # noqa: F821


def t_conv():
    """The projection month of *Rentenbeginn*, ``12 x k_conv()``."""
    return 12 * k_conv()                                             # noqa: F821


def horizon_age():
    """The attained age at which the projection ends, ``issue_age() + policy_term()``."""
    return issue_age() + policy_term()                               # noqa: F821


def proj_len():
    """The number of projected months, the frame's exclusive end.

    ``12 x (horizon_age() - issue_age()) - clock_offset_mth()``: the months from issue to
    the horizon, less those completed before ``t = 0``.
    """
    return 12 * (horizon_age() - issue_age()) - clock_offset_mth()   # noqa: F821


def proj_len_y():
    """The number of projected years, ``proj_len() // 12``."""
    return proj_len() // 12                                          # noqa: F821


def calendar_year_y(k):
    """The calendar year of projection year k, ``issue_year() + duration_y(k)``."""
    return issue_year() + duration_y(k)                              # noqa: F821


def calendar_year(t):
    """The calendar year of month t, ``issue_year() + duration(t)``."""
    return issue_year() + duration(t)                                # noqa: F821


def is_anniv(t):
    """Whether month t is the **last** month of its policy year: ``t % 12 == 11``.

    The month the annual machinery acts in, the month before the next anniversary.  A
    decrement that is a certainty rather than a rate (an annual rate of 1) cannot be spread
    geometrically over twelve months without emptying the cohort eleven months early, so the
    monthly rates place it here.
    """
    return t % 12 == 11


def mort_be_factor():
    """The step from the product's mortality table to the best estimate; 1, neutral.

    A product whose best estimate is a multiple of its table overrides it with its own
    value, a tariff parameter in its *param_table.csv*.
    """
    return 1.0


def mort_rate_base(t):
    """The annual table death rate in month t before the best-estimate factor.

    ``mort_rate_at_age(age(t))``: reads the product's ``mort_rate_at_age``, its table rate at
    an attained age; a product without one inherits this cell unused.  Flat across a policy
    year, the attained age stepping on the anniversary.
    """
    return mort_rate_at_age(age(t))                                  # noqa: F821


def mort_rate(t):
    """q(t): the best-estimate **annual** death rate of the policy year containing month t.

    ``min(1, mort_rate_base(t) x mort_be_factor())``: the table rate stepped to the best
    estimate, capped at 1.  The annual rate, flat across a policy year; ``mort_rate_mth``
    is the monthly rate the recursion applies.
    """
    return min(1.0, mort_rate_base(t) * mort_be_factor())            # noqa: F821


def mort_rate_mth(t):
    """The **monthly** death rate applied in month t, the geometric twelfth of ``mort_rate(t)``.

    ``1 - (1 - q)^(1/12)``, so the twelve months of a policy year compound back to the
    annual rate exactly.  A rate of 1 is a certainty, not a rate: it is not twelfth-rooted
    but placed in the anniversary month, 1 where ``is_anniv(t)`` and 0 in the eleven months
    before it.
    """
    q = mort_rate(t)                                                 # noqa: F821
    if q >= 1.0:
        return 1.0 if is_anniv(t) else 0.0                           # noqa: F821
    return 1.0 - (1.0 - q) ** (1.0 / 12.0)


def lapse_rate_base(t):
    """The table **annual** lapse rate of the policy year containing month t.

    Read from the product's *lapse_table.csv* at ``policy_year(t)``, holding the table's
    last row for later policy years, so the twelve months of a year share one rate.
    """
    tbl = data.lapse_table()                                         # noqa: F821
    return float(tbl.at[min(policy_year(t), int(tbl.index.max())),  # noqa: F821
                        "lapse_rate"])


def lapse_factor(t):
    """The factor on the table lapse rate in month t; 1, neutral.

    A product that closes the lapse in part of the frame (0 there) or loads it overrides
    it; where it is 0 the table is not read.
    """
    return 1.0


def lapse_rate(t):
    """w(t): the **annual** lapse rate of the policy year containing month t.

    ``lapse_rate_base(t) x lapse_factor(t)``, and 0 without reading the table where the
    factor is 0.  The annual rate; ``lapse_rate_mth`` is the monthly rate the recursion
    applies.
    """
    f = lapse_factor(t)                                              # noqa: F821
    if f == 0.0:
        return 0.0
    return lapse_rate_base(t) * f                                    # noqa: F821


def lapse_rate_mth(t):
    """The **monthly** lapse rate applied in month t, the geometric twelfth of ``lapse_rate(t)``.

    ``1 - (1 - w)^(1/12)``, as :func:`mort_rate_mth`: twelve months compound back to the
    annual rate, and an annual rate of 1, a dated contractual act rather than a rate, falls
    whole in the anniversary month, 1 where ``is_anniv(t)`` and 0 before it.
    """
    w = lapse_rate(t)                                                # noqa: F821
    if w >= 1.0:
        return 1.0 if is_anniv(t) else 0.0                           # noqa: F821
    return 1.0 - (1.0 - w) ** (1.0 / 12.0)


def pols_if(t):
    """l(t): the policies in force at the **start** of month t, the weight on that month's row.

    ``pols_if_init()`` at ``t_start()``, then
    ``l(t) = l(t-1) - pols_death(t-1) - pols_lapse(t-1) - pols_maturity(t-1)``, the exits of
    the month before subtracted; 0 outside ``t_start() .. proj_len()``.  ``pols_if(proj_len())``
    is the state one past the last month: every exit lands inside the frame, so it is 0
    exactly where the survivors leave as maturities.
    """
    if t < t_start() or t > proj_len():                              # noqa: F821
        return 0.0
    if t == t_start():                                               # noqa: F821
        return pols_if_init()
    return (pols_if(t - 1) - pols_death(t - 1) - pols_lapse(t - 1)
            - pols_maturity(t - 1))


def pols_if_at(t, timing):
    """The policy count at a point inside month t, in the order of the month's decrements.

    ``"BEF_DECR"``
        l(t), the start of the month before any decrement: :func:`pols_if`, the weight on
        that month's cash flows.

    ``"AFT_DEATH"``
        ``l(t) (1 - q^m(t))``, after the month's deaths: the population the later exits
        are taken from.

    ``"AFT_DECR"``
        l(t + 1), the end-of-month state after every exit, ``pols_if(t + 1)``.

    Raises ``ValueError`` for any other timing.
    """
    if timing == "BEF_DECR":
        return pols_if(t)                                            # noqa: F821
    if timing == "AFT_DEATH":
        return pols_if(t) * (1.0 - mort_rate_mth(t))                 # noqa: F821
    if timing == "AFT_DECR":
        return pols_if(t + 1)                                        # noqa: F821
    raise ValueError("invalid timing")


def pols_death(t):
    """l(t) q^m(t): the expected deaths in month t, ``pols_if(t) x mort_rate_mth(t)``.

    Taken first, at the end of the month, on the best-estimate monthly rate; the deceased
    have paid what fell due in advance at the start of the month.
    """
    return pols_if(t) * mort_rate_mth(t)                             # noqa: F821


def pols_lapse(t):
    """The expected lapses in month t, ``pols_if_at(t, "AFT_DEATH") x lapse_rate_mth(t)``.

    Taken from the survivors of the month's deaths, at the end of the month; zero where the
    lapse rate is zero.
    """
    return pols_if_at(t, "AFT_DEATH") * lapse_rate_mth(t)            # noqa: F821


def pols_maturity(t):
    """The policies whose term ends with the last projected month, ``t = proj_len() - 1``.

    There the survivors of both decrements, ``pols_if_at(t, "AFT_DEATH") x (1 -
    lapse_rate_mth(t))``, and 0 in every month before; where the lapse is closed in the
    final month, the factor is exactly 1.  The count whose cover ends at the scheduled end
    of the contract, whether or not anything is paid for it.
    """
    if t != proj_len() - 1:                                          # noqa: F821
        return 0.0
    return (pols_if_at(t, "AFT_DEATH")                               # noqa: F821
            * (1.0 - lapse_rate_mth(t)))                             # noqa: F821


def rechnungszins():
    """i: the contract's *Rechnungszins*, fixed at conclusion, from the model point.

    The rate used at conclusion applies for the whole term (§ 2 Abs. 2 DeckRV), so a book
    carries a stack of guarantee vintages and the rate is a model-point attribute.
    """
    return float(model_point()["rechnungszins"])                     # noqa: F821


def hoechstrechnungszins():
    """The statutory *Höchstrechnungszins* in force at ``issue_year()``, the contract's cap.

    Read from ``data.hoechstrechnungszins_table()`` by the band that covers the year of
    issue: the cap in force at conclusion stays with the contract for its whole term
    (§ 2 Abs. 2 DeckRV).  Raises ``ValueError`` where no band covers it.
    """
    tab = data.hoechstrechnungszins_table()                          # noqa: F821
    y = issue_year()                                                 # noqa: F821
    for year_from in tab.index:
        if int(year_from) <= y <= int(tab.loc[year_from, "year_to"]):
            return float(tab.loc[year_from, "max_rate"])
    raise ValueError("no Hoechstrechnungszins band covers issue_year")


def beitragssumme_prem():
    """The annual premium the *Beitragssumme* is struck on: the product's ``prem_gross_pp()``.

    Reads the product's level annual gross premium; a product without one inherits this
    cell unused.
    """
    return prem_gross_pp()                                           # noqa: F821


def beitragssumme_years():
    """The number of premium years the *Beitragssumme* counts, ``prem_term()``."""
    return prem_term()                                               # noqa: F821


def beitragssumme():
    """BS: the *Beitragssumme*, ``beitragssumme_prem() x beitragssumme_years()``.

    The total of the premiums payable over the agreed term, fixed at conclusion: the base
    of the § 4 DeckRV acquisition-cost cap and of the initial commission.
    """
    return beitragssumme_prem() * beitragssumme_years()              # noqa: F821


def zillmer_on():
    """1 where the acquisition cost is zillmered into the reserve; 1, the default."""
    return 1


def zillmer_amount():
    """The zillmered acquisition charge, ``zillmer_on() x alpha_rate() x beitragssumme()``.

    Reads the product's ``alpha_rate``, its *Zillmersatz* on the *Beitragssumme*; a product
    without one inherits this cell unused.
    """
    return zillmer_on() * alpha_rate() * beitragssumme()             # noqa: F821


def disc_factor_mth(t):
    """v^(t/12): the *Rechnungszins* discount factor to month t, ``(1 + i)^(-t/12)``.

    On a year start ``t = 12y`` the exponent is exactly ``-y``, so it equals
    ``disc_factor(y)`` there bit for bit.
    """
    return (1.0 + rechnungszins()) ** (-t / 12.0)                    # noqa: F821


def disc_factor(y):
    """v^y: the *Rechnungszins* discount factor to the start of policy year y, ``(1 + i)^(-y)``."""
    return (1.0 + rechnungszins()) ** -y                             # noqa: F821


def unisex_mix_male():
    """The male share of the unisex tariff blend, from the product's *param_table.csv*."""
    return float(data.param_table().at["unisex_mix_male", "value"])  # noqa: F821


def unisex_blend(q_m, q_f):
    """The unisex blend of a male and a female rate, ``w q_m + (1 - w) q_f``.

    ``w = unisex_mix_male()``: sex may not enter the premium of a contract concluded from
    21 December 2012, so a tariff rate is struck on the mixed basis.
    """
    w = unisex_mix_male()                                            # noqa: F821
    return w * q_m + (1.0 - w) * q_f


def mort_load_tariff(t):
    """The loading on the first-order base rate in month t: 1, neutral."""
    return 1.0


def mort_rate_tariff_base(t):
    """The first-order base rate in month t, ``mort_rate_tariff_at_age(age(t))``.

    Reads the product's ``mort_rate_tariff_at_age``, its first-order rate at an attained
    age; a product without one inherits this cell unused.
    """
    return mort_rate_tariff_at_age(age(t))                           # noqa: F821


def mort_rate_tariff(t):
    """The first-order (tariff) annual death rate in month t.

    ``mort_load_tariff(t) x mort_rate_tariff_base(t)``: the base rate at ``age(t)`` times
    its loading, 1 unless the product loads it.
    """
    return mort_load_tariff(t) * mort_rate_tariff_base(t)            # noqa: F821


def pols_tariff(y):
    """p1(y): the tariff survivorship entering policy year y, mortality only.

    ``p1(0) = 1`` and ``p1(y) = p1(y - 1) x (1 - q1(12 (y - 1)))`` on the first-order
    annual rate :func:`mort_rate_tariff`, read at the opening month of each policy year.
    It always starts at issue, also on an in-force point: the tariff was struck then.
    """
    if y <= 0:
        return 1.0
    return pols_tariff(y - 1) * (1.0 - mort_rate_tariff(12 * (y - 1)))  # noqa: F821


def tariff_annuity():
    """ae: the premium annuity-due over the paying term, ``sum v^y p1(y)``, ``y < prem_term()``.

    Equal to 1 where ``prem_term() = 1``, so a single premium falls out of the same
    equivalence.
    """
    return sum(disc_factor(y) * pols_tariff(y)                       # noqa: F821
               for y in range(prem_term()))                          # noqa: F821


def tariff_death_sum():
    """The death sum the tariff's death benefit is struck on, outside the sum; 1, neutral."""
    return 1.0


def tariff_death_load(y):
    """The loading on the first-order death rate of policy year y in the death leg; 1."""
    return 1.0


def tariff_schedule(y):
    """The sum insured of policy year y relative to the death sum; 1, a level sum."""
    return 1.0


def tariff_maturity_sum():
    """The survival benefit at the end of the term; 0, a pure death cover."""
    return 0.0


def tariff_death_pv():
    """The first-order present value at issue of the death benefit, per policy.

    ``tariff_death_sum() x sum v^(y+1) p1(y) load(y) q1(12 y) schedule(y)`` over
    ``y < proj_len_y()``: claims fall at the end of the policy year of death, and the
    annual rate and sum are read at that year's opening month.
    """
    return tariff_death_sum() * sum(                                 # noqa: F821
        disc_factor(y + 1) * pols_tariff(y) * tariff_death_load(y)   # noqa: F821
        * mort_rate_tariff(12 * y) * tariff_schedule(y)              # noqa: F821
        for y in range(proj_len_y()))                                # noqa: F821


def tariff_maturity_pv():
    """The first-order present value at issue of the survival benefit, ``SE v^n p1(n)``."""
    return (tariff_maturity_sum() * disc_factor(policy_term())       # noqa: F821
            * pols_tariff(policy_term()))                            # noqa: F821


def tariff_benefit_pv():
    """A: the first-order present value at issue of the benefits, death plus survival."""
    return tariff_death_pv() + tariff_maturity_pv()


def tariff_term_annuity():
    """The annuity-due over the cover term, ``sum v^y p1(y) schedule(y)``, ``y < proj_len_y()``.

    The base of a loading on the sum insured that runs for as long as there is a sum at
    risk, not only over the paying term.
    """
    return sum(disc_factor(y) * pols_tariff(y) * tariff_schedule(y)  # noqa: F821
               for y in range(proj_len_y()))                         # noqa: F821


def prem_net_level_pp():
    """The net level premium, ``tariff_benefit_pv() / tariff_annuity()``, before loadings.

    ``tariff_benefit_pv`` is the present value of the benefits on the tariff basis.  A
    pricing quantity, never a cash flow.
    """
    return tariff_benefit_pv() / tariff_annuity()                    # noqa: F821


def prem_inst_pp(t):
    """The premium collected per policy at the start of month t; 0, no premium.

    A product with a premium overrides it with its own per-policy amount, zero in a month
    in which nothing falls due.
    """
    return 0.0


def pols_prem(t):
    """The count the premium is collected from at the start of month t, ``pols_if(t)``.

    A product whose premium is paid by a part of the in-force only (a premium-paying ledger,
    a waiver of premium) overrides it.
    """
    return pols_if(t)                                                # noqa: F821


def premiums(t):
    """Premium income at the **start** of month t, an inflow: ``prem_inst_pp(t) x pols_prem(t)``.

    Not further multiplied by a survival factor: the decrements fall at the end of the
    month, so a policy that leaves in it has already paid what fell due at its start.
    """
    return prem_inst_pp(t) * pols_prem(t)                            # noqa: F821


def claim_kinds():
    """The benefit kinds of :func:`claims`, in the order of its total: death, lapse, maturity.

    A product with other kinds overrides the tuple; a kind outside death, lapse and maturity
    is computed by :func:`claims_other`.
    """
    return ("DEATH", "LAPSE", "MATURITY")


def benefit_death_pp(t):
    """What a death in month t pays per claim; 0, no death benefit."""
    return 0.0


def benefit_lapse_pp(t):
    """What a surrender in month t pays per lapsing policy; 0, no surrender value."""
    return 0.0


def benefit_maturity_pp(t):
    """What the end of the term pays per maturing policy in month t; 0, no survival benefit."""
    return 0.0


def claims_other(t, kind):
    """The outgo of a benefit kind other than death, lapse and maturity in month t.

    None in the core: raises ``ValueError`` for any kind.  A product with further kinds
    overrides it with their outgo and keeps the ``ValueError`` for an unknown kind.
    """
    raise ValueError("invalid kind")


def claims(t, kind=None):
    """Benefit outgo in month t, by kind; the total over ``claim_kinds()`` when kind is omitted.

    ``"DEATH"``
        ``benefit_death_pp(t) x pols_death(t)``.

    ``"LAPSE"``
        ``benefit_lapse_pp(t) x pols_lapse(t)``.

    ``"MATURITY"``
        ``benefit_maturity_pp(t) x pols_maturity(t)``.

    Every other kind is :func:`claims_other`, which raises ``ValueError`` for an unknown
    one.  A kind whose per-policy amount is 0 is exactly 0, a published zero rather than a
    missing column.
    """
    if kind is None:
        return sum(claims(t, k) for k in claim_kinds())              # noqa: F821
    if kind == "DEATH":
        return benefit_death_pp(t) * pols_death(t)                  # noqa: F821
    if kind == "LAPSE":
        return benefit_lapse_pp(t) * pols_lapse(t)                   # noqa: F821
    if kind == "MATURITY":
        return benefit_maturity_pp(t) * pols_maturity(t)             # noqa: F821
    return claims_other(t, kind)                                     # noqa: F821


def expenses_acq(t):
    """The acquisition expense in month t; 0, none."""
    return 0.0


def expenses_maint(t):
    """The maintenance (administration) expense in month t; 0, none."""
    return 0.0


def expenses_claim(t):
    """The claim handling (per-event) expense in month t; 0, none."""
    return 0.0


def expenses(t):
    """The insurer's own expense outgo in month t, **excluding commission**.

    ``expenses_acq(t) + expenses_maint(t) + expenses_claim(t)``: the acquisition expense,
    the maintenance expense on the policies in force and the expense on the month's claims.
    :func:`commissions` is a line of its own, and :func:`net_cf` subtracts each once.
    """
    return expenses_acq(t) + expenses_maint(t) + expenses_claim(t)   # noqa: F821


def comm_init_rate():
    """The initial commission as a rate on the *Beitragssumme*; 0, no initial commission."""
    return 0.0


def comm_init(t):
    """The initial commission (*Abschlussprovision*) in month t.

    ``comm_init_rate() x beitragssumme() x pols_if(t)`` in the frame's first month on a
    new-business point (``duration_init() == 0``), and 0 otherwise: on an in-force point it
    was paid at conclusion, before the frame opens.  0 without reading the *Beitragssumme*
    where the rate is 0.
    """
    rate = comm_init_rate()                                          # noqa: F821
    if rate == 0.0 or t != t_start() or duration_init() != 0:        # noqa: F821
        return 0.0
    return rate * beitragssumme() * pols_if(t)                       # noqa: F821


def comm_renew(t):
    """The renewal commission (*Bestandsprovision*) in month t; 0, none."""
    return 0.0


def commissions(t):
    """Commission outgo in month t, ``comm_init(t) + comm_renew(t)``.

    A line of its own beside :func:`expenses`, which excludes it; :func:`net_cf` subtracts
    each once.
    """
    return comm_init(t) + comm_renew(t)                              # noqa: F821


def income_other(t):
    """Income in month t beside the premium (a top-up, a subsidy); 0, none."""
    return 0.0


def annuity_outgo(t):
    """Annuity outgo in month t that is not a kind of :func:`claims`; 0, none."""
    return 0.0


def net_cf(t):
    """The net liability cash flow of month t, **income positive**.

    ``premiums(t) + income_other(t)``, less ``claims(t, kind)`` for each kind of
    ``claim_kinds()`` in turn, less ``annuity_outgo(t)``, ``expenses(t)`` and
    ``commissions(t)``: each outgo subtracted exactly once, the commission apart from the
    expenses.  The library-wide sign; :func:`liability_cf` publishes the same stream
    outgo-positive.
    """
    out = premiums(t) + income_other(t)                              # noqa: F821
    for kind in claim_kinds():                                       # noqa: F821
        out = out - claims(t, kind)                                  # noqa: F821
    return out - annuity_outgo(t) - expenses(t) - commissions(t)     # noqa: F821


def liability_cf(t):
    """The same stream as :func:`net_cf`, outgo positive: ``-net_cf(t)`` exactly.

    The orientation a valuation layer consumes: a best-estimate liability is
    ``sum v(t) liability_cf(t)`` over whatever discount curve it supplies.  Published beside
    :func:`net_cf` so the sign convention is verifiable in the frame rather than only in
    prose.
    """
    return -net_cf(t)                                                # noqa: F821


def roll_fwd_tol():
    """The tolerance the ``check_*`` identities close to, from *param_table.csv*.

    A float comparison tolerance, not an actuarial assumption: each check scales it by the
    magnitude of what it compares.  A product without the row raises ``KeyError``.
    """
    return float(data.param_table().at["roll_fwd_tol", "value"])     # noqa: F821


def result_cf_columns():
    """The columns of :func:`result_cf` in their order, as ``(label, cell)`` pairs.

    Each cell is a function of the month ``t``.  The default is the statement the core's own
    cells make: ``pols_if``, ``premiums``, one ``claims_<kind>`` column per kind of
    ``claim_kinds()`` in its order (the kind in lower case), ``expenses``, ``commissions``,
    ``net_cf`` and ``liability_cf``.  A product whose statement has other lines overrides the
    tuple; a column that is not a cell of ``t`` alone is a lambda of ``t``.
    """
    claim_columns = tuple(("claims_" + kind.lower(),
                           lambda t, kind=kind: claims(t, kind))     # noqa: F821
                          for kind in claim_kinds())                 # noqa: F821
    return (("pols_if", pols_if), ("premiums", premiums)            # noqa: F821
            ) + claim_columns + (
            ("expenses", expenses), ("commissions", commissions),    # noqa: F821
            ("net_cf", net_cf), ("liability_cf", liability_cf))      # noqa: F821


def result_cf():
    """The table of cash flows by policy month t, ``t_start() .. proj_len() - 1``.

    One column per pair of :func:`result_cf_columns`, in its order, each the cell evaluated
    at every month of the frame; ``pols_if`` is the start-of-month count, the weight on every
    cash flow of the same row.  The frame runs contiguously and stops: there is no
    ``t = proj_len()`` row.
    """
    ts = list(range(t_start(), proj_len()))                          # noqa: F821
    frame = pd.DataFrame(                                            # noqa: F821
        {label: [cell(t) for t in ts] for label, cell in result_cf_columns()},  # noqa: F821
        index=ts)
    frame.index.name = "t"
    return frame


def result_cf_counts():
    """The count columns of :func:`result_cf` taken at each year's start: ``pols_if``.

    :func:`result_cf_annual` takes them at the policy year's start rather than summing them.
    A product whose frame carries a further count overrides the tuple.
    """
    return ("pols_if",)


def result_cf_annual():
    """:func:`result_cf` summed into policy years, indexed by the 1-based ``policy_year``.

    A regrouping of the monthly frame and never a second projection: every cash flow column
    is the sum of its policy year's months, while each column of ``result_cf_counts()`` is
    the count at the year's **start** and stands first, in that order, which is the only
    reading under which a count and a flow can share a row.
    """
    df = result_cf()                                                 # noqa: F821
    years = pd.Series([duration(t) + 1 for t in df.index],           # noqa: F821
                      index=df.index, name="policy_year")
    counts = list(result_cf_counts())                                # noqa: F821
    out = df.drop(columns=counts).groupby(years).sum()
    for i, column in enumerate(counts):
        out.insert(i, column, df[column].groupby(years).first())
    return out
