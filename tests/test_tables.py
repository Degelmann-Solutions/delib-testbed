"""The table factory (``docs/core.md``, "The table factory").

The loader's part, on scratch copies of RLV:

- Every shipped product reads the table parameter file ``param_tables.csv`` beside the core
  file as its layer ``tables``, second of the layers; the shipped file holds the rows of the
  factory's tables, each with its value, basis and provenance, and no other, and a copy
  without the file raises.
- A fixture item of a copy's ``param_tables.csv`` is read through ``param`` like any other.
- An item named ``<role>_table`` holds a table name and is loaded as a ``str``, in the
  tariff-type and the tariff file; a number or a value of another form raises, and a name
  as the value of any other item is still no number.
- An item of the tables layer in the tariff-type or the tariff file raises, naming both
  files, and so does an item of the core file in the tables file (the core lock).

The space ``core/Core/Tables``:

- Every product holds it as the symlink ``CoreTables``, lists it in ``_spaces`` and names it
  as a base of no space; its ``Projection`` reads it through the Reference ``tables``, the
  space reads the product's ``Data`` through ``data``, takes no parameter and holds the
  core's cells and no other, so no product defines one.
- Its source holds no numeric literal but 0 and 1 and no cell name containing ``mort`` or
  ``q`` besides ``q``, and its cells read only ``data.param`` and each other.
- Five tables are defined, all on the law ``makeham``, in every product. For
  ``dav2008t_proxy`` ``q`` gives ``a + b * c ** x`` in the law's float operations for both
  sexes, capped at 1 and exactly 1 at the closing age 120, the figures of the values package
  to their six digits; an age outside 0 to 120, a ``birth_year`` and a ``duration`` raise,
  and so does any other table name.
- ``dav1997ti_proxy`` is the first select table: ``q`` gives ``b * 1.095 ** x`` times the
  factor of the claim year, 3.0, 2.0, 1.6, 1.4, 1.3 and 1.2, capped at 1, the figures of the
  values package to their six digits at each select year; every claim year past the sixth
  has the sixth's rate; a missing ``duration``, one below 1 and a ``birth_year`` raise; an
  age outside 18 to 120 raises, and the rate at 120 is exactly 1.
- ``dav2004r_proxy`` is the first generational table, with the trend law ``trend_linear``:
  the trend is 0.025 up to age 75, linear to 0.0125 at 90, linear to 0 at 120 and 0 beyond,
  the same for both sexes; ``q`` gives ``b * 1.11 ** x * (1 - trend) ** (birth_year + x -
  2005)`` in the factory's float operations, capped at 1, the figures of the values package
  to their six digits at several birth years, with ``q_base(M, 65)`` 0.008 and women at 0.6
  of men; a missing ``birth_year`` and a ``duration`` raise; the rate at 120 is exactly 1
  for any birth year, and an age outside 0 to 120 raises.
- ``dav2008t_nr_proxy`` and ``dav2008t_r_proxy`` are the aggregate table scaled, period
  tables without selection: ``q`` gives ``a + b * 1.1 ** x`` with each table's items, capped
  at 1 and exactly 1 at 120; non-smokers stand at 0.8 of ``dav2008t_proxy`` and smokers at
  2.2 times non-smokers at every age below the cap, to the items' digits; the figures of
  the values package to their six digits; an age outside 0 to 120, a ``birth_year`` and a
  ``duration`` raise.
- On a scratch copy of Index with fixture tables and laws written into its ``CoreTables``
  and ``param_tables.csv`` beside the shipped table (``fixture_copy``): the period table
  gives its law's rate
  unrounded, 1 at the last age and at most 1; an age outside the table, another sex, a
  missing or a refused ``birth_year`` or ``duration`` and a duration below 1 raise, naming
  the table and the argument; the generational table applies its trend from its base year
  to the calendar year ``birth_year + x`` and not to the closure; the select table applies
  the factor of the duration and holds the last; a table naming an item the layer lacks
  raises the loader's ``KeyError``, and so does a gap in a table's select factors;
  ``items()`` lists every table's items.
- The runner's export engine, running the copy's points with per-contract cleanup, computes
  the same results as the modelx engine and keeps the rates of an earlier point in
  ``CoreTables`` after the point's item is deleted.

The derivation hooks of the core's ``Projection``:

- Only a switched product reaches a hook that reads the factory: ``mort_table_name`` and
  ``mort_rate_table`` are derived everywhere but ``mort_rate_table`` in Riester, reachable in
  the usage scan of Index, BU, KLV, FRV and Riester, which choose ``dav2008t_proxy`` as
  ``mort_table``, and of RV and Basis, which choose ``dav2004r_proxy``, and unreachable in
  RLV, whose two roles ``mort_nr_table`` and ``mort_r_table`` its own cell
  ``mort_table_smoker`` reads, and in Pflege, which holds no choice. Sofort chooses
  ``dav2004r_proxy`` as ``mort_table`` and reaches ``mort_table_name`` from its own hook
  ``mort_rate_gen``, read for each of two lives, and not ``mort_rate_table`` or
  ``mort_rate_at_age``. BU's second
  role, ``mort_dis_table``, is read by a hook of its own, ``mort_rate_dis_at_age``, which
  no other product has, and Riester's, ``annuity_mort_table``, by its payout hook
  ``annuity_mort_rate`` and its ``omega_age``; ``omega_age_table`` is reachable in RV,
  Basis and Sofort alone, whose ``omega_age`` reads it. Riester alone overrides
  ``mort_rate_table``, to read its main role, a period table, without the birth year of its
  second.
- Index reads its death rates through the factory alone: on every shipped point
  ``mort_rate(t)`` is ``q(dav2008t_proxy, sex, age(t))`` times its ``mort_be_factor`` 0.75,
  through the core's cells, none overridden but the factor; its folder holds no mortality
  file or column, its ``Data`` no Reference ``mort_file``, and no ``mort_table`` loader is
  reachable.
- BU reads its death rates through the factory alone, off two tables. Active lives: on
  every shipped point ``mort_rate(t)`` is ``q(dav2008t_proxy, sex, age(t))`` times 0.75
  through the core's cells, and the tariff rate of the pricing run the load 0.6 on the 50/50
  blend of the two sexes at ``age_first(s)``. Lives in claim: the best estimate is
  ``q(dav1997ti_proxy, sex, age(t), duration=claim_year(z))`` without a factor, the tariff
  rate the load 0.7 on the 50/50 blend at the same claim year; the per-claim-year tuples
  equal the addressable cells; the rates are the values package's to six digits. Its folder
  holds no mortality file or column, its ``Data`` no mortality Reference or cell, its
  ``Projection`` one read of the factory besides the core's hooks, through ``q``; an age
  is not clamped. On a scratch copy whose two tables close at the last age a point attains
  the best estimate and the tariff rates are 1 there, not the factor or a load.
- RV reads its death rates through the factory alone, as the first reader of a generational
  table: on every shipped point ``birth_year()`` is the issue year less the issue age and
  ``birth_year() + age(t)`` the calendar year; ``mort_rate(t)`` is ``min(1, 1.15 *
  q(dav2004r_proxy, sex, age(t), birth_year))`` through the core's cells, and 1 where the
  table rate is 1; the tariff rate ``mort_rate_tariff(t)`` is the blend of 45 % men and 55 %
  women at the same age and birth year, the same for a man and a woman, and stands in the
  column ``mort_rate_guar`` and in ``charge_risk_pp``; ``omega_age()`` is the table's end
  age 121 and the frame runs to it; the rates are the values package's to six digits. A
  scratch copy whose anchor is a woman has the man's risk charge, account and annuity per
  policy and her own decrements. Its
  folder holds no mortality file or column, its tariff-type file no ``mort_base_year`` and
  no ``omega_age``, its ``Data`` no Reference ``mort_file``, its ``Projection`` no
  ``mort_rate_at_age``, ``improve_rate``, ``mort_rate_base`` or ``mort_rate_tariff`` of its
  own and no read of the factory besides the core's hooks.
- KLV reads its death rates through the factory alone, the fourth switched product and the
  third reader of ``dav2008t_proxy``, which is its former file's law in full precision. The
  tariff rate: on every shipped point ``mort_rate_tariff_at_age(x)`` is the core's cell,
  ``0.5 q_M + 0.5 q_F`` of the table, the same whatever the point's sex, and the premium of
  points 1 and 7, which differ in sex, is one. The best estimate: ``mort_rate(t)`` is
  ``q(dav2008t_proxy, own sex, age(t)) * 0.75``, and on a scratch copy whose table closes at
  the last age a point attains it is 1 there, as the tariff rate is. Against the file: at
  ages 0 to 119 for both sexes the table rate differs from ``mort_rate_1st`` of the file the
  switch deleted, read from git at the commit before, by at most 6.1e-12 below the cap, and
  the two are 1 at the same ages. The results: the baseline after the switch has the shape
  and keys of the one before and every value within the tolerance of a within-rounding
  change. Its folder holds no mortality file or column, its ``Data`` no Reference
  ``mort_file``, its ``Projection`` no ``mort_rate_tariff_at_age`` or ``mort_rate_at_age`` of
  its own and no read of the factory besides the core's hooks.
- FRV reads its death rates through the factory alone, the fifth switched product and the
  fourth reader of ``dav2008t_proxy``. The tariff rate: on every shipped point
  ``mort_rate_tariff(t)`` is the core's cell, ``0.5 q_M + 0.5 q_F`` of the table at the
  attained age, the same whatever the point's sex, the values package's "Tariff new" to six
  digits. The best estimate: ``mort_rate(t)`` is ``q(dav2008t_proxy, own sex, age(t)) *
  0.75`` through the core's ``mort_rate_base``, the package's "BE new". The monthly split is
  FRV's own and linear as before the switch: ``mort_rate_tariff_mth(t)`` and
  ``mort_rate_mth(t)`` are the annual rates divided by 12. On a scratch copy whose table
  closes at the last age a point attains the annual best estimate and the annual tariff rate
  are 1 there, not 0.75 of the table rate. On a scratch copy whose anchor is a woman the
  *Risikobeitrag* per policy is the man's in every month and her decrements are her own; the
  *Risikoergebnis* is no fixed share of the *Risikobeitrag*, 14.19 % of it for the man and
  35.81 % for the woman, where it was a quarter. Its folder holds no mortality file or column,
  its ``Data`` no Reference ``mort_file`` and no ``mort_table_index``, its ``Projection`` no
  ``mort_rate_tariff_at_age`` or ``mort_rate_base`` of its own and no read of the factory
  besides the core's hooks.
- RLV reads its death rates through the factory alone, the sixth switched product and the
  first whose table depends on the life: ``mort_table_smoker`` maps the smoker status ``N``
  to the table of ``mort_nr_table`` and ``R`` to that of ``mort_r_table``, any other code
  raises, and the second life reads the table of ``smoker2()``. The tariff rate: the rating
  factor alone on the 50/50 blend of the life's table, no 2.25, the same for points that
  differ in sex alone. Two lives: the first-death rule ``q_A + q_B - q_A q_B`` on the blends
  and on the own-sex rates, before any factor. The best estimate: ``0.75 * rating_factor *
  Q * sel_lapse_factor(t)``, capped at 1, and on a scratch copy whose table closes at an
  attained age 1 there, for one life and for two; the rates are the values package's to six
  digits. The declaration: ``beitragsverrechnung_rate`` stands on the margin share ``1 -
  mort_be_factor`` = 0.25. Its folder holds no mortality file, its model points no column
  ``mort_table_id``, its tariff-type file no ``mort_load_first``, its ``Data`` no Reference
  ``mort_file`` and no ``mort_table_index`` of its own, its ``Projection`` no cell
  ``mort_table_id`` and one read of the factory, through ``q``.
- Basis reads its best estimate through the factory alone, the seventh switched product, the
  second reader of ``dav2004r_proxy`` and the first that forms no tariff rate from a table:
  on every shipped point ``mort_rate(t)`` is ``min(1, 1.15 * q(dav2004r_proxy, sex, age(t),
  birth_year))`` through the core's cells, none overridden but the factor, and a woman's
  table rate is 0.6 of a man's at equal age and birth year; the package's sixteen rate rows
  to six digits. ``birth_year()`` is the issue year less the issue age, 1969 on the in-force
  points 6 and 14, and ``birth_year() + age(t)`` the calendar year on every point.
  ``omega_age()`` is the table's end age 121 and the frame runs to it, ``proj_len_y() = 121 -
  age(0)``, one year less than before the switch; at age 120 the best estimate is exactly 1,
  the certainty falls in the anniversary month and ``pols_if(proj_len())`` is 0, and age 121
  raises. A scratch copy whose anchor is a woman has the man's annuity per annuitant and her
  own decrements. Its folder holds no mortality file or column, its tariff-type file no
  ``mort_base_year`` and no ``unisex_mix_male``, its ``Data`` no Reference ``mort_file`` and no
  ``mort_table_index`` of its own, its ``Projection`` no mortality cell of its own but the
  factor and no read of the factory besides the core's hooks.
- Riester reads its death rates through the factory alone, the eighth switched product and the
  first whose two roles sit on different kinds of table. Accumulation: on every shipped point
  ``mort_rate(t)`` is ``min(1, 0.75 * q(dav2008t_proxy, sex, age(t)))`` through the core's
  ``mort_rate_at_age`` and ``mort_rate_base`` on its own ``mort_rate_table``, and the period
  table is never read with a birth year; a man and a woman of equal age differ. Payout:
  ``mort_rate(t)`` is ``min(1, 1.15 * q(dav2004r_proxy, sex, age(t), birth_year))`` through
  its hook ``annuity_mort_rate``, 1 where the table rate is 1. The package's twenty rate rows
  to six digits. ``ann_factor()`` is the annuity-due factor on the blend of 45 % men and 55 %
  women of ``dav2004r_proxy`` at the cohort, from the age at conversion to 120, less 11/24,
  the same for a man and a woman of equal age and birth year, 24.78315099 on the anchor, and
  the guaranteed *Rentenfaktor* binds on every point. ``omega_age()`` is the end age 121 of
  the annuitant table, ``proj_len_y() = 121 - age(0)``, ten years more than before the
  switch; at age 120 the rate is exactly 1, the certainty falls in the anniversary month,
  ``pols_if(proj_len())`` is 0, and age 121 raises in both tables. ``birth_year()`` is the
  issue year less the issue age, and ``birth_year() + age(t)`` the calendar year on every
  point. Its folder holds no mortality file or column, its tariff-type file no
  ``mort_base_year``, its ``Data`` no mortality Reference or cell of its own, its
  ``Projection`` no mortality cell of its own but the factor, the phase switch, the payout
  hook and the read of the main role, and no read of the factory but those and the end age.
- Sofort reads its death rates through the factory alone, the ninth switched product and the
  fourth reader of ``dav2004r_proxy``, with two lives on one table: its hook
  ``mort_rate_gen`` is ``q(dav2004r_proxy, sex, x, birth_year)`` for each life, the unisex
  ``U`` the core's blend. The package's ten rate rows to six digits, the best estimate also
  in the package's form ``1.2 * q_base * (1 - 0.8 trend) ** (g + x - 2005)``. The best
  estimate: on every shipped point and both lives ``mort_rate(t, life)`` is ``min(1, 1.2 * T
  * q)``, 1 where the table rate is 1, with the trend term ``T = ((1 - 0.8 tr) / (1 - tr))
  ** (g + x - 2005)``, which at 65, 80 and 95 on the anchor is above 1, the best estimate
  improving more slowly than the table, and 1 from 120. The tariff rate is the blend of 45 %
  men and 55 % women at the life's age and birth year; a scratch copy whose anchor is a
  woman has the man's tariff rate, annuity factor and guaranteed annuity and her own
  decrements. On the joint-life points 4 and 5 the older life passes 120: from the end age
  its best-estimate and tariff rates are 1, its survival 0, and no age above 120 reaches
  the factory, where age 121 raises. A second life without a survivor's annuity reads 0.
  ``omega_age()`` is the table's end age 121 and every frame is as long as before the
  switch. Its folder holds no mortality file or column, its tariff-type file no
  ``mort_base_year`` and no ``omega_age``, its ``Data`` no mortality Reference or cell of its
  own, its ``Projection`` no mortality cell of its own but the factor, the trend term, the
  hook and the per-life rates, and no read of the factory but ``q`` in the hook and the
  trend and base year in the trend term.
- On a scratch copy of Index that chooses a fixture table in its tariff-type file
  (``switched_copy``), the hooks deliver the table's rate on the point's own sex,
  its unisex blend and its end age, ``mort_rate`` stands on them, and the copy runs through
  both engines of the runner with the same results, the factory called without a birth
  year; with a ``birth_year`` cell and the generational fixture table the hooks pass the
  birth year on, and without the cell the generational table raises.
- A table rate of 1 passes through the core's derivation as 1 (AD-12): on a copy whose
  fixture table closes at the last age a point attains, with Index' best-estimate factor and a
  trend term below 1 and a loading above 1, ``mort_rate`` and ``mort_rate_tariff`` are 1 at the end age minus
  one and the factor and the loading times the table rate the year before.

The usage scan ``core/param_usage.py`` (``docs/core.md``, "The usage check and the view"):

- Every shipped product is clean and holds the factory's tables; Index holds its choice and
  reads the table's items through ``mort_table_name``, as KLV, RV, FRV and Basis do, BU its two
  choices, the items of the second read through ``mort_rate_dis_at_age``, RLV its two, the
  items of both read through ``mort_table_smoker``, Riester its two, the items of the second
  read through ``annuity_mort_rate`` and ``omega_age``, Sofort its one, its items read
  through ``mort_table_name`` as RV's; Pflege holds no choice and reads no tables item, and no
  table is unchosen across the ten.
- On a scratch copy of Index that chooses a fixture table (``choosing_copy``) the scan holds
  the factory's ``items()`` and the choice, counts the chosen table's items as read by the
  cells reading the choice item and no other table's item, and reports nothing; a copy with
  the fixture tables, a table read of its own and no choice (``unswitched_copy``) reads no
  tables item, and neither does one whose choice item no cell reads.
- The scan reports a chosen name the factory lacks, naming the item, its file and the name,
  in the tariff-type and the tariff file; an item of the tables layer that is in no table's
  items; an item a chosen table names that the layer lacks; a product-defined
  ``param_tables_path``; and a cell referencing ``param_tables_path``.
- The scan reports an item of a table that stands in another layer than the tables layer,
  and an item named ``<role>_table`` in the core or the tables file.
- The scan reports a reachable cell that reads an item of the tables layer itself, by a
  literal call or a ``param_indirect()`` declaration.
- ``unchosen_tables`` names, sorted, the tables no scanned model chooses; a table whose
  choice item no cell reads is not chosen.
"""
from __future__ import annotations

import ast
import builtins
import csv
import hashlib
import importlib
import importlib.util
import io
import subprocess
from pathlib import Path

import modelx as mx
import pytest

from test_core import (CORE_MODEL, MODELS, PRODUCTS_DIR, ROOT, _add_params, _formula_cells,
                       _loader_error, param_usage, product_copy)

RLV = "risikolebensversicherung"
SOFORT = "sofortrente"
TABLES_FILE = "param_tables.csv"


# The tables the factory holds, {table: (law cell, trend cell or None, parameters)}, the rows
# of the table parameter file, {item: (value as written, basis)}, each a row of the accepted
# values package, and the products that have switched to the factory, {product: its choices}.
SHIPPED_TABLES = {
    "dav2008t_proxy": ("makeham", None, ("m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
                                         "first_age", "end_age")),
    "dav1997ti_proxy": ("makeham", None, ("m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
                                          "sel_1", "sel_2", "sel_3", "sel_4", "sel_5", "sel_6",
                                          "first_age", "end_age")),
    "dav2004r_proxy": ("makeham", "trend_linear", (
        "m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
        "trend_start", "trend_start_age", "trend_mid", "trend_mid_age", "trend_end_age",
        "base_year", "first_age", "end_age")),
    "dav2008t_nr_proxy": ("makeham", None, ("m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
                                            "first_age", "end_age")),
    "dav2008t_r_proxy": ("makeham", None, ("m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
                                           "first_age", "end_age")),
}
SHIPPED_ITEMS = {table: tuple(f"{table}_{name}" for name in names)
                 for table, (_law, _trend, names) in SHIPPED_TABLES.items()}
SHIPPED_ROWS = {
    "dav2008t_proxy_m_a": ("0.00022", "Setzung"),
    "dav2008t_proxy_m_b": ("2.8820182383e-05", "Setzung"),
    "dav2008t_proxy_m_c": ("1.1", "Setzung"),
    "dav2008t_proxy_f_a": ("0.00016", "Setzung"),
    "dav2008t_proxy_f_b": ("2.1653029589e-05", "Setzung"),
    "dav2008t_proxy_f_c": ("1.1", "Setzung"),
    "dav2008t_proxy_first_age": ("0", "Setzung"),
    "dav2008t_proxy_end_age": ("121", "Setzung"),
    "dav1997ti_proxy_m_a": ("0.0", "Setzung"),
    "dav1997ti_proxy_m_b": ("0.00011037881", "Setzung"),
    "dav1997ti_proxy_m_c": ("1.095", "Setzung"),
    "dav1997ti_proxy_f_a": ("0.0", "Setzung"),
    "dav1997ti_proxy_f_b": ("7.35858731e-05", "Setzung"),
    "dav1997ti_proxy_f_c": ("1.095", "Setzung"),
    "dav1997ti_proxy_sel_1": ("3.0", "Setzung"),
    "dav1997ti_proxy_sel_2": ("2.0", "Setzung"),
    "dav1997ti_proxy_sel_3": ("1.6", "Setzung"),
    "dav1997ti_proxy_sel_4": ("1.4", "Setzung"),
    "dav1997ti_proxy_sel_5": ("1.3", "Setzung"),
    "dav1997ti_proxy_sel_6": ("1.2", "Setzung"),
    "dav1997ti_proxy_first_age": ("18", "Setzung"),
    "dav1997ti_proxy_end_age": ("121", "Setzung"),
    "dav2004r_proxy_m_a": ("0.0", "Setzung"),
    "dav2004r_proxy_m_b": ("9.05933597e-06", "Setzung"),
    "dav2004r_proxy_m_c": ("1.11", "Setzung"),
    "dav2004r_proxy_f_a": ("0.0", "Setzung"),
    "dav2004r_proxy_f_b": ("5.43560158e-06", "Setzung"),
    "dav2004r_proxy_f_c": ("1.11", "Setzung"),
    "dav2004r_proxy_trend_start": ("0.025", "Setzung"),
    "dav2004r_proxy_trend_start_age": ("75", "Setzung"),
    "dav2004r_proxy_trend_mid": ("0.0125", "Setzung"),
    "dav2004r_proxy_trend_mid_age": ("90", "Setzung"),
    "dav2004r_proxy_trend_end_age": ("120", "Setzung"),
    "dav2004r_proxy_base_year": ("2005", "Setzung"),
    "dav2004r_proxy_first_age": ("0", "Setzung"),
    "dav2004r_proxy_end_age": ("121", "Setzung"),
    "dav2008t_nr_proxy_m_a": ("0.000176", "Setzung"),
    "dav2008t_nr_proxy_m_b": ("2.30561459064e-05", "Setzung"),
    "dav2008t_nr_proxy_m_c": ("1.1", "Setzung"),
    "dav2008t_nr_proxy_f_a": ("0.000128", "Setzung"),
    "dav2008t_nr_proxy_f_b": ("1.73224236712e-05", "Setzung"),
    "dav2008t_nr_proxy_f_c": ("1.1", "Setzung"),
    "dav2008t_nr_proxy_first_age": ("0", "Setzung"),
    "dav2008t_nr_proxy_end_age": ("121", "Setzung"),
    "dav2008t_r_proxy_m_a": ("0.0003872", "Setzung"),
    "dav2008t_r_proxy_m_b": ("5.07235209941e-05", "Setzung"),
    "dav2008t_r_proxy_m_c": ("1.1", "Setzung"),
    "dav2008t_r_proxy_f_a": ("0.0002816", "Setzung"),
    "dav2008t_r_proxy_f_b": ("3.81093320766e-05", "Setzung"),
    "dav2008t_r_proxy_f_c": ("1.1", "Setzung"),
    "dav2008t_r_proxy_first_age": ("0", "Setzung"),
    "dav2008t_r_proxy_end_age": ("121", "Setzung"),
}
SHIPPED_LAYER = {item: (int(text) if text.isdigit() else float(text))
                 for item, (text, _basis) in SHIPPED_ROWS.items()}
SHIPPED_PROVENANCE = {
    "dav2008t_proxy": "[std] proxy of DAV 2008 T, first order, not the table itself, whose"
                      " values are DAV property and are not shipped; ",
    "dav1997ti_proxy": "[std] proxy of DAV 1997 TI, mortality of disabled lives, select on"
                       " the claim year, not the table itself, which is not shipped; ",
    "dav2004r_proxy": "[std] proxy of DAV 2004 R, first order, generational, not the table"
                      " itself, whose values are DAV property and are not shipped; ",
    "dav2008t_nr_proxy": "[std] proxy of DAV 2008 T NR (non-smokers), first order, not the"
                         " table itself, whose values are DAV property and are not shipped; ",
    "dav2008t_r_proxy": "[std] proxy of DAV 2008 T R (smokers), first order, not the table"
                        " itself, whose values are DAV property and are not shipped; ",
}
# The products that have switched to the factory: {product: {choice item: table}}, and the
# cell that reads each choice item.
SWITCHED = {
    "berufsunfaehigkeit": {"mort_table": "dav2008t_proxy", "mort_dis_table": "dav1997ti_proxy"},
    "fondsgebundene_rentenversicherung": {"mort_table": "dav2008t_proxy"},
    "indexpolice": {"mort_table": "dav2008t_proxy"},
    "kapitallebensversicherung": {"mort_table": "dav2008t_proxy"},
    "basisrente": {"mort_table": "dav2004r_proxy"},
    "klassische_rentenversicherung": {"mort_table": "dav2004r_proxy"},
    "riester_rente": {"mort_table": "dav2008t_proxy", "annuity_mort_table": "dav2004r_proxy"},
    "risikolebensversicherung": {"mort_nr_table": "dav2008t_nr_proxy",
                                 "mort_r_table": "dav2008t_r_proxy"},
    "sofortrente": {"mort_table": "dav2004r_proxy"},
}
# Riester's second role is read by its payout hook and by its ``omega_age``, which names the
# role whose end age is its horizon.
CHOICE_READERS = {"mort_table": {"mort_table_name"}, "mort_dis_table": {"mort_rate_dis_at_age"},
                  "mort_nr_table": {"mort_table_smoker"}, "mort_r_table": {"mort_table_smoker"},
                  "annuity_mort_table": {"annuity_mort_rate", "omega_age"}}


def tables_file(folder: Path, product: str = RLV) -> Path:
    """The table parameter file of a scratch copy, a real file beside its core file."""
    path = folder / MODELS[product] / "CoreData" / TABLES_FILE
    assert path.is_file() and not path.is_symlink()
    return path


@pytest.fixture(scope="module")
def product_models():
    """Every product's modelx model, read once for this module and closed afterwards."""
    models = {}

    def read(product):
        if product not in models:
            models[product] = mx.read_model(PRODUCTS_DIR / product / MODELS[product],
                                            name=f"Tables_{MODELS[product]}")
        return models[product]

    yield read
    for model in models.values():
        model.close()


def test_the_shipped_tables_file_holds_the_rows_of_its_tables_and_no_other():
    path = CORE_MODEL / "Data" / TABLES_FILE
    text = path.read_text(encoding="utf-8")
    assert text.isascii()
    with path.open(encoding="utf-8", newline="") as handle:
        header, *rows = list(csv.reader(handle))
    assert header == ["item", "value", "basis", "provenance"]
    assert all(len(row) == 4 for row in rows)
    assert [row[0] for row in rows] == [item for table in SHIPPED_TABLES
                                        for item in SHIPPED_ITEMS[table]]
    assert {row[0]: (row[1], row[2]) for row in rows} == SHIPPED_ROWS
    for item, _value, _basis, provenance in rows:
        (table,) = [table for table in SHIPPED_TABLES if item in SHIPPED_ITEMS[table]]
        assert provenance.startswith(SHIPPED_PROVENANCE[table]), item
        assert len(provenance) > len(SHIPPED_PROVENANCE[table]), item
    assert len({row[3] for row in rows if not row[0].endswith(("_m_c", "_f_c"))}) == len(
        [row for row in rows if not row[0].endswith(("_m_c", "_f_c"))])


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_tables_layer_is_the_second_layer_and_holds_the_tables(product, product_models):
    data = product_models(product).Data
    assert data.param_tables_path() == data.model.path / "CoreData" / TABLES_FILE
    assert data.param_tables_path().is_file()
    assert list(data.param_paths()) == ["core", "tables", "tariff_type"]
    assert data.param_paths()["tables"] == data.param_tables_path()
    assert [(row[0], row[1], row[2]) for row in data.param_rows()["tables"]] == [
        (item, value, basis) for item, (value, basis) in SHIPPED_ROWS.items()]
    assert list(data.param_layers()) == ["core", "tables", "tariff_type"]
    layer = data.param_layers()["tables"]
    assert layer == SHIPPED_LAYER
    assert all(type(layer[item]) is type(value) for item, value in SHIPPED_LAYER.items())


def test_param_without_the_tables_file_raises(tmp_path):
    folder = product_copy(tmp_path, RLV)
    path = tables_file(folder)
    path.unlink()
    message = _loader_error(folder / MODELS[RLV], "NoTablesProbe")
    assert f"parameter file {path} cannot be read" in message


def test_param_reads_an_item_of_the_tables_layer(tmp_path):
    folder = product_copy(tmp_path, RLV)
    shipped = (CORE_MODEL / "Data" / TABLES_FILE).read_text(encoding="utf-8")
    _add_params(tables_file(folder), {"fixture_end_age": "121", "fixture_m_a": "0.0005"})
    copy = mx.read_model(folder / MODELS[RLV], name="TablesItemProbe")
    try:
        data = copy.Data
        assert data.param_layers()["tables"] == SHIPPED_LAYER | {"fixture_end_age": 121,
                                                                 "fixture_m_a": 0.0005}
        assert data.param("fixture_end_age") == 121
        assert type(data.param("fixture_end_age")) is int
        assert data.param("fixture_m_a") == 0.0005
        assert data.param("check_tol") == 1e-08
    finally:
        copy.close()
    assert (CORE_MODEL / "Data" / TABLES_FILE).read_text(encoding="utf-8") == shipped


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_a_table_choice_is_loaded_as_a_name(tmp_path, file):
    folder = product_copy(tmp_path, RLV)
    _add_params(folder / file, {"mort_table": "dav_x_proxy", "probe2_table": " t2 "})
    copy = mx.read_model(folder / MODELS[RLV], name="ChoiceProbe")
    try:
        data = copy.Data
        assert data.param("mort_table") == "dav_x_proxy"
        assert type(data.param("mort_table")) is str
        assert data.param("probe2_table") == "t2"
        layer = "tariff" if file == "param_tariff.csv" else "tariff_type"
        assert data.param_layers()[layer]["mort_table"] == "dav_x_proxy"
    finally:
        copy.close()


@pytest.mark.parametrize(("text", "name"), [
    ("3", "IntChoiceProbe"),
    ("0.5", "FloatChoiceProbe"),
    ("1e3", "ExponentChoiceProbe"),
    ("Dav_x_proxy", "UpperChoiceProbe"),
    ("dav_X_proxy", "InnerUpperChoiceProbe"),
    ("_dav_x", "UnderscoreFirstChoiceProbe"),
    ("dav-x", "HyphenChoiceProbe"),
    ("dav x", "SpaceChoiceProbe"),
    ("däv_x", "UmlautChoiceProbe"),
])
def test_a_table_choice_that_is_no_name_raises(tmp_path, text, name):
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    _add_params(path, {"mort_table": text})
    message = _loader_error(folder / MODELS[RLV], name)
    assert f"parameter 'mort_table' has the value {text!r} in {path}, no table name" in message


def test_an_empty_table_choice_has_no_value(tmp_path):
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    _add_params(path, {"mort_table": ""})
    message = _loader_error(folder / MODELS[RLV], "EmptyChoiceProbe")
    assert f"parameter 'mort_table' has no value in {path}" in message


@pytest.mark.parametrize("item", ["mort_table_name", "table", "probe_tables"])
def test_a_name_is_no_number_for_any_other_item(tmp_path, item):
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    _add_params(path, {item: "dav_x_proxy"})
    message = _loader_error(folder / MODELS[RLV], "NameValueProbe")
    assert f"parameter {item!r} has the value 'dav_x_proxy' in {path}, no number" in message


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_param_rejects_a_tables_item_in_a_product_file(tmp_path, file):
    folder = product_copy(tmp_path, RLV)
    tables = tables_file(folder)
    _add_params(tables, {"fixture_end_age": "121"})
    _add_params(folder / file, {"fixture_end_age": "110"})
    message = _loader_error(folder / MODELS[RLV], "TablesLockProbe")
    assert "'fixture_end_age' is a tables item of" in message
    assert str(tables) in message and str(folder / file) in message


def test_param_rejects_a_core_item_in_the_tables_file(tmp_path):
    folder = product_copy(tmp_path, RLV)
    tables = tables_file(folder)
    _add_params(tables, {"check_tol": "1e-9"})
    message = _loader_error(folder / MODELS[RLV], "CoreInTablesProbe")
    assert "'check_tol' is a core item of" in message
    assert str(tables.with_name("param_core.csv")) in message and str(tables) in message


def test_param_rejects_an_item_twice_in_the_tables_file(tmp_path):
    folder = product_copy(tmp_path, RLV)
    tables = tables_file(folder)
    _add_params(tables, {"fixture_end_age": "121"})
    _add_params(tables, {"fixture_end_age": "121"})
    message = _loader_error(folder / MODELS[RLV], "TablesTwiceProbe")
    assert f"'fixture_end_age' stands twice in {tables}" in message


# --------------------------------------------------------------------------- the space

TABLES_SOURCE = CORE_MODEL / "Tables" / "__init__.py"
TABLES_CELLS = ["definitions", "definition", "items", "parameter", "first_age", "end_age",
                "base_year", "select_factors", "base_rate", "trend", "makeham",
                "trend_linear", "q"]


def raised_line(call) -> str:
    """The line ``<Error>: <message>`` of the error ``call()`` raises.

    modelx wraps a formula's error in a ``FormulaError`` whose text also holds the formula
    source; only the last line before ``Formula traceback:`` is the raised error. The
    exported model raises the plain exception.
    """
    with pytest.raises(Exception) as raised:
        call()
    if type(raised.value).__name__ != "FormulaError":
        return f"{type(raised.value).__name__}: {raised.value}"
    head = str(raised.value).split("Formula traceback:", 1)[0]
    return [text for text in head.splitlines() if text.strip()][-1]


def test_the_core_holds_the_tables_space_without_a_parameter():
    model = mx.read_model(CORE_MODEL, name="TablesCoreProbe")
    try:
        assert sorted(model.spaces) == ["Data", "Projection", "Tables"]
        tables = model.Tables
        assert tables.formula is None
        assert list(tables.cells) == TABLES_CELLS
        assert tables.data is model.Data
        assert tables.bases == []
        assert list(tables.definitions()) == list(SHIPPED_TABLES)
        for table, (law_name, trend_name, names) in SHIPPED_TABLES.items():
            law_cell, trend_cell, held = tables.definitions()[table]
            assert f".Tables.{law_name}(table, sex, x)" in repr(law_cell)
            if trend_name is None:
                assert trend_cell is None
            else:
                assert f".Tables.{trend_name}(table, sex, x)" in repr(trend_cell)
            assert held == names
        # one generational table, one select table
        assert [table for table, (_law, trend_name, _names) in SHIPPED_TABLES.items()
                if trend_name is not None] == [DAV2004R]
        assert tables.items() == SHIPPED_ITEMS
    finally:
        model.close()


@pytest.mark.parametrize("product", sorted(MODELS))
def test_a_product_holds_the_factory_as_a_symlink_and_inherits_it_nowhere(product,
                                                                          product_models):
    folder = PRODUCTS_DIR / product / MODELS[product]
    link = folder / "CoreTables"
    assert link.is_symlink()
    assert link.readlink() == Path("../../../core/Core/Tables")
    assert link.resolve() == (CORE_MODEL / "Tables").resolve()
    spaces = ast.literal_eval(
        (folder / "__init__.py").read_text(encoding="utf-8").split("_spaces = ", 1)[1])
    assert spaces == ["CoreData", "CoreProjection", "CoreTables", "Data", "Projection"]

    model = product_models(product)
    tables = model.CoreTables
    assert list(model.spaces) == spaces
    for space in model.spaces.values():
        assert tables not in space.bases, space.name
    assert tables.bases == []
    assert tables.formula is None
    assert model.Projection.tables is tables
    assert tables.data is model.Data
    # the core's cells and no other, each with the core's source: no product defines one
    assert list(tables.cells) == TABLES_CELLS
    source = TABLES_SOURCE.read_text(encoding="utf-8")
    for name, cell in tables.cells.items():
        assert cell._is_defined()
        assert cell.formula.source in source, name


@pytest.mark.parametrize("product", sorted(MODELS))
def test_every_shipped_product_holds_the_factorys_tables_and_no_other(product, product_models):
    """Also a product no cell of which reads the table: the factory is model-wide."""
    tables = product_models(product).CoreTables
    assert list(tables.definitions()) == list(SHIPPED_TABLES)
    assert tables.items() == SHIPPED_ITEMS
    assert tables.q("dav2008t_proxy", "M", 40) == makeham_rate("M", 40)
    assert tables.end_age("dav2008t_proxy") == 121 and tables.first_age("dav2008t_proxy") == 0
    line = raised_line(lambda: tables.q("nosuch", "M", 40))
    assert line == "ValueError: table 'nosuch' is not defined"
    assert raised_line(lambda: tables.end_age("nosuch")).startswith("KeyError")


DAV2008T = "dav2008t_proxy"


def makeham_rate(sex: str, x: int, table: str = DAV2008T) -> float:
    """The rate of the law ``makeham`` from the rows of a shipped table, in the float
    operations of the law's cell: ``a + b * c ** x``."""
    a, b, c = (SHIPPED_LAYER[f"{table}_{sex.lower()}_{name}"] for name in "abc")
    return a + b * c ** x


@pytest.fixture(scope="module")
def shipped_tables(product_models):
    """The factory as a shipped product holds it, read off RLV: every product holds every
    table, whichever it chooses."""
    return product_models(RLV).CoreTables


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2008t_proxy_gives_its_makeham_rate_capped_at_1(shipped_tables, sex):
    assert SHIPPED_LAYER["dav2008t_proxy_m_a"] == 0.00022
    assert SHIPPED_LAYER["dav2008t_proxy_m_b"] == 2.8820182383e-05
    assert SHIPPED_LAYER["dav2008t_proxy_f_a"] == 0.00016
    assert SHIPPED_LAYER["dav2008t_proxy_f_b"] == 2.1653029589e-05
    assert SHIPPED_LAYER["dav2008t_proxy_m_c"] == 1.1 == SHIPPED_LAYER["dav2008t_proxy_f_c"]
    a, b = {"M": (0.00022, 2.8820182383e-05), "F": (0.00016, 2.1653029589e-05)}[sex]
    capped = []
    for x in range(0, 120):
        rate = shipped_tables.q(DAV2008T, sex, x)
        assert type(rate) is float
        assert rate == min(1.0, a + b * 1.1 ** x) == min(1.0, makeham_rate(sex, x)), x
        assert shipped_tables.base_rate(DAV2008T, sex, x) == a + b * 1.1 ** x, x
        assert shipped_tables.makeham(DAV2008T, sex, x) == a + b * 1.1 ** x, x
        if a + b * 1.1 ** x > 1.0:
            capped.append(x)
    # the cap binds from 110 for a man and 113 for a woman, below it the rate is the law's
    assert capped == list(range({"M": 110, "F": 113}[sex], 120))
    assert shipped_tables.q(DAV2008T, sex, capped[0]) == 1.0
    assert shipped_tables.q(DAV2008T, sex, capped[0] - 1) < 1.0
    assert shipped_tables.q(DAV2008T, sex, 40) != round(makeham_rate(sex, 40), 10)
    assert raised_line(lambda: shipped_tables.trend(DAV2008T, sex, 40)) == (
        "ValueError: table 'dav2008t_proxy': a period table has no trend")
    assert shipped_tables.select_factors(DAV2008T) == ()


# The values package's "New table" figures of dav2008t_proxy, six significant digits.
PACKAGE_RATES = {
    ("M", 30): 0.000722895, ("M", 40): 0.00152438, ("M", 50): 0.00360323, ("M", 65): 0.0143526,
    ("F", 30): 0.000537832, ("F", 40): 0.00114, ("F", 50): 0.00270187, ("F", 65): 0.010778,
}


@pytest.mark.parametrize(("sex", "x"), sorted(PACKAGE_RATES))
def test_dav2008t_proxy_gives_the_rates_of_the_values_package(shipped_tables, sex, x):
    rate = shipped_tables.q(DAV2008T, sex, x)
    assert float(f"{rate:.6g}") == PACKAGE_RATES[(sex, x)]
    # the anchor of the table: q(M, 37) = 0.0012, and women three years of age behind
    assert shipped_tables.q(DAV2008T, "M", 37) == pytest.approx(0.0012, rel=1e-9)
    assert shipped_tables.q(DAV2008T, "F", 40) - 0.00016 == pytest.approx(
        shipped_tables.q(DAV2008T, "M", 37) - 0.00022, rel=1e-9)


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2008t_proxy_closes_at_120_and_raises_outside_its_ages(shipped_tables, sex):
    rate = shipped_tables.q(DAV2008T, sex, 120)
    assert rate == 1.0 and type(rate) is float
    assert shipped_tables.q(DAV2008T, sex, 0) == makeham_rate(sex, 0)
    for x in (121, -1, 150):
        for cell in (shipped_tables.q, shipped_tables.base_rate):
            line = raised_line(lambda: cell(DAV2008T, sex, x))
            assert line == (f"ValueError: table 'dav2008t_proxy': x {x!r} is outside its ages"
                            f" 0 to 120"), line


def test_dav2008t_proxy_is_a_period_table_without_selection(shipped_tables):
    for x in (40, 120):
        line = raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, 1960))
        assert line == ("ValueError: table 'dav2008t_proxy': birth_year 1960 is given, the"
                        " table is a period table")
        assert line == raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, birth_year=1960))
        line = raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, None, 1))
        assert line == ("ValueError: table 'dav2008t_proxy': duration 1 is given, the table"
                        " has no selection")
        assert line == raised_line(lambda: shipped_tables.q(DAV2008T, "M", x, duration=1))


DAV1997TI = "dav1997ti_proxy"
TI_SELECT = (3.0, 2.0, 1.6, 1.4, 1.3, 1.2)


def ti_rate(sex: str, x: int, duration: int) -> float:
    """The rate of ``dav1997ti_proxy`` from its rows, in the float operations of the law's
    cell and of ``q``: ``(a + b * c ** x) * sel``, the last factor for every later
    duration, capped at 1."""
    factor = SHIPPED_LAYER[f"{DAV1997TI}_sel_{min(duration, len(TI_SELECT))}"]
    return min(1.0, makeham_rate(sex, x, DAV1997TI) * factor)


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav1997ti_proxy_gives_its_rate_times_the_select_factor(shipped_tables, sex):
    assert SHIPPED_LAYER["dav1997ti_proxy_m_a"] == 0.0 == SHIPPED_LAYER["dav1997ti_proxy_f_a"]
    assert SHIPPED_LAYER["dav1997ti_proxy_m_b"] == 0.00011037881
    assert SHIPPED_LAYER["dav1997ti_proxy_f_b"] == 7.35858731e-05
    assert SHIPPED_LAYER["dav1997ti_proxy_m_c"] == 1.095 == SHIPPED_LAYER["dav1997ti_proxy_f_c"]
    assert shipped_tables.select_factors(DAV1997TI) == TI_SELECT
    assert tuple(SHIPPED_LAYER[f"dav1997ti_proxy_sel_{d}"] for d in range(1, 7)) == TI_SELECT
    assert shipped_tables.first_age(DAV1997TI) == 18 and shipped_tables.end_age(DAV1997TI) == 121
    b = {"M": 0.00011037881, "F": 7.35858731e-05}[sex]
    capped = set()
    for x in range(18, 120):
        # the law's own rate: a is 0, so Makeham's law is Gompertz' here
        assert shipped_tables.base_rate(DAV1997TI, sex, x) == b * 1.095 ** x, x
        for duration, factor in enumerate(TI_SELECT, start=1):
            rate = shipped_tables.q(DAV1997TI, sex, x, duration=duration)
            assert type(rate) is float
            assert rate == min(1.0, b * 1.095 ** x * factor) == ti_rate(sex, x, duration)
            assert rate == shipped_tables.q(DAV1997TI, sex, x, None, duration)
            if b * 1.095 ** x * factor > 1.0:
                capped.add(x)
    # the cap binds at the oldest ages only, far above every age a claim is paid at
    assert capped and min(capped) > 85
    assert shipped_tables.q(DAV1997TI, sex, 40, duration=1) != round(ti_rate(sex, 40, 1), 10)
    assert raised_line(lambda: shipped_tables.trend(DAV1997TI, sex, 40)) == (
        "ValueError: table 'dav1997ti_proxy': a period table has no trend")
    # the split by sex: men at 1.2 and women at 0.8 of one level, at every age
    assert shipped_tables.q(DAV1997TI, "M", 40, duration=6) / shipped_tables.q(
        DAV1997TI, "F", 40, duration=6) == pytest.approx(1.5, rel=1e-8)


# The values package's "New table" figures of dav1997ti_proxy by (sex, age, claim year), six
# significant digits.
TI_PACKAGE_RATES = {
    ("M", 30, 1): 0.00504, ("M", 30, 3): 0.002688, ("M", 30, 6): 0.002016,
    ("M", 40, 1): 0.0124903, ("M", 40, 2): 0.00832684, ("M", 40, 3): 0.00666148,
    ("M", 40, 4): 0.00582879, ("M", 40, 5): 0.00541245, ("M", 40, 6): 0.00499611,
    ("M", 50, 1): 0.0309537, ("M", 50, 3): 0.0165087, ("M", 50, 6): 0.0123815,
    ("M", 65, 1): 0.12076, ("M", 65, 3): 0.0644056, ("M", 65, 6): 0.0483042,
    ("M", 18, 1): 0.00169614,
    ("F", 30, 1): 0.00336, ("F", 30, 3): 0.001792, ("F", 30, 6): 0.001344,
    ("F", 40, 1): 0.00832684, ("F", 40, 3): 0.00444098, ("F", 40, 6): 0.00333074,
    ("F", 50, 1): 0.0206358, ("F", 50, 3): 0.0110058, ("F", 50, 6): 0.00825433,
    ("F", 65, 1): 0.080507, ("F", 65, 3): 0.042937, ("F", 65, 6): 0.0322028,
}


@pytest.mark.parametrize(("sex", "x", "duration"), sorted(TI_PACKAGE_RATES))
def test_dav1997ti_proxy_gives_the_rates_of_the_values_package(shipped_tables, sex, x, duration):
    rate = shipped_tables.q(DAV1997TI, sex, x, duration=duration)
    assert float(f"{rate:.6g}") == TI_PACKAGE_RATES[(sex, x, duration)]


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav1997ti_proxy_holds_its_last_factor_for_every_later_claim_year(shipped_tables, sex):
    for x in (18, 30, 40, 65, 119):
        sixth = shipped_tables.q(DAV1997TI, sex, x, duration=6)
        assert sixth == ti_rate(sex, x, 6)
        assert shipped_tables.q(DAV1997TI, sex, x, duration=5) > sixth or sixth == 1.0
        for duration in (7, 10, 11, 40):
            assert shipped_tables.q(DAV1997TI, sex, x, duration=duration) == sixth, duration
    for x in (40, 120):
        for duration, words in [(None, "duration is missing, the table is select"),
                                (0, "duration 0 is below 1"), (-1, "duration -1 is below 1")]:
            line = raised_line(lambda: shipped_tables.q(DAV1997TI, sex, x, None, duration))
            assert line == f"ValueError: table 'dav1997ti_proxy': {words}"
        line = raised_line(lambda: shipped_tables.q(DAV1997TI, sex, x, 1960, 1))
        assert line == ("ValueError: table 'dav1997ti_proxy': birth_year 1960 is given, the"
                        " table is a period table")


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav1997ti_proxy_closes_at_120_and_raises_outside_its_ages(shipped_tables, sex):
    for duration in (1, 6, 11):
        rate = shipped_tables.q(DAV1997TI, sex, 120, duration=duration)
        assert rate == 1.0 and type(rate) is float
    assert shipped_tables.q(DAV1997TI, sex, 18, duration=1) == ti_rate(sex, 18, 1) < 1.0
    for x in (17, 121, 0, -1):
        for call in (lambda: shipped_tables.q(DAV1997TI, sex, x, duration=1),
                     lambda: shipped_tables.base_rate(DAV1997TI, sex, x)):
            line = raised_line(call)
            assert line == (f"ValueError: table 'dav1997ti_proxy': x {x!r} is outside its ages"
                            f" 18 to 120"), line


DAV2004R = "dav2004r_proxy"


def linear_trend(x: int) -> float:
    """The trend of ``dav2004r_proxy`` at age ``x`` from its rows, in the float operations
    of the law ``trend_linear``."""
    start, start_age, mid, mid_age, stop_age = (
        SHIPPED_LAYER[f"{DAV2004R}_trend_{name}"]
        for name in ("start", "start_age", "mid", "mid_age", "end_age"))
    if x <= start_age:
        return start
    if x <= mid_age:
        return start + (mid - start) * (x - start_age) / (mid_age - start_age)
    if x < stop_age:
        return mid * (stop_age - x) / (stop_age - mid_age)
    return 0.0


def r_rate(sex: str, x: int, birth_year: int) -> float:
    """The rate of ``dav2004r_proxy`` from its rows, in the float operations of the law's
    cell and of ``q``: the base rate times ``(1 - trend) ** (birth_year + x - base_year)``,
    capped at 1, and 1 at the closing age."""
    if x == SHIPPED_LAYER[f"{DAV2004R}_end_age"] - 1:
        return 1.0
    years = birth_year + x - SHIPPED_LAYER[f"{DAV2004R}_base_year"]
    return min(1.0, makeham_rate(sex, x, DAV2004R) * (1.0 - linear_trend(x)) ** years)


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2004r_proxy_has_the_linear_trend_of_the_values_package(shipped_tables, sex):
    assert SHIPPED_LAYER["dav2004r_proxy_trend_start"] == 0.025
    assert SHIPPED_LAYER["dav2004r_proxy_trend_start_age"] == 75
    assert SHIPPED_LAYER["dav2004r_proxy_trend_mid"] == 0.0125
    assert SHIPPED_LAYER["dav2004r_proxy_trend_mid_age"] == 90
    assert SHIPPED_LAYER["dav2004r_proxy_trend_end_age"] == 120
    for x in range(0, 131):
        rate = shipped_tables.trend(DAV2004R, sex, x)
        assert type(rate) is float
        assert rate == shipped_tables.trend_linear(DAV2004R, sex, x) == linear_trend(x), x
        # the same for both sexes
        assert rate == shipped_tables.trend(DAV2004R, "M", x), x
        if x <= 75:
            assert rate == 0.025, x
        elif x <= 90:
            assert rate == pytest.approx(0.025 - 0.0125 * (x - 75) / 15, rel=1e-12), x
        elif x < 120:
            assert rate == pytest.approx(0.0125 * (120 - x) / 30, rel=1e-12), x
        else:
            assert rate == 0.0, x
    assert shipped_tables.trend(DAV2004R, sex, 90) == 0.0125
    assert shipped_tables.trend(DAV2004R, sex, 105) == 0.00625
    assert shipped_tables.trend(DAV2004R, sex, 119) > 0.0
    # falling from 75 on, never rising
    rates = [shipped_tables.trend(DAV2004R, sex, x) for x in range(0, 131)]
    assert all(later <= earlier for earlier, later in zip(rates, rates[1:]))
    assert all(later < earlier for earlier, later in zip(rates[75:120], rates[76:121]))
    # a period table has none, as built
    assert raised_line(lambda: shipped_tables.trend(DAV2008T, sex, 40)) == (
        "ValueError: table 'dav2008t_proxy': a period table has no trend")


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2004r_proxy_gives_its_rate_at_the_calendar_year_of_the_cohort(shipped_tables, sex):
    assert SHIPPED_LAYER["dav2004r_proxy_m_a"] == 0.0 == SHIPPED_LAYER["dav2004r_proxy_f_a"]
    assert SHIPPED_LAYER["dav2004r_proxy_m_b"] == 9.05933597e-06
    assert SHIPPED_LAYER["dav2004r_proxy_f_b"] == 5.43560158e-06
    assert SHIPPED_LAYER["dav2004r_proxy_m_c"] == 1.11 == SHIPPED_LAYER["dav2004r_proxy_f_c"]
    assert shipped_tables.base_year(DAV2004R) == 2005
    assert shipped_tables.first_age(DAV2004R) == 0 and shipped_tables.end_age(DAV2004R) == 121
    assert shipped_tables.select_factors(DAV2004R) == ()
    b = {"M": 9.05933597e-06, "F": 5.43560158e-06}[sex]
    capped = {}
    for birth_year in (1935, 1962, 1963, 1977, 1990, 2005, 2027):
        for x in range(0, 120):
            base = b * 1.11 ** x
            assert shipped_tables.base_rate(DAV2004R, sex, x) == base, x
            rate = shipped_tables.q(DAV2004R, sex, x, birth_year)
            assert type(rate) is float
            expected = min(1.0, base * (1.0 - linear_trend(x)) ** (birth_year + x - 2005))
            assert rate == expected == r_rate(sex, x, birth_year), (birth_year, x)
            assert rate == shipped_tables.q(DAV2004R, sex, x, birth_year=birth_year)
            if expected == 1.0:
                capped.setdefault(birth_year, []).append(x)
    # the cap binds at the oldest ages only: from 114 for a man and 118 for a woman of the
    # cohorts 1962 to 1990, a year earlier for the cohort 1935, a year later for men from 2005
    first = {"M": 114, "F": 118}[sex]
    for birth_year in (1962, 1963, 1977, 1990):
        assert capped[birth_year] == list(range(first, 120)), birth_year
    assert capped[1935] == list(range(first - 1, 120))
    assert capped[2027] == list(range({"M": 115, "F": 118}[sex], 120))
    # in the base year the rate is the law's: a cohort born in 2005 - x is x in 2005
    assert shipped_tables.q(DAV2004R, sex, 65, 1940) == b * 1.11 ** 65
    # a later cohort has the lower rate at the same age, an earlier calendar year the higher
    assert (shipped_tables.q(DAV2004R, sex, 65, 1990) < shipped_tables.q(DAV2004R, sex, 65, 1962)
            < shipped_tables.q(DAV2004R, sex, 65, 1940) < shipped_tables.q(DAV2004R, sex, 65, 1930))
    assert shipped_tables.q(DAV2004R, sex, 40, 1990) != round(r_rate(sex, 40, 1990), 12)


def test_dav2004r_proxy_is_anchored_at_65_with_women_at_six_tenths_of_men(shipped_tables):
    assert shipped_tables.base_rate(DAV2004R, "M", 65) == pytest.approx(0.008, rel=1e-8)
    assert shipped_tables.base_rate(DAV2004R, "F", 65) == pytest.approx(0.0048, rel=1e-8)
    for x in (0, 40, 65, 95, 113):
        for birth_year in (1962, 1990):
            assert shipped_tables.q(DAV2004R, "F", x, birth_year) == pytest.approx(
                0.6 * shipped_tables.q(DAV2004R, "M", x, birth_year), rel=1e-8)


# The values package's "New table" figures of dav2004r_proxy by (sex, age, birth year), six
# significant digits, with the best estimate at the factor 1.15 and, by (age, birth year),
# the tariff rate of the blend of 45 % men: the rows of RV.
R_PACKAGE_RATES = {
    ("M", 65, 1962): 0.00458344, ("M", 80, 1962): 0.0175643, ("M", 95, 1962): 0.106244,
    ("M", 105, 1962): 0.352527, ("M", 115, 1962): 1.0, ("M", 120, 1962): 1.0,
    ("F", 65, 1962): 0.00275006, ("F", 80, 1962): 0.0105386, ("F", 95, 1962): 0.0637461,
    ("F", 105, 1962): 0.211516, ("F", 115, 1962): 0.762392, ("F", 120, 1962): 1.0,
    ("M", 0, 1990): 1.32442e-05, ("M", 40, 1990): 0.000312702, ("M", 50, 1990): 0.000689298,
    ("M", 65, 1990): 0.0022559, ("M", 80, 1990): 0.00974126, ("M", 95, 1990): 0.0792445,
    ("F", 0, 1990): 7.94655e-06, ("F", 40, 1990): 0.000187621, ("F", 50, 1990): 0.000413579,
    ("F", 65, 1990): 0.00135354, ("F", 80, 1990): 0.00584475, ("F", 95, 1990): 0.0475467,
}
R_BE_PACKAGE_RATES = {
    ("M", 65, 1962): 0.00527096, ("M", 80, 1962): 0.0201989, ("M", 95, 1962): 0.12218,
    ("M", 105, 1962): 0.405406, ("M", 115, 1962): 1.0, ("M", 120, 1962): 1.0,
    ("F", 65, 1962): 0.00316257, ("F", 80, 1962): 0.0121193, ("F", 95, 1962): 0.0733081,
    ("F", 105, 1962): 0.243243, ("F", 115, 1962): 0.87675, ("F", 120, 1962): 1.0,
    ("M", 0, 1990): 1.52309e-05, ("M", 40, 1990): 0.000359608, ("M", 50, 1990): 0.000792692,
    ("M", 65, 1990): 0.00259429, ("M", 80, 1990): 0.0112024, ("M", 95, 1990): 0.0911312,
    ("F", 0, 1990): 9.13853e-06, ("F", 40, 1990): 0.000215765, ("F", 50, 1990): 0.000475615,
    ("F", 65, 1990): 0.00155657, ("F", 80, 1990): 0.00672147, ("F", 95, 1990): 0.0546787,
}
R_TARIFF_PACKAGE_RATES = {
    (65, 1962): 0.00357508, (80, 1962): 0.0137001, (95, 1962): 0.08287,
    (105, 1962): 0.274971, (115, 1962): 0.869315, (120, 1962): 1.0,
    (0, 1990): 1.03305e-05, (40, 1990): 0.000243908, (50, 1990): 0.000537652,
    (65, 1990): 0.00175961, (80, 1990): 0.00759818, (95, 1990): 0.0618107,
}


@pytest.mark.parametrize(("sex", "x", "birth_year"), sorted(R_PACKAGE_RATES))
def test_dav2004r_proxy_gives_the_rates_of_the_values_package(shipped_tables, sex, x,
                                                              birth_year):
    rate = shipped_tables.q(DAV2004R, sex, x, birth_year)
    assert float(f"{rate:.6g}") == R_PACKAGE_RATES[(sex, x, birth_year)]
    # the two factors of RV on it: the best estimate at 1.15, 1 where the table rate is 1,
    # and the blend of 45 % men
    best = 1.0 if rate >= 1.0 else min(1.0, rate * 1.15)
    assert float(f"{best:.6g}") == R_BE_PACKAGE_RATES[(sex, x, birth_year)]
    mixed = blend(shipped_tables.q(DAV2004R, "M", x, birth_year),
                  shipped_tables.q(DAV2004R, "F", x, birth_year), 0.45)
    assert float(f"{mixed:.6g}") == R_TARIFF_PACKAGE_RATES[(x, birth_year)]


@pytest.mark.parametrize("sex", ["M", "F"])
def test_dav2004r_proxy_closes_at_120_and_raises_outside_its_ages(shipped_tables, sex):
    for birth_year in (1900, 1962, 1990, 2027, 2100):
        rate = shipped_tables.q(DAV2004R, sex, 120, birth_year)
        assert rate == 1.0 and type(rate) is float
    assert shipped_tables.q(DAV2004R, sex, 0, 1990) == r_rate(sex, 0, 1990) < 1.0
    for x in (121, -1, 150):
        for call in (lambda: shipped_tables.q(DAV2004R, sex, x, 1962),
                     lambda: shipped_tables.base_rate(DAV2004R, sex, x)):
            line = raised_line(call)
            assert line == (f"ValueError: table 'dav2004r_proxy': x {x!r} is outside its ages"
                            f" 0 to 120"), line


def test_dav2004r_proxy_is_a_generational_table_without_selection(shipped_tables):
    for x in (40, 120):
        line = raised_line(lambda: shipped_tables.q(DAV2004R, "M", x))
        assert line == ("ValueError: table 'dav2004r_proxy': birth_year is missing, the table"
                        " is generational")
        assert line == raised_line(lambda: shipped_tables.q(DAV2004R, "M", x, None))
        line = raised_line(lambda: shipped_tables.q(DAV2004R, "M", x, 1962, 1))
        assert line == ("ValueError: table 'dav2004r_proxy': duration 1 is given, the table"
                        " has no selection")
        assert line == raised_line(
            lambda: shipped_tables.q(DAV2004R, "M", x, birth_year=1962, duration=1))


def test_the_factory_source_holds_no_number_but_0_and_1():
    cells = dict(_formula_cells(TABLES_SOURCE))
    assert list(cells) == TABLES_CELLS
    numbers = [(name, node.value) for name, cell in cells.items() for node in ast.walk(cell)
               if isinstance(node, ast.Constant) and type(node.value) in (int, float, complex)
               and (type(node.value) is complex or node.value not in (0, 1))]
    assert numbers == []


def test_only_q_says_mortality_in_the_factory():
    names = [name for name, _cell in _formula_cells(TABLES_SOURCE)]
    assert "q" in names
    assert [name for name in names if name != "q" and ("mort" in name or "q" in name)] == []


def _local_names(cell: ast.AST) -> set[str]:
    """The names a formula binds itself: its arguments and every name it stores."""
    names = {arg.arg for node in ast.walk(cell) if isinstance(node, ast.arguments)
             for arg in node.posonlyargs + node.args + node.kwonlyargs}
    names |= {node.id for node in ast.walk(cell)
              if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
    return names


def foreign_reads(path: Path) -> list[str]:
    """What the cells of a factory source read besides ``data.param``, each other, their own
    names and Python's builtins: ``<cell>: <name>`` each, sorted."""
    cells = dict(_formula_cells(path))
    found = set()
    for name, cell in cells.items():
        local = _local_names(cell)
        loader = set()
        for node in ast.walk(cell):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "data" and "data" not in local):
                if node.attr == "param":
                    loader.add(id(node.value))
                else:
                    found.add(f"{name}: data.{node.attr}")
                    loader.add(id(node.value))
        for node in ast.walk(cell):
            if not isinstance(node, ast.Name) or node.id in local or node.id in cells:
                continue
            if node.id == "data":
                if id(node) not in loader:
                    found.add(f"{name}: data")
            elif not hasattr(builtins, node.id):
                found.add(f"{name}: {node.id}")
    return sorted(found)


def test_the_factory_cells_read_only_data_param_and_each_other(tmp_path):
    assert foreign_reads(TABLES_SOURCE) == []
    probe = tmp_path / "probe.py"
    probe.write_text(
        "def a(table):\n    return data.param(table) + b()\n\n"
        "def b():\n    return data.model_point_table() + point_id + tables.q()\n\n"
        "def c(x):\n    y = [z for z in range(x)]\n    return len(y) + pd.NA\n\n"
        "def d():\n    return a(data)\n",
        encoding="utf-8")
    assert foreign_reads(probe) == ["b: data.model_point_table", "b: point_id", "b: tables",
                                    "c: pd", "d: data"]


# The fixture tables of a scratch copy: laws no shipped table has, numbers of no real table,
# and names that are none of the tables the factory holds or will hold.
FIXTURE_LAWS = '''
def law_fixture(table, sex, x):
    """A fixture law: ``a * b ** x`` on the rate, by sex."""
    return (parameter(table, sex.lower() + "_a")
            * parameter(table, sex.lower() + "_b") ** x)


def trend_fixture(table, sex, x):
    """A fixture trend law: one annual improvement rate by sex, the same at every age."""
    return parameter(table, sex.lower() + "_trend")

'''
FIXTURE_LAW_ITEMS = ("m_a", "m_b", "f_a", "f_b", "first_age", "end_age")
FIXTURE_DEFINITIONS = {
    "period_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS),
    "steep_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS),
    "gen_fixture": ("law_fixture", "trend_fixture",
                    FIXTURE_LAW_ITEMS + ("m_trend", "f_trend", "base_year")),
    "sel_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS + ("sel_2", "sel_1", "sel_3")),
    "broken_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS),
    "gap_fixture": ("law_fixture", "None", FIXTURE_LAW_ITEMS + ("sel_1", "sel_3")),
}
FIXTURE_LAW_VALUES = {"m_a": "0.0000201", "m_b": "1.09", "f_a": "0.0000107", "f_b": "1.092",
                      "first_age": "0", "end_age": "121"}
FIXTURE_VALUES = {
    "period_fixture": FIXTURE_LAW_VALUES,
    "steep_fixture": FIXTURE_LAW_VALUES | {"m_a": "0.01", "first_age": "20", "end_age": "111"},
    "gen_fixture": FIXTURE_LAW_VALUES | {"m_trend": "0.0125", "f_trend": "0.0175",
                                         "base_year": "1999"},
    "sel_fixture": FIXTURE_LAW_VALUES | {"sel_1": "3.5", "sel_2": "2.25", "sel_3": "1.5"},
    "broken_fixture": {name: value for name, value in FIXTURE_LAW_VALUES.items()
                       if name != "f_b"},
    "gap_fixture": FIXTURE_LAW_VALUES | {"sel_1": "3.5", "sel_3": "1.5"},
}
MARKER = "# " + "-" * 75 + "\n# References"
INDEX = "indexpolice"
BU = "berufsunfaehigkeit"
RV = "klassische_rentenversicherung"
KLV = "kapitallebensversicherung"
FRV = "fondsgebundene_rentenversicherung"


ALL_TABLES = list(SHIPPED_TABLES) + list(FIXTURE_DEFINITIONS)


def add_cells(path: Path, source: str) -> None:
    """Append the cells of ``source`` to a space file, before its References."""
    text = path.read_text(encoding="utf-8")
    assert text.count(MARKER) == 1
    path.write_text(text.replace(MARKER, source.lstrip("\n") + "\n" + MARKER),
                    encoding="utf-8")


def write_fixture_tables(model_dir: Path) -> None:
    """Write the fixture tables into a scratch copy, beside the shipped tables: their
    definitions, after the shipped ones, and laws into its ``CoreTables`` and their numbers
    into its ``param_tables.csv``."""
    path = model_dir / "CoreTables" / "__init__.py"
    assert path.is_file() and not (model_dir / "CoreTables").is_symlink()
    text = path.read_text(encoding="utf-8")
    (cell,) = [node for node in ast.parse(text).body
               if isinstance(node, ast.FunctionDef) and node.name == "definitions"]
    (held,) = [node.value for node in ast.walk(cell) if isinstance(node, ast.Return)]
    assert isinstance(held, ast.Dict) and held.end_lineno > held.lineno
    assert [key.value for key in held.keys] == list(SHIPPED_TABLES)
    lines = text.splitlines(keepends=True)
    assert lines[held.end_lineno - 1] == "    }\n"
    assert lines[held.end_lineno - 2].endswith(",\n")
    lines[held.end_lineno - 1:held.end_lineno - 1] = [
        f"        {table!r}: ({law}, {trend}, {names!r}),\n"
        for table, (law, trend, names) in FIXTURE_DEFINITIONS.items()]
    path.write_text("".join(lines), encoding="utf-8")
    add_cells(path, FIXTURE_LAWS)
    _add_params(model_dir / "CoreData" / TABLES_FILE,
                {f"{table}_{name}": value for table, values in FIXTURE_VALUES.items()
                 for name, value in values.items()})


def fixture_copy(tmp_path: Path, product: str = INDEX) -> Path:
    """A scratch copy of a product folder whose factory holds the fixture tables."""
    folder = product_copy(tmp_path, product)
    write_fixture_tables(folder / MODELS[product])
    return folder


def law(sex: str, x: int, values: dict = FIXTURE_LAW_VALUES) -> float:
    """The fixture law's rate, in the float operations of the fixture cell."""
    return float(values[sex.lower() + "_a"]) * float(values[sex.lower() + "_b"]) ** x


@pytest.fixture(scope="module")
def fixture_tables(tmp_path_factory):
    """The factory of a scratch copy of Index with the fixture tables, read by modelx."""
    folder = fixture_copy(tmp_path_factory.mktemp("fixture_tables"))
    model = mx.read_model(folder / MODELS[INDEX], name="FixtureTables")
    yield model.CoreTables
    model.close()


def test_the_fixture_is_written_into_the_copy_only(fixture_tables):
    assert list(fixture_tables.definitions()) == ALL_TABLES
    assert "_fixture" not in TABLES_SOURCE.read_text(encoding="utf-8")
    assert "_fixture" not in (CORE_MODEL / "Data" / TABLES_FILE).read_text(encoding="utf-8")
    known = ("dav2008t_proxy", "dav2008t_nr_proxy", "dav2008t_r_proxy", "dav2004r_proxy",
             "dav1997ti_proxy", "pflege_aktive_proxy")
    assert set(SHIPPED_TABLES) <= set(known)
    assert not set(FIXTURE_DEFINITIONS) & set(known)
    # the shipped table is the same beside the fixture tables
    assert fixture_tables.q("dav2008t_proxy", "F", 50) == makeham_rate("F", 50)
    assert not any(name.endswith("_proxy") for name in FIXTURE_DEFINITIONS)


def test_items_lists_the_items_of_every_table(fixture_tables):
    items = fixture_tables.items()
    assert list(items) == ALL_TABLES
    for table in SHIPPED_TABLES:
        assert items[table] == SHIPPED_ITEMS[table]
    for table, (_law, _trend, names) in FIXTURE_DEFINITIONS.items():
        assert items[table] == tuple(f"{table}_{name}" for name in names)
    held = set(fixture_tables.data.param_layers()["tables"])
    listed = {item for table in items for item in items[table]}
    assert listed - held == {"broken_fixture_f_b"}
    assert held - listed == set()


@pytest.mark.parametrize("sex", ["M", "F"])
def test_a_period_table_gives_its_laws_rate_unrounded(fixture_tables, sex):
    for x in range(0, 120):
        rate = fixture_tables.q("period_fixture", sex, x)
        assert type(rate) is float
        assert rate == min(1.0, law(sex, x)) == law(sex, x), x
        assert rate == fixture_tables.base_rate("period_fixture", sex, x)
    assert fixture_tables.q("period_fixture", "M", 40) != round(law("M", 40), 10)
    assert fixture_tables.q("period_fixture", "M", 40) != fixture_tables.q(
        "period_fixture", "F", 40)


def test_a_table_parameter_is_read_through_param(fixture_tables):
    assert fixture_tables.parameter("period_fixture", "m_a") == 0.0000201
    assert fixture_tables.first_age("steep_fixture") == 20
    assert fixture_tables.end_age("steep_fixture") == 111
    assert type(fixture_tables.end_age("steep_fixture")) is int
    assert fixture_tables.base_year("gen_fixture") == 1999
    assert fixture_tables.select_factors("sel_fixture") == (3.5, 2.25, 1.5)
    assert fixture_tables.select_factors("period_fixture") == ()


@pytest.mark.parametrize("table", ["period_fixture", "steep_fixture", "gen_fixture",
                                   "sel_fixture"])
def test_the_rate_at_the_last_age_is_exactly_1(fixture_tables, table):
    last = fixture_tables.end_age(table) - 1
    extra = {"gen_fixture": {"birth_year": 2090}, "sel_fixture": {"duration": 1}}.get(table, {})
    for sex in ("M", "F"):
        rate = fixture_tables.q(table, sex, last, **extra)
        assert rate == 1.0 and type(rate) is float
    # the closure is the table's, not the law's
    assert law("F", 120) < 1.0
    assert fixture_tables.base_rate("period_fixture", "F", 120) == law("F", 120)


def test_a_rate_is_capped_at_1_and_the_base_rate_is_not(fixture_tables):
    values = FIXTURE_VALUES["steep_fixture"]
    capped = [x for x in range(20, 110) if law("M", x, values) > 1.0]
    assert capped and capped[0] > 20
    for x in range(20, 110):
        assert fixture_tables.q("steep_fixture", "M", x) == min(1.0, law("M", x, values))
        assert fixture_tables.base_rate("steep_fixture", "M", x) == law("M", x, values)
    assert fixture_tables.q("steep_fixture", "M", capped[0]) == 1.0


@pytest.mark.parametrize(("table", "x"), [
    ("period_fixture", -1), ("period_fixture", 121), ("period_fixture", 150),
    ("steep_fixture", 19), ("steep_fixture", 0), ("steep_fixture", 111),
])
def test_an_age_outside_the_table_raises_and_is_not_clamped(fixture_tables, table, x):
    for cell in (fixture_tables.q, fixture_tables.base_rate):
        line = raised_line(lambda: cell(table, "M", x))
        assert line.startswith(f"ValueError: table {table!r}: x {x!r} is outside"), line


@pytest.mark.parametrize("sex", ["U", "m", "f", "", None, 1])
def test_a_sex_other_than_m_and_f_raises(fixture_tables, sex):
    line = raised_line(lambda: fixture_tables.q("period_fixture", sex, 40))
    assert line.startswith(f"ValueError: table 'period_fixture': sex {sex!r} is"), line


def test_an_unknown_table_raises(fixture_tables):
    for cell in (fixture_tables.q, fixture_tables.base_rate, fixture_tables.trend):
        assert raised_line(lambda: cell("fixture", "M", 40)) == (
            "ValueError: table 'fixture' is not defined")
    assert raised_line(lambda: fixture_tables.definition("fixture")) == (
        "ValueError: table 'fixture' is not defined")


@pytest.mark.parametrize(("sex", "trend"), [("M", 0.0125), ("F", 0.0175)])
def test_a_generational_table_applies_its_trend_to_the_calendar_year(fixture_tables, sex, trend):
    assert fixture_tables.trend("gen_fixture", sex, 40) == trend
    for birth_year, x in [(1959, 40), (1960, 67), (1999, 0), (2010, 30), (1940, 20), (1900, 119)]:
        rate = fixture_tables.q("gen_fixture", sex, x, birth_year)
        assert rate == min(1.0, law(sex, x) * (1.0 - trend) ** (birth_year + x - 1999))
        assert rate == fixture_tables.q("gen_fixture", sex, x, birth_year=birth_year)
    # the base year's rate is the law's, a later year's lower, an earlier year's higher
    assert fixture_tables.q("gen_fixture", sex, 40, 1959) == law(sex, 40)
    assert fixture_tables.q("gen_fixture", sex, 40, 1989) < law(sex, 40)
    assert fixture_tables.q("gen_fixture", sex, 40, 1929) > law(sex, 40)
    # the same calendar year reached by two birth years has the same trend power
    assert fixture_tables.q("gen_fixture", sex, 60, 1990) / law(sex, 60) == pytest.approx(
        fixture_tables.q("gen_fixture", sex, 50, 2000) / law(sex, 50), rel=1e-14)


def test_the_trend_does_not_act_on_the_closure(fixture_tables):
    assert fixture_tables.q("gen_fixture", "M", 120, 2100) == 1.0
    assert fixture_tables.q("gen_fixture", "M", 119, 2100) < 1.0


def test_a_generational_table_without_a_birth_year_raises(fixture_tables):
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q("gen_fixture", "M", x))
        assert line == ("ValueError: table 'gen_fixture': birth_year is missing, the table is"
                        " generational")


@pytest.mark.parametrize("table", ["period_fixture", "sel_fixture"])
def test_a_period_table_with_a_birth_year_raises(fixture_tables, table):
    extra = {"duration": 1} if table == "sel_fixture" else {}
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q(table, "M", x, 1960, **extra))
        assert line == (f"ValueError: table {table!r}: birth_year 1960 is given, the table is a"
                        f" period table")
    line = raised_line(lambda: fixture_tables.trend(table, "M", 40))
    assert line == f"ValueError: table {table!r}: a period table has no trend"


def test_a_select_table_applies_the_factor_of_the_duration_and_holds_the_last(fixture_tables):
    factors = {1: 3.5, 2: 2.25, 3: 1.5, 4: 1.5, 11: 1.5, 80: 1.5}
    for duration, factor in factors.items():
        for x in (30, 55):
            rate = fixture_tables.q("sel_fixture", "F", x, None, duration)
            assert rate == min(1.0, law("F", x) * factor)
            assert rate == fixture_tables.q("sel_fixture", "F", x, duration=duration)
    # a selected rate is capped at 1 too
    assert law("M", 115) < 1.0 < law("M", 115) * 3.5
    assert fixture_tables.q("sel_fixture", "M", 115, duration=1) == 1.0


@pytest.mark.parametrize(("duration", "words"), [
    (None, "duration is missing, the table is select"),
    (0, "duration 0 is below 1"),
    (-3, "duration -3 is below 1"),
])
def test_a_select_table_without_a_duration_from_1_raises(fixture_tables, duration, words):
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q("sel_fixture", "M", x, None, duration))
        assert line == f"ValueError: table 'sel_fixture': {words}"


@pytest.mark.parametrize("table", ["period_fixture", "gen_fixture"])
def test_a_table_without_selection_with_a_duration_raises(fixture_tables, table):
    birth_year = 1960 if table == "gen_fixture" else None
    for x in (40, 120):
        line = raised_line(lambda: fixture_tables.q(table, "M", x, birth_year, 1))
        assert line == (f"ValueError: table {table!r}: duration 1 is given, the table has no"
                        f" selection")


def test_a_table_naming_an_item_the_layer_lacks_raises_the_loaders_key_error(fixture_tables):
    assert fixture_tables.q("broken_fixture", "M", 40) == law("M", 40)
    line = raised_line(lambda: fixture_tables.q("broken_fixture", "F", 40))
    assert line == "KeyError: 'broken_fixture_f_b'"


def test_a_gap_in_the_select_factors_raises_the_loaders_key_error(fixture_tables):
    """``sel_1`` and ``sel_3`` are two factors, read as ``sel_1`` and ``sel_2``: duration 2
    does not silently get ``sel_3``."""
    for cell in (lambda: fixture_tables.select_factors("gap_fixture"),
                 lambda: fixture_tables.q("gap_fixture", "M", 40, duration=1),
                 lambda: fixture_tables.q("gap_fixture", "M", 40, duration=2)):
        assert raised_line(cell) == "KeyError: 'gap_fixture_sel_2'"


# --------------------------------------------------------------------------- the runner

def load_runner():
    spec = importlib.util.spec_from_file_location("run_baseline",
                                                  ROOT / "tools" / "run_baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def held_rates(space_model) -> dict:
    """The rates the factory of an exported model holds, by the arguments of ``q``."""
    return dict(space_model.CoreTables._v_q)


def run_spying_on_the_factory(folder: Path, monkeypatch, **run):
    """Run ``folder`` through the runner's export engine. Return the run's result, the rates
    ``CoreTables`` held just after each point's item was deleted, by point in the order of
    the deletions, and the rates it held when the run ended."""
    after, models = {}, []
    import_module = importlib.import_module

    def spying_import(name, *args, **kwargs):
        module = import_module(name, *args, **kwargs)
        if name.startswith("_delib_export_"):
            space_model = module.mx_model
            models.append(space_model)
            cls = type(space_model.Projection)
            original = cls.__delitem__

            def spy(self, key):
                original(self, key)
                after[key] = held_rates(space_model)

            monkeypatch.setattr(cls, "__delitem__", spy)
        return module

    monkeypatch.setattr(importlib, "import_module", spying_import)
    result = load_runner().run_product(folder, **run)
    assert len(models) == 1
    return result, after, held_rates(models[0])


def test_the_runner_keeps_the_rates_of_an_earlier_point(tmp_path, monkeypatch):
    """The copy of Index reads the period fixture table in a cell of its own, which
    overrides the core's hook: the two engines agree, and the rates point 1 computed are
    still held after its item and every later point's item are deleted."""
    folder = fixture_copy(tmp_path)
    add_cells(folder / MODELS[INDEX] / "Projection" / "__init__.py",
              'def mort_rate_at_age(x):\n'
              '    """The fixture table\'s rate.\n\n'
              '    Override reason: test fixture, tests/test_tables.py\n    """\n'
              '    return tables.q("period_fixture", sex(), x)\n')
    runner = load_runner()
    traced = runner.run_product(folder, engine="modelx")
    shipped = runner.run_product(PRODUCTS_DIR / INDEX, engine="modelx")
    (count, checks, sha, failures, _lines, digests), after, at_end = run_spying_on_the_factory(
        folder, monkeypatch)
    assert failures == [] and traced[3] == []
    assert count > 2 and list(after) == list(range(1, count + 1))
    assert (count, checks, sha, digests) == (traced[0], traced[1], traced[2], traced[5])
    assert sha != shipped[2]

    first = after[1]
    assert first and all(key[0] == "period_fixture" for key in first)
    sex, age = next((key[1], key[2]) for key in first)
    assert first[("period_fixture", sex, age, None, None)] == law(sex, age)
    for point_id in range(2, count + 1):
        assert first.items() <= after[point_id].items(), point_id
    assert first.items() <= at_end.items()
    assert len(at_end) > len(first)


# --------------------------------------------------------------------------- the hooks

TABLE_HOOKS = ("mort_table_name", "mort_rate_table", "omega_age_table")


@pytest.mark.parametrize("product", sorted(MODELS))
def test_only_a_switched_product_reaches_a_hook_that_reads_the_factory(product, product_models):
    model = product_models(product)
    reachable = param_usage.scan(model).reachable
    for hook in TABLE_HOOKS:
        # Riester reads its main role, a period table, without the birth year of its second
        assert model.Projection.cells[hook]._is_derived() or (
            product, hook) == ("riester_rente", "mort_rate_table"), hook
    # the end age is read off the table by a switched product that runs to it: RV, Basis and
    # Sofort; Riester, with two roles, names the role in its own ``omega_age``
    assert ("omega_age_table" in reachable) == (product in (RV, "basisrente", SOFORT))
    choices = {item: value for item, value in model.Data.param_dict().items()
               if item.endswith("_table")}
    if product == RLV:
        # its table depends on the life: it has no role ``mort_table``, reads the factory in
        # its own ``mort_rate_at_age`` and reaches no hook of the core
        for hook in TABLE_HOOKS:
            assert hook not in reachable, hook
        assert model.Projection.cells["mort_rate_at_age"]._is_defined()
        assert "mort_rate_at_age" in reachable
        assert choices == SWITCHED[product]
        assert set().union(*(CHOICE_READERS[item] for item in choices)) <= reachable
    elif product == SOFORT:
        # two lives on one table: its hook ``mort_rate_gen`` reads the main role through the
        # core's ``mort_table_name`` for each life, and the core's own reads stay unreached
        assert "mort_table_name" in reachable
        assert not {"mort_rate_table", "mort_rate_at_age"} & reachable
        assert model.Projection.cells["mort_rate_gen"]._is_defined()
        assert {"mort_rate_gen", "mort_be_trend"} <= reachable
        assert choices == SWITCHED[product]
        assert set().union(*(CHOICE_READERS[item] for item in choices)) <= reachable
    elif product in SWITCHED:
        assert {"mort_table_name", "mort_rate_table", "mort_rate_at_age"} <= reachable
        assert choices == SWITCHED[product]
        assert set().union(*(CHOICE_READERS[item] for item in choices)) <= reachable
    else:
        for hook in TABLE_HOOKS:
            assert hook not in reachable, hook
        assert choices == {}
    # a second role is a hook of the product, not of the core, and so is the cell that maps
    # a contract attribute to a role
    assert ("mort_rate_dis_at_age" in model.Projection.cells) == (product == BU)
    assert ("mort_table_smoker" in model.Projection.cells) == (product == RLV)
    assert ("annuity_mort_rate" in model.Projection.cells) == (product == "riester_rente")
    # the read of the main role without a birth year is Riester's, whose main role is a period
    # table and whose second role the generational one
    assert model.Projection.cells["mort_rate_table"]._is_defined() == (
        product == "riester_rente")
    # the cohort of a generational table is the product's: RV's, Basis' and Riester's, and
    # Sofort's since the scaffold
    assert model.Projection.cells["birth_year"]._is_defined() == (
        product in (RV, "basisrente", "riester_rente", "sofortrente"))


# The best-estimate rates of the values package on ``dav2008t_proxy`` at the factor 0.75, six
# significant digits: the rows of Index and of BU's active lives, which are the same.
BE_PACKAGE_RATES = {
    ("M", 30): 0.000542171, ("M", 40): 0.00114328, ("M", 50): 0.00270242, ("M", 65): 0.0107644,
    ("F", 30): 0.000403374, ("F", 40): 0.000855, ("F", 50): 0.0020264, ("F", 65): 0.00808351,
}


def test_index_best_estimate_is_the_factorys_rate_times_its_factor(product_models):
    model = product_models(INDEX)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in TABLE_HOOKS + ("birth_year", "mort_rate_at_age", "mort_rate_base",
                               "mort_be_trend", "mort_rate", "mort_rate_mth", "pols_death"):
        assert cells[name]._is_derived(), name
    assert cells["mort_be_factor"]._is_defined()
    assert "Override reason:" in cells["mort_be_factor"].formula.source
    assert model.Data.param("mort_be_factor") == 0.75
    assert model.Data.param("mort_table") == "dav2008t_proxy"
    seen = set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex = item.sex()
        assert item.mort_table_name() == "dav2008t_proxy"
        assert item.mort_be_factor() == 0.75 and item.birth_year() == 0
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            rate = tables.q("dav2008t_proxy", sex, x)
            assert rate == makeham_rate(sex, x) < 1.0
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == rate * 0.75, (point_id, t)
            assert item.mort_rate_mth(t) == 1.0 - (1.0 - rate * 0.75) ** (1.0 / 12.0)
            if (sex, x) in BE_PACKAGE_RATES:
                assert float(f"{item.mort_rate(t):.6g}") == BE_PACKAGE_RATES[(sex, x)]
                seen.add((sex, x))
    assert {("M", 40), ("M", 50), ("M", 65), ("F", 40), ("F", 50), ("F", 65)} <= seen
    assert {key[0] for key in tables.q} == {"dav2008t_proxy"}


def test_index_holds_no_mortality_file_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / INDEX
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header if "mort" in column or column == "qx"], path
    model = product_models(INDEX)
    assert "mort_file" not in model.Data.refs
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    assert own == ["mort_be_factor"]
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    reachable = param_usage.scan(model).reachable
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & reachable
    for space in ("Data", "Projection"):
        source = (folder / MODELS[INDEX] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()"):
            assert name not in source, (space, name)
    # every death rate of a run comes through the factory's one lookup
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0


# The tariff rates of the values package for BU by age, six significant digits: active lives,
# 0.6 of the 50/50 blend of ``dav2008t_proxy``, and lives in claim by claim year, 0.7 of the
# 50/50 blend of ``dav1997ti_proxy``.
BU_ACTV_TARIFF_PACKAGE_RATES = {30: 0.000378218, 40: 0.000799314, 50: 0.00189153,
                                65: 0.00753918}
BU_DIS_TARIFF_PACKAGE_RATES = {
    (30, 1): 0.00294, (30, 3): 0.001568, (30, 6): 0.001176, (30, 10): 0.001176,
    (40, 1): 0.00728599, (40, 2): 0.00485733, (40, 3): 0.00388586, (40, 4): 0.00340013,
    (40, 5): 0.00315726, (40, 6): 0.0029144, (40, 10): 0.0029144,
    (50, 1): 0.0180563, (50, 3): 0.00963005, (50, 6): 0.00722254,
    (65, 1): 0.0704436, (65, 3): 0.0375699, (65, 6): 0.0281774,
    (18, 1): 0.000989414,
}
BU_CORE_MORT_CELLS = TABLE_HOOKS + (
    "birth_year", "mort_rate_at_age", "mort_rate_tariff_at_age", "mort_rate_base",
    "mort_be_trend", "mort_rate", "mort_rate_mth", "unisex_blend", "unisex_mix_male")
BU_OWN_MORT_CELLS = [
    "mort_be_factor", "mort_rate_dis", "mort_rate_dis_at_age", "mort_rate_dis_first_at_age",
    "mort_rate_dis_first_mth", "mort_rate_dis_first_mth_year", "mort_rate_dis_mth",
    "mort_rate_dis_mth_year", "mort_rate_first_at_age", "mort_rate_first_mth"]


def blend(male: float, female: float, share: float = 0.5) -> float:
    """The unisex blend in the float operations of the core's ``unisex_blend``."""
    return share * male + (1.0 - share) * female


def twelfth(rate: float) -> float:
    """The monthly rate of an annual rate, as BU's monthly cells form it."""
    return 1.0 - (1.0 - rate) ** (1.0 / 12.0)


def test_bu_active_best_estimate_is_the_factorys_rate_times_its_factor(product_models):
    model = product_models(BU)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in BU_CORE_MORT_CELLS:
        assert cells[name]._is_derived(), name
    assert cells["mort_be_factor"]._is_defined()
    assert "Override reason:" in cells["mort_be_factor"].formula.source
    assert model.Data.param("mort_be_factor") == 0.75
    assert model.Data.param("mort_table") == DAV2008T
    seen, sexes = set(), set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex = item.sex()
        sexes.add(sex)
        assert item.mort_table_name() == DAV2008T
        assert item.mort_be_factor() == 0.75 and item.birth_year() == 0
        for t in range(0, item.proj_len()):
            x = item.age(t)
            rate = tables.q(DAV2008T, sex, x)
            assert rate == makeham_rate(sex, x) < 1.0
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == rate * 0.75, (point_id, t)
            assert item.mort_rate_mth(t) == twelfth(rate * 0.75)
            if (sex, x) in BE_PACKAGE_RATES:
                assert float(f"{item.mort_rate(t):.6g}") == BE_PACKAGE_RATES[(sex, x)]
                seen.add((sex, x))
    assert sexes == {"M", "F"}
    assert {("M", 40), ("M", 50), ("M", 65), ("F", 30), ("F", 40), ("F", 50), ("F", 65)} <= seen


def test_bu_points_that_differ_in_sex_alone_share_the_premium_and_not_the_frame(product_models):
    # pitfall 12 of BU's technical notes: sex must not enter the premium
    model = product_models(BU)
    points = model.Data.model_point_table()
    columns = [column for column in points.columns if column != "sex"]
    assert list(points.loc[1, columns]) == list(points.loc[2, columns])
    assert {points.at[1, "sex"], points.at[2, "sex"]} == {"M", "F"}
    woman, man = model.Projection[1], model.Projection[2]
    assert woman.prem_gross_level_pp() == man.prem_gross_level_pp()
    for s_first in (0, 1, 12, 119, 299, 443):
        assert woman.mort_rate_first_mth(s_first) == man.mort_rate_first_mth(s_first)
        assert woman.mort_rate_dis_first_mth_year(woman.age_first(s_first)) == (
            man.mort_rate_dis_first_mth_year(man.age_first(s_first)))
    frames = [item.result_cf() for item in (woman, man)]
    assert frames[0].shape == frames[1].shape
    assert not frames[0].equals(frames[1])
    assert frames[0]["claims_bu_rente"].sum() > frames[1]["claims_bu_rente"].sum()


def test_bu_active_tariff_rate_is_the_load_on_the_unisex_blend(product_models):
    model = product_models(BU)
    tables = model.CoreTables
    assert model.Data.param("mort_actv_load_first") == 0.6
    assert model.Data.param("unisex_mix_male") == 0.5
    seen, annual = set(), {}
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        assert item.unisex_mix_male() == 0.5
        for s in range(0, item.first_len()):
            x = item.age_first(s)
            mixed = blend(tables.q(DAV2008T, "M", x), tables.q(DAV2008T, "F", x))
            assert item.mort_rate_tariff_at_age(x) == mixed
            assert item.mort_rate_first_at_age(x) == mixed * 0.6 < 1.0, (point_id, s)
            assert item.mort_rate_first_mth(s) == twelfth(mixed * 0.6)
            # the same rate whatever the sex of the model point: sex does not price
            assert annual.setdefault(x, item.mort_rate_first_at_age(x)) == mixed * 0.6
            if x in BU_ACTV_TARIFF_PACKAGE_RATES:
                assert float(f"{mixed * 0.6:.6g}") == BU_ACTV_TARIFF_PACKAGE_RATES[x]
                seen.add(x)
    assert seen == set(BU_ACTV_TARIFF_PACKAGE_RATES)
    # the first order stays 20 % below the best estimate of the blend: 0.6 = 0.8 * 0.75
    assert annual[40] == pytest.approx(0.8 * 0.75 * blend(makeham_rate("M", 40),
                                                         makeham_rate("F", 40)), rel=1e-15)


def test_bu_disabled_rates_are_the_select_table_at_the_claim_year(product_models):
    model = product_models(BU)
    tables = model.CoreTables
    assert model.Data.param("mort_dis_table") == DAV1997TI
    assert model.Data.param("mort_dis_load_first") == 0.7
    assert model.Data.claim_duration_last_year() == 11
    years = range(1, 12)
    durations = (1, 2, 12, 13, 25, 37, 49, 60, 61, 72, 73, 121, 132, 133, 400)
    seen, sexes = set(), set()
    for point_id in model.Data.model_point_table().index:
        item = model.Projection[point_id]
        sex = item.sex()
        sexes.add(sex)
        for t in sorted({0, 1, 12, 13, item.proj_len() // 2, item.proj_len() - 1}):
            x = item.age(t)
            # the best estimate: the table on the own sex, without a factor
            for z in durations:
                year = item.claim_year(z)
                assert year == min(11, (z - 1) // 12 + 1)
                rate = tables.q(DAV1997TI, sex, x, duration=year)
                assert rate == ti_rate(sex, x, year) < 1.0
                assert item.mort_rate_dis_at_age(sex, x)[year - 1] == rate
                assert item.mort_rate_dis(t, z) == rate, (point_id, t, z)
                assert item.mort_rate_dis_mth(t, z) == twelfth(rate)
                assert item.mort_rate_dis_mth_year(x)[year - 1] == item.mort_rate_dis_mth(t, z)
            # the hook reads ``q`` at every claim year of the claim-duration table
            assert item.mort_rate_dis_at_age(sex, x) == tuple(
                tables.q(DAV1997TI, sex, x, duration=year) for year in years)
            assert item.mort_rate_dis_mth_year(x) == tuple(
                twelfth(tables.q(DAV1997TI, sex, x, duration=year)) for year in years)
            assert item.dis_q_year(x).tolist() == list(item.mort_rate_dis_mth_year(x))
        for s in sorted({0, 12, item.first_len() // 2, item.first_len() - 1}):
            x = item.age_first(s)
            # the tariff rate: the load on the blend of both sexes at the same claim year
            for z in durations:
                year = item.claim_year(z)
                mixed = blend(tables.q(DAV1997TI, "M", x, duration=year),
                              tables.q(DAV1997TI, "F", x, duration=year))
                assert item.mort_rate_dis_first_at_age(x)[year - 1] == mixed * 0.7 < 1.0
                assert item.mort_rate_dis_first_mth(s, z) == twelfth(mixed * 0.7)
                assert (item.mort_rate_dis_first_mth_year(x)[year - 1]
                        == item.mort_rate_dis_first_mth(s, z))
            assert item.mort_rate_dis_first_mth_year(x) == tuple(
                twelfth(rate) for rate in item.mort_rate_dis_first_at_age(x))
            assert len(item.mort_rate_dis_first_at_age(x)) == 11
            assert item.dis_q_year_first(x).tolist() == list(
                item.mort_rate_dis_first_mth_year(x))
        for (x, year), figure in BU_DIS_TARIFF_PACKAGE_RATES.items():
            tariff = item.mort_rate_dis_first_at_age(x)[year - 1]
            assert float(f"{tariff:.6g}") == figure, (x, year)
            best = item.mort_rate_dis_at_age(sex, x)[year - 1]
            if (sex, x, min(year, 6)) in TI_PACKAGE_RATES:
                assert float(f"{best:.6g}") == TI_PACKAGE_RATES[(sex, x, min(year, 6))]
                seen.add((sex, x, min(year, 6)))
        # the tuples hold the last select factor from claim year 6 to the table's last row
        assert len(set(item.mort_rate_dis_mth_year(40)[5:])) == 1
        assert len(set(item.mort_rate_dis_mth_year(40)[:6])) == 6
    assert sexes == {"M", "F"} and seen == set(TI_PACKAGE_RATES)
    # the tariff rate is the unisex level, the best estimate 1.2 and 0.8 of it
    item = model.Projection[1]
    level = item.mort_rate_dis_first_at_age(40)[0] / 0.7
    assert tables.q(DAV1997TI, "M", 40, duration=1) == pytest.approx(1.2 * level, rel=1e-8)
    assert tables.q(DAV1997TI, "F", 40, duration=1) == pytest.approx(0.8 * level, rel=1e-8)
    # never one rate for both states
    assert item.mort_rate_dis(0, 1) > item.mort_rate_dis(0, 61) > item.mort_rate(0)


def test_bu_holds_no_mortality_file_column_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / BU
    assert not (folder / "mortality_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header if "mort" in column or column == "qx"], path
    with (folder / "claim_duration_table.csv").open(encoding="utf-8", newline="") as handle:
        assert next(csv.reader(handle)) == ["dur_year", "recov_rate", "provenance"]
    model = product_models(BU)
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    assert own == BU_OWN_MORT_CELLS
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    for name in ("mort_table_ages", "mort_dis_sel_factors", "mort_dis_sel_factor"):
        assert name not in model.Data.cells and name not in model.Projection.cells, name
    reachable = param_usage.scan(model).reachable
    assert not {"mort_table", "mort_table_dict", "mort_table_index", "omega_age"} & reachable
    for space in ("Data", "Projection"):
        source = (folder / MODELS[BU] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mortality_table", "mort_file", "mort_table_dict", "mort_table()",
                     "mort_table_ages", "mort_table_index", "sel_factor", "mort_rate_actv"):
            assert name not in source, (space, name)
    # one read of the factory besides the core's hooks, and it goes through ``q``
    cells = dict(_formula_cells(folder / MODELS[BU] / "Projection" / "__init__.py"))
    reads = {name: ast.unparse(node) for name, cell in cells.items() for node in ast.walk(cell)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id == "tables"}
    assert reads == {"mort_rate_dis_at_age": "tables.q"}
    # every death rate of a run comes through the factory's one lookup, off its two tables
    item = model.Projection[7]
    item.result_cf()
    item.prem_gross_level_pp()
    assert {key[0] for key in model.CoreTables.q} == {DAV2008T, DAV1997TI}
    assert all(key[4] is None for key in model.CoreTables.q if key[0] == DAV2008T)
    assert all(key[4] in range(1, 12) for key in model.CoreTables.q if key[0] == DAV1997TI)
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0


def test_bu_reads_its_ages_unclamped(product_models):
    """The clamp to the file's ages 18 to 70 went without a guard: an age above 70 has a
    rate of its own, and an age outside a table raises."""
    model = product_models(BU)
    item, tables = model.Projection[1], model.CoreTables
    sex = item.sex()
    assert item.mort_rate_at_age(75) == tables.q(DAV2008T, sex, 75) > item.mort_rate_at_age(70)
    assert item.mort_rate_dis_at_age(sex, 75)[0] > item.mort_rate_dis_at_age(sex, 70)[0]
    assert item.mort_rate_dis_first_at_age(75)[0] > item.mort_rate_dis_first_at_age(70)[0]
    assert item.mort_rate_first_at_age(75) > item.mort_rate_first_at_age(70)
    line = raised_line(lambda: item.mort_rate_dis_at_age(sex, 17))
    assert line == "ValueError: table 'dav1997ti_proxy': x 17 is outside its ages 18 to 120"
    line = raised_line(lambda: item.mort_rate_dis_first_at_age(121))
    assert line == "ValueError: table 'dav1997ti_proxy': x 121 is outside its ages 18 to 120"
    line = raised_line(lambda: item.mort_rate_at_age(121))
    assert line == "ValueError: table 'dav2008t_proxy': x 121 is outside its ages 0 to 120"


def test_bu_passes_a_table_rate_of_1_through_its_factor_and_its_loads(tmp_path):
    """On a scratch copy whose two tables close at 66, the last age a point attains: the
    best estimate and the tariff rates are 1 there, not the factor or a load."""
    folder = product_copy(tmp_path, BU)
    path = tables_file(folder, BU)
    text = path.read_text(encoding="utf-8")
    for table in (DAV2008T, DAV1997TI):
        assert text.count(f"{table}_end_age,121,") == 1
        text = text.replace(f"{table}_end_age,121,", f"{table}_end_age,67,")
    path.write_text(text, encoding="utf-8")
    model = mx.read_model(folder / MODELS[BU], name="BuThruProbe")
    try:
        tables = model.CoreTables
        sexes = set()
        for point_id in (1, 2, 5):
            item = model.Projection[point_id]
            sex = item.sex()
            sexes.add(sex)
            assert item.cover_end_age() == 67
            last, last_first = item.proj_len() - 1, item.first_len() - 1
            assert item.age(last) == 66 == item.age_first(last_first)
            assert item.mort_be_factor() == 0.75
            # at the closing age: 1, not 0.75, 0.6 or 0.7
            assert tables.q(DAV2008T, sex, 66) == 1.0
            assert item.mort_rate_base(last) == 1.0 == item.mort_rate(last)
            assert item.mort_rate_tariff_at_age(66) == 1.0
            assert item.mort_rate_first_at_age(66) == 1.0 == item.mort_rate_first_mth(last_first)
            for z in (1, 13, 61, 133):
                assert item.mort_rate_dis(last, z) == 1.0 == item.mort_rate_dis_mth(last, z)
                assert item.mort_rate_dis_first_mth(last_first, z) == 1.0
            assert item.mort_rate_dis_at_age(sex, 66) == (1.0,) * 11
            assert item.mort_rate_dis_first_at_age(66) == (1.0,) * 11
            assert set(item.mort_rate_dis_mth_year(66)) == {1.0}
            assert set(item.mort_rate_dis_first_mth_year(66)) == {1.0}
            # the year before, the factor and the loads act on the table rates
            before, before_first = last - 12, last_first - 12
            assert item.age(before) == 65 == item.age_first(before_first)
            assert item.mort_rate(before) == makeham_rate(sex, 65) * 0.75 < 1.0
            mixed = blend(makeham_rate("M", 65), makeham_rate("F", 65))
            assert item.mort_rate_first_at_age(65) == mixed * 0.6
            assert item.mort_rate_first_mth(before_first) == twelfth(mixed * 0.6)
            assert item.mort_rate_dis(before, 1) == ti_rate(sex, 65, 1) < 1.0
            assert item.mort_rate_dis_first_at_age(65)[0] == blend(
                ti_rate("M", 65, 1), ti_rate("F", 65, 1)) * 0.7
        assert sexes == {"M", "F"}
    finally:
        model.close()


RV_CORE_MORT_CELLS = TABLE_HOOKS + (
    "mort_rate_at_age", "mort_rate_base", "mort_be_trend", "mort_rate", "mort_rate_mth",
    "mort_load_tariff", "mort_rate_tariff_at_age", "mort_rate_tariff_base", "mort_rate_tariff",
    "unisex_blend", "unisex_mix_male", "pols_death")


def test_rv_reads_the_table_at_the_cohort_and_runs_to_its_end_age(product_models):
    model = product_models(RV)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in ("birth_year", "omega_age", "horizon_age"):
        assert cells[name]._is_defined(), name
        assert "Override reason:" in cells[name].formula.source, name
    assert model.Data.param("mort_table") == DAV2004R
    assert tables.end_age(DAV2004R) == 121
    cohorts, rows = set(), 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.mort_table_name() == DAV2004R
        assert item.birth_year() == item.issue_year() - item.issue_age()
        assert item.omega_age() == 121 == item.omega_age_table() == item.horizon_age()
        # the frame is the one the item omega_age 121 gave: to the end age, no survivor left
        assert item.proj_len_y() == 121 - item.issue_age()
        assert item.proj_len() == 12 * item.proj_len_y()
        assert item.age(item.proj_len() - 1) == 120
        assert item.mort_rate(item.proj_len() - 1) == 1.0
        for t in range(item.t_start(), item.proj_len(), 12):
            # the table's calendar year, birth year plus attained age, is the policy year's
            assert item.birth_year() + item.age(t) == item.calendar_year(t), (point_id, t)
        cohorts.add(item.birth_year())
        rows += item.proj_len() - item.t_start()
    assert {1963, 1970, 1977, 1992} <= cohorts and min(cohorts) == 1963
    with (ROOT / "baseline" / RV / "result_cf.csv").open(encoding="utf-8") as handle:
        assert rows == sum(1 for _line in handle) - 1 == 12036


def test_rv_best_estimate_is_the_factorys_rate_times_its_factor(product_models):
    model = product_models(RV)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in RV_CORE_MORT_CELLS:
        assert cells[name]._is_derived(), name
    assert cells["mort_be_factor"]._is_defined()
    assert model.Data.param("mort_be_factor") == 1.15
    certain, capped, sexes = set(), set(), set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex, cohort = item.sex(), item.birth_year()
        sexes.add(sex)
        assert item.mort_be_factor() == 1.15
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            rate = tables.q(DAV2004R, sex, x, cohort)
            assert rate == r_rate(sex, x, cohort), (point_id, t)
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == min(1.0, rate * 1.15), (point_id, t)
            if rate == 1.0:
                # 1 and not 1.15 capped: the table rate of 1 passes through the factor
                assert item.mort_rate(t) == 1.0
                certain.add((sex, x))
            elif rate * 1.15 >= 1.0:
                capped.add((sex, x))
            if item.mort_rate(t) == 1.0:
                assert item.mort_rate_mth(t) == (1.0 if t % 12 == 11 else 0.0)
            else:
                assert item.mort_rate_mth(t) == 1.0 - (1.0 - rate * 1.15) ** (1.0 / 12.0)
    assert sexes == {"M", "F"}
    # the table's cap binds from 114 for a man and 118 for a woman, its closure at 120; the
    # factor reaches 1 a year earlier
    assert certain == ({("M", x) for x in range(114, 121)} | {("F", x) for x in range(118, 121)})
    assert capped == {("M", 113), ("F", 117)}
    # every death rate of the run came through the factory's one lookup, at a birth year
    # (the probe of the period table is another test's, on the model they share)
    held = [key for key in tables.q if key[0] == DAV2004R]
    assert len(held) > 500 and {key[0] for key in tables.q} <= {DAV2004R, DAV2008T}
    assert all(key[3] in range(1963, 1993) and key[4] is None for key in held)


def test_rv_tariff_rate_is_the_unisex_blend_at_the_cohort(product_models):
    model = product_models(RV)
    projection, tables = model.Projection, model.CoreTables
    assert model.Data.param("unisex_mix_male") == 0.45
    by_key = {}
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        cohort = item.birth_year()
        assert item.unisex_mix_male() == 0.45
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            male, female = tables.q(DAV2004R, "M", x, cohort), tables.q(DAV2004R, "F", x, cohort)
            mixed = 0.45 * male + (1.0 - 0.45) * female
            assert mixed == blend(r_rate("M", x, cohort), r_rate("F", x, cohort), 0.45)
            assert item.mort_rate_tariff_at_age(x) == mixed == item.mort_rate_tariff_base(t)
            assert item.mort_rate_tariff(t) == mixed, (point_id, t)
            # between the two sexes' table rates, and not the own sex's
            assert female <= mixed <= male
            if male < 1.0:
                assert mixed != item.mort_rate_at_age(x)
                assert mixed == pytest.approx(0.78 * male, rel=1e-6)
                assert mixed == pytest.approx(1.3 * female, rel=1e-6)
            by_key.setdefault((x, cohort), {})[item.sex()] = mixed
        # the output column and the risk charge hold it
        frame = item.result_pols()
        aufschub = int(item.model_point()["aufschub_y"])
        for k in range(item.k_start(), item.proj_len_y()):
            assert frame.at[k + 1, "mort_rate_guar"] == item.mort_rate_tariff(12 * k)
            assert frame.at[k + 1, "mort_rate"] == item.mort_rate(12 * k)
            if k < aufschub:
                assert item.charge_risk_pp(k) == item.mort_rate_tariff(12 * k) * item.nar_pp(k)
            else:
                assert item.charge_risk_pp(k) == 0.0
        assert item.mort_rate_tariff(item.proj_len() - 1) == 1.0
    # a man and a woman of equal age and birth year have one tariff rate: points 4, 7 and 12
    shared = [rates for rates in by_key.values() if len(rates) == 2]
    assert len(shared) >= 76
    assert all(rates["M"] == rates["F"] for rates in shared)
    four, seven, twelve = projection[4], projection[7], projection[12]
    assert (four.sex(), seven.sex(), twelve.sex()) == ("F", "F", "M")
    assert four.birth_year() == seven.birth_year() == twelve.birth_year() == 1982
    for t in range(0, twelve.proj_len(), 12):
        assert four.mort_rate_tariff(t) == twelve.mort_rate_tariff(t) == seven.mort_rate_tariff(t)
        assert four.mort_rate(t) < twelve.mort_rate(t) or twelve.mort_rate(t) == 1.0


def test_rv_points_that_differ_in_sex_alone_share_the_charges_and_not_the_decrements(tmp_path):
    """On a scratch copy whose anchor is a woman: the risk charge, the account and the annuity
    per policy are the man's, the tariff rate being unisex; the best estimate is not."""
    folder = product_copy(tmp_path, RV)
    path = folder / "model_point_table.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[1].startswith("1,DE-RV-0001,M,50,2027,")
    rows[1] = rows[1].replace("1,DE-RV-0001,M,50,2027,", "1,DE-RV-0001,F,50,2027,", 1)
    path.write_text("".join(rows), encoding="utf-8")
    woman = mx.read_model(folder / MODELS[RV], name="RvWomanProbe")
    man = mx.read_model(PRODUCTS_DIR / RV / MODELS[RV], name="RvManProbe")
    try:
        her, him = woman.Projection[1], man.Projection[1]
        assert (her.sex(), him.sex()) == ("F", "M")
        assert her.birth_year() == him.birth_year() == 1977
        aufschub = int(him.model_point()["aufschub_y"])
        for k in range(aufschub):
            assert her.mort_rate_tariff(12 * k) == him.mort_rate_tariff(12 * k)
            assert her.charge_risk_pp(k) == him.charge_risk_pp(k) > 0.0
            assert her.prem_pp(k) == him.prem_pp(k)
            assert her.av_pp(k) == him.av_pp(k) and her.av_sur_pp(k) == him.av_sur_pp(k)
            assert her.cv_pp(k) == him.cv_pp(k) and her.db_pp(k) == him.db_pp(k)
            assert her.mort_rate(12 * k) < him.mort_rate(12 * k)
        assert her.capital_conv_pp() == him.capital_conv_pp()
        assert her.annuity_rate_appl() == him.annuity_rate_appl()
        assert her.annuity_guar_mth_pp() == him.annuity_guar_mth_pp()
        # the decrements, and with them the frame, are her own
        assert her.pols_if(12 * aufschub) > him.pols_if(12 * aufschub)
        assert her.result_cf()["annuity_payments"].sum() > him.result_cf()["annuity_payments"].sum()
    finally:
        woman.close()
        man.close()


def test_rv_holds_no_mortality_file_item_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / RV
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header
                    if column.startswith("mort") or column in ("qx", "q_base", "improve")], path
    model = product_models(RV)
    layer = model.Data.param_layers()["tariff_type"]
    assert "mort_base_year" not in layer and "omega_age" not in layer
    assert {item: layer[item] for item in layer if "mort" in item or "unisex" in item} == {
        "mort_be_factor": 1.15, "mort_table": DAV2004R, "unisex_mix_male": 0.45}
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if ("mort" in name or "improve" in name) and cell._is_defined())
    assert own == ["mort_be_factor"]
    assert "improve_rate" not in model.Projection.cells
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    usage = param_usage.scan(model)
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & usage.reachable
    assert "omega_age" not in usage.reads and "mort_base_year" not in usage.reads
    for space in ("Data", "Projection"):
        source = (folder / MODELS[RV] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()",
                     "mort_base_year", "improve_rate", '"omega_age"'):
            assert name not in source, (space, name)
    # no read of the factory besides the core's hooks
    cells = dict(_formula_cells(folder / MODELS[RV] / "Projection" / "__init__.py"))
    reads = {name: ast.unparse(node) for name, cell in cells.items() for node in ast.walk(cell)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id == "tables"}
    assert reads == {}
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0
    line = raised_line(lambda: item.mort_rate_at_age(121))
    assert line == "ValueError: table 'dav2004r_proxy': x 121 is outside its ages 0 to 120"


# The tariff rates of the values package for KLV by age, six significant digits: the 50/50
# blend of ``dav2008t_proxy``. Its best estimate is ``BE_PACKAGE_RATES``, as Index'.
KLV_TARIFF_PACKAGE_RATES = {40: 0.00133219, 50: 0.00315255, 65: 0.0125653}
KLV_CORE_MORT_CELLS = TABLE_HOOKS + (
    "birth_year", "mort_rate_at_age", "mort_rate_base", "mort_be_trend", "mort_rate",
    "mort_rate_mth", "mort_load_tariff", "mort_rate_tariff_at_age", "mort_rate_tariff_base",
    "mort_rate_tariff", "unisex_blend", "unisex_mix_male", "pols_tariff", "pols_death")
KLV_MORT_FILE = f"products/{KLV}/mort_table.csv"
KLV_BASELINE = f"baseline/{KLV}/result_cf.csv"


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                          check=True).stdout


def klv_switch() -> tuple[str, str | None]:
    """The revisions around KLV's switch: the commit before it and the switch commit, the
    one that deleted its mortality file. While the switch is not committed the commit before
    is ``HEAD`` and the switch is the working tree, ``None``. Skips the test where the
    history does not hold the file: a source archive or a shallow clone."""
    try:
        deleting = git_bytes("log", "-1", "--format=%H", "--diff-filter=D", "--",
                             KLV_MORT_FILE).decode().strip()
        before = f"{deleting}^" if deleting else "HEAD"
        git_bytes("cat-file", "-e", f"{before}:{KLV_MORT_FILE}")
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("the git history does not hold KLV's former mortality file")
    return before, deleting or None


def test_klv_tariff_rate_is_the_unisex_blend_of_the_factorys_table(product_models):
    model = product_models(KLV)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in KLV_CORE_MORT_CELLS:
        assert cells[name]._is_derived(), name
    assert model.Data.param("mort_table") == DAV2008T
    assert model.Data.param("unisex_mix_male") == 0.5
    by_age, seen = {}, set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.mort_table_name() == DAV2008T and item.birth_year() == 0
        assert item.unisex_mix_male() == 0.5
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            male, female = tables.q(DAV2008T, "M", x), tables.q(DAV2008T, "F", x)
            mixed = 0.5 * male + (1.0 - 0.5) * female
            assert mixed == blend(makeham_rate("M", x), makeham_rate("F", x)) < 1.0
            assert item.mort_rate_tariff_at_age(x) == mixed == item.mort_rate_tariff_base(t)
            # the neutral load: the rating factor loads the death leg, not the rate
            assert item.mort_rate_tariff(t) == mixed, (point_id, t)
            assert female < mixed < male and mixed != item.mort_rate_at_age(x)
            by_age.setdefault(x, {})[item.sex()] = mixed
            if x in KLV_TARIFF_PACKAGE_RATES:
                assert float(f"{mixed:.6g}") == KLV_TARIFF_PACKAGE_RATES[x]
                seen.add(x)
        # the first-order survivorship of the premium and the reserves stands on it
        x0 = item.issue_age()
        assert item.pols_tariff(1) == 1.0 - item.mort_rate_tariff_at_age(x0)
    assert seen == set(KLV_TARIFF_PACKAGE_RATES)
    # the same whatever the point's sex: every age a man and a woman both attain
    shared = [rates for rates in by_age.values() if len(rates) == 2]
    assert len(shared) == 25 and all(rates["M"] == rates["F"] for rates in shared)
    # points 1 and 7 differ in sex (and in the payment frequency): one tariff, one premium
    # before the Ratenzahlungszuschlag, and decrements of their own
    man, woman = projection[1], projection[7]
    assert (man.sex(), woman.sex()) == ("M", "F")
    assert man.prem_gross_level_pp() == woman.prem_gross_level_pp()
    for t in range(0, man.proj_len(), 12):
        assert man.mort_rate_tariff(t) == woman.mort_rate_tariff(t)
        assert woman.mort_rate(t) < man.mort_rate(t)
    # the anchor of the worked example: 0.0012 for a man of 37, the blend to twelve decimals
    assert tables.q(DAV2008T, "M", 37) == pytest.approx(0.0012, abs=1e-14)
    assert f"{man.mort_rate_tariff(0):.12f}" == "0.001048144252"


def test_klv_best_estimate_is_the_factorys_rate_times_its_factor(product_models):
    model = product_models(KLV)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    assert cells["mort_be_factor"]._is_defined()
    assert "Override reason:" in cells["mort_be_factor"].formula.source
    assert model.Data.param("mort_be_factor") == 0.75
    seen, sexes, oldest = set(), set(), 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex = item.sex()
        sexes.add(sex)
        assert item.mort_be_factor() == 0.75
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            oldest = max(oldest, x)
            rate = tables.q(DAV2008T, sex, x)
            assert rate == makeham_rate(sex, x) < 1.0
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == rate * 0.75, (point_id, t)
            assert item.mort_rate_mth(t) == 1.0 - (1.0 - rate * 0.75) ** (1.0 / 12.0)
            if (sex, x) in BE_PACKAGE_RATES:
                assert float(f"{item.mort_rate(t):.6g}") == BE_PACKAGE_RATES[(sex, x)]
                seen.add((sex, x))
    assert sexes == {"M", "F"}
    assert {("M", 40), ("M", 50), ("M", 65), ("F", 40), ("F", 50)} <= seen
    # no shipped point comes near the cap, which binds from 110
    assert oldest == 69
    assert f"{projection[1].mort_rate(0):.12f}" == "0.000900000000"


def test_klv_passes_a_table_rate_of_1_through_its_factor(tmp_path):
    """On a scratch copy whose table closes at 66, the last age point 14 attains: the best
    estimate and the tariff rate are 1 there, not 0.75 of the table rate or its blend."""
    folder = product_copy(tmp_path, KLV)
    path = tables_file(folder, KLV)
    text = path.read_text(encoding="utf-8")
    assert text.count(f"{DAV2008T}_end_age,121,") == 1
    path.write_text(text.replace(f"{DAV2008T}_end_age,121,", f"{DAV2008T}_end_age,67,"),
                    encoding="utf-8")
    model = mx.read_model(folder / MODELS[KLV], name="KlvThruProbe")
    try:
        item, tables = model.Projection[14], model.CoreTables
        last = item.proj_len() - 1
        assert (item.sex(), item.age(last)) == ("M", 66)
        assert item.mort_be_factor() == 0.75
        assert tables.q(DAV2008T, "M", 66) == 1.0 == tables.q(DAV2008T, "F", 66)
        assert item.mort_rate_base(last) == 1.0 == item.mort_rate(last)
        assert item.mort_rate_tariff_at_age(66) == 1.0 == item.mort_rate_tariff(last)
        # the certainty falls in the anniversary month
        assert item.mort_rate_mth(last) == 1.0 and item.mort_rate_mth(last - 1) == 0.0
        # the year before, the factor acts on the table rate
        before = last - 12
        assert item.age(before) == 65
        assert item.mort_rate(before) == makeham_rate("M", 65) * 0.75 < 1.0
        assert item.mort_rate_tariff(before) == blend(makeham_rate("M", 65),
                                                      makeham_rate("F", 65)) < 1.0
    finally:
        model.close()


def test_dav2008t_proxy_is_the_law_of_klvs_former_file(shipped_tables):
    """The table against the file KLV's switch deleted, read from git at the commit before:
    the file held the same law written to twelve decimals, and the rates differ by at most
    6.1e-12 below the cap."""
    before, _switch = klv_switch()
    data = git_bytes("show", f"{before}:{KLV_MORT_FILE}")
    # the file as upstream shipped it: its hash stands in the product's UPSTREAM.md
    upstream = (PRODUCTS_DIR / KLV / "UPSTREAM.md").read_text(encoding="utf-8")
    assert f"| `mort_table.csv` | `{hashlib.sha256(data).hexdigest()}` |" in upstream
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))
    held = {(row["sex"], int(row["age"])): float(row["mort_rate_1st"]) for row in rows}
    assert sorted(held) == [(sex, x) for sex in "FM" for x in range(0, 121)]
    worst, where = 0.0, None
    for (sex, x), filed in held.items():
        rate = shipped_tables.q(DAV2008T, sex, x)
        if x == 120:
            assert filed == 1.0 == rate
            continue
        # the cap binds at the same ages, from 110 for a man and 113 for a woman
        assert (filed == 1.0) == (rate == 1.0) == (x >= {"M": 110, "F": 113}[sex]), (sex, x)
        if abs(rate - filed) > worst:
            worst, where = abs(rate - filed), (sex, x)
    # at most 6.1e-12 below the cap, at a woman of 112 (the values package)
    assert where == ("F", 112) and float(f"{worst:.2g}") == 6.1e-12
    assert shipped_tables.q(DAV2008T, "M", 37) == pytest.approx(held[("M", 37)], abs=1e-14)


def test_klv_results_moved_within_rounding_at_its_switch():
    """The baseline of the switch against the one of the commit before: the same shape and
    keys, every value within the tolerance of a within-rounding change (``docs/core.md``,
    "Commit trailers"), and the frame is not the same bytes."""
    before, switch = klv_switch()
    old = git_bytes("show", f"{before}:{KLV_BASELINE}").decode("utf-8")
    new = (git_bytes("show", f"{switch}:{KLV_BASELINE}").decode("utf-8") if switch
           else (ROOT / KLV_BASELINE).read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location(
        "baseline_deviations_for_tables", ROOT / "tools" / "baseline_deviations.py")
    deviations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deviations)
    old_rows, new_rows = (list(csv.reader(io.StringIO(text))) for text in (old, new))
    assert old_rows[0] == new_rows[0] and len(old_rows) == len(new_rows) == 3865
    assert [row[:2] for row in old_rows] == [row[:2] for row in new_rows]
    assert old != new
    result = deviations.compare(old, new, deviations.EURO_COLUMNS[KLV])
    assert result["within"], result["detail"]
    # far inside the tolerance: a euro amount by less than a ten-millionth of a cent
    assert result["euro_max_abs"] < 1e-7 and result["other_max_rel"] < 1e-12


def test_klv_holds_no_mortality_file_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / KLV
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header if "mort" in column or column == "qx"], path
    model = product_models(KLV)
    layer = model.Data.param_layers()["tariff_type"]
    assert {item: layer[item] for item in layer if "mort" in item or "unisex" in item} == {
        "mort_be_factor": 0.75, "mort_table": DAV2008T, "unisex_mix_male": 0.5}
    assert "mort_file" not in model.Data.refs
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    assert own == ["mort_be_factor"]
    for name in ("mort_rate_tariff_at_age", "mort_rate_at_age"):
        assert model.Projection.cells[name]._is_derived(), name
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    reachable = param_usage.scan(model).reachable
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & reachable
    for space in ("Data", "Projection"):
        source = (folder / MODELS[KLV] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()",
                     "mort_rate_1st"):
            assert name not in source, (space, name)
    # no read of the factory besides the core's hooks
    cells = dict(_formula_cells(folder / MODELS[KLV] / "Projection" / "__init__.py"))
    reads = {name: ast.unparse(node) for name, cell in cells.items() for node in ast.walk(cell)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id == "tables"}
    assert reads == {}
    # every death rate of a run comes through the factory's one lookup
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0
    line = raised_line(lambda: item.mort_rate_at_age(121))
    assert line == "ValueError: table 'dav2008t_proxy': x 121 is outside its ages 0 to 120"


# The tariff rates of the values package for FRV by age, six significant digits: the 50/50
# blend of ``dav2008t_proxy`` ("Tariff new"). Its best estimate is ``BE_PACKAGE_RATES``.
FRV_TARIFF_PACKAGE_RATES = {30: 0.000630364, 40: 0.00133219, 50: 0.00315255, 65: 0.0125653}
FRV_CORE_MORT_CELLS = TABLE_HOOKS + (
    "birth_year", "mort_rate_at_age", "mort_rate_base", "mort_be_trend", "mort_rate",
    "mort_load_tariff", "mort_rate_tariff_at_age", "mort_rate_tariff_base",
    "mort_rate_tariff", "unisex_blend", "unisex_mix_male", "pols_death")


def test_frv_tariff_rate_is_the_unisex_blend_of_the_factorys_table(product_models):
    model = product_models(FRV)
    projection, tables = model.Projection, model.CoreTables
    for name in FRV_CORE_MORT_CELLS:
        assert projection.cells[name]._is_derived(), name
    assert model.Data.param("mort_table") == DAV2008T
    assert model.Data.param("unisex_mix_male") == 0.5
    by_age, seen = {}, set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.mort_table_name() == DAV2008T and item.birth_year() == 0
        assert item.unisex_mix_male() == 0.5
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            male, female = tables.q(DAV2008T, "M", x), tables.q(DAV2008T, "F", x)
            mixed = 0.5 * male + (1.0 - 0.5) * female
            assert mixed == blend(makeham_rate("M", x), makeham_rate("F", x)) < 1.0
            assert item.mort_rate_tariff_at_age(x) == mixed == item.mort_rate_tariff_base(t)
            # the neutral load
            assert item.mort_rate_tariff(t) == mixed, (point_id, t)
            assert female < mixed < male and mixed != item.mort_rate_base(t)
            by_age.setdefault(x, {})[item.sex()] = mixed
            if x in FRV_TARIFF_PACKAGE_RATES:
                assert float(f"{mixed:.6g}") == FRV_TARIFF_PACKAGE_RATES[x]
                seen.add(x)
    assert seen == set(FRV_TARIFF_PACKAGE_RATES)
    # the same whatever the point's sex: every age a man and a woman both attain
    shared = [rates for rates in by_age.values() if len(rates) == 2]
    assert len(shared) == 32 and all(rates["M"] == rates["F"] for rates in shared)
    assert (min(by_age), max(by_age)) == (25, 69)
    # the anchor of the worked example: a man of 37, the blend to twelve decimals
    anchor = projection[1]
    assert (anchor.sex(), anchor.age(0)) == ("M", 37)
    assert f"{anchor.mort_rate_tariff(0):.12f}" == "0.001048144252"


def test_frv_best_estimate_is_the_factorys_rate_on_the_own_sex_times_its_factor(product_models):
    model = product_models(FRV)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    assert cells["mort_be_factor"]._is_defined()
    assert "Override reason:" in cells["mort_be_factor"].formula.source
    assert model.Data.param("mort_be_factor") == 0.75
    seen, sexes = set(), set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex = item.sex()
        sexes.add(sex)
        assert item.mort_be_factor() == 0.75
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            rate = tables.q(DAV2008T, sex, x)
            assert rate == makeham_rate(sex, x) < 1.0
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == rate * 0.75, (point_id, t)
            # no fixed share of the tariff rate, which is the blend: below it for both sexes
            assert item.mort_rate(t) < item.mort_rate_tariff(t)
            assert item.mort_rate(t) != 0.75 * item.mort_rate_tariff(t)
            if (sex, x) in BE_PACKAGE_RATES:
                assert float(f"{item.mort_rate(t):.6g}") == BE_PACKAGE_RATES[(sex, x)]
                seen.add((sex, x))
    assert sexes == {"M", "F"}
    # every row of the package but the woman of 30: the youngest woman shipped is 35
    assert seen == set(BE_PACKAGE_RATES) - {("F", 30)}
    # at 40 the best estimate is 0.858 of the tariff rate for a man and 0.642 for a woman
    blend_40 = blend(makeham_rate("M", 40), makeham_rate("F", 40))
    assert round(0.75 * makeham_rate("M", 40) / blend_40, 3) == 0.858
    assert round(0.75 * makeham_rate("F", 40) / blend_40, 3) == 0.642
    assert f"{projection[1].mort_rate(0):.12f}" == "0.000900000000"


def test_frv_monthly_rates_are_the_linear_twelfth_of_the_annual_rates(product_models):
    model = product_models(FRV)
    projection = model.Projection
    cells = projection.cells
    for name in ("mort_rate_mth", "mort_rate_tariff_mth"):
        assert cells[name]._is_defined(), name
    assert "Override reason:" in cells["mort_rate_mth"].formula.source
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for t in range(item.t_start(), item.proj_len()):
            assert item.mort_rate_tariff_mth(t) == item.mort_rate_tariff(t) / 12.0, (point_id, t)
            assert item.mort_rate_mth(t) == item.mort_rate(t) / 12.0, (point_id, t)
            # not the core's geometric twelfth
            assert item.mort_rate_mth(t) != 1.0 - (1.0 - item.mort_rate(t)) ** (1.0 / 12.0)
        # the Risikobeitrag stands on the tariff's monthly rate
        t0 = item.t_start()
        assert item.charge_risk_pp(t0) == min(item.mort_rate_tariff_mth(t0) * item.nar_pp(t0),
                                              item.av_pp_at(t0, "AFT_WD"))


def test_frv_passes_a_table_rate_of_1_through_its_factor(tmp_path):
    """On a scratch copy whose table closes at 66, the last age the anchor attains: the annual
    best estimate and the annual tariff rate are 1 there, not 0.75 of the table rate or its
    blend, and the monthly rates their linear twelfth."""
    folder = product_copy(tmp_path, FRV)
    path = tables_file(folder, FRV)
    text = path.read_text(encoding="utf-8")
    assert text.count(f"{DAV2008T}_end_age,121,") == 1
    path.write_text(text.replace(f"{DAV2008T}_end_age,121,", f"{DAV2008T}_end_age,67,"),
                    encoding="utf-8")
    model = mx.read_model(folder / MODELS[FRV], name="FrvThruProbe")
    try:
        item, tables = model.Projection[1], model.CoreTables
        last = item.proj_len() - 1
        assert (item.sex(), item.age(last)) == ("M", 66)
        assert item.mort_be_factor() == 0.75
        assert tables.q(DAV2008T, "M", 66) == 1.0 == tables.q(DAV2008T, "F", 66)
        assert item.mort_rate_base(last) == 1.0 == item.mort_rate(last)
        assert item.mort_rate_tariff_at_age(66) == 1.0 == item.mort_rate_tariff(last)
        assert item.mort_rate_mth(last) == 1.0 / 12.0 == item.mort_rate_tariff_mth(last)
        # the year before, the factor acts on the table rate
        before = last - 12
        assert item.age(before) == 65
        assert item.mort_rate(before) == makeham_rate("M", 65) * 0.75 < 1.0
        assert item.mort_rate_tariff(before) == blend(makeham_rate("M", 65),
                                                      makeham_rate("F", 65)) < 1.0
    finally:
        model.close()


def test_frv_points_that_differ_in_sex_alone_share_the_risk_charge_and_not_the_decrements(
        tmp_path):
    """On a scratch copy whose anchor is a woman: the *Risikobeitrag* and the fund per policy
    are the man's, the tariff rate being unisex; the best estimate is her own, and the
    *Risikoergebnis* is no fixed share of the *Risikobeitrag*, where it was a quarter."""
    folder = product_copy(tmp_path, FRV)
    path = folder / "model_point_table.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[1].startswith("1,DE-FRV-0001,M,37,")
    rows[1] = rows[1].replace("1,DE-FRV-0001,M,37,", "1,DE-FRV-0001,F,37,", 1)
    path.write_text("".join(rows), encoding="utf-8")
    woman = mx.read_model(folder / MODELS[FRV], name="FrvWomanProbe")
    man = mx.read_model(PRODUCTS_DIR / FRV / MODELS[FRV], name="FrvManProbe")
    try:
        her, him = woman.Projection[1], man.Projection[1]
        assert (her.sex(), him.sex()) == ("F", "M")
        charged = 0
        for t in range(him.proj_len()):
            assert her.mort_rate_tariff(t) == him.mort_rate_tariff(t)
            assert her.mort_rate_tariff_mth(t) == him.mort_rate_tariff_mth(t)
            assert her.charge_risk_pp(t) == him.charge_risk_pp(t)
            assert her.av_pp_at(t, "BEF_DECR") == him.av_pp_at(t, "BEF_DECR")
            assert her.mort_rate(t) < him.mort_rate(t) < him.mort_rate_tariff(t)
            assert her.mort_rate_mth(t) < him.mort_rate_mth(t)
            charged += him.charge_risk_pp(t) > 0.0
        assert charged == 94
        assert her.av_maturity_pp() == him.av_maturity_pp()
        # the decrements, and with them the frame, are her own
        assert her.pols_if(him.proj_len() - 1) > him.pols_if(him.proj_len() - 1)
        shares = []
        for item in (him, her):
            frame = item.result_cf()
            charge, strain = frame["charge_risk"].sum(), frame["death_strain"].sum()
            assert 0.0 < strain < charge
            shares.append((charge - strain) / charge)
        # no fixed share: 25 % while the best estimate was 0.75 of the tariff rate
        assert [round(share, 4) for share in shares] == [0.1419, 0.3581]
    finally:
        woman.close()
        man.close()


def test_frv_holds_no_mortality_file_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / FRV
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header
                    if "mort" in column or column.startswith("qx")], path
    model = product_models(FRV)
    layer = model.Data.param_layers()["tariff_type"]
    assert {item: layer[item] for item in layer if "mort" in item or "unisex" in item} == {
        "mort_be_factor": 0.75, "mort_table": DAV2008T, "unisex_mix_male": 0.5}
    assert "mort_file" not in model.Data.refs
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    # the factor and the linear monthly split, the tariff's and the best estimate's
    assert own == ["mort_be_factor", "mort_rate_mth", "mort_rate_tariff_mth"]
    for name in ("mort_rate_tariff_at_age", "mort_rate_at_age", "mort_rate_base"):
        assert model.Projection.cells[name]._is_derived(), name
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    assert model.Data.cells["mort_table_index"]._is_derived()
    reachable = param_usage.scan(model).reachable
    assert not {"mort_table", "mort_table_dict", "mort_table_index", "omega_age"} & reachable
    for space in ("Data", "Projection"):
        source = (folder / MODELS[FRV] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()",
                     "qx_tariff"):
            assert name not in source, (space, name)
    # no read of the factory besides the core's hooks
    cells = dict(_formula_cells(folder / MODELS[FRV] / "Projection" / "__init__.py"))
    reads = {name: ast.unparse(node) for name, cell in cells.items() for node in ast.walk(cell)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id == "tables"}
    assert reads == {}
    # every death rate of a run comes through the factory's one lookup, unclamped
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0
    line = raised_line(lambda: item.mort_rate_at_age(121))
    assert line == "ValueError: table 'dav2008t_proxy': x 121 is outside its ages 0 to 120"


# --------------------------------------------------------------------------- RLV

NR, R = "dav2008t_nr_proxy", "dav2008t_r_proxy"
# The values package's rows of RLV, six significant digits: the table rate by table, sex and
# age ("New table"), the best estimate at the factor 0.75 ("BE new") and the tariff rate, the
# 50/50 blend ("Tariff new").
RLV_PACKAGE_RATES = {
    (NR, "M", 0): 0.000199056, (NR, "M", 30): 0.000578316, (NR, "M", 40): 0.0012195,
    (NR, "M", 50): 0.00288258, (NR, "M", 65): 0.0114821,
    (NR, "F", 30): 0.000430266, (NR, "F", 40): 0.000912, (NR, "F", 50): 0.00216149,
    (NR, "F", 65): 0.00862241,
    (R, "M", 0): 0.000437924, (R, "M", 30): 0.0012723, (R, "M", 40): 0.00268291,
    (R, "M", 50): 0.00634168, (R, "M", 65): 0.0252605,
    (R, "F", 30): 0.000946585, (R, "F", 40): 0.0020064, (R, "F", 50): 0.00475529,
    (R, "F", 65): 0.0189693,
}
RLV_BE_PACKAGE_RATES = {
    (NR, "M", 40): 0.000914628, (NR, "M", 50): 0.00216194, (NR, "F", 40): 0.000684,
    (NR, "F", 50): 0.00162112, (R, "M", 40): 0.00201218, (R, "M", 50): 0.00475626,
}
RLV_TARIFF_PACKAGE_RATES = {
    (NR, 30): 0.000504291, (NR, 40): 0.00106575, (NR, 50): 0.00252204, (NR, 65): 0.0100522,
    (R, 30): 0.00110944, (R, 40): 0.00234465, (R, 50): 0.00554848, (R, 65): 0.0221149,
}
RLV_ROLES = {"N": NR, "R": R}
RLV_OWN_MORT_CELLS = ["mort_be_factor", "mort_load_tariff", "mort_rate", "mort_rate_at_age",
                      "mort_rate_base", "mort_rate_blend", "mort_rate_tariff_base",
                      "mort_table_smoker"]


@pytest.mark.parametrize("table", [NR, R])
@pytest.mark.parametrize("sex", ["M", "F"])
def test_the_smoker_tables_give_their_makeham_rate_capped_at_1(shipped_tables, table, sex):
    key = sex.lower()
    a, b, c = (SHIPPED_LAYER[f"{table}_{key}_{name}"] for name in "abc")
    assert c == 1.1
    below_the_cap = 0
    for x in range(0, 120):
        rate = shipped_tables.q(table, sex, x)
        assert type(rate) is float
        assert rate == min(1.0, a + b * 1.1 ** x) == min(1.0, makeham_rate(sex, x, table)), x
        assert shipped_tables.base_rate(table, sex, x) == a + b * 1.1 ** x, x
        below_the_cap += rate < 1.0
    # the cap binds in the last ages below the closing age, as in the aggregate table
    assert 100 < below_the_cap < 120
    assert shipped_tables.q(table, sex, below_the_cap - 1) < 1.0 == shipped_tables.q(
        table, sex, below_the_cap)
    # the closing age and the ages outside the table
    rate = shipped_tables.q(table, sex, 120)
    assert rate == 1.0 and type(rate) is float
    for x in (121, -1):
        line = raised_line(lambda: shipped_tables.q(table, sex, x))
        assert line == f"ValueError: table {table!r}: x {x!r} is outside its ages 0 to 120"
    # a period table without selection
    assert shipped_tables.select_factors(table) == ()
    assert raised_line(lambda: shipped_tables.q(table, sex, 40, 1980)) == (
        f"ValueError: table {table!r}: birth_year 1980 is given, the table is a period table")
    assert raised_line(lambda: shipped_tables.q(table, sex, 40, duration=1)) == (
        f"ValueError: table {table!r}: duration 1 is given, the table has no selection")


@pytest.mark.parametrize("sex", ["M", "F"])
def test_the_smoker_tables_are_the_aggregate_table_scaled(shipped_tables, sex):
    """Non-smokers at 0.8 of ``dav2008t_proxy`` and smokers at 2.2 times non-smokers, to the
    digits of the items, at every age below the cap; the slope is the aggregate's."""
    key = sex.lower()
    for name in "ab":
        aggregate = SHIPPED_LAYER[f"{DAV2008T}_{key}_{name}"]
        assert SHIPPED_LAYER[f"{NR}_{key}_{name}"] == pytest.approx(0.8 * aggregate, rel=1e-11)
        assert SHIPPED_LAYER[f"{R}_{key}_{name}"] == pytest.approx(1.76 * aggregate, rel=1e-11)
    assert SHIPPED_LAYER[f"{NR}_{key}_c"] == SHIPPED_LAYER[f"{R}_{key}_c"] == SHIPPED_LAYER[
        f"{DAV2008T}_{key}_c"]
    for x in range(0, 100):
        non_smoker, smoker = shipped_tables.q(NR, sex, x), shipped_tables.q(R, sex, x)
        assert smoker < 1.0
        assert smoker == pytest.approx(2.2 * non_smoker, rel=1e-11), x
        assert non_smoker == pytest.approx(0.8 * shipped_tables.q(DAV2008T, sex, x), rel=1e-11)


@pytest.mark.parametrize(("table", "sex", "x"), sorted(RLV_PACKAGE_RATES))
def test_the_smoker_tables_give_the_rates_of_the_values_package(shipped_tables, table, sex, x):
    assert float(f"{shipped_tables.q(table, sex, x):.6g}") == RLV_PACKAGE_RATES[(table, sex, x)]


def rlv_points(model):
    return [model.Projection[point_id] for point_id in model.Data.model_point_table().index]


def test_rlv_maps_the_smoker_status_of_a_life_to_its_table(product_models, tmp_path):
    model = product_models(RLV)
    data = model.Data
    assert data.param("mort_nr_table") == NR and data.param("mort_r_table") == R
    statuses = set()
    for item in rlv_points(model):
        assert item.smoker_codes() == ("N", "R")
        assert item.mort_table_smoker("N") == NR and item.mort_table_smoker("R") == R
        for code in ("S", "-", "n", "", None):
            assert raised_line(lambda: item.mort_table_smoker(code)) == (
                f"ValueError: smoker status {code!r} is neither 'N' nor 'R'")
        statuses.add((item.smoker(), item.smoker2() if item.lives() == 2 else None))
        x = item.age(item.t_start())
        for sex in ("M", "F"):
            for code, table in RLV_ROLES.items():
                assert item.mort_rate_at_age(sex, code, x) == model.CoreTables.q(table, sex, x)
    assert statuses == {("N", None), ("R", None), ("N", "N")}
    # each role's choice item is read by a literal, so the usage scan sees both
    source = model.Projection.cells["mort_table_smoker"].formula.source
    assert 'data.param("mort_nr_table")' in source and 'data.param("mort_r_table")' in source
    # the second life by ``smoker2()``: a copy whose couple is a non-smoker and a smoker
    folder = product_copy(tmp_path, RLV)
    path = folder / "model_point_table.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[10].startswith("10,") and ",2,36,N," in rows[10]
    rows[10] = rows[10].replace(",2,36,N,", ",2,36,R,", 1)
    rows[1] = rows[1].replace(",M,N,", ",M,S,", 1)
    path.write_text("".join(rows), encoding="utf-8")
    copy = mx.read_model(folder / MODELS[RLV], name="RlvRoleProbe")
    try:
        item, tables = copy.Projection[10], copy.CoreTables
        assert (item.sex(), item.smoker(), item.smoker2(), item.age(0), item.age2(0)) == (
            "M", "N", "R", 38, 36)
        q_a, q_b = tables.q(NR, "M", 38), tables.q(R, "M", 36)
        assert item.mort_rate_base(0) == q_a + q_b - q_a * q_b
        assert item.mort_rate_base(0) != product_models(RLV).Projection[10].mort_rate_base(0)
        # another code is refused where the model point is read, as before the switch
        assert "ValueError" in raised_line(lambda: copy.Projection[1].mort_rate(0))
    finally:
        copy.close()


def test_rlv_tariff_rate_is_the_rating_factor_on_the_unisex_blend(product_models):
    model = product_models(RLV)
    tables = model.CoreTables
    cells = model.Projection.cells
    for name in ("mort_rate_tariff", "unisex_blend", "unisex_mix_male", "pols_tariff"):
        assert cells[name]._is_derived(), name
    for name in ("mort_load_tariff", "mort_rate_tariff_base", "mort_rate_at_age"):
        assert cells[name]._is_defined() and "Override reason:" in cells[name].formula.source
    assert model.Data.param("unisex_mix_male") == 0.5
    seen, rated = set(), set()
    for item in rlv_points(model):
        if item.lives() != 1:
            continue
        table, factor = RLV_ROLES[item.smoker()], item.rating_factor()
        rated.add(factor)
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            mixed = blend(makeham_rate("M", x, table), makeham_rate("F", x, table))
            assert mixed == blend(tables.q(table, "M", x), tables.q(table, "F", x)) < 1.0
            assert item.mort_rate_blend(t) == mixed == item.mort_rate_tariff_base(t)
            # the rating factor alone: no further load on the first-order table
            assert item.mort_load_tariff(t) == factor
            assert item.mort_rate_tariff(t) == factor * mixed, (item.point_id, t)
            assert item.mort_rate_tariff(t) != 2.25 * factor * mixed
            if (table, x) in RLV_TARIFF_PACKAGE_RATES:
                assert float(f"{mixed:.6g}") == RLV_TARIFF_PACKAGE_RATES[(table, x)]
                seen.add((table, x))
    assert rated == {1.0, 1.75}
    # no shipped point attains 65, no smoker is 30
    assert seen == set(RLV_TARIFF_PACKAGE_RATES) - {(NR, 65), (R, 30), (R, 65)}
    # points 1 and 2 differ in sex alone: one tariff rate, one premium
    man, woman = model.Projection[1], model.Projection[2]
    assert (man.sex(), woman.sex()) == ("M", "F")
    assert man.mort_rate_tariff(0) == woman.mort_rate_tariff(0)
    assert man.prem_gross_level_pp() == woman.prem_gross_level_pp()
    assert f"{man.mort_rate_tariff(0):.9f}" == "0.000719368"


def test_rlv_combines_two_lives_by_the_first_death_rule_before_any_factor(product_models):
    model = product_models(RLV)
    tables = model.CoreTables
    item = model.Projection[10]
    assert (item.lives(), item.sex(), item.smoker(), item.smoker2()) == (2, "M", "N", "N")
    assert item.mort_be_factor() == 0.75 and item.rating_factor() == 1.0
    for t in range(item.t_start(), item.proj_len()):
        x, x2 = item.age(t), item.age2(t)
        assert x2 == x - 2
        # the best estimate: the own-sex rates of the two lives
        q_a, q_b = tables.q(NR, "M", x), tables.q(NR, "M", x2)
        first = q_a + q_b - q_a * q_b
        assert item.mort_rate_base(t) == first
        assert item.mort_rate(t) == 0.75 * 1.0 * first * item.sel_lapse_factor(t)
        # not the rule on the two best estimates
        assert item.mort_rate(t) != 0.75 * q_a + 0.75 * q_b - 0.75 * q_a * 0.75 * q_b
        # the tariff rate: the blends of the two lives
        b_a = blend(tables.q(NR, "M", x), tables.q(NR, "F", x))
        b_b = blend(tables.q(NR, "M", x2), tables.q(NR, "F", x2))
        assert item.mort_rate_blend(t) == b_a + b_b - b_a * b_b
        assert item.mort_rate_tariff(t) == 1.0 * (b_a + b_b - b_a * b_b)
    assert f"{item.mort_rate_base(0):.10f}" == "0.0019262044"


def test_rlv_best_estimate_is_the_factorys_rate_on_the_own_sex_times_its_factors(
        product_models):
    model = product_models(RLV)
    tables = model.CoreTables
    cells = model.Projection.cells
    for name in ("mort_be_factor", "mort_rate", "mort_rate_base"):
        assert cells[name]._is_defined() and "Override reason:" in cells[name].formula.source
    assert cells["mort_rate_mth"]._is_derived() and cells["sel_lapse_factor"]._is_defined()
    assert model.Data.param("mort_be_factor") == 0.75
    seen, sexes = set(), set()
    for item in rlv_points(model):
        if item.lives() != 1:
            continue
        sex, table, factor = item.sex(), RLV_ROLES[item.smoker()], item.rating_factor()
        sexes.add(sex)
        assert item.mort_be_factor() == 0.75
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            rate = tables.q(table, sex, x)
            assert rate == makeham_rate(sex, x, table) < 1.0
            assert item.mort_rate_base(t) == rate == item.mort_rate_at_age(sex, item.smoker(), x)
            # the selective-lapse loading is off in the shipped tariff
            assert item.sel_lapse_factor(t) == 1.0
            assert item.mort_rate(t) == 0.75 * factor * rate * 1.0, (item.point_id, t)
            if factor == 1.0 and (table, sex, x) in RLV_BE_PACKAGE_RATES:
                assert float(f"{item.mort_rate(t):.6g}") == RLV_BE_PACKAGE_RATES[(table, sex, x)]
                seen.add((table, sex, x))
    assert sexes == {"M", "F"}
    assert seen == set(RLV_BE_PACKAGE_RATES)
    # the anchor of the worked example, a non-smoking man of 35
    anchor = model.Projection[1]
    assert (anchor.sex(), anchor.smoker(), anchor.age(0)) == ("M", "N", 35)
    assert f"{anchor.mort_rate(0):.12f}" == "0.000617950413"


def test_rlv_loads_the_best_estimate_for_selective_lapse_and_caps_it_at_1(tmp_path):
    """On a scratch copy with the selective-lapse module on: the best estimate is the factor,
    the rating factor and the loading on the table rate, and the tariff rate is not loaded;
    with a rating factor that carries the product past 1 the best estimate is 1."""
    folder = product_copy(tmp_path, RLV)
    path = folder / "param_tariff_type.csv"
    text = path.read_text(encoding="utf-8")
    assert text.count("sel_lapse_lambda,0.0,") == 1 and text.count("sel_lapse_ref,0.25,") == 1
    path.write_text(text.replace("sel_lapse_lambda,0.0,", "sel_lapse_lambda,0.3,")
                    .replace("sel_lapse_ref,0.25,", "sel_lapse_ref,0.05,"), encoding="utf-8")
    path = folder / "model_point_table.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[13].startswith("13,") and ",-,1.0,0," in rows[13]
    rows[13] = rows[13].replace(",-,1.0,0,", ",-,250.0,0,", 1)
    path.write_text("".join(rows), encoding="utf-8")
    model = mx.read_model(folder / MODELS[RLV], name="RlvSelProbe")
    try:
        item, tables = model.Projection[1], model.CoreTables
        loaded = 0
        for t in range(0, item.proj_len(), 12):
            x = item.age(t)
            factor = 1.0 + 0.3 * max(0.0, item.lapse_cum(t) - 0.05)
            assert item.sel_lapse_factor(t) == factor
            assert item.mort_rate(t) == min(1.0, 0.75 * 1.0 * tables.q(NR, "M", x) * factor)
            assert item.mort_rate_tariff(t) == blend(tables.q(NR, "M", x), tables.q(NR, "F", x))
            loaded += factor > 1.0
        assert loaded == 24
        rated = model.Projection[13]
        assert (rated.rating_factor(), rated.age(0)) == (250.0, 60)
        assert 0.75 * 250.0 * tables.q(NR, "M", 60) > 1.0 > tables.q(NR, "M", 60)
        assert rated.mort_rate(0) == 1.0
    finally:
        model.close()


def test_rlv_passes_a_table_rate_of_1_through_its_factors(tmp_path):
    """On a scratch copy whose non-smoker table closes at 59, the last age the anchor and the
    first life of the couple attain: the best estimate and the tariff rate are 1 there, for
    one life and for two, not 0.75 of the table rate, and the monthly rate is the core's
    certainty in the anniversary month."""
    folder = product_copy(tmp_path, RLV)
    path = tables_file(folder)
    text = path.read_text(encoding="utf-8")
    assert text.count(f"{NR}_end_age,121,") == 1
    path.write_text(text.replace(f"{NR}_end_age,121,", f"{NR}_end_age,60,"), encoding="utf-8")
    model = mx.read_model(folder / MODELS[RLV], name="RlvThruProbe")
    try:
        tables = model.CoreTables
        assert tables.q(NR, "M", 59) == 1.0 == tables.q(NR, "F", 59)
        for point_id, lives in ((1, 1), (10, 2)):
            item = model.Projection[point_id]
            last = item.proj_len() - 1
            assert (item.lives(), item.age(last), item.mort_be_factor()) == (lives, 59, 0.75)
            assert item.mort_rate_base(last) == 1.0 == item.mort_rate(last)
            assert item.mort_rate_blend(last) == 1.0 == item.mort_rate_tariff(last)
            assert item.mort_rate_mth(last) == 1.0 and item.mort_rate_mth(last - 1) == 0.0
            # the year before, the factor acts on the table rate
            before = last - 12
            assert item.age(before) == 58
            assert item.mort_rate(before) == 0.75 * item.mort_rate_base(before) < 0.75
            assert item.mort_rate_tariff(before) == item.mort_rate_blend(before) < 1.0
        couple = model.Projection[10]
        last = couple.proj_len() - 1
        # the second life is 57 there, below its table's end: the combined rate is set to 1
        q_b = tables.q(NR, "M", couple.age2(last))
        assert 0.0 < q_b < 1.0 and couple.mort_rate_base(last) == 1.0
    finally:
        model.close()


def test_rlv_declares_on_the_margin_of_the_tables_over_the_best_estimate(product_models):
    model = product_models(RLV)
    data = model.Data
    assert "mort_load_first" not in data.param_dict()
    source = model.Projection.cells["beitragsverrechnung_rate"].formula.source
    assert "1.0 - mort_be_factor()" in source and "data.param(\"mort_be" not in source
    declared = 0
    for item in rlv_points(model):
        if item.surplus_form() == "keine":
            assert item.beitragsverrechnung_rate() == 0.0
            continue
        share = 1.0 - item.mort_be_factor()
        assert share == 0.25
        raw = (data.param("decl_scale") * data.param("surplus_share") * share
               * item.tariff_benefit_pv() / (item.prem_gross_level_pp() * item.tariff_annuity()))
        assert item.beitragsverrechnung_rate() == min(data.param("v_max"), raw) == raw
        # the Zahlbeitrag stands at about four fifths of the Bruttobeitrag, 0.57 before
        assert 0.79 < 1.0 - item.beitragsverrechnung_rate() < 0.84
        declared += 1
    assert declared == 13
    anchor = model.Projection[1]
    assert f"{anchor.prem_gross_level_pp():.6f}" == "826.875656"
    assert f"{anchor.beitragsverrechnung_rate():.8f}" == "0.18282785"


def test_rlv_holds_no_mortality_file_column_item_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / RLV
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header
                    if "mort" in column or column.startswith("qx")], path
    model = product_models(RLV)
    layer = model.Data.param_layers()["tariff_type"]
    assert {item: layer[item] for item in layer
            if "mort" in item or "unisex" in item or "sel_lapse" in item} == {
        "mort_be_factor": 0.75, "mort_nr_table": NR, "mort_r_table": R,
        "unisex_mix_male": 0.5, "sel_lapse_lambda": 0.0, "sel_lapse_ref": 0.25}
    assert "mort_file" not in model.Data.refs
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    assert own == RLV_OWN_MORT_CELLS
    assert "mort_table_id" not in model.Projection.cells
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    assert model.Data.cells["mort_table_index"]._is_derived()
    reachable = param_usage.scan(model).reachable
    assert not {"mort_table", "mort_table_dict", "mort_table_index", "omega_age",
                "mort_table_name"} & reachable
    for space in ("Data", "Projection"):
        source = (folder / MODELS[RLV] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()",
                     "mort_table_id", "mort_load_first"):
            assert name not in source, (space, name)
    # one read of the factory, through ``q``, in the product's hook
    cells = dict(_formula_cells(folder / MODELS[RLV] / "Projection" / "__init__.py"))
    reads = {name: ast.unparse(node) for name, cell in cells.items() for node in ast.walk(cell)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id == "tables"}
    assert reads == {"mort_rate_at_age": "tables.q"}
    # every death rate of a run comes through the factory's one lookup, unclamped
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0
    line = raised_line(lambda: item.mort_rate_at_age("M", "N", 121))
    assert line == "ValueError: table 'dav2008t_nr_proxy': x 121 is outside its ages 0 to 120"


# --------------------------------------------------------------------------- Basis

BASIS = "basisrente"
# The values package's rate rows of Basis on ``dav2004r_proxy`` by (sex, age, birth year),
# six significant digits: "New table" and "BE new", the best estimate at the factor 1.15.
BASIS_PACKAGE_RATES = {
    ("M", 65, 1962): (0.00458344, 0.00527096), ("M", 80, 1962): (0.0175643, 0.0201989),
    ("M", 95, 1962): (0.106244, 0.12218), ("F", 65, 1962): (0.00275006, 0.00316257),
    ("F", 80, 1962): (0.0105386, 0.0121193), ("F", 95, 1962): (0.0637461, 0.0733081),
    ("M", 40, 1990): (0.000312702, 0.000359608), ("M", 50, 1990): (0.000689298, 0.000792692),
    ("M", 65, 1990): (0.0022559, 0.00259429), ("M", 80, 1990): (0.00974126, 0.0112024),
    ("M", 95, 1990): (0.0792445, 0.0911312), ("F", 40, 1990): (0.000187621, 0.000215765),
    ("F", 50, 1990): (0.000413579, 0.000475615), ("F", 65, 1990): (0.00135354, 0.00155657),
    ("F", 80, 1990): (0.00584475, 0.00672147), ("F", 95, 1990): (0.0475467, 0.0546787),
}
BASIS_CORE_MORT_CELLS = TABLE_HOOKS + (
    "mort_rate_at_age", "mort_rate_base", "mort_be_trend", "mort_rate", "mort_rate_mth")


@pytest.mark.parametrize(("sex", "x", "birth_year"), sorted(BASIS_PACKAGE_RATES))
def test_basis_rates_are_the_values_packages(shipped_tables, sex, x, birth_year):
    rate = shipped_tables.q(DAV2004R, sex, x, birth_year)
    table, best = BASIS_PACKAGE_RATES[(sex, x, birth_year)]
    assert float(f"{rate:.6g}") == table
    assert float(f"{min(1.0, 1.15 * rate):.6g}") == best


def test_basis_best_estimate_is_the_factorys_rate_on_the_own_sex_times_its_factor(
        product_models):
    model = product_models(BASIS)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in BASIS_CORE_MORT_CELLS:
        assert cells[name]._is_derived(), name
    assert cells["mort_be_factor"]._is_defined()
    assert model.Data.param("mort_table") == DAV2004R
    assert model.Data.param("mort_be_factor") == 1.15
    certain, capped, sexes = set(), set(), set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex, cohort = item.sex(), item.birth_year()
        sexes.add(sex)
        assert item.mort_table_name() == DAV2004R and item.mort_be_factor() == 1.15
        for t in range(item.t_start(), item.proj_len()):
            x = item.age(t)
            rate = tables.q(DAV2004R, sex, x, cohort)
            assert rate == r_rate(sex, x, cohort), (point_id, t)
            assert item.mort_rate_at_age(x) == rate == item.mort_rate_base(t)
            assert item.mort_rate(t) == min(1.0, 1.15 * rate), (point_id, t)
            if rate == 1.0:
                certain.add((sex, x))
            elif rate * 1.15 >= 1.0:
                capped.add((sex, x))
    assert sexes == {"M", "F"}
    # the cohorts 1958 to 1997: the table's cap binds from 114 for a man and 118 for a woman,
    # its closure at 120; the factor reaches 1 a year earlier
    assert certain == ({("M", x) for x in range(114, 121)} | {("F", x) for x in range(118, 121)})
    assert capped == {("M", 113), ("F", 117)}
    # every death rate of the run came through the factory's one lookup, at a birth year
    held = [key for key in tables.q if key[0] == DAV2004R]
    assert held and all(key[3] in range(1958, 1998) and key[4] is None for key in held)
    # a man and a woman of equal age and birth year: the best estimate is the own sex's
    item = projection[1]
    for x in (45, 67, 85, 100):
        male, female = item.mort_rate_table("M", x), item.mort_rate_table("F", x)
        assert female == pytest.approx(0.6 * male, rel=1e-8) and female < male
        assert item.mort_rate_at_age(x) == male


def test_basis_points_that_differ_in_sex_alone_share_the_annuity_and_not_the_decrements(
        tmp_path):
    """On a scratch copy whose anchor is a woman: the fund and the annuity per annuitant are
    the man's, the guaranteed *Rentenfaktor* being a model-point and table fact and no rate of
    the factory; the best estimate is her own."""
    folder = product_copy(tmp_path, BASIS)
    path = folder / "model_point_table.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[1].startswith("1,DE-BAS-0001,M,45,2027,")
    rows[1] = rows[1].replace("1,DE-BAS-0001,M,45,2027,", "1,DE-BAS-0001,F,45,2027,", 1)
    path.write_text("".join(rows), encoding="utf-8")
    woman = mx.read_model(folder / MODELS[BASIS], name="BasisWomanProbe")
    man = mx.read_model(PRODUCTS_DIR / BASIS / MODELS[BASIS], name="BasisManProbe")
    try:
        her, him = woman.Projection[1], man.Projection[1]
        assert (her.sex(), him.sex()) == ("F", "M")
        assert her.birth_year() == him.birth_year() == 1982
        for t in range(0, him.proj_len(), 12):
            assert her.mort_rate(t) < him.mort_rate(t) or him.mort_rate(t) == 1.0, t
        conv = him.k_conv()
        assert her.rentenfaktor_applied() == him.rentenfaktor_applied()
        assert her.ann_pp(conv) == pytest.approx(him.ann_pp(conv), rel=1e-12)
        assert her.pols_if(12 * conv) > him.pols_if(12 * conv)
        assert her.result_cf()["claims_annuity"].sum() > him.result_cf()["claims_annuity"].sum()
    finally:
        woman.close()
        man.close()


def test_basis_runs_to_the_tables_end_age_and_closes_there(product_models):
    model = product_models(BASIS)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in ("birth_year", "omega_age", "horizon_age"):
        assert cells[name]._is_defined(), name
        assert "Override reason:" in cells[name].formula.source, name
    assert tables.end_age(DAV2004R) == 121
    rows = 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.omega_age() == 121 == item.omega_age_table() == item.horizon_age()
        # one year less than the file's limiting age 122 gave before the switch
        assert item.proj_len_y() == 121 - item.age(0)
        assert item.proj_len() == 12 * item.proj_len_y()
        last = item.proj_len() - 1
        assert item.age(last) == 120 and item.age(last - 12) == 119
        # the closing age: the table's certainty, in the anniversary month
        assert tables.q(DAV2004R, item.sex(), 120, item.birth_year()) == 1.0
        for t in range(last - 11, last + 1):
            assert item.mort_rate(t) == 1.0
            assert item.mort_rate_mth(t) == (1.0 if t == last else 0.0), (point_id, t)
        assert item.pols_if(item.proj_len()) == 0.0
        rows += item.proj_len()
    with (ROOT / "baseline" / BASIS / "result_cf.csv").open(encoding="utf-8") as handle:
        assert rows == sum(1 for _line in handle) - 1 == 12132 - 14 * 12
    # age 121 is not reached; the table raises there and nothing clamps it
    line = raised_line(lambda: projection[1].mort_rate_at_age(121))
    assert line == "ValueError: table 'dav2004r_proxy': x 121 is outside its ages 0 to 120"


def test_basis_reads_the_table_at_the_cohort_of_every_point(product_models):
    model = product_models(BASIS)
    projection = model.Projection
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.birth_year() == item.issue_year() - item.issue_age()
        for t in range(0, item.proj_len(), 12):
            # the table's calendar year, birth year plus attained age, is the projection
            # year's, on the valuation clock of an in-force point as of new business
            assert item.birth_year() + item.age(t) == item.calendar_year(t), (point_id, t)
    # the paying and the premium-free cohort of the 2009 contract issued at 40, in force 18
    # years at the valuation date
    for point_id in (6, 14):
        item = projection[point_id]
        assert (item.issue_year(), item.issue_age(), item.duration_init()) == (2009, 40, 18)
        assert item.birth_year() == 1969
        assert item.age(0) == 58 and item.calendar_year(0) == 2027


def test_basis_holds_no_mortality_file_item_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / BASIS
    assert not (folder / "mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header
                    if column.startswith("mort") or column in ("qx", "trend")], path
    model = product_models(BASIS)
    layer = model.Data.param_layers()["tariff_type"]
    assert "mort_base_year" not in layer and "unisex_mix_male" not in layer
    assert {item: layer[item] for item in layer if "mort" in item or "unisex" in item} == {
        "mort_table": DAV2004R, "mort_be_factor": 1.15}
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if name.startswith("mort") and cell._is_defined())
    assert own == ["mort_be_factor"]
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    assert model.Data.cells["mort_table_index"]._is_derived()
    usage = param_usage.scan(model)
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & usage.reachable
    assert "mort_base_year" not in usage.reads and "unisex_mix_male" not in usage.reads
    for space in ("Data", "Projection"):
        source = (folder / MODELS[BASIS] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "mort_file", "mort_table_dict", "mort_table()",
                     "mort_base_year", "mort_table_index", "1.085", "0.014"):
            assert name not in source, (space, name)
    # no read of the factory besides the core's hooks
    cells = dict(_formula_cells(folder / MODELS[BASIS] / "Projection" / "__init__.py"))
    reads = {name: ast.unparse(node) for name, cell in cells.items() for node in ast.walk(cell)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id == "tables"}
    assert reads == {}
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0


# --------------------------------------------------------------------------- Riester

RIESTER = "riester_rente"
# The values package's rate rows of Riester, six significant digits. The accumulation on
# ``dav2008t_proxy`` by (sex, age): "New table" and "BE new" at the factor 0.75. The payout on
# ``dav2004r_proxy`` by (sex, age, birth year): "New table", "BE new" at the factor 1.15 and
# "Tariff new", the blend of 45 % men and 55 % women.
RIESTER_ACCUM_PACKAGE_RATES = {
    ("M", 30): (0.000722895, 0.000542171), ("M", 40): (0.00152438, 0.00114328),
    ("M", 50): (0.00360323, 0.00270242), ("M", 65): (0.0143526, 0.0107644),
    ("F", 30): (0.000537832, 0.000403374), ("F", 40): (0.00114, 0.000855),
    ("F", 50): (0.00270187, 0.0020264), ("F", 65): (0.010778, 0.00808351),
}
RIESTER_PAYOUT_PACKAGE_RATES = {
    ("M", 65, 1965): (0.0042482, 0.00488543, 0.0033136),
    ("M", 80, 1965): (0.0164892, 0.0189626, 0.0128616),
    ("M", 95, 1965): (0.102958, 0.118402, 0.0803072),
    ("F", 65, 1965): (0.00254892, 0.00293126, 0.0033136),
    ("F", 80, 1965): (0.00989352, 0.0113775, 0.0128616),
    ("F", 95, 1965): (0.0617748, 0.071041, 0.0803072),
    ("M", 65, 1995): (0.00198767, 0.00228582, 0.00155038),
    ("M", 80, 1995): (0.00876795, 0.0100831, 0.006839),
    ("M", 95, 1995): (0.0752023, 0.0864826, 0.0586578),
    ("F", 65, 1995): (0.0011926, 0.00137149, 0.00155038),
    ("F", 80, 1995): (0.00526077, 0.00604989, 0.006839),
    ("F", 95, 1995): (0.0451214, 0.0518896, 0.0586578),
}
RIESTER_CORE_MORT_CELLS = ("mort_table_name", "mort_rate_at_age", "mort_rate_base",
                           "mort_rate_mth", "unisex_blend", "unisex_mix_male")


def six(value: float) -> float:
    """A rate to the package's six significant digits."""
    return float(f"{value:.6g}")


@pytest.mark.parametrize(("sex", "x"), sorted(RIESTER_ACCUM_PACKAGE_RATES))
def test_riester_accumulation_rates_are_the_values_packages(shipped_tables, sex, x):
    rate = shipped_tables.q(DAV2008T, sex, x)
    table, best = RIESTER_ACCUM_PACKAGE_RATES[(sex, x)]
    assert six(rate) == table and six(min(1.0, 0.75 * rate)) == best


@pytest.mark.parametrize(("sex", "x", "birth_year"), sorted(RIESTER_PAYOUT_PACKAGE_RATES))
def test_riester_payout_rates_are_the_values_packages(shipped_tables, sex, x, birth_year):
    rate = shipped_tables.q(DAV2004R, sex, x, birth_year)
    table, best, tariff = RIESTER_PAYOUT_PACKAGE_RATES[(sex, x, birth_year)]
    assert six(rate) == table and six(min(1.0, 1.15 * rate)) == best
    blend = (0.45 * shipped_tables.q(DAV2004R, "M", x, birth_year)
             + 0.55 * shipped_tables.q(DAV2004R, "F", x, birth_year))
    assert six(blend) == tariff


def test_riester_accumulation_best_estimate_is_the_period_tables_rate_times_its_factor(
        product_models):
    model = product_models(RIESTER)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in RIESTER_CORE_MORT_CELLS:
        assert cells[name]._is_derived(), name
    for name in ("mort_rate_table", "birth_year", "mort_rate", "mort_be_factor"):
        assert cells[name]._is_defined(), name
        assert "Override reason:" in cells[name].formula.source, name
    assert model.Data.param("mort_table") == DAV2008T
    assert model.Data.param("mort_be_factor") == 0.75
    sexes, months = set(), 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex = item.sex()
        sexes.add(sex)
        assert item.mort_table_name() == DAV2008T and item.mort_be_factor() == 0.75
        for t in range(0, item.t_conv()):
            x = item.age(t)
            rate = tables.q(DAV2008T, sex, x)
            assert rate == makeham_rate(sex, x) < 1.0, (point_id, t)
            assert item.mort_rate_table(sex, x) == item.mort_rate_at_age(x) == rate
            assert item.mort_rate_base(t) == rate
            assert item.mort_rate(t) == min(1.0, 0.75 * rate), (point_id, t)
            months += 1
    assert sexes == {"M", "F"} and months > 0
    # the main role is never read with a birth year, though ``birth_year()`` is overridden
    held = [key for key in tables.q if key[0] == DAV2008T]
    assert held and all(key[3] is None and key[4] is None for key in held)
    assert projection[1].birth_year() != 0
    # a man and a woman of equal age differ in the accumulation (points 8 and 1)
    man, woman = projection[8], projection[1]
    assert (man.sex(), woman.sex()) == ("M", "F") and man.age(0) == woman.age(0)
    for t in range(0, man.t_conv(), 12):
        assert woman.mort_rate(t) < man.mort_rate(t), t


def test_riester_payout_best_estimate_is_the_generational_tables_rate_times_its_factor(
        product_models):
    model = product_models(RIESTER)
    projection, tables = model.Projection, model.CoreTables
    assert model.Data.param("annuity_mort_table") == DAV2004R
    assert model.Data.param("annuity_mort_be_factor") == 1.15
    certain, capped, sexes, cohorts = set(), set(), set(), set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        sex, cohort = item.sex(), item.birth_year()
        sexes.add(sex)
        cohorts.add(cohort)
        for t in range(item.t_conv(), item.proj_len()):
            x = item.age(t)
            rate = tables.q(DAV2004R, sex, x, cohort)
            assert rate == r_rate(sex, x, cohort), (point_id, t)
            assert item.annuity_mort_rate(sex, x) == rate
            assert item.mort_rate(t) == min(1.0, 1.15 * rate), (point_id, t)
            if rate == 1.0:
                # 1 and not 1.15 capped: the table rate of 1 passes through the factor
                certain.add((sex, x))
            elif rate * 1.15 >= 1.0:
                capped.add((sex, x))
    assert sexes == {"M", "F"} and min(cohorts) == 1966 and max(cohorts) == 2003
    # the table's cap binds from 114 for a man and 118 for a woman of these cohorts, its
    # closure at 120; the factor reaches 1 a year earlier
    assert certain == ({("M", x) for x in range(114, 121)} | {("F", x) for x in range(118, 121)})
    assert capped == {("M", 113), ("F", 117)}
    held = [key for key in tables.q if key[0] == DAV2004R]
    assert held and all(key[3] in cohorts and key[4] is None for key in held)
    # a man and a woman of equal age and birth year differ in the payout (points 8 and 1)
    man, woman = projection[8], projection[1]
    assert man.birth_year() == woman.birth_year() == 1977
    for t in range(man.t_conv(), man.proj_len() - 12 * 8, 12):
        assert woman.mort_rate(t) < man.mort_rate(t), t


def riester_annuity_factor(item) -> float:
    """The annuity-due factor at *Rentenbeginn* from the table's rows: survivorship on the
    blend of 45 % men and 55 % women of ``dav2004r_proxy`` at the point's birth year, at
    factor 1, from the age at conversion to the closing age 120, less 11/24."""
    v = 1.0 / (1.0 + 0.01)
    w = 0.45
    cohort = item.issue_year() - item.issue_age()
    total, kp = 0.0, 1.0
    for k, x in enumerate(range(item.age_y(item.k_conv()), 121)):
        total += v ** k * kp
        kp *= 1.0 - (w * r_rate("M", x, cohort) + (1.0 - w) * r_rate("F", x, cohort))
    assert kp == 0.0
    return total - 11 / 24


def test_riester_annuity_factor_runs_on_the_unisex_blend_of_the_annuitant_table(
        product_models):
    model = product_models(RIESTER)
    projection = model.Projection
    assert model.Data.param("unisex_mix_male") == 0.45
    assert projection.cells["ann_factor"]._is_defined()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.unisex_mix_male() == 0.45
        assert item.ann_factor() == pytest.approx(riester_annuity_factor(item), rel=1e-13)
    # the anchor, a woman of 67 in 2044, born 1977, and point 8, a man of the same age and
    # birth year: one annuity factor, one current Rentenfaktor
    woman, man = projection[1], projection[8]
    assert (woman.sex(), man.sex()) == ("F", "M")
    assert woman.age_y(woman.k_conv()) == 67 and woman.calendar_year_y(woman.k_conv()) == 2044
    assert woman.ann_factor() == man.ann_factor()
    assert round(woman.ann_factor(), 8) == 24.78315099
    assert woman.rentenfaktor_curr() == man.rentenfaktor_curr()
    assert round(woman.rentenfaktor_curr(), 6) == 23.537497
    # the guaranteed Rentenfaktor binds on every point, as before the switch
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.rentenfaktor_curr() < item.rentenfaktor_guar() == item.rentenfaktor_applied()


def test_riester_runs_to_the_tables_end_age_and_closes_there(product_models):
    model = product_models(RIESTER)
    projection, tables = model.Projection, model.CoreTables
    cells = projection.cells
    for name in ("omega_age", "horizon_age"):
        assert cells[name]._is_defined(), name
        assert "Override reason:" in cells[name].formula.source, name
    assert tables.end_age(DAV2004R) == 121 == tables.end_age(DAV2008T)
    rows = 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.omega_age() == 121 == item.horizon_age()
        # ten years more than the files' limiting age 111 gave before the switch
        assert item.proj_len_y() == 121 - item.age(0)
        assert item.proj_len() == 12 * item.proj_len_y()
        last = item.proj_len() - 1
        assert item.age(last) == 120 and item.age(last - 12) == 119
        # the closing age: the table's certainty, in the anniversary month
        assert tables.q(DAV2004R, item.sex(), 120, item.birth_year()) == 1.0
        for t in range(last - 11, last + 1):
            assert item.mort_rate(t) == 1.0
            assert item.mort_rate_mth(t) == (1.0 if t == last else 0.0), (point_id, t)
        assert item.pols_if(item.proj_len()) == 0.0
        rows += item.proj_len()
    with (ROOT / "baseline" / RIESTER / "result_cf.csv").open(encoding="utf-8") as handle:
        assert rows == sum(1 for _line in handle) - 1 == 9456 + 13 * 120
    # age 121 is not reached; both tables raise there and nothing clamps them
    item = projection[1]
    line = raised_line(lambda: item.mort_rate_at_age(121))
    assert line == "ValueError: table 'dav2008t_proxy': x 121 is outside its ages 0 to 120"
    line = raised_line(lambda: item.annuity_mort_rate("F", 121))
    assert line == "ValueError: table 'dav2004r_proxy': x 121 is outside its ages 0 to 120"


def test_riester_reads_the_annuitant_table_at_the_cohort_of_every_point(product_models):
    model = product_models(RIESTER)
    projection = model.Projection
    in_force = 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.birth_year() == item.issue_year() - item.issue_age()
        in_force += item.duration_init() > 0
        for t in range(0, item.proj_len(), 12):
            # the table's calendar year, birth year plus attained age, is the projection
            # year's, on the valuation clock of an in-force point as of new business
            assert item.birth_year() + item.age(t) == item.calendar_year(t), (point_id, t)
    assert in_force > 0
    # the anchor: issued 2024 at 47, in force three years at the valuation date
    item = projection[1]
    assert (item.issue_year(), item.issue_age(), item.duration_init()) == (2024, 47, 3)
    assert item.birth_year() == 1977 and item.calendar_year(0) == 2027


def test_riester_holds_no_mortality_file_item_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / RIESTER
    assert not (folder / "mort_table_accum.csv").exists()
    assert not (folder / "annuity_mort_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header if column.startswith("mort")
                    or column in ("qx", "qx_base", "improvement")], path
    model = product_models(RIESTER)
    layer = model.Data.param_layers()["tariff_type"]
    assert "mort_base_year" not in layer
    assert {item: layer[item] for item in layer if "mort" in item or "unisex" in item} == {
        "mort_table": DAV2008T, "mort_be_factor": 0.75, "annuity_mort_table": DAV2004R,
        "annuity_mort_be_factor": 1.15, "unisex_mix_male": 0.45}
    assert not [name for name in model.Data.refs if "mort" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if "mort" in name and cell._is_defined())
    assert own == ["annuity_mort_rate", "mort_be_factor", "mort_rate", "mort_rate_table"]
    assert not [name for name, cell in model.Data.cells.items()
                if "mort" in name and cell._is_defined()]
    assert model.Data.cells["mort_table_index"]._is_derived()
    for name in ("annuity_mort_table", "annuity_mort_table_dict"):
        assert name not in model.Data.cells, name
    usage = param_usage.scan(model)
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & usage.reachable
    assert "mort_base_year" not in usage.reads
    for space in ("Data", "Projection"):
        source = (folder / MODELS[RIESTER] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table_accum.csv", "annuity_mort_table.csv", "mort_file",
                     "annuity_mort_file", "mort_table_dict", "mort_table()",
                     "annuity_mort_table_dict", "mort_base_year", "mort_table_index",
                     "\"improvement\"", "qx_base"):
            assert name not in source, (space, name)
    # its reads of the factory: the period table without a birth year in its override of
    # ``mort_rate_table``, the annuitant table at the birth year in its payout hook, and the
    # end age of the annuitant table in ``omega_age``
    cells = dict(_formula_cells(folder / MODELS[RIESTER] / "Projection" / "__init__.py"))
    reads = {name: sorted(ast.unparse(node) for node in ast.walk(cell)
                          if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                          and node.value.id == "tables")
             for name, cell in cells.items()}
    assert {name: found for name, found in reads.items() if found} == {
        "mort_rate_table": ["tables.q"], "annuity_mort_rate": ["tables.q"],
        "omega_age": ["tables.end_age"]}
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0


# --------------------------------------------------------------------------- Sofort

# The values package's rate rows of Sofort on ``dav2004r_proxy`` by (sex, age, birth year),
# six significant digits: "New table", "BE new", ``thru(1.2 * T, q)`` with the trend term at
# 0.8 of the table's trend, and "Tariff new", the blend of 45 % men and 55 % women.
SOFORT_PACKAGE_RATES = {
    ("M", 80, 1947): (0.0240869, 0.0317346, 0.0187878),
    ("M", 95, 1947): (0.124313, 0.161247, 0.0969643),
    ("F", 80, 1947): (0.0144521, 0.0190407, 0.0187878),
    ("F", 95, 1947): (0.0745879, 0.0967483, 0.0969643),
    ("M", 65, 1962): (0.00458344, 0.00615524, 0.00357508),
    ("M", 80, 1962): (0.0175643, 0.0246629, 0.0137001),
    ("M", 95, 1962): (0.106244, 0.142226, 0.08287),
    ("F", 65, 1962): (0.00275006, 0.00369314, 0.00357508),
    ("F", 80, 1962): (0.0105386, 0.0147977, 0.0137001),
    ("F", 95, 1962): (0.0637461, 0.0853354, 0.08287),
}
# The frame lengths of the fourteen points before the switch, which the switch keeps: the end
# age 121 of the table is the limiting age the item ``omega_age`` gave.
SOFORT_PROJ_LEN = {1: 672, 2: 672, 3: 672, 4: 708, 5: 636, 6: 708, 7: 672, 8: 588, 9: 672,
                   10: 672, 11: 432, 12: 732, 13: 612, 14: 672}


def sofort_trend_term(sex: str, x: int, birth_year: int) -> float:
    """The best-estimate trend term from the table's rows, in the float operations of
    Sofort's ``mort_be_trend``: ``((1 - 0.8 tr) / (1 - tr)) ** (g + x - 2005)``."""
    tr = linear_trend(x)
    years = birth_year + x - SHIPPED_LAYER[f"{DAV2004R}_base_year"]
    return ((1.0 - 0.8 * tr) / (1.0 - tr)) ** years


def sofort_best_estimate(sex: str, x: int, birth_year: int) -> float:
    """``thru(1.2 * T, q)``: 1 where the table rate is 1, else ``min(1, 1.2 * T * q)``."""
    rate = r_rate(sex, x, birth_year)
    if rate >= 1.0:
        return 1.0
    return min(1.0, 1.2 * sofort_trend_term(sex, x, birth_year) * rate)


@pytest.mark.parametrize(("sex", "x", "birth_year"), sorted(SOFORT_PACKAGE_RATES))
def test_sofort_rates_are_the_values_packages(shipped_tables, sex, x, birth_year):
    rate = shipped_tables.q(DAV2004R, sex, x, birth_year)
    table, best, tariff = SOFORT_PACKAGE_RATES[(sex, x, birth_year)]
    assert six(rate) == table
    assert six(sofort_best_estimate(sex, x, birth_year)) == best
    # the package's form below the cap: 1.2 times the base rate at 0.8 of the trend
    base = makeham_rate(sex, x, DAV2004R)
    years = birth_year + x - 2005
    assert six(1.2 * base * (1.0 - 0.8 * linear_trend(x)) ** years) == best
    blend = (0.45 * shipped_tables.q(DAV2004R, "M", x, birth_year)
             + 0.55 * shipped_tables.q(DAV2004R, "F", x, birth_year))
    assert six(blend) == tariff


def sofort_lives(item) -> tuple[int, ...]:
    """The lives of a point: the annuitant, and the second life where a survivor's annuity
    is in force."""
    return (1, 2) if item.surv_pct() > 0.0 else (1,)


def test_sofort_best_estimate_is_the_tables_rate_times_its_factor_and_trend_term(
        product_models):
    model = product_models(SOFORT)
    projection = model.Projection
    cells = projection.cells
    for name in ("omega_age", "mort_be_factor", "mort_be_trend", "mort_rate", "mort_rate_mth",
                 "birth_year"):
        assert cells[name]._is_defined(), name
        assert "Override reason:" in cells[name].formula.source, name
    for name in ("mort_table_name", "omega_age_table", "unisex_blend", "unisex_mix_male"):
        assert cells[name]._is_derived(), name
    assert model.Data.param("mort_table") == DAV2004R
    assert model.Data.param("mort_be_factor") == 1.2
    assert model.Data.param("mort_be_trend_factor") == 0.8
    certain, months, sexes = set(), 0, set()
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.mort_table_name() == DAV2004R and item.mort_be_factor() == 1.2
        for life in sofort_lives(item):
            sex, cohort = item.sex(life), item.birth_year(life)
            sexes.add(sex)
            for t in range(item.t_start(), item.proj_len()):
                x = item.age(t, life)
                if x >= 121:
                    continue
                rate = r_rate(sex, x, cohort)
                assert item.mort_rate_gen(x, sex, cohort) == rate, (point_id, life, t)
                expected = (1.0 if rate >= 1.0
                            else min(1.0, 1.2 * sofort_trend_term(sex, x, cohort) * rate))
                assert item.mort_rate(t, life) == expected, (point_id, life, t)
                if rate == 1.0:
                    # 1 and not 1.2 capped: the table rate of 1 passes through the factors
                    certain.add((sex, x))
                if x >= 120:
                    assert item.mort_be_trend(t, life) == 1.0
                months += 1
    assert sexes == {"M", "F"} and months > 0
    assert ("M", 120) in certain and ("F", 120) in certain
    # a woman's table rate is 0.6 of a man's at equal age and birth year
    item = projection[1]
    assert item.mort_rate_gen(65, "F", 1962) == pytest.approx(
        0.6 * item.mort_rate_gen(65, "M", 1962), rel=1e-8)


@pytest.mark.parametrize("x", [65, 80, 95])
def test_sofort_trend_term_is_0_8_of_the_tables_trend(product_models, x):
    model = product_models(SOFORT)
    tables = model.CoreTables
    item = model.Projection[1]
    assert (item.sex(), item.birth_year(), item.age(0)) == ("M", 1962, 65)
    t = 12 * (x - 65)
    assert item.age(t) == x
    tr = tables.trend(DAV2004R, "M", x)
    assert tr == linear_trend(x) > 0.0
    expected = ((1.0 - 0.8 * tr) / (1.0 - tr)) ** (1962 + x - 2005)
    assert item.mort_be_trend(t) == expected == sofort_trend_term("M", x, 1962)
    # the best estimate improves more slowly than the table, so after the base year the
    # term lifts the table rate: above 1, and the more the further the calendar year
    assert expected > 1.0
    assert item.mort_be_trend(t) * item.mort_rate_gen(x, "M", 1962) == pytest.approx(
        SHIPPED_LAYER[f"{DAV2004R}_m_b"] * 1.11 ** x * (1.0 - 0.8 * tr) ** (1962 + x - 2005),
        rel=1e-12)


def test_sofort_tariff_rate_is_the_unisex_blend_at_the_cohort(tmp_path, product_models):
    model = product_models(SOFORT)
    projection = model.Projection
    assert model.Data.param("unisex_mix_male") == 0.45
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        for life in sofort_lives(item):
            cohort = item.birth_year(life)
            for t in range(0, item.proj_len(), 12):
                x = item.age(t, life)
                if x >= 121:
                    continue
                blend = 0.45 * r_rate("M", x, cohort) + (1.0 - 0.45) * r_rate("F", x, cohort)
                assert item.mort_rate_tariff(t, life) == blend, (point_id, life, t)
    # a scratch copy whose anchor is a woman: the tariff rate, the annuity factor and the
    # guaranteed annuity are the man's, the best estimate and the decrements her own
    folder = product_copy(tmp_path, SOFORT)
    path = folder / "model_point_table.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert rows[1].startswith("1,SOF-000001,single,100000.00,65,2027,1962,M,")
    rows[1] = rows[1].replace(",1962,M,", ",1962,F,", 1)
    path.write_text("".join(rows), encoding="utf-8")
    woman = mx.read_model(folder / MODELS[SOFORT], name="SofortWomanProbe")
    try:
        her, him = woman.Projection[1], projection[1]
        assert (her.sex(), him.sex()) == ("F", "M")
        for t in range(0, him.proj_len(), 12):
            assert her.mort_rate_tariff(t) == him.mort_rate_tariff(t), t
        assert her.annuity_factor() == him.annuity_factor()
        assert her.annuity_pp_derived() == him.annuity_pp_derived()
        for t in range(0, him.proj_len() - 12 * 8, 12):
            assert her.mort_rate(t) < him.mort_rate(t), t
        assert her.lives_if(240) > him.lives_if(240)
    finally:
        woman.close()


def test_sofort_reads_no_rate_past_the_end_age_of_a_joint_life_frame(product_models):
    model = product_models(SOFORT)
    projection, tables = model.Projection, model.CoreTables
    past = 0
    for point_id, older in ((4, 1), (5, 2)):
        item = projection[point_id]
        assert item.surv_pct() > 0.0
        assert item.proj_len() == SOFORT_PROJ_LEN[point_id]
        last = item.proj_len() - 1
        assert item.age(last, older) > 120
        for t in range(item.t_start(), item.proj_len()):
            if item.age(t, older) >= 121:
                assert item.mort_rate(t, older) == 1.0
                assert item.mort_rate_tariff(t, older) == 1.0
                assert item.mort_rate_mth(t, older) == 1.0
                assert item.lives_if(t, older) == 0.0
                past += 1
        item.result_cf()
    assert past == 12 * 3 + 12 * 2
    # the guard returns 1 without calling ``q``: no age above 120 reached the factory
    held = [key for key in tables.q if key[0] == DAV2004R]
    assert held and max(key[2] for key in held) == 120
    # the table itself raises there, and nothing clamps it
    line = raised_line(lambda: tables.q(DAV2004R, "M", 121, 1962))
    assert line == "ValueError: table 'dav2004r_proxy': x 121 is outside its ages 0 to 120"
    assert projection[4].mort_rate_gen(121, "M", 1962) == 1.0
    assert projection[4].mort_rate_gen(121, "U", 1962) == 1.0


def test_sofort_second_life_without_a_survivors_annuity_reads_nothing(product_models):
    model = product_models(SOFORT)
    projection = model.Projection
    without = 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        if item.surv_pct() > 0.0:
            continue
        without += 1
        for t in (item.t_start(), item.t_start() + 12, item.proj_len() - 1):
            assert item.mort_rate(t, 2) == 0.0
            assert item.mort_rate_tariff(t, 2) == 0.0
            assert item.lives_if(t, 2) == 0.0
    assert without == 12


def test_sofort_runs_to_the_tables_end_age_with_its_frames_unchanged(product_models):
    model = product_models(SOFORT)
    projection, tables = model.Projection, model.CoreTables
    assert tables.end_age(DAV2004R) == 121
    rows = 0
    for point_id in model.Data.model_point_table().index:
        item = projection[point_id]
        assert item.omega_age() == 121 == item.omega_age_table()
        assert type(item.omega_age()) is int
        for life in sofort_lives(item):
            assert item.horizon_mths(life) == 12 * (121 - item.issue_age(life))
        assert item.proj_len() == SOFORT_PROJ_LEN[point_id]
        rows += item.proj_len() - item.t_start()
    with (ROOT / "baseline" / SOFORT / "result_cf.csv").open(encoding="utf-8") as handle:
        assert rows == sum(1 for _line in handle) - 1 == 8940


def test_sofort_holds_no_mortality_file_item_reference_or_formula(product_models):
    folder = PRODUCTS_DIR / SOFORT
    assert not (folder / "mort_table.csv").exists()
    assert not (folder / "improvement_table.csv").exists()
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert not [column for column in header if column.startswith("mort")
                    or column == "improve_rate"], path
    model = product_models(SOFORT)
    layer = model.Data.param_layers()["tariff_type"]
    assert "mort_base_year" not in layer and "omega_age" not in layer
    assert {item: layer[item] for item in layer if "mort" in item or "unisex" in item} == {
        "mort_table": DAV2004R, "mort_be_factor": 1.2, "mort_be_trend_factor": 0.8,
        "unisex_mix_male": 0.45}
    assert not [name for name in model.Data.refs if "mort" in name or "improve" in name]
    own = sorted(name for name, cell in model.Projection.cells.items()
                 if ("mort" in name or "improve" in name) and cell._is_defined())
    assert own == ["mort_be_factor", "mort_be_trend", "mort_rate", "mort_rate_gen",
                   "mort_rate_mth", "mort_rate_tariff", "mort_rate_tariff_mth"]
    assert not [name for name, cell in model.Data.cells.items()
                if ("mort" in name or "improve" in name) and cell._is_defined()]
    assert model.Data.cells["mort_table_index"]._is_derived()
    assert model.Projection.cells["mort_rate_at_age"]._is_derived()
    for name in ("improvement_table", "improvement_table_dict", "mort_table_ages",
                 "improvement_table_ages"):
        assert name not in model.Data.cells, name
    assert "improve_rate_at_age" not in model.Projection.cells
    usage = param_usage.scan(model)
    assert not {"mort_table", "mort_table_dict", "mort_table_index"} & usage.reachable
    assert "mort_base_year" not in usage.reads and "omega_age" not in usage.reads
    assert usage.reads["mort_be_trend_factor"] == {"mort_be_trend"}
    for space in ("Data", "Projection"):
        source = (folder / MODELS[SOFORT] / space / "__init__.py").read_text(encoding="utf-8")
        for name in ("mort_table.csv", "improvement_table.csv", "mort_file", "improvement_file",
                     "mort_table_dict", "mort_table()", "improvement_table", "mort_base_year",
                     "mort_table_index", "mort_table_ages", "improve_rate", "\"FIRST\"",
                     "\"SECOND\""):
            assert name not in source, (space, name)
    # its reads of the factory: the rate in its hook, the trend and the base year in its
    # trend term; the end age through the core's ``omega_age_table``
    cells = dict(_formula_cells(folder / MODELS[SOFORT] / "Projection" / "__init__.py"))
    reads = {name: sorted(ast.unparse(node) for node in ast.walk(cell)
                          if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                          and node.value.id == "tables")
             for name, cell in cells.items()}
    assert {name: found for name, found in reads.items() if found} == {
        "mort_rate_gen": ["tables.q"], "mort_be_trend": ["tables.base_year", "tables.trend"]}
    item = model.Projection[1]
    item.result_cf()
    assert len(model.CoreTables.q) > 0
    assert len(model.Data.cells["mort_table"]) == 0
    assert len(model.Data.cells["mort_table_dict"]) == 0


def unswitched_copy(tmp_path: Path) -> Path:
    """A scratch copy of Index with the fixture tables that chooses no table: without its
    row ``mort_table`` and with a ``mort_rate_at_age`` of its own that reads no table, as a
    product before its switch."""
    folder = fixture_copy(tmp_path)
    path = folder / "param_tariff_type.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    choice = [row for row in rows if row.startswith("mort_table,")]
    assert len(choice) == 1
    path.write_text("".join(row for row in rows if row not in choice), encoding="utf-8")
    add_cells(folder / MODELS[INDEX] / "Projection" / "__init__.py",
              'def mort_rate_at_age(x):\n'
              '    """A rate of its own, read off no table.\n\n'
              '    Override reason: test fixture, tests/test_tables.py\n    """\n'
              '    return 0.001 if sex() == "M" else 0.0007\n')
    return folder


def switched_copy(tmp_path: Path, table: str, birth_year: int | None = None) -> Path:
    """A scratch copy of Index with the fixture tables that chooses ``table`` as its
    ``mort_table`` in place of the shipped choice; with ``birth_year``, a cell of that name
    returning it. Index has no ``mort_rate_at_age`` of its own, and its ``mort_be_factor``
    0.75 stands."""
    folder = fixture_copy(tmp_path)
    path = folder / MODELS[INDEX] / "Projection" / "__init__.py"
    assert "def mort_rate_at_age(" not in path.read_text(encoding="utf-8")
    if birth_year is not None:
        add_cells(path,
                  'def birth_year():\n'
                  '    """A fixture birth year.\n\n'
                  '    Override reason: test fixture, tests/test_tables.py\n    """\n'
                  f'    return {birth_year}\n')
    path = folder / "param_tariff_type.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    choice = [row for row in rows if row.startswith("mort_table,")]
    assert len(choice) == 1
    path.write_text("".join(row for row in rows if row not in choice), encoding="utf-8")
    _add_params(path, {"mort_table": table, "unisex_mix_male": "0.45"})
    return folder


def test_the_hooks_deliver_the_chosen_table(tmp_path):
    folder = switched_copy(tmp_path, "period_fixture")
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedProbe")
    try:
        projection, tables = model.Projection, model.CoreTables
        for hook in TABLE_HOOKS + ("mort_rate_at_age", "mort_rate_tariff_at_age", "birth_year",
                                   "mort_be_trend", "mort_rate_base", "mort_rate"):
            assert projection.cells[hook]._is_derived(), hook
        points = model.Data.model_point_table()
        sexes = set()
        for point_id in points.index[:4]:
            item = projection[point_id]
            sex = points.at[point_id, "sex"]
            sexes.add(sex)
            assert item.mort_table_name() == "period_fixture"
            assert item.birth_year() == 0          # no birth year: the factory gets None
            assert item.omega_age_table() == 121 == tables.end_age("period_fixture")
            for x in (0, 40, 67, 119, 120):
                rate = tables.q("period_fixture", sex, x)
                assert item.mort_rate_table(sex, x) == rate
                assert item.mort_rate_at_age(x) == rate
                assert rate == (law(sex, x) if x < 120 else 1.0)
                male, female = (tables.q("period_fixture", s, x) for s in "MF")
                assert item.mort_rate_tariff_at_age(x) == 0.45 * male + (1.0 - 0.45) * female
            assert item.mort_rate_tariff_at_age(120) == 1.0
            for t in (item.t_start(), item.t_start() + 13, item.proj_len() - 1):
                rate = tables.q("period_fixture", sex, item.age(t))
                assert item.mort_be_trend(t) == 1.0 and item.mort_be_factor() == 0.75
                assert item.mort_rate_base(t) == rate
                assert item.mort_rate(t) == rate * 0.75
            line = raised_line(lambda: item.mort_rate_at_age(121))
            assert line.startswith("ValueError: table 'period_fixture': x 121 is outside")
        assert sexes == {"M", "F"}
    finally:
        model.close()


def test_the_hooks_pass_the_birth_year_on(tmp_path):
    folder = switched_copy(tmp_path, "gen_fixture", birth_year=1975)
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedGenProbe")
    try:
        item, tables = model.Projection[1], model.CoreTables
        sex = item.sex()
        trend = float(FIXTURE_VALUES["gen_fixture"][sex.lower() + "_trend"])
        assert item.birth_year() == 1975
        rate = item.mort_rate_at_age(50)
        assert rate == tables.q("gen_fixture", sex, 50, 1975)
        assert rate == law(sex, 50) * (1.0 - trend) ** (1975 + 50 - 1999)
        assert item.omega_age_table() == 121
    finally:
        model.close()


def test_a_generational_table_without_a_birth_year_cell_raises(tmp_path):
    folder = switched_copy(tmp_path, "gen_fixture")
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedNoBirthProbe")
    try:
        line = raised_line(lambda: model.Projection[1].mort_rate_at_age(50))
        assert line == ("ValueError: table 'gen_fixture': birth_year is missing, the table is"
                        " generational")
    finally:
        model.close()


def test_a_chosen_table_the_factory_does_not_hold_raises(tmp_path):
    folder = switched_copy(tmp_path, "no_such_proxy")
    model = mx.read_model(folder / MODELS[INDEX], name="SwitchedUnknownProbe")
    try:
        item = model.Projection[1]
        for call in (lambda: item.mort_rate_at_age(50), lambda: item.mort_rate(item.t_start())):
            assert raised_line(call) == "ValueError: table 'no_such_proxy' is not defined"
    finally:
        model.close()


# Index' own ``mort_be_factor`` is 0.75, a factor below 1; the copy adds a trend term and a load.
THRU_CELLS = '''
def mort_be_trend(t):
    """A fixture best-estimate trend term below 1.

    Override reason: test fixture, tests/test_tables.py
    """
    return 0.5


def mort_load_tariff(t):
    """A fixture loading above 1.

    Override reason: test fixture, tests/test_tables.py
    """
    return 1.25

'''


def test_a_table_rate_of_1_passes_through_the_factor_and_the_load(tmp_path):
    # the fixture table closes at 66, the last age an Index point attains (ret_age 67)
    folder = switched_copy(tmp_path, "period_fixture")
    model_dir = folder / MODELS[INDEX]
    tables_path = model_dir / "CoreData" / TABLES_FILE
    text = tables_path.read_text(encoding="utf-8")
    assert text.count("period_fixture_end_age,121,") == 1
    tables_path.write_text(text.replace("period_fixture_end_age,121,",
                                        "period_fixture_end_age,67,"), encoding="utf-8")
    add_cells(model_dir / "Projection" / "__init__.py", THRU_CELLS)
    model = mx.read_model(model_dir, name="ThruProbe")
    try:
        cells = model.Projection.cells
        assert not cells["mort_be_factor"]._is_derived()
        assert not cells["mort_be_trend"]._is_derived()
        assert not cells["mort_load_tariff"]._is_derived()
        for name in ("mort_rate_base", "mort_rate", "mort_rate_tariff_base", "mort_rate_tariff"):
            assert cells[name]._is_derived(), name
        points = model.Data.model_point_table()
        sexes = set()
        for point_id in points.index[:4]:
            item = model.Projection[point_id]
            sexes.add(item.sex())
            assert item.omega_age_table() == 67 == item.ret_age()
            last = item.proj_len() - 1
            assert item.age(last) == 66
            # at the closing age, end age minus one: 1, not the factor, the trend or the load
            assert item.mort_rate_base(last) == 1.0 == item.mort_rate_tariff_base(last)
            assert item.mort_be_factor() == 0.75 and item.mort_load_tariff(last) == 1.25
            assert item.mort_be_trend(last) == 0.5 == item.mort_be_trend(last - 12)
            assert item.mort_rate(last) == 1.0
            assert item.mort_rate_tariff(last) == 1.0
            # the year before, the factor and the load act on the table rate
            before = last - 12
            assert item.age(before) == 65
            rate = law(item.sex(), 65)
            blend = 0.45 * law("M", 65) + (1.0 - 0.45) * law("F", 65)
            assert item.mort_rate_base(before) == rate < 1.0
            assert item.mort_rate(before) == rate * 0.75 * 0.5
            assert item.mort_rate_tariff_base(before) == blend < 1.0
            assert item.mort_rate_tariff(before) == 1.25 * blend
        assert sexes == {"M", "F"}
    finally:
        model.close()


def test_a_switched_copy_runs_through_both_engines(tmp_path, monkeypatch):
    folder = switched_copy(tmp_path, "period_fixture")
    runner = load_runner()
    traced = runner.run_product(folder, engine="modelx")
    shipped = runner.run_product(PRODUCTS_DIR / INDEX, engine="modelx")
    (count, checks, sha, failures, _lines, digests), after, at_end = run_spying_on_the_factory(
        folder, monkeypatch)
    assert failures == [] and traced[3] == []
    assert (count, checks, sha, digests) == (traced[0], traced[1], traced[2], traced[5])
    assert sha != shipped[2]
    assert after[1] and after[1].items() <= at_end.items()
    assert all(key[0] == "period_fixture" and key[3] is None for key in at_end)
    # the shipped choice is replaced in the copy: no rate of the shipped table is read
    assert not [key for key in at_end if key[0] in SHIPPED_TABLES]


# --------------------------------------------------------------------------- the usage scan

def fixture_items(table: str) -> tuple[str, ...]:
    """The items of a fixture table, as its definition names them."""
    return tuple(f"{table}_{name}" for name in FIXTURE_DEFINITIONS[table][2])


def choosing_copy(tmp_path: Path, table: str, file: str = "param_tariff_type.csv") -> Path:
    """A scratch copy of Index with the fixture tables that chooses ``table`` as its
    ``mort_table`` in ``file``, in place of the shipped choice, and is otherwise clean in the
    usage scan: ``switched_copy`` without its row ``unisex_mix_male``, which no reachable
    cell of Index reads."""
    folder = switched_copy(tmp_path, table)
    path = folder / "param_tariff_type.csv"
    rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    choice = [row for row in rows if row.startswith("mort_table,")]
    dropped = [row for row in rows if row.startswith(("unisex_mix_male,", "mort_table,"))]
    assert len(choice) == 1 and len(dropped) == 2
    path.write_text("".join(row for row in rows if row not in dropped), encoding="utf-8")
    _add_params(folder / file, {"mort_table": table})
    return folder


def scan_of(folder: Path, name: str, edit=None):
    """The usage scan of a scratch copy of Index, after ``edit(model)`` changed its model."""
    model = mx.read_model(folder / MODELS[INDEX], name=name)
    try:
        if edit is not None:
            edit(model)
        return param_usage.scan(model)
    finally:
        model.close()


@pytest.mark.parametrize("product", sorted(MODELS))
def test_the_scan_of_a_shipped_product_holds_the_tables_and_no_problem(product, product_models):
    usage = param_usage.scan(product_models(product))
    assert usage.problems == []
    assert usage.tables == SHIPPED_ITEMS
    assert usage.layers["tables"] == SHIPPED_LAYER
    read = set(usage.reads) & set(usage.layers["tables"])
    choices = SWITCHED.get(product, {})
    assert usage.choices == choices
    assert read == {item for table in choices.values() for item in SHIPPED_ITEMS[table]}
    for choice, table in choices.items():
        readers = usage.reads[choice]
        assert readers == CHOICE_READERS[choice] and readers <= usage.reachable
        for item in SHIPPED_ITEMS[table]:
            assert usage.reads[item] == readers, item
    if not choices:
        assert not [item for item in usage.reads if item.endswith("_table")]


def test_no_table_is_unchosen_in_the_ten_products(product_models):
    usages = [param_usage.scan(product_models(product)) for product in sorted(MODELS)]
    assert len(usages) == 10
    assert param_usage.unchosen_tables(usages) == []
    chosen = {table for usage in usages for table in usage.choices.values()}
    assert chosen == set(SHIPPED_TABLES) == {table for choices in SWITCHED.values()
                                             for table in choices.values()}
    # without the products that chose them, the tables would be reported
    others = [param_usage.scan(product_models(product)) for product in sorted(MODELS)
              if product not in SWITCHED]
    assert param_usage.unchosen_tables(others) == sorted(SHIPPED_TABLES)
    # the select table and the two smoker tables have one reader each, the generational
    # table four and the aggregate table five
    without_bu = [param_usage.scan(product_models(product)) for product in sorted(MODELS)
                  if product != BU]
    assert param_usage.unchosen_tables(without_bu) == [DAV1997TI]
    without_its_readers = [param_usage.scan(product_models(product))
                           for product in sorted(MODELS)
                           if product not in (RV, "basisrente", "riester_rente", SOFORT)]
    assert param_usage.unchosen_tables(without_its_readers) == [DAV2004R]
    without_rlv = [param_usage.scan(product_models(product)) for product in sorted(MODELS)
                   if product != RLV]
    assert param_usage.unchosen_tables(without_rlv) == [NR, R]
    for reader in (FRV, INDEX, KLV, RV, "basisrente", "riester_rente", SOFORT):
        without = [param_usage.scan(product_models(product)) for product in sorted(MODELS)
                   if product != reader]
        assert param_usage.unchosen_tables(without) == []
    without_its_readers = [param_usage.scan(product_models(product))
                           for product in sorted(MODELS)
                           if product not in (BU, FRV, INDEX, KLV, "riester_rente")]
    assert param_usage.unchosen_tables(without_its_readers) == [DAV1997TI, DAV2008T]


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_the_scan_counts_the_items_of_a_chosen_table_as_read(tmp_path, file):
    usage = scan_of(choosing_copy(tmp_path, "period_fixture", file), "ChosenScanProbe")
    assert usage.problems == []
    assert usage.tables == SHIPPED_ITEMS | {table: fixture_items(table)
                                            for table in FIXTURE_DEFINITIONS}
    assert usage.choices == {"mort_table": "period_fixture"}
    readers = usage.reads["mort_table"]
    assert readers == {"mort_table_name"} and readers <= usage.reachable
    for item in fixture_items("period_fixture"):
        assert usage.reads[item] == readers, item
    read = set(usage.reads) & set(usage.layers["tables"])
    assert read == set(fixture_items("period_fixture"))
    assert len(usage.layers["tables"]) > len(read)


def test_the_scan_reads_no_tables_item_without_a_choice(tmp_path):
    usage = scan_of(unswitched_copy(tmp_path), "NoChoiceScanProbe")
    assert usage.problems == []
    assert list(usage.tables) == ALL_TABLES and usage.choices == {}
    assert usage.layers["tables"] and not set(usage.reads) & set(usage.layers["tables"])
    assert "mort_table" not in usage.reads


def test_the_scan_reads_no_item_of_a_table_whose_choice_no_cell_reads(tmp_path):
    folder = unswitched_copy(tmp_path)
    _add_params(folder / "param_tariff_type.csv", {"probe_table": "period_fixture"})
    usage = scan_of(folder, "UnreadChoiceScanProbe")
    assert usage.choices == {"probe_table": "period_fixture"}
    assert usage.problems == ["item 'probe_table' of the tariff_type layer"
                              " (param_tariff_type.csv) is read by no reachable cell"]
    assert not set(usage.reads) & set(usage.layers["tables"])
    assert param_usage.unchosen_tables([usage]) == sorted(ALL_TABLES)


def test_the_scan_reports_an_item_of_a_table_in_another_layer(tmp_path):
    """The item ``broken_fixture`` lacks in the tables layer, held by the tariff-type file:
    ``param`` would find it, the scan reports it."""
    folder = choosing_copy(tmp_path, "broken_fixture")
    _add_params(folder / "param_tariff_type.csv", {"broken_fixture_f_b": "1.092"})
    usage = scan_of(folder, "TableItemElsewhereScanProbe")
    assert usage.problems == [
        "item 'broken_fixture_f_b' of the table 'broken_fixture' stands in the tariff_type"
        " layer (param_tariff_type.csv), not in the tables layer"]


@pytest.mark.parametrize(("layer", "file"), [("core", "param_core.csv"),
                                             ("tables", TABLES_FILE)])
def test_the_scan_reports_a_table_choice_in_the_core_or_the_tables_file(tmp_path, layer, file):
    folder = unswitched_copy(tmp_path)
    _add_params(folder / MODELS[INDEX] / "CoreData" / file, {"mort_table": "period_fixture"})
    usage = scan_of(folder, "ChoiceElsewhereScanProbe")
    assert usage.choices == {}
    assert (f"item 'mort_table' of the {layer} layer ({file}) is a table choice outside the"
            f" tariff-type and tariff files") in usage.problems
    assert len(usage.problems) == (1 if layer == "core" else 2)
    assert not set(usage.reads) & set(fixture_items("period_fixture"))


@pytest.mark.parametrize("file", ["param_tariff_type.csv", "param_tariff.csv"])
def test_the_scan_reports_a_chosen_name_the_factory_lacks(tmp_path, file):
    usage = scan_of(choosing_copy(tmp_path, "nosuch_table", file), "UnknownChoiceScanProbe")
    layer = "tariff" if file == "param_tariff.csv" else "tariff_type"
    assert usage.problems == [f"item 'mort_table' of the {layer} layer ({file}) names the"
                              f" table 'nosuch_table', which the factory does not hold"]
    assert usage.choices == {"mort_table": "nosuch_table"}
    assert not set(usage.reads) & set(usage.layers["tables"])


def test_the_scan_reports_a_tables_item_of_no_table(tmp_path):
    """A row that is no table's item, and one that starts with a table's name but is not
    among the items its definition names."""
    folder = choosing_copy(tmp_path, "period_fixture")
    _add_params(tables_file(folder, INDEX), {"stray_item": "1.5", "period_fixture_m_c": "2"})
    usage = scan_of(folder, "StrayItemScanProbe")
    assert usage.problems == [
        "item 'stray_item' of the tables layer (param_tables.csv) belongs to no table",
        "item 'period_fixture_m_c' of the tables layer (param_tables.csv) belongs to no table"]
    assert "stray_item" not in usage.reads and "period_fixture_m_c" not in usage.reads


def test_the_scan_reports_an_item_a_chosen_table_names_and_the_layer_lacks(tmp_path):
    usage = scan_of(choosing_copy(tmp_path, "broken_fixture"), "BrokenTableScanProbe")
    assert usage.problems == [
        "item 'broken_fixture_f_b' read by mort_table_name stands in no layer"]
    assert set(fixture_items("broken_fixture")) <= set(usage.reads)


def test_the_scan_reports_a_cell_reading_a_tables_item_directly(tmp_path):
    """By a literal call and by a declared indirect read; the table stays unchosen. The
    copy keeps the shipped choice, whose table is read through the factory."""
    def edit(model):
        model.Projection.new_cells(
            name="probe_direct",
            formula='def probe_direct():\n    return data.param("gen_fixture_m_a")\n')
        model.Projection.new_cells(
            name="probe_declared",
            formula='def probe_declared():\n    name = "gen_fixture_f_a"\n'
                    '    return data.param(name)\n')
        model.Data.cells["param_indirect"].formula = (
            'def param_indirect():\n    return {"probe_declared": ("gen_fixture_f_a",)}\n')

    usage = scan_of(fixture_copy(tmp_path), "DirectTablesReadScanProbe", edit)
    assert usage.problems == [
        "cell probe_declared reads the item 'gen_fixture_f_a' of the tables layer directly,"
        " not through the table factory",
        "cell probe_direct reads the item 'gen_fixture_m_a' of the tables layer directly,"
        " not through the table factory"]
    assert param_usage.unchosen_tables([usage]) == sorted(set(ALL_TABLES) - {DAV2008T})


def test_the_scan_reports_a_product_defined_tables_path(tmp_path):
    def edit(model):
        model.Data.cells["param_tables_path"].formula = (
            'def param_tables_path():\n'
            '    return _model.path / "CoreData" / "param_tables.csv"\n')
        assert model.Data.cells["param_tables_path"]._is_defined()

    usage = scan_of(choosing_copy(tmp_path, "period_fixture"), "TablesPathScanProbe", edit)
    assert usage.problems == ["Data defines param_tables_path; the table parameter file is the"
                              " core's param_tables.csv beside its loaders"]


def test_the_scan_reports_a_read_around_param_through_the_tables_path(tmp_path):
    def edit(model):
        model.Projection.new_cells(
            name="probe_path",
            formula="def probe_path():\n    return data.param_tables_path()\n")

    usage = scan_of(choosing_copy(tmp_path, "period_fixture"), "TablesBypassScanProbe", edit)
    assert usage.problems == [
        "cell probe_path reads the parameters around param(): param_tables_path"]


def test_unchosen_tables_names_the_tables_no_model_chooses(tmp_path):
    others = sorted(set(ALL_TABLES) - {"period_fixture"})
    period = scan_of(choosing_copy(tmp_path / "period", "period_fixture"), "UnchosenProbeA")
    assert param_usage.unchosen_tables([period]) == others
    gen = scan_of(choosing_copy(tmp_path / "gen", "gen_fixture"), "UnchosenProbeB")
    none = scan_of(unswitched_copy(tmp_path / "none"), "UnchosenProbeC")
    assert param_usage.unchosen_tables([none]) == sorted(ALL_TABLES)
    assert param_usage.unchosen_tables([none, period, gen]) == sorted(
        set(others) - {"gen_fixture"})
    # the copy with the shipped choice chooses Index' table and no other
    shipped = scan_of(fixture_copy(tmp_path / "shipped"), "UnchosenProbeD")
    assert param_usage.unchosen_tables([shipped]) == sorted(set(ALL_TABLES) - {DAV2008T})
    assert param_usage.unchosen_tables([none, period, gen, shipped]) == sorted(
        set(ALL_TABLES) - {DAV2008T, "period_fixture", "gen_fixture"})
    assert param_usage.unchosen_tables([]) == []
