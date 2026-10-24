"""The common core of phase 3 (``docs/core.md``): grep test, override reasons, trace.

- No file under ``core/`` names a product: no product folder name, model name or model
  prefix as a case-sensitive whole word.
- A product cell that redefines a cell of a core base carries an ``Override reason:`` line
  in its docstring.
- RLV takes ``model_point`` from the core, and the traced modelx model shows it.
"""
from __future__ import annotations

import re
from pathlib import Path

import modelx as mx
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


def test_at_least_one_product_has_a_core_base():
    assert "risikolebensversicherung" in products_with_core()


@pytest.mark.parametrize("product", products_with_core())
def test_every_override_of_a_core_cell_has_a_reason(product):
    model = mx.read_model(PRODUCTS_DIR / product / MODELS[product])
    try:
        assert any(core_bases(space) for space in model.spaces.values()), product
        violations = override_violations(model)
    finally:
        model.close()
    assert not violations, f"{product}: overrides without 'Override reason:': {violations}"


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


def test_rlv_takes_model_point_from_the_core():
    model = mx.read_model(PRODUCTS_DIR / "risikolebensversicherung" / "RLV_DE_S")
    try:
        assert model.Projection.bases == [model.CoreProjection]
        assert model.Data.bases == [model.CoreData]
        cell = model.Projection.model_point
        assert cell._is_derived()
        assert cell.formula is model.CoreProjection.model_point.formula
        assert model.Projection[1].model_point()["policy_id"] == "RLV-000001"
    finally:
        model.close()
