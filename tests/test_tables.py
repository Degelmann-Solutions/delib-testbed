"""The table factory (``docs/core.md``, "The table factory").

The loader's part, on scratch copies of RLV:

- Every shipped product reads the table parameter file ``param_tables.csv`` beside the core
  file as its layer ``tables``, second of the layers; the shipped file holds the header alone,
  so the layer is empty, and a copy without the file raises.
- A fixture item of a copy's ``param_tables.csv`` is read through ``param`` like any other.
- An item named ``<role>_table`` holds a table name and is loaded as a ``str``, in the
  tariff-type and the tariff file; a number or a value of another form raises, and a name
  as the value of any other item is still no number.
- An item of the tables layer in the tariff-type or the tariff file raises, naming both
  files, and so does an item of the core file in the tables file (the core lock).
"""
from __future__ import annotations

from pathlib import Path

import modelx as mx
import pytest

from test_core import CORE_MODEL, MODELS, PRODUCTS_DIR, _add_params, _loader_error, product_copy

RLV = "risikolebensversicherung"
TABLES_FILE = "param_tables.csv"


def tables_file(folder: Path, product: str = RLV) -> Path:
    """The table parameter file of a scratch copy, a real file beside its core file."""
    path = folder / MODELS[product] / "CoreData" / TABLES_FILE
    assert path.is_file() and not path.is_symlink()
    return path


@pytest.fixture(scope="module")
def product_models():
    """Every product's modelx model, read once for this module and closed afterwards."""
    models = {}

    def read(product):
        if product not in models:
            models[product] = mx.read_model(PRODUCTS_DIR / product / MODELS[product],
                                            name=f"Tables_{MODELS[product]}")
        return models[product]

    yield read
    for model in models.values():
        model.close()


def test_the_shipped_tables_file_holds_the_header_alone():
    path = CORE_MODEL / "Data" / TABLES_FILE
    assert path.read_text(encoding="utf-8") == "item,value,basis,provenance\n"


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_tables_layer_is_the_second_layer_and_empty(product, product_models):
    data = product_models(product).Data
    assert data.param_tables_path() == data.model.path / "CoreData" / TABLES_FILE
    assert data.param_tables_path().is_file()
    assert list(data.param_paths()) == ["core", "tables", "tariff_type"]
    assert data.param_paths()["tables"] == data.param_tables_path()
    assert data.param_rows()["tables"] == []
    assert list(data.param_layers()) == ["core", "tables", "tariff_type"]
    assert data.param_layers()["tables"] == {}


def test_param_without_the_tables_file_raises(tmp_path):
    folder = product_copy(tmp_path, RLV)
    path = tables_file(folder)
    path.unlink()
    message = _loader_error(folder / MODELS[RLV], "NoTablesProbe")
    assert f"parameter file {path} cannot be read" in message


def test_param_reads_an_item_of_the_tables_layer(tmp_path):
    folder = product_copy(tmp_path, RLV)
    shipped = (CORE_MODEL / "Data" / TABLES_FILE).read_text(encoding="utf-8")
    _add_params(tables_file(folder), {"fixture_end_age": "121", "fixture_m_a": "0.0005"})
    copy = mx.read_model(folder / MODELS[RLV], name="TablesItemProbe")
    try:
        data = copy.Data
        assert data.param_layers()["tables"] == {"fixture_end_age": 121, "fixture_m_a": 0.0005}
        assert data.param("fixture_end_age") == 121
        assert type(data.param("fixture_end_age")) is int
        assert data.param("fixture_m_a") == 0.0005
        assert data.param("check_tol") == 1e-08
    finally:
        copy.close()
    assert (CORE_MODEL / "Data" / TABLES_FILE).read_text(encoding="utf-8") == shipped


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_a_table_choice_is_loaded_as_a_name(tmp_path, file):
    folder = product_copy(tmp_path, RLV)
    _add_params(folder / file, {"mort_table": "dav_x_proxy", "probe2_table": " t2 "})
    copy = mx.read_model(folder / MODELS[RLV], name="ChoiceProbe")
    try:
        data = copy.Data
        assert data.param("mort_table") == "dav_x_proxy"
        assert type(data.param("mort_table")) is str
        assert data.param("probe2_table") == "t2"
        layer = "tariff" if file == "param_tariff.csv" else "tariff_type"
        assert data.param_layers()[layer]["mort_table"] == "dav_x_proxy"
    finally:
        copy.close()


@pytest.mark.parametrize(("text", "name"), [
    ("3", "IntChoiceProbe"),
    ("0.5", "FloatChoiceProbe"),
    ("1e3", "ExponentChoiceProbe"),
    ("Dav_x_proxy", "UpperChoiceProbe"),
    ("dav_X_proxy", "InnerUpperChoiceProbe"),
    ("_dav_x", "UnderscoreFirstChoiceProbe"),
    ("dav-x", "HyphenChoiceProbe"),
    ("dav x", "SpaceChoiceProbe"),
    ("däv_x", "UmlautChoiceProbe"),
])
def test_a_table_choice_that_is_no_name_raises(tmp_path, text, name):
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    _add_params(path, {"mort_table": text})
    message = _loader_error(folder / MODELS[RLV], name)
    assert f"parameter 'mort_table' has the value {text!r} in {path}, no table name" in message


def test_an_empty_table_choice_has_no_value(tmp_path):
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    _add_params(path, {"mort_table": ""})
    message = _loader_error(folder / MODELS[RLV], "EmptyChoiceProbe")
    assert f"parameter 'mort_table' has no value in {path}" in message


@pytest.mark.parametrize("item", ["mort_table_name", "table", "probe_tables"])
def test_a_name_is_no_number_for_any_other_item(tmp_path, item):
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    _add_params(path, {item: "dav_x_proxy"})
    message = _loader_error(folder / MODELS[RLV], "NameValueProbe")
    assert f"parameter {item!r} has the value 'dav_x_proxy' in {path}, no number" in message


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_param_rejects_a_tables_item_in_a_product_file(tmp_path, file):
    folder = product_copy(tmp_path, RLV)
    tables = tables_file(folder)
    _add_params(tables, {"fixture_end_age": "121"})
    _add_params(folder / file, {"fixture_end_age": "110"})
    message = _loader_error(folder / MODELS[RLV], "TablesLockProbe")
    assert "'fixture_end_age' is a tables item of" in message
    assert str(tables) in message and str(folder / file) in message


def test_param_rejects_a_core_item_in_the_tables_file(tmp_path):
    folder = product_copy(tmp_path, RLV)
    tables = tables_file(folder)
    _add_params(tables, {"check_tol": "1e-9"})
    message = _loader_error(folder / MODELS[RLV], "CoreInTablesProbe")
    assert "'check_tol' is a core item of" in message
    assert str(tables.with_name("param_core.csv")) in message and str(tables) in message


def test_param_rejects_an_item_twice_in_the_tables_file(tmp_path):
    folder = product_copy(tmp_path, RLV)
    tables = tables_file(folder)
    _add_params(tables, {"fixture_end_age": "121"})
    _add_params(tables, {"fixture_end_age": "121"})
    message = _loader_error(folder / MODELS[RLV], "TablesTwiceProbe")
    assert f"'fixture_end_age' stands twice in {tables}" in message
