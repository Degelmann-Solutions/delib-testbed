# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The seven input CSVs are read here, **once per model**, and referenced from
:mod:`~.Riester_DE_S.Projection` as ``data``. :mod:`~.Riester_DE_S.Projection` is
parameterized by ``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its
own cells cache; if the readers lived there, every model point would re-read every file.
Holding them in an unparameterized Space reads each file once no matter how many policies
are projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/riester_rente/``, rather than data stored inside the model. The model folder
therefore holds nothing but formulas — no ``_data/``, no IOSpec, no embedded values — so
a diff of the model shows logic changes only. This follows ``annuallife.TradLife_A``;
contrast ``basiclife.BasicTerm_S``, which keeps its inputs *inside* the model through
modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``Riester_DE_S`` folder without its parent's CSVs produces a model that reads and then
fails on first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

=========================  ==============================  ==========================
Reference                  Cells                           File
=========================  ==============================  ==========================
model_point_file           model_point_table()             model_point_table.csv
lapse_file                 lapse_table()                   lapse_table.csv
zulage_file                zulage_schedule()               zulage_schedule.csv
income_file                income_schedule()               income_schedule.csv
surplus_file               surplus_table()                 surplus_scenario.csv
prem_freq_file             prem_freq_table()               prem_freq_table.csv
param_file                 param()                         param_tariff_type.csv
=========================  ==============================  ==========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.at`` and ``.loc``: the core's for ``lapse_table`` and ``surplus_table``, this
space's ``zulage_schedule_dict`` and ``income_schedule_dict``.

**Every file but ``model_point_table.csv`` carries a per-row ``provenance`` column**,
which is delib's second ruling: a model point is a *configuration*, every other row is an
*assumption* and says on the row where its number came from. The tags are the same
vocabulary the prose uses — ``[S#]``, ``[R#]``, ``[REG-R#]``, ``[std]`` with a rationale.

.. rubric:: No mortality table is read here, and what a replacement must preserve

The German first-order tables are the property of the **Deutsche Aktuarvereinigung**, are
not public, and are **not redistributed here**. They are cited by name and stood in for.
The death rates come from the core's table factory: the tariff chooses two tables in
``param_tariff_type.csv``, each a **[std]** proxy with the structure the real table has and
none of its values, whose parameters are rows of ``core/Core/Data/param_tables.csv``, each
with its provenance.

``mort_table`` = ``dav2008t_proxy`` stands in for **DAV 2008 T**, the death-risk table of
the accumulation. It is a Makeham proxy by sex, ``0.00022 + 2.882e-05 x 1.10^age`` for men
and ``0.00016 + 2.165e-05 x 1.10^age`` for women, women three years of age behind men,
over ages 0 to 120 and closed with ``q = 1`` at 120, and it carries **no improvement projection at
all**, because on a death cover improvement runs in the insurer's favour and a first-order
death basis does not anticipate it; it is read without a birth year. The projection
applies ``mort_be_factor = 0.75`` on the insured's own sex, which is the direction of
prudence for a death table: a first-order death basis assumes mortality *higher* than
expected, so the best estimate sits **below** it.

``annuity_mort_table`` = ``dav2004r_proxy`` stands in for **DAV 2004 R**, the annuitant
table, and the one structural property that is *not* optional is that it is
**generational**: the rate at attained age ``x`` of the birth year ``g``, issue year less
issue age, is ``q_base x (1 - trend)^(g + x - 2005)``, the rate of the calendar year
``g + x``, with the base year 2005 the table's own. A period-table proxy understates a
twenty-year-deferred annuitisation by a margin that dwarfs every other assumption in the
model, so a replacement may change the level and the trend but must keep the cohort. The
base rate is Gompertz, ``0.008 x 1.11^(age - 65)`` for men and 0.6 of it for women, over
ages 0 to 120 and closed with ``q = 1`` at 120; the trend is 2,5 % a year up to age 75,
grading linearly to 1,25 % at 90 and to zero at 120, the same for both sexes. It is applied
at ``annuity_mort_be_factor = 1.15`` on the own sex in the projection — the opposite
direction, because a first-order *annuity* table assumes mortality *lower* than expected —
and at 1.00 on the unisex blend, 45 % men (``unisex_mix_male``), inside
:func:`~.Riester_DE_S.Projection.ann_factor`, which is the first-order basis the market's
*Rentenfaktor* is struck on. On the anchor — age 67 in calendar 2044, born 1977 — that is
``ann_factor() = 24.78315099``, which puts ``rentenfaktor_curr()`` at 23,537497, below the
anchor's guaranteed 29,00, so that the **guaranteed** *Rentenfaktor* binds on the worked
example. Both tables end at 121, the limiting age ``omega_age()`` the projection runs to.

The six files besides ``model_point_table.csv`` are assumption or configuration tables
rather than proxies for a named instrument; each row says so in its own ``provenance``
cell.
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

def zulage_schedule():
    """The Zulage entitlement drivers by schedule id and projection period ``t``.

    Read from *zulage_schedule.csv*.  The ``t`` key is the model's own **0-based** time
    index, running ``0 ... 59``, and is read directly at ``t``.  Four drivers per row: ``unmittelbar``, the indicator
    that the *Grundzulage* is drawn at all; ``n_kinder_pre2008`` and
    ``n_kinder_post2008``, the counts of children for whom *Kindergeld* is drawn at the
    185 € and the 300 € rate — a permanent **birth-cohort** split, not a transition, so a
    contract can carry both at once; and ``bonus``, the once-in-a-lifetime
    *Berufseinsteiger-Bonus*.  The schedule is exogenous because *Kindergeld* is a
    household fact the insurance contract does not observe, which is the most awkward
    feature of this product for a per-policy projection.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / zulage_file, index_col=["zulage_id", "t"])     # noqa: F821


def income_schedule():
    """Contribution-liable earnings by schedule id and projection period ``t``.

    Read from *income_schedule.csv*.  The ``t`` key is the model's own **0-based** time
    index, running ``0 ... 59``.  ``income(t)`` is the earnings of the **calendar year of
    period t**; the § 86 *Mindesteigenbeitrag* of period ``t`` is struck on the
    **previous** calendar year, so the projection reads ``income(t - 1)`` and takes
    ``income_init`` from the model point for ``t = 0``.  The ``zero`` path encodes a
    *mittelbar zulageberechtigt* spouse, who has no contribution-liable earnings of their
    own and whose *Mindesteigenbeitrag* is therefore the 60 € *Sockelbeitrag*.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / income_file, index_col=["income_id", "t"])     # noqa: F821


def zulage_schedule_dict():
    """The Zulage drivers as a dict by column: ``{column: {(zulage_id, t): value}}``.

    Built once per model from ``zulage_schedule()``; ``Projection.zulage_entitlement_pp``
    reads its ``unmittelbar``, ``n_kinder_pre2008``, ``n_kinder_post2008`` and ``bonus``
    columns.
    """
    return zulage_schedule().to_dict()


def income_schedule_dict():
    """The earnings schedule as a dict by column: ``{column: {(income_id, t): income}}``.

    Built once per model from ``income_schedule()``; ``Projection.income_ref`` reads its
    ``income`` column.
    """
    return income_schedule().to_dict()


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

lapse_file = "lapse_table.csv"

zulage_file = "zulage_schedule.csv"

income_file = "income_schedule.csv"

surplus_file = "surplus_scenario.csv"

prem_freq_file = "prem_freq_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
