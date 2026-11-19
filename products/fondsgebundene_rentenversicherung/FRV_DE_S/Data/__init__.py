# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The seven input CSVs are read here, **once per model**, and referenced from
:mod:`~.FRV_DE_S.Projection` as ``data``. :mod:`~.FRV_DE_S.Projection` is parameterized
by ``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its own cells
cache; if the readers lived there, every model point would re-read every file. Holding
them in an unparameterized Space reads each file once no matter how many policies are
projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/fondsgebundene_rentenversicherung/``, rather than data stored inside the
model. The model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec,
no embedded values — so a diff of the model shows logic changes only. This follows
``annuallife.TradLife_A``; contrast ``basiclife.BasicTerm_S``, which keeps its inputs
*inside* the model through modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``FRV_DE_S`` folder without its parent's CSVs produces a model that reads and then fails
on first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

========================  ============================  ==========================
Reference                 Cells                         File
========================  ============================  ==========================
model_point_file          model_point_table()           model_point_table.csv
lapse_file                lapse_table()                 lapse_table.csv
charge_file               charge_table()                charge_table.csv
fund_scenario_file        fund_scenario_table()         fund_scenario_table.csv
rentenfaktor_file         rentenfaktor_table()          rentenfaktor_table.csv
prem_freq_file            prem_freq_table()             prem_freq_table.csv
param_file                param()                       param_tariff_type.csv
========================  ============================  ==========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.loc``: the core's for ``model_point_table``,
``lapse_table``, ``rentenfaktor_table`` and ``prem_freq_table``, this space's
``fund_scenario_table_dict`` and ``charge_table_rows``, the charge table by row.

**Every file but ``model_point_table.csv`` carries a ``provenance`` column**, one tag per
row, and the library's conventions suite asserts it. That is this library's second
ruling: the citation discipline reaches the data files rather than stopping at the prose.
The model point table is the single exemption, because a model point is a *configuration*
— one policy's own terms — and not an assumption.

.. rubric:: The two decrement proxies, and what a replacement must preserve

Nothing in this product's source corpus was retrieved, and **no charge level, lapse rate
or *Rentenfaktor* was established at any carrier**. Three of the four assumption files
are therefore standardizations end to end, and the fourth and the death table stand in
for tables this library may not ship.

The product ships no mortality file. Its death table is ``dav2008t_proxy`` of the core's
table factory (``docs/core.md``, "The table factory"), which the tariff chooses in the
row ``mort_table`` of ``param_tariff_type.csv``: a **[std] Makeham-form proxy** of the
*first-order* DAV 2008 T death table by sex, for ages 0 to 120::

    q(M, x) = 0.00022 + b x 1.10^x,   b from the anchor q(M, 37) = 0.0012
    q(F, x) = 0.00016 + b x 1.10^(x - 3)

The tariff rate is the 50/50 blend of the two (``unisex_mix_male = 0.5``), 0.001048144 at
37, the value the notes' worked example rests on — it produces
``mort_rate_tariff_mth(0) = 0.001048144/12`` — and the best estimate is
``mort_be_factor = 0.75`` times the rate of the policy's own sex, ``mort_rate(0) =
0.00090`` on the anchor, a man. What a
replacement must preserve is the *direction* of the two bases: DAV 2008 T is a **death**
table with a first-order margin **above** best estimate, which is the opposite direction
from an annuity table, and the 10 % per year of age is an **insured-lives** gradient — a
proxy built on population mortality overstates claims at the working ages this product
lives at. DAV 2008 T is the property of the Deutsche Aktuarvereinigung, is not public and
is cited by name here rather than redistributed.

``rentenfaktor_table.csv`` is **[std] and derived, not observed**. At a *Rechnungszins*
of 0 % — the only conversion-basis statement with any corroboration anywhere in the delib
corpus, and that at one remove and for a *classic* tariff — a monthly annuity of ``R`` per
10 000 € for an expected ``T`` years has present value ``12 T R``, so::

    T_eff(x) = 100/3 - 0.75 (x - 67)            ages 60 to 75
    rentenfaktor_guar(x) = 10000 / (12 T_eff(x)) = 10000 / (400 - 9 (x - 67))

which is **exactly 25.00 at age 67**, 22.47 at 62 and 26.81 at 70. Read the other way,
25.00 prices the guarantee as though the insurer holds the capital for 33⅓ years and
earns nothing on it — the *Sicherheitsabschlag* made concrete. The ``std_2026`` row sets
the current factor equal to the guaranteed one, so the ``max(guaranteed, current)`` rule
is exercised without injecting an unsourced uplift; ``rich_current`` sets it 12 % higher
so that the ``max()`` visibly bites on one model point. The underlying table, DAV 2004 R,
is generational and is likewise cited and not shipped: a replacement must preserve a
**generational annuitant basis with a first-order margin**, which is a margin in the
*opposite* direction from the death table above.

``charge_table.csv``, ``lapse_table.csv`` and ``fund_scenario_table.csv`` are
standardizations of the same kind, each row carrying its own rationale in the
``provenance`` column. ``charge_table.csv`` holds one row per cost group, keyed by
``cost_group``, with the charges the four groups differ in; the acquisition spread
``acq_spread_years``, 5 in every group, is a row of ``param_tariff_type.csv``. The one
anchor in the charge stack is the *Höchstzillmersatz* of 25 ‰ of the *Beitragssumme*, and
``std_gross`` takes the cap rather than a guessed interior point.
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

def fund_scenario_table():
    """The gross fund return and TER by scenario and policy year, from *fund_scenario_table.csv*.

    Four **[std]** deterministic paths — ``base``, ``etf``, ``zero``, ``stress``.  The
    ``policy_year`` half of the key is the contractual 1-based label, reached through
    ``policy_year(t) = t // 12 + 1``, so it is unaffected by the 0-based frame.  The
    **TER is a return item, never a policy charge**: it is borne inside the *Anteilspreis*
    and never appears in the ledger, so the projection nets it off the gross return.
    Charging it explicitly double-counts; ignoring it overstates the policyholder's return.
    Nothing here is a PRIIPs performance scenario and nothing here may be compared with
    one — those are derived from an underlying's own return history, not chosen.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / fund_scenario_file,                            # noqa: F821
        index_col=["scenario_id", "policy_year"])


def rentenfaktor_table_index():
    """The index columns of *rentenfaktor_table.csv*: ``factor_id`` and ``annuity_age``.

    The table holds the guaranteed and current *Rentenfaktoren*, euro of monthly annuity per
    10 000 € of *Fondsguthaben*.  **[std]** and derived rather than observed — see the Space
    docstring for the derivation and for what the underlying DAV 2004 R basis requires of
    a replacement.  The table is indexed by the **age at *Rentenbeginn***, not by the
    attained age in the last projected month, which is one lower.

    Override reason: the table carries a guaranteed and a current factor per ``factor_id``
    and ``annuity_age``, products/fondsgebundene_rentenversicherung/model.md:369
    """
    return ["factor_id", "annuity_age"]


def fund_scenario_table_dict():
    """The fund paths as a dict by column: ``{column: {(scenario_id, policy_year): rate}}``.

    Built once per model from ``fund_scenario_table()``, keyed by the tuple of its two index
    columns; ``Projection.fund_return_gross_ann`` and ``fund_ter_ann`` read the columns they
    use.
    """
    return fund_scenario_table().to_dict()


def charge_table_rows():
    """The core's ``charge_table()`` as a dict by row: ``{cost_group: {column: value}}``.

    Built once per model, like the core's ``model_point_table_dict``; ``Projection.charge_row``
    returns the row of the policy's ``cost_group``, which its callers index by column.  The
    row is shared and read-only.
    """
    return charge_table().to_dict("index")


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

lapse_file = "lapse_table.csv"

charge_file = "charge_table.csv"

fund_scenario_file = "fund_scenario_table.csv"

rentenfaktor_file = "rentenfaktor_table.csv"

prem_freq_file = "prem_freq_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
