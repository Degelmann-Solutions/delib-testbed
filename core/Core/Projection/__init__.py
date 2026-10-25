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
