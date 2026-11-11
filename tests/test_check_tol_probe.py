"""The roll-forward checks still fail just above ``check_tol`` (retrospective A7, entry 22).

Entry 12 of epic-parameter-files replaced the check tolerances 1e-10 and 1e-09 of eight
products with the one core item ``check_tol`` = 1e-08 (``docs/core.md``, "The outputs and
checks"). This module shows the looser tolerance has not made the checks deaf: for every
product it takes the policy roll-forward (``check_pols_roll_fwd``, Sofort's
``check_lives_roll_fwd``) and disturbs one term of its residual, in memory, at one month by
``c`` times the check's own bound there, ``roll_fwd_tol() * max(pols_if_init(), 1.0)``.

- Undisturbed, the check is ``True`` and the residual at the month is at most 1 % of the
  bound, so the margin below the bound is real.
- Disturbed, the residual at the month moves by the disturbance (within 0.1 % of it), so the
  term enters the residual and is not fed back into the residual's other terms.
- At ``c = 1.01`` the check is ``False``, at ``c = 0.99`` it is ``True``.

The disturbance is an overridden cell of the model read by ``mx.read_model``: the term's
formula moves to a cell ``probe_<term>`` and the term becomes ``probe_<term>(...) +
probe_delta(t)``, with ``probe_delta`` the amount at the term's month and 0.0 elsewhere. No
file is written. The term is ``pols_if`` (Sofort ``lives_if``) at ``t0 + 1``: its value
enters the residual at ``t0`` and rolls forward from there, so the later residuals still
close. Basis's residual also tests ``pols_if`` against the sum of its two ledgers at every
month, so there the disturbance enters ``pols_if(t0 + 1)`` through the paying ledger.
"""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import modelx as mx
import pytest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

sys.path.insert(0, str(ROOT / "tools"))
from run_baseline import model_dir  # noqa: E402

# product -> the check, the term disturbed, the term's month relative to t0, and t0 where
# it is not ``t_start()``.
PROBES = {
    "basisrente": {"check": "check_pols_roll_fwd", "term": "pols_paying", "at": 1},
    # BU's model point carries no duration_init, so t_start() is not defined; its check
    # runs from t = 0.
    "berufsunfaehigkeit": {"check": "check_pols_roll_fwd", "term": "pols_if", "at": 1,
                           "t0": 0},
    "fondsgebundene_rentenversicherung": {"check": "check_pols_roll_fwd", "term": "pols_if",
                                          "at": 1},
    "indexpolice": {"check": "check_pols_roll_fwd", "term": "pols_if", "at": 1},
    "kapitallebensversicherung": {"check": "check_pols_roll_fwd", "term": "pols_if", "at": 1},
    "klassische_rentenversicherung": {"check": "check_pols_roll_fwd", "term": "pols_if",
                                      "at": 1},
    "pflegerentenversicherung": {"check": "check_pols_roll_fwd", "term": "pols_if", "at": 1},
    "riester_rente": {"check": "check_pols_roll_fwd", "term": "pols_if", "at": 1},
    "risikolebensversicherung": {"check": "check_pols_roll_fwd", "term": "pols_if", "at": 1},
    "sofortrente": {"check": "check_lives_roll_fwd", "term": "lives_if", "at": 1},
}
CASES = {"above": (1.01, False), "below": (0.99, True)}
PRODUCTS = sorted(p.name for p in PRODUCTS_DIR.iterdir() if p.is_dir())


def test_every_product_has_a_probe():
    assert sorted(PROBES) == PRODUCTS


def _point_id(model):
    """The first model point that stands for a positive policy count."""
    for point_id in model.Data.model_point_table().index:
        if model.Projection[point_id].pols_if_init() > 0:
            return point_id
    raise AssertionError("no model point with pols_if_init() > 0")


def _bound(item) -> float:
    """The check's tolerance at a month, as every product's roll-forward computes it."""
    return item.roll_fwd_tol() * max(item.pols_if_init(), 1.0)


def _install_probe(projection, term: str) -> None:
    """Move ``term``'s formula to ``probe_<term>`` and make ``term`` add ``probe_delta(t)``."""
    cell = projection.cells[term]
    signature = inspect.signature(cell.formula.func)
    source = re.sub(rf"^def {term}\(", f"def probe_{term}(", cell.formula.source,
                    count=1, flags=re.MULTILINE)
    projection.new_cells(name=f"probe_{term}", formula=source)
    projection.new_cells(name="probe_delta", formula="lambda t: 0.0")
    args = ", ".join(signature.parameters)
    cell.formula = f"def {term}{signature}:\n    return probe_{term}({args}) + probe_delta(t)\n"


def _set_delta(projection, month: int, delta: float) -> None:
    projection.cells["probe_delta"].formula = (
        f"lambda t: {delta!r} if t == {month} else 0.0")


@pytest.mark.parametrize("case", sorted(CASES))
@pytest.mark.parametrize("product", sorted(PROBES))
def test_the_roll_forward_fails_just_above_its_bound(product, case):
    probe = PROBES[product]
    check, term = probe["check"], probe["term"]
    c, expected = CASES[case]
    where = f"{product}: {check}, term {term}"
    model = mx.read_model(model_dir(PRODUCTS_DIR / product),
                          name=f"CheckTolProbe_{product}_{case}")
    try:
        point_id = _point_id(model)
        item = model.Projection[point_id]
        t0 = probe["t0"] if "t0" in probe else item.t_start()
        bound = _bound(item)
        resid_old = getattr(item, f"{check}_resid")(t0)
        assert getattr(item, check)() is True, f"{where}: undisturbed check is not True"
        assert abs(resid_old) <= 0.01 * bound, (
            f"{where}: undisturbed residual {resid_old!r} at t = {t0} is not far inside "
            f"the bound {bound!r}")

        delta = c * bound
        _install_probe(model.Projection, term)
        _set_delta(model.Projection, t0 + probe["at"], delta)
        item = model.Projection[point_id]
        resid_new = getattr(item, f"{check}_resid")(t0)
        assert abs(abs(resid_new - resid_old) - delta) <= 1e-3 * delta, (
            f"{where}: disturbing {term}({t0 + probe['at']}) by {delta!r} moved the "
            f"residual at t = {t0} by {resid_new - resid_old!r}")
        assert bool(getattr(item, check)()) is expected, (
            f"{where}: disturbed by {c} x the bound, the check is not {expected}")
    finally:
        model.close()
