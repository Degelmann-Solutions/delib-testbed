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
- The outputs and checks: every product reads ``roll_fwd_tol`` from its ``param_tariff_type.csv``
  and a missing row raises; KLV's ``result_cf`` is the core's statement from ``t_start()``;
  RV's annual frame sums the flows and takes its two counts at the year's start; RLV's
  net-cash-flow residual is rebuilt from its frame's columns; KLV's ``check_net_cf`` closes to
  the scaled tolerance and fails above it.
- The parameter files: ``param(item)`` reads RLV's tariff-type file without a tariff file,
  ``claim_expense`` among it and no longer a Reference of its ``Projection``,
  keeps an integer literal ``int``, reads a fixture core item and a tariff item in a scratch
  copy, and raises on an unknown item and on a missing core file; it equals the
  file's value of every product's every item, and the core's former readers
  ``param_table()`` and ``param_table_dict()`` are gone with every read of them; every
  product's ``param_file`` is its ``param_tariff_type.csv`` with the layer columns, and no
  ``param_table.csv`` is left.
  Riester's 32 former numeric References are rows of its tariff-type file with their
  literals' types and values, and no numeric Reference but ``point_id`` is left on its
  ``Projection``. RLV's 17 likewise, and its premium-shock test switches the module on
  through a row of a scratch copy's tariff-type file. KLV's 4 read ones likewise; its
  three References of the lapse modules that were never built, read by no cell, are in
  neither its ``Projection`` nor its parameter files. BU's 11, FRV's 12, Basis' 5,
  Index' 10 and 8 of Sofort's 10 likewise; Sofort's other 2, the bisection settings of its
  refund solve, are literals in its formula. RV and Pflege never had one.
  Every product's core layer is ``rate_cap_eps``, 1e-12 as a ``float``; Pflege's eleven
  guards read it, and no ``1e-12`` literal is left in its formulas. FRV's 3 actuarial
  formula literals (the tax step of ``lapse_tax_step``) are rows of its
  tariff-type file with their literals' types and values; Index' five-year spread and KLV's
  five-year spread and three-year suicide window likewise. Every other numeric literal of a
  formula cell of the core and the ten products, but 0, 1, 0.0 and 1.0, is structural and
  listed for its space in ``STRUCTURAL_LITERALS``, and every listed value occurs there.
  BU's claim-year caps are the last ``dur_year`` of its claim-duration table, so a scratch
  copy with a twelfth row reads it; Pflege's surrender cap is the last policy year of its
  surrender table likewise. The nine products with a regular premium read their premium
  frequencies from one ``prem_freq_table.csv``, keyed ``annual`` to ``monthly``, with
  ``instalments`` an ``int`` a year, and every model point's ``prem_freq`` is a key; Basis'
  single premium reads no loading, Pflege's is the premium form ``single``, not a frequency.
  ``prem_form`` is ``regular`` or ``single`` in the six products that have it, and an unknown
  form raises. Sofort's annuity frequencies are the keys of its ``ann_freq_table.csv``. A
  frequency outside its table raises (FRV, Pflege, Sofort), and a row added to a scratch copy
  admits it. Riester's annuity frequency is a row ``ann_freq``, 12 as an ``int`` as Basis', and
  the *Rentenfaktor* unit of FRV, Index, RV and Riester a row ``rf_unit``, 10000.0 as Basis'.
  Every product's ``param_layers()`` holds each item once and merges into ``param_dict()``;
  the loader raises ``ValueError`` on an item in two layers, twice in one file, and on a core
  item in the tariff-type or the tariff file.
- The usage scan ``core/param_usage.py``: every product reads every item of its layers
  through a reachable literal ``param`` call and the core file has no unused item; on a
  scratch copy it reports an unused item of either product layer, a call to a missing item,
  an undeclared indirect read, a declared item no layer holds, a declared cell that does not
  exist and a read around ``param``, counts a declared indirect read, and names an unused
  core item.
- The expense inflation: Sofort's derived factor steps on the policy anniversary, Pflege's
  compounds continuously over ``t / 12`` years.
- The dict cells: every core dict cell of a table a product has equals its reader's
  DataFrame; the lookups through them keep their clamp and errors (the lapse rate beyond the
  table, an unknown ``prem_freq``, a missing ``expense_infl`` row, an issue year outside every
  *Höchstrechnungszins* band), and a table the product lacks is never read.
- Pflege's own dict cells equal their readers; its care-grade rates are keyed by attained
  age and grade, not by month, and keep their limiting-age, recovery-damping and grade-5
  values; a missing ``rec_margin`` row raises; its entrants and graduations are the ledger's
  own and equal the formulas they had beside it; its month-keyed rates depend on the month only
  through the attained age, as the age-keyed transitions assume.
- The shared caches are read-only: every product's ``model_point()``, FRV's ``charge_row()``
  and BU's cohort index and step arrays, their slices included, raise on a write.
- RV's and KLV's own dict cells and scenario bounds equal their readers; their
  decrement-closure residual equals the old sum over the exit cells up to floating-point
  noise, on a new and an in-force point; their lookups keep their clamps (the declared rate
  outside the calendar range, the surplus rates and the *Stornoabzug* beyond the last policy year, the DeckRV
  ceilings outside the issue years), ``echt`` instalments carry no loading, and an unknown
  scenario raises.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import math
import re
import shutil
import subprocess
from pathlib import Path

import modelx as mx
import numpy as np
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
        "charge_table_index": {"basisrente": "override",
                               "fondsgebundene_rentenversicherung": "derived",
                               "kapitallebensversicherung": "override",
                               "klassische_rentenversicherung": "override"},
        "charge_table": {"basisrente": "derived",
                         "fondsgebundene_rentenversicherung": "derived",
                         "kapitallebensversicherung": "derived",
                         "klassische_rentenversicherung": "derived"},
        "hoechstrechnungszins_table": {"sofortrente": "derived"},
        "model_point_table_dict": dict.fromkeys(MODELS, "derived"),
        "param_core_path": dict.fromkeys(MODELS, "derived"),
        "param_tariff_path": dict.fromkeys(MODELS, "derived"),
        "param_layers": dict.fromkeys(MODELS, "derived"),
        "param_dict": dict.fromkeys(MODELS, "derived"),
        "param": dict.fromkeys(MODELS, "derived"),
        "param_indirect": dict.fromkeys(MODELS, "derived"),
        "mort_table_dict": dict.fromkeys(MODELS, "derived"),
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
                             "klassische_rentenversicherung": "override",
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
        "expense_infl": {"basisrente": "override",
                         "fondsgebundene_rentenversicherung": "derived",
                         "indexpolice": "derived",
                         "kapitallebensversicherung": "override",
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


def tariff_type_table(product):
    """The product's ``param_tariff_type.csv`` as pandas reads it, by ``item``."""
    return pd.read_csv(PRODUCTS_DIR / product / "param_tariff_type.csv", index_col="item")


def test_pflege_tariff_type_file_holds_the_two_merged_tables(product_models):
    product = "pflegerentenversicherung"
    model = product_models(product)
    merged = tariff_type_table(product)
    basis = upstream_table(product, "basis_table.csv", index_col="param")
    expense = upstream_table(product, "expense_table.csv", index_col="item")
    # The Rechnungszins moved from the table to the model point (a contract attribute).
    moved = ["rechnungszins"]
    points = model.Data.model_point_table()
    for item in moved:
        assert (points[item] == basis.at[item, "value"]).all(), item
    basis = basis.drop(moved)
    assert list(merged.columns) == ["value", "unit", "basis", "provenance"]
    assert list(merged.index) == list(basis.index) + list(expense.index)
    assert merged["basis"].isna().all()
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
    points = model.Data.model_point_table().copy()
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
    points = model.Data.model_point_table().copy()
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


def test_klv_mort_rate_steps_its_table_by_the_factor_from_its_tariff_type_file(product_models):
    model = product_models("kapitallebensversicherung")
    projection = model.Projection
    assert projection.mort_rate._is_derived()
    assert projection.mort_be_factor._is_defined()
    assert model.Data.param("mort_be_factor") == 0.75
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


def test_rlv_lapse_rate_is_the_table_rate_times_the_shock_factor(tmp_path):
    """With the premium-shock module on and the declaration cut in year 4, the shock fires."""
    folder = product_copy(tmp_path, "risikolebensversicherung")
    param_file = folder / "param_tariff_type.csv"
    text = param_file.read_text(encoding="utf-8")
    assert text.count("\nshock_lapse_lambda,0.0,") == 1
    param_file.write_text(text.replace("\nshock_lapse_lambda,0.0,", "\nshock_lapse_lambda,2.0,"),
                          encoding="utf-8")
    model = mx.read_model(folder / MODELS["risikolebensversicherung"], name="ShockProbe")
    try:
        projection = model.Projection
        assert projection.lapse_rate._is_derived()
        assert model.Data.param("shock_lapse_lambda") == 2.0
        projection.new_cells("prem_rebate_level_pp", formula=projection.prem_rebate_pp.formula)
        projection.prem_rebate_pp.formula = _rebate_cut_from_policy_year_4
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
def test_roll_fwd_tol_is_read_from_its_tariff_type_file(product, product_models):
    model = product_models(product)
    projection = model.Projection
    assert projection.roll_fwd_tol._is_derived()
    assert "roll_fwd_tol" not in projection.refs
    point_id = model.Data.model_point_table().index[0]
    assert projection[point_id].roll_fwd_tol() == ROLL_FWD_TOL[product]


def test_roll_fwd_tol_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "kapitallebensversicherung")
    table = folder / "param_tariff_type.csv"
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


def test_param_reads_the_tariff_type_layer(product_models):
    data = product_models("risikolebensversicherung").Data
    assert data.param._is_derived() and data.param_dict._is_derived()
    assert not data.param_tariff_path().exists()
    assert data.param_core_path() == data.model.path / "CoreData" / "param_core.csv"
    assert data.param_core_path().is_file()
    for item in ("roll_fwd_tol", "expense_infl"):
        value = data.param(item)
        assert type(value) is float and value == tariff_type_table(
            "risikolebensversicherung").at[item, "value"], item


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
    """``param(item)`` is the value pandas reads for every item of the tariff-type file."""
    data = product_models(product).Data
    values = tariff_type_table(product)["value"].to_dict()
    assert values
    for item, value in values.items():
        assert data.param(item) == value, item


@pytest.mark.parametrize("product, omega", [("klassische_rentenversicherung", 121),
                                             ("pflegerentenversicherung", 110),
                                             ("sofortrente", 121)])
def test_omega_age_is_an_int(product, omega, product_models):
    """Every file writes ``omega_age`` as an integer, so ``param`` gives an ``int``; so does
    Pflege's ``beitragssumme_cap_age`` (``85``)."""
    model = product_models(product)
    assert type(model.Data.param("omega_age")) is int
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
        for item, text in pd.read_csv(path, dtype=str, keep_default_na=False)[
                ["item", "value"]].itertuples(index=False):
            kind = "int" if text.strip().lstrip("+-").isdigit() else "float"
            types.setdefault(item, {}).setdefault(kind, []).append(path.parent.name)
    mixed = {item: kinds for item, kinds in types.items() if len(kinds) > 1}
    assert not mixed, mixed


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_product_reads_its_tariff_type_file(product, product_models):
    """``param_file`` is ``param_tariff_type.csv``, in the layer columns, and no
    ``param_table.csv`` is left; Pflege keeps its ``unit`` column before ``basis``."""
    assert product_models(product).Data.param_file == "param_tariff_type.csv"
    folder = PRODUCTS_DIR / product
    assert not (folder / "param_table.csv").exists()
    header = (folder / "param_tariff_type.csv").read_text(encoding="utf-8").splitlines()[0]
    expected = ("item,value,unit,basis,provenance" if product == "pflegerentenversicherung"
                else "item,value,basis,provenance")
    assert header == expected


def test_rlv_claim_expense_is_a_tariff_type_row(product_models):
    model = product_models("risikolebensversicherung")
    data = model.Data
    assert data.param_file == "param_tariff_type.csv"
    value = data.param("claim_expense")
    assert type(value) is float and value == 250.0
    assert "claim_expense" not in model.Projection.refs
    item = model.Projection[model.Data.model_point_table().index[0]]
    for t in range(item.t_start(), item.t_start() + 24):
        assert item.expenses_claim(t) == 250.0 * item.pols_death(t), t


# The 32 numeric References Riester's ``Projection`` held, as their former Python literals.
RIESTER_MOVED_REFERENCES = {
    "valuation_year": 2027,
    "grundzulage": 175.0,
    "kinderzulage_pre2008": 185.0,
    "kinderzulage_post2008": 300.0,
    "berufseinsteiger_bonus": 200.0,
    "mindest_rate": 0.04,
    "foerder_ceiling": 2100.0,
    "sockelbeitrag": 60.0,
    "zulage_lag": 1,
    "charge_acq_bsum_once": 0.025,
    "acq_spread_years": 5,
    "charge_admin_prem_inst": 0.04,
    "charge_admin_pp_ann": 12.0,
    "guar_carve_out_cap": 0.2,
    "slueb_rate": 0.02,
    "bwr_rate": 0.01,
    "teilkapital_cap": 0.3,
    "kleinbetrag_threshold_mth": 39.55,
    "rentenfaktor_margin": 0.3,
    "annuity_rechnungszins": 0.01,
    "woolhouse": 0.4583333333333333,
    "annuity_mort_be_factor": 1.15,
    "mort_base_year": 2027,
    "stornoabzug_rate": 0.02,
    "charge_transfer_pp_once": 50.0,
    "expense_admin_pp_ann": 30.0,
    "expense_annuity_pp_ann": 24.0,
    "expense_claim_pp_once": 80.0,
    "expense_acq_pp_once": 150.0,
    "expense_acq_bsum_once": 0.02,
    "comm_acq_bsum_once": 0.025,
    "comm_renew_prem_inst": 0.015,
}

# The 17 numeric References RLV's ``Projection`` held, as their former Python literals.
RLV_MOVED_REFERENCES = {
    "sicherheitszuschlag_m": 1.25,
    "sex_mix_male": 0.5,
    "surplus_share": 0.9,
    "decl_scale": 1.0,
    "v_max": 0.95,
    "zillmer_rate": 0.025,
    "comm_rate_init": 0.02,
    "beta_tariff": 0.05,
    "gamma_rate": 0.0003,
    "maint_prem_pct": 0.03,
    "comm_rate_renew": 0.01,
    "suicide_share": 0.03,
    "suicide_years": 3,
    "shock_lapse_lambda": 0.0,
    "sel_lapse_lambda": 0.0,
    "sel_lapse_ref": 0.25,
    "val_tol": 1e-09,
}

# The 4 numeric References KLV's ``Projection`` held and its cells read, as their former
# Python literals.
KLV_MOVED_REFERENCES = {
    "suicide_share": 0.02,
    "bfz_min_si": 2500.0,
    "term_surr_share": 0.0,
    "bwr_rate": 0.0,
}

# The 11 numeric References BU's ``Projection`` held, as their former Python literals.
BU_MOVED_REFERENCES = {
    "accept_factor": 0.8,
    "inc_load_first": 1.3,
    "recov_load_first": 0.7,
    "mort_dis_load_first": 0.8,
    "mort_actv_load_first": 0.8,
    "load_acq_bsum_once": 0.025,
    "load_admin_prem_inst": 0.09,
    "load_admin_pp_ann": 18.0,
    "load_claim_assess_pp_once": 800.0,
    "load_claim_admin_pp_mth": 12.0,
    "runoff_months": 3,
}

# The 12 numeric References FRV's ``Projection`` held, as their former Python literals.
FRV_MOVED_REFERENCES = {
    "lapse_cap": 0.4,
    "lapse_dyn_beta": 0.0,
    "mmkt_return_ann": 0.015,
    "glide_months": 60,
    "comm_acq_bsum_once": 0.025,
    "expense_acq_pp_once": 200.0,
    "expense_admin_pp_mth": 4.0,
    "comm_renew_prem_inst": 0.015,
    "expense_claim_pp_once": 150.0,
    "expense_surr_pp_once": 50.0,
    "expense_conv_pp_once": 100.0,
    "val_tol": 1e-10,
}

# The 3 actuarial literals FRV's formulas held (``lapse_tax_step``), as written there.
FRV_MOVED_LITERALS = {
    "tax_step_min_year": 13,
    "tax_step_age": 62,
    "tax_step_factor": 2.5,
}

# The actuarial literal Index' formulas held (``prem_charge_acq_min_pp``), as written there.
INDEX_MOVED_LITERALS = {"surr_spread_years": 5}

# The actuarial literals KLV's formulas held (``res_min_pp``, ``benefit_death_pp``), as rows.
# ``surr_spread_years`` was ``5.0`` there; its row is ``5``, an ``int`` as Index' row.
KLV_MOVED_LITERALS = {"surr_spread_years": 5, "suicide_years": 3}

# The 5 numeric References Basis' ``Projection`` held, as their former Python literals.
BASIS_MOVED_REFERENCES = {
    "elig_surv_prob": 0.55,
    "mort_base_year": 2005,
    "acq_spread_years": 5,
    "rf_unit": 10000.0,
    "ann_freq": 12,
}

# The 10 numeric References Index' ``Projection`` held, as their former Python literals.
INDEX_MOVED_REFERENCES = {
    "charge_acq_bsum_once": 0.025,
    "expense_acq_bsum_once": 0.025,
    "acq_spread_years": 5,
    "zillmer_cap_bsum": 0.025,
    "charge_admin_prem_inst": 0.03,
    "charge_admin_av_ann": 0.0025,
    "expense_admin_pp_ann": 36.0,
    "stornoabzug_rate": 0.02,
    "rentenfaktor_guar": 25.0,
    "rentenfaktor_curr": 25.0,
}

# 8 of the 10 numeric References Sofort's ``Projection`` held, as their former Python literals;
# the other 2, ``solve_tol`` 1e-10 and ``solve_max_iter`` 200, are literals of ``annuity_pp_derived``.
SOFORT_MOVED_REFERENCES = {
    "load_acq_sp_once": 0.025,
    "load_admin_annval_once": 0.02,
    "expense_acq_sp_once": 0.02,
    "expense_acq_pp_once": 200.0,
    "expense_admin_pp_ann": 60.0,
    "expense_pay_pp_inst": 1.5,
    "unisex_mix_male": 0.45,
    "mort_base_year": 2025,
}

# The products whose numeric References have all moved into their parameter files: all ten,
# RV and Pflege having never had one.
REFERENCES_MOVED = (
    "riester_rente", "risikolebensversicherung", "kapitallebensversicherung",
    "berufsunfaehigkeit", "fondsgebundene_rentenversicherung", "basisrente",
    "indexpolice", "sofortrente", "klassische_rentenversicherung",
    "pflegerentenversicherung",
)


def test_riester_references_are_tariff_type_rows(product_models):
    model = product_models("riester_rente")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(RIESTER_MOVED_REFERENCES) == 32
    for item, literal in RIESTER_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_rlv_references_are_tariff_type_rows(product_models):
    model = product_models("risikolebensversicherung")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(RLV_MOVED_REFERENCES) == 17
    for item, literal in RLV_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_klv_references_are_tariff_type_rows(product_models):
    model = product_models("kapitallebensversicherung")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(KLV_MOVED_REFERENCES) == 4
    for item, literal in KLV_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_bu_references_are_tariff_type_rows(product_models):
    model = product_models("berufsunfaehigkeit")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(BU_MOVED_REFERENCES) == 11
    for item, literal in BU_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_frv_references_are_tariff_type_rows(product_models):
    model = product_models("fondsgebundene_rentenversicherung")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(FRV_MOVED_REFERENCES) == 12
    for item, literal in FRV_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_frv_literals_are_tariff_type_rows(product_models):
    data = product_models("fondsgebundene_rentenversicherung").Data
    layer = data.param_layers()["tariff_type"]
    assert len(FRV_MOVED_LITERALS) == 3
    for item, literal in FRV_MOVED_LITERALS.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item


def test_index_literals_are_tariff_type_rows(product_models):
    data = product_models("indexpolice").Data
    layer = data.param_layers()["tariff_type"]
    assert len(INDEX_MOVED_LITERALS) == 1
    for item, literal in INDEX_MOVED_LITERALS.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item


def test_klv_literals_are_tariff_type_rows(product_models):
    data = product_models("kapitallebensversicherung").Data
    layer = data.param_layers()["tariff_type"]
    assert len(KLV_MOVED_LITERALS) == 2
    for item, literal in KLV_MOVED_LITERALS.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item


# The units and annuity frequencies that are rows rather than literals: product -> item ->
# value. Basis' were References; the others were literals in formulas. One quantity has one
# item name and one type in every product.
UNIT_AND_FREQUENCY_ROWS = {
    "basisrente": {"rf_unit": 10000.0, "ann_freq": 12},
    "fondsgebundene_rentenversicherung": {"rf_unit": 10000.0},
    "indexpolice": {"rf_unit": 10000.0},
    "klassische_rentenversicherung": {"rf_unit": 10000.0},
    "riester_rente": {"rf_unit": 10000.0, "ann_freq": 12},
}


@pytest.mark.parametrize("product", sorted(UNIT_AND_FREQUENCY_ROWS))
def test_units_and_frequencies_are_tariff_type_rows(product, product_models):
    data = product_models(product).Data
    layer = data.param_layers()["tariff_type"]
    for item, literal in UNIT_AND_FREQUENCY_ROWS[product].items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item


def test_basis_references_are_tariff_type_rows(product_models):
    model = product_models("basisrente")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(BASIS_MOVED_REFERENCES) == 5
    for item, literal in BASIS_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_index_references_are_tariff_type_rows(product_models):
    model = product_models("indexpolice")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(INDEX_MOVED_REFERENCES) == 10
    for item, literal in INDEX_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


def test_sofort_references_are_tariff_type_rows(product_models):
    model = product_models("sofortrente")
    data = model.Data
    layer = data.param_layers()["tariff_type"]
    assert len(SOFORT_MOVED_REFERENCES) == 8
    for item, literal in SOFORT_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layer, item
        assert item not in model.Projection.refs, item


# The items of the core file ``core/Core/Data/param_core.csv``, as their former Python literals.
CORE_ITEMS = {"rate_cap_eps": 1e-12}


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_product_reads_the_core_items(product, product_models):
    core = product_models(product).Data.param_layers()["core"]
    assert core == CORE_ITEMS
    assert all(type(core[item]) is type(literal) for item, literal in CORE_ITEMS.items())


def test_pflege_guards_read_the_core_epsilon():
    """Pflege's eleven guards ``1.0 - 1e-12`` read ``1.0 - data.param("rate_cap_eps")``, and
    no ``1e-12`` literal is left in its formulas (its docstrings still give the value)."""
    path = PRODUCTS_DIR / "pflegerentenversicherung" / MODELS["pflegerentenversicherung"]
    text = (path / "Projection" / "__init__.py").read_text(encoding="utf-8")
    literals = [node for node in ast.walk(ast.parse(text))
                if isinstance(node, ast.Constant) and type(node.value) is float
                and node.value == 1e-12]
    assert literals == []
    assert text.count('1.0 - data.param("rate_cap_eps")') == 11


# The structural numeric literals of the formula cells, by space, as ``repr`` of the value
# (docs/core.md, "Formula literals"): every other literal of a formula is a parameter row.
STRUCTURAL_LITERALS = {
    "core": {"11", "12", "12.0"},
    "basisrente": {"12", "12.0"},
    "berufsunfaehigkeit": {"2", "12", "12.0"},
    "fondsgebundene_rentenversicherung": {"0.5", "0.99", "5.0", "12", "12.0", "200"},
    "indexpolice": {"11", "12", "12.0", "13"},
    "kapitallebensversicherung": {"11", "12", "12.0"},
    "klassische_rentenversicherung": {"2", "12", "12.0"},
    "pflegerentenversicherung": {"2", "3", "4", "5", "12", "12.0", "1000.0"},
    "riester_rente": {"12", "12.0"},
    "risikolebensversicherung": {"2", "12", "12.0"},
    "sofortrente": {"0.5", "1e-10", "2", "12", "12.0", "200"},
}


def _formula_cells(path: Path):
    """The formula cells of a ``Projection``, as docs/roadmap.md, "The new M", counts them:
    module-level ``def``s and non-underscore ``name = lambda``, each with its name."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef):
            yield node.name, node
        elif (isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda)
              and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
              and not node.targets[0].id.startswith("_")):
            yield node.targets[0].id, node.value


def test_formula_literals_are_listed_as_structural():
    """Every numeric literal of a formula cell but 0, 1, 0.0 and 1.0, subscripts and
    ``range(...)`` included, is listed for its space, and every listed value occurs there."""
    assert sorted(STRUCTURAL_LITERALS) == sorted(["core", *MODELS])
    paths = {"core": CORE_MODEL / "Projection" / "__init__.py"}
    paths.update({product: PRODUCTS_DIR / product / model / "Projection" / "__init__.py"
                  for product, model in MODELS.items()})
    unlisted, found = [], {}
    for space, path in paths.items():
        found[space] = set()
        for name, cell in _formula_cells(path):
            for node in ast.walk(cell):
                if (isinstance(node, ast.Constant) and type(node.value) in (int, float)
                        and node.value not in (0, 1)):
                    found[space].add(repr(node.value))
                    if repr(node.value) not in STRUCTURAL_LITERALS[space]:
                        unlisted.append(f"{space}: {name} line {node.lineno}: {node.value!r}")
    assert not unlisted, unlisted
    assert found == STRUCTURAL_LITERALS


# KLV's switches of two lapse modules that were specified and never built, read by no cell.
KLV_UNREAD_REFERENCES = ("beta_shock", "lapse_gap_a", "ref_rate")


def test_klv_unread_references_are_removed(product_models):
    model = product_models("kapitallebensversicherung")
    items = model.Data.param_dict()
    for name in KLV_UNREAD_REFERENCES:
        assert name not in model.Projection.refs, name
        assert name not in items, name


@pytest.mark.parametrize("product", REFERENCES_MOVED)
def test_no_numeric_projection_reference_remains(product, product_models):
    refs = product_models(product).Projection.refs
    numeric = {
        name: value for name, value in refs.items()
        if name != "point_id" and isinstance(value, (int, float)) and not isinstance(value, bool)
    }
    assert numeric == {}


def _add_params(path: Path, values: dict[str, str]) -> None:
    """Append one row per item to a parameter file, its value as text, in the file's columns.

    A file that does not exist is created with the columns of the layer files.
    """
    text = (path.read_text(encoding="utf-8") if path.exists()
            else "item,value,basis,provenance\n")
    columns = text.splitlines()[0].split(",")
    for item, value in values.items():
        row = {"item": item, "value": value, "provenance": "[std] test fixture"}
        text += ",".join(row.get(column, "") for column in columns) + "\n"
    path.write_text(text, encoding="utf-8")


def test_param_keeps_an_integer_literal_int(tmp_path, product_models):
    param_file = product_models("risikolebensversicherung").Data.param_file
    folder = product_copy(tmp_path, "risikolebensversicherung")
    _add_params(folder / param_file,
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
    _add_params(core_file, {"probe_core": "0.125"})
    _add_params(folder / "param_tariff.csv", {"probe_tariff": "7"})
    copy = mx.read_model(model_dir, name="CoreItemProbe")
    try:
        assert copy.Data.param("probe_core") == 0.125
        assert copy.Data.param("probe_tariff") == 7
        assert copy.Data.param("roll_fwd_tol") == 1e-10
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
            copy.Data.param("roll_fwd_tol")
    finally:
        copy.close()


@pytest.mark.parametrize("product", sorted(MODELS))
def test_param_layers_hold_every_item_once_and_merge_into_param_dict(product, product_models):
    """Every product reads the core and the tariff-type layer (and the tariff layer only where
    the file exists), each item in one layer, and ``param_dict()`` is their merge."""
    data = product_models(product).Data
    layers = data.param_layers()
    expected = ["core", "tariff_type"] + (["tariff"] if data.param_tariff_path().is_file()
                                          else [])
    assert list(layers) == expected
    tariff_type = pd.read_csv(data.input_dir() / data.param_file, dtype=str,
                              keep_default_na=False)["item"].tolist()
    assert sorted(layers["tariff_type"]) == sorted(tariff_type)
    assert len(tariff_type) == len(set(tariff_type))
    items = [item for layer in layers.values() for item in layer]
    assert len(items) == len(set(items))
    merged = {item: value for layer in layers.values() for item, value in layer.items()}
    assert data.param_dict() == merged
    assert list(data.param_dict()) == list(merged)


def _loader_error(model_dir: Path, name: str, item: str = "roll_fwd_tol") -> str:
    """The error line of the loader's error on ``param(item)`` in a scratch copy, which must be
    a ``ValueError``.

    modelx wraps it in a ``FormulaError`` whose text also holds the formula source; only the
    line before ``Formula traceback:`` is the raised error.
    """
    copy = mx.read_model(model_dir, name=name)
    try:
        with pytest.raises(Exception) as raised:
            copy.Data.param(item)
    finally:
        copy.close()
    if isinstance(raised.value, ValueError):
        return f"ValueError: {raised.value}"
    head = str(raised.value).split("Formula traceback:", 1)[0]
    line = [text for text in head.splitlines() if text.strip()][-1]
    assert line.startswith("ValueError: "), str(raised.value)
    return line


def test_param_rejects_an_item_in_two_layers(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    _add_params(folder / "param_tariff.csv", {"expense_infl": "0.03"})
    message = _loader_error(folder / MODELS["risikolebensversicherung"], "TwoLayerProbe")
    assert "'expense_infl' stands in two layers" in message
    assert str(folder / "param_tariff_type.csv") in message
    assert str(folder / "param_tariff.csv") in message


def test_param_rejects_an_item_twice_in_one_file(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    _add_params(folder / "param_tariff_type.csv", {"roll_fwd_tol": "1e-10"})
    message = _loader_error(folder / MODELS["risikolebensversicherung"], "TwiceProbe")
    assert "'roll_fwd_tol' stands twice in" in message
    assert str(folder / "param_tariff_type.csv") in message


def test_param_rejects_a_core_item_in_the_tariff_type_file(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    model_dir = folder / MODELS["risikolebensversicherung"]
    _add_params(model_dir / "CoreData" / "param_core.csv", {"roll_fwd_tol": "1e-10"})
    message = _loader_error(model_dir, "CoreLockProbe")
    assert "'roll_fwd_tol' is a core item of" in message
    assert str(folder / "param_tariff_type.csv") in message


def test_param_rejects_a_core_item_in_the_tariff_file(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    model_dir = folder / MODELS["risikolebensversicherung"]
    _add_params(model_dir / "CoreData" / "param_core.csv", {"probe_core": "0.125"})
    _add_params(folder / "param_tariff.csv", {"probe_core": "0.25"})
    message = _loader_error(model_dir, "CoreLockTariffProbe")
    assert "'probe_core' is a core item of" in message
    assert str(folder / "param_tariff.csv") in message


def load_param_usage():
    """The static usage scan ``core/param_usage.py``, a plain module beside the core model."""
    spec = importlib.util.spec_from_file_location("param_usage", CORE_DIR / "param_usage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


param_usage = load_param_usage()


def _usage_copy(tmp_path, name: str, edit=None):
    """The scan of a scratch RLV copy, after ``edit(folder)`` changed its files, and the copy;
    the caller closes it."""
    folder = product_copy(tmp_path, "risikolebensversicherung")
    if edit is not None:
        edit(folder)
    return mx.read_model(folder / MODELS["risikolebensversicherung"], name=name)


def _add_cell(model, space: str, source: str) -> None:
    name = source.split("(", 1)[0].removeprefix("def ")
    model.spaces[space].new_cells(name=name, formula=source)


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_usage_scan_finds_no_problem(product, product_models):
    """Every shipped product reads every item of its layers, calls no missing item, reads
    no parameter indirectly and does not bypass ``param``."""
    model = product_models(product)
    usage = param_usage.scan(model)
    assert usage.problems == []
    assert usage.indirect == {}
    assert usage.reads and set(usage.reads) <= set(model.Data.param_dict())
    assert {"param", "param_dict", "param_layers"} <= usage.reachable


def test_no_core_item_is_unused(product_models):
    usages = [param_usage.scan(product_models(product)) for product in sorted(MODELS)]
    assert param_usage.unused_core_items(usages) == []


def test_the_usage_scan_counts_a_core_cell_only_where_it_is_reachable(product_models):
    """Pflege reads ``expense_infl`` through the core's ``expense_infl()``, RLV's
    ``omega_age()`` is inherited but reached by nothing."""
    pflege = param_usage.scan(product_models("pflegerentenversicherung"))
    assert "expense_infl" in pflege.reads["expense_infl"]
    rlv = param_usage.scan(product_models("risikolebensversicherung"))
    assert "omega_age" not in rlv.reachable and "omega_age" not in rlv.reads
    assert "expenses_claim" in rlv.reads["claim_expense"]


def test_the_usage_scan_reports_an_unused_item_in_each_product_layer(tmp_path):
    def edit(folder):
        _add_params(folder / "param_tariff_type.csv", {"probe_unused": "1.5"})
        _add_params(folder / "param_tariff.csv", {"probe_unused_tariff": "2.5"})

    copy = _usage_copy(tmp_path, "UnusedProbe", edit)
    try:
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 2, problems
    assert "'probe_unused'" in problems[0] and "tariff_type layer" in problems[0]
    assert "param_tariff_type.csv" in problems[0]
    assert "'probe_unused_tariff'" in problems[1] and "tariff layer" in problems[1]
    assert "param_tariff.csv" in problems[1]


def test_the_usage_scan_reports_a_call_to_a_missing_item(tmp_path):
    def edit(folder):
        table = folder / "param_tariff_type.csv"
        params = pd.read_csv(table, dtype=str, keep_default_na=False, index_col="item")
        params.drop(index="claim_expense").to_csv(table)

    copy = _usage_copy(tmp_path, "MissingProbe", edit)
    try:
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "'claim_expense'" in problems[0] and "expenses_claim" in problems[0]
    assert "no layer" in problems[0]


INDIRECT_CELL = ('def probe_indirect():\n'
                 '    name = "expense_infl"\n'
                 '    return data.param(name)\n')


def test_the_usage_scan_reports_an_undeclared_indirect_read(tmp_path):
    copy = _usage_copy(tmp_path, "IndirectProbe")
    try:
        _add_cell(copy, "Projection", INDIRECT_CELL)
        _add_cell(copy, "Projection", "def probe_reader():\n    return probe_indirect()\n")
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert "probe_indirect" in usage.reachable
    assert len(usage.problems) == 1, usage.problems
    assert "probe_indirect" in usage.problems[0] and "param_indirect()" in usage.problems[0]


def _declare(model, declared: dict) -> None:
    model.Data.cells["param_indirect"].formula = (
        f"def param_indirect():\n    return {declared!r}\n")


def test_the_usage_scan_counts_a_declared_indirect_read(tmp_path):
    copy = _usage_copy(tmp_path, "DeclaredProbe")
    try:
        _add_cell(copy, "Projection", INDIRECT_CELL)
        _declare(copy, {"probe_indirect": ("expense_infl",)})
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert usage.problems == []
    assert usage.indirect == {"probe_indirect": ("expense_infl",)}
    assert "probe_indirect" in usage.reads["expense_infl"]


def test_the_usage_scan_reports_a_declared_item_no_layer_holds(tmp_path):
    copy = _usage_copy(tmp_path, "DeclaredMissingProbe")
    try:
        _add_cell(copy, "Projection", INDIRECT_CELL)
        _declare(copy, {"probe_indirect": ("expense_infl", "probe_missing")})
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "'probe_missing'" in problems[0] and "probe_indirect" in problems[0]


def test_the_usage_scan_reports_a_declared_cell_that_does_not_exist(tmp_path):
    copy = _usage_copy(tmp_path, "DeclaredUnknownProbe")
    try:
        _declare(copy, {"probe_nowhere": ("expense_infl",)})
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "probe_nowhere" in problems[0] and "no cell" in problems[0]


@pytest.mark.parametrize("reader", ["param_dict", "param_layers"])
def test_the_usage_scan_reports_a_read_around_param(tmp_path, reader):
    copy = _usage_copy(tmp_path, "BypassProbe")
    try:
        _add_cell(copy, "Projection", f"def probe_bypass():\n    return data.{reader}()\n")
        problems = param_usage.scan(copy).problems
    finally:
        copy.close()
    assert len(problems) == 1, problems
    assert "probe_bypass" in problems[0] and reader in problems[0]


def test_the_usage_scan_reports_a_declared_missing_item_of_an_unreachable_cell(tmp_path):
    """RLV inherits the core's ``omega_age`` unreached; a declared item no layer holds is a
    problem there too."""
    copy = _usage_copy(tmp_path, "DeclaredUnreachableProbe")
    try:
        _declare(copy, {"omega_age": ("probe_missing",)})
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert "omega_age" not in usage.reachable
    assert len(usage.problems) == 1, usage.problems
    assert "'probe_missing'" in usage.problems[0] and "omega_age" in usage.problems[0]


def test_a_core_item_read_by_one_product_is_used():
    """``unused_core_items`` checks the core file across products: an item one product reads
    is used, one that none reads is named."""
    layers = {"core": {"probe_core": 0.125}, "tariff_type": {}}
    reader = param_usage.Usage(layers=layers, reads={"probe_core": frozenset({"cell"})},
                               reachable=frozenset({"cell"}), indirect={}, problems=[])
    other = param_usage.Usage(layers=layers, reads={}, reachable=frozenset(), indirect={},
                              problems=[])
    assert param_usage.unused_core_items([reader, other]) == []
    assert param_usage.unused_core_items([other, other]) == ["probe_core"]


def test_an_unused_core_item_is_named(tmp_path):
    def edit(folder):
        model_dir = folder / MODELS["risikolebensversicherung"]
        _add_params(model_dir / "CoreData" / "param_core.csv", {"probe_core": "0.125"})

    copy = _usage_copy(tmp_path, "UnusedCoreProbe", edit)
    try:
        usage = param_usage.scan(copy)
    finally:
        copy.close()
    assert usage.problems == []
    assert usage.layers["core"] == {**CORE_ITEMS, "probe_core": 0.125}
    assert param_usage.unused_core_items([usage]) == sorted(["probe_core", *CORE_ITEMS])


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


@pytest.mark.parametrize("product", [
    "kapitallebensversicherung", "klassische_rentenversicherung", "riester_rente",
    "risikolebensversicherung"])
def test_net_cf_resid_reads_the_frame_through_its_dict(product_models, product):
    model = product_models(product)
    projection = model.Projection
    assert projection.check_net_cf_resid._is_derived()
    assert projection.result_cf_dict._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        frame = item.result_cf()
        columns = item.result_cf_dict()
        assert list(columns) == list(frame.columns), point_id
        for label in frame.columns:
            assert list(columns[label]) == list(frame.index), (point_id, label)
            for t in frame.index:
                assert columns[label][t] == frame.at[t, label], (point_id, label, t)
        with pytest.raises(Exception, match=f"KeyError: {item.proj_len()}\n"):
            item.check_net_cf_resid(item.proj_len())


def _resid_just_above_tolerance(t):
    """A residual a little above the month's scaled tolerance."""
    return check_net_cf_tol(t) * 1.01                                # noqa: F821


def _resid_just_below_tolerance(t):
    """A residual a little below the month's scaled tolerance."""
    return -check_net_cf_tol(t) * 0.99                               # noqa: F821


def test_klv_check_net_cf_closes_to_the_scaled_tolerance(product_models):
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

    # A residual just below roll_fwd_tol() * check_net_cf_scale(t) passes, one just above fails.
    folder = PRODUCTS_DIR / "kapitallebensversicherung" / MODELS["kapitallebensversicherung"]
    copy = mx.read_model(folder, name="NetCfProbe")
    try:
        copy.Projection.check_net_cf_resid.formula = _resid_just_below_tolerance
        assert copy.Projection[point_id].check_net_cf() is True
        copy.Projection.check_net_cf_resid.formula = _resid_just_above_tolerance
        assert copy.Projection[point_id].check_net_cf() is False
    finally:
        copy.close()


def test_sofort_inflation_factor_steps_on_the_policy_anniversary(product_models):
    model = product_models("sofortrente")
    projection = model.Projection
    assert projection.inflation_factor._is_derived()
    assert projection.inflation_years._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.expense_infl() == 0.015
        for t in range(item.t_start(), item.proj_len()):
            assert item.inflation_factor(t) == 1.015 ** item.duration(t), (point_id, t)
            assert item.inflation_factor(t) == 1.015 ** (t // 12), (point_id, t)


def test_pflege_inflation_factor_compounds_continuously(product_models):
    model = product_models("pflegerentenversicherung")
    projection = model.Projection
    assert projection.inflation_factor._is_derived()
    assert projection.inflation_years._is_defined()
    point_id = model.Data.model_point_table().index[0]
    item = projection[point_id]
    assert item.expense_infl() == 0.015
    assert item.inflation_factor(6) == 1.015 ** 0.5
    assert item.inflation_factor(0) == 1.0


# The core's dict cells: reader -> the file Reference whose presence says a product has it.
DICT_READERS = {
    "model_point_table": "model_point_file",
    "mort_table": "mort_file",
    "lapse_table": "lapse_file",
    "rentenfaktor_table": "rentenfaktor_file",
    "prem_freq_table": "prem_freq_file",
    "surplus_table": "surplus_file",
    "charge_table": "charge_file",
    "hoechstrechnungszins_table": "hoechstrechnungszins_file",
}


def same_value(a, b) -> bool:
    return a == b or (pd.isna(a) and pd.isna(b))


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_dict_cell_equals_its_reader(product, product_models):
    data = product_models(product).Data
    readers = [r for r, ref in DICT_READERS.items() if ref in data.refs]
    assert "model_point_table" in readers
    for reader in readers:
        df = data.cells[reader]()
        table = data.cells[reader + "_dict"]()
        if reader == "model_point_table":
            assert list(table) == list(df.index), reader
            rows = table
        else:
            assert list(table) == list(df.columns), reader
            for column, values in table.items():
                assert list(values) == list(df.index), (reader, column)
            rows = {k: {c: table[c][k] for c in df.columns} for k in df.index}
        for key in df.index:
            for column in df.columns:
                assert same_value(rows[key][column], df.at[key, column]), (reader, key, column)


def test_lapse_rate_beyond_the_table_holds_its_last_row(product_models):
    model = product_models("risikolebensversicherung")
    assert model.Projection.lapse_rate_base._is_derived()
    table = model.Data.lapse_table()
    last = table.index.max()
    item = model.Projection[model.Data.model_point_table().index[0]]
    t = 12 * int(last + 5)
    assert item.policy_year(t) > last
    assert item.lapse_rate_base(t) == float(table.at[last, "lapse_rate"])


@pytest.mark.parametrize("product", sorted(MODELS))
def test_model_point_is_read_only(product, product_models):
    """``model_point()`` is the shared row of ``model_point_table_dict()``, read-only."""
    model = product_models(product)
    point_id = model.Data.model_point_table().index[0]
    row = model.Projection[point_id].model_point()
    shared = model.Data.model_point_table_dict()[point_id]
    before = dict(shared)
    column = "sex" if "sex" in row else next(iter(row))
    with pytest.raises(TypeError):
        row[column] = "M"
    with pytest.raises(TypeError):
        del row[column]
    assert shared == before and dict(row) == before


def test_frv_charge_row_is_read_only(product_models):
    """FRV's ``charge_row()`` is the shared row of ``charge_table_rows()``, read-only."""
    model = product_models("fondsgebundene_rentenversicherung")
    item = model.Projection[model.Data.model_point_table().index[0]]
    row = item.charge_row()
    shared = model.Data.charge_table_rows()[item.charge_id()]
    before = dict(shared)
    column = next(iter(row))
    with pytest.raises(TypeError):
        row[column] = 5
    assert shared == before and dict(row) == before


def test_a_prem_freq_outside_the_table_raises(tmp_path):
    folder = product_copy(tmp_path, "risikolebensversicherung")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "prem_freq"] = "weekly"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["risikolebensversicherung"], name="FreqProbe")
    try:
        message = "invalid prem_freq weekly"
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].prem_freq()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


def test_expense_infl_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "klassische_rentenversicherung")
    table = folder / "param_tariff_type.csv"
    params = pd.read_csv(table, index_col="item")
    params.drop(index="expense_infl").to_csv(table)
    copy = mx.read_model(folder / MODELS["klassische_rentenversicherung"], name="InflProbe")
    try:
        assert copy.Projection.expense_infl._is_derived()
        point_id = copy.Data.model_point_table().index[0]
        with pytest.raises(Exception, match="expense_infl") as raised:
            copy.Projection[point_id].expense_infl()
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_an_issue_year_outside_every_band_raises(tmp_path):
    folder = product_copy(tmp_path, "sofortrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "issue_year"] = 1900
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["sofortrente"], name="HrzProbe")
    try:
        assert copy.Projection.hoechstrechnungszins._is_derived()
        message = "no Hoechstrechnungszins band covers issue_year"
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].hoechstrechnungszins()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


def test_a_product_without_a_table_never_builds_its_dict(product_models):
    model = product_models("risikolebensversicherung")
    assert "surplus_file" not in model.Data.refs
    model.Projection[model.Data.model_point_table().index[0]].result_cf()
    assert len(model.Data.model_point_table_dict) == 1
    assert len(model.Data.surplus_table_dict) == 0


# Pflege's own dict cells, beside the core's: reader -> the file Reference of its table.
PFLEGE_DICT_READERS = {
    "benefit_scale_table": "benefit_scale_file",
    "incidence_table": "incidence_file",
    "care_table": "care_file",
    "surrender_table": "surrender_file",
}


def test_pflege_product_dict_cells_equal_their_readers(product_models):
    data = product_models("pflegerentenversicherung").Data
    for reader, ref in PFLEGE_DICT_READERS.items():
        assert ref in data.refs, reader
        assert data.cells[reader + "_dict"]._is_defined(), reader
        df = data.cells[reader]()
        table = data.cells[reader + "_dict"]()
        assert list(table) == list(df.columns), reader
        for column, values in table.items():
            assert list(values) == list(df.index), (reader, column)
            for key in df.index:
                assert same_value(values[key], df.at[key, column]), (reader, key, column)


def test_pflege_grade_count_is_read_from_the_care_table(product_models):
    """Pflege's number of care grades is the rows of ``care_table.csv``, and no formula
    holds it as ``range(1, 6)``, ``(0.0,) * 5``, ``g < 5`` or ``min(5, ...)``."""
    data = product_models("pflegerentenversicherung").Data
    table = data.care_table()
    count = data.pflegegrad_count()
    assert type(count) is int and count == len(table) == 5
    assert list(table.index) == list(range(1, count + 1))
    path = PRODUCTS_DIR / "pflegerentenversicherung" / MODELS["pflegerentenversicherung"]
    text = (path / "Projection" / "__init__.py").read_text(encoding="utf-8")
    for literal in ("range(1, 6)", "(0.0,) * 5", "g < 5", "min(5, "):
        assert literal not in text, literal
    columns = [label for label, _ in
               product_models("pflegerentenversicherung").Projection[1].result_states_columns()]
    assert columns[:count] == ["pols_pg%d" % g for g in range(1, count + 1)]
    assert "mort_rate_care_pg%d" % count in columns


def test_pflege_surrender_cap_is_read_from_the_surrender_table(tmp_path, product_models):
    """The policy-year cap of ``rkw_pp`` is the table's last row, so a 41st row is read too."""
    data = product_models("pflegerentenversicherung").Data
    table = data.surrender_table()
    last = data.surrender_table_last_year()
    assert type(last) is int and last == int(table.index.max()) == len(table) == 40
    folder = product_copy(tmp_path, "pflegerentenversicherung")
    path = folder / "surrender_table.csv"
    path.write_text(path.read_text(encoding="utf-8") + '41,0.900000,"[std] test fixture"\n',
                    encoding="utf-8")
    copy = mx.read_model(folder / MODELS["pflegerentenversicherung"], name="SurrenderProbe")
    try:
        assert copy.Data.surrender_table_last_year() == 41
        checked = 0
        for point_id in copy.Data.model_point_table().index:
            item = copy.Projection[point_id]
            for t in range(item.t_start(), item.proj_len()):
                if item.policy_year(t) < 41 or item.cum_prem_max_pp(t) <= 0.0:
                    continue
                expected = 0.9 * item.cum_prem_max_pp(t) * (1.0 - item.stornoabzug_rate())
                assert item.rkw_pp(t) == expected, (point_id, t)
                checked += 1
        assert checked
    finally:
        copy.close()


# Pflege's care-grade rates keyed by attained age (and grade), not by month: cell -> whether
# the cell takes the grade, the age, or both.
PFLEGE_AGE_KEYED = {
    "rec_rate": ("x", "g"),
    "det_force": ("x", "g"),
    "rec_force": ("x", "g"),
    "tar_mort_rate_care": ("x", "g"),
    "tar_rec_rate": ("x", "g"),
    "tar_p_pg": ("x", "g"),
    "tar_inc_rate": ("x",),
    "tar_det_rate": ("g",),
}


def test_pflege_care_grade_rates_are_keyed_by_age():
    # A model of its own, so that the cells' caches start empty whatever ran before.
    product = "pflegerentenversicherung"
    model = mx.read_model(PRODUCTS_DIR / product / MODELS[product], name="AgeKeyProbe")
    try:
        item = model.Projection[1]
        item.result_cf()
        assert item.premium_mth() == 0.0
        item.premium_mth_pp()
        ages = {item.age(t) for t in range(item.proj_len())}
        bound = {("x", "g"): len(ages) * 5, ("x",): len(ages), ("g",): 5}
        for name, params in PFLEGE_AGE_KEYED.items():
            cell = item.cells[name]
            assert tuple(cell.parameters) == params, name
            keys = list(cell.keys())
            assert 0 < len(keys) <= bound[params], (name, len(keys))
            for key in keys:
                key = key if isinstance(key, tuple) else (key,)
                if params[0] == "x":
                    assert key[0] in ages, (name, key)
                if params[-1] == "g":
                    assert 1 <= key[-1] <= 5, (name, key)
    finally:
        model.close()


def test_pflege_entries_and_graduations_are_the_ledgers_own(product_models):
    """``pols_entry`` and ``pols_grad`` read the ledger and equal the formulas they had beside it.

    On every point and every month of the frame, the last one included, whose flows the
    ledger forms at ``proj_len()``: the entrants are ``pols_act(t)`` times the ``care``
    component of ``p_act_age`` times ``inc_share(g)``; the graduations equal the entrants
    where ``karenz_months() == 0`` and are the ``z = K`` cohort carried one month through
    ``p_pg_age`` at ``age(t)`` where it is positive (point 7).
    """
    model = product_models("pflegerentenversicherung")
    seen = set()
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        k = item.karenz_months()
        seen.add(k > 0)
        for t in range(item.t_start(), item.proj_len()):
            state = item.pols_ledger(t)
            waiting = item.duration_mth(t) < item.wartezeit_months()
            care = item.p_act_age(item.age(t), waiting)[2]
            for g in range(1, 6):
                entry = state[0] * care * item.inc_share(g)
                assert item.pols_entry(t, g) == entry, (point_id, t, g)
                if k <= 0:
                    assert item.pols_grad(t, g) == item.pols_entry(t, g), (point_id, t, g)
                    continue
                grad = 0.0
                for h in range(max(1, g - 1), min(5, g + 1) + 1):
                    w = state[3][h - 1][k - 1]
                    if w == 0.0:
                        continue
                    p = item.p_pg_age(item.age(t), h)
                    grad += w * (p[0] if h == g else p[2] if g == h + 1 else p[3])
                assert item.pols_grad(t, g) == grad, (point_id, t, g)
    assert seen == {False, True}


def test_pflege_month_keyed_rates_depend_on_the_month_only_through_the_age(product_models):
    """The age-keyed transitions read the month-keyed rates at ``age_month(age(t))``.

    ``p_act_age`` and ``p_pg_age`` are keyed by attained age and read ``inc_rate``,
    ``mort_force`` and ``mort_force_care`` at the first month of the age; that is right only
    while those rates take the same value in every month of a year of age. On every point
    and every month of the frame: ``age_month`` maps back to the age, the three rates equal
    their values at it, and ``inc_force`` is 0 in the *Wartezeit* and else
    ``inc_force_age`` at the age.
    """
    model = product_models("pflegerentenversicherung")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            m = item.age_month(x)
            assert item.age(m) == x, (point_id, t)
            assert item.inc_rate(t) == item.inc_rate(m), (point_id, t)
            assert item.mort_force(t) == item.mort_force(m), (point_id, t)
            for g in range(1, 6):
                assert item.mort_force_care(t, g) == item.mort_force_care(m, g), (point_id, t, g)
            if item.duration_mth(t) < item.wartezeit_months():
                assert item.inc_force(t) == 0.0, (point_id, t)
            else:
                assert item.inc_force(t) == item.inc_force_age(x), (point_id, t)


def test_pflege_tariff_care_mortality_is_certain_at_the_limiting_age(product_models):
    item = product_models("pflegerentenversicherung").Projection[1]
    x = item.omega_age() - 1
    for g in range(1, 6):
        assert item.tar_mort_rate_care(x, g) == 1.0
        stay, death, worse, better = item.tar_p_pg(x, g)
        assert (worse, better) == (0.0, 0.0)
        assert stay + death == pytest.approx(1.0, abs=1e-15)


def test_pflege_recovery_is_damped_only_above_the_reference_age(product_models):
    model = product_models("pflegerentenversicherung")
    item = model.Projection[1]
    care = model.Data.care_table()
    ref = item.rec_age_ref()
    decay = item.rec_age_decay()
    assert (ref, decay) == (75.0, 0.1)
    for g in range(1, 6):
        base = float(care.at[g, "rec_rate"])
        assert item.rec_rate(60, g) == base
        assert item.rec_rate(75, g) == base
        assert item.rec_rate(85, g) == base * math.exp(-decay * (85 - ref))


def test_pflege_tariff_deterioration_is_zero_at_grade_5(product_models):
    item = product_models("pflegerentenversicherung").Projection[1]
    assert item.det_rate(5) == 0.0
    assert item.tar_det_rate(5) == 0.0
    assert item.det_force(60, 5) == 0.0
    assert item.tar_det_rate(1) == min(1.0 - 1e-12, 1.15 * item.det_rate(1))


def test_pflege_rec_margin_without_its_row_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "pflegerentenversicherung")
    table = folder / "param_tariff_type.csv"
    params = pd.read_csv(table, index_col="item")
    params.drop(index="rec_margin").to_csv(table)
    copy = mx.read_model(folder / MODELS["pflegerentenversicherung"], name="RecProbe")
    try:
        point_id = copy.Data.model_point_table().index[0]
        with pytest.raises(Exception, match="rec_margin") as raised:
            copy.Projection[point_id].tar_rec_rate(60, 1)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


# The products' own dict cells, beside the core's: product -> {reader: file Reference}; the
# bounds cell of a table a lookup clamps to: product -> {bounds cell: (reader, group level or
# None, bounded level, "range" for (first, last) or "last" for the last key alone)}; and the
# by-row cells: product -> {rows cell: reader}.
PRODUCT_DICT_READERS = {
    "klassische_rentenversicherung": {"decl_rate_table": "decl_rate_file"},
    "kapitallebensversicherung": {
        "surplus_rate_table": "surplus_rate_file",
        "deckrv_table": "deckrv_file",
    },
    "basisrente": {"behaviour_table": "behaviour_file", "option_table": "option_file"},
    "fondsgebundene_rentenversicherung": {"fund_scenario_table": "fund_scenario_file"},
    "indexpolice": {
        "index_return_table": "index_return_file",
        "index_param_table": "index_param_file",
        "surplus_rate_table": "surplus_rate_file",
        "election_table": "election_file",
    },
    "sofortrente": {
        "improvement_table": "improvement_file",
        "surplus_scale_table": "surplus_scale_file",
    },
    "berufsunfaehigkeit": {
        "inception_table": "inception_file",
        "claim_duration_table": "claim_duration_file",
        "occupation_table": "occupation_file",
    },
    "riester_rente": {
        "annuity_mort_table": "annuity_mort_file",
        "zulage_schedule": "zulage_file",
        "income_schedule": "income_file",
    },
    "risikolebensversicherung": {
        "benefit_schedule": "benefit_schedule_file",
        "nvg_schedule": "nvg_schedule_file",
    },
}
PRODUCT_BOUNDS = {
    "klassische_rentenversicherung": {
        "decl_rate_years": ("decl_rate_table", "scenario_id", "calendar_year", "range")},
    "kapitallebensversicherung": {
        "surplus_rate_years": ("surplus_rate_table", "scenario_id", "policy_year", "range")},
    "basisrente": {
        "behaviour_table_durs": ("behaviour_table", "beh_table_id", "dur", "last"),
        "surplus_table_years": ("surplus_table", "scenario_id", "t", "last"),
    },
    "sofortrente": {
        "mort_table_ages": ("mort_table", None, "age", "range"),
        "improvement_table_ages": ("improvement_table", None, "age", "range"),
    },
    "berufsunfaehigkeit": {
        "inception_table_ages": ("inception_table", None, "age", "range"),
        "mort_table_ages": ("mort_table", None, "age", "range"),
    },
}
PRODUCT_ROWS = {"fondsgebundene_rentenversicherung": {"charge_table_rows": "charge_table"}}


def _expected_bound(values, shape):
    """The bound of an index level's values: ``(first, last)`` or the last alone, as ints."""
    if shape == "range":
        return (int(values.min()), int(values.max()))
    return int(values.max())


@pytest.mark.parametrize("product", sorted(PRODUCT_DICT_READERS))
def test_product_dict_cells_equal_their_readers(product, product_models):
    data = product_models(product).Data
    for reader, ref in PRODUCT_DICT_READERS[product].items():
        assert ref in data.refs, reader
        assert data.cells[reader + "_dict"]._is_defined(), reader
        df = data.cells[reader]()
        table = data.cells[reader + "_dict"]()
        assert list(table) == list(df.columns), reader
        for column, values in table.items():
            assert list(values) == list(df.index), (reader, column)
            for key in df.index:
                assert same_value(values[key], df.at[key, column]), (reader, key, column)
    for cell, (reader, group, level, shape) in PRODUCT_BOUNDS.get(product, {}).items():
        assert data.cells[cell]._is_defined(), cell
        df = data.cells[reader]()
        bounds = data.cells[cell]()
        if group is None:
            expected = _expected_bound(df.index.get_level_values(level), shape)
            assert bounds == expected, cell
            assert all(type(b) is int for b in (bounds if shape == "range" else (bounds,))), cell
            continue
        groups = df.index.get_level_values(group).unique()
        assert sorted(bounds) == sorted(groups), cell
        for key in groups:
            values = df.loc[key].index
            assert values.name == level
            assert bounds[key] == _expected_bound(values, shape), (cell, key)
            assert all(type(b) is int for b in (
                bounds[key] if shape == "range" else (bounds[key],))), (cell, key)
    for cell, reader in PRODUCT_ROWS.get(product, {}).items():
        assert data.cells[cell]._is_defined(), cell
        df = data.cells[reader]()
        rows = data.cells[cell]()
        assert list(rows) == list(df.index), cell
        for key in df.index:
            assert list(rows[key]) == list(df.columns), (cell, key)
            for column in df.columns:
                assert same_value(rows[key][column], df.at[key, column]), (cell, key, column)


# product -> (the third exit cell the residual sums, a new point, an in-force point).
DECREMENT_CLOSURE = {
    "klassische_rentenversicherung": ("pols_commutation", 1, 6),
    "kapitallebensversicherung": ("pols_maturity", 1, 10),
}


@pytest.mark.parametrize("product", sorted(DECREMENT_CLOSURE))
def test_decrement_closure_residual_equals_the_sum_over_the_exit_cells(product, product_models):
    third, new, in_force = DECREMENT_CLOSURE[product]
    projection = product_models(product).Projection
    assert projection.cells["pols_exits_cum"]._is_defined()
    for point_id in (new, in_force):
        item = projection[point_id]
        third_exit = item.cells[third]
        start = item.t_start()
        assert (start > 0) == (point_id == in_force), point_id
        assert item.pols_exits_cum(start - 1) == 0
        index = list(item.result_cf().index)
        assert index[0] == start and index[-1] == item.proj_len() - 1
        # The running total equals the old direct sum up to floating-point noise.
        noise = 1e-12 * max(item.pols_if_init(), 1.0)
        for t in index:
            exits = sum(item.pols_death(s) + item.pols_lapse(s) + third_exit(s)
                        for s in range(start, t + 1))
            assert item.pols_exits_cum(t) == pytest.approx(exits, rel=0, abs=noise), (point_id, t)
            if product == "kapitallebensversicherung":
                carried = item.pols_if(t + 1) if t < item.proj_len() - 1 else 0.0
                old = exits + carried - item.pols_if_init()
            else:
                old = exits + item.pols_if(t + 1) - item.pols_if_init()
            assert item.check_decrement_closure_resid(t) == pytest.approx(
                old, rel=0, abs=noise), (point_id, t)
        assert item.check_decrement_closure()


def test_rv_decl_rate_holds_the_scenario_range(product_models):
    model = product_models("klassische_rentenversicherung")
    table = model.Data.decl_rate_table()
    item = model.Projection[1]
    scen = item.scenario_id()
    years = table.loc[scen].index
    first, last = int(years.min()), int(years.max())
    assert (first, last) == (2005, 2060)
    k_late = last - item.issue_year() + 5
    assert item.calendar_year_y(k_late) > last
    assert item.decl_rate(k_late) == float(table.at[(scen, last), "decl_rate"])
    k_early = first - item.issue_year() - 5
    assert item.calendar_year_y(k_early) < first
    assert item.decl_rate(k_early) == float(table.at[(scen, first), "decl_rate"])


def test_klv_surplus_rates_and_stornoabzug_hold_their_last_policy_year(product_models):
    model = product_models("kapitallebensversicherung")
    surplus = model.Data.surplus_rate_table()
    lapse = model.Data.lapse_table()
    item = model.Projection[1]
    scen = item.scenario_id()
    last = int(surplus.loc[scen].index.max())
    k = last + 5
    assert item.policy_year_y(k) > last
    for cell in ("decl_rate", "term_rate", "ans_rate"):
        assert item.cells[cell](k) == float(surplus.at[(scen, last), cell]), cell
    last_lapse = int(lapse.index.max())
    k = last_lapse + 5
    assert item.policy_year_y(k) > last_lapse
    assert item.storno_rate(k) == float(lapse.at[last_lapse, "storno_rate"])


def test_klv_echt_instalments_carry_no_loading(product_models):
    model = product_models("kapitallebensversicherung")
    loading = model.Data.prem_freq_table()
    unecht, echt = model.Projection[4], model.Projection[5]
    assert (unecht.prem_freq(), echt.prem_freq()) == ("monthly", "monthly")
    assert (unecht.unterjaehrig_form(), echt.unterjaehrig_form()) == ("unecht", "echt")
    assert unecht.prem_freq_load() == float(loading.at["monthly", "prem_freq_load"]) == 1.05
    assert echt.prem_freq_load() == 1.0


@pytest.mark.parametrize("issue_year", [1950, 2090])
def test_klv_deckrv_ceilings_clamp_the_issue_year(tmp_path, issue_year):
    product = "kapitallebensversicherung"
    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "issue_year"] = issue_year
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS[product], name=f"DeckRVProbe{issue_year}")
    try:
        deckrv = copy.Data.deckrv_table()
        assert issue_year not in deckrv.index
        edge = deckrv.index.min() if issue_year < deckrv.index.min() else deckrv.index.max()
        item = copy.Projection[point_id]
        assert item.issue_year() == issue_year
        assert item.hoechstrechnungszins() == float(deckrv.at[edge, "hoechstrechnungszins"])
        assert item.zillmer_max() == float(deckrv.at[edge, "hoechstzillmersatz"])
    finally:
        copy.close()


@pytest.mark.parametrize("product, cell", [
    ("klassische_rentenversicherung", "decl_rate"),
    ("kapitallebensversicherung", "decl_rate"),
    ("kapitallebensversicherung", "term_rate"),
    ("kapitallebensversicherung", "ans_rate"),
    ("basisrente", "decl_rate"),
    ("basisrente", "ann_bonus_rate"),
])
def test_an_unknown_scenario_raises_key_error(tmp_path, product, cell):
    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "scenario_id"] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS[product], name="ScenProbe")
    try:
        with pytest.raises(Exception, match="unbekannt") as raised:
            copy.Projection[point_id].cells[cell](0)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_basis_behaviour_holds_its_first_and_last_policy_year(product_models):
    model = product_models("basisrente")
    table = model.Data.behaviour_table()
    item = model.Projection[1]
    key = item.model_point()["beh_table_id"]
    last = int(table.loc[key].index.max())
    k_late = last + 5
    assert item.policy_year_y(k_late) > last
    assert item.zuz_take_up(k_late) == float(table.at[(key, last), "zuz_take_up"])
    k_early = -item.duration_init() - 5
    assert item.policy_year_y(k_early) < 1
    assert item.zuz_take_up(k_early) == float(table.at[(key, 1), "zuz_take_up"])


def test_basis_bf_rate_holds_the_last_row_of_a_short_table(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    path = folder / "behaviour_table.csv"
    table = pd.read_csv(path, index_col=["beh_table_id", "dur"])
    table = table[table.index.get_level_values("dur") <= 7]
    table.to_csv(path)
    copy = mx.read_model(folder / MODELS["basisrente"], name="BfProbe")
    try:
        item = copy.Projection[1]
        key = item.model_point()["beh_table_id"]
        assert copy.Data.behaviour_table_durs()[key] == 7
        t = 12 * 9
        assert item.policy_year(t) == 10 and t < min(item.t_conv(), item.proj_len())
        assert item.bf_rate(t) == float(table.at[(key, 7), "bf_rate"])
        assert item.zuz_take_up(9) == float(table.at[(key, 7), "zuz_take_up"])
    finally:
        copy.close()


def test_basis_unknown_behaviour_table_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "beh_table_id"] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["basisrente"], name="BehProbe")
    try:
        for cell in ("zuz_take_up", "bf_rate"):
            with pytest.raises(Exception, match="unbekannt") as raised:
                copy.Projection[point_id].cells[cell](0)
            assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_basis_surplus_holds_its_first_and_last_year(product_models):
    model = product_models("basisrente")
    table = model.Data.surplus_table()
    item = model.Projection[1]
    scen = item.scenario_id()
    last = int(table.loc[scen].index.max())
    for cell in ("decl_rate", "ann_bonus_rate"):
        assert item.cells[cell](last + 5) == float(table.at[(scen, last), cell]), cell
        assert item.cells[cell](-3) == float(table.at[(scen, 0), cell]), cell


def test_basis_unknown_surplus_scenario_raises_key_error(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "scenario_id"] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["basisrente"], name="SurplusProbe")
    try:
        for cell in ("decl_rate", "ann_bonus_rate"):
            with pytest.raises(Exception, match="unbekannt") as raised:
                copy.Projection[point_id].cells[cell](0)
            assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_basis_single_premium_reads_no_loading(tmp_path):
    folder = product_copy(tmp_path, "basisrente")
    table = folder / "prem_freq_table.csv"
    table.write_text(table.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
    copy = mx.read_model(folder / MODELS["basisrente"], name="LoadProbe")
    try:
        points = copy.Data.model_point_table()
        single = points.index[points["prem_form"] == "single"][0]
        regular = points.index[points["prem_form"] == "regular"][0]
        assert copy.Projection[single].prem_freq_load() == 1.0
        message = "invalid prem_freq " + str(points.at[regular, "prem_freq"])
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[regular].prem_freq_load()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


# The premium payment frequencies, one name and one table in every product with a regular
# premium: key -> instalments a year.
PREM_FREQ_INSTALMENTS = {"annual": 1, "half_yearly": 2, "quarterly": 4, "monthly": 12}
PREM_FREQ_PRODUCTS = sorted(["basisrente", "berufsunfaehigkeit",
                             "fondsgebundene_rentenversicherung", "indexpolice",
                             "kapitallebensversicherung", "klassische_rentenversicherung",
                             "pflegerentenversicherung", "riester_rente",
                             "risikolebensversicherung"])


def test_the_products_with_a_premium_frequency_table_are_listed(product_models):
    having = [product for product in sorted(MODELS)
              if "prem_freq_file" in product_models(product).Data.refs]
    assert having == PREM_FREQ_PRODUCTS


@pytest.mark.parametrize("product", PREM_FREQ_PRODUCTS)
def test_premium_frequencies_are_one_table_with_instalments(product, product_models):
    """``prem_freq_table.csv`` keyed by ``prem_freq``, its ``instalments`` an ``int`` a year,
    and every model point's ``prem_freq`` one of its keys."""
    model = product_models(product)
    data = model.Data
    assert data.prem_freq_file == "prem_freq_table.csv"
    table = data.prem_freq_table()
    assert table.index.name == "prem_freq"
    assert set(table.index) <= set(PREM_FREQ_INSTALMENTS)
    assert table.columns[0] == "instalments" and table.columns[-1] == "provenance"
    assert set(table.columns) <= {"instalments", "prem_freq_load", "provenance"}
    instalments = data.prem_freq_table_dict()["instalments"]
    assert all(type(n) is int for n in instalments.values())
    assert instalments == {key: PREM_FREQ_INSTALMENTS[key] for key in table.index}
    points = data.model_point_table()
    assert not {"prem_mode", "prem_mode_months"} & set(points.columns)
    assert set(points["prem_freq"]) <= set(table.index)
    for point_id in points.index:
        item = model.Projection[point_id]
        assert type(item.instalments()) is int
        assert item.prem_cycle() == 12 // PREM_FREQ_INSTALMENTS[points.at[point_id, "prem_freq"]]


# The products with a single and a regular premium form, one model-point column prem_form.
PREM_FORM_PRODUCTS = sorted(["basisrente", "fondsgebundene_rentenversicherung", "indexpolice",
                             "klassische_rentenversicherung", "pflegerentenversicherung",
                             "risikolebensversicherung"])


def test_the_premium_form_is_one_column_with_two_values(product_models):
    """``prem_form`` is ``regular`` or ``single`` wherever a product has the column, the core's
    ``prem_form()`` reads it, and no ``premium_form`` of that meaning is left (BU's
    ``premium_form``, *Dynamik* or level, is another quantity)."""
    having = []
    for product in sorted(MODELS):
        model = product_models(product)
        points = model.Data.model_point_table()
        if "prem_form" not in points.columns:
            continue
        having.append(product)
        assert set(points["prem_form"]) == {"regular", "single"}, product
        for point_id in points.index:
            assert model.Projection[point_id].prem_form() == points.at[point_id, "prem_form"]
        assert "premium_form" not in points.columns, product
    assert having == PREM_FORM_PRODUCTS
    bu = product_models("berufsunfaehigkeit").Data.model_point_table()
    assert set(bu["premium_form"]) == {"dynamik", "level"}


def test_an_unknown_premium_form_raises(tmp_path):
    folder = product_copy(tmp_path, "indexpolice")
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, "prem_form"] = "level"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS["indexpolice"], name="FormProbe")
    try:
        message = "invalid prem_form"
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].prem_form()
        assert raised_value_error(raised, message)
    finally:
        copy.close()


# The payment frequencies a product allows, a table of its own: product -> (keys cell, keys).
FREQUENCY_KEYS = {
    "sofortrente": ("ann_freq_table_keys", frozenset({1, 2, 4, 12})),
}

# A frequency the shipped table lacks: product -> (table file, model-point column, value,
# row that admits it, cell that checks it, its error message, the cell's value once admitted).
FREQUENCY_PROBES = {
    "fondsgebundene_rentenversicherung": (
        "prem_freq_table.csv", "prem_freq", "bimonthly", 'bimonthly,6,"[std] test fixture"',
        "prem_freq", "invalid prem_freq bimonthly", "bimonthly"),
    "pflegerentenversicherung": (
        "prem_freq_table.csv", "prem_freq", "bimonthly", 'bimonthly,6,"[std] test fixture"',
        "prem_freq", "invalid prem_freq bimonthly", "bimonthly"),
    "sofortrente": (
        "ann_freq_table.csv", "ann_freq", 3, '3,"[std] test fixture"',
        "ann_freq", "invalid ann_freq", 3),
}


def test_a_single_premium_is_annual_and_carries_no_frequency_loading(product_models):
    """Every single-premium point carries ``prem_freq = annual`` and ``prem_freq_load`` 1.0,
    the core's rule for every product; Basis no longer overrides ``prem_freq_load``."""
    checked = 0
    for product in sorted(MODELS):
        model = product_models(product)
        points = model.Data.model_point_table()
        if "prem_form" not in points.columns:
            assert model.Projection[int(points.index[0])].prem_form() == "regular"
            continue
        for point_id in points.index[points["prem_form"] == "single"]:
            assert points.at[point_id, "prem_freq"] == "annual", (product, point_id)
            assert model.Projection[int(point_id)].prem_freq_load() == 1.0, (product, point_id)
            checked += 1
    assert checked == 6
    path = PRODUCTS_DIR / "basisrente" / MODELS["basisrente"] / "Projection" / "__init__.py"
    assert "def prem_freq_load" not in path.read_text(encoding="utf-8")


def test_pflege_single_premium_is_a_premium_form_not_a_frequency(product_models):
    """Pflege's *Einmalbeitrag* is ``prem_form = single``, paid at ``t = 0`` alone, and its
    ``prem_freq`` (shipped as ``annual``) is a key of the table; a ``regular`` premium falls
    due every ``prem_cycle()`` months, over all four frequencies."""
    model = product_models("pflegerentenversicherung")
    assert "single" not in model.Data.prem_freq_table().index
    points = model.Data.model_point_table()
    forms, freqs = set(), set()
    for point_id in points.index:
        item = model.Projection[point_id]
        forms.add(item.prem_form())
        if item.prem_form() == "single":
            assert points.at[point_id, "prem_freq"] == "annual"
            assert [t for t in range(24) if item.premium_due(t)] == [0]
        else:
            freqs.add(item.prem_freq())
            assert item.prem_cycle() == 12 // PREM_FREQ_INSTALMENTS[item.prem_freq()]
    assert forms == {"regular", "single"}
    assert freqs == set(PREM_FREQ_INSTALMENTS)


@pytest.mark.parametrize("product", sorted(FREQUENCY_KEYS))
def test_annuity_frequencies_are_the_keys_of_their_table(product, product_models):
    data = product_models(product).Data
    cell, keys = FREQUENCY_KEYS[product]
    assert data.cells[cell]() == keys
    assert all(type(key) is int for key in data.cells[cell]())


@pytest.mark.parametrize("product", sorted(FREQUENCY_PROBES))
def test_a_frequency_outside_the_table_raises_and_a_row_admits_it(product, tmp_path):
    table, column, value, row, cell, message, admitted = FREQUENCY_PROBES[product]
    folder = product_copy(tmp_path, product)
    points = pd.read_csv(folder / "model_point_table.csv", dtype=str, keep_default_na=False)
    points.loc[0, column] = str(value)
    points.to_csv(folder / "model_point_table.csv", index=False)
    point_id = int(points.loc[0, "point_id"])
    copy = mx.read_model(folder / MODELS[product], name="FreqProbe")
    try:
        with pytest.raises(Exception, match=message) as raised:
            copy.Projection[point_id].cells[cell]()
        assert raised_value_error(raised, message)
    finally:
        copy.close()
    path = folder / table
    path.write_text(path.read_text(encoding="utf-8") + row + "\n", encoding="utf-8")
    copy = mx.read_model(folder / MODELS[product], name="FreqProbeAdmitted")
    try:
        assert copy.Projection[point_id].cells[cell]() == admitted
    finally:
        copy.close()


def test_sofort_ages_outside_the_tables_hold_their_ends(product_models):
    model = product_models("sofortrente")
    mort = model.Data.mort_table()
    improve = model.Data.improvement_table()
    item = model.Projection[model.Data.model_point_table().index[0]]
    ages = mort.index.get_level_values("age")
    lo, hi = int(ages.min()), int(ages.max())
    for basis in ("FIRST", "SECOND"):
        for sex in ("M", "F"):
            assert item.mort_rate_at_age(lo - 5, sex, basis) == float(
                mort.at[(basis, sex, lo), "mort_rate"]), (basis, sex)
            assert item.mort_rate_at_age(hi + 5, sex, basis) == float(
                mort.at[(basis, sex, hi), "mort_rate"]), (basis, sex)
    ages = improve.index.get_level_values("age")
    lo, hi = int(ages.min()), int(ages.max())
    for basis in ("FIRST", "SECOND"):
        assert item.improve_rate_at_age(lo - 5, basis) == float(
            improve.at[(basis, lo), "improve_rate"]), basis
        assert item.improve_rate_at_age(hi + 5.5, basis) == float(
            improve.at[(basis, hi), "improve_rate"]), basis


def test_bu_ages_outside_the_tables_hold_their_ends(product_models):
    model = product_models("berufsunfaehigkeit")
    inception = model.Data.inception_table()
    mort = model.Data.mort_table()
    item = model.Projection[model.Data.model_point_table().index[0]]
    assert (int(inception.index.min()), int(inception.index.max())) == (18, 66)
    assert (int(mort.index.min()), int(mort.index.max())) == (18, 70)
    assert item.inc_rate_at_age(10) == float(inception.at[18, "inc_rate"])
    assert item.inc_rate_at_age(80) == float(inception.at[66, "inc_rate"])
    for cell, column in (("mort_rate_at_age", "mort_rate_actv"),
                         ("mort_rate_dis_at_age", "mort_rate_dis")):
        assert item.cells[cell](10) == float(mort.at[18, column]), cell
        assert item.cells[cell](80) == float(mort.at[70, column]), cell


def _bu_roll_reference(qy, ry, g, ppols, pval, n):
    """The disabled ledger's roll before story 2.14: a Python loop over lists."""
    pols = [0.0] * n
    val = [0.0] * n
    for i in range(min(len(ppols), n - 1)):
        cy = min(i // 12, 10)
        keep = (1.0 - qy[cy]) * (1.0 - ry[cy])
        step = g if (i + 1) % 12 == 0 else 1.0
        pols[i + 1] = ppols[i] * keep
        val[i + 1] = pval[i] * keep * step
    return pols, val


def _bu_exits_reference(qy, ry, pols, val):
    """The disabled ledger's exits before story 2.14: three totals added left to right."""
    deaths = rec = recval = 0.0
    for i in range(len(pols)):
        cy = min(i // 12, 10)
        q, r = qy[cy], ry[cy]
        deaths += pols[i] * q
        rec += pols[i] * (1.0 - q) * r
        recval += val[i] * (1.0 - q) * r
    return deaths, rec, recval


def _bu_ledger_cells(item, first):
    """The cells of one of BU's two disabled ledgers, the best-estimate or the first-order one."""
    if first:
        return (item.first_len(), item.dis_cohorts_first, item.dis_exits_first,
                item.cohort_len_first, item.age_first, item.mort_rate_dis_first_mth_year,
                item.recov_rate_first_mth_year(), item.pols_inception_first,
                item.bu_rente_pp_first)
    return (item.proj_len(), item.dis_cohorts, item.dis_exits, item.cohort_len, item.age,
            item.mort_rate_dis_mth_year, item.recov_rate_mth_year(), item.pols_inception,
            item.bu_rente_pp)


@pytest.mark.parametrize("first", [False, True], ids=["best_estimate", "first_order"])
def test_bu_cohort_arrays_equal_the_list_recursion(product_models, first):
    """``dis_cohorts*`` and ``dis_exits*`` give the old loop's bits, as arrays and floats."""
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        end, cohorts, exits, length, age, mort_year, ry, inception, rente = (
            _bu_ledger_cells(item, first))
        g = 1.0 + item.leistungsdyn_rate()
        months = {0, 1, 13, 121, end}
        ref = None
        for t in range(end + 1):
            pols, val = cohorts(t)
            if t == 0:
                n = length(0)
                ref = ([0.0] * n, [0.0] * n)
                z0 = 0 if first else item.seed_claim_dur()
                if z0 and z0 <= n:
                    ref[0][z0 - 1] = item.pols_if_init()
                    ref[1][z0 - 1] = item.pols_if_init() * item.rente_pay_pp(0, z0)
            else:
                ref = _bu_roll_reference(mort_year(age(t - 1)), ry, g, *ref, length(t))
                ref[0][0] = inception(t - 1)
                ref[1][0] = ref[0][0] * rente(t - 1)
            if t not in months:
                continue
            assert isinstance(pols, np.ndarray) and isinstance(val, np.ndarray), (point_id, t)
            assert pols.tolist() == ref[0], (point_id, t)
            assert val.tolist() == ref[1], (point_id, t)
            got = exits(t)
            assert all(type(x) is float for x in got), (point_id, t)
            assert got == _bu_exits_reference(mort_year(age(t)), ry, ref[0], ref[1]), (
                point_id, t)


def test_bu_rate_tuples_by_age_equal_the_cells_by_claim_year(product_models):
    """The tuples keyed by attained age hold ``mort_rate_dis_mth`` and its first-order twin."""
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        for t in sorted({0, 1, 13, 121, item.proj_len() - 1}):
            year = item.mort_rate_dis_mth_year(item.age(t))
            assert len(year) == 11
            assert year == tuple(item.mort_rate_dis_mth(t, 12 * cy + 1)
                                 for cy in range(11)), (point_id, t)
        for s in sorted({0, 1, 13, 121, item.first_len() - 1}):
            year = item.mort_rate_dis_first_mth_year(item.age_first(s))
            assert year == tuple(item.mort_rate_dis_first_mth(s, 12 * cy + 1)
                                 for cy in range(11)), (point_id, s)
    mort = model.Data.mort_table()
    item = model.Projection[model.Data.model_point_table().index[0]]
    assert (int(mort.index.min()), int(mort.index.max())) == (18, 70)
    assert item.mort_rate_dis_mth_year(10) == item.mort_rate_dis_mth_year(18)
    assert item.mort_rate_dis_mth_year(80) == item.mort_rate_dis_mth_year(70)
    assert item.mort_rate_dis_first_mth_year(10) == item.mort_rate_dis_first_mth_year(18)
    assert item.mort_rate_dis_first_mth_year(80) == item.mort_rate_dis_first_mth_year(70)


def test_bu_cohort_arrays_seed_age_and_step(product_models):
    """The seeded state, claim year 11, the onset anniversary, the full length, ``pols_dis_dur``."""
    model = product_models("berufsunfaehigkeit")
    points = model.Data.model_point_table()
    aktiv = model.Projection[points.index[points["status"] == "aktiv"][0]]
    pols, val = aktiv.dis_cohorts(0)
    assert aktiv.seed_claim_dur() == 0
    assert pols.tolist() == [0.0] and val.tolist() == [0.0]
    leistung = points.index[points["status"] == "leistung"]
    assert len(leistung), "no in-claim model point"
    item = model.Projection[leistung[0]]
    z0 = item.seed_claim_dur()
    assert 1 <= z0 <= item.cohort_len(0)
    pols, val = item.dis_cohorts(0)
    assert pols[z0 - 1] == item.pols_if_init()
    assert val[z0 - 1] == item.pols_if_init() * item.rente_pay_pp(0, z0)
    assert np.count_nonzero(pols) == 1 and np.count_nonzero(val) == 1

    keep = [(1.0 - q) * (1.0 - r) for q, r in zip(item.mort_rate_dis_mth_year(item.age(130)),
                                                  item.recov_rate_mth_year())]
    g = 1.0 + item.leistungsdyn_rate()
    assert g != 1.0
    ppols, pval = item.dis_cohorts(130)
    pols, val = item.dis_cohorts(131)
    for i in (119, 120, 125, len(ppols) - 1):
        cy = min(i // 12, 10)
        assert cy == (10 if i >= 120 else 9)
        step = g if (i + 1) % 12 == 0 else 1.0
        assert pols[i + 1] == ppols[i] * keep[cy], i
        assert val[i + 1] == pval[i] * keep[cy] * step, i
    assert val[120] != pval[119] * keep[9]

    end = item.proj_len()
    assert item.cohort_len(end) == item.max_claim_dur()
    pols, val = item.dis_cohorts(end)
    assert len(pols) == item.max_claim_dur()
    assert pols[-1] == 0.0 and val[-1] == 0.0
    assert item.check_dis_roll_fwd()

    for dur, cohorts, length, t in ((item.pols_dis_dur, item.dis_cohorts, item.cohort_len, 13),
                                    (item.pols_dis_dur_first, item.dis_cohorts_first,
                                     item.cohort_len_first, 13)):
        n = length(t)
        assert dur(t, 0) == 0.0 and dur(t, n + 1) == 0.0
        assert type(dur(t, 1)) is float and dur(t, 1) == cohorts(t)[0][0]
        assert type(dur(t, n)) is float
    assert type(item.pols_dis(13)) is float and type(item.pols_dis_first(13)) is float


def test_bu_cohort_index_and_step_sliced_equal_the_vectors_by_month(product_models):
    """``cohort_year_idx`` and ``cohort_anniv_step`` at full length, sliced, are the old vectors.

    Both orders: the best estimate at ``max_claim_dur()``, the first order at
    ``first_len() + 1``; every slice ``[:m]`` with ``m <= n``, the empty one included, equals
    the array the ledgers built for that month.
    """
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        g = 1.0 + item.leistungsdyn_rate()
        for n in (item.max_claim_dur(), item.first_len() + 1):
            idx, step = item.cohort_year_idx(n), item.cohort_anniv_step(n)
            assert len(idx) == len(step) == n
            for m in sorted({0, 1, 11, 12, 13, 120, 121, n - 1, n}):
                ref_idx = np.minimum(np.arange(m) // 12, 10)
                ref_step = np.where(np.arange(1, m + 1) % 12 == 0, g, 1.0)
                assert idx[:m].dtype == ref_idx.dtype
                assert idx[:m].tolist() == ref_idx.tolist(), (point_id, n, m)
                assert step[:m].tolist() == ref_step.tolist(), (point_id, n, m)
        item.result_cf()
        for n in (item.max_claim_dur(), item.first_len() + 1):
            assert item.cohort_year_idx(n).tolist() == np.minimum(np.arange(n) // 12, 10).tolist()
            assert item.cohort_anniv_step(n).tolist() == np.where(
                np.arange(1, n + 1) % 12 == 0, g, 1.0).tolist(), "a reader mutated the cache"


def test_bu_cohort_index_and_step_are_read_only(product_models):
    """A write into ``cohort_year_idx`` or ``cohort_anniv_step``, or a slice of it, raises."""
    model = product_models("berufsunfaehigkeit")
    item = model.Projection[model.Data.model_point_table().index[0]]
    for n in (item.max_claim_dur(), item.first_len() + 1):
        for array in (item.cohort_year_idx(n), item.cohort_anniv_step(n)):
            before = array.tolist()
            with pytest.raises(ValueError):
                array[0] = 5
            with pytest.raises(ValueError):
                array[:13][0] = 5
            with pytest.raises(ValueError):
                array[:13] *= 2
            assert array.tolist() == before
    assert item.cohort_year_idx(item.max_claim_dur())[0] == 0


def test_bu_claim_years_are_read_from_the_claim_duration_table(tmp_path, product_models):
    """The claim-year cap is the table's last ``dur_year``, so a twelfth row is read too."""
    data = product_models("berufsunfaehigkeit").Data
    table = data.claim_duration_table()
    last = data.claim_duration_last_year()
    assert type(last) is int and last == int(table.index.max()) == len(table) == 11
    folder = product_copy(tmp_path, "berufsunfaehigkeit")
    path = folder / "claim_duration_table.csv"
    path.write_text(path.read_text(encoding="utf-8") + '12,0.005,1.1,"[std] test fixture"\n',
                    encoding="utf-8")
    copy = mx.read_model(folder / MODELS["berufsunfaehigkeit"], name="ClaimYearProbe")
    try:
        assert copy.Data.claim_duration_last_year() == 12
        item = copy.Projection[copy.Data.model_point_table().index[0]]
        assert [item.claim_year(z) for z in (1, 12, 13, 132, 133, 144, 145, 999)] == [
            1, 1, 2, 11, 12, 12, 12, 12]
        assert item.recov_rates()[11] == 0.005 and len(item.recov_rates()) == 12
        assert item.mort_dis_sel_factors()[11] == 1.1 and len(item.mort_dis_sel_factors()) == 12
        assert item.cohort_year_idx(300).tolist() == np.minimum(np.arange(300) // 12, 11).tolist()
    finally:
        copy.close()


def test_bu_rate_arrays_by_age_equal_the_tuples(product_models):
    """``dis_keep_year*``, ``dis_q_year*`` and ``recov_year*`` hold the tuples' values as arrays.

    The keep factor is ``(1 - q)(1 - r)`` of the tuples at ``x``, element for element; the
    arrays survive a full run unmutated.
    """
    model = product_models("berufsunfaehigkeit")
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        item.result_cf()
        ages = {item.age(t) for t in range(item.proj_len() + 1)}
        ages_first = {item.age_first(s) for s in range(item.first_len() + 1)}
        for x in sorted(ages):
            qy, ry = item.mort_rate_dis_mth_year(x), item.recov_rate_mth_year()
            keep = item.dis_keep_year(x)
            assert isinstance(keep, np.ndarray) and len(keep) == 11
            assert keep.tolist() == [(1.0 - q) * (1.0 - r) for q, r in zip(qy, ry)], (point_id, x)
            assert item.dis_q_year(x).tolist() == list(qy), (point_id, x)
        assert item.recov_year().tolist() == list(item.recov_rate_mth_year())
        for x in sorted(ages_first):
            qy, ry = item.mort_rate_dis_first_mth_year(x), item.recov_rate_first_mth_year()
            assert item.dis_keep_year_first(x).tolist() == [
                (1.0 - q) * (1.0 - r) for q, r in zip(qy, ry)], (point_id, x)
            assert item.dis_q_year_first(x).tolist() == list(qy), (point_id, x)
        assert item.recov_year_first().tolist() == list(item.recov_rate_first_mth_year())


def test_index_lapse_beyond_the_table_raises_key_error():
    folder = PRODUCTS_DIR / "indexpolice" / MODELS["indexpolice"]
    copy = mx.read_model(folder, name="IndexLapseProbe")
    try:
        last = int(copy.Data.lapse_table().index.max())
        item = copy.Projection[copy.Data.model_point_table().index[0]]
        t = 12 * (last + 1)
        assert item.duration(t) == last + 1
        assert item.lapse_rate_base(12 * last) == float(
            copy.Data.lapse_table().at[last, "lapse_rate"])
        with pytest.raises(Exception, match=f"KeyError: {last + 1}") as raised:
            item.lapse_rate_base(t)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_riester_ages_from_omega_minus_one_read_no_table(product_models):
    model = product_models("riester_rente")
    item = model.Projection[1]
    assert item.omega_age() == int(model.Data.mort_table().index.max()) + 1 == 111
    # 115 is in neither table, so a lookup there would raise.
    assert 115 not in model.Data.mort_table().index
    assert 115 not in model.Data.annuity_mort_table().index
    for x in (110, 115):
        assert item.mort_rate_at_age(x) == 1.0, x
        assert item.annuity_mort_rate(x, 2050) == 1.0, x
    assert item.mort_rate_at_age(109) == float(model.Data.mort_table().at[109, "qx"])


def test_riester_after_conversion_reads_no_schedule(product_models):
    model = product_models("riester_rente")
    item = model.Projection[1]
    k = item.k_conv()
    assert k > 0
    for k_after in (k, k + 100):
        assert not item.is_accum_y(k_after)
        assert not item.is_accum(12 * k_after)
        assert item.transfer_rate(12 * k_after) == 0.0, k_after
        assert item.income_ref(k_after) == 0.0, k_after
        assert item.zulage_entitlement_pp(k_after) == 0.0, k_after
        assert item.decl_rate(k_after) == 0.0, k_after


def test_riester_income_ref_at_zero_is_the_initial_income(product_models):
    model = product_models("riester_rente")
    table = model.Data.income_schedule()
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        if not item.is_accum_y(0):
            continue
        assert item.income_ref(0) == item.income_init(), point_id
        if item.is_accum_y(1):
            assert item.income_ref(1) == float(
                table.at[(item.income_id(), 0), "income"]), point_id


@pytest.mark.parametrize("product, column, cell, arg", [
    ("riester_rente", "zulage_id", "zulage_entitlement_pp", 0),
    ("riester_rente", "income_id", "income_ref", 1),
    ("risikolebensversicherung", "benefit_schedule_id", "benefit_factor", 0),
    ("risikolebensversicherung", "nvg_schedule_id", "sum_uplift_y", 0),
])
def test_an_unknown_schedule_id_raises_key_error(tmp_path, product, column, cell, arg):
    folder = product_copy(tmp_path, product)
    table = folder / "model_point_table.csv"
    points = pd.read_csv(table, index_col="point_id")
    point_id = points.index[0]
    points.loc[point_id, column] = "unbekannt"
    points.to_csv(table)
    copy = mx.read_model(folder / MODELS[product], name="ScheduleProbe")
    try:
        with pytest.raises(Exception, match="unbekannt") as raised:
            copy.Projection[point_id].cells[cell](arg)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_rlv_schedules_beyond_their_last_year_raise_key_error():
    product = "risikolebensversicherung"
    copy = mx.read_model(PRODUCTS_DIR / product / MODELS[product], name="RlvScheduleProbe")
    try:
        item = copy.Projection[copy.Data.model_point_table().index[0]]
        benefit = copy.Data.benefit_schedule()
        sched = item.benefit_schedule_id()
        last = int(benefit.loc[sched].index.max())
        t = 12 * last
        assert item.policy_year(t) == last + 1
        assert item.benefit_factor(t - 12) == float(
            benefit.at[(sched, last), "benefit_factor"])
        with pytest.raises(Exception, match=re.escape(f"KeyError: ('{sched}', {last + 1})")) \
                as raised:
            item.benefit_factor(t)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
        nvg = copy.Data.nvg_schedule()
        nvg_id = item.nvg_schedule_id()
        last = int(nvg.loc[nvg_id].index.max())
        assert item.sum_uplift_y(last - 1) == float(nvg.at[(nvg_id, last), "sum_uplift"])
        with pytest.raises(Exception, match=re.escape(f"KeyError: ('{nvg_id}', {last + 1})")) \
                as raised:
            item.sum_uplift_y(last)
        assert "KeyError" in str(raised.value) or isinstance(raised.value, KeyError)
    finally:
        copy.close()


def test_basis_net_cf_resid_reads_the_frame_through_its_dict(product_models):
    model = product_models("basisrente")
    projection = model.Projection
    assert projection.check_net_cf_resid._is_defined()
    assert projection.result_cf_dict._is_derived()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        frame = item.result_cf()
        columns = item.result_cf_dict()
        assert list(columns) == list(frame.columns), point_id
        for label in frame.columns:
            assert list(columns[label]) == list(frame.index), (point_id, label)
            for t in frame.index:
                assert columns[label][t] == frame.at[t, label], (point_id, label, t)
        for t in frame.index:
            row = frame.loc[t]
            expected = float(row["premiums"] + row["zuzahlungen"]
                             - row["claims_death"] - row["claims_annuity"]
                             - row["claims_survivor"] - row["expenses"]
                             - row["commissions"] - row["net_cf"])
            assert item.check_net_cf_resid(t) == expected, (point_id, t)
        with pytest.raises(Exception, match=f"KeyError: {item.proj_len()}\n"):
            item.check_net_cf_resid(item.proj_len())
