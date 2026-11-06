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


def param_core_path():
    """The core parameter file, ``param_core.csv`` beside the core's loaders.

    Found through the product's ``CoreData`` space folder, so a scratch copy of a product
    folder, which copies that folder with the file in it, reads its own copy.
    """
    return _model.path / "CoreData" / "param_core.csv"               # noqa: F821


def param_tariff_path():
    """The optional tariff parameter file, ``param_tariff.csv`` in the product folder."""
    return input_dir() / "param_tariff.csv"


def param_layers():
    """The parameter layers of the tariff: ``{layer: {item: value}}``, built once per model.

    The layers in turn, ``"core"`` from ``param_core_path()``, ``"tariff_type"`` from the
    tariff-type file ``param_file`` and, where it exists, ``"tariff"`` from the tariff file
    ``param_tariff_path()``; each file has the columns ``item``, ``value``, ``basis`` and
    ``provenance``.  A value whose text is an integer literal is a Python ``int``, any other a
    Python ``float``, the value the same literal has in Python.

    The loader checks the files as it reads them and raises ``ValueError`` naming the item
    and the file or files: an item standing twice in one file, an item of the core file in a
    product file (the core lock), an item standing in both product files (uniqueness).
    """
    paths = {"core": param_core_path(),
             "tariff_type": input_dir() / param_file}                 # noqa: F821
    if param_tariff_path().is_file():
        paths["tariff"] = param_tariff_path()
    layers = {}
    seen = {}
    for layer, path in paths.items():
        table = pd.read_csv(path, dtype=str, keep_default_na=False)  # noqa: F821
        values = {}
        for item, text in zip(table["item"], table["value"]):
            if item in values:
                raise ValueError(f"parameter {item!r} stands twice in {path}")
            if item in seen:
                first_layer, first_path = seen[item]
                if first_layer == "core":
                    raise ValueError(
                        f"parameter {item!r} is a core item of {first_path}; the product"
                        f" file {path} must not hold it")
                raise ValueError(
                    f"parameter {item!r} stands in two layers: {first_path} and {path}")
            text = text.strip()
            values[item] = int(text) if text.lstrip("+-").isdigit() else float(text)
        for item in values:
            seen[item] = (layer, path)
        layers[layer] = values
    return layers


def param_dict():
    """Every parameter of the tariff by ``item``: ``{item: value}``, built once per model.

    The layers of ``param_layers()`` merged in their order; the loader has checked that they
    are disjoint.
    """
    values = {}
    for layer in param_layers().values():
        values.update(layer)
    return values


def param(item):
    """The parameter ``item`` from ``param_dict()``; an unknown item raises ``KeyError``."""
    return param_dict()[item]


def param_indirect():
    """The cells that read parameters other than by a literal ``param("<item>")``.

    ``{cell: (item, ...)}``, each such cell with the items it reads; empty in the core.  A
    product (or a table factory reading its items by a computed name) overrides it.  Only
    the static usage scan ``core/param_usage.py`` reads it, never a run.
    """
    return {}


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


def prem_freq_table():
    """The premium payment frequencies by ``prem_freq``, from ``prem_freq_file``.

    One row per frequency the product allows, with its ``instalments`` a year and, where the
    product charges one, its *Ratenzahlungszuschlag* ``prem_freq_load``.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / prem_freq_file, index_col="prem_freq")         # noqa: F821


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


def prem_freq_table_dict():
    """The premium frequency table as a dict by column: ``{column: {prem_freq: value}}``.

    ``Projection.prem_freq`` checks the frequency against its keys,
    ``prem_freq_load`` and ``instalments`` read the columns of their names.
    """
    return prem_freq_table().to_dict()


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
