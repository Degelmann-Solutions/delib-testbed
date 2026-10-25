# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The shared input cells; a product's ``Data`` inherits them as ``CoreData``.

Input files stay the product's own: the product's ``Data`` reads them relative to the
product's model folder.
"""

from modelx.serialize.jsonvalues import *

_formula = None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def input_dir():
    """The directory holding the product's input CSVs: its model folder's parent.

    Resolved at run time from where the product's model was read, so a core cell reads
    the product's own input files.
    """
    return _model.path.parent                                        # noqa: F821
