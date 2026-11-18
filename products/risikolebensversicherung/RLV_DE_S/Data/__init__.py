# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The six input CSVs are read here, **once per model**, and referenced from
:mod:`~.RLV_DE_S.Projection` as ``data``. :mod:`~.RLV_DE_S.Projection` is parameterized
by ``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its own cells
cache; if the readers lived there, every model point would re-read every file. Holding
them in an unparameterized Space reads each file once no matter how many policies are
projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/risikolebensversicherung/``, rather than data stored inside the model. The
model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec, no embedded
values — so a diff of the model shows logic changes only. This follows
``annuallife.TradLife_A``; contrast ``basiclife.BasicTerm_S``, which keeps its inputs
*inside* the model through modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``RLV_DE_S`` folder without its parent's CSVs produces a model that reads and then fails
on first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

========================  ============================  ==========================
Reference                 Cells                         File
========================  ============================  ==========================
model_point_file          model_point_table()           model_point_table.csv
benefit_schedule_file     benefit_schedule()            benefit_schedule.csv
nvg_schedule_file         nvg_schedule()                nvg_schedule.csv
lapse_file                lapse_table()                 lapse_table.csv
prem_freq_file            prem_freq_table()             prem_freq_table.csv
param_file                param()                       param_tariff_type.csv
========================  ============================  ==========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.at``: this space's ``benefit_schedule_dict`` and ``nvg_schedule_dict``.

**Every file but the model point table carries a per-row ``provenance`` column.** That is
this library's second ruling and it is machine-checked in
``tests/test_model_conventions_de.py``: a number in a shipped input file says where it
came from, in the same ``[S#]`` / ``[R#]`` / ``[REG-R#]`` / ``[std]`` vocabulary the
documents use. ``model_point_table.csv`` is the single exemption, because a model point is
a *configuration* — one policy's own terms — rather than an assumption.

.. rubric:: The death rates are no file of the product

The death rates come from the model-wide table factory, the space ``CoreTables``, which
``Projection`` reads through its Reference ``tables``. *param_tariff_type.csv* names the
tariff's two tables: ``mort_nr_table`` = ``dav2008t_nr_proxy`` for non-smokers and
``mort_r_table`` = ``dav2008t_r_proxy`` for smokers, and the smoker status of a life
selects its table.  Both are **[std]** first-order proxies on the law of Makeham::

    q(sex, x) = a(sex) + b(sex) x 1.1^x        capped at 1, ages 0 to 120, q = 1 at 120

whose numbers are rows of the table parameter file *param_tables.csv* beside the core's
loaders: the non-smoker table is 0.8 of the aggregate proxy ``dav2008t_proxy``, the smoker
table 2.2 times the non-smoker table at every age, and women stand at a setback of three
years of age against men.  The best estimate is ``mort_be_factor`` = 0.75 of the table on
the own sex, a row of *param_tariff_type.csv*.

The German first-order basis for a term product is **DAV 2008 T**, with its
**DAV 2008 T NR** and **DAV 2008 T R** smoker variants — derived by the DAV
*Arbeitsgruppe Biometrische Rechnungsgrundlagen* from German insurers' own policy data
over 2006 to 2008, adopted 4 December 2008 and restated as a *Fachgrundsatz* dated
29 November 2022, and expressly suitable for premium calculation but **not** for policies
written without a *Gesundheitsprüfung*. **Those tables are the property of the Deutsche
Aktuarvereinigung, are not public, and are not redistributed here.** They are cited by
name; the proxies stand in for them, and every tariff that reads a table shares it, so a
replacement is a change of the table parameter file and not of this product.

.. rubric:: The other four assumption files

The three schedule files are keyed on ``policy_year``, the **contractual 1-based label**,
and their values are left as they are: ``Projection`` reads them at ``t + 1``, ``t`` being
the model's 0-based period index.

``benefit_schedule.csv`` carries the three German *Versicherungssumme* shapes as factors
on the initial sum: ``konstant`` (1.0 at every year, the majority form, shipped for forty
years), ``linear_fallend`` (``(21 - policy_year)/20``, i.e. ``f(t) = (20 - t)/20``,
shipped for the twenty-year term model
point 4 is written on) and ``annuitaet_fallend_3pct`` (the outstanding balance of a
thirty-year annuity loan at 3,00 % nominal, shipped for model point 5's thirty-year term).
The falling schedules are **term-specific by construction**: an amortisation shape is
agreed at issue for a stated term, so a schedule id is written for the term it belongs to
rather than truncated from a longer one. A model that hard-codes a constant sum insured
cannot represent two of the three shapes the German market sells, which is why the
schedule is a first-class input.

``nvg_schedule.csv`` carries the cumulative *Nachversicherungsgarantie* multiplier
``sum_uplift``: ``keine`` is 1.0 throughout and is the base run, and
``nvg_zwei_erhoehungen`` steps to 1.2 at policy year 6 (``t = 5``) and 1.4 at policy
year 12 (``t = 11``). **No
event list, cap, exercise window or age limit was established from any document**, so the
take-up is exogenous — a schedule, not a modelled decision. What the model does with it is
not exogenous: each increment carries **its own** three-year § 161 window, so
``suicide_factor`` is a weighted average across tranches in the years after an increase.

``lapse_table.csv`` is 6 % in policy year 1, 4 % in years 2 and 3 and 3 % thereafter, all
**[std]**, argued from three structural features rather than from data: nothing is
forfeited by lapsing, exit is frictionless in time because the *Versicherungsperiode*
follows the *Zahlweise*, and the need that motivated the purchase amortises. The GDV
whole-market *Stornoquote* is a book average dominated by long-dated savings contracts and
is deliberately **not** used. The table's own row for the final policy year still reads
3 %; the model zeroes it, because a lapse and an expiry at the end of the last period
``t = n - 1`` are the same event paying the same nothing.

``prem_freq_table.csv`` carries the *Ratenzahlungszuschlag* — 1.000 annual, 1.02
half-yearly, 1.03 quarterly, 1.05 monthly — a German market convention with no carrier
attribution, and the instalment count that goes with it. Whether carriers strike the
loading on the *Bruttobeitrag* or the *Zahlbeitrag* was not established; this model loads
the billed amount, so the *Brutto* = *Zahl* + *Verrechnung* identity holds at every
frequency.
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

def benefit_schedule():
    """The *Versicherungssumme* factors by schedule id and **1-based** policy year.

    Read from *benefit_schedule.csv*.  ``konstant``, ``linear_fallend`` and
    ``annuitaet_fallend_3pct`` are the three German shapes; the two falling ones are
    written for the term of the model point that uses them, an amortisation schedule being
    agreed at issue for a stated term.  ``policy_year`` is the contractual label and runs
    from 1; ``Projection.benefit_factor`` reads it at ``t + 1``.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / benefit_schedule_file,                         # noqa: F821
        index_col=["schedule_id", "policy_year"])


def nvg_schedule():
    """The cumulative *Nachversicherungsgarantie* multiplier by schedule id and **1-based** policy year.

    Read from *nvg_schedule.csv*.  ``keine`` is 1.0 throughout — the base run — and
    ``nvg_zwei_erhoehungen`` steps twice.  Take-up is **exogenous**: no event list, cap,
    window or age limit was established from any document, so an increase is supplied as a
    schedule rather than modelled as a decision.  ``policy_year`` is the contractual label
    and runs from 1; ``Projection.sum_uplift`` reads it at ``t + 1``.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / nvg_schedule_file,                             # noqa: F821
        index_col=["nvg_id", "policy_year"])


def benefit_schedule_dict():
    """The benefit schedule as a dict by column: ``{column: {(schedule_id, policy_year): value}}``.

    Built once per model from ``benefit_schedule()``; ``Projection.benefit_factor`` reads
    its ``benefit_factor`` column.
    """
    return benefit_schedule().to_dict()


def nvg_schedule_dict():
    """The NVG schedule as a dict by column: ``{column: {(nvg_id, policy_year): value}}``.

    Built once per model from ``nvg_schedule()``; ``Projection.sum_uplift_y`` reads its
    ``sum_uplift`` column.
    """
    return nvg_schedule().to_dict()


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

benefit_schedule_file = "benefit_schedule.csv"

nvg_schedule_file = "nvg_schedule.csv"

lapse_file = "lapse_table.csv"

prem_freq_file = "prem_freq_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
