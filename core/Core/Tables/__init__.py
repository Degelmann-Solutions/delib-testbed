# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The table factory; a product model holds it as ``CoreTables`` and inherits it nowhere.

One cell, ``q``, hands out the rates of the model-wide tables. A table is an entry of
``definitions()`` and its numbers, rows of the table parameter file read through ``data``,
the sibling ``Data``; a law is a cell of this space. The space takes no parameter and holds
no contract data: whatever depends on the contract is an argument of ``q``, so a rate is
computed once per model and looked up afterwards. A product's ``Projection`` reads the space
through its Reference ``tables``; no product space names it as a base, so no product
overrides a cell of it.
"""

from modelx.serialize.jsonvalues import *

_formula = None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def definitions():
    """Every table by name: ``{table: (law, trend, parameters)}``.

    ``law`` is the cell that gives the table's rate, ``trend`` the cell that gives its annual
    improvement rate, or ``None`` for a period table, each with the signature
    ``(table, sex, x)``; ``parameters`` names the table's parameters, and the item of a
    parameter is ``<table>_<parameter>``.  A table is generational where its trend is not
    ``None`` and select where it names a parameter ``sel_<n>``.  No table is defined yet.
    """
    return {}


def definition(table):
    """The entry ``(law, trend, parameters)`` of ``table``; an unknown name raises ``ValueError``."""
    if table not in definitions():
        raise ValueError(f"table {table!r} is not defined")
    return definitions()[table]


def items():
    """The items of each table: ``{table: (item, ...)}``, ``<table>_<parameter>`` each.

    What a reader of a table reads of the table parameter file.
    """
    return {table: tuple(table + "_" + name for name in names)
            for table, (_law, _trend, names) in definitions().items()}


def parameter(table, name):
    """The parameter ``name`` of ``table``, its item ``<table>_<name>`` read through ``param``.

    The one read by a computed name; an item the layers do not hold is the loader's
    ``KeyError``.
    """
    return data.param(table + "_" + name)                            # noqa: F821


def first_age(table):
    """The first age of ``table``, the lowest it has a rate for."""
    return parameter(table, "first_age")


def end_age(table):
    """The end age of ``table``: the first age nobody reaches, one above its last age."""
    return parameter(table, "end_age")


def base_year(table):
    """The base year of a generational ``table``, the calendar year its law's rates refer to."""
    return parameter(table, "base_year")


def select_factors(table):
    """The select factors of ``table`` by duration, ``sel_1`` first; empty without selection."""
    _law, _trend, names = definition(table)
    numbers = sorted(int(name.removeprefix("sel_")) for name in names
                     if name.startswith("sel_"))
    return tuple(parameter(table, "sel_" + str(number)) for number in numbers)


def base_rate(table, sex, x):
    """The rate the law of ``table`` gives for ``sex`` at age ``x``, in its base year.

    The law's own value in full precision: neither capped at 1 nor closed at the last age,
    which ``q`` does.  Raises ``ValueError`` on an unknown table, a ``sex`` other than ``M``
    and ``F`` and an age outside ``first_age(table) .. end_age(table) - 1``; an age is never
    clamped.
    """
    law, _trend, _names = definition(table)
    if sex not in ("M", "F"):
        raise ValueError(f"table {table!r}: sex {sex!r} is neither 'M' nor 'F'")
    if not first_age(table) <= x < end_age(table):
        raise ValueError(
            f"table {table!r}: x {x!r} is outside its ages {first_age(table)} to"
            f" {end_age(table) - 1}")
    return law(table, sex, x)


def trend(table, sex, x):
    """The annual improvement rate the trend law of ``table`` gives for ``sex`` at age ``x``.

    Raises ``ValueError`` on a period table, which has no trend.
    """
    _law, law, _names = definition(table)
    if law is None:
        raise ValueError(f"table {table!r}: a period table has no trend")
    return law(table, sex, x)


def q(table, sex, x, birth_year=None, duration=None):
    """The annual rate of ``table`` for ``sex`` at the attained age ``x``.

    The base rate, on a generational table times ``(1 - trend) ** (birth_year + x -
    base_year)``, the rate of the calendar year ``birth_year + x``, on a select table times
    the factor of the 1-based ``duration``, the last factor holding for every later
    duration; capped at 1 and never rounded.  At the last age, ``end_age(table) - 1``, the
    rate is 1 whatever the trend and the selection.

    Raises ``ValueError``, naming the table and the argument, where the call does not fit
    the table: the cases of ``base_rate``, a generational table without ``birth_year``, a
    period table with one, a select table without ``duration`` or with one below 1, and a
    table without selection with one.
    """
    rate = base_rate(table, sex, x)
    _law, trend_law, _names = definition(table)
    generational = trend_law is not None
    factors = select_factors(table)
    if generational and birth_year is None:
        raise ValueError(f"table {table!r}: birth_year is missing, the table is generational")
    if not generational and birth_year is not None:
        raise ValueError(
            f"table {table!r}: birth_year {birth_year!r} is given, the table is a period table")
    if factors and duration is None:
        raise ValueError(f"table {table!r}: duration is missing, the table is select")
    if factors and duration < 1:
        raise ValueError(f"table {table!r}: duration {duration!r} is below 1")
    if not factors and duration is not None:
        raise ValueError(
            f"table {table!r}: duration {duration!r} is given, the table has no selection")
    if x == end_age(table) - 1:
        return 1.0
    if generational:
        rate = rate * (1.0 - trend(table, sex, x)) ** (birth_year + x - base_year(table))
    if factors:
        rate = rate * factors[min(duration, len(factors)) - 1]
    return min(1.0, rate)


# ---------------------------------------------------------------------------
# References

data = ("Interface", ("..", "Data"), "auto")
