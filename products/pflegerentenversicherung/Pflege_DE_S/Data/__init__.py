# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""Input data shared by every by-policy projection.

The eight input CSVs are read here, **once per model**, and referenced from
:mod:`~.Pflege_DE_S.Projection` as ``data``. :mod:`~.Pflege_DE_S.Projection` is
parameterized by ``point_id``, so each ``Projection[N]`` is a separate ItemSpace with its
own cells cache; if the readers lived there, every model point would re-read every file.
Holding them in an unparameterized Space reads each file once no matter how many policies
are projected.

Inputs are **external files**: plain CSVs in the model folder's parent directory,
``products/pflegerentenversicherung/``, rather than data stored inside the model. The
model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec, no embedded
values — so a diff of the model shows logic changes only. This follows
``annuallife.TradLife_A``; contrast ``basiclife.BasicTerm_S``, which keeps its inputs
*inside* the model through modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``Pflege_DE_S`` folder without its parent's CSVs produces a model that reads and then
fails on first evaluation.

:func:`input_dir` resolves the directory from ``_model.path.parent`` at run time, so the
model works wherever the repository is checked out. Each table has a filename Reference
and a reader Cells:

=========================  ==============================  =========================
Reference                  Cells                           File
=========================  ==============================  =========================
model_point_file           model_point_table()             model_point_table.csv
benefit_scale_file         benefit_scale_table()           benefit_scale_table.csv
mort_file                  mort_table()                    mort_table.csv
incidence_file             incidence_table()               incidence_table.csv
care_file                  care_table()                    care_table.csv
lapse_file                 lapse_table()                   lapse_table.csv
surrender_file             surrender_table()               surrender_table.csv
param_file                 param()                         param_tariff_type.csv
=========================  ==============================  =========================

Beside each reader stands a dict cell ``<reader>_dict()``, the same table as plain Python
dicts by column, built once per model, which the projection's lookups read instead of
``DataFrame.at``: the core's for ``model_point_table``, ``mort_table``
and ``lapse_table``, this space's for ``benefit_scale_table``, ``incidence_table``,
``care_table`` and ``surrender_table``.

Every file but ``model_point_table.csv`` carries a final ``provenance`` column, one tag
per row — the library's second ruling, asserted by
``tests/test_model_conventions_de.py``. A model point is a *configuration* rather than an
assumption, which is why it is the single exemption.

.. rubric:: The tables are ``[std]`` proxies, and what a replacement must preserve

**DAV 2008 P, the German market's standard multi-state *Pflegetafel*, is the property of
the Deutsche Aktuarvereinigung, is not public, and is not redistributed by this library.**
Neither is DAV 2008 T, DAV 2004 R or any other DAV table. They are cited by name in
``sources.md`` and nothing here is derived from them. What ships instead is a set of
shaped proxies, and the anchors below are what a substitute must reproduce for the
technical notes' worked example to close to the cent:

* ``mort_table.csv`` — active-life mortality, a **Gompertz proxy**
  ``1 - exp(-B c**age)`` by sex over ages 18 to 108, with ``mort_rate = 1.0`` at age 109.
  Anchored at ``q(65) = 1.35 %`` and ``q(85) = 10.5 %`` male, ``q(65) = 0.75 %`` and
  ``q(85) = 7.0 %`` female, which fix ``B_M = 1.47884e-05``, ``c_M = 1.110680``,
  ``B_F = 4.76290e-06``, ``c_F = 1.119962``. **A replacement must preserve those four
  anchor rates.**
* ``incidence_table.csv`` — the rate at which an active life enters *any* *Pflegegrad*,
  ``min(I0 exp(g (age - 65)), 0.50)`` with ``I0_F = 0.0110``, ``g_F = 0.1400``,
  ``I0_M = 0.0085``, ``g_M = 0.1380``. The slope is anchored on the one shape the research
  file states with confidence — prevalence roughly doubling every five years of age above
  75, a growth rate of ``ln 2 / 5 = 0.1386``.
* ``care_table.csv`` — the whole in-care basis in five rows. ``mort_mult`` is a multiple
  on the **force** of active mortality at the same age, not on the rate.

A replacement table must preserve four properties: **(a)** incidence by attained age, sex
and *grade of entry*, because a stroke or a fracture enters directly at grade 3 or 4;
**(b)** deterioration dominating recovery above age 75; **(c)** mortality in care as a
grade-increasing multiple of active mortality; and **(d)** transition probabilities out of
each state summing, with the stay probability, to one. Dropping a licensed or company
table in place of these changes the basis with no formula change.

The remaining tables are standardizations of a different kind: ``lapse_table.csv`` and
``surrender_table.csv`` encode a shape argued from the *Zillmerung* and the § 169 VVG
five-year spread rather than from data — no lapse rate and no *Rückkaufswert* for a German
*Pflegerente* at any duration was established — and ``param_tariff_type.csv`` holds the scalar
parameters by ``item``. Its first twelve rows are the bases and conventions: the
terminal age ``omega_age``, the unisex mix ``unisex_mix_male``, the
recovery-damping shape ``rec_age_ref`` / ``rec_age_decay``, the ``inc_cap`` shape device,
the *Beitragssumme* convention ``beitragssumme_cap_age``, the check tolerance
``roll_fwd_tol`` and the five first-order prudence margins ``inc_margin``, ``det_margin``,
``rec_margin``, ``care_mort_margin`` and ``act_mort_margin``, none of them cited; the
*Rechnungszins* is a model-point column. The last five rows are the expense assumptions with their ``unit``:
``acq_permille`` (‰ of *Beitragssumme*, charged once at ``t = 0``), ``admin_prem_pct``
(fraction of each *Beitrag* collected), ``admin_mth_pp`` (EUR per policy in force per month
at ``t = 0`` prices), ``claim_expense_pp`` (EUR per annuity payment made) and
``expense_infl`` (annual); they are placeholder levels whose only cited element is the
25 ‰ ceiling the acquisition charge is set exactly at. The two groups were the files
``basis_table.csv`` and ``expense_table.csv`` upstream; phase 3 merged them so that the
loader ``param()`` is the common core's.
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

def benefit_scale_table():
    """The *Leistungsstaffel* by schedule and *Pflegegrad*, from *benefit_scale_table.csv*.

    Two schedules ship.  ``delib_std`` is 0 / 30 / 50 / 75 / 100 % — the flatter, higher
    shape a *Pflegerente* aimed at the residential funding gap tends to use, and a
    **[std]** choice within an observed range.  ``bahr`` is the statutory
    10 / 20 / 30 / 40 / 100 % minimum grid of § 127 SGB XI, the only *Leistungsstaffel*
    fixed by German statute; it is carried for comparison, since a *Pflegerente* written
    by a *Lebensversicherer* cannot be a *geförderter Tarif*.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / benefit_scale_file,                            # noqa: F821
        index_col=["staffel_id", "pflegegrad"])


def incidence_table():
    """Annual incidence into **any** *Pflegegrad* by sex and age, from *incidence_table.csv*.

    A **[std]** exponential proxy capped at ``inc_cap``.  It is the rate of leaving the
    active state for care; the grade actually entered is drawn from ``entry_share`` in
    *care_table.csv*, because entry is not uniformly at the lowest grade.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / incidence_file, index_col=["sex", "age"])      # noqa: F821


def care_table():
    """The whole in-care basis in five rows, from *care_table.csv*.

    ``entry_share`` is the distribution of the grade first entered and sums to 1.00;
    ``det_rate`` the annual deterioration rate to the next grade up, zero at grade 5;
    ``rec_rate`` the annual recovery rate to the grade below — to the active state from
    grade 1 — before the age damping; and ``mort_mult`` the multiple on the **force** of
    active mortality at the same age.

    ``entry_share`` is deliberately **not** the stock distribution of about
    9 / 44 / 27 / 14 / 6 %: entrants skew lower than the stock because deterioration moves
    people up over a spell, and using the stock as the entry mix is a listed pitfall.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / care_file, index_col="pflegegrad")             # noqa: F821


def surrender_table():
    """The guaranteed *Rückkaufswert* as a fraction of premiums paid to date.

    Read from *surrender_table.csv*, by *Versicherungsjahr* ``y(t) = t // 12 + 1``, 1 to 40:
    year ``k``'s ratio applies throughout policy year ``k``, ``t = 12(k - 1) … 12k - 1``,
    and year 40's applies thereafter, intermediate years interpolated in the shipped file.
    It is the **current** policy year, not the completed one — a surrender at ``t = 24``,
    two completed years, already takes year 3's ratio.  The
    scale-free form, which is the form a German contract states.  The shape encodes two
    cited facts — the 25 ‰ *Zillmerung* allowance, which is why the first two years are
    zero, and the § 169 Abs. 3 VVG five-year spread floor, which is why it turns positive
    in year three — and no cited level, because none was established.
    """
    return pd.read_csv(                                              # noqa: F821
        input_dir() / surrender_file, index_col="policy_year")       # noqa: F821


def benefit_scale_table_dict():
    """The *Leistungsstaffel* as a dict by column: ``{column: {(staffel_id, grade): pct}}``.

    Built once per model from ``benefit_scale_table()``, keyed by the tuple of its two index
    columns; ``Projection.benefit_pct`` reads its ``benefit_pct`` column.
    """
    return benefit_scale_table().to_dict()


def incidence_table_dict():
    """The incidence table as a dict by column: ``{column: {(sex, age): rate}}``.

    Built once per model from ``incidence_table()``, keyed by the tuple of its two index
    columns; ``Projection.inc_rate`` and ``tar_inc_rate`` read its ``inc_rate`` column.
    """
    return incidence_table().to_dict()


def care_table_dict():
    """The in-care basis as a dict by column: ``{column: {pflegegrad: value}}``.

    Built once per model from ``care_table()``; ``Projection.inc_share``, ``det_rate``,
    ``rec_rate``, ``mort_force_care`` and ``tar_mort_rate_care`` read its columns.
    """
    return care_table().to_dict()


def surrender_table_dict():
    """The *Rückkaufswert* ratios as a dict by column: ``{column: {policy_year: ratio}}``.

    Built once per model from ``surrender_table()``, the policy year **1-based**;
    ``Projection.rkw_pp`` reads its ``rkw_prem_ratio`` column.
    """
    return surrender_table().to_dict()


# ---------------------------------------------------------------------------
# References

model_point_file = "model_point_table.csv"

benefit_scale_file = "benefit_scale_table.csv"

mort_file = "mort_table.csv"

incidence_file = "incidence_table.csv"

care_file = "care_table.csv"

lapse_file = "lapse_table.csv"

surrender_file = "surrender_table.csv"

param_file = "param_tariff_type.csv"

pd = ("Module", "pandas")
