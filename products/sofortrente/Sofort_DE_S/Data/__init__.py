# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The five input CSVs are read here, **once per model**, and referenced from
:mod:`~.Sofort_DE_S.Projection` as ``data``. :mod:`~.Sofort_DE_S.Projection` is
parameterized by ``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its
own cells cache; if the readers lived there, every model point would re-read every file.
Holding them in an unparameterized Space reads each file once no matter how many points
are projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/sofortrente/``, rather than data stored inside the model. The model folder
therefore holds nothing but formulas — no ``_data/``, no IOSpec, no embedded values — so a
diff of the model shows logic changes only. This follows ``annuallife.TradLife_A``;
contrast ``basiclife.BasicTerm_S``, which keeps its inputs *inside* the model through
modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``Sofort_DE_S`` folder without its parent's CSVs produces a model that reads and then
fails on first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

============================  ==============================  ================================
Reference                     Cells                           File
============================  ==============================  ================================
model_point_file              model_point_table()             model_point_table.csv
surplus_scale_file            surplus_scale_table()           surplus_scale_table.csv
hoechstrechnungszins_file     hoechstrechnungszins_table()    hoechstrechnungszins_table.csv
ann_freq_file                 ann_freq_table()                ann_freq_table.csv
param_file                    param()                         param_tariff_type.csv
============================  ==============================  ================================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.loc``: the core's for ``model_point_table`` and ``hoechstrechnungszins_table``,
this space's ``surplus_scale_table_dict``, and ``ann_freq_table_keys``, the payment
frequencies the table allows.

Every file but ``model_point_table.csv`` carries a final ``provenance`` column, one tag
per row, per the library's second ruling. A model point is a *configuration* rather than
an assumption, and that is the only exemption.

.. rubric:: No mortality table is read here, and what a replacement must preserve

**DAV 2004 R and DAV 2004 R-Bestand are the property of the Deutsche Aktuarvereinigung,
are not public, and are not redistributed here.** They are cited by name in
``sources.md``. The death rates come from the core's table factory: the tariff chooses
``mort_table`` = ``dav2004r_proxy`` in ``param_tariff_type.csv``, a **[std]** proxy with
the structure the real table has and none of its values, whose parameters are rows of
``core/Core/Data/param_tables.csv``, each with its provenance. Both lives read it, each
at its own birth year.

The table is **generational**: the first-order rate at attained age ``x`` of the birth
year ``g`` is ``q_base x (1 - trend(x))^(g + x - 2005)``, the rate of the calendar year
``g + x``, with the base year 2005 the table's own. The base rate is Gompertz,
``0.008 x 1.11^(x - 65)`` for men and 0.6 of it for women, over ages 0 to 120 and closed
with ``q = 1`` at 120, so the end age 121 is :func:`~.Sofort_DE_S.Projection.omega_age`;
the trend is 2,5 % a year up to age 75, grading linearly to 1,25 % at 90 and to zero at
120, the same for both sexes. The anchor, born 1962, reads exponent
``1962 + 65 - 2005 = 22`` at 65.

The projection derives two rates from it. The **tariff rate** is the unisex blend
``0.45 q_M + 0.55 q_F`` at ``unisex_mix_male``, the same for a man and a woman of equal
age and birth year. The **best estimate** is the own sex's rate times
``mort_be_factor = 1.2`` and a trend term ``T = ((1 - 0.8 trend(x)) / (1 - trend(x)))^(g
+ x - 2005)`` at ``mort_be_trend_factor = 0.8``: below the cap that is
``1.2 x q_base x (1 - 0.8 trend(x))^(g + x - 2005)``, a best estimate that improves at
0.8 of the table's trend. A table rate of 1 stays 1.

**What a replacement must preserve.** Three things, and a substitution that keeps only
the first is not a substitution for this table. (i) The **generational structure**: a
``q(x, cohort)`` surface, not a period table, because a period proxy applied to a
forty-year annuity understates the liability by a margin that dwarfs every other
assumption. (ii) The **first-order margin in both dimensions**: the best estimate above
the table in level (``mort_be_factor = 1.2``) *and* improving more slowly
(``mort_be_trend_factor = 0.8``), because prudence in an annuity table must reach the
rate of improvement as well as its level. (iii) The **age-adjustment convention** —
here, integer attained age last birthday with the closing age 120 — since a table
supplied with an *Altersverschiebung* must have it applied before it is read here.
Replacing the level alone leaves the wedge between the two bases wrong, and that wedge is
the systematic *Risikoüberschuss* this product's *Überschussrente* is largely financed
from.

The other two assumption files are levels, not tables. ``surplus_scale_table.csv`` gives
the opening *Überschussrente* share and its annual growth for each of the four
*Überschussverwendung* forms, all [std]: no *Überschussanteilsatz* was established at any
carrier for any year. ``hoechstrechnungszins_table.csv`` is the statutory rate history a
model point's tariff rate is checked against, by the contract's own vintage — a German
in-force book is a stack of cohorts and each carries its own cap.
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

def surplus_scale_table():
    """The *Überschussverwendung* scale by form, from *surplus_scale_table.csv*.

    Indexed by ``surplus_form``.  ``surplus_init_pct`` is the *Überschussrente* at outset
    as a fraction of the *garantierte Rente* and ``surplus_growth`` its annual increase,
    for the four forms ``none`` / ``konstant`` / ``teildynamisch`` / ``volldynamisch``.

    Every figure is **[std]**.  No *Überschussanteilsatz* was established for this product
    at any carrier for any year; what the corpus establishes is the *shape* — the constant
    form highest at outset and flat in intention only, the volldynamic form lowest at
    outset and rising with each declaration.  The four forms are **not** calibrated to
    equal present value here, and a user who needs them to be must do that calibration.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / surplus_scale_file, index_col="surplus_form")  # noqa: F821


def ann_freq_table():
    """The payment frequencies an annuity may have, in instalments a year.

    Read from *ann_freq_table.csv*, one row per frequency, keyed by ``ann_freq``:
    12, 4, 2 and 1, monthly, quarterly, half-yearly and annual.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / ann_freq_file, index_col="ann_freq")           # noqa: F821


def surplus_scale_table_dict():
    """The *Überschussverwendung* scale as a dict by column: ``{column: {surplus_form: value}}``.

    Built once per model from ``surplus_scale_table()``; ``Projection.surplus_init_pct`` and
    ``surplus_growth`` read the columns of their names.
    """
    return surplus_scale_table().to_dict()


def ann_freq_table_keys():
    """The keys of ``ann_freq_table()`` as a ``frozenset`` of ``int``: 12, 4, 2 and 1.

    Built once per model; ``Projection.ann_freq`` checks the model point's frequency
    against it.
    """
    return frozenset(int(m) for m in ann_freq_table().index)


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

surplus_scale_file = "surplus_scale_table.csv"

hoechstrechnungszins_file = "hoechstrechnungszins_table.csv"

ann_freq_file = "ann_freq_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
