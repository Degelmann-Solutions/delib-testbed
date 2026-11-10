# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The eight input CSVs are read here, **once per model**, and referenced from
:mod:`~.RV_DE_S.Projection` as ``data``. :mod:`~.RV_DE_S.Projection` is parameterized by
``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its own cells cache;
if the readers lived there, every model point would re-read every file. Holding them in an
unparameterized Space reads each file once no matter how many policies are projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/klassische_rentenversicherung/``, rather than data stored inside the model. The
model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec, no embedded
values — so a diff of the model shows logic changes only. This follows
``annuallife.TradLife_A``; contrast ``basiclife.BasicTerm_S``, which keeps its inputs
*inside* the model through modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``RV_DE_S`` folder without its parent's CSVs produces a model that reads and then fails on
first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

========================  ============================  ==========================
Reference                 Cells                         File
========================  ============================  ==========================
model_point_file          model_point_table()           model_point_table.csv
mort_file                 mort_table()                  mort_table.csv
decl_rate_file            decl_rate_table()             decl_rate_table.csv
rentenfaktor_file         rentenfaktor_table()          rentenfaktor_table.csv
charge_file               charge_table()                charge_table.csv
lapse_file                lapse_table()                 lapse_table.csv
prem_freq_file            prem_freq_table()             prem_freq_table.csv
param_file                param()                       param_tariff_type.csv
========================  ============================  ==========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.at``: the core's for ``model_point_table``, ``mort_table``,
``rentenfaktor_table``, ``charge_table``, ``lapse_table`` and ``prem_freq_table``, this
space's ``decl_rate_table_dict`` with ``decl_rate_years``, the calendar range of each
scenario the declared rate is clamped to.

Every file but ``model_point_table.csv`` carries a per-row ``provenance`` column, this
library's second ruling: an assumption says on its own row where it came from. The model
point table is exempt because a model point is a *configuration* — one policy's own terms
— rather than an assumption.

.. rubric:: What is a proxy here, what it is anchored on, and what a replacement must preserve

Three of the seven assumption files are **[std] proxies for tables that exist and are not
redistributable**, and one is a scenario path standing in for declarations that were never
established. Each is anchored so that the technical notes' worked example reproduces
exactly, and the anchor is the thing a substitute must preserve.

``mort_table.csv`` — the first-order basis of this product is **DAV 2004 R**, a
*Generationentafel* which is the property of the Deutsche Aktuarvereinigung, is not public
and is **not shipped here**. What ships is a proxy with the structure the real table has
and none of its values: a sex-distinct base table ``q_base(sex, age)`` for base year
**2005** — the year DAV 2004 R was intended for new business — and an age-dependent annual
improvement rate ``improve(age)``, combined generationally as ``q_base x (1 -
improve)^(calendar_year - 2005)``. The base table is Gompertz, ``0.002000 x 1.09^(age -
50)`` for males and ``0.001300 x 1.09^(age - 50)`` for females, closed with ``q = 1`` at
age 120 so the projection ends with no survivors. The improvement is 1,5 % a year below
age 60, grading linearly to 0,5 % at age 100 and to zero at 110 — a deliberate
simplification of the *Starttrend* / *Zieltrend* structure the German construction
actually uses, documented as one rather than presented as a replication. **The anchor a
substitute table must preserve is ``q_base(M, 50) = 0.002000`` exactly**, together with
the 2005 base year and the terminal ``q = 1`` at age 120; with those three the worked
example still closes. Dropping a licensed or company generational table in place of this
one changes the basis with no formula change — but note that the table and the
*Rentenfaktor* below are **not calibrated to each other**, and the *Rentenfaktor* is
authoritative, so a substitution must either re-strike the factors or accept the
inconsistency.

``rentenfaktor_table.csv`` — the *aktueller Rentenfaktor* is the carrier's then-current
immediate-annuity tariff, and **no German market level was established for any carrier in
any year**. Three scenario paths ship, rising 2,5 % per year of age at *Rentenbeginn*:
``base`` anchored at **32,00 € per month per 10 000 € at age 67**, ``low`` at 25,50 € and
``high`` at 35,00 €. The anchors are chosen so both branches of the ``max(garantierter,
aktueller)`` rule are exercised by the shipped model points — the current factor wins on
point 1, the guarantee binds on point 13 — because a rule with one branch never exercised
is a rule no test covers. A replacement must keep ``base`` at age 67 equal to 32,00 € for
the worked example to close.

``decl_rate_table.csv`` — the declared *laufende Verzinsung* by calendar year and
scenario. The declaration instrument exists and its 2026 vintage is evidenced; **nothing
inside it is**. The ``base`` path is level at **2,55 % p.a.**, which sits inside the only
public pair the library has (2,53 % Klassik / 2,58 % Neue Klassik for 2025) and is a
market average rather than a carrier's declaration; ``low`` is level at 1,50 %. The path
is a scenario, not a forecast. It covers calendar years 2005 to 2060 and the reader in
:mod:`~.RV_DE_S.Projection` clamps to that range, so a projection running past 2060 holds
the last declared year flat.

``charge_table.csv``, ``lapse_table.csv``, ``prem_freq_table.csv`` and ``param_tariff_type.csv``
carry levels that are **[std] throughout** with two exceptions that are cited rather than
chosen: the *Höchstzillmersatz* of 25 ‰ of the *Beitragssumme* (40 ‰ before 1 January
2015), and the five-year spread of acquisition costs that § 169 Abs. 3 VVG imposes on the
surrender floor. The lapse table's one shaped feature is the **duration-12 step**, at the
twelve-year threshold § 20 Abs. 1 Nr. 6 EStG puts on the halving of the taxable gain: the
shape is argued, every level is a placeholder.
"""

from modelx.serialize.jsonvalues import *

_formula = None

_bases = [
    ".CoreData"
]

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def decl_rate_table():
    """The declared *laufende Verzinsung* by ``(scenario_id, calendar_year)``.

    Read from *decl_rate_table.csv*.  The declared rate **contains** the guarantee: it is
    the *Garantieverzinsung* plus the *laufende Zinsüberschussbeteiligung*, never a surplus
    on top of the guarantee, which is what the ``max(0, .)`` in
    :func:`~.RV_DE_S.Projection.bonus_rate` implements.  Levels are **[std]**.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / decl_rate_file,                                # noqa: F821
        index_col=["scenario_id", "calendar_year"])


def decl_rate_table_dict():
    """The declared rates as a dict by column: ``{column: {(scenario_id, calendar_year): rate}}``.

    Built once per model from ``decl_rate_table()``, keyed by the tuple of its two index
    columns; ``Projection.decl_rate`` reads its ``decl_rate`` column.
    """
    return decl_rate_table().to_dict()


def decl_rate_years():
    """The calendar range of each scenario: ``{scenario_id: (first_year, last_year)}``.

    Built once per model from the index of ``decl_rate_table()``, the bounds
    ``Projection.decl_rate`` clamps the calendar year to.
    """
    years = decl_rate_table().index.to_frame(index=False).groupby(
        "scenario_id")["calendar_year"]
    return {scen: (int(lo), int(hi))
            for scen, lo, hi in zip(years.min().index, years.min(), years.max())}


def charge_table_index():
    """The index columns of *charge_table.csv*: ``charge_id`` and ``item``.

    Two charge sets: ``zillmer_25`` for contracts concluded from 1 January 2015 and
    ``zillmer_40`` for the earlier *Höchstzillmersatz*.  Six items each —
    ``charge_acq_bsum_once``, ``charge_admin_prem_inst``, ``charge_admin_av_ann``,
    ``charge_admin_pup_av_ann``, ``stornoabzug_rate`` and ``min_annuity_mth``; the
    five-year spread is the core's ``surr_spread_years``.  Keyed per item so each number
    carries its own provenance tag.

    A **charge** is a deduction the tariff makes from the premium or the
    *Deckungskapital*: it moves money inside the contract and produces no cash flow.  An
    **expense** is the insurer's own outgo and is a cash flow.  The two are different
    things and confusing them is a listed pitfall; the expense levels live in
    the parameter file ``param_file``, read through ``param``.

    Override reason: the table is keyed per item, so each number carries its own
    provenance, by ``charge_id`` and ``item``,
    products/klassische_rentenversicherung/technical-notes.md:223
    """
    return ["charge_id", "item"]


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

mort_file = "mort_table.csv"

decl_rate_file = "decl_rate_table.csv"

rentenfaktor_file = "rentenfaktor_table.csv"

charge_file = "charge_table.csv"

lapse_file = "lapse_table.csv"

prem_freq_file = "prem_freq_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
