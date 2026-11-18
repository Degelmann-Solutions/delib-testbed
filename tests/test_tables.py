"""The table factory (``docs/core.md``, "The table factory").

The loader's part, on scratch copies of RLV:

- Every shipped product reads the table parameter file ``param_tables.csv`` beside the core
  file as its layer ``tables``, second of the layers; the shipped file holds the rows of the
  factory's tables, each with its value, basis and provenance, and no other, and a copy
  without the file raises.
- A fixture item of a copy's ``param_tables.csv`` is read through ``param`` like any other.
- An item named ``<role>_table`` holds a table name and is loaded as a ``str``, in the
  tariff-type and the tariff file; a number or a value of another form raises, and a name
  as the value of any other item is still no number.
- An item of the tables layer in the tariff-type or the tariff file raises, naming both
  files, and so does an item of the core file in the tables file (the core lock).

The space ``core/Core/Tables``:

- Every product holds it as the symlink ``CoreTables``, lists it in ``_spaces`` and names it
  as a base of no space; its ``Projection`` reads it through the Reference ``tables``, the
  space reads the product's ``Data`` through ``data``, takes no parameter and holds the
  core's cells and no other, so no product defines one.
- Its source holds no numeric literal but 0 and 1 and no cell name containing ``mort`` or
  ``q`` besides ``q``, and its cells read only ``data.param`` and each other.
- One table is defined, ``dav2008t_proxy`` on the law ``makeham``, in every product: ``q``
  gives ``a + b * c ** x`` in the law's float operations for both sexes, capped at 1 and
  exactly 1 at the closing age 120, the figures of the values package to their six digits;
  an age outside 0 to 120, a ``birth_year`` and a ``duration`` raise, and so does any other
  table name.
- On a scratch copy of Index with fixture tables and laws written into its ``CoreTables``
  and ``param_tables.csv`` beside the shipped table (``fixture_copy``): the period table
  gives its law's rate
  unrounded, 1 at the last age and at most 1; an age outside the table, another sex, a
  missing or a refused ``birth_year`` or ``duration`` and a duration below 1 raise, naming
  the table and the argument; the generational table applies its trend from its base year
  to the calendar year ``birth_year + x`` and not to the closure; the select table applies
  the factor of the duration and holds the last; a table naming an item the layer lacks
  raises the loader's ``KeyError``, and so does a gap in a table's select factors;
  ``items()`` lists every table's items.
- The runner's export engine, running the copy's points with per-contract cleanup, computes
  the same results as the modelx engine and keeps the rates of an earlier point in
  ``CoreTables`` after the point's item is deleted.

The derivation hooks of the core's ``Projection``:

- Only a switched product reaches a hook that reads the factory: ``mort_table_name`` and
  ``mort_rate_table`` are derived everywhere, reachable in the usage scan of Index, which
  chooses ``dav2008t_proxy``, and unreachable in the other nine, which hold no choice.
- Index reads its death rates through the factory alone: on every shipped point
  ``mort_rate(t)`` is ``q(dav2008t_proxy, sex, age(t))`` times its ``mort_be_factor`` 0.75,
  through the core's cells, none overridden but the factor; its folder holds no mortality
  file or column, its ``Data`` no Reference ``mort_file``, and no ``mort_table`` loader is
  reachable.
- On a scratch copy of Index that chooses a fixture table in its tariff-type file
  (``switched_copy``), the hooks deliver the table's rate on the point's own sex,
  its unisex blend and its end age, ``mort_rate`` stands on them, and the copy runs through
  both engines of the runner with the same results, the factory called without a birth
  year; with a ``birth_year`` cell and the generational fixture table the hooks pass the
  birth year on, and without the cell the generational table raises.
- A table rate of 1 passes through the core's derivation as 1 (AD-12): on a copy whose
  fixture table closes at the last age a point attains, with Index' best-estimate factor and a
  trend term below 1 and a loading above 1, ``mort_rate`` and ``mort_rate_tariff`` are 1 at the end age minus
  one and the factor and the loading times the table rate the year before.

The usage scan ``core/param_usage.py`` (``docs/core.md``, "The usage check and the view"):

- Every shipped product is clean and holds the factory's table; Index holds its choice and
  reads the table's items through ``mort_table_name``, the other nine hold no choice and
  read no tables item, and no table is unchosen across the ten.
- On a scratch copy of Index that chooses a fixture table (``choosing_copy``) the scan holds
  the factory's ``items()`` and the choice, counts the chosen table's items as read by the
  cells reading the choice item and no other table's item, and reports nothing; a copy with
  the fixture tables, a table read of its own and no choice (``unswitched_copy``) reads no
  tables item, and neither does one whose choice item no cell reads.
- The scan reports a chosen name the factory lacks, naming the item, its file and the name,
  in the tariff-type and the tariff file; an item of the tables layer that is in no table's
  items; an item a chosen table names that the layer lacks; a product-defined
  ``param_tables_path``; and a cell referencing ``param_tables_path``.
- The scan reports an item of a table that stands in another layer than the tables layer,
  and an item named ``<role>_table`` in the core or the tables file.
- The scan reports a reachable cell that reads an item of the tables layer itself, by a
  literal call or a ``param_indirect()`` declaration.
- ``unchosen_tables`` names, sorted, the tables no scanned model chooses; a table whose
  choice item no cell reads is not chosen.
"""
from __future__ import annotations

import ast
import builtins
import csv
import importlib
import importlib.util
from pathlib import Path

import modelx as mx
import pytest

from test_core import (CORE_MODEL, MODELS, PRODUCTS_DIR, ROOT, _add_params, _formula_cells,
                       _loader_error, param_usage, product_copy)

RLV = "risikolebensversicherung"
TABLES_FILE = "param_tables.csv"


# The tables the factory holds, {table: (law cell, parameters)}, the rows of the table
# parameter file, {item: (value as written, basis)}, each a row of the accepted values
# package, and the products that have switched to the factory, {product: its ``mort_table``}.
SHIPPED_TABLES = {
    "dav2008t_proxy": ("makeham", ("m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
                                   "first_age", "end_age")),
}
SHIPPED_ITEMS = {table: tuple(f"{table}_{name}" for name in names)
                 for table, (_law, names) in SHIPPED_TABLES.items()}
SHIPPED_ROWS = {
    "dav2008t_proxy_m_a": ("0.00022", "Setzung"),
    "dav2008t_proxy_m_b": ("2.8820182383e-05", "Setzung"),
    "dav2008t_proxy_m_c": ("1.1", "Setzung"),
    "dav2008t_proxy_f_a": ("0.00016", "Setzung"),
    "dav2008t_proxy_f_b": ("2.1653029589e-05", "Setzung"),
    "dav2008t_proxy_f_c": ("1.1", "Setzung"),
    "dav2008t_proxy_first_age": ("0", "Setzung"),
    "dav2008t_proxy_end_age": ("121", "Setzung"),
}
SHIPPED_LAYER = {item: (int(text) if text.isdigit() else float(text))
                 for item, (text, _basis) in SHIPPED_ROWS.items()}
SHIPPED_PROVENANCE = {
    "dav2008t_proxy": "[std] proxy of DAV 2008 T, first order, not the table itself, whose"
                      " values are DAV property and are not shipped; ",
}
SWITCHED = {"indexpolice": "dav2008t_proxy"}


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


def test_the_shipped_tables_file_holds_the_rows_of_its_tables_and_no_other():
    path = CORE_MODEL / "Data" / TABLES_FILE
    text = path.read_text(encoding="utf-8")
    assert text.isascii()
    with path.open(encoding="utf-8", newline="") as handle:
        header, *rows = list(csv.reader(handle))
    assert header == ["item", "value", "basis", "provenance"]
    assert all(len(row) == 4 for row in rows)
    assert [row[0] for row in rows] == [item for table in SHIPPED_TABLES
                                        for item in SHIPPED_ITEMS[table]]
    assert {row[0]: (row[1], row[2]) for row in rows} == SHIPPED_ROWS
    for item, _value, _basis, provenance in rows:
        (table,) = [table for table in SHIPPED_TABLES if item in SHIPPED_ITEMS[table]]
        assert provenance.startswith(SHIPPED_PROVENANCE[table]), item
        assert len(provenance) > len(SHIPPED_PROVENANCE[table]), item
    assert len({row[3] for row in rows if not row[0].endswith(("_m_c", "_f_c"))}) == len(
        [row for row in rows if not row[0].endswith(("_m_c", "_f_c"))])


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_tables_layer_is_the_second_layer_and_holds_the_tables(product, product_models):
    data = product_models(product).Data
    assert data.param_tables_path() == data.model.path / "CoreData" / TABLES_FILE
    assert data.param_tables_path().is_file()
    assert list(data.param_paths()) == ["core", "tables", "tariff_type"]
    assert data.param_paths()["tables"] == data.param_tables_path()
    assert [(row[0], row[1], row[2]) for row in data.param_rows()["tables"]] == [
        (item, value, basis) for item, (value, basis) in SHIPPED_ROWS.items()]
    assert list(data.param_layers()) == ["core", "tables", "tariff_type"]
    layer = data.param_layers()["tables"]
    assert layer == SHIPPED_LAYER
    assert all(type(layer[item]) is type(value) for item, value in SHIPPED_LAYER.items())


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
        assert data.param_layers()["tables"] == SHIPPED_LAYER | {"fixture_end_age": 121,
                                                                 "fixture_m_a": 0.0005}
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


# --------------------------------------------------------------------------- the space

TABLES_SOURCE = CORE_MODEL / "Tables" / "__init__.py"
TABLES_CELLS = ["definitions", "definition", "items", "parameter", "first_age", "end_age",
                "base_year", "select_factors", "base_rate", "trend", "makeham", "q"]


def raised_line(call) -> str:
    """The line ``<Error>: <message>`` of the error ``call()`` raises.

    modelx wraps a formula's error in a ``FormulaError`` whose text also holds the formula
    source; only the last line before ``Formula traceback:`` is the raised error. The
    exported model raises the plain exception.
    """
    with pytest.raises(Exception) as raised:
        call()
    if type(raised.value).__name__ != "FormulaError":
        return f"{type(raised.value).__name__}: {raised.value}"
    head = str(raised.value).split("Formula traceback:", 1)[0]
    return [text for text in head.splitlines() if text.strip()][-1]


def test_the_core_holds_the_tables_space_without_a_parameter():
    model = mx.read_model(CORE_MODEL, name="TablesCoreProbe")
    try:
        assert sorted(model.spaces) == ["Data", "Projection", "Tables"]
        tables = model.Tables
        assert tables.formula is None
        assert list(tables.cells) == TABLES_CELLS
        assert tables.data is model.Data
        assert tables.bases == []
        assert list(tables.definitions()) == list(SHIPPED_TABLES)
        for table, (law_name, names) in SHIPPED_TABLES.items():
            law_cell, trend_cell, held = tables.definitions()[table]
            assert f".Tables.{law_name}(table, sex, x)" in repr(law_cell)
            assert trend_cell is None and held == names
        assert tables.items() == SHIPPED_ITEMS
    finally:
        model.close()


@pytest.mark.parametrize("product", sorted(MODELS))
def test_a_product_holds_the_factory_as_a_symlink_and_inherits_it_nowhere(product,
                                                                          product_models):
    folder = PRODUCTS_DIR / product / MODELS[product]
    link = folder / "CoreTables"
    assert link.is_symlink()
    assert link.readlink() == Path("../../../core/Core/Tables")
    assert link.resolve() == (CORE_MODEL / "Tables").resolve()
    spaces = ast.literal_eval(
        (folder / "__init__.py").read_text(encoding="utf-8").split("_spaces = ", 1)[1])
    assert spaces == ["CoreData", "CoreProjection", "CoreTables", "Data", "Projection"]

    model = product_models(product)
    tables = model.CoreTables
    assert list(model.spaces) == spaces
    for space in model.spaces.values():
        assert tables not in space.bases, space.name
    assert tables.bases == []
    assert tables.formula is None
    assert model.Projection.tables is tables
    assert tables.data is model.Data
    # the core's cells and no other, each with the core's source: no product defines one
    assert list(tables.cells) == TABLES_CELLS
    source = TABLES_SOURCE.read_text(encoding="utf-8")
    for name, cell in tables.cells.items():
        assert cell._is_defined()
        assert cell.formula.source in source, name


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_shipped_product_holds_the_factorys_tables_and_no_other(product, product_models):
    """Also a product no cell of which reads the table: the factory is model-wide."""
    tables = product_models(product).CoreTables
    assert list(tables.definitions()) == list(SHIPPED_TABLES)
    assert tables.items() == SHIPPED_ITEMS
    assert tables.q("dav2008t_proxy", "M", 40) == makeham_rate("M", 40)
    assert tables.end_age("dav2008t_proxy") == 121 and tables.first_age("dav2008t_proxy") == 0
    line = raised_line(lambda: tables.q("nosuch", "M", 40))
    assert line == "ValueError: table 'nosuch' is not defined"
    assert raised_line(lambda: tables.end_age("nosuch")).startswith("KeyError")


DAV2008T = "dav2008t_proxy"


def makeham_rate(sex: str, x: int, table: str = DAV2008T) -> float:
    """The rate of the law ``makeham`` from the rows of a shipped table, in the float
    operations of the law's cell: ``a + b * c ** x``."""
    a, b, c = (SHIPPED_LAYER[f"{table}_{sex.lower()}_{name}"] for name in "abc")
    return a + b * c ** x


@pytest.fixture(scope="module")
def shipped_tables(product_models):
    """The factory as a shipped product holds it, read off RLV, which reads no table of it."""
    return product_models(RLV).CoreTables


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2008t_proxy_gives_its_makeham_rate_capped_at_1(shipped_tables, sex):
    assert SHIPPED_LAYER["dav2008t_proxy_m_a"] == 0.00022
    assert SHIPPED_LAYER["dav2008t_proxy_m_b"] == 2.8820182383e-05
    assert SHIPPED_LAYER["dav2008t_proxy_f_a"] == 0.00016
    assert SHIPPED_LAYER["dav2008t_proxy_f_b"] == 2.1653029589e-05
    assert SHIPPED_LAYER["dav2008t_proxy_m_c"] == 1.1 == SHIPPED_LAYER["dav2008t_proxy_f_c"]
    a, b = {"M": (0.00022, 2.8820182383e-05), "F": (0.00016, 2.1653029589e-05)}[sex]
    capped = []
    for x in range(0, 120):
        rate = shipped_tables.q(DAV2008T, sex, x)
        assert type(rate) is float
        assert rate == min(1.0, a + b * 1.1 ** x) == min(1.0, makeham_rate(sex, x)), x
        assert shipped_tables.base_rate(DAV2008T, sex, x) == a + b * 1.1 ** x, x
        assert shipped_tables.makeham(DAV2008T, sex, x) == a + b * 1.1 ** x, x
        if a + b * 1.1 ** x > 1.0:
            capped.append(x)
    # the cap binds from 110 for a man and 113 for a woman, below it the rate is the law's
    assert capped == list(range({"M": 110, "F": 113}[sex], 120))
    assert shipped_tables.q(DAV2008T, sex, capped[0]) == 1.0
    assert shipped_tables.q(DAV2008T, sex, capped[0] - 1) < 1.0
    assert shipped_tables.q(DAV2008T, sex, 40) != round(makeham_rate(sex, 40), 10)
    assert raised_line(lambda: shipped_tables.trend(DAV2008T, sex, 40)) == (
        "ValueError: table 'dav2008t_proxy': a period table has no trend")
    assert shipped_tables.select_factors(DAV2008T) == ()


# The values package's "New table" figures of dav2008t_proxy, six significant digits.
PACKAGE_RATES = {
    ("M", 30): 0.000722895, ("M", 40): 0.00152438, ("M", 50): 0.00360323, ("M", 65): 0.0143526,
    ("F", 30): 0.000537832, ("F", 40): 0.00114, ("F", 50): 0.00270187, ("F", 65): 0.010778,
}


@pytest.mark.parametrize(("sex", "x"), sorted(PACKAGE_RATES))
def test_dav2008t_proxy_gives_the_rates_of_the_values_package(shipped_tables, sex, x):
    rate = shipped_tables.q(DAV2008T, sex, x)
    assert float(f"{rate:.6g}") == PACKAGE_RATES[(sex, x)]
    # the anchor of the table: q(M, 37) = 0.0012, and women three years of age behind
    assert shipped_tables.q(DAV2008T, "M", 37) == pytest.approx(0.0012, rel=1e-9)
    assert shipped_tables.q(DAV2008T, "F", 40) - 0.00016 == pytest.approx(
        shipped_tables.q(DAV2008T, "M", 37) - 0.00022, rel=1e-9)


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2008t_proxy_closes_at_120_and_raises_outside_its_ages(shipped_tables, sex):
    rate = shipped_tables.q(DAV2008T, sex, 120)
    assert rate == 1.0 and type(rate) is float
    assert shipped_tables.q(DAV2008T, sex, 0) == makeham_rate(sex, 0)
    for x in (121, -1, 150):
        for cell in (shipped_tables.q, shipped_tables.base_rate):
            line = raised_line(lambda: cell(DAV2008T, sex, x))
            assert line == (f"ValueError: table 'dav2008t_proxy': x {x!r} is outside its ages"
                            f" 0 to 120"), line


def test_dav2008t_proxy_is_a_period_table_without_selection(shipped_tables):
    for x in (40, 120):
        line = raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, 1960))
        assert line == ("ValueError: table 'dav2008t_proxy': birth_year 1960 is given, the"
                        " table is a period table")
        assert line == raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, birth_year=1960))
        line = raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, None, 1))
        assert line == ("ValueError: table 'dav2008t_proxy': duration 1 is given, the table"
                        " has no selection")
        assert line == raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, duration=1))


def test_the_factory_source_holds_no_number_but_0_and_1():
    cells = dict(_formula_cells(TABLES_SOURCE))
    assert list(cells) == TABLES_CELLS
    numbers = [(name, node.value) for name, cell in cells.items() for node in ast.walk(cell)
               if isinstance(node, ast.Constant) and type(node.value) in (int, float, complex)
               and (type(node.value) is complex or node.value not in (0, 1))]
    assert numbers == []


def test_only_q_says_mortality_in_the_factory():
    names = [name for name, _cell in _formula_cells(TABLES_SOURCE)]
    assert "q" in names
    assert [name for name in names if name != "q" and ("mort" in name or "q" in name)] == []


def _local_names(cell: ast.AST) -> set[str]:
    """The names a formula binds itself: its arguments and every name it stores."""
    names = {arg.arg for node in ast.walk(cell) if isinstance(node, ast.arguments)
             for arg in node.posonlyargs + node.args + node.kwonlyargs}
    names |= {node.id for node in ast.walk(cell)
              if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
    return names


def foreign_reads(path: Path) -> list[str]:
    """What the cells of a factory source read besides ``data.param``, each other, their own
    names and Python's builtins: ``<cell>: <name>`` each, sorted."""
    cells = dict(_formula_cells(path))
    found = set()
    for name, cell in cells.items():
        local = _local_names(cell)
        loader = set()
        for node in ast.walk(cell):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "data" and "data" not in local):
                if node.attr == "param":
                    loader.add(id(node.value))
                else:
                    found.add(f"{name}: data.{node.attr}")
                    loader.add(id(node.value))
        for node in ast.walk(cell):
            if not isinstance(node, ast.Name) or node.id in local or node.id in cells:
                continue
            if node.id == "data":
                if id(node) not in loader:
                    found.add(f"{name}: data")
            elif not hasattr(builtins, node.id):
                found.add(f"{name}: {node.id}")
    return sorted(found)


def test_the_factory_cells_read_only_data_param_and_each_other(tmp_path):
    assert foreign_reads(TABLES_SOURCE) == []
    probe = tmp_path / "probe.py"
    probe.write_text(
        "def a(table):\n    return data.param(table) + b()\n\n"
        "def b():\n    return data.model_point_table() + point_id + tables.q()\n\n"
        "def c(x):\n    y = [z for z in range(x)]\n    return len(y) + pd.NA\n\n"
        "def d():\n    return a(data)\n",
        encoding="utf-8")
    assert foreign_reads(probe) == ["b: data.model_point_table", "b: point_id", "b: tables",
                                    "c: pd", "d: data"]


# The fixture tables of a scratch copy: laws no shipped table has, numbers of no real table,
# and names that are none of the tables the factory holds or will hold.
FIXTURE_LAWS = '''
def law_fixture(table, sex, x):
    """A fixture law: ``a * b ** x`` on the rate, by sex."""
    return (parameter(table, sex.lower() + "_a")
            * parameter(table, sex.lower() + "_b") ** x)


def trend_fixture(table, sex, x):
    """A fixture trend law: one annual improvement rate by sex, the same at every age."""
    return parameter(table, sex.lower() + "_trend")

'''
FIXTURE_LAW_ITEMS = ("m_a", "m_b", "f_a", "f_b", "first_age", "end_age")
FIXTURE_DEFINITIONS = {
    "period_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS),
    "steep_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS),
    "gen_fixture": ("law_fixture", "trend_fixture",
                    FIXTURE_LAW_ITEMS + ("m_trend", "f_trend", "base_year")),
    "sel_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS + ("sel_2", "sel_1", "sel_3")),
    "broken_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS),
    "gap_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS + ("sel_1", "sel_3")),
}
FIXTURE_LAW_VALUES = {"m_a": "0.0000201", "m_b": "1.09", "f_a": "0.0000107", "f_b": "1.092",
                      "first_age": "0", "end_age": "121"}
FIXTURE_VALUES = {
    "period_fixture": FIXTURE_LAW_VALUES,
    "steep_fixture": FIXTURE_LAW_VALUES | {"m_a": "0.01", "first_age": "20", "end_age": "111"},
    "gen_fixture": FIXTURE_LAW_VALUES | {"m_trend": "0.0125", "f_trend": "0.0175",
                                         "base_year": "1999"},
    "sel_fixture": FIXTURE_LAW_VALUES | {"sel_1": "3.5", "sel_2": "2.25", "sel_3": "1.5"},
    "broken_fixture": {name: value for name, value in FIXTURE_LAW_VALUES.items()
                       if name != "f_b"},
    "gap_fixture": FIXTURE_LAW_VALUES | {"sel_1": "3.5", "sel_3": "1.5"},
}
MARKER = "# " + "-" * 75 + "\n# References"
INDEX = "indexpolice"


ALL_TABLES = list(SHIPPED_TABLES) + list(FIXTURE_DEFINITIONS)


def add_cells(path: Path, source: str) -> None:
    """Append the cells of ``source`` to a space file, before its References."""
    text = path.read_text(encoding="utf-8")
    assert text.count(MARKER) == 1
    path.write_text(text.replace(MARKER, source.lstrip("\n") + "\n" + MARKER),
                    encoding="utf-8")


def write_fixture_tables(model_dir: Path) -> None:
    """Write the fixture tables into a scratch copy, beside the shipped tables: their
    definitions, after the shipped ones, and laws into its ``CoreTables`` and their numbers
    into its ``param_tables.csv``."""
    path = model_dir / "CoreTables" / "__init__.py"
    assert path.is_file() and not (model_dir / "CoreTables").is_symlink()
    text = path.read_text(encoding="utf-8")
    (cell,) = [node for node in ast.parse(text).body
               if isinstance(node, ast.FunctionDef) and node.name == "definitions"]
    (held,) = [node.value for node in ast.walk(cell) if isinstance(node, ast.Return)]
    assert isinstance(held, ast.Dict) and held.end_lineno > held.lineno
    assert [key.value for key in held.keys] == list(SHIPPED_TABLES)
    lines = text.splitlines(keepends=True)
    assert lines[held.end_lineno - 1] == "    }\n"
    lines[held.end_lineno - 1:held.end_lineno - 1] = [
        f"        {table!r}: ({law}, {trend}, {names!r}),\n"
        for table, (law, trend, names) in FIXTURE_DEFINITIONS.items()]
    path.write_text("".join(lines), encoding="utf-8")
    add_cells(path, FIXTURE_LAWS)
    _add_params(model_dir / "CoreData" / TABLES_FILE,
                {f"{table}_{name}": value for table, values in FIXTURE_VALUES.items()
                 for name, value in values.items()})


def fixture_copy(tmp_path: Path, product: str = INDEX) -> Path:
    """A scratch copy of a product folder whose factory holds the fixture tables."""
    folder = product_copy(tmp_path, product)
    write_fixture_tables(folder / MODELS[product])
    return folder


def law(sex: str, x: int, values: dict = FIXTURE_LAW_VALUES) -> float:
    """The fixture law's rate, in the float operations of the fixture cell."""
    return float(values[sex.lower() + "_a"]) * float(values[sex.lower() + "_b"]) ** x


@pytest.fixture(scope="module")
def fixture_tables(tmp_path_factory):
    """The factory of a scratch copy of Index with the fixture tables, read by modelx."""
    folder = fixture_copy(tmp_path_factory.mktemp("fixture_tables"))
    model = mx.read_model(folder / MODELS[INDEX], name="FixtureTables")
    yield model.CoreTables
    model.close()


def test_the_fixture_is_written_into_the_copy_only(fixture_tables):
    assert list(fixture_tables.definitions()) == ALL_TABLES
    assert "_fixture" not in TABLES_SOURCE.read_text(encoding="utf-8")
    assert "_fixture" not in (CORE_MODEL / "Data" / TABLES_FILE).read_text(encoding="utf-8")
    known = ("dav2008t_proxy", "dav2008t_nr_proxy", "dav2008t_r_proxy", "dav2004r_proxy",
             "dav1997ti_proxy", "pflege_aktive_proxy")
    assert set(SHIPPED_TABLES) <= set(known)
    assert not set(FIXTURE_DEFINITIONS) & set(known)
    # the shipped table is the same beside the fixture tables
    assert fixture_tables.q("dav2008t_proxy", "F", 50) == makeham_rate("F", 50)
    assert not any(name.endswith("_proxy") for name in FIXTURE_DEFINITIONS)


def test_items_lists_the_items_of_every_table(fixture_tables):
    items = fixture_tables.items()
    assert list(items) == ALL_TABLES
    for table in SHIPPED_TABLES:
        assert items[table] == SHIPPED_ITEMS[table]
    for table, (_law, _trend, names) in FIXTURE_DEFINITIONS.items():
        assert items[table] == tuple(f"{table}_{name}" for name in names)
    held = set(fixture_tables.data.param_layers()["tables"])
    listed = {item for table in items for item in items[table]}
    assert listed - held == {"broken_fixture_f_b"}
    assert held - listed == set()


@pytest.mark.parametrize("sex", ["M", "F"])
def test_a_period_table_gives_its_laws_rate_unrounded(fixture_tables, sex):
    for x in range(0, 120):
        rate = fixture_tables.q("period_fixture", sex, x)
        assert type(rate) is float
        assert rate == min(1.0, law(sex, x)) == law(sex, x), x
        assert rate == fixture_tables.base_rate("period_fixture", sex, x)
    assert fixture_tables.q("period_fixture", "M", 40) != round(law("M", 40), 10)
    assert fixture_tables.q("period_fixture", "M", 40) != fixture_tables.q(
        "period_fixture", "F", 40)


def test_a_table_parameter_is_read_through_param(fixture_tables):
    assert fixture_tables.parameter("period_fixture", "m_a") == 0.0000201
    assert fixture_tables.first_age("steep_fixture") == 20
    assert fixture_tables.end_age("steep_fixture") == 111
    assert type(fixture_tables.end_age("steep_fixture")) is int
    assert fixture_tables.base_year("gen_fixture") == 1999
    assert fixture_tables.select_factors("sel_fixture") == (3.5, 2.25, 1.5)
    assert fixture_tables.select_factors("period_fixture") == ()


@pytest.mark.parametrize("table", ["period_fixture", "steep_fixture", "gen_fixture",
                                   "sel_fixture"])
def test_the_rate_at_the_last_age_is_exactly_1(fixture_tables, table):
    last = fixture_tables.end_age(table) - 1
    extra = {"gen_fixture": {"birth_year": 2090}, "sel_fixture": {"duration": 1}}.get(table, {})
    for sex in ("M", "F"):
        rate = fixture_tables.q(table, sex, last, **extra)
        assert rate == 1.0 and type(rate) is float
    # the closure is the table's, not the law's
    assert law("F", 120) < 1.0
    assert fixture_tables.base_rate("period_fixture", "F", 120) == law("F", 120)


def test_a_rate_is_capped_at_1_and_the_base_rate_is_not(fixture_tables):
    values = FIXTURE_VALUES["steep_fixture"]
    capped = [x for x in range(20, 110) if law("M", x, values) > 1.0]
    assert capped and capped[0] > 20
    for x in range(20, 110):
        assert fixture_tables.q("steep_fixture", "M", x) == min(1.0, law("M", x, values))
        assert fixture_tables.base_rate("steep_fixture", "M", x) == law("M", x, values)
    assert fixture_tables.q("steep_fixture", "M", capped[0]) == 1.0


@pytest.mark.parametrize(("table", "x"), [
    ("period_fixture", -1), ("period_fixture", 121), ("period_fixture", 150),
    ("steep_fixture", 19), ("steep_fixture", 0), ("steep_fixture", 111),
])
def test_an_age_outside_the_table_raises_and_is_not_clamped(fixture_tables, table, x):
    for cell in (fixture_tables.q, fixture_tables.base_rate):
        line = raised_line(lambda: cell(table, "M", x))
        assert line.startswith(f"ValueError: table {table!r}: x {x!r} is outside"), line


@pytest.mark.parametrize("sex", ["U", "m", "f", "", None, 1])
def test_a_sex_other_than_m_and_f_raises(fixture_tables, sex):
    line = raised_line(lambda: fixture_tables.q("period_fixture", sex, 40))
    assert line.startswith(f"ValueError: table 'period_fixture': sex {sex!r} is"), line


def test_an_unknown_table_raises(fixture_tables):
    for cell in (fixture_tables.q, fixture_tables.base_rate, fixture_tables.trend):
        assert raised_line(lambda: cell("fixture", "M", 40)) == (
            "ValueError: table 'fixture' is not defined")
    assert raised_line(lambda: fixture_tables.definition("fixture")) == (
        "ValueError: table 'fixture' is not defined")


@pytest.mark.parametrize(("sex", "trend"), [("M", 0.0125), ("F", 0.0175)])
def test_a_generational_table_applies_its_trend_to_the_calendar_year(fixture_tables, sex, trend):
    assert fixture_tables.trend("gen_fixture", sex, 40) == trend
    for birth_year, x in [(1959, 40), (1960, 67), (1999, 0), (2010, 30), (1940, 20), (1900, 119)]:
        rate = fixture_tables.q("gen_fixture", sex, x, birth_year)
        assert rate == min(1.0, law(sex, x) * (1.0 - trend) ** (birth_year + x - 1999))
        assert rate == fixture_tables.q("gen_fixture", sex, x, birth_year=birth_year)
    # the base year's rate is the law's, a later year's lower, an earlier year's higher
    assert fixture_tables.q("gen_fixture", sex, 40, 1959) == law(sex, 40)
    assert fixture_tables.q("gen_fixture", sex, 40, 1989) < law(sex, 40)
    assert fixture_tables.q("gen_fixture", sex, 40, 1929) > law(sex, 40)
    # the same calendar year reached by two birth years has the same trend power
    assert fixture_tables.q("gen_fixture", sex, 60, 1990) / law(sex, 60) == pytest.approx(
        fixture_tables.q("gen_fixture", sex, 50, 2000) / law(sex, 50), rel=1e-14)


def test_the_trend_does_not_act_on_the_closure(fixture_tables):
    assert fixture_tables.q("gen_fixture", "M", 120, 2100) == 1.0
    assert fixture_tables.q("gen_fixture", "M", 119, 2100) < 1.0


def test_a_generational_table_without_a_birth_year_raises(fixture_tables):
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q("gen_fixture", "M", x))
        assert line == ("ValueError: table 'gen_fixture': birth_year is missing, the table is"
                        " generational")


@pytest.mark.parametrize("table", ["period_fixture", "sel_fixture"])
def test_a_period_table_with_a_birth_year_raises(fixture_tables, table):
    extra = {"duration": 1} if table == "sel_fixture" else {}
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q(table, "M", x, 1960, **extra))
        assert line == (f"ValueError: table {table!r}: birth_year 1960 is given, the table is a"
                        f" period table")
    line = raised_line(lambda: fixture_tables.trend(table, "M", 40))
    assert line == f"ValueError: table {table!r}: a period table has no trend"


def test_a_select_table_applies_the_factor_of_the_duration_and_holds_the_last(fixture_tables):
    factors = {1: 3.5, 2: 2.25, 3: 1.5, 4: 1.5, 11: 1.5, 80: 1.5}
    for duration, factor in factors.items():
        for x in (30, 55):
            rate = fixture_tables.q("sel_fixture", "F", x, None, duration)
            assert rate == min(1.0, law("F", x) * factor)
            assert rate == fixture_tables.q("sel_fixture", "F", x, duration=duration)
    # a selected rate is capped at 1 too
    assert law("M", 115) < 1.0 < law("M", 115) * 3.5
    assert fixture_tables.q("sel_fixture", "M", 115, duration=1) == 1.0


@pytest.mark.parametrize(("duration", "words"), [
    (None, "duration is missing, the table is select"),
    (0, "duration 0 is below 1"),
    (-3, "duration -3 is below 1"),
])
def test_a_select_table_without_a_duration_from_1_raises(fixture_tables, duration, words):
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q("sel_fixture", "M", x, None, duration))
        assert line == f"ValueError: table 'sel_fixture': {words}"


@pytest.mark.parametrize("table", ["period_fixture", "gen_fixture"])
def test_a_table_without_selection_with_a_duration_raises(fixture_tables, table):
    birth_year = 1960 if table == "gen_fixture" else None
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q(table, "M", x, birth_year, 1))
        assert line == (f"ValueError: table {table!r}: duration 1 is given, the table has no"
                        f" selection")


def test_a_table_naming_an_item_the_layer_lacks_raises_the_loaders_key_error(fixture_tables):
    assert fixture_tables.q("broken_fixture", "M", 40) == law("M", 40)
    line = raised_line(lambda: fixture_tables.q("broken_fixture", "F", 40))
    assert line == "KeyError: 'broken_fixture_f_b'"


def test_a_gap_in_the_select_factors_raises_the_loaders_key_error(fixture_tables):
    """``sel_1`` and ``sel_3`` are two factors, read as ``sel_1`` and ``sel_2``: duration 2
    does not silently get ``sel_3``."""
    for cell in (lambda: fixture_tables.select_factors("gap_fixture"),
                 lambda: fixture_tables.q("gap_fixture", "M", 40, duration=1),
                 lambda: fixture_tables.q("gap_fixture", "M", 40, duration=2)):
        assert raised_line(cell) == "KeyError: 'gap_fixture_sel_2'"


# --------------------------------------------------------------------------- the runner

def load_runner():
    spec = importlib.util.spec_from_file_location("run_baseline",
                                                  ROOT / "tools" / "run_baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def held_rates(space_model) -> dict:
    """The rates the factory of an exported model holds, by the arguments of ``q``."""
    return dict(space_model.CoreTables._v_q)


def run_spying_on_the_factory(folder: Path, monkeypatch, **run):
    """Run ``folder`` through the runner's export engine. Return the run's result, the rates
    ``CoreTables`` held just after each point's item was deleted, by point in the order of
    the deletions, and the rates it held when the run ended."""
    after, models = {}, []
    import_module = importlib.import_module

    def spying_import(name, *args, **kwargs):
        module = import_module(name, *args, **kwargs)
        if name.startswith("_delib_export_"):
            space_model = module.mx_model
            models.append(space_model)
            cls = type(space_model.Projection)
            original = cls.__delitem__

            def spy(self, key):
                original(self, key)
                after[key] = held_rates(space_model)

            monkeypatch.setattr(cls, "__delitem__", spy)
        return module

    monkeypatch.setattr(importlib, "import_module", spying_import)
    result = load_runner().run_product(folder, **run)
    assert len(models) == 1
    return result, after, held_rates(models[0])


def test_the_runner_keeps_the_rates_of_an_earlier_point(tmp_path, monkeypatch):
    """The copy of Index reads the period fixture table in a cell of its own, which
    overrides the core's hook: the two engines agree, and the rates point 1 computed are
    still held after its item and every later point's item are deleted."""
    folder = fixture_copy(tmp_path)
    add_cells(folder / MODELS[INDEX] / "Projection" / "__init__.py",
              'def mort_rate_at_age(x):\n'
              '    """The fixture table\'s rate.\n\n'
              '    Override reason: test fixture, tests/test_tables.py\n    """\n'
              '    return tables.q("period_fixture", sex(), x)\n')
    runner = load_runner()
    traced = runner.run_product(folder, engine="modelx")
    shipped = runner.run_product(PRODUCTS_DIR / INDEX, engine="modelx")
    (count, checks, sha, failures, _lines, digests), after, at_end = run_spying_on_the_factory(
        folder, monkeypatch)
    assert failures == [] and traced[3] == []
    assert count > 2 and list(after) == list(range(1, count + 1))
    assert (count, checks, sha, digests) == (traced[0], traced[1], traced[2], traced[5])
    assert sha != shipped[2]

    first = after[1]
    assert first and all(key[0] == "period_fixture" for key in first)
    sex, age = next((key[1], key[2]) for key in first)
    assert first[("period_fixture", sex, age, None, None)] == law(sex, age)
    for point_id in range(2, count + 1):
        assert first.items() <= after[point_id].items(), point_id
    assert first.items() <= at_end.items()
    assert len(at_end) > len(first)


# --------------------------------------------------------------------------- the hooks

TABLE_HOOKS = ("mort_table_name", "mort_rate_table", "omega_age_table")


@pytest.mark.parametrize("product", sorted(MODELS))
def test_only_a_switched_product_reaches_a_hook_that_reads_the_factory(product, product_models):
    model = product_models(product)
    reachable = param_usage.scan(model).reachable
    for hook in TABLE_HOOKS:
        assert model.Projection.cells[hook]._is_derived(), hook
    assert "omega_age_table" not in reachable
    if product in SWITCHED:
        assert {"mort_table_name", "mort_rate_table", "mort_rate_at_age"} <= reachable
        assert model.Data.param_dict()["mort_table"] == SWITCHED[product]
    else:
        for hook in TABLE_HOOKS:
            assert hook not in reachable, hook
        assert "mort_table" not in model.Data.param_dict()


# The best-estimate rates of the values package for Index, six significant digits.
INDEX_PACKAGE_RATES = {
    ("M", 30): 0.000542171, ("M", 40): 0.00114328, ("M", 50): 0.00270242, ("M", 65): 0.0107644,
    ("F", 30): 0.000403374, ("F", 40): 0.000855, ("F", 50): 0.0020264, ("F", 65): 0.00808351,
}


def test_index_best_estimate_is_the_factorys_rate_times_its_factor(product_models):
    model = product_models(INDEX)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in TABLE_HOOKS + ("birth_year", "mort_rate_at_age", "mort_rate_base",
                               "mort_be_trend", "mort_rate", "mort_rate_mth", "pols_death"):
        assert cells[name]._is_derived(), name
    assert cells["mort_be_factor"]._is_defined()
    assert "Override reason:" in cells["mort_be_factor"].formula.source
    assert model.Data.param("mort_be_factor") == 0.75
    assert model.Data.param("mort_table") == "dav2008t_proxy"
    seen = set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex = item.sex()
        assert item.mort_table_name() == "dav2008t_proxy"
        assert item.mort_be_factor() == 0.75 and item.birth_year() == 0
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            rate = tables.q("dav2008t_proxy", sex, x)
            assert rate == makeham_rate(sex, x) < 1.0
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == rate * 0.75, (point_id, t)
            assert item.mort_rate_mth(t) == 1.0 - (1.0 - rate * 0.75) ** (1.0 / 12.0)
            if (sex, x) in INDEX_PACKAGE_RATES:
                assert float(f"{item.mort_rate(t):.6g}") == INDEX_PACKAGE_RATES[(sex, x)]
                seen.add((sex, x))
    assert {("M", 40), ("M", 50), ("M", 65), ("F", 40), ("F", 50), ("F", 65)} <= seen
    assert {key[0] for key in tables.q} == {"dav2008t_proxy"}


def test_index_holds_no_mortality_file_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / INDEX
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header if "mort" in column or column == "qx"], path
    model = product_models(INDEX)
    assert "mort_file" not in model.Data.refs
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    assert own == ["mort_be_factor"]
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    reachable = param_usage.scan(model).reachable
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & reachable
    for space in ("Data", "Projection"):
        source = (folder / MODELS[INDEX] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()"):
            assert name not in source, (space, name)
    # every death rate of a run comes through the factory's one lookup
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0


def unswitched_copy(tmp_path: Path) -> Path:
    """A scratch copy of Index with the fixture tables that chooses no table: without its
    row ``mort_table`` and with a ``mort_rate_at_age`` of its own that reads no table, as a
    product before its switch."""
    folder = fixture_copy(tmp_path)
    path = folder / "param_tariff_type.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    choice = [row for row in rows if row.startswith("mort_table,")]
    assert len(choice) == 1
    path.write_text("".join(row for row in rows if row not in choice), encoding="utf-8")
    add_cells(folder / MODELS[INDEX] / "Projection" / "__init__.py",
              'def mort_rate_at_age(x):\n'
              '    """A rate of its own, read off no table.\n\n'
              '    Override reason: test fixture, tests/test_tables.py\n    """\n'
              '    return 0.001 if sex() == "M" else 0.0007\n')
    return folder


def switched_copy(tmp_path: Path, table: str, birth_year: int | None = None) -> Path:
    """A scratch copy of Index with the fixture tables that chooses ``table`` as its
    ``mort_table`` in place of the shipped choice; with ``birth_year``, a cell of that name
    returning it. Index has no ``mort_rate_at_age`` of its own, and its ``mort_be_factor``
    0.75 stands."""
    folder = fixture_copy(tmp_path)
    path = folder / MODELS[INDEX] / "Projection" / "__init__.py"
    assert "def mort_rate_at_age(" not in path.read_text(encoding="utf-8")
    if birth_year is not None:
        add_cells(path,
                  'def birth_year():\n'
                  '    """A fixture birth year.\n\n'
                  '    Override reason: test fixture, tests/test_tables.py\n    """\n'
                  f'    return {birth_year}\n')
    path = folder / "param_tariff_type.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    choice = [row for row in rows if row.startswith("mort_table,")]
    assert len(choice) == 1
    path.write_text("".join(row for row in rows if row not in choice), encoding="utf-8")
    _add_params(path, {"mort_table": table, "unisex_mix_male": "0.45"})
    return folder


def test_the_hooks_deliver_the_chosen_table(tmp_path):
    folder = switched_copy(tmp_path, "period_fixture")
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedProbe")
    try:
        projection, tables = model.Projection, model.CoreTables
        for hook in TABLE_HOOKS + ("mort_rate_at_age", "mort_rate_tariff_at_age", "birth_year",
                                   "mort_be_trend", "mort_rate_base", "mort_rate"):
            assert projection.cells[hook]._is_derived(), hook
        points = model.Data.model_point_table()
        sexes = set()
        for point_id in points.index[:4]:
            item = projection[point_id]
            sex = points.at[point_id, "sex"]
            sexes.add(sex)
            assert item.mort_table_name() == "period_fixture"
            assert item.birth_year() == 0          # no birth year: the factory gets None
            assert item.omega_age_table() == 121 == tables.end_age("period_fixture")
            for x in (0, 40, 67, 119, 120):
                rate = tables.q("period_fixture", sex, x)
                assert item.mort_rate_table(sex, x) == rate
                assert item.mort_rate_at_age(x) == rate
                assert rate == (law(sex, x) if x < 120 else 1.0)
                male, female = (tables.q("period_fixture", s, x) for s in "MF")
                assert item.mort_rate_tariff_at_age(x) == 0.45 * male + (1.0 - 0.45) * female
            assert item.mort_rate_tariff_at_age(120) == 1.0
            for t in (item.t_start(), item.t_start() + 13, item.proj_len() - 1):
                rate = tables.q("period_fixture", sex, item.age(t))
                assert item.mort_be_trend(t) == 1.0 and item.mort_be_factor() == 0.75
                assert item.mort_rate_base(t) == rate
                assert item.mort_rate(t) == rate * 0.75
            line = raised_line(lambda: item.mort_rate_at_age(121))
            assert line.startswith("ValueError: table 'period_fixture': x 121 is outside")
        assert sexes == {"M", "F"}
    finally:
        model.close()


def test_the_hooks_pass_the_birth_year_on(tmp_path):
    folder = switched_copy(tmp_path, "gen_fixture", birth_year=1975)
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedGenProbe")
    try:
        item, tables = model.Projection[1], model.CoreTables
        sex = item.sex()
        trend = float(FIXTURE_VALUES["gen_fixture"][sex.lower() + "_trend"])
        assert item.birth_year() == 1975
        rate = item.mort_rate_at_age(50)
        assert rate == tables.q("gen_fixture", sex, 50, 1975)
        assert rate == law(sex, 50) * (1.0 - trend) ** (1975 + 50 - 1999)
        assert item.omega_age_table() == 121
    finally:
        model.close()


def test_a_generational_table_without_a_birth_year_cell_raises(tmp_path):
    folder = switched_copy(tmp_path, "gen_fixture")
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedNoBirthProbe")
    try:
        line = raised_line(lambda: model.Projection[1].mort_rate_at_age(50))
        assert line == ("ValueError: table 'gen_fixture': birth_year is missing, the table is"
                        " generational")
    finally:
        model.close()


def test_a_chosen_table_the_factory_does_not_hold_raises(tmp_path):
    folder = switched_copy(tmp_path, "dav2004r_proxy")
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedUnknownProbe")
    try:
        item = model.Projection[1]
        for call in (lambda: item.mort_rate_at_age(50), lambda: item.mort_rate(item.t_start())):
            assert raised_line(call) == "ValueError: table 'dav2004r_proxy' is not defined"
    finally:
        model.close()


# Index' own ``mort_be_factor`` is 0.75, a factor below 1; the copy adds a trend term and a load.
THRU_CELLS = '''
def mort_be_trend(t):
    """A fixture best-estimate trend term below 1.

    Override reason: test fixture, tests/test_tables.py
    """
    return 0.5


def mort_load_tariff(t):
    """A fixture loading above 1.

    Override reason: test fixture, tests/test_tables.py
    """
    return 1.25

'''


def test_a_table_rate_of_1_passes_through_the_factor_and_the_load(tmp_path):
    # the fixture table closes at 66, the last age an Index point attains (ret_age 67)
    folder = switched_copy(tmp_path, "period_fixture")
    model_dir = folder / MODELS[INDEX]
    tables_path = model_dir / "CoreData" / TABLES_FILE
    text = tables_path.read_text(encoding="utf-8")
    assert text.count("period_fixture_end_age,121,") == 1
    tables_path.write_text(text.replace("period_fixture_end_age,121,",
                                        "period_fixture_end_age,67,"), encoding="utf-8")
    add_cells(model_dir / "Projection" / "__init__.py", THRU_CELLS)
    model = mx.read_model(model_dir, name="ThruProbe")
    try:
        cells = model.Projection.cells
        assert not cells["mort_be_factor"]._is_derived()
        assert not cells["mort_be_trend"]._is_derived()
        assert not cells["mort_load_tariff"]._is_derived()
        for name in ("mort_rate_base", "mort_rate", "mort_rate_tariff_base", "mort_rate_tariff"):
            assert cells[name]._is_derived(), name
        points = model.Data.model_point_table()
        sexes = set()
        for point_id in points.index[:4]:
            item = model.Projection[point_id]
            sexes.add(item.sex())
            assert item.omega_age_table() == 67 == item.ret_age()
            last = item.proj_len() - 1
            assert item.age(last) == 66
            # at the closing age, end age minus one: 1, not the factor, the trend or the load
            assert item.mort_rate_base(last) == 1.0 == item.mort_rate_tariff_base(last)
            assert item.mort_be_factor() == 0.75 and item.mort_load_tariff(last) == 1.25
            assert item.mort_be_trend(last) == 0.5 == item.mort_be_trend(last - 12)
            assert item.mort_rate(last) == 1.0
            assert item.mort_rate_tariff(last) == 1.0
            # the year before, the factor and the load act on the table rate
            before = last - 12
            assert item.age(before) == 65
            rate = law(item.sex(), 65)
            blend = 0.45 * law("M", 65) + (1.0 - 0.45) * law("F", 65)
            assert item.mort_rate_base(before) == rate < 1.0
            assert item.mort_rate(before) == rate * 0.75 * 0.5
            assert item.mort_rate_tariff_base(before) == blend < 1.0
            assert item.mort_rate_tariff(before) == 1.25 * blend
        assert sexes == {"M", "F"}
    finally:
        model.close()


def test_a_switched_copy_runs_through_both_engines(tmp_path, monkeypatch):
    folder = switched_copy(tmp_path, "period_fixture")
    runner = load_runner()
    traced = runner.run_product(folder, engine="modelx")
    shipped = runner.run_product(PRODUCTS_DIR / INDEX, engine="modelx")
    (count, checks, sha, failures, _lines, digests), after, at_end = run_spying_on_the_factory(
        folder, monkeypatch)
    assert failures == [] and traced[3] == []
    assert (count, checks, sha, digests) == (traced[0], traced[1], traced[2], traced[5])
    assert sha != shipped[2]
    assert after[1] and after[1].items() <= at_end.items()
    assert all(key[0] == "period_fixture" and key[3] is None for key in at_end)
    # the shipped choice is replaced in the copy: no rate of the shipped table is read
    assert not [key for key in at_end if key[0] in SHIPPED_TABLES]


# --------------------------------------------------------------------------- the usage scan

def fixture_items(table: str) -> tuple[str, ...]:
    """The items of a fixture table, as its definition names them."""
    return tuple(f"{table}_{name}" for name in FIXTURE_DEFINITIONS[table][2])


def choosing_copy(tmp_path: Path, table: str, file: str = "param_tariff_type.csv") -> Path:
    """A scratch copy of Index with the fixture tables that chooses ``table`` as its
    ``mort_table`` in ``file``, in place of the shipped choice, and is otherwise clean in the
    usage scan: ``switched_copy`` without its row ``unisex_mix_male``, which no reachable
    cell of Index reads."""
    folder = switched_copy(tmp_path, table)
    path = folder / "param_tariff_type.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    choice = [row for row in rows if row.startswith("mort_table,")]
    dropped = [row for row in rows if row.startswith(("unisex_mix_male,", "mort_table,"))]
    assert len(choice) == 1 and len(dropped) == 2
    path.write_text("".join(row for row in rows if row not in dropped), encoding="utf-8")
    _add_params(folder / file, {"mort_table": table})
    return folder


def scan_of(folder: Path, name: str, edit=None):
    """The usage scan of a scratch copy of Index, after ``edit(model)`` changed its model."""
    model = mx.read_model(folder / MODELS[INDEX], name=name)
    try:
        if edit is not None:
            edit(model)
        return param_usage.scan(model)
    finally:
        model.close()


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_scan_of_a_shipped_product_holds_the_tables_and_no_problem(product, product_models):
    usage = param_usage.scan(product_models(product))
    assert usage.problems == []
    assert usage.tables == SHIPPED_ITEMS
    assert usage.layers["tables"] == SHIPPED_LAYER
    read = set(usage.reads) & set(usage.layers["tables"])
    if product in SWITCHED:
        table = SWITCHED[product]
        assert usage.choices == {"mort_table": table}
        readers = usage.reads["mort_table"]
        assert readers == {"mort_table_name"} and readers <= usage.reachable
        assert read == set(SHIPPED_ITEMS[table])
        for item in SHIPPED_ITEMS[table]:
            assert usage.reads[item] == readers, item
    else:
        assert usage.choices == {} and read == set()
        assert "mort_table" not in usage.reads


def test_no_table_is_unchosen_in_the_ten_products(product_models):
    usages = [param_usage.scan(product_models(product)) for product in sorted(MODELS)]
    assert len(usages) == 10
    assert param_usage.unchosen_tables(usages) == []
    chosen = {table for usage in usages for table in usage.choices.values()}
    assert chosen == set(SHIPPED_TABLES) == set(SWITCHED.values())
    # without the products that chose it, the table would be reported
    others = [param_usage.scan(product_models(product)) for product in sorted(MODELS)
              if product not in SWITCHED]
    assert param_usage.unchosen_tables(others) == sorted(SHIPPED_TABLES)


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_the_scan_counts_the_items_of_a_chosen_table_as_read(tmp_path, file):
    usage = scan_of(choosing_copy(tmp_path, "period_fixture", file), "ChosenScanProbe")
    assert usage.problems == []
    assert usage.tables == SHIPPED_ITEMS | {table: fixture_items(table)
                                            for table in FIXTURE_DEFINITIONS}
    assert usage.choices == {"mort_table": "period_fixture"}
    readers = usage.reads["mort_table"]
    assert readers == {"mort_table_name"} and readers <= usage.reachable
    for item in fixture_items("period_fixture"):
        assert usage.reads[item] == readers, item
    read = set(usage.reads) & set(usage.layers["tables"])
    assert read == set(fixture_items("period_fixture"))
    assert len(usage.layers["tables"]) > len(read)


def test_the_scan_reads_no_tables_item_without_a_choice(tmp_path):
    usage = scan_of(unswitched_copy(tmp_path), "NoChoiceScanProbe")
    assert usage.problems == []
    assert list(usage.tables) == ALL_TABLES and usage.choices == {}
    assert usage.layers["tables"] and not set(usage.reads) & set(usage.layers["tables"])
    assert "mort_table" not in usage.reads


def test_the_scan_reads_no_item_of_a_table_whose_choice_no_cell_reads(tmp_path):
    folder = unswitched_copy(tmp_path)
    _add_params(folder / "param_tariff_type.csv", {"probe_table": "period_fixture"})
    usage = scan_of(folder, "UnreadChoiceScanProbe")
    assert usage.choices == {"probe_table": "period_fixture"}
    assert usage.problems == ["item 'probe_table' of the tariff_type layer"
                              " (param_tariff_type.csv) is read by no reachable cell"]
    assert not set(usage.reads) & set(usage.layers["tables"])
    assert param_usage.unchosen_tables([usage]) == sorted(ALL_TABLES)


def test_the_scan_reports_an_item_of_a_table_in_another_layer(tmp_path):
    """The item ``broken_fixture`` lacks in the tables layer, held by the tariff-type file:
    ``param`` would find it, the scan reports it."""
    folder = choosing_copy(tmp_path, "broken_fixture")
    _add_params(folder / "param_tariff_type.csv", {"broken_fixture_f_b": "1.092"})
    usage = scan_of(folder, "TableItemElsewhereScanProbe")
    assert usage.problems == [
        "item 'broken_fixture_f_b' of the table 'broken_fixture' stands in the tariff_type"
        " layer (param_tariff_type.csv), not in the tables layer"]


@pytest.mark.parametrize(("layer", "file"), [("core", "param_core.csv"),
                                             ("tables", TABLES_FILE)])
def test_the_scan_reports_a_table_choice_in_the_core_or_the_tables_file(tmp_path, layer, file):
    folder = unswitched_copy(tmp_path)
    _add_params(folder / MODELS[INDEX] / "CoreData" / file, {"mort_table": "period_fixture"})
    usage = scan_of(folder, "ChoiceElsewhereScanProbe")
    assert usage.choices == {}
    assert (f"item 'mort_table' of the {layer} layer ({file}) is a table choice outside the"
            f" tariff-type and tariff files") in usage.problems
    assert len(usage.problems) == (1 if layer == "core" else 2)
    assert not set(usage.reads) & set(fixture_items("period_fixture"))


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_the_scan_reports_a_chosen_name_the_factory_lacks(tmp_path, file):
    usage = scan_of(choosing_copy(tmp_path, "nosuch_table", file), "UnknownChoiceScanProbe")
    layer = "tariff" if file == "param_tariff.csv" else "tariff_type"
    assert usage.problems == [f"item 'mort_table' of the {layer} layer ({file}) names the"
                              f" table 'nosuch_table', which the factory does not hold"]
    assert usage.choices == {"mort_table": "nosuch_table"}
    assert not set(usage.reads) & set(usage.layers["tables"])


def test_the_scan_reports_a_tables_item_of_no_table(tmp_path):
    """A row that is no table's item, and one that starts with a table's name but is not
    among the items its definition names."""
    folder = choosing_copy(tmp_path, "period_fixture")
    _add_params(tables_file(folder, INDEX), {"stray_item": "1.5", "period_fixture_m_c": "2"})
    usage = scan_of(folder, "StrayItemScanProbe")
    assert usage.problems == [
        "item 'stray_item' of the tables layer (param_tables.csv) belongs to no table",
        "item 'period_fixture_m_c' of the tables layer (param_tables.csv) belongs to no table"]
    assert "stray_item" not in usage.reads and "period_fixture_m_c" not in usage.reads


def test_the_scan_reports_an_item_a_chosen_table_names_and_the_layer_lacks(tmp_path):
    usage = scan_of(choosing_copy(tmp_path, "broken_fixture"), "BrokenTableScanProbe")
    assert usage.problems == [
        "item 'broken_fixture_f_b' read by mort_table_name stands in no layer"]
    assert set(fixture_items("broken_fixture")) <= set(usage.reads)


def test_the_scan_reports_a_cell_reading_a_tables_item_directly(tmp_path):
    """By a literal call and by a declared indirect read; the table stays unchosen. The
    copy keeps the shipped choice, whose table is read through the factory."""
    def edit(model):
        model.Projection.new_cells(
            name="probe_direct",
            formula='def probe_direct():\n    return data.param("gen_fixture_m_a")\n')
        model.Projection.new_cells(
            name="probe_declared",
            formula='def probe_declared():\n    name = "gen_fixture_f_a"\n'
                    '    return data.param(name)\n')
        model.Data.cells["param_indirect"].formula = (
            'def param_indirect():\n    return {"probe_declared": ("gen_fixture_f_a",)}\n')

    usage = scan_of(fixture_copy(tmp_path), "DirectTablesReadScanProbe", edit)
    assert usage.problems == [
        "cell probe_declared reads the item 'gen_fixture_f_a' of the tables layer directly,"
        " not through the table factory",
        "cell probe_direct reads the item 'gen_fixture_m_a' of the tables layer directly,"
        " not through the table factory"]
    assert param_usage.unchosen_tables([usage]) == sorted(FIXTURE_DEFINITIONS)


def test_the_scan_reports_a_product_defined_tables_path(tmp_path):
    def edit(model):
        model.Data.cells["param_tables_path"].formula = (
            'def param_tables_path():\n'
            '    return _model.path / "CoreData" / "param_tables.csv"\n')
        assert model.Data.cells["param_tables_path"]._is_defined()

    usage = scan_of(choosing_copy(tmp_path, "period_fixture"), "TablesPathScanProbe", edit)
    assert usage.problems == ["Data defines param_tables_path; the table parameter file is the"
                              " core's param_tables.csv beside its loaders"]


def test_the_scan_reports_a_read_around_param_through_the_tables_path(tmp_path):
    def edit(model):
        model.Projection.new_cells(
            name="probe_path",
            formula="def probe_path():\n    return data.param_tables_path()\n")

    usage = scan_of(choosing_copy(tmp_path, "period_fixture"), "TablesBypassScanProbe", edit)
    assert usage.problems == [
        "cell probe_path reads the parameters around param(): param_tables_path"]


def test_unchosen_tables_names_the_tables_no_model_chooses(tmp_path):
    others = sorted(set(ALL_TABLES) - {"period_fixture"})
    period = scan_of(choosing_copy(tmp_path / "period", "period_fixture"), "UnchosenProbeA")
    assert param_usage.unchosen_tables([period]) == others
    gen = scan_of(choosing_copy(tmp_path / "gen", "gen_fixture"), "UnchosenProbeB")
    none = scan_of(unswitched_copy(tmp_path / "none"), "UnchosenProbeC")
    assert param_usage.unchosen_tables([none]) == sorted(ALL_TABLES)
    assert param_usage.unchosen_tables([none, period, gen]) == sorted(
        set(others) - {"gen_fixture"})
    # the copy with the shipped choice chooses the shipped table and no fixture table
    shipped = scan_of(fixture_copy(tmp_path / "shipped"), "UnchosenProbeD")
    assert param_usage.unchosen_tables([shipped]) == sorted(FIXTURE_DEFINITIONS)
    assert param_usage.unchosen_tables([none, period, gen, shipped]) == sorted(
        set(FIXTURE_DEFINITIONS) - {"period_fixture", "gen_fixture"})
    assert param_usage.unchosen_tables([]) == []
