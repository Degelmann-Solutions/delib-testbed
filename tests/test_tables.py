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

The space ``core/Core/Tables``:

- Every product holds it as the symlink ``CoreTables``, lists it in ``_spaces`` and names it
  as a base of no space; its ``Projection`` reads it through the Reference ``tables``, the
  space reads the product's ``Data`` through ``data``, takes no parameter and holds the
  core's cells and no other, so no product defines one.
- Its source holds no numeric literal but 0 and 1 and no cell name containing ``mort`` or
  ``q`` besides ``q``, and its cells read only ``data.param`` and each other.
- No table is defined: ``q`` raises a ``ValueError`` naming the table for any name, in every
  product.
- On a scratch copy of Index with fixture tables and laws written into its ``CoreTables``
  and ``param_tables.csv`` (``fixture_copy``): the period table gives its law's rate
  unrounded, 1 at the last age and at most 1; an age outside the table, another sex, a
  missing or a refused ``birth_year`` or ``duration`` and a duration below 1 raise, naming
  the table and the argument; the generational table applies its trend from its base year
  to the calendar year ``birth_year + x`` and not to the closure; the select table applies
  the factor of the duration and holds the last; a table naming an item the layer lacks
  raises the loader's ``KeyError``; ``items()`` lists every table's items.
- The runner's export engine, running the copy's points with per-contract cleanup, computes
  the same results as the modelx engine and keeps the rates of an earlier point in
  ``CoreTables`` after the point's item is deleted.
"""
from __future__ import annotations

import ast
import builtins
import importlib
import importlib.util
from pathlib import Path

import modelx as mx
import pytest

from test_core import (CORE_MODEL, MODELS, PRODUCTS_DIR, ROOT, _add_params, _formula_cells,
                       _loader_error, product_copy)

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


# --------------------------------------------------------------------------- the space

TABLES_SOURCE = CORE_MODEL / "Tables" / "__init__.py"
TABLES_CELLS = ["definitions", "definition", "items", "parameter", "first_age", "end_age",
                "base_year", "select_factors", "base_rate", "trend", "q"]


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
        assert tables.definitions() == {} and tables.items() == {}
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
@pytest.mark.parametrize("table", ["dav2008t_proxy", "nosuch"])
def test_no_table_is_defined_in_a_shipped_product(product, table, product_models):
    tables = product_models(product).CoreTables
    assert tables.definitions() == {}
    line = raised_line(lambda: tables.q(table, "M", 40))
    assert line == f"ValueError: table {table!r} is not defined"
    assert raised_line(lambda: tables.end_age(table)).startswith("KeyError")


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
# and names that are none of the tables the factory will hold.
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
}
MARKER = "# " + "-" * 75 + "\n# References"
INDEX = "indexpolice"


def write_fixture_tables(model_dir: Path) -> None:
    """Write the fixture tables into a scratch copy: their definitions and laws into its
    ``CoreTables`` and their numbers into its ``param_tables.csv``."""
    path = model_dir / "CoreTables" / "__init__.py"
    assert path.is_file() and not (model_dir / "CoreTables").is_symlink()
    text = path.read_text(encoding="utf-8")
    assert text.count("    return {}\n") == 1 and text.count(MARKER) == 1
    entries = "".join(f"        {table!r}: ({law}, {trend}, {names!r}),\n"
                      for table, (law, trend, names) in FIXTURE_DEFINITIONS.items())
    text = text.replace("    return {}\n", "    return {\n" + entries + "    }\n")
    path.write_text(text.replace(MARKER, FIXTURE_LAWS.lstrip("\n") + "\n" + MARKER),
                    encoding="utf-8")
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
    assert list(fixture_tables.definitions()) == list(FIXTURE_DEFINITIONS)
    assert "law_fixture" not in TABLES_SOURCE.read_text(encoding="utf-8")
    assert (CORE_MODEL / "Data" / TABLES_FILE).read_text(
        encoding="utf-8") == "item,value,basis,provenance\n"
    known = ("dav2008t_proxy", "dav2008t_nr_proxy", "dav2008t_r_proxy", "dav2004r_proxy",
             "dav1997ti_proxy", "pflege_aktive_proxy")
    assert not set(FIXTURE_DEFINITIONS) & set(known)
    assert not any(name.endswith("_proxy") for name in FIXTURE_DEFINITIONS)


def test_items_lists_the_items_of_every_table(fixture_tables):
    items = fixture_tables.items()
    assert list(items) == list(FIXTURE_DEFINITIONS)
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


# --------------------------------------------------------------------------- the runner

def load_runner():
    spec = importlib.util.spec_from_file_location("run_baseline",
                                                  ROOT / "tools" / "run_baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_cell(path: Path, name: str, source: str) -> None:
    """Replace the module-level cell ``name`` of a space file by ``source`` ('' deletes it)."""
    text = path.read_text(encoding="utf-8")
    cells = [node for node in ast.parse(text).body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(cells) == 1, name
    lines = text.splitlines(keepends=True)
    lines[cells[0].lineno - 1:cells[0].end_lineno] = [source]
    path.write_text("".join(lines), encoding="utf-8")


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
    """Index' own table lookup replaced, in the copy, by a read of the period fixture table:
    the two engines agree, and the rates point 1 computed are still held after its item and
    every later point's item are deleted."""
    folder = fixture_copy(tmp_path)
    replace_cell(folder / MODELS[INDEX] / "Projection" / "__init__.py", "mort_rate_at_age",
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
