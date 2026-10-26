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


def issue_age():
    """The age at issue of the selected model point, from its ``issue_age`` column."""
    return int(model_point()["issue_age"])                           # noqa: F821


def sex():
    """The sex of the insured life, ``M`` or ``F``, from the model point."""
    v = model_point()["sex"]                                         # noqa: F821
    if v not in ("M", "F"):
        raise ValueError("invalid sex")
    return v


def smoker():
    """The smoker status of the insured life, ``N`` or ``S``, from the model point."""
    v = model_point()["smoker"]                                      # noqa: F821
    if v not in ("N", "S"):
        raise ValueError("invalid smoker")
    return v


def policy_term():
    """The policy term in years, from the model point."""
    return int(model_point()["policy_term"])                         # noqa: F821


def prem_term():
    """The premium payment term in whole years, from the model point."""
    return int(model_point()["prem_term"])                           # noqa: F821


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


def k_start():
    """The first projected policy year, ``duration_init()``."""
    return duration_init()                                           # noqa: F821


def t_start():
    """The first projected month, ``12 x k_start()``; ``t`` counts months from issue."""
    return 12 * k_start()                                            # noqa: F821


def proj_year(t):
    """The 0-based projection year month t falls in, ``t // 12``."""
    return t // 12


def duration_mth(t):
    """The completed policy months at the start of month t: ``t``, counted from issue."""
    return t


def duration(t):
    """The completed policy years at the start of month t, ``duration_mth(t) // 12``."""
    return duration_mth(t) // 12                                     # noqa: F821


def duration_y(k):
    """The completed policy years at the start of projection year k, ``duration_init() + k``."""
    return duration_init() + k                                       # noqa: F821


def policy_year(t):
    """The contractual 1-based policy year containing month t, ``duration(t) + 1``."""
    return duration(t) + 1                                           # noqa: F821


def age_y(k):
    """The attained age at the start of policy year k, ``issue_age() + k``."""
    return issue_age() + k                                           # noqa: F821


def age(t):
    """The attained age in month t, ``age_y(duration(t))``, stepping on the anniversary."""
    return age_y(duration(t))                                        # noqa: F821


def proj_len_y():
    """The number of projected policy years, the policy term."""
    return policy_term()                                             # noqa: F821


def proj_len():
    """The number of projected months, ``12 x proj_len_y()``; the frame's exclusive end."""
    return 12 * proj_len_y()                                         # noqa: F821


def calendar_year_y(k):
    """The calendar year of policy year k, ``issue_year() + k``."""
    return issue_year() + k                                          # noqa: F821


def calendar_year(t):
    """The calendar year of month t, ``calendar_year_y(duration(t))``."""
    return calendar_year_y(duration(t))                              # noqa: F821


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
