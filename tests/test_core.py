"""The common core of phase 3 (``docs/core.md``): grep test, override reasons, trace.

- No file under ``core/`` names a product: no product folder name, model name or model
  prefix as a case-sensitive whole word.
- A product cell that redefines a cell of a core base carries an ``Override reason:`` line
  in its docstring.
- RLV takes ``model_point`` from the core, and the traced modelx model shows it.
- Every product has the core spaces as bases, and every cell unified into the core
  (``CORE_CELLS``) is defined in the core and, in each product that has it, either derived
  from the core or overridden (with the reason the override test requires).
- The time axis: RLV's derived ``age`` and ``policy_year`` follow the inception clock, BU's
  overrides floor them before inception, Sofort's ``age`` reads the second life.
"""
from __future__ import annotations

import hashlib
import io
import re
import subprocess
from pathlib import Path

import modelx as mx
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT / "core"
CORE_MODEL = CORE_DIR / "Core"
PRODUCTS_DIR = ROOT / "products"

# Product folder -> model folder; the same ten products as tests/test_provenance.py.
MODELS = {
    "basisrente": "Basis_DE_S",
    "berufsunfaehigkeit": "BU_DE_S",
    "fondsgebundene_rentenversicherung": "FRV_DE_S",
    "indexpolice": "Index_DE_S",
    "kapitallebensversicherung": "KLV_DE_S",
    "klassische_rentenversicherung": "RV_DE_S",
    "pflegerentenversicherung": "Pflege_DE_S",
    "riester_rente": "Riester_DE_S",
    "risikolebensversicherung": "RLV_DE_S",
    "sofortrente": "Sofort_DE_S",
}
MODEL_PREFIXES = ("Basis", "BU", "FRV", "Index", "KLV", "RV", "Pflege", "Riester", "RLV", "Sofort")
FORBIDDEN = sorted(set(MODELS) | set(MODELS.values()) | set(MODEL_PREFIXES))
FORBIDDEN_RE = re.compile(r"\b(" + "|".join(map(re.escape, FORBIDDEN)) + r")\b")
OVERRIDE_REASON_RE = re.compile(r"^\s*Override reason:\s*\S", re.MULTILINE)
CORE_PREFIX = "Core"


def core_files() -> list[Path]:
    return sorted(p for p in CORE_DIR.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def test_the_core_is_a_model_with_data_and_projection():
    assert (CORE_MODEL / "_system.json").is_file()
    model = mx.read_model(CORE_MODEL)
    try:
        assert sorted(model.spaces) == ["Data", "Projection"]
        assert model.Projection.formula.parameters == ("point_id",)
    finally:
        model.close()


def test_no_core_file_names_a_product():
    files = core_files()
    assert files, "core/ holds no file"
    found = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in FORBIDDEN_RE.finditer(text):
            found.append(f"{path.relative_to(ROOT)}: {match.group(1)}")
    assert not found, "core files name a product:\n" + "\n".join(found)


def test_the_grep_finds_every_forbidden_word():
    for word in FORBIDDEN:
        assert FORBIDDEN_RE.search(f"see {word}.") is not None, word
    assert FORBIDDEN_RE.search("Indexed BUT rv basis_x") is None


def core_bases(space) -> list:
    """The bases of a product space that are core spaces in the product's model."""
    return [base for base in space.bases if base.name.startswith(CORE_PREFIX)]


def override_violations(model) -> list[str]:
    """``space.cell`` for every override of a core cell without an ``Override reason:`` line."""
    violations = []
    for space in model.spaces.values():
        if space.name.startswith(CORE_PREFIX):
            continue
        bases = core_bases(space)
        if not bases:
            continue
        for name, cell in space.cells.items():
            if not cell._is_defined():
                continue
            if not any(name in base.cells for base in bases):
                continue
            if not OVERRIDE_REASON_RE.search(cell.doc or ""):
                violations.append(f"{space.name}.{name}")
    return violations


def products_with_core() -> list[str]:
    """Products whose model folder holds a core space (``Core…``)."""
    return sorted(product for product, model in MODELS.items()
                  if any(p.name.startswith(CORE_PREFIX)
                         for p in (PRODUCTS_DIR / product / model).iterdir()))


def test_every_product_has_a_core_base():
    assert products_with_core() == sorted(MODELS)


@pytest.fixture(scope="module")
def product_models():
    """Every product's modelx model, read once for this module and closed afterwards."""
    models = {}

    def read(product):
        if product not in models:
            models[product] = mx.read_model(PRODUCTS_DIR / product / MODELS[product])
        return models[product]

    yield read
    for model in models.values():
        model.close()


@pytest.mark.parametrize("product", products_with_core())
def test_every_override_of_a_core_cell_has_a_reason(product, product_models):
    model = product_models(product)
    assert any(core_bases(space) for space in model.spaces.values()), product
    violations = override_violations(model)
    assert not violations, f"{product}: overrides without 'Override reason:': {violations}"


@pytest.mark.parametrize("product", sorted(MODELS))
def test_data_and_projection_have_the_core_spaces_as_bases(product, product_models):
    model = product_models(product)
    assert model.Data.bases == [model.CoreData]
    assert model.Projection.bases == [model.CoreProjection]


# Cells unified into the core: space -> cell -> {product: "derived" or "override"}. The core
# defines each cell once; a product derives it or overrides it, an override with its reason
# (test_every_override_of_a_core_cell_has_a_reason). A product not named did not have the
# cell before; it inherits the core cell unused, so it must not define it either.
CORE_CELLS = {
    "Data": {
        "input_dir": dict.fromkeys(MODELS, "derived"),
        "model_point_table": dict.fromkeys(MODELS, "derived"),
        "param_table": {"berufsunfaehigkeit": "derived",
                        "klassische_rentenversicherung": "derived",
                        "pflegerentenversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "mort_table": {"basisrente": "override",
                       "berufsunfaehigkeit": "override",
                       "fondsgebundene_rentenversicherung": "override",
                       "indexpolice": "derived",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "derived",
                       "pflegerentenversicherung": "derived",
                       "riester_rente": "override",
                       "risikolebensversicherung": "override",
                       "sofortrente": "override"},
        "lapse_table": {"berufsunfaehigkeit": "derived",
                        "fondsgebundene_rentenversicherung": "derived",
                        "indexpolice": "override",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "override",
                        "pflegerentenversicherung": "derived",
                        "riester_rente": "override",
                        "risikolebensversicherung": "derived"},
        "rentenfaktor_table": {"basisrente": "derived",
                               "fondsgebundene_rentenversicherung": "override",
                               "klassische_rentenversicherung": "derived"},
        "freq_loading_table": {"berufsunfaehigkeit": "override",
                               "indexpolice": "derived",
                               "kapitallebensversicherung": "derived",
                               "klassische_rentenversicherung": "derived",
                               "riester_rente": "derived",
                               "risikolebensversicherung": "derived"},
    },
    "Projection": {
        "model_point": dict.fromkeys(MODELS, "derived"),
        "issue_age": {**dict.fromkeys(MODELS, "derived"), "sofortrente": "override"},
        "sex": {"berufsunfaehigkeit": "derived",
                "fondsgebundene_rentenversicherung": "derived",
                "indexpolice": "derived",
                "kapitallebensversicherung": "derived",
                "klassische_rentenversicherung": "derived",
                "pflegerentenversicherung": "derived",
                "riester_rente": "derived",
                "risikolebensversicherung": "derived",
                "sofortrente": "override"},
        "smoker": {"kapitallebensversicherung": "derived",
                   "risikolebensversicherung": "override"},
        "policy_term": {"kapitallebensversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "prem_term": {"kapitallebensversicherung": "derived",
                      "risikolebensversicherung": "override"},
        "prem_term_y": {"fondsgebundene_rentenversicherung": "derived",
                        "indexpolice": "derived",
                        "klassische_rentenversicherung": "derived"},
        "issue_year": {"basisrente": "derived",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "derived",
                       "sofortrente": "derived"},
        "duration_init": {"basisrente": "derived",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "derived",
                          "riester_rente": "derived",
                          "risikolebensversicherung": "derived"},
        "duration_mth_init": {"berufsunfaehigkeit": "derived",
                              "fondsgebundene_rentenversicherung": "derived",
                              "pflegerentenversicherung": "derived",
                              "sofortrente": "derived"},
        "k_start": {"basisrente": "override",
                    "indexpolice": "derived",
                    "kapitallebensversicherung": "derived",
                    "klassische_rentenversicherung": "derived",
                    "riester_rente": "override"},
        "t_start": {"fondsgebundene_rentenversicherung": "override",
                    "indexpolice": "derived",
                    "kapitallebensversicherung": "derived",
                    "klassische_rentenversicherung": "derived",
                    "pflegerentenversicherung": "override",
                    "risikolebensversicherung": "derived",
                    "sofortrente": "override"},
        "proj_year": {"basisrente": "derived",
                      "riester_rente": "derived"},
        "duration_mth": {"basisrente": "override",
                         "berufsunfaehigkeit": "override",
                         "indexpolice": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived",
                         "pflegerentenversicherung": "derived",
                         "riester_rente": "override",
                         "risikolebensversicherung": "derived",
                         "sofortrente": "derived"},
        "duration": {"basisrente": "derived",
                     "indexpolice": "derived",
                     "kapitallebensversicherung": "derived",
                     "klassische_rentenversicherung": "derived",
                     "riester_rente": "derived",
                     "risikolebensversicherung": "derived",
                     "sofortrente": "derived"},
        "duration_y": {"basisrente": "derived",
                       "riester_rente": "derived"},
        "policy_year": {"basisrente": "derived",
                        "berufsunfaehigkeit": "override",
                        "fondsgebundene_rentenversicherung": "derived",
                        "indexpolice": "derived",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "derived",
                        "pflegerentenversicherung": "derived",
                        "risikolebensversicherung": "derived",
                        "sofortrente": "derived"},
        "age_y": {"basisrente": "override",
                  "indexpolice": "derived",
                  "kapitallebensversicherung": "derived",
                  "klassische_rentenversicherung": "derived",
                  "riester_rente": "override"},
        "age": {"basisrente": "override",
                "berufsunfaehigkeit": "override",
                "fondsgebundene_rentenversicherung": "derived",
                "indexpolice": "derived",
                "kapitallebensversicherung": "derived",
                "klassische_rentenversicherung": "derived",
                "pflegerentenversicherung": "derived",
                "riester_rente": "override",
                "risikolebensversicherung": "derived",
                "sofortrente": "override"},
        "proj_len_y": {"basisrente": "override",
                       "indexpolice": "override",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "override",
                       "riester_rente": "override",
                       "risikolebensversicherung": "derived"},
        "proj_len": {"basisrente": "derived",
                     "berufsunfaehigkeit": "override",
                     "fondsgebundene_rentenversicherung": "override",
                     "indexpolice": "derived",
                     "kapitallebensversicherung": "derived",
                     "klassische_rentenversicherung": "derived",
                     "pflegerentenversicherung": "override",
                     "riester_rente": "derived",
                     "risikolebensversicherung": "derived",
                     "sofortrente": "override"},
        "calendar_year_y": {"basisrente": "override",
                            "klassische_rentenversicherung": "derived",
                            "riester_rente": "override"},
        "calendar_year": {"basisrente": "override",
                          "klassische_rentenversicherung": "derived",
                          "riester_rente": "override",
                          "sofortrente": "derived"},
        "rechnungszins": {"basisrente": "derived",
                          "berufsunfaehigkeit": "override",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "derived",
                          "pflegerentenversicherung": "override",
                          "riester_rente": "derived",
                          "risikolebensversicherung": "override",
                          "sofortrente": "derived"},
        "disc_factor_mth": {"berufsunfaehigkeit": "derived",
                            "pflegerentenversicherung": "derived"},
    },
}


def core_cell_cases():
    return [(space, cell, product, kind)
            for space, cells in CORE_CELLS.items()
            for cell, products in cells.items()
            for product, kind in ((p, products.get(p, "absent")) for p in sorted(MODELS))]


def test_every_unified_cell_is_defined_in_the_core():
    model = mx.read_model(CORE_MODEL)
    try:
        for space, cells in CORE_CELLS.items():
            for cell in cells:
                assert model.spaces[space].cells[cell]._is_defined(), f"{space}.{cell}"
    finally:
        model.close()


@pytest.mark.parametrize("space, cell, product, kind", core_cell_cases())
def test_a_unified_cell_is_derived_or_overridden(space, cell, product, kind, product_models):
    model = product_models(product)
    product_cell = model.spaces[space].cells[cell]
    core_cell = model.spaces["Core" + space].cells[cell]
    if kind in ("derived", "absent"):
        assert product_cell._is_derived(), f"{product}: {space}.{cell} is not derived"
        assert product_cell.formula is core_cell.formula
    else:
        assert product_cell._is_defined(), f"{product}: {space}.{cell} is not overridden"
        assert OVERRIDE_REASON_RE.search(product_cell.doc or "")



def _core_cell():
    """The core's version."""
    return 1


def _override_without_reason():
    """A product's version."""
    return 2


def _override_with_reason():
    """A product's version.

    Override reason: the product differs, docs/core.md
    """
    return 2


def _override_with_empty_reason():
    """A product's version.

    Override reason:
    """
    return 2


def test_override_test_catches_a_missing_reason():
    model = mx.new_model("OverrideProbe")
    try:
        core = model.new_space("CoreProjection")
        core.new_cells("cell", formula=_core_cell)
        core.new_cells("other", formula=_core_cell)
        projection = model.new_space("Projection", bases=core)
        projection.new_cells("own", formula=_override_without_reason)
        assert override_violations(model) == []
        projection.cells["cell"].formula = _override_without_reason
        assert override_violations(model) == ["Projection.cell"]
        projection.cells["cell"].formula = _override_with_empty_reason
        assert override_violations(model) == ["Projection.cell"]
        projection.cells["cell"].formula = _override_with_reason
        assert override_violations(model) == []
    finally:
        model.close()


def test_rlv_takes_model_point_from_the_core(product_models):
    model = product_models("risikolebensversicherung")
    assert model.Projection.bases == [model.CoreProjection]
    assert model.Data.bases == [model.CoreData]
    cell = model.Projection.model_point
    assert cell._is_derived()
    assert cell.formula is model.CoreProjection.model_point.formula
    assert model.Projection[1].model_point()["policy_id"] == "RLV-000001"


# The last commit before the Pflege merge; its basis_table.csv and expense_table.csv are
# upstream's bytes (checked against the hashes in UPSTREAM.md).
PRE_MERGE_REVISION = "34938cec06fa412fe0af0c3a484f7e1551c87c89"


def upstream_table(product: str, name: str, **read_csv) -> pd.DataFrame:
    """A file phase 3 removed, read from git at ``PRE_MERGE_REVISION``, hash-checked."""
    data = subprocess.run(
        ["git", "show", f"{PRE_MERGE_REVISION}:products/{product}/{name}"],
        cwd=ROOT, check=True, capture_output=True).stdout
    upstream = (PRODUCTS_DIR / product / "UPSTREAM.md").read_text(encoding="utf-8")
    assert f"| `{name}` | `{hashlib.sha256(data).hexdigest()}` |" in upstream, name
    return pd.read_csv(io.BytesIO(data), **read_csv)


def test_pflege_param_table_holds_the_two_merged_tables(product_models):
    product = "pflegerentenversicherung"
    model = product_models(product)
    assert model.Data.param_table._is_derived()
    merged = model.Data.param_table()
    basis = upstream_table(product, "basis_table.csv", index_col="param")
    expense = upstream_table(product, "expense_table.csv", index_col="item")
    assert list(merged.columns) == ["value", "unit", "provenance"]
    assert list(merged.index) == list(basis.index) + list(expense.index)
    for item in basis.index:
        assert merged.at[item, "value"] == basis.at[item, "value"], item
        assert pd.isna(merged.at[item, "unit"]), item
        assert merged.at[item, "provenance"] == basis.at[item, "provenance"], item
    for item in expense.index:
        for column in ("value", "unit", "provenance"):
            assert merged.at[item, column] == expense.at[item, column], (item, column)


def test_sofort_issue_age_reads_the_second_life_from_surv_age(product_models):
    model = product_models("sofortrente")
    projection = model.Projection
    assert projection.issue_age._is_defined()
    points = model.Data.model_point_table()
    joint = points.index[points["surv_pct"] > 0]
    assert len(joint), "no joint-life model point"
    for point_id in joint:
        item = projection[point_id]
        assert item.issue_age() == int(points.at[point_id, "issue_age"])
        assert item.issue_age(1) == int(points.at[point_id, "issue_age"])
        assert item.issue_age(2) == int(points.at[point_id, "surv_age"])


def test_rlv_age_and_policy_year_follow_the_inception_clock(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.age._is_derived()
    assert projection.policy_year._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in (points.index[0], in_force[0]):
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            assert item.age(t) == item.issue_age() + t // 12, (point_id, t)
            assert item.policy_year(t) == t // 12 + 1, (point_id, t)


def test_bu_policy_year_and_age_are_floored_before_inception(product_models):
    model = product_models("berufsunfaehigkeit")
    projection = model.Projection
    assert projection.policy_year._is_defined()
    assert projection.age._is_defined()
    points = model.Data.model_point_table()
    new = points.index[points["duration_mth_init"] == 0]
    assert len(new), "no new-business model point"
    item = projection[new[0]]
    assert item.policy_year(-30) == 1
    assert item.age(-30) == item.issue_age()


def test_sofort_age_reads_the_second_life_from_surv_age(product_models):
    model = product_models("sofortrente")
    projection = model.Projection
    assert projection.age._is_defined()
    points = model.Data.model_point_table()
    joint = points.index[points["surv_pct"] > 0]
    assert len(joint), "no joint-life model point"
    for point_id in joint:
        item = projection[point_id]
        assert item.age(0) == int(points.at[point_id, "issue_age"])
        assert item.age(0, 2) == int(points.at[point_id, "surv_age"])
        assert item.age(24, 2) == int(points.at[point_id, "surv_age"]) + 2
