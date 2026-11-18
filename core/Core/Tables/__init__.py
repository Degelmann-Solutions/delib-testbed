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
    ``None`` and select where it names a parameter ``sel_<n>``.
    """
    return {
        "dav2008t_proxy": (makeham, None, (
            "m_a", "m_b", "m_c", "f_a", "f_b", "f_c", "first_age", "end_age")),
        "dav1997ti_proxy": (makeham, None, (
            "m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
            "sel_1", "sel_2", "sel_3", "sel_4", "sel_5", "sel_6", "first_age", "end_age")),
        "dav2004r_proxy": (makeham, trend_linear, (
            "m_a", "m_b", "m_c", "f_a", "f_b", "f_c",
            "trend_start", "trend_start_age", "trend_mid", "trend_mid_age", "trend_end_age",
            "base_year", "first_age", "end_age")),
        "dav2008t_nr_proxy": (makeham, None, (
            "m_a", "m_b", "m_c", "f_a", "f_b", "f_c", "first_age", "end_age")),
        "dav2008t_r_proxy": (makeham, None, (
            "m_a", "m_b", "m_c", "f_a", "f_b", "f_c", "first_age", "end_age")),
    }


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
    """The select factors of ``table`` by duration, ``sel_1`` first; empty without selection.

    Read by name, ``sel_1`` to ``sel_<count>`` with ``count`` the number of ``sel_``
    parameters the table names, so a gap in the numbering or a name that is no number is
    the loader's ``KeyError``.
    """
    _law, _trend, names = definition(table)
    count = sum(name.startswith("sel_") for name in names)
    return tuple(parameter(table, "sel_" + str(number + 1)) for number in range(count))


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


def makeham(table, sex, x):
    """The law of Makeham on the rate: ``a + b * c ** x``, with the parameters of ``sex``.

    Reads ``<m or f>_a``, ``<m or f>_b`` and ``<m or f>_c`` of ``table``; the law of
    Gompertz is the case ``a = 0``.
    """
    key = sex.lower()
    return (parameter(table, key + "_a")
            + parameter(table, key + "_b") * parameter(table, key + "_c") ** x)


def trend_linear(table, sex, x):
    """The piecewise linear trend law: the annual improvement rate at age ``x``, for both sexes.

    ``trend_start`` up to ``trend_start_age``, linear to ``trend_mid`` at ``trend_mid_age``,
    linear to 0 at ``trend_end_age`` and 0 beyond; the five are parameters of ``table``.
    """
    start = parameter(table, "trend_start")
    start_age = parameter(table, "trend_start_age")
    mid = parameter(table, "trend_mid")
    mid_age = parameter(table, "trend_mid_age")
    stop_age = parameter(table, "trend_end_age")
    if x <= start_age:
        return start
    if x <= mid_age:
        return start + (mid - start) * (x - start_age) / (mid_age - start_age)
    if x < stop_age:
        return mid * (stop_age - x) / (stop_age - mid_age)
    return 0.0


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
