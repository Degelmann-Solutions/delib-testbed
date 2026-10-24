# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The shared by-policy cells; a product's ``Projection`` inherits them as ``CoreProjection``.

The space is parameterized by ``point_id``, like the product's ``Projection``. Its cells use
the names the product's ``Projection`` defines: ``data`` for the product's ``Data`` and
``point_id`` for the selected model point.
"""

from modelx.serialize.jsonvalues import *

_formula = lambda point_id: None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def model_point():
    """The selected model point as a Series."""
    return data.model_point_table().loc[point_id]                    # noqa: F821
