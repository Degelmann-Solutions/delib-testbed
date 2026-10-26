# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The shared input cells; a product's ``Data`` inherits them as ``CoreData``.

Input files stay the product's own: the product's ``Data`` reads them relative to the
product's model folder.
"""

from modelx.serialize.jsonvalues import *

_formula = None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def input_dir():
    """The directory holding the product's input CSVs: its model folder's parent.

    Resolved at run time from where the product's model was read, so a core cell reads
    the product's own input files.
    """
    return _model.path.parent                                        # noqa: F821


def model_point_table():
    """The model point table, read from the product's ``model_point_file``, by ``point_id``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / model_point_file, index_col="point_id")        # noqa: F821


def param_table():
    """The product's scalar parameters by ``item``, read from its ``param_file``.

    Columns ``value`` and ``provenance``, and an optional ``unit``.  The values are read
    with pandas' default float parsing, which round-trips the decimal literals.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / param_file, index_col="item")                  # noqa: F821


def mort_table_index():
    """The index columns of the mortality table: ``sex`` and attained ``age``."""
    return ["sex", "age"]


def mort_table():
    """The annual death rates, read from ``mort_file`` by ``mort_table_index()``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / mort_file, index_col=mort_table_index())       # noqa: F821


def lapse_table_index():
    """The index column of the lapse table: the **1-based** ``policy_year``."""
    return "policy_year"


def lapse_table():
    """The annual lapse rates, read from ``lapse_file`` by ``lapse_table_index()``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / lapse_file, index_col=lapse_table_index())     # noqa: F821


def rentenfaktor_table_index():
    """The index columns of the *Rentenfaktor* table: ``rf_scenario_id`` and ``age``."""
    return ["rf_scenario_id", "age"]


def rentenfaktor_table():
    """The *Rentenfaktor*, from ``rentenfaktor_file`` by ``rentenfaktor_table_index()``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / rentenfaktor_file,                             # noqa: F821
        index_col=rentenfaktor_table_index())


def freq_loading_table():
    """The *Ratenzahlungszuschlag* by ``prem_freq``, from ``freq_loading_file``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / freq_loading_file, index_col="prem_freq")      # noqa: F821


def surplus_table_index():
    """The index columns of the surplus table: ``scenario_id`` and the 0-based ``t``."""
    return ["scenario_id", "t"]


def surplus_table():
    """The declared surplus path, read from ``surplus_file`` by ``surplus_table_index()``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / surplus_file, index_col=surplus_table_index())  # noqa: F821


def charge_table_index():
    """The index column of the charge table: ``charge_id``."""
    return "charge_id"


def charge_table():
    """The tariff charges, read from ``charge_file`` by ``charge_table_index()``."""
    return pd.read_csv(                                              # noqa: F821
        input_dir() / charge_file, index_col=charge_table_index())   # noqa: F821
