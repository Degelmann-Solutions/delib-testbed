# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The shared input cells; a product's ``Data`` inherits them as ``CoreData``.

Input files stay the product's own: the product's ``Data`` reads them relative to the
product's model folder.  Each reader has a dict cell ``<reader>_dict()`` beside it, the
same table as plain dicts built once per model, which the projection's lookups read.
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

    Columns ``value``, ``basis`` and ``provenance``, and an optional ``unit``: the
    product's tariff-type file ``param_tariff_type.csv`` (``docs/core.md``, "The parameter
    files").  The values are read with pandas' default float parsing, which round-trips
    the decimal literals.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / param_file, index_col="item")                  # noqa: F821


def param_core_path():
    """The core parameter file, ``param_core.csv`` beside the core's loaders.

    Found through the product's ``CoreData`` space folder, so a scratch copy of a product
    folder, which copies that folder with the file in it, reads its own copy.
    """
    return _model.path / "CoreData" / "param_core.csv"               # noqa: F821


def param_tariff_path():
    """The optional tariff parameter file, ``param_tariff.csv`` in the product folder."""
    return input_dir() / "param_tariff.csv"


def param_dict():
    """Every parameter of the tariff by ``item``: ``{item: value}``, built once per model.

    The layers are read in turn, the core file ``param_core_path()``, the tariff-type file
    ``param_file`` and, where it exists, the tariff file ``param_tariff_path()``; each has
    the columns ``item``, ``value``, ``basis`` and ``provenance``, and the layers are
    disjoint.  A value whose text is an integer literal is a Python ``int``, any other a
    Python ``float``, the value the same literal has in Python.
    """
    paths = [param_core_path(), input_dir() / param_file]            # noqa: F821
    if param_tariff_path().is_file():
        paths.append(param_tariff_path())
    values = {}
    for path in paths:
        table = pd.read_csv(path, dtype=str, keep_default_na=False)  # noqa: F821
        for item, text in zip(table["item"], table["value"]):
            text = text.strip()
            values[item] = int(text) if text.lstrip("+-").isdigit() else float(text)
    return values


def param(item):
    """The parameter ``item`` from ``param_dict()``; an unknown item raises ``KeyError``."""
    return param_dict()[item]


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


def hoechstrechnungszins_table():
    """The statutory *Höchstrechnungszins* history by band, from ``hoechstrechnungszins_file``.

    Indexed by ``year_from``, with ``year_to`` closing each band and ``max_rate`` the cap
    in force.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / hoechstrechnungszins_file, index_col="year_from")   # noqa: F821


def model_point_table_dict():
    """The model point table as a dict by row: ``{point_id: {column: value}}``.

    Built once per model from ``model_point_table()``; ``Projection.model_point`` returns
    the selected point's row from it.  The values are the table's own, boxed as Python
    ``int``, ``float``, ``bool`` and ``str`` with the same bits.
    """
    return model_point_table().to_dict("index")


def param_table_dict():
    """The parameter table as a dict by column: ``{column: {item: value}}``.

    Built once per model from ``param_table()``.  No cell reads it: every parameter is
    read through ``param(item)``.
    """
    return param_table().to_dict()


def mort_table_dict():
    """The mortality table as a dict by column: ``{column: {key: rate}}``.

    Keyed as ``mort_table()`` is indexed, by the tuple of ``mort_table_index()`` (a scalar
    for a single index column); the products' lookups read the column they use.
    """
    return mort_table().to_dict()


def lapse_table_dict():
    """The lapse table as a dict by column: ``{column: {policy_year: rate}}``.

    Keyed as ``lapse_table()`` is indexed by ``lapse_table_index()``, the policy year
    **1-based** by default; ``Projection.lapse_rate_base`` reads its ``lapse_rate`` column.
    """
    return lapse_table().to_dict()


def rentenfaktor_table_dict():
    """The *Rentenfaktor* table as a dict by column: ``{column: {key: value}}``.

    Keyed as ``rentenfaktor_table()`` is indexed, by the tuple of
    ``rentenfaktor_table_index()``; the products' lookups read it.
    """
    return rentenfaktor_table().to_dict()


def freq_loading_table_dict():
    """The frequency loading table as a dict by column: ``{column: {prem_freq: value}}``.

    ``Projection.prem_freq`` checks the frequency against its keys,
    ``prem_freq_load`` and ``instalments`` read the columns of their names.
    """
    return freq_loading_table().to_dict()


def surplus_table_dict():
    """The surplus table as a dict by column: ``{column: {key: value}}``.

    Keyed as ``surplus_table()`` is indexed, by the tuple of ``surplus_table_index()``;
    the products' lookups read it.
    """
    return surplus_table().to_dict()


def charge_table_dict():
    """The charge table as a dict by column: ``{column: {key: value}}``.

    Keyed as ``charge_table()`` is indexed by ``charge_table_index()``; the products'
    lookups read it.
    """
    return charge_table().to_dict()


def hoechstrechnungszins_table_dict():
    """The *Höchstrechnungszins* bands as a dict by column: ``{column: {year_from: value}}``.

    The keys in the file's order; ``Projection.hoechstrechnungszins`` tries the bands in
    that order on the ``year_to`` and ``max_rate`` columns.
    """
    return hoechstrechnungszins_table().to_dict()
