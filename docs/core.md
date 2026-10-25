# The common core of phase 3: layout and conventions

Phase 3 moves the quantities the ten products share into one core. This file describes where the core lives, how a product reaches it, and the conventions every core commit follows: commit trailers, the reason on a product override, and how a product's `UPSTREAM.md` names the files phase 3 changed. The tests that enforce the conventions are `tests/test_core.py` and `tests/test_provenance.py`.

## Layout

- `core/Core/` is a modelx model of its own, with the spaces `Data` and `Projection`. It holds the shared cells and nothing product-specific: no product folder name, model name or model prefix appears anywhere under `core/` (grep test in `tests/test_core.py`). Because it is a readable model, the tests can load it without a product.
- `core/Core/Projection` is parameterized by `point_id`, like every product's `Projection`; its cells are written against the product's names (`data`, `point_id`), which the product space provides.
- `core/Core/Data` holds the shared input loaders. Its cells use the product's References (`pd`, `model_point_file`, `param_file`, `mort_file`, `lapse_file`, `rentenfaktor_file`, `freq_loading_file`), which the product's `Data` defines; the core defines no References.
- A product inherits every core cell, also one it has no use for: a product without a lapse table still has a derived `lapse_table`, which nothing evaluates. `CORE_CELLS` in `tests/test_core.py` lists, for every cell in the core, the products that derive it and those that override it with a reason.

## How a product reaches the core

modelx `bases` work only inside one model, and each product is its own model. The core therefore enters each product's model folder as two symlinks next to the product's own spaces:

```text
products/<product>/<Model>/CoreData       -> ../../../core/Core/Data
products/<product>/<Model>/CoreProjection -> ../../../core/Core/Projection
```

The product's `__init__.py` lists `CoreData` and `CoreProjection` in `_spaces` (before `Data` and `Projection`), and its `Data` and `Projection` name them as bases in the serialized format of `mx.write_model`, one leading dot for a sibling space:

```python
_bases = [
    ".CoreProjection"
]
```

`mx.read_model` follows the symlinks, so the product stays a self-contained modelx model: `run.py` and the runner `tools/run_baseline.py` read it unchanged, under `--engine export` and `--engine modelx`. A product cell that the product space does not define is derived from the core; under `--engine modelx` the trace shows the core's formula. `Data.input_dir()` resolves from the product's model path, so a core cell reads the product's own input files.

`shutil.copytree` follows symlinks by default, so a scratch copy of a product folder (tests, `tools/measure_marginal.py`) holds real copies of the core spaces and runs the same way.

A checkout without symlink support (Windows without developer mode or `core.symlinks`) is not supported. Composing the core into the product at load time in `tools/` was probed as an alternative and not built (Moritz, 2026-10-25).

## Commit trailers

Every commit that touches the core or a product model follows these rules from the first phase-3 commit on. Trailers stand in the last paragraph of the commit message, before `Co-Authored-By`.

- **Byte-identical commit** (refactor, unification without result change, reasoned override, tests, docs): no result trailer. A commit without `Result-Change` claims that every product's results are byte-identical to the commit before; the `pytest` gate (`tests/test_baseline.py` with its pinned hashes) proves it.
- **Result-changing commit**: one trailer naming every product whose results change, the reason, and the agent check:

  ```text
  Result-Change: risikolebensversicherung, kapitallebensversicherung
  Reason: products/kapitallebensversicherung/technical-notes.md, section …
  Checked-By: <agent>: <verdict>
  ```

  `Reason` points to the document and place that justify the change (product docs, a decision); `Checked-By` names the agent that checked the change and its verdict. The same commit updates the affected baselines and their pins. Every deviation from the tag `phase-2-baseline` leads to exactly one such commit.
- **Performance commit** (epic-night-run): `Performance: byte-identical`. Results stay byte-identical; the trailer marks the commit as a speed-up rather than a refactor.
- **Fix forward**: a commit that repairs an earlier commit is not a revert; it names the repaired commit with its full SHA:

  ```text
  Fixes: 0123456789abcdef0123456789abcdef01234567
  ```

  The repaired commit stays in the history, as the README's rules for the history require.

## Override reason

A product cell that redefines a cell of a core base is an override. Its docstring carries one line with the reason and the document that gives it:

```python
def model_point():
    """The selected model point as a Series.

    Override reason: <reason>, <doc ref>
    """
```

The line starts with `Override reason:` and is not empty after the colon. `tests/test_core.py` loads every product that has a core base and fails, naming product and cell, for an override without it. A cell that the product does not define is inherited and needs no reason.

## Changed files in `UPSTREAM.md`

The hash table of a product's `UPSTREAM.md` stays upstream's: it lists every copied file with its upstream SHA-256, also after phase 3 changes the file. A product whose folder phase 3 changes gets a section below the hash table that names every changed file and every added symlink:

```markdown
## Changed in phase 3

| Path | Change |
|---|---|
| `RLV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core |
| `RLV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
```

`tests/test_provenance.py` skips the hash check for a listed file, requires every listed changed file to stay in the hash table, and requires every symlink in a product folder to be listed and to resolve to a core space folder under `core/`. A changed file that is not listed fails the hash check as before.

As a rule a product adds no regular file, since an added file has no upstream hash; the paths phase 3 adds are symlinks to core space folders. The exception is a merge of input files, decided for each case (epic Notes): Pflege's `basis_table.csv` and `expense_table.csv` merge into one `param_table.csv`, so that RV and Pflege share the core's `param_table` loader. Such a merge is listed with two kinds of change:

```markdown
| `param_table.csv` | added: merged from `basis_table.csv` and `expense_table.csv` |
| `basis_table.csv` | removed: merged into `param_table.csv` |
| `expense_table.csv` | removed: merged into `param_table.csv` |
```

A change starting `added:` that is no symlink names a regular file that must be present and is not in the hash table. A change starting `removed:` names a file of the hash table that must be absent; its row with upstream's hash stays. The folder then holds exactly the hash table's files without the removed ones, plus the added ones and `UPSTREAM.md`.
