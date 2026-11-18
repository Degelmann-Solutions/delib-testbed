# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The seven input CSVs are read here, **once per model**, and referenced from
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
occupation_file           occupation_table()            occupation_table.csv
lapse_file                lapse_table()                 lapse_table.csv
prem_freq_file            prem_freq_table()             prem_freq_table.csv
param_file                param()                       param_tariff_type.csv
========================  ============================  ==========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.loc``: the core's for ``model_point_table``, ``lapse_table`` and
``prem_freq_table``, this space's ``inception_table_dict``,
``claim_duration_table_dict`` and ``occupation_table_dict``, with ``inception_table_ages``,
the age range the inception lookup clamps to, and ``claim_duration_last_year``, the claim
year the claim-duration lookups cap at.

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

**No mortality table is read here.** The death rates come from the core's table factory:
the tariff chooses ``dav2008t_proxy`` in the row ``mort_table`` of
``param_tariff_type.csv`` for the active lives and the run-off, a first-order proxy of
DAV 2008 T of which the projection takes 0.75, the row ``mort_be_factor``, as the best
estimate, and ``dav1997ti_proxy`` in the row ``mort_dis_table`` for the lives in claim, a
proxy of DAV 1997 TI at the best-estimate level, select on the claim year with the
factors 3.0 / 2.0 / 1.6 / 1.4 / 1.3 and 1.2 from claim year 6.  Both are distinct by sex
and ``[std]`` proxies on the law of Makeham.  What a replacement must preserve is the
**excess of disabled over active mortality** — never one table for both states — and
that disabled-lives mortality is itself select on claim duration.

Each proxy shipped here is anchored so that the technical notes' worked example
reproduces exactly.  The two anchors, and what a replacement built from company or DAV
data must preserve:

``inception_table.csv``
    ``inc_rate(30) = 0.001100`` exactly, on a two-slope Gompertz form
    ``0.00110 x 1.06^(min(x,45) - 30) x 1.13^(max(x,45) - 45)``. What must be preserved
    is the **age shape** — nearly flat to 30, moderate through the forties, sharply
    accelerating from the mid-forties, so that the last decade before the *Endalter*
    dominates the liability — and the declaration of whether the table is **gross or net
    of declinature**. The shipped table is gross, and ``accept_factor = 0.75`` sits on
    top of it; a table already net of declinature must be used with that factor at 1.00
    or the *Anerkennungsquote* is counted twice.

``claim_duration_table.csv``
    ``recov_rate(1) = 0.250`` falling to ``0.006`` ultimate. What must be preserved is
    the **duration shape**: reactivation is concentrated in the first one to two claim
    years and is close to zero after about five. A flat reactivation rate is a modelling
    error, not a simplification, and it is worth roughly a factor of two on projected
    benefit.

The remaining three files are market conventions rather than biometric bases:
``occupation_table.csv`` carries the five-class *Berufsgruppen* cut with BG1 at 1.00 and
BG4 at 3.00 as its anchors, ``lapse_table.csv`` a low German BU *Stornoquote* falling
from 4.0 % to a 2.0 % ultimate, and ``prem_freq_table.csv`` the
*Ratenzahlungszuschlag* ladder with the instalments a year. All three are
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

    One column, ``recov_rate``, the annual *Reaktivierungswahrscheinlichkeit*.  Rows 1-10
    are claim years 1-10 and **row 11 is the ultimate**, applied to claim year 11 and
    beyond.  **[std]**; DAV 1997 RI is not shipped.  The select factors of disabled-lives
    mortality, on the same duration, are items of the table factory's table of the lives
    in claim.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / claim_duration_file, index_col="dur_year")     # noqa: F821


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

    Built once per model from ``claim_duration_table()``; ``Projection.recov_rates`` reads
    its ``recov_rate`` column.
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


def claim_duration_last_year():
    """The last claim year of ``claim_duration_table()``, its largest ``dur_year``: 11.

    Built once per model from its index, which runs from 1 without a gap, the last row the
    ultimate; ``Projection.claim_year`` caps the claim year at it, ``cohort_year_idx`` the
    index at one below, and ``recov_rates`` and the per-claim-year mortality tuples
    ``mort_rate_dis_mth_year`` and ``mort_rate_dis_first_mth_year`` run over claim years 1
    to it.
    """
    return int(claim_duration_table().index.max())


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

inception_file = "inception_table.csv"

claim_duration_file = "claim_duration_table.csv"

occupation_file = "occupation_table.csv"

lapse_file = "lapse_table.csv"

prem_freq_file = "prem_freq_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
