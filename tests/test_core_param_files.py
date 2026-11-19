"""The parameter files and their loader in the core's ``Data`` (``docs/core.md``, "The
parameter files").

- ``param(item)`` reads RLV's tariff-type file without a tariff file,
  ``expense_claim_pp_once`` among it and no longer a Reference of its ``Projection``,
  keeps an integer literal ``int``, reads a fixture core item and a tariff item in a scratch
  copy, and raises on an unknown item and on a missing core file; it equals the
  file's value of every product's every item, and the core's former readers
  ``param_table()`` and ``param_table_dict()`` are gone with every read of them; every
  product's ``param_file`` is its ``param_tariff_type.csv`` with the layer columns, and no
  ``param_table.csv`` is left.
- An item named in several parameter files has one type in all of them, every row's
  ``basis`` is ``source`` or ``Setzung``, and no product document calls a core item a row of
  the tariff-type file.
- Every product's ``param_layers()`` holds each item once and merges into ``param_dict()``;
  the loader raises ``ValueError`` on an item in two layers, twice in one file, and on a core
  item in the tariff-type or the tariff file, on a value that is no finite number, on an
  item that is empty or padded with whitespace, on a file with other columns and on a row
  wider than the header.
- A scratch copy with an item of the cost table also in the tariff-type or the tariff file
  raises ``ValueError`` naming the item and both files.

The layer files are read and rewritten as the loader reads them, as text
(``tests/helpers.py``: ``read_layer``, ``add_layer_rows``, ``drop_layer_rows``).
"""
from __future__ import annotations

import re

import modelx as mx
import pytest

from helpers import (CORE_DIR, CORE_MODEL, LAYER_FILES, MODELS, PRODUCTS_DIR, ROOT,
                     add_layer_rows, loader_error, product_copy, read_layer)


def test_param_reads_the_tariff_type_layer(product_models):
    data = product_models("risikolebensversicherung").Data
    assert data.param._is_derived() and data.param_dict._is_derived()
    assert not data.param_tariff_path().exists()
    assert data.param_core_path() == data.model.path / "CoreData" / "param_core.csv"
    assert data.param_core_path().is_file()
    for item in ("expense_claim_pp_once", "unisex_mix_male"):
        value = data.param(item)
        text = read_layer(PRODUCTS_DIR / "risikolebensversicherung"
                          / "param_tariff_type.csv").set_index("item").at[item, "value"]
        assert type(value) is float and value == float(text), item


PARAM_TABLE_RE = re.compile(r"(?<!\w)param_table(_dict)?\(")


def test_no_param_table_reader_remains(product_models):
    """Every parameter is read through ``param("<item>")``; the core's former readers
    ``param_table()`` and ``param_table_dict()`` are gone, and no source names them."""
    data = product_models("risikolebensversicherung").Data
    assert "param_table" not in data.cells and "param_table_dict" not in data.cells
    sources = sorted(p for folder in (CORE_DIR, PRODUCTS_DIR) for p in folder.rglob("*.py")
                     if "__pycache__" not in p.parts)
    assert sources
    hits = []
    for path in sources:
        text = path.read_text(encoding="utf-8")
        for match in PARAM_TABLE_RE.finditer(text):
            number = text.count("\n", 0, match.start()) + 1
            hits.append(f"{path.relative_to(ROOT)}:{number}")
    assert not hits, hits


@pytest.mark.parametrize("product", sorted(MODELS))
def test_param_equals_the_file_value(product, product_models):
    """``param(item)`` is the number every item of the tariff-type file writes, the file read
    as text; a table choice is the name as written."""
    data = product_models(product).Data
    values = read_layer(PRODUCTS_DIR / product / "param_tariff_type.csv").set_index(
        "item")["value"].to_dict()
    assert values
    for item, value in values.items():
        expected = value if item.endswith("_table") else float(value)
        assert data.param(item) == expected, item


@pytest.mark.parametrize("product, omega", [("klassische_rentenversicherung", 121),
                                             ("pflegerentenversicherung", 110),
                                             ("sofortrente", 121)])
def test_omega_age_is_an_int(product, omega, product_models):
    """``omega_age`` is an integer, so ``param`` gives an ``int``; so does Pflege's
    ``beitragssumme_cap_age`` (``85``). RV, Sofort and Pflege read it off their tables
    through the core's ``omega_age()``, the items ``dav2004r_proxy_end_age`` and
    ``pflege_aktive_proxy_end_age``, integers as the item ``omega_age`` was."""
    model = product_models(product)
    item_name = {"klassische_rentenversicherung": "dav2004r_proxy_end_age",
                 "sofortrente": "dav2004r_proxy_end_age",
                 "pflegerentenversicherung": "pflege_aktive_proxy_end_age"}[product]
    assert type(model.Data.param(item_name)) is int
    item = model.Projection[model.Data.model_point_table().index[0]]
    assert item.omega_age() == omega and type(item.omega_age()) is int
    if product == "pflegerentenversicherung":
        assert model.Data.param("beitragssumme_cap_age") == 85
        assert type(model.Data.param("beitragssumme_cap_age")) is int
        assert type(item.beitragssumme_years()) is int


def test_an_item_of_several_files_has_one_type():
    """An item named in several parameter files is one quantity: every file writes its
    value as the same type, an integer literal everywhere or a decimal one everywhere."""
    files = sorted(PRODUCTS_DIR.glob("*/param_tariff_type.csv"))
    files.append(CORE_MODEL / "Data" / "param_core.csv")
    types = {}
    for path in files:
        for item, text in read_layer(path)[["item", "value"]].itertuples(index=False):
            kind = "int" if text.strip().lstrip("+-").isdigit() else "float"
            types.setdefault(item, {}).setdefault(kind, []).append(path.parent.name)
    mixed = {item: kinds for item, kinds in types.items() if len(kinds) > 1}
    assert not mixed, mixed


def test_basis_is_source_or_setzung():
    """Every row of every parameter file has ``basis`` ``source`` or ``Setzung``; since entry 12
    of epic-parameter-files aligned the last values, no row is left empty."""
    files = [path for name in LAYER_FILES for path in sorted(PRODUCTS_DIR.glob(f"*/{name}"))]
    files.append(CORE_MODEL / "Data" / "param_core.csv")
    for path in files:
        table = read_layer(path)
        wrong = table.loc[~table["basis"].isin(["source", "Setzung"]), "item"].tolist()
        assert not wrong, (path, wrong)


def test_no_product_doc_calls_a_core_item_a_row_of_the_tariff_type_file():
    """A core item, a row of ``core/Core/Data/param_core.csv``, is no row of a product's
    ``param_tariff_type.csv``: no product ``.md`` file names one, in backticks, within the same table
    cell and the 80 characters before "a row of `param_tariff_type.csv`" (or "rows of", or
    "the tariff-type file")."""
    core_items = read_layer(CORE_MODEL / "Data" / "param_core.csv")["item"].tolist()
    phrase = re.compile(r"rows? of (`param_tariff_type\.csv`|the tariff-type file)")
    docs = sorted(PRODUCTS_DIR.glob("*/*.md"))
    assert len(docs) >= 40, docs
    found = []
    for path in docs:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in phrase.finditer(line):
                before = line[max(0, match.start() - 80):match.start()].rsplit("|", 1)[-1]
                for item in core_items:
                    if re.search(rf"`{re.escape(item)}\b", before):
                        found.append((str(path.relative_to(PRODUCTS_DIR)), number, item))
    assert not found, found


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_product_reads_its_tariff_type_file(product, product_models):
    """``param_file`` is ``param_tariff_type.csv``, in the layer columns, and no
    ``param_table.csv`` is left."""
    assert product_models(product).Data.param_file == "param_tariff_type.csv"
    folder = PRODUCTS_DIR / product
    assert not (folder / "param_table.csv").exists()
    header = (folder / "param_tariff_type.csv").read_text(encoding="utf-8").splitlines()[0]
    assert header == "item,value,basis,provenance"


def test_rlv_claim_expense_is_a_tariff_type_row(product_models):
    model = product_models("risikolebensversicherung")
    data = model.Data
    assert data.param_file == "param_tariff_type.csv"
    value = data.param("expense_claim_pp_once")
    assert type(value) is float and value == 250.0
    assert "claim_expense" not in model.Projection.refs
    assert "expense_claim_pp_once" not in model.Projection.refs
    item = model.Projection[model.Data.model_point_table().index[0]]
    for t in range(item.t_start(), item.t_start() + 24):
        assert item.expenses_claim(t) == 250.0 * item.pols_death(t), t


def test_param_keeps_an_integer_literal_int(tmp_path, product_models):
    param_file = product_models("risikolebensversicherung").Data.param_file
    folder = product_copy(tmp_path, "risikolebensversicherung")
    add_layer_rows(folder / param_file,
                   {"probe_int": "3", "probe_neg": "-2", "probe_float": "3.0",
                    "probe_pad": " 3 "})
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="IntProbe")
    try:
        data = copy.Data
        assert data.param("probe_int") == 3 and type(data.param("probe_int")) is int
        assert data.param("probe_neg") == -2 and type(data.param("probe_neg")) is int
        assert type(data.param("probe_float")) is float
        assert data.param("probe_pad") == 3 and type(data.param("probe_pad")) is int
    finally:
        copy.close()


def test_param_reads_a_core_item_and_a_tariff_item(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    model_dir = folder / MODELS["risikolebensversicherung"]
    core_file = model_dir / "CoreData" / "param_core.csv"
    assert not core_file.is_symlink()
    shipped = (CORE_MODEL / "Data" / "param_core.csv").read_text(encoding="utf-8")
    add_layer_rows(core_file, {"probe_core": "0.125"})
    add_layer_rows(folder / "param_tariff.csv", {"probe_tariff": "7"})
    copy = mx.read_model(model_dir, name="CoreItemProbe")
    try:
        assert copy.Data.param("probe_core") == 0.125
        assert copy.Data.param("probe_tariff") == 7
        assert copy.Data.param("check_tol") == 1e-08
    finally:
        copy.close()
    assert (CORE_MODEL / "Data" / "param_core.csv").read_text(encoding="utf-8") == shipped


def test_param_rejects_an_unknown_item(product_models):
    data = product_models("risikolebensversicherung").Data
    with pytest.raises(Exception, match="nope") as raised:
        data.param("nope")
    assert "KeyError: 'nope'" in str(raised.value) or isinstance(raised.value, KeyError)


def test_param_without_the_core_file_raises(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    model_dir = folder / MODELS["risikolebensversicherung"]
    (model_dir / "CoreData" / "param_core.csv").unlink()
    copy = mx.read_model(model_dir, name="NoCoreProbe")
    try:
        with pytest.raises(Exception, match="param_core.csv"):
            copy.Data.param("check_tol")
    finally:
        copy.close()


@pytest.mark.parametrize("product", sorted(MODELS))
def test_param_layers_hold_every_item_once_and_merge_into_param_dict(product, product_models):
    """Every product reads the core, the tables and the tariff-type layer (and the tariff layer
    only where the file exists), each item in one layer, and ``param_dict()`` is their merge."""
    data = product_models(product).Data
    layers = data.param_layers()
    expected = ["core", "tables", "tariff_type"] + (
        ["tariff"] if data.param_tariff_path().is_file() else [])
    assert list(layers) == expected
    tariff_type = read_layer(data.input_dir() / data.param_file)["item"].tolist()
    assert sorted(layers["tariff_type"]) == sorted(tariff_type)
    assert len(tariff_type) == len(set(tariff_type))
    items = [item for layer in layers.values() for item in layer]
    assert len(items) == len(set(items))
    merged = {item: value for layer in layers.values() for item, value in layer.items()}
    assert data.param_dict() == merged
    assert list(data.param_dict()) == list(merged)


def test_param_rejects_an_item_in_two_layers(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    add_layer_rows(folder / "param_tariff.csv", {"expense_claim_pp_once": "300.0"})
    message = loader_error(folder / MODELS["risikolebensversicherung"], "TwoLayerProbe")
    assert "'expense_claim_pp_once' stands in two layers" in message
    assert str(folder / "param_tariff_type.csv") in message
    assert str(folder / "param_tariff.csv") in message


def test_param_rejects_an_item_twice_in_one_file(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    add_layer_rows(folder / "param_tariff_type.csv", {"expense_claim_pp_once": "250.0"})
    message = loader_error(folder / MODELS["risikolebensversicherung"], "TwiceProbe")
    assert "'expense_claim_pp_once' stands twice in" in message
    assert str(folder / "param_tariff_type.csv") in message


def test_param_rejects_a_core_item_in_the_tariff_type_file(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    model_dir = folder / MODELS["risikolebensversicherung"]
    add_layer_rows(model_dir / "CoreData" / "param_core.csv", {"expense_claim_pp_once": "250.0"})
    message = loader_error(model_dir, "CoreLockProbe")
    assert "'expense_claim_pp_once' is a core item of" in message
    assert str(folder / "param_tariff_type.csv") in message


def test_param_rejects_a_core_item_in_the_tariff_file(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    model_dir = folder / MODELS["risikolebensversicherung"]
    add_layer_rows(model_dir / "CoreData" / "param_core.csv", {"probe_core": "0.125"})
    add_layer_rows(folder / "param_tariff.csv", {"probe_core": "0.25"})
    message = loader_error(model_dir, "CoreLockTariffProbe")
    assert "'probe_core' is a core item of" in message
    assert str(folder / "param_tariff.csv") in message


@pytest.mark.parametrize(("text", "name", "words"), [
    ("", "EmptyValueProbe", "has no value in"),
    ("  ", "BlankValueProbe", "has no value in"),
    ("abc", "NoNumberProbe", "has the value 'abc' in"),
    ("+-3", "TwoSignsProbe", "has the value '+-3' in"),
    ("nan", "NanProbe", "not finite"),
    ("inf", "InfProbe", "not finite"),
    ("-inf", "NegInfProbe", "not finite"),
])
def test_param_rejects_a_value_that_is_no_finite_number(tmp_path, text, name, words):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    add_layer_rows(folder / "param_tariff_type.csv", {"probe_value": text})
    message = loader_error(folder / MODELS["risikolebensversicherung"], name)
    assert "'probe_value'" in message and words in message, message
    assert str(folder / "param_tariff_type.csv") in message


@pytest.mark.parametrize(("item", "name"), [
    (" check_tol", "PaddedCoreItemProbe"),
    ("probe_pad ", "PaddedItemProbe"),
])
def test_param_rejects_an_item_padded_with_whitespace(tmp_path, item, name):
    """A padded item would be a key of its own and slip past the core lock; it is rejected,
    not stripped."""
    folder = product_copy(tmp_path, "risikolebensversicherung")
    add_layer_rows(folder / "param_tariff_type.csv", {item: "1.0"})
    message = loader_error(folder / MODELS["risikolebensversicherung"], name)
    assert repr(item) in message and "padded with whitespace" in message, message
    assert str(folder / "param_tariff_type.csv") in message


def test_param_rejects_an_empty_item(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    add_layer_rows(folder / "param_tariff_type.csv", {"": "1.0"})
    message = loader_error(folder / MODELS["risikolebensversicherung"], "EmptyItemProbe")
    assert "item '' in" in message, message
    assert str(folder / "param_tariff_type.csv") in message


@pytest.mark.parametrize(("change", "name"), [
    (lambda table: table.drop(columns="basis"), "MissingColumnProbe"),
    (lambda table: table.insert(2, "unit", "") or table, "ExtraColumnProbe"),
    (lambda table: table[["item", "basis", "value", "provenance"]], "SwappedColumnProbe"),
])
def test_param_rejects_a_file_with_other_columns(tmp_path, change, name):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    path = folder / "param_tariff_type.csv"
    table = change(read_layer(path))
    table.to_csv(path, index=False)
    message = loader_error(folder / MODELS["risikolebensversicherung"], name)
    assert f"parameter file {path} has the columns {list(table.columns)}" in message, message


@pytest.mark.parametrize("every_row", [False, True], ids=["one_row", "every_row"])
def test_param_rejects_a_row_wider_than_the_header(tmp_path, every_row):
    """A row with a field more than the header is a parse error naming the file; with every
    row wide it does not become an index whose rows come back shifted."""
    folder = product_copy(tmp_path, "risikolebensversicherung")
    path = folder / "param_tariff_type.csv"
    header, *rows = path.read_text(encoding="utf-8").splitlines()
    rows = [row + ",x" if every_row or number == 1 else row for number, row in enumerate(rows)]
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    name = "WideRowsProbe" if every_row else "WideRowProbe"
    message = loader_error(folder / MODELS["risikolebensversicherung"], name)
    assert f"parameter file {path} cannot be read" in message, message


@pytest.mark.parametrize("product, file", [
    ("basisrente", "param_tariff_type.csv"),
    ("klassische_rentenversicherung", "param_tariff.csv"),
    ("fondsgebundene_rentenversicherung", "param_tariff_type.csv"),
])
def test_param_rejects_an_item_of_the_cost_table_in_a_layer(tmp_path, product, file):
    folder = product_copy(tmp_path, product)
    add_layer_rows(folder / file, {"charge_acq_bsum_once": "0.025"})
    message = loader_error(folder / MODELS[product], "CostTwiceProbe")
    assert "'charge_acq_bsum_once' stands in the cost table" in message
    assert str(folder / "charge_table.csv") in message
    assert str(folder / file) in message
