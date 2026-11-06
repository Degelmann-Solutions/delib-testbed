# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The eight input CSVs are read here, **once per model**, and referenced from
:mod:`~.BU_DE_S.Projection` as ``data``. :mod:`~.BU_DE_S.Projection` is parameterized by
``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its own cells cache;
if the readers lived there, every model point would re-read every file. Holding them in
an unparameterized Space reads each file once no matter how many policies are projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/berufsunfaehigkeit/``, rather than data stored inside the model. The model
folder therefore holds nothing but formulas — no ``_data/``, no IOSpec, no embedded
values — so a diff of the model shows logic changes only. This follows
``annuallife.TradLife_A``; contrast ``basiclife.BasicTerm_S``, which keeps its inputs
*inside* the model through modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``BU_DE_S`` folder without its parent's CSVs produces a model that reads and then fails
on first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

========================  ============================  ==========================
Reference                 Cells                         File
========================  ============================  ==========================
model_point_file          model_point_table()           model_point_table.csv
inception_file            inception_table()             inception_table.csv
claim_duration_file       claim_duration_table()        claim_duration_table.csv
mort_file                 mort_table()                  mortality_table.csv
occupation_file           occupation_table()            occupation_table.csv
lapse_file                lapse_table()                 lapse_table.csv
freq_loading_file         freq_loading_table()          freq_loading_table.csv
param_file                param()                       param_tariff_type.csv
========================  ============================  ==========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.loc``: the core's for ``model_point_table``, ``mort_table``,
``lapse_table`` and ``freq_loading_table``, this space's ``inception_table_dict``,
``claim_duration_table_dict`` and ``occupation_table_dict``, with ``inception_table_ages``
and ``mort_table_ages``, the age range the lookups clamp to.

Every file but ``model_point_table.csv`` carries a per-row ``provenance`` column, which
is delib's second ruling: the citation discipline reaches the data files and is
machine-checked rather than merely practised. The model point table is the single
exemption, because a model point is a *configuration* and not an assumption.

.. rubric:: The biometric tables are [std] proxies, and what a replacement must preserve

**Nothing in this directory is a DAV table.** DAV 1997 I (*Invalidisierungswahrschein-
lichkeiten*), DAV 1997 RI (*Reaktivierungswahrscheinlichkeiten*), DAV 1997 TI
(*Sterbewahrscheinlichkeiten der Invaliden*) and DAV 2008 T are the property of the
Deutsche Aktuarvereinigung, are not published and are **not redistributed by delib**.
They are cited by name in the product's ``sources.md`` and the tables shipped beside this
model are anchored ``[std]`` constructions that reproduce their *shape* and nothing more.

Each proxy is anchored so that the technical notes' worked example reproduces exactly.
The three anchors, and what a replacement built from company or DAV data must preserve:

``inception_table.csv``
    ``inc_rate(30) = 0.001100`` exactly, on a two-slope Gompertz form
    ``0.00110 x 1.06^(min(x,45) - 30) x 1.13^(max(x,45) - 45)``. What must be preserved
    is the **age shape** — nearly flat to 30, moderate through the forties, sharply
    accelerating from the mid-forties, so that the last decade before the *Endalter*
    dominates the liability — and the declaration of whether the table is **gross or net
    of declinature**. The shipped table is gross, and ``accept_factor = 0.80`` sits on
    top of it; a table already net of declinature must be used with that factor at 1.00
    or the *Anerkennungsquote* is counted twice.

``mortality_table.csv``
    ``mort_rate_actv(30) = 0.000350`` exactly, with the disabled-lives rate at 4.00x it,
    both on ``1.095^(age - 30)``. What must be preserved is the **excess of disabled over
    active mortality** — never one rate for both states — and the fact that the active
    table is an insured-lives *Todesfall*-character shape rather than a population table.

``claim_duration_table.csv``
    ``recov_rate(1) = 0.250`` falling to ``0.006`` ultimate, with disabled-mortality
    select factors 3.0 / 2.0 / 1.6 / 1.4 / 1.3 and 1.2 from claim year 6. What must be
    preserved is the **duration shape**: reactivation is concentrated in the first one to
    two claim years and is close to zero after about five, and disabled-lives mortality
    is itself select on claim duration. A flat reactivation rate is a modelling error,
    not a simplification, and it is worth roughly a factor of two on projected benefit.

The remaining three files are market conventions rather than biometric bases:
``occupation_table.csv`` carries the five-class *Berufsgruppen* cut with BG1 at 1.00 and
BG4 at 3.00 as its anchors, ``lapse_table.csv`` a low German BU *Stornoquote* falling
from 4.0 % to a 2.0 % ultimate, and ``freq_loading_table.csv`` the
*Ratenzahlungszuschlag* ladder with the months between instalments. All three are
``[std]``: no German insurer publishes any of them.
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

def inception_table():
    """The annual *Invalidisierungswahrscheinlichkeit* by attained age, ages 18-66.

    Read from *inception_table.csv*.  A **[std]** two-slope Gompertz proxy for the
    reference occupational class BG1, unisex and **gross of declinature**, anchored at
    ``inc_rate(30) = 0.001100``; DAV 1997 I is DAV property and is not shipped.  See the
    Space docstring for what a replacement must preserve.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / inception_file, index_col="age")               # noqa: F821


def claim_duration_table():
    """The claim-duration table by claim year, from *claim_duration_table.csv*.

    Two columns on one index, because both quantities are select on the same duration:
    ``recov_rate``, the annual *Reaktivierungswahrscheinlichkeit*, and
    ``mort_dis_sel_factor``, the multiplier on disabled-lives mortality.  Rows 1-10 are
    claim years 1-10 and **row 11 is the ultimate**, applied to claim year 11 and beyond.
    Both columns are **[std]**; DAV 1997 RI and DAV 1997 TI are not shipped.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / claim_duration_file, index_col="dur_year")     # noqa: F821


def mort_table_index():
    """The index columns of *mortality_table.csv*: ``age`` alone.

    Read from *mortality_table.csv*: ``mort_rate_actv`` for lives in the *aktiv* and
    run-off ledgers and ``mort_rate_dis`` for lives in claim, before the claim-duration
    select factor.  Both are **[std]** Gompertz proxies anchored at
    ``mort_rate_actv(30) = 0.000350``, with the disabled rate at 4.00x the active one;
    DAV 2008 T and DAV 1997 TI are not shipped.  **Using one rate for both states is a
    numbered pitfall**, which is why the file carries two columns rather than one.

    Override reason: the table carries an active and a disabled rate (``mort_rate_actv``,
    ``mort_rate_dis``) keyed by ``age`` alone,
    products/berufsunfaehigkeit/technical-notes.md:352
    """
    return "age"


def occupation_table():
    """The occupational loading by *Berufsgruppe*, from *occupation_table.csv*.

    ``occ_factor`` multiplies the **inception rate** and reaches the premium only through
    the equivalence — it is not the *Risikozuschlag*, which loads the premium alone.  The
    ``label`` column carries the class description so that a model point's
    ``berufsgruppe`` is readable without the product specification open.  **[std]**: one
    base table with occupational loadings is how German BU pricing works, but no
    insurer's *Berufsgruppenverzeichnis* was retrievable and carrier classifications are
    not comparable with one another.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / occupation_file, index_col="berufsgruppe")     # noqa: F821


def inception_table_dict():
    """The inception rates as a dict by column: ``{column: {age: rate}}``.

    Built once per model from ``inception_table()``; ``Projection.inc_rate_at_age`` reads its
    ``inc_rate`` column.
    """
    return inception_table().to_dict()


def claim_duration_table_dict():
    """The claim-duration table as a dict by column: ``{column: {dur_year: value}}``.

    Built once per model from ``claim_duration_table()``; ``Projection.recov_rates`` and
    ``mort_dis_sel_factors`` read its ``recov_rate`` and ``mort_dis_sel_factor`` columns.
    """
    return claim_duration_table().to_dict()


def occupation_table_dict():
    """The occupational loadings as a dict by column: ``{column: {berufsgruppe: value}}``.

    Built once per model from ``occupation_table()``; ``Projection.occ_factor`` reads its
    ``occ_factor`` column.
    """
    return occupation_table().to_dict()


def inception_table_ages():
    """The age range of ``inception_table()``: ``(first_age, last_age)``, 18 and 66.

    Built once per model from its index; the bounds ``Projection.inc_rate_at_age`` clamps
    the attained age to.
    """
    ages = inception_table().index
    return (int(ages.min()), int(ages.max()))


def mort_table_ages():
    """The age range of the core's ``mort_table()``: ``(first_age, last_age)``, 18 and 70.

    Built once per model from its index; the bounds ``Projection.mort_rate_at_age`` and
    ``mort_rate_dis_at_age`` clamp the attained age to.
    """
    ages = mort_table().index
    return (int(ages.min()), int(ages.max()))


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

inception_file = "inception_table.csv"

claim_duration_file = "claim_duration_table.csv"

mort_file = "mortality_table.csv"

occupation_file = "occupation_table.csv"

lapse_file = "lapse_table.csv"

freq_loading_file = "freq_loading_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
