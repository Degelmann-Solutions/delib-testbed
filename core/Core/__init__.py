# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The common core of the products (phase 3, ``docs/core.md``).

The model holds the cells the products share, in two spaces that mirror a product's:
:mod:`~.Core.Data` for the inputs and :mod:`~.Core.Projection` for the by-policy
projection. A product reaches them through symlinks ``CoreData`` and ``CoreProjection``
in its model folder and names them as bases of its own ``Data`` and ``Projection``.
"""

from modelx.serialize.jsonvalues import *

_name = "Core"

_allow_none = False

_spaces = [
    "Data",
    "Projection"
]
