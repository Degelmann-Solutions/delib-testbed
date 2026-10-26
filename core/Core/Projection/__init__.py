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


def prem_freq():
    """The payment frequency, a key into the product's *freq_loading_table.csv*.

    Raises ``ValueError`` for a frequency the table has no row for.
    """
    v = model_point()["prem_freq"]                                   # noqa: F821
    if v not in data.freq_loading_table().index:                     # noqa: F821
        raise ValueError("no frequency loading for prem_freq " + str(v))
    return v


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


def rechnungszins():
    """i: the contract's *Rechnungszins*, fixed at conclusion, from the model point.

    The rate used at conclusion applies for the whole term (§ 2 Abs. 2 DeckRV), so a book
    carries a stack of guarantee vintages and the rate is a model-point attribute.
    """
    return float(model_point()["rechnungszins"])                     # noqa: F821


def disc_factor_mth(t):
    """v^(t/12): the *Rechnungszins* discount factor to month t, ``(1 + i)^(-t/12)``.

    On a year start ``t = 12y`` the exponent is exactly ``-y``, so it equals
    ``disc_factor(y)`` there bit for bit.
    """
    return (1.0 + rechnungszins()) ** (-t / 12.0)                    # noqa: F821


def disc_factor(y):
    """v^y: the *Rechnungszins* discount factor to the start of policy year y, ``(1 + i)^(-y)``."""
    return (1.0 + rechnungszins()) ** -y                             # noqa: F821


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


def prem_net_level_pp():
    """The net level premium, ``tariff_benefit_pv() / tariff_annuity()``, before loadings.

    Reads the product's ``tariff_benefit_pv``, the present value of its benefits on the
    tariff basis; a product without one inherits this cell unused.  A pricing quantity,
    never a cash flow.
    """
    return tariff_benefit_pv() / tariff_annuity()                    # noqa: F821
