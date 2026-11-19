"""The common core of phase 3 (``docs/core.md``): grep test, override reasons, trace.

- No file under ``core/`` names a product: no product folder name, model name or model
  prefix as a case-sensitive whole word.
- A product cell that redefines a cell of a core base carries an ``Override reason:`` line
  in its docstring.
- RLV takes ``model_point`` from the core, and the traced modelx model shows it.
- Every product has the core spaces as bases, and every cell unified into the core
  (``CORE_CELLS``) is defined in the core and, in each product that has it, either derived
  from the core or overridden (with the reason the override test requires).
- Every product's core layer holds the items of ``CORE_ITEMS`` (``tests/helpers.py``) with
  their types, among them ``rate_cap_eps``, 1e-12 as a ``float``.
- Every model point of a product with a calendar year opens at the valuation date, the core
  item ``valuation_year``, and the core file has no unused item but the ones a test reads
  (``CORE_ITEMS_READ_BY_TESTS``).

The other themes of the core stand in the files ``tests/test_core_*.py``: the cells of the
``Projection`` (``test_core_projection.py``), the parameter files and their loader
(``test_core_param_files.py``), the moved References and formula literals
(``test_core_literals.py``), the usage scan (``test_core_param_usage.py``), the tables and
their lookups (``test_core_lookups.py``), the payment frequencies
(``test_core_frequencies.py``), Pflege (``test_core_pflege.py``) and BU's cohorts
(``test_core_bu.py``). What they share stands in ``tests/helpers.py``, the fixture
``product_models`` in ``tests/conftest.py``; the files sort before
``tests/test_core_quota.py``, so the models are read once and closed before it.
"""
from __future__ import annotations

import re
from pathlib import Path

import modelx as mx
import pytest

from helpers import CORE_DIR, CORE_ITEMS, CORE_MODEL, MODELS, PRODUCTS_DIR, ROOT, param_usage


MODEL_PREFIXES = ("Basis", "BU", "FRV", "Index", "KLV", "RV", "Pflege", "Riester", "RLV", "Sofort")
FORBIDDEN = sorted(set(MODELS) | set(MODELS.values()) | set(MODEL_PREFIXES))
FORBIDDEN_RE = re.compile(r"\b(" + "|".join(map(re.escape, FORBIDDEN)) + r")\b")
OVERRIDE_REASON_RE = re.compile(r"^\s*Override reason:\s*\S", re.MULTILINE)
CORE_PREFIX = "Core"


def core_files() -> list[Path]:
    return sorted(p for p in CORE_DIR.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def test_the_core_is_a_model_with_data_projection_and_tables():
    assert (CORE_MODEL / "_system.json").is_file()
    model = mx.read_model(CORE_MODEL)
    try:
        assert sorted(model.spaces) == ["Data", "Projection", "Tables"]
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
        "lapse_table_index": {"berufsunfaehigkeit": "derived",
                              "fondsgebundene_rentenversicherung": "derived",
                              "indexpolice": "override",
                              "kapitallebensversicherung": "derived",
                              "klassische_rentenversicherung": "derived",
                              "pflegerentenversicherung": "derived",
                              "riester_rente": "derived",
                              "risikolebensversicherung": "derived"},
        "lapse_table": {"berufsunfaehigkeit": "derived",
                        "fondsgebundene_rentenversicherung": "derived",
                        "indexpolice": "derived",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "derived",
                        "pflegerentenversicherung": "derived",
                        "riester_rente": "derived",
                        "risikolebensversicherung": "derived"},
        "rentenfaktor_table_index": {"basisrente": "derived",
                                     "fondsgebundene_rentenversicherung": "override",
                                     "klassische_rentenversicherung": "derived"},
        "rentenfaktor_table": {"basisrente": "derived",
                               "fondsgebundene_rentenversicherung": "derived",
                               "klassische_rentenversicherung": "derived"},
        "prem_freq_table": {"basisrente": "derived",
                            "berufsunfaehigkeit": "derived",
                            "fondsgebundene_rentenversicherung": "derived",
                            "indexpolice": "derived",
                            "kapitallebensversicherung": "derived",
                            "klassische_rentenversicherung": "derived",
                            "pflegerentenversicherung": "derived",
                            "riester_rente": "derived",
                            "risikolebensversicherung": "derived"},
        "surplus_table_index": {"basisrente": "derived",
                                "riester_rente": "derived"},
        "surplus_table": {"basisrente": "derived",
                          "riester_rente": "derived"},
        "charge_table_index": {"basisrente": "derived",
                               "fondsgebundene_rentenversicherung": "derived",
                               "klassische_rentenversicherung": "derived"},
        "charge_table": {"basisrente": "derived",
                         "fondsgebundene_rentenversicherung": "derived",
                         "klassische_rentenversicherung": "derived"},
        "charge_table_items": dict.fromkeys(MODELS, "derived"),
        "hoechstrechnungszins_table": {"sofortrente": "derived"},
        "model_point_table_dict": dict.fromkeys(MODELS, "derived"),
        "param_core_path": dict.fromkeys(MODELS, "derived"),
        "param_tables_path": dict.fromkeys(MODELS, "derived"),
        "param_tariff_path": dict.fromkeys(MODELS, "derived"),
        "param_paths": dict.fromkeys(MODELS, "derived"),
        "param_rows": dict.fromkeys(MODELS, "derived"),
        "param_layers": dict.fromkeys(MODELS, "derived"),
        "param_dict": dict.fromkeys(MODELS, "derived"),
        "param": dict.fromkeys(MODELS, "derived"),
        "param_indirect": dict.fromkeys(MODELS, "derived"),
        "lapse_table_dict": dict.fromkeys(MODELS, "derived"),
        "rentenfaktor_table_dict": dict.fromkeys(MODELS, "derived"),
        "prem_freq_table_dict": dict.fromkeys(MODELS, "derived"),
        "surplus_table_dict": dict.fromkeys(MODELS, "derived"),
        "charge_table_dict": dict.fromkeys(MODELS, "derived"),
        "hoechstrechnungszins_table_dict": dict.fromkeys(MODELS, "derived"),
    },
    "Projection": {
        "model_point": dict.fromkeys(MODELS, "derived"),
        "policy_id": {"fondsgebundene_rentenversicherung": "derived",
                      "indexpolice": "derived",
                      "kapitallebensversicherung": "derived",
                      "pflegerentenversicherung": "derived",
                      "risikolebensversicherung": "derived",
                      "sofortrente": "derived"},
        "sum_assured": {"fondsgebundene_rentenversicherung": "derived",
                        "kapitallebensversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "rating_factor": {"berufsunfaehigkeit": "derived",
                          "kapitallebensversicherung": "derived",
                          "pflegerentenversicherung": "derived",
                          "risikolebensversicherung": "derived"},
        "scenario_id": {"basisrente": "derived",
                        "fondsgebundene_rentenversicherung": "derived",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "derived",
                        "riester_rente": "derived"},
        "karenz_months": {"berufsunfaehigkeit": "derived",
                          "pflegerentenversicherung": "derived"},
        "prem_freq": {"basisrente": "derived",
                      "berufsunfaehigkeit": "derived",
                      "fondsgebundene_rentenversicherung": "derived",
                      "indexpolice": "derived",
                      "kapitallebensversicherung": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "derived",
                      "riester_rente": "derived",
                      "risikolebensversicherung": "derived"},
        "prem_freq_load": {"basisrente": "derived",
                           "berufsunfaehigkeit": "derived",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "derived",
                           "riester_rente": "derived",
                           "risikolebensversicherung": "derived"},
        "instalments": {"berufsunfaehigkeit": "derived",
                        "fondsgebundene_rentenversicherung": "derived",
                        "kapitallebensversicherung": "derived",
                        "pflegerentenversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "prem_form": {"basisrente": "derived",
                      "fondsgebundene_rentenversicherung": "derived",
                      "indexpolice": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "derived",
                      "risikolebensversicherung": "override"},
        "prem_cycle": {"berufsunfaehigkeit": "derived",
                       "fondsgebundene_rentenversicherung": "derived",
                       "kapitallebensversicherung": "derived",
                       "pflegerentenversicherung": "derived",
                       "risikolebensversicherung": "derived"},
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
        "smoker_codes": {"kapitallebensversicherung": "derived",
                         "risikolebensversicherung": "override"},
        "smoker": {"kapitallebensversicherung": "derived",
                   "risikolebensversicherung": "derived"},
        "policy_term": {"kapitallebensversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "prem_term": {"kapitallebensversicherung": "derived",
                      "risikolebensversicherung": "derived"},
        "prem_term_y": {"fondsgebundene_rentenversicherung": "derived",
                        "indexpolice": "derived",
                        "klassische_rentenversicherung": "derived"},
        "issue_year": {"basisrente": "derived",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "derived",
                       "riester_rente": "derived",
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
        "clock_offset_mth": {"basisrente": "override",
                             "berufsunfaehigkeit": "override",
                             "indexpolice": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "pflegerentenversicherung": "derived",
                             "riester_rente": "override",
                             "risikolebensversicherung": "derived",
                             "sofortrente": "derived"},
        "k_start": {"basisrente": "derived",
                    "indexpolice": "derived",
                    "kapitallebensversicherung": "derived",
                    "klassische_rentenversicherung": "derived",
                    "riester_rente": "derived"},
        "t_start": {"fondsgebundene_rentenversicherung": "override",
                    "indexpolice": "derived",
                    "kapitallebensversicherung": "derived",
                    "klassische_rentenversicherung": "derived",
                    "pflegerentenversicherung": "override",
                    "risikolebensversicherung": "derived",
                    "sofortrente": "override"},
        "proj_year": {"basisrente": "derived",
                      "riester_rente": "derived"},
        "duration_mth": {"basisrente": "derived",
                         "berufsunfaehigkeit": "derived",
                         "indexpolice": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived",
                         "pflegerentenversicherung": "derived",
                         "riester_rente": "derived",
                         "risikolebensversicherung": "derived",
                         "sofortrente": "derived"},
        "duration": {"basisrente": "derived",
                     "berufsunfaehigkeit": "override",
                     "indexpolice": "derived",
                     "kapitallebensversicherung": "derived",
                     "klassische_rentenversicherung": "derived",
                     "riester_rente": "derived",
                     "risikolebensversicherung": "derived",
                     "sofortrente": "derived"},
        "duration_y": {"basisrente": "derived",
                       "riester_rente": "derived"},
        "policy_year": {"basisrente": "derived",
                        "berufsunfaehigkeit": "derived",
                        "fondsgebundene_rentenversicherung": "derived",
                        "indexpolice": "derived",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "derived",
                        "pflegerentenversicherung": "derived",
                        "riester_rente": "derived",
                        "risikolebensversicherung": "derived",
                        "sofortrente": "derived"},
        "policy_year_y": {"basisrente": "derived",
                          "kapitallebensversicherung": "derived",
                          "riester_rente": "derived"},
        "age_y": {"basisrente": "derived",
                  "indexpolice": "derived",
                  "kapitallebensversicherung": "derived",
                  "klassische_rentenversicherung": "derived",
                  "riester_rente": "derived"},
        "age": {"basisrente": "derived",
                "berufsunfaehigkeit": "derived",
                "fondsgebundene_rentenversicherung": "derived",
                "indexpolice": "derived",
                "kapitallebensversicherung": "derived",
                "klassische_rentenversicherung": "derived",
                "pflegerentenversicherung": "derived",
                "riester_rente": "derived",
                "risikolebensversicherung": "derived",
                "sofortrente": "override"},
        "omega_age": {"basisrente": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "derived",
                      "riester_rente": "override",
                      "sofortrente": "derived"},
        "ret_age": {"basisrente": "derived",
                    "fondsgebundene_rentenversicherung": "derived",
                    "indexpolice": "derived",
                    "riester_rente": "derived"},
        "k_conv": {"basisrente": "derived",
                   "riester_rente": "derived"},
        "t_conv": {"basisrente": "derived",
                   "riester_rente": "derived"},
        "horizon_age": {"basisrente": "override",
                        "berufsunfaehigkeit": "override",
                        "fondsgebundene_rentenversicherung": "override",
                        "indexpolice": "override",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "override",
                        "pflegerentenversicherung": "override",
                        "riester_rente": "override",
                        "risikolebensversicherung": "derived"},
        "proj_len_y": {"basisrente": "derived",
                       "indexpolice": "derived",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "derived",
                       "riester_rente": "derived",
                       "risikolebensversicherung": "derived"},
        "proj_len": {"basisrente": "derived",
                     "berufsunfaehigkeit": "derived",
                     "fondsgebundene_rentenversicherung": "derived",
                     "indexpolice": "derived",
                     "kapitallebensversicherung": "derived",
                     "klassische_rentenversicherung": "derived",
                     "pflegerentenversicherung": "derived",
                     "riester_rente": "derived",
                     "risikolebensversicherung": "derived",
                     "sofortrente": "override"},
        "calendar_year_y": {"basisrente": "derived",
                            "klassische_rentenversicherung": "derived",
                            "riester_rente": "derived"},
        "calendar_year": {"basisrente": "derived",
                          "klassische_rentenversicherung": "derived",
                          "riester_rente": "derived",
                          "sofortrente": "derived"},
        "rechnungszins": {"basisrente": "derived",
                          "berufsunfaehigkeit": "derived",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "derived",
                          "pflegerentenversicherung": "derived",
                          "riester_rente": "derived",
                          "risikolebensversicherung": "derived",
                          "sofortrente": "derived"},
        "hoechstrechnungszins": {"kapitallebensversicherung": "override",
                                 "sofortrente": "derived"},
        "beitragssumme_prem": {"fondsgebundene_rentenversicherung": "override",
                               "indexpolice": "derived",
                               "kapitallebensversicherung": "derived",
                               "pflegerentenversicherung": "override"},
        "beitragssumme_years": {"fondsgebundene_rentenversicherung": "override",
                                "indexpolice": "override",
                                "kapitallebensversicherung": "derived",
                                "pflegerentenversicherung": "override"},
        "beitragssumme": {"basisrente": "override",
                          "fondsgebundene_rentenversicherung": "derived",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "override",
                          "pflegerentenversicherung": "derived",
                          "riester_rente": "override"},
        "zillmer_on": {"basisrente": "derived",
                       "fondsgebundene_rentenversicherung": "derived",
                       "kapitallebensversicherung": "override",
                       "klassische_rentenversicherung": "derived",
                       "pflegerentenversicherung": "derived",
                       "riester_rente": "derived"},
        "zillmer_amount": {"basisrente": "derived",
                           "fondsgebundene_rentenversicherung": "derived",
                           "kapitallebensversicherung": "derived",
                           "klassische_rentenversicherung": "derived",
                           "pflegerentenversicherung": "derived",
                           "riester_rente": "derived"},
        "disc_factor_mth": {"berufsunfaehigkeit": "derived",
                            "pflegerentenversicherung": "derived"},
        "disc_factor": {"kapitallebensversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "unisex_mix_male": {"berufsunfaehigkeit": "derived",
                            "kapitallebensversicherung": "derived",
                            "klassische_rentenversicherung": "derived",
                            "pflegerentenversicherung": "derived",
                            "riester_rente": "derived",
                            "risikolebensversicherung": "derived",
                            "sofortrente": "derived"},
        "unisex_blend": {"berufsunfaehigkeit": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived",
                         "pflegerentenversicherung": "derived",
                         "riester_rente": "derived",
                         "risikolebensversicherung": "derived"},
        "mort_load_tariff": {"fondsgebundene_rentenversicherung": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "risikolebensversicherung": "override"},
        "mort_rate_tariff_base": {"fondsgebundene_rentenversicherung": "derived",
                                  "kapitallebensversicherung": "derived",
                                  "klassische_rentenversicherung": "derived",
                                  "risikolebensversicherung": "override"},
        "mort_rate_tariff": {"fondsgebundene_rentenversicherung": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "pflegerentenversicherung": "override",
                             "risikolebensversicherung": "derived",
                             "sofortrente": "override"},
        "pols_tariff": {"kapitallebensversicherung": "derived",
                        "risikolebensversicherung": "derived"},
        "tariff_annuity": {"kapitallebensversicherung": "derived",
                           "pflegerentenversicherung": "override",
                           "risikolebensversicherung": "derived"},
        "tariff_death_sum": {"kapitallebensversicherung": "override",
                             "risikolebensversicherung": "derived"},
        "tariff_death_load": {"kapitallebensversicherung": "override",
                              "risikolebensversicherung": "derived"},
        "tariff_schedule": {"kapitallebensversicherung": "derived",
                            "risikolebensversicherung": "override"},
        "tariff_maturity_sum": {"kapitallebensversicherung": "override",
                                "risikolebensversicherung": "derived"},
        "tariff_death_pv": {"kapitallebensversicherung": "derived",
                            "risikolebensversicherung": "derived"},
        "tariff_maturity_pv": {"kapitallebensversicherung": "derived",
                               "risikolebensversicherung": "derived"},
        "tariff_benefit_pv": {"kapitallebensversicherung": "derived",
                              "pflegerentenversicherung": "override",
                              "risikolebensversicherung": "derived"},
        "tariff_term_annuity": {"kapitallebensversicherung": "derived",
                                "risikolebensversicherung": "derived"},
        "prem_net_level_pp": {"kapitallebensversicherung": "derived",
                              "pflegerentenversicherung": "derived",
                              "risikolebensversicherung": "derived"},
        "is_anniv": {"basisrente": "derived",
                     "indexpolice": "derived",
                     "kapitallebensversicherung": "derived",
                     "klassische_rentenversicherung": "derived",
                     "riester_rente": "derived"},
        # The derivation hooks of the table factory (docs/core.md, "The table factory"): a
        # product that defines the name reads its own mortality file until its switch.
        "birth_year": {"basisrente": "override",
                       "klassische_rentenversicherung": "override",
                       "riester_rente": "override",
                       "sofortrente": "override"},
        "mort_table_name": {},
        "mort_rate_table": {"riester_rente": "override"},
        "mort_rate_at_age": {"basisrente": "derived",
                             "berufsunfaehigkeit": "derived",
                             "indexpolice": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "pflegerentenversicherung": "derived",
                             "riester_rente": "derived",
                             "risikolebensversicherung": "override",
                             "sofortrente": "derived"},
        "mort_rate_tariff_at_age": {"berufsunfaehigkeit": "derived",
                                    "fondsgebundene_rentenversicherung": "derived",
                                    "kapitallebensversicherung": "derived",
                                    "klassische_rentenversicherung": "derived"},
        "mort_be_trend": {"basisrente": "derived",
                          "berufsunfaehigkeit": "derived",
                          "fondsgebundene_rentenversicherung": "derived",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "derived",
                          "pflegerentenversicherung": "derived",
                          "sofortrente": "override"},
        "mort_be_factor": {"basisrente": "override",
                           "berufsunfaehigkeit": "override",
                           "fondsgebundene_rentenversicherung": "override",
                           "indexpolice": "override",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "override",
                           "riester_rente": "override",
                           "risikolebensversicherung": "override",
                           "sofortrente": "override"},
        "mort_rate_base": {"basisrente": "derived",
                           "berufsunfaehigkeit": "derived",
                           "fondsgebundene_rentenversicherung": "derived",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "derived",
                           "klassische_rentenversicherung": "derived",
                           "pflegerentenversicherung": "derived",
                           "riester_rente": "derived",
                           "risikolebensversicherung": "override"},
        "mort_rate": {"basisrente": "derived",
                      "berufsunfaehigkeit": "derived",
                      "fondsgebundene_rentenversicherung": "derived",
                      "indexpolice": "derived",
                      "kapitallebensversicherung": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "derived",
                      "riester_rente": "override",
                      "risikolebensversicherung": "override",
                      "sofortrente": "override"},
        "mort_rate_mth": {"basisrente": "derived",
                          "berufsunfaehigkeit": "derived",
                          "fondsgebundene_rentenversicherung": "override",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "derived",
                          "pflegerentenversicherung": "override",
                          "riester_rente": "derived",
                          "risikolebensversicherung": "derived",
                          "sofortrente": "override"},
        "lapse_rate_base": {"berufsunfaehigkeit": "derived",
                            "fondsgebundene_rentenversicherung": "derived",
                            "indexpolice": "override",
                            "kapitallebensversicherung": "derived",
                            "klassische_rentenversicherung": "derived",
                            "pflegerentenversicherung": "derived",
                            "riester_rente": "derived",
                            "risikolebensversicherung": "derived"},
        "lapse_factor": {"indexpolice": "override",
                         "pflegerentenversicherung": "override",
                         "riester_rente": "override",
                         "risikolebensversicherung": "override"},
        "lapse_rate": {"berufsunfaehigkeit": "derived",
                       "fondsgebundene_rentenversicherung": "override",
                       "indexpolice": "derived",
                       "kapitallebensversicherung": "override",
                       "klassische_rentenversicherung": "override",
                       "pflegerentenversicherung": "derived",
                       "riester_rente": "derived",
                       "risikolebensversicherung": "derived"},
        "lapse_rate_mth": {"berufsunfaehigkeit": "derived",
                           "fondsgebundene_rentenversicherung": "override",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "derived",
                           "klassische_rentenversicherung": "derived",
                           "pflegerentenversicherung": "derived",
                           "riester_rente": "derived",
                           "risikolebensversicherung": "derived"},
        "pols_if_init": dict.fromkeys(MODELS, "derived"),
        "pols_death": {"basisrente": "override",
                       "berufsunfaehigkeit": "override",
                       "fondsgebundene_rentenversicherung": "derived",
                       "indexpolice": "derived",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "derived",
                       "pflegerentenversicherung": "override",
                       "riester_rente": "override",
                       "risikolebensversicherung": "derived"},
        "pols_if_at": {"basisrente": "override",
                       "berufsunfaehigkeit": "derived",
                       "fondsgebundene_rentenversicherung": "override",
                       "indexpolice": "override",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "override",
                       "pflegerentenversicherung": "derived",
                       "riester_rente": "derived",
                       "risikolebensversicherung": "derived"},
        "pols_lapse": {"berufsunfaehigkeit": "override",
                       "fondsgebundene_rentenversicherung": "derived",
                       "indexpolice": "derived",
                       "kapitallebensversicherung": "derived",
                       "klassische_rentenversicherung": "derived",
                       "pflegerentenversicherung": "override",
                       "riester_rente": "derived",
                       "risikolebensversicherung": "derived"},
        "pols_maturity": {"fondsgebundene_rentenversicherung": "derived",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "risikolebensversicherung": "derived"},
        "pols_if": {"basisrente": "override",
                    "berufsunfaehigkeit": "override",
                    "fondsgebundene_rentenversicherung": "override",
                    "indexpolice": "derived",
                    "kapitallebensversicherung": "override",
                    "klassische_rentenversicherung": "override",
                    "pflegerentenversicherung": "override",
                    "riester_rente": "override",
                    "risikolebensversicherung": "derived",
                    "sofortrente": "override"},
        "prem_inst_pp": dict.fromkeys(MODELS, "override"),
        "pols_prem": {"basisrente": "override",
                      "berufsunfaehigkeit": "override",
                      "fondsgebundene_rentenversicherung": "derived",
                      "indexpolice": "derived",
                      "kapitallebensversicherung": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "override",
                      "riester_rente": "derived",
                      "risikolebensversicherung": "derived",
                      "sofortrente": "override"},
        "premiums": dict.fromkeys(MODELS, "derived"),
        "claim_kinds": {"basisrente": "override",
                        "berufsunfaehigkeit": "override",
                        "indexpolice": "derived",
                        "kapitallebensversicherung": "override",
                        "klassische_rentenversicherung": "override",
                        "riester_rente": "override",
                        "risikolebensversicherung": "derived",
                        "sofortrente": "override"},
        "benefit_death_pp": {"indexpolice": "override",
                             "kapitallebensversicherung": "override",
                             "klassische_rentenversicherung": "override",
                             "riester_rente": "override",
                             "risikolebensversicherung": "override"},
        "benefit_lapse_pp": {"berufsunfaehigkeit": "derived",
                             "indexpolice": "override",
                             "kapitallebensversicherung": "override",
                             "klassische_rentenversicherung": "override",
                             "riester_rente": "override",
                             "risikolebensversicherung": "derived"},
        "benefit_maturity_pp": {"indexpolice": "override",
                                "kapitallebensversicherung": "override",
                                "risikolebensversicherung": "derived"},
        "claims_other": {"berufsunfaehigkeit": "override",
                         "klassische_rentenversicherung": "override",
                         "riester_rente": "override",
                         "sofortrente": "override"},
        "claims": {"basisrente": "override",
                   "berufsunfaehigkeit": "derived",
                   "fondsgebundene_rentenversicherung": "override",
                   "indexpolice": "derived",
                   "kapitallebensversicherung": "derived",
                   "klassische_rentenversicherung": "derived",
                   "pflegerentenversicherung": "override",
                   "riester_rente": "derived",
                   "risikolebensversicherung": "derived",
                   "sofortrente": "derived"},
        "expense_infl": {"basisrente": "derived",
                         "fondsgebundene_rentenversicherung": "derived",
                         "indexpolice": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived",
                         "pflegerentenversicherung": "derived",
                         "riester_rente": "derived",
                         "risikolebensversicherung": "derived",
                         "sofortrente": "derived"},
        "inflation_years": {"basisrente": "override",
                            "fondsgebundene_rentenversicherung": "override",
                            "indexpolice": "derived",
                            "kapitallebensversicherung": "derived",
                            "klassische_rentenversicherung": "derived",
                            "pflegerentenversicherung": "override",
                            "riester_rente": "derived",
                            "risikolebensversicherung": "derived",
                            "sofortrente": "derived"},
        "inflation_factor": {"basisrente": "derived",
                             "fondsgebundene_rentenversicherung": "derived",
                             "indexpolice": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "pflegerentenversicherung": "derived",
                             "riester_rente": "derived",
                             "risikolebensversicherung": "derived",
                             "sofortrente": "derived"},
        "expenses_acq": {"basisrente": "override",
                         "indexpolice": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "override",
                         "riester_rente": "override",
                         "risikolebensversicherung": "override",
                         "sofortrente": "override"},
        "expenses_maint": {"basisrente": "override",
                           "indexpolice": "override",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "override",
                           "riester_rente": "override",
                           "risikolebensversicherung": "override",
                           "sofortrente": "override"},
        "expenses_claim": {"basisrente": "derived",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "override",
                           "riester_rente": "override",
                           "risikolebensversicherung": "override",
                           "sofortrente": "override"},
        "expenses": {"basisrente": "derived",
                     "berufsunfaehigkeit": "override",
                     "fondsgebundene_rentenversicherung": "override",
                     "indexpolice": "derived",
                     "kapitallebensversicherung": "derived",
                     "klassische_rentenversicherung": "derived",
                     "pflegerentenversicherung": "override",
                     "riester_rente": "derived",
                     "risikolebensversicherung": "derived",
                     "sofortrente": "derived"},
        "comm_init_rate": {"basisrente": "override",
                           "berufsunfaehigkeit": "derived",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "derived",
                           "pflegerentenversicherung": "derived",
                           "riester_rente": "override",
                           "sofortrente": "derived"},
        "comm_init": {"basisrente": "derived",
                      "berufsunfaehigkeit": "derived",
                      "fondsgebundene_rentenversicherung": "override",
                      "indexpolice": "derived",
                      "kapitallebensversicherung": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "derived",
                      "riester_rente": "derived",
                      "risikolebensversicherung": "override",
                      "sofortrente": "derived"},
        "comm_renew": {"basisrente": "override",
                       "berufsunfaehigkeit": "derived",
                       "fondsgebundene_rentenversicherung": "override",
                       "indexpolice": "derived",
                       "kapitallebensversicherung": "override",
                       "klassische_rentenversicherung": "derived",
                       "pflegerentenversicherung": "derived",
                       "riester_rente": "override",
                       "risikolebensversicherung": "override",
                       "sofortrente": "derived"},
        "commissions": dict.fromkeys(MODELS, "derived"),
        "income_other": {"basisrente": "derived",
                         "indexpolice": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived",
                         "riester_rente": "override",
                         "risikolebensversicherung": "derived"},
        "annuity_outgo": {"basisrente": "derived",
                          "indexpolice": "derived",
                          "kapitallebensversicherung": "derived",
                          "klassische_rentenversicherung": "override",
                          "riester_rente": "derived",
                          "risikolebensversicherung": "derived"},
        "net_cf": {"basisrente": "derived",
                   "berufsunfaehigkeit": "override",
                   "fondsgebundene_rentenversicherung": "override",
                   "indexpolice": "derived",
                   "kapitallebensversicherung": "derived",
                   "klassische_rentenversicherung": "derived",
                   "pflegerentenversicherung": "override",
                   "riester_rente": "derived",
                   "risikolebensversicherung": "derived",
                   "sofortrente": "override"},
        "liability_cf": {**dict.fromkeys(MODELS, "derived"), "sofortrente": "override"},
        "roll_fwd_tol": dict.fromkeys(MODELS, "derived"),
        "result_cf_columns": {**dict.fromkeys(MODELS, "override"),
                              "kapitallebensversicherung": "derived",
                              "risikolebensversicherung": "derived"},
        "result_cf": {**dict.fromkeys(MODELS, "derived"), "berufsunfaehigkeit": "override"},
        "result_cf_dict": dict.fromkeys(MODELS, "derived"),
        "result_cf_counts": {"indexpolice": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "override",
                             "risikolebensversicherung": "derived"},
        "result_cf_annual": {"basisrente": "override",
                             "indexpolice": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "riester_rente": "override",
                             "risikolebensversicherung": "derived"},
        "result_pols_columns": {"risikolebensversicherung": "override",
                                "sofortrente": "override"},
        "result_pols": {"basisrente": "override",
                        "klassische_rentenversicherung": "override",
                        "risikolebensversicherung": "derived",
                        "sofortrente": "derived"},
        "result_states_columns": {"berufsunfaehigkeit": "override",
                                  "pflegerentenversicherung": "override"},
        "result_states": {"berufsunfaehigkeit": "override",
                          "pflegerentenversicherung": "derived"},
        "net_cf_income_columns": {"kapitallebensversicherung": "derived",
                                  "klassische_rentenversicherung": "derived",
                                  "riester_rente": "override",
                                  "risikolebensversicherung": "derived"},
        "net_cf_outgo_columns": {"kapitallebensversicherung": "derived",
                                 "klassische_rentenversicherung": "override",
                                 "riester_rente": "derived",
                                 "risikolebensversicherung": "derived"},
        "check_net_cf_resid": {"basisrente": "override",
                               "berufsunfaehigkeit": "override",
                               "fondsgebundene_rentenversicherung": "override",
                               "indexpolice": "override",
                               "kapitallebensversicherung": "derived",
                               "klassische_rentenversicherung": "derived",
                               "pflegerentenversicherung": "override",
                               "riester_rente": "derived",
                               "risikolebensversicherung": "derived",
                               "sofortrente": "override"},
        "check_net_cf_scale": {"basisrente": "derived",
                               "berufsunfaehigkeit": "override",
                               "fondsgebundene_rentenversicherung": "derived",
                               "indexpolice": "override",
                               "kapitallebensversicherung": "override",
                               "klassische_rentenversicherung": "derived",
                               "pflegerentenversicherung": "override",
                               "riester_rente": "override",
                               "risikolebensversicherung": "derived",
                               "sofortrente": "override"},
        "check_net_cf_tol": {**dict.fromkeys(MODELS, "derived"),
                             "fondsgebundene_rentenversicherung": "override",
                             "risikolebensversicherung": "override"},
        "check_net_cf": {**dict.fromkeys(MODELS, "derived"),
                         "basisrente": "override",
                         "berufsunfaehigkeit": "override",
                         "klassische_rentenversicherung": "override"},
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


def _probe_omega_age():
    """The core's version."""
    return 121


def _probe_use():
    """Reads omega_age by its bare name, as a product cell does."""
    return omega_age()                                               # noqa: F821


def test_a_module_reference_cannot_shadow_a_core_cell(tmp_path):
    """A product module's ``omega_age = 110`` beside a core cell ``omega_age`` is no Reference.

    modelx reads the assignment as an input value of the derived cell in the static space;
    an item space computes the core formula, so the value is silently ignored there.  Hence
    a parameter that was a Reference becomes a ``param_tariff_type.csv`` row, not a Reference of
    the core cell's name.
    """
    model = mx.new_model("ShadowProbe")
    core = model.new_space("CoreProjection", formula=lambda point_id: None)
    core.new_cells("omega_age", formula=_probe_omega_age)
    core.new_cells("use", formula=_probe_use)
    model.new_space("Projection", bases=core, formula=lambda point_id: None)
    path = tmp_path / "ShadowProbe"
    mx.write_model(model, path)
    model.close()
    source = path / "Projection" / "__init__.py"
    source.write_text(source.read_text(encoding="utf-8")
                      + "\n# " + "-" * 75 + "\n# References\n\nomega_age = 110\n",
                      encoding="utf-8")
    model = mx.read_model(path)
    try:
        projection = model.Projection
        assert "omega_age" not in projection.refs
        assert projection.omega_age._is_derived()
        assert projection[1].use() == 121
        assert projection[1].omega_age() == 121
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


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_product_reads_the_core_items(product, product_models):
    core = product_models(product).Data.param_layers()["core"]
    assert core == CORE_ITEMS
    assert all(type(core[item]) is type(literal) for item, literal in CORE_ITEMS.items())


# The products with a calendar year, those whose model points carry ``issue_year``: each of
# their points opens at the valuation date 1 January 2027, the core item ``valuation_year``,
# its year of issue plus its completed policy years being the valuation year, on its policy
# anniversary (entry 23 of epic-parameter-files). Read off the files, so a product gaining
# the column is checked without a list to keep.
VALUATION_DATE_PRODUCTS = tuple(sorted(
    product for product in MODELS
    if "issue_year" in (PRODUCTS_DIR / product / "model_point_table.csv")
    .read_text().splitlines()[0].split(",")))


def test_the_products_with_a_calendar_year_are_five():
    assert VALUATION_DATE_PRODUCTS == (
        "basisrente", "kapitallebensversicherung", "klassische_rentenversicherung",
        "riester_rente", "sofortrente")


# The core items no cell reads, each with the test that reads it: the valuation date is the
# date the model points are built against, not a parameter of a formula.
CORE_ITEMS_READ_BY_TESTS = {
    "valuation_year": "test_every_model_point_opens_at_the_valuation_date",
}


@pytest.mark.parametrize("product", VALUATION_DATE_PRODUCTS)
def test_every_model_point_opens_at_the_valuation_date(product, product_models):
    model = product_models(product)
    year = model.Data.param("valuation_year")
    points = model.Data.model_point_table()
    for point_id, row in points.iterrows():
        if "duration_init" in points.columns:
            elapsed = int(row["duration_init"])
        else:
            assert int(row["duration_mth_init"]) % 12 == 0, point_id
            elapsed = int(row["duration_mth_init"]) // 12
        assert int(row["issue_year"]) + elapsed == year, point_id


def test_no_core_item_is_unused(product_models):
    usages = [param_usage.scan(product_models(product)) for product in sorted(MODELS)]
    assert param_usage.unused_core_items(usages) == sorted(CORE_ITEMS_READ_BY_TESTS)
    for test in CORE_ITEMS_READ_BY_TESTS.values():
        assert callable(globals().get(test)), test
