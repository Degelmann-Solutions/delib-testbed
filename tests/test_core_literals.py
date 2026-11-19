"""The References and formula literals that moved into the parameter files (``docs/core.md``,
"The parameter files" and "Formula literals").

- 31 of Riester's 32 former numeric References are rows of its tariff-type file with their
  literals' types and values, and no numeric Reference but ``point_id`` is left on its
  ``Projection``; the 32nd, ``mort_base_year``, went with its switch to the table factory.
  RLV's 17 likewise. KLV's 4 read ones likewise; its three References of the lapse modules that were never built, read by no cell, are in
  neither its ``Projection`` nor its parameter files. BU's 11, FRV's 12, Basis' 5,
  Index' 10 and 7 of Sofort's 10 likewise; 2 more of Sofort's, the bisection settings of its
  refund solve, are literals in its formula, and the tenth, ``mort_base_year``, went with its
  switch to the table factory. RV and Pflege never had one.
- Pflege's nine guards read the core item ``rate_cap_eps``, and no ``1e-12`` literal is left
  in its formulas. FRV's 3 actuarial formula literals (the tax step of ``lapse_tax_step``)
  are parameter items with their literals' types and values, the two statutory limbs in the
  core file; Index' five-year spread and KLV's five-year spread and three-year suicide
  window are items of the core file. Every other numeric literal of a formula cell of the
  core and the ten products, but 0, 1, 0.0 and 1.0, is structural and listed for its space
  in ``STRUCTURAL_LITERALS``, and every listed value occurs there.
- Riester's annuity frequency is a row ``ann_freq``, 12 as an ``int`` as Basis', and
  the *Rentenfaktor* unit of FRV, Index, RV and Riester a row ``rf_unit``, 10000.0 as Basis'.
"""
from __future__ import annotations

import ast

import pytest

from helpers import CORE_ITEMS, CORE_MODEL, MODELS, PRODUCTS_DIR, formula_cells


# The moved References and literals below are keyed by their current item names, which may
# differ from the References' names (docs/core.md, "Parameter names"). An item of the core file
# stands in the core layer, any other in the tariff-type layer.

def param_layer_of(item):
    """The layer a moved item stands in: the core file for an item of ``CORE_ITEMS``, the
    tariff-type file for any other."""
    return "core" if item in CORE_ITEMS else "tariff_type"


# 31 of the 32 numeric References Riester's ``Projection`` held, as their former Python literals,
# with the value entry 12 of epic-parameter-files aligned (``kleinbetrag_threshold_mth`` 39.55 to
# 59.33); the 32nd, ``mort_base_year`` 2027, an item until Riester's switch to the table factory,
# went for the item ``dav2004r_proxy_base_year`` of its annuitant table, 2005 (values package,
# open point 8).
RIESTER_MOVED_REFERENCES = {
    "valuation_year": 2027,
    "grundzulage": 175.0,
    "kinderzulage_pre2008": 185.0,
    "kinderzulage_post2008": 300.0,
    "berufseinsteiger_bonus": 200.0,
    "mindesteigenbeitrag_rate": 0.04,
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
    "kleinbetrag_threshold_mth": 59.33,
    "rentenfaktor_margin": 0.3,
    "annuity_rechnungszins": 0.01,
    "woolhouse": 0.4583333333333333,
    "annuity_mort_be_factor": 1.15,
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

# The 16 numeric References RLV's ``Projection`` held and its cells read, as their former
# Python literals; ``val_tol``, aligned to 1e-08 by entry 12 of epic-parameter-files, is read as
# ``check_tol``. The *Sicherheitszuschlag* ``sicherheitszuschlag_m`` 1.25, the item
# ``mort_load_first`` 2.25 until RLV's switch to the table factory, has no item: the tables are
# first order, and the item ``mort_be_factor`` 0.75 steps from them to the best estimate.
RLV_MOVED_REFERENCES = {
    "unisex_mix_male": 0.5,
    "surplus_share": 0.9,
    "decl_scale": 1.0,
    "v_max": 0.95,
    "load_acq_bsum_once": 0.025,
    "comm_acq_bsum_once": 0.02,
    "load_admin_prem_inst": 0.05,
    "load_admin_sum_ann": 0.0003,
    "expense_collect_prem_inst": 0.03,
    "comm_renew_prem_inst": 0.01,
    "suicide_share": 0.03,
    "suicide_years": 3,
    "shock_lapse_lambda": 0.0,
    "sel_lapse_lambda": 0.0,
    "sel_lapse_ref": 0.25,
    "check_tol": 1e-08,
}

# The 4 numeric References KLV's ``Projection`` held and its cells read, as their former
# Python literals.
KLV_MOVED_REFERENCES = {
    "suicide_share": 0.02,
    "bfz_min_sum": 2500.0,
    "term_surr_share": 0.0,
    "bwr_rate": 0.0,
}

# The 11 numeric References BU's ``Projection`` held, as their former Python literals, with the
# values entry 12 of epic-parameter-files aligned (``accept_factor`` 0.8 to 0.75, ``mort_dis_load_first``
# 0.8 to 0.7) and the value BU's switch to the table factory set (``mort_actv_load_first`` 0.8
# to 0.6, the load now on a first-order death table).
BU_MOVED_REFERENCES = {
    "accept_factor": 0.75,
    "inc_load_first": 1.3,
    "recov_load_first": 0.7,
    "mort_dis_load_first": 0.7,
    "mort_actv_load_first": 0.6,
    "load_acq_bsum_once": 0.025,
    "load_admin_prem_inst": 0.09,
    "load_admin_pp_ann": 18.0,
    "load_claim_assess_pp_once": 800.0,
    "load_claim_admin_pp_mth": 12.0,
    "runoff_months": 3,
}

# The 12 numeric References FRV's ``Projection`` held, as their former Python literals;
# ``val_tol`` 1e-10 is read as ``check_tol``, the same quantity with the same value, which entry 12
# of epic-parameter-files aligned to 1e-08.
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
    "check_tol": 1e-08,
}

# The 3 actuarial literals FRV's formulas held (``lapse_tax_step``), as written there.
FRV_MOVED_LITERALS = {
    "tax_step_min_year": 13,
    "tax_step_age": 62,
    "tax_step_factor": 2.5,
}

# The actuarial literal Index' formulas held (``prem_charge_acq_min_pp``), as written there.
INDEX_MOVED_LITERALS = {"surr_spread_years": 5}

# The actuarial literals KLV's formulas held (``res_min_pp``, ``benefit_death_pp``), as items.
# ``surr_spread_years`` was ``5.0`` there; its row is ``5``, an ``int`` as Index' row.
KLV_MOVED_LITERALS = {"surr_spread_years": 5, "suicide_years": 3}

# 4 of the 5 numeric References Basis' ``Projection`` held, as their former Python literals; the
# fifth, ``mort_base_year`` 2005, an item until Basis' switch to the table factory, is the item
# ``dav2004r_proxy_base_year`` of its table, 2005 as before.
BASIS_MOVED_REFERENCES = {
    "elig_surv_prob": 0.55,
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

# 7 of the 10 numeric References Sofort's ``Projection`` held, as their former Python literals;
# 2 more, ``solve_tol`` 1e-10 and ``solve_max_iter`` 200, are literals of ``annuity_pp_derived``;
# the tenth, ``mort_base_year`` 2025, an item until Sofort's switch to the table factory, went
# for the item ``dav2004r_proxy_base_year`` of its table, 2005 (values package, open point 8).
SOFORT_MOVED_REFERENCES = {
    "load_acq_sp_once": 0.025,
    "load_admin_annval_once": 0.02,
    "expense_acq_sp_once": 0.02,
    "expense_acq_pp_once": 200.0,
    "expense_admin_pp_ann": 60.0,
    "expense_pay_pp_inst": 1.5,
    "unisex_mix_male": 0.45,
}

# The products whose numeric References have all moved into their parameter files: all ten,
# RV and Pflege having never had one.
REFERENCES_MOVED = (
    "riester_rente", "risikolebensversicherung", "kapitallebensversicherung",
    "berufsunfaehigkeit", "fondsgebundene_rentenversicherung", "basisrente",
    "indexpolice", "sofortrente", "klassische_rentenversicherung",
    "pflegerentenversicherung",
)


def test_riester_references_stand_in_their_layer(product_models):
    model = product_models("riester_rente")
    data = model.Data
    layers = data.param_layers()
    assert len(RIESTER_MOVED_REFERENCES) == 31
    assert "mort_base_year" not in model.Projection.refs
    assert "mort_base_year" not in data.param_dict()
    assert data.param("dav2004r_proxy_base_year") == 2005
    for item, literal in RIESTER_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_rlv_references_stand_in_their_layer(product_models):
    model = product_models("risikolebensversicherung")
    data = model.Data
    layers = data.param_layers()
    assert len(RLV_MOVED_REFERENCES) == 16
    assert "sicherheitszuschlag_m" not in model.Projection.refs
    assert "mort_load_first" not in data.param_dict()
    assert data.param("mort_be_factor") == 0.75
    for item, literal in RLV_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_klv_references_stand_in_their_layer(product_models):
    model = product_models("kapitallebensversicherung")
    data = model.Data
    layers = data.param_layers()
    assert len(KLV_MOVED_REFERENCES) == 4
    for item, literal in KLV_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_bu_references_stand_in_their_layer(product_models):
    model = product_models("berufsunfaehigkeit")
    data = model.Data
    layers = data.param_layers()
    assert len(BU_MOVED_REFERENCES) == 11
    for item, literal in BU_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_frv_references_stand_in_their_layer(product_models):
    model = product_models("fondsgebundene_rentenversicherung")
    data = model.Data
    layers = data.param_layers()
    assert len(FRV_MOVED_REFERENCES) == 12
    for item, literal in FRV_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_frv_literals_stand_in_their_layer(product_models):
    data = product_models("fondsgebundene_rentenversicherung").Data
    layers = data.param_layers()
    assert len(FRV_MOVED_LITERALS) == 3
    for item, literal in FRV_MOVED_LITERALS.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item


def test_index_literals_stand_in_their_layer(product_models):
    data = product_models("indexpolice").Data
    layers = data.param_layers()
    assert len(INDEX_MOVED_LITERALS) == 1
    for item, literal in INDEX_MOVED_LITERALS.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item


def test_klv_literals_stand_in_their_layer(product_models):
    data = product_models("kapitallebensversicherung").Data
    layers = data.param_layers()
    assert len(KLV_MOVED_LITERALS) == 2
    for item, literal in KLV_MOVED_LITERALS.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item


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
def test_units_and_frequencies_stand_in_their_layer(product, product_models):
    data = product_models(product).Data
    layers = data.param_layers()
    for item, literal in UNIT_AND_FREQUENCY_ROWS[product].items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item


def test_basis_references_stand_in_their_layer(product_models):
    model = product_models("basisrente")
    data = model.Data
    layers = data.param_layers()
    assert len(BASIS_MOVED_REFERENCES) == 4
    assert "mort_base_year" not in model.Projection.refs
    assert "mort_base_year" not in data.param_dict()
    assert data.param("dav2004r_proxy_base_year") == 2005
    for item, literal in BASIS_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_index_references_stand_in_their_layer(product_models):
    model = product_models("indexpolice")
    data = model.Data
    layers = data.param_layers()
    assert len(INDEX_MOVED_REFERENCES) == 10
    for item, literal in INDEX_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_sofort_references_stand_in_their_layer(product_models):
    model = product_models("sofortrente")
    data = model.Data
    layers = data.param_layers()
    assert len(SOFORT_MOVED_REFERENCES) == 7
    assert "mort_base_year" not in model.Projection.refs
    assert "mort_base_year" not in data.param_dict()
    assert data.param("dav2004r_proxy_base_year") == 2005
    for item, literal in SOFORT_MOVED_REFERENCES.items():
        value = data.param(item)
        assert type(value) is type(literal) and value == literal, item
        assert item in layers[param_layer_of(item)], item
        assert item not in model.Projection.refs, item


def test_pflege_guards_read_the_core_epsilon():
    """Pflege's guards ``1.0 - 1e-12`` read ``1.0 - data.param("rate_cap_eps")``, and no
    ``1e-12`` literal is left in its formulas (its docstrings still give the value). Eleven
    until its switch to the table factory, nine since: the caps of the two tariff death rates
    went, a table rate of 1 passing through, and the force of a care grade took one."""
    path = PRODUCTS_DIR / "pflegerentenversicherung" / MODELS["pflegerentenversicherung"]
    text = (path / "Projection" / "__init__.py").read_text(encoding="utf-8")
    literals = [node for node in ast.walk(ast.parse(text))
                if isinstance(node, ast.Constant) and type(node.value) is float
                and node.value == 1e-12]
    assert literals == []
    assert text.count('1.0 - data.param("rate_cap_eps")') == 9


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
    "pflegerentenversicherung": {"2", "3", "4", "5", "12", "12.0"},
    "riester_rente": {"12", "12.0"},
    "risikolebensversicherung": {"2", "12", "12.0"},
    "sofortrente": {"0.5", "1e-10", "2", "12", "12.0", "200"},
}


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
        for name, cell in formula_cells(path):
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
