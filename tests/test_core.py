"""The common core of phase 3 (``docs/core.md``): grep test, override reasons, trace.

- No file under ``core/`` names a product: no product folder name, model name or model
  prefix as a case-sensitive whole word.
- A product cell that redefines a cell of a core base carries an ``Override reason:`` line
  in its docstring.
- RLV takes ``model_point`` from the core, and the traced modelx model shows it.
- Every product has the core spaces as bases, and every cell unified into the core
  (``CORE_CELLS``) is defined in the core and, in each product that has it, either derived
  from the core or overridden (with the reason the override test requires).
- The time axis: Basis and Riester offset every clock cell by ``clock_offset_mth``, KLV
  counts from issue; RLV's derived ``age`` and ``policy_year`` follow the inception clock, BU's
  ``duration`` floors them before inception, Sofort's ``age`` reads the second life.
- The tariff basis: KLV, RLV, BU and Pflege read their rate from the model point;
  the monthly discount factor equals the annual one on a year start; the tariff
  survivorship is 1 at issue; the net level premium is the benefit value over the annuity.
- The decrement rates: BU's derived death rate is its table rate at the neutral factor, KLV's
  its table rate times 0.75; an annual certainty falls in the anniversary month (Basis and RV
  deaths at the terminal age, KLV's failed *Beitragsfreistellung*); FRV splits mortality
  linearly; Index and RLV close the lapse in the final policy year without reading the table.
- The policy counts: RLV and BU read their count from the model point; RLV opens at it; RLV and
  Index close at exactly zero; the end-of-month count is the next month's opening count and
  an unknown timing is rejected; the survivors mature in the last month; KLV's lapses are
  taken from the survivors of the month's deaths.
- The cash flows: KLV's premium is the instalment times the in-force; RLV's claim total is its
  death claim and its lapse and maturity claims are exactly zero; RV's commutation is a further
  kind and an unknown kind is rejected; Index and RV pay exactly zero commission; KLV's net
  cash flow subtracts its claims kind by kind; RLV's liability cash flow is its net cash flow
  negated.
"""
from __future__ import annotations

import hashlib
import io
import math
import re
import shutil
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
        "param_table": {"basisrente": "derived",
                        "fondsgebundene_rentenversicherung": "derived",
                        "kapitallebensversicherung": "derived",
                        "klassische_rentenversicherung": "derived",
                        "pflegerentenversicherung": "derived",
                        "riester_rente": "derived",
                        "sofortrente": "derived"},
        "mort_table_index": {"basisrente": "override",
                             "berufsunfaehigkeit": "override",
                             "fondsgebundene_rentenversicherung": "override",
                             "indexpolice": "derived",
                             "kapitallebensversicherung": "derived",
                             "klassische_rentenversicherung": "derived",
                             "pflegerentenversicherung": "derived",
                             "riester_rente": "override",
                             "risikolebensversicherung": "override",
                             "sofortrente": "override"},
        "mort_table": dict.fromkeys(MODELS, "derived"),
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
        "freq_loading_table": {"berufsunfaehigkeit": "derived",
                               "indexpolice": "derived",
                               "kapitallebensversicherung": "derived",
                               "klassische_rentenversicherung": "derived",
                               "riester_rente": "derived",
                               "risikolebensversicherung": "derived"},
        "surplus_table_index": {"basisrente": "derived",
                                "riester_rente": "derived"},
        "surplus_table": {"basisrente": "derived",
                          "riester_rente": "derived"},
        "charge_table_index": {"basisrente": "override",
                               "fondsgebundene_rentenversicherung": "derived",
                               "kapitallebensversicherung": "override",
                               "klassische_rentenversicherung": "override"},
        "charge_table": {"basisrente": "derived",
                         "fondsgebundene_rentenversicherung": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived"},
        "hoechstrechnungszins_table": {"sofortrente": "derived"},
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
        "prem_freq": {"basisrente": "override",
                      "berufsunfaehigkeit": "derived",
                      "indexpolice": "derived",
                      "kapitallebensversicherung": "derived",
                      "klassische_rentenversicherung": "derived",
                      "pflegerentenversicherung": "override",
                      "riester_rente": "derived",
                      "risikolebensversicherung": "derived"},
        "prem_freq_load": {"basisrente": "override",
                           "berufsunfaehigkeit": "derived",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "derived",
                           "riester_rente": "derived",
                           "risikolebensversicherung": "derived"},
        "instalments": {"kapitallebensversicherung": "derived",
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
                       "riester_rente": "override",
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
        "omega_age": {"basisrente": "override",
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
                               "kapitallebensversicherung": "derived",
                               "pflegerentenversicherung": "override"},
        "beitragssumme_years": {"fondsgebundene_rentenversicherung": "override",
                                "kapitallebensversicherung": "derived",
                                "pflegerentenversicherung": "override"},
        "beitragssumme": {"basisrente": "override",
                          "fondsgebundene_rentenversicherung": "derived",
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
        "unisex_mix_male": {"kapitallebensversicherung": "derived",
                            "pflegerentenversicherung": "derived"},
        "unisex_blend": {"kapitallebensversicherung": "derived",
                         "pflegerentenversicherung": "derived"},
        "mort_load_tariff": {"fondsgebundene_rentenversicherung": "derived",
                             "kapitallebensversicherung": "derived",
                             "risikolebensversicherung": "override"},
        "mort_rate_tariff_base": {"fondsgebundene_rentenversicherung": "derived",
                                  "kapitallebensversicherung": "derived",
                                  "risikolebensversicherung": "override"},
        "mort_rate_tariff": {"fondsgebundene_rentenversicherung": "derived",
                             "kapitallebensversicherung": "derived",
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
        "mort_be_factor": {"basisrente": "override",
                           "fondsgebundene_rentenversicherung": "override",
                           "kapitallebensversicherung": "override",
                           "klassische_rentenversicherung": "override",
                           "riester_rente": "override",
                           "risikolebensversicherung": "derived"},
        "mort_rate_base": {"basisrente": "override",
                           "berufsunfaehigkeit": "derived",
                           "fondsgebundene_rentenversicherung": "override",
                           "indexpolice": "derived",
                           "kapitallebensversicherung": "derived",
                           "klassische_rentenversicherung": "override",
                           "pflegerentenversicherung": "derived",
                           "riester_rente": "derived",
                           "risikolebensversicherung": "override"},
        "mort_rate": {"basisrente": "override",
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
        "income_other": {"basisrente": "override",
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
                              "kapitallebensversicherung": "derived"},
        "result_cf": {**dict.fromkeys(MODELS, "derived"), "berufsunfaehigkeit": "override"},
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
        "net_cf_income_columns": {"basisrente": "override",
                                  "kapitallebensversicherung": "derived",
                                  "klassische_rentenversicherung": "derived",
                                  "riester_rente": "override",
                                  "risikolebensversicherung": "derived"},
        "net_cf_outgo_columns": {"basisrente": "derived",
                                 "kapitallebensversicherung": "derived",
                                 "klassische_rentenversicherung": "override",
                                 "riester_rente": "derived",
                                 "risikolebensversicherung": "derived"},
        "check_net_cf_resid": {"basisrente": "derived",
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
    a parameter that was a Reference becomes a ``param_table.csv`` row, not a Reference of
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
    # The Rechnungszins moved from the table to the model point (a contract attribute).
    moved = ["rechnungszins"]
    points = model.Data.model_point_table()
    for item in moved:
        assert (points[item] == basis.at[item, "value"]).all(), item
    basis = basis.drop(moved)
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


@pytest.mark.parametrize("product", ["basisrente", "riester_rente"])
def test_the_valuation_clock_offsets_every_clock_cell(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.clock_offset_mth._is_defined()
    for name in ("k_start", "duration_mth", "duration_y", "age_y", "age"):
        assert projection.cells[name]._is_derived(), name
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in in_force:
        item = projection[point_id]
        d = item.duration_init()
        assert item.clock_offset_mth() == 12 * d
        assert item.k_start() == 0
        for k in range(3):
            assert item.duration_y(k) == d + k, (point_id, k)
        for t in (0, 11, 12, 30):
            assert item.age(t) == item.issue_age() + d + t // 12, (point_id, t)


def test_the_inception_clock_counts_from_issue(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.clock_offset_mth._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in in_force:
        item = projection[point_id]
        assert item.clock_offset_mth() == 0
        assert item.k_start() == item.duration_init()
        for k in range(3):
            assert item.duration_y(k) == k, (point_id, k)


def test_bu_duration_is_floored_before_inception(product_models):
    model = product_models("berufsunfaehigkeit")
    projection = model.Projection
    assert projection.duration._is_defined()
    assert projection.policy_year._is_derived()
    assert projection.age._is_derived()
    points = model.Data.model_point_table()
    new = points.index[points["duration_mth_init"] == 0]
    assert len(new), "no new-business model point"
    item = projection[new[0]]
    assert item.duration(-30) == 0
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


def product_copy(tmp_path, product: str) -> Path:
    """A scratch copy of a product folder; ``copytree`` follows the core symlinks."""
    folder = tmp_path / product
    shutil.copytree(PRODUCTS_DIR / product, folder)
    return folder


def test_rlv_smoker_reads_its_codes_and_rejects_others(tmp_path, product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.smoker._is_derived()
    assert projection.smoker_codes._is_defined()
    points = model.Data.model_point_table()
    smokers = points.index[points["smoker"] == "R"]
    assert len(smokers), "no smoker model point"
    assert projection[smokers[0]].smoker() == "R"

    folder = product_copy(tmp_path, "risikolebensversicherung")
    table = folder / "model_point_table.csv"
    points.loc[smokers[0], "smoker"] = "S"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="SmokerProbe")
    try:
        with pytest.raises(Exception, match="invalid smoker"):
            copy.Projection[smokers[0]].smoker()
    finally:
        copy.close()


def test_core_prem_term_rejects_a_term_beyond_the_policy_term(tmp_path, product_models):
    model = product_models("risikolebensversicherung")
    assert model.Projection.prem_term._is_derived()
    points = model.Data.model_point_table()
    point_id = points.index[0]
    assert model.Projection[point_id].prem_term() <= model.Projection[point_id].policy_term()

    folder = product_copy(tmp_path, "risikolebensversicherung")
    points.loc[point_id, "prem_term"] = points.loc[point_id, "policy_term"] + 1
    points.to_csv(folder / "model_point_table.csv")
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="PremTermProbe")
    try:
        with pytest.raises(Exception, match="prem_term outside 1 .. policy_term"):
            copy.Projection[point_id].prem_term()
    finally:
        copy.close()


def test_klv_in_force_point_reads_its_own_rechnungszins(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.rechnungszins._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in in_force:
        assert (projection[point_id].rechnungszins()
                == float(points.at[point_id, "rechnungszins"])), point_id


@pytest.mark.parametrize("product", ["berufsunfaehigkeit", "pflegerentenversicherung",
                                     "risikolebensversicherung"])
def test_rechnungszins_is_read_from_the_model_point(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.rechnungszins._is_derived()
    points = model.Data.model_point_table()
    for point_id in points.index:
        assert projection[point_id].rechnungszins() == 0.01, point_id


def test_pflege_monthly_discount_equals_the_annual_one_on_a_year_start(product_models):
    projection = product_models("pflegerentenversicherung").Projection
    assert projection.disc_factor_mth._is_derived()
    assert projection.disc_factor._is_derived()
    item = projection[1]
    for y in range(4):
        assert item.disc_factor_mth(12 * y) == item.disc_factor(y), y


def test_rlv_tariff_survivorship_is_one_at_issue_on_an_in_force_point(product_models):
    model = product_models("risikolebensversicherung")
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    item = model.Projection[in_force[0]]
    assert item.t_start() > 0
    assert item.pols_tariff(0) == 1.0


@pytest.mark.parametrize("product", ["kapitallebensversicherung", "risikolebensversicherung"])
def test_net_level_premium_divides_benefit_pv_by_tariff_annuity(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.prem_net_level_pp._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert (item.prem_net_level_pp()
                == item.tariff_benefit_pv() / item.tariff_annuity()), point_id


@pytest.mark.parametrize("product", ["kapitallebensversicherung", "risikolebensversicherung"])
def test_annual_discount_factor_is_the_rechnungszins_power(product, product_models):
    projection = product_models(product).Projection
    assert projection.disc_factor._is_derived()
    item = projection[1]
    assert item.disc_factor(3) == (1.0 + item.rechnungszins()) ** -3


def test_bu_mort_rate_is_its_table_rate_at_the_neutral_factor(product_models):
    model = product_models("berufsunfaehigkeit")
    projection = model.Projection
    assert projection.mort_rate._is_derived()
    assert projection.mort_be_factor._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.mort_be_factor() == 1.0
        for t in range(item.proj_len()):
            assert item.mort_rate(t) == item.mort_rate_at_age(item.age(t)), (point_id, t)


def test_klv_mort_rate_steps_its_table_by_the_factor_from_param_table(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.mort_rate._is_derived()
    assert projection.mort_be_factor._is_defined()
    assert model.Data.param_table().at["mort_be_factor", "value"] == 0.75
    item = projection[model.Data.model_point_table().index[0]]
    assert item.mort_be_factor() == 0.75
    for t in range(item.proj_len()):
        assert item.mort_rate(t) == min(1.0, item.mort_rate_base(t) * 0.75), t


@pytest.mark.parametrize("product", ["basisrente", "klassische_rentenversicherung"])
def test_a_certain_death_falls_in_the_anniversary_month(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.mort_rate_mth._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    terminal = [t for t in range(item.proj_len()) if item.mort_rate(t) == 1.0]
    assert terminal, "no month with mort_rate = 1"
    start = terminal[0] - terminal[0] % 12
    assert all(item.mort_rate(start + m) == 1.0 for m in range(12))
    assert [item.mort_rate_mth(start + m) for m in range(12)] == [0.0] * 11 + [1.0]
    assert item.is_anniv(start + 11)


def test_frv_splits_mortality_linearly(product_models):
    model = product_models("fondsgebundene_rentenversicherung")
    projection = model.Projection
    assert projection.mort_rate_mth._is_defined()
    assert projection.mort_rate._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    for t in range(item.proj_len()):
        assert item.mort_rate_mth(t) == item.mort_rate(t) / 12.0, t


@pytest.mark.parametrize("product", ["indexpolice", "risikolebensversicherung"])
def test_lapse_is_closed_in_the_final_policy_year_without_reading_the_table(
        product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.lapse_rate._is_derived()
    assert projection.lapse_factor._is_defined()
    item = projection[model.Data.model_point_table().index[0]]
    final = 12 * (item.proj_len_y() - 1)
    for t in range(final, item.proj_len()):
        assert item.lapse_rate(t) == 0.0, t
        names = {node.obj.name for node in item.lapse_rate.precedents(t)}
        assert names == {"lapse_factor"}, (t, names)
    assert item.lapse_rate(final - 1) > 0.0


def _rebate_cut_from_policy_year_4(t):
    """The declaration cut to nothing from policy year 4: the bill rises to the guaranteed one."""
    return 0.0 if duration(t) >= 3 else prem_rebate_level_pp(t)      # noqa: F821


def test_rlv_lapse_rate_is_the_table_rate_times_the_shock_factor():
    """With the premium-shock module on and the declaration cut in year 4, the shock fires."""
    model = mx.read_model(PRODUCTS_DIR / "risikolebensversicherung"
                          / MODELS["risikolebensversicherung"], name="ShockProbe")
    try:
        projection = model.Projection
        assert projection.lapse_rate._is_derived()
        projection.new_cells("prem_rebate_level_pp", formula=projection.prem_rebate_pp.formula)
        projection.prem_rebate_pp.formula = _rebate_cut_from_policy_year_4
        projection.shock_lapse_lambda = 2.0
        item = projection[model.Data.model_point_table().index[0]]
        final = 12 * (item.proj_len_y() - 1)
        shocked = [t for t in range(item.t_start(), final) if item.shock_lapse_factor(t) > 1.0]
        assert shocked, "the premium shock never fires"
        for t in shocked:
            assert (item.lapse_rate(t)
                    == item.lapse_rate_base(t) * item.shock_lapse_factor(t)), t
            assert item.lapse_rate(t) > item.lapse_rate_base(t), t
        for t in range(final, item.proj_len()):
            assert item.lapse_rate(t) == 0.0, t
    finally:
        model.close()


def test_klv_failed_beitragsfreistellung_lapses_in_the_anniversary_month(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.lapse_rate_mth._is_derived()
    failing = [p for p in model.Data.model_point_table().index if projection[p].bfz_fails()]
    assert failing, "no model point with a failed Beitragsfreistellung"
    item = projection[failing[0]]
    start = 12 * (item.bfz_year() - 1)
    assert all(item.lapse_rate(start + m) == 1.0 for m in range(12))
    assert [item.lapse_rate_mth(start + m) for m in range(12)] == [0.0] * 11 + [1.0]
    assert item.is_anniv(start + 11)


@pytest.mark.parametrize("product", ["berufsunfaehigkeit", "risikolebensversicherung"])
def test_pols_if_init_is_read_from_the_model_point(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_if_init._is_derived()
    points = model.Data.model_point_table()
    assert (points["pols_if_init"] == 1.0).all()
    for point_id in points.index:
        assert projection[point_id].pols_if_init() == 1.0, point_id


@pytest.mark.parametrize("product", ["berufsunfaehigkeit", "kapitallebensversicherung",
                                     "pflegerentenversicherung", "risikolebensversicherung"])
def test_the_end_of_month_count_is_the_next_start_of_month_count(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_if_at._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    # BU's frame opens at t = 0, the valuation month: its pols_if guards on t < 0 and does
    # not use the t_start() it inherits from the core.
    start = 0 if product == "berufsunfaehigkeit" else item.t_start()
    for t in range(start, item.proj_len()):
        assert item.pols_if_at(t, "BEF_DECR") == item.pols_if(t), t
        assert item.pols_if_at(t, "AFT_DECR") == item.pols_if(t + 1), t
    with pytest.raises(Exception, match="invalid timing") as raised:
        item.pols_if_at(start, "END")
    # modelx re-raises a formula's error as a FormulaError without chaining it, and names
    # the original type in its message.
    chain, error = [], raised.value
    while error is not None and error not in chain:
        chain.append(error)
        error = error.__cause__ or error.__context__
    assert (any(isinstance(e, ValueError) for e in chain)
            or "ValueError: invalid timing" in str(raised.value)), raised.value


def test_klv_lapses_are_taken_from_the_survivors_of_the_deaths(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.pols_lapse._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    lapsing = [t for t in range(item.t_start(), item.proj_len()) if item.pols_lapse(t) > 0.0]
    assert lapsing, "no month with lapses"
    for t in range(item.t_start(), item.proj_len()):
        assert (item.pols_lapse(t)
                == item.pols_if_at(t, "AFT_DEATH") * item.lapse_rate_mth(t)), t
        assert (item.pols_if_at(t, "AFT_DEATH")
                == item.pols_if(t) * (1.0 - item.mort_rate_mth(t))), t



@pytest.mark.parametrize("product", ["fondsgebundene_rentenversicherung", "indexpolice",
                                     "kapitallebensversicherung", "risikolebensversicherung"])
def test_the_survivors_of_both_decrements_mature_in_the_last_month(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_maturity._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    last = item.proj_len() - 1
    for t in range(item.t_start(), last):
        assert item.pols_maturity(t) == 0.0, t
    # The lapse is closed in the last month, so the survivors of both decrements are the
    # survivors of the month's deaths.
    assert item.lapse_rate_mth(last) == 0.0
    assert item.pols_lapse(last) == 0.0
    assert item.pols_maturity(last) > 0.0
    assert item.pols_maturity(last) == item.pols_if_at(last, "AFT_DEATH")



def test_rlv_opens_at_pols_if_init_on_new_and_in_force_points(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.pols_if._is_derived()
    points = model.Data.model_point_table()
    in_force = points.index[points["duration_init"] > 0]
    assert len(in_force), "no in-force model point"
    for point_id in (points.index[0], in_force[0]):
        item = projection[point_id]
        assert item.pols_if(item.t_start()) == item.pols_if_init(), point_id
        assert item.pols_if(item.t_start() - 1) == 0.0, point_id


@pytest.mark.parametrize("product", ["indexpolice", "risikolebensversicherung"])
def test_the_count_after_the_last_month_is_exactly_positive_zero(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.pols_if._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        closing = item.pols_if(item.proj_len())
        assert closing == 0.0 and math.copysign(1.0, closing) == 1.0, point_id
        assert item.pols_maturity(item.proj_len() - 1) > 0.0, point_id


def test_klv_premium_is_the_instalment_times_the_in_force(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.premiums._is_derived()
    assert projection.pols_prem._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        paying = [t for t in range(item.t_start(), item.proj_len()) if item.premiums(t) > 0.0]
        assert paying, point_id
        for t in range(item.t_start(), item.proj_len()):
            assert item.pols_prem(t) == item.pols_if(t), (point_id, t)
            assert item.premiums(t) == item.prem_inst_pp(t) * item.pols_prem(t), (point_id, t)


def raised_value_error(raised, message: str) -> bool:
    """Whether a modelx error carries a ``ValueError`` with ``message``.

    modelx re-raises a formula's error as a FormulaError without chaining it, and names the
    original type in its message.
    """
    chain, error = [], raised.value
    while error is not None and error not in chain:
        chain.append(error)
        error = error.__cause__ or error.__context__
    return (any(isinstance(e, ValueError) for e in chain)
            or f"ValueError: {message}" in str(raised.value))


def test_rlv_claim_total_is_the_death_claim_and_the_cash_values_are_zero(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.claims._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.claim_kinds() == ("DEATH", "LAPSE", "MATURITY")
        for t in range(item.t_start(), item.proj_len()):
            assert item.claims(t) == item.claims(t, "DEATH"), (point_id, t)
            for kind in ("LAPSE", "MATURITY"):
                zero = item.claims(t, kind)
                assert zero == 0.0 and math.copysign(1.0, zero) == 1.0, (point_id, t, kind)


def test_rv_commutation_is_a_further_kind_and_an_unknown_kind_is_rejected(product_models):
    model = product_models("klassische_rentenversicherung")
    projection = model.Projection
    assert projection.claims._is_derived()
    item = projection[model.Data.model_point_table().index[0]]
    commuting = [t for t in range(item.t_start(), item.proj_len())
                 if item.pols_commutation(t) > 0.0]
    assert commuting, "no month with commutations"
    for t in commuting:
        assert (item.claims(t, "COMMUTATION")
                == item.claims_other(t, "COMMUTATION")
                == item.capital_conv_pp() * item.pols_commutation(t)), t
    with pytest.raises(Exception, match="invalid kind") as raised:
        item.claims(item.t_start(), "ANNUITY")
    assert raised_value_error(raised, "invalid kind"), raised.value


@pytest.mark.parametrize("product", ["indexpolice", "klassische_rentenversicherung"])
def test_a_product_without_commission_pays_exactly_zero(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.commissions._is_derived()
    assert projection.comm_init_rate._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            zero = item.commissions(t)
            assert zero == 0.0 and math.copysign(1.0, zero) == 1.0, (point_id, t)


def test_klv_net_cf_subtracts_each_claim_kind_in_turn(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.net_cf._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            expected = (item.premiums(t) - item.claims(t, "DEATH")
                        - item.claims(t, "MATURITY") - item.claims(t, "LAPSE")
                        - item.expenses(t) - item.commissions(t))
            assert math.copysign(1.0, item.net_cf(t)) == math.copysign(1.0, expected)
            assert item.net_cf(t) == expected, (point_id, t)


def test_rlv_liability_cf_is_the_negated_net_cf(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.liability_cf._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            assert item.liability_cf(t) == -item.net_cf(t), (point_id, t)
            assert (math.copysign(1.0, item.liability_cf(t))
                    == -math.copysign(1.0, item.net_cf(t))), (point_id, t)



ROLL_FWD_TOL = {
    "basisrente": 1e-09,
    "berufsunfaehigkeit": 1e-10,
    "fondsgebundene_rentenversicherung": 1e-10,
    "indexpolice": 1e-08,
    "kapitallebensversicherung": 1e-10,
    "klassische_rentenversicherung": 1e-09,
    "pflegerentenversicherung": 1e-10,
    "riester_rente": 1e-09,
    "risikolebensversicherung": 1e-10,
    "sofortrente": 1e-08,
}


@pytest.mark.parametrize("product", sorted(MODELS))
def test_roll_fwd_tol_is_read_from_param_table(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.roll_fwd_tol._is_derived()
    assert "roll_fwd_tol" not in projection.refs
    point_id = model.Data.model_point_table().index[0]
    assert projection[point_id].roll_fwd_tol() == ROLL_FWD_TOL[product]


def test_roll_fwd_tol_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "kapitallebensversicherung")
    table = folder / "param_table.csv"
    params = pd.read_csv(table, index_col="item")
    params.drop(index="roll_fwd_tol").to_csv(table)
    copy = mx.read_model(folder / MODELS["kapitallebensversicherung"], name="TolProbe")
    try:
        point_id = copy.Data.model_point_table().index[0]
        with pytest.raises(Exception, match="roll_fwd_tol") as raised:
            copy.Projection[point_id].roll_fwd_tol()
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_klv_result_cf_is_the_core_statement_from_t_start(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.result_cf._is_derived()
    assert projection.result_cf_columns._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        frame = item.result_cf()
        assert list(frame.columns) == [
            "pols_if", "premiums", "claims_death", "claims_maturity", "claims_lapse",
            "expenses", "commissions", "net_cf", "liability_cf"], point_id
        assert frame.index.name == "t"
        assert list(frame.index) == list(range(item.t_start(), item.proj_len())), point_id
        t = item.t_start()
        assert frame.loc[t, "claims_lapse"] == item.claims(t, "LAPSE")
        assert frame.loc[t, "pols_if"] == item.pols_if_init()


def test_rv_result_cf_annual_sums_flows_and_takes_counts_at_the_year_start(product_models):
    model = product_models("klassische_rentenversicherung")
    projection = model.Projection
    assert projection.result_cf_annual._is_derived()
    assert projection.result_cf_counts._is_defined()
    item = projection[model.Data.model_point_table().index[0]]
    monthly = item.result_cf()
    annual = item.result_cf_annual()
    assert annual.index.name == "policy_year"
    assert list(annual.columns[:2]) == ["pols_if", "pols_annuity"]
    assert list(annual.columns[2:]) == [c for c in monthly.columns
                                        if c not in ("pols_if", "pols_annuity")]
    for year in annual.index:
        months = [t for t in monthly.index if item.duration(t) + 1 == year]
        start = months[0]
        assert annual.loc[year, "pols_if"] == monthly.loc[start, "pols_if"], year
        assert annual.loc[year, "pols_annuity"] == monthly.loc[start, "pols_annuity"], year
        for column in annual.columns[2:]:
            assert annual.loc[year, column] == pytest.approx(
                monthly.loc[months, column].sum(), rel=1e-12, abs=1e-9), (year, column)


def test_rlv_net_cf_resid_rebuilds_net_cf_from_the_frame(product_models):
    model = product_models("risikolebensversicherung")
    projection = model.Projection
    assert projection.check_net_cf_resid._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.net_cf_income_columns() == ("premiums",)
        assert item.net_cf_outgo_columns() == (
            "claims_death", "claims_lapse", "claims_maturity", "expenses", "commissions")
        frame = item.result_cf()
        for t in frame.index:
            row = frame.loc[t]
            rebuilt = (row["premiums"] - row["claims_death"] - row["claims_lapse"]
                       - row["claims_maturity"] - row["expenses"] - row["commissions"])
            resid = item.check_net_cf_resid(t)
            assert resid == float(row["net_cf"] - rebuilt), (point_id, t)
            assert resid == 0.0, (point_id, t)


def test_klv_check_net_cf_closes_to_the_scaled_tolerance(tmp_path, product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.check_net_cf._is_derived()
    assert projection.check_net_cf_tol._is_derived()
    assert projection.check_net_cf_scale._is_defined()
    point_id = model.Data.model_point_table().index[0]
    item = projection[point_id]
    assert item.check_net_cf() is True
    t = item.t_start()
    assert item.check_net_cf_tol(t) == item.roll_fwd_tol() * max(item.sum_assured(), 1.0)

    # A residual above the tolerance fails the check: a tolerance of -1 is below any |resid|.
    folder = product_copy(tmp_path, "kapitallebensversicherung")
    table = folder / "param_table.csv"
    params = pd.read_csv(table, index_col="item")
    params.loc["roll_fwd_tol", "value"] = -1.0
    params.to_csv(table)
    copy = mx.read_model(folder / MODELS["kapitallebensversicherung"], name="NetCfProbe")
    try:
        assert copy.Projection[point_id].check_net_cf() is False
    finally:
        copy.close()
