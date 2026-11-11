"""The static usage scan of the parameter reads (``docs/core.md``, "The parameter files").

A plain module beside the core model, not a model space: ``mx.read_model`` of ``core/Core``
does not see it.  ``scan(model)`` reads a product's modelx model, the formula sources of its
``Projection`` and ``Data`` cells only, and evaluates no ``Projection`` cell; of the loader it
evaluates ``param_layers()``, ``param_paths()`` (for the files' names) and the term
``param_indirect()``.

A read counts for a product only where its cell is reachable:

- the roots are the product's own cells (``_is_defined()``) in ``Projection`` and ``Data`` and
  every cell named ``result_*`` or ``check_*``;
- the edges are every ``ast.Name`` id and ``ast.Attribute`` attr in a cell's
  ``formula.source`` that names a cell of either space.

This is meant to over-approximate what a run evaluates: ``tests/test_core_quota.py`` checks
that every ``Projection`` cell the core quota records as executed is reachable (``Data``
cells are not compared).  Where that holds, an item reported unused is read by no executed
``Projection`` cell, and a call to a missing item is reported for every such call a run makes.  Counting every inherited core cell instead would flag core items in products
that never evaluate the core cell reading them.

In a reachable cell a call ``param("<item>")`` (or ``data.param("<item>")``) with one string
literal reads that item.  Any other reference to ``param`` is an indirect read, which the cell
has to declare in ``param_indirect()``, ``{cell: (item, ...)}``; the declared items count as
read by the cell.  A cell other than the loader cells must not reference the readers behind
``param`` (``param_dict``, ``param_layers``, ``param_rows``, ``param_paths``) or the files
they read (``param_core_path``, ``param_tariff_path``, ``param_file``), and a product must not
define ``param_core_path``: the core file is the one beside the core's loaders.

The problems of one product: a call or declared item naming an item no layer holds, an item
of the tariff-type or the tariff layer that no reachable cell reads, an undeclared indirect
read, a declared cell that does not exist, a bypass of ``param`` through a reader or a file
path, and a product-defined ``param_core_path``.  An item of the core file is checked across
all products together, ``unused_core_items(usages)``: it is used if any product reads it.
``tools/params.py``, the view of a tariff's parameters, builds on this scan.
"""
import ast
import textwrap
from dataclasses import dataclass

SPACES = ("Projection", "Data")
ROOT_PREFIXES = ("result_", "check_")
LOADER = "param"
READERS = frozenset({"param_dict", "param_layers", "param_rows", "param_paths"})
CORE_PATH = "param_core_path"
PATHS = frozenset({CORE_PATH, "param_tariff_path", "param_file"})
LOADER_CELLS = READERS | {LOADER}
PRODUCT_LAYERS = ("tariff_type", "tariff")


@dataclass(frozen=True)
class Usage:
    """What ``scan`` found for one model.

    ``layers`` is ``param_layers()``, ``reads`` maps each item read to the reachable cells
    reading it, ``reachable`` the names of the reachable cells, ``indirect`` the declared
    ``param_indirect()`` and ``problems`` one line per problem, empty for a clean model.
    """

    layers: dict
    reads: dict
    reachable: frozenset
    indirect: dict
    problems: list


def _references(tree: ast.AST) -> set[str]:
    """Every ``ast.Name`` id and ``ast.Attribute`` attr in ``tree``."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _is_loader(node: ast.AST) -> bool:
    return ((isinstance(node, ast.Name) and node.id == LOADER)
            or (isinstance(node, ast.Attribute) and node.attr == LOADER))


def _param_reads(tree: ast.AST) -> tuple[list[str], bool]:
    """The items of the literal ``param("<item>")`` calls in ``tree``, and whether ``tree``
    references ``param`` in any other way."""
    items = []
    literal = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and _is_loader(node.func) and len(node.args) == 1
                and not node.keywords and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            items.append(node.args[0].value)
            literal.add(id(node.func))
    indirect = any(_is_loader(node) and id(node) not in literal for node in ast.walk(tree))
    return items, indirect


def _cells(model) -> dict[str, list]:
    """Every cell of the model's ``Projection`` and ``Data`` by name."""
    cells = {}
    for space in SPACES:
        for name, cell in model.spaces[space].cells.items():
            cells.setdefault(name, []).append(cell)
    return cells


def scan(model) -> Usage:
    """Scan one model's parameter reads statically (module docstring)."""
    cells = _cells(model)
    trees = {name: [ast.parse(textwrap.dedent(cell.formula.source)) for cell in group]
             for name, group in cells.items()}
    references = {name: set().union(*map(_references, group)) & set(cells)
                  for name, group in trees.items()}

    roots = {name for name, group in cells.items()
             if name.startswith(ROOT_PREFIXES) or any(cell._is_defined() for cell in group)}
    reachable = set()
    stack = sorted(roots)
    while stack:
        name = stack.pop()
        if name not in reachable:
            reachable.add(name)
            stack.extend(references[name] - reachable)

    data = model.Data
    layers = data.param_layers()
    indirect = dict(data.param_indirect())
    files = {layer: path.name for layer, path in data.param_paths().items()}
    problems = []

    reads = {}
    for name in sorted(reachable):
        if name in LOADER_CELLS:
            continue
        indirect_ref = False
        for tree in trees[name]:
            items, other = _param_reads(tree)
            indirect_ref = indirect_ref or other
            for item in items:
                reads.setdefault(item, set()).add(name)
        if indirect_ref and name not in indirect:
            problems.append(f"cell {name} reads a parameter by a computed name and is not "
                            f"declared in param_indirect()")

    for name, items in sorted(indirect.items()):
        if name not in cells:
            problems.append(f"param_indirect() declares {name}, which is no cell")
            continue
        for item in items:
            if name in reachable:
                reads.setdefault(item, set()).add(name)
            elif not any(item in layer for layer in layers.values()):
                problems.append(f"param_indirect() declares item {item!r} for cell {name}, "
                                f"which no layer holds")

    for name in sorted(cells):
        if name in LOADER_CELLS:
            continue
        bypass = sorted(set().union(*map(_references, trees[name])) & (READERS | PATHS))
        if bypass:
            problems.append(f"cell {name} reads the parameters around param(): "
                            f"{', '.join(bypass)}")
    if data.cells[CORE_PATH]._is_defined():
        problems.append(f"Data defines {CORE_PATH}; the core file is the core's "
                        "param_core.csv beside its loaders")

    for item in sorted(reads):
        if not any(item in layer for layer in layers.values()):
            problems.append(f"item {item!r} read by {', '.join(sorted(reads[item]))} "
                            f"stands in no layer")
    for layer in PRODUCT_LAYERS:
        for item in layers.get(layer, {}):
            if item not in reads:
                problems.append(f"item {item!r} of the {layer} layer ({files[layer]}) "
                                f"is read by no reachable cell")

    return Usage(layers=layers,
                 reads={item: frozenset(names) for item, names in reads.items()},
                 reachable=frozenset(reachable), indirect=indirect, problems=problems)


def unused_core_items(usages) -> list[str]:
    """The items of the core file that none of the scanned models reads, sorted."""
    usages = list(usages)
    core = set().union(*(usage.layers["core"] for usage in usages))
    read = set().union(*(usage.reads for usage in usages))
    return sorted(core - read)
