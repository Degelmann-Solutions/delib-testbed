# Roadmap and working notes

## Phase 1: first step

Import upstream `delib` with all standard products at a pinned commit. Then run every product once on its own model points and store the baseline results.

- Upstream as of `fb1d195` has ten products. Each is a separate model with its own tables and `product-spec.md`; they share no code.
- Check whether upstream has moved on (lifelib release 2026-10-10) and pin the start commit explicitly.
- Record provenance per product as in delib-history: upstream commit, source path, SHA-256 of every copied file, and lifelib's licence notice.

## Phase 2: how to measure

- Measure the **marginal** time per contract (the slope), not the average. Run each product at two sizes, for example all shipped points and a replicated multiple, so that fixed costs (model load, export) separate from the per-contract cost.
- State these assumptions with the estimate: the projected number of mutants (from the operator list, scaled to the code size after phase 3) and the pool size. A linear extrapolation without trace-pruning is conservative.
- Mutants exist only after phase 4, so the night-run criterion is a forecast, not a measurement.
- Rough order of magnitude, an estimate only: the term life product alone yields about 500 code mutants with the chosen operators, without parameter cells. 500 mutants × 10,000 contracts in 10 h needs about 7 ms per contract-run across all workers. Today a run takes about 230 ms per contract (82 s for 350 points). Replaced on 2026-10-28 by the new M counted on the code base after the core, M = 5,300 for all ten products, recounted on 2026-11-02 at M = 5,305 (section "The new M" below).

## Known facts to start from

- Term life performance, measured 2026-10-21 in delib-history: about 130 s and 8.2 GB per run of 350 points. Deleting `Projection[pid]` after each point gives 82 s and 155 MB. `mx.export_model` takes about 9.5 s and is bit-identical on 35 states.
- modelx 0.33.0, checked in its source: a formula change marks the space dirty and deletes **all** `Projection[pid]` itemspaces. Caching across mutants therefore does not work at cell level.
- modelx ships a memory-optimised run (`execute_actions` / `get_calcsteps` in `core/model.py`). Look at it before building per-contract cleanup.
- For the test-set repository later: recording the trace per contract allows pruning mutants at positions that are never called. Keep the model traceable.

## Where phase 2 ended

Measured in phase 2d (2026-10-24, details and the earlier steps in [performance.md](performance.md)): with the export engine, per-contract cleanup and 24 worker processes, `t_marginal` is 3.1 to 15.7 ms per contract, and 91.6 ms for `pflegerentenversicherung`; the 230 ms above are the phase-1 starting point. By the forecast (M = 500, P = 10,000), `risikolebensversicherung`, `riester_rente` and, just, `sofortrente` fit the 10 h night; six products miss it by a factor of 1.1 to 2.2, `pflegerentenversicherung` by 12.7. Peak memory no longer grows with the points run.

Speed stays a goal beyond phase 2: faster is always better. Phase 3, which may change the model, closed the remaining gap in epic-night-run (below, "Where phase 3 ended").

## Where the common core stands

The common core of phase 3 is delivered on `main` (PRs #7 and #9 to #19; layout and conventions in [core.md](core.md)). All ten products inherit `core/Core/` through modelx `bases` and override only what is their own, each override with its reason; the groups moved in the dependency order of the RLV graph, from the contract data through the time axis, the tariff basis and present values, the decrement rates, the policy counts and the cash flows to the outputs and checks. `uv run python tools/baseline_deviations.py` finds no baseline deviation from the tag `phase-2-baseline` (`73c7c75`): every product's results are byte-identical to phase 2, and every built-in check is true. The core quota is at least 20 % in every product but `berufsunfaehigkeit`, which carries its own bound at its measured quota, 18.9 % (28 of 148; Moritz, 2026-10-29, epic-night-run variant c, as recorded in `3ab6cbc`); the others run from 22.0 % (`sofortrente`) to 54.0 % (`risikolebensversicherung`). Shared quantities whose unification would change results (the gross premium, reserves and annuity present values as one formula, among others) are not unified yet; [core.md](core.md) lists them as open work, each a result-changing commit of its own.

Epic-night-run set out to fit all ten products together into one 10 h night at P = 10,000 contracts, 1,000 per product, first at M = 500, then at the new M. At its starting point, measured with the core on 2026-10-28 (export engine, per-contract cleanup, W = 24, `tools/measure_marginal.py --all --workers 24`), `t_marginal` was 2.5 to 14.1 ms per contract, and 72.0 ms for `pflegerentenversicherung` (91.6 ms in phase 2d); the sum over the ten products was 137.8 ms (171 ms in phase 2d). All ten together, 1,000 contracts each, took 500 × 1,000 × 137.8 ms ≈ 19.1 h and missed the night by a factor of about 1.9 (2.4 in phase 2d); with the fixed cost per mutant, `M × (Σ fixed(W) + 1,000 × Σ t_marginal(W))` with Σ fixed = 20.3 s, it was about 22.0 h, a factor of 2.2. `pflegerentenversicherung` alone was half of the marginal time. M = 500 was replaced by the new M (next section): M = 5,300 at `f07f003` (recounted at 5,305 since), split into core and product mutants, gave about 36.2 h with the fixed cost and set the target Σ t_marginal ≈ 25.6 ms.

## The new M

M = 500 was an estimate for term life alone from phase 1 (above, "Phase 2: how to measure"). The new M is counted on the code base after the core, first at commit `f07f0036f775e1a797004ae90cf5ac533f7889d2` (merge of PR #20, 2026-10-28), recounted at commit `790706b06b02755cf5882a68cae6977234ad7a0c` (merge of PR #38, the code after entries 17 and 18 of epic-night-run, 2026-11-02), split by where each mutant sits: a mutant in the core runs all ten products, a mutant in a product only that product (epic-night-run, decision of 2026-10-28). It replaces M = 500 and sets the target speed every later optimisation reports against.

**What is counted.** The operators O1–O6 of the operator list (P-013, sections 2 and 4), without O7 (parameter cells), per node of the Python AST:

- O1 `<` `<=` `>` `>=`: 3 mutants, O2 `==` `!=`: 2, each per operator in a comparison (a chained comparison counts every operator).
- O3 only `+` `-` `*` `/`, in binary operations and augmented assignments: 1 each; `//` `%` `**` none.
- O4 `and`/`or`: one fewer than the operands of each boolean operation.
- O5 calls of the bare names `max`/`min` with at least two positional arguments: 2 each; methods (`.max()`) not.
- O6 numeric literals, judged without sign (`-1` is `1`): the values `0`, `1`, `0.0`, `1.0` and `True`/`False` are excluded, and so is any literal anywhere inside a subscript's index or an argument of `range(...)` (operators there still count for O1–O5); an `int` gives 2 mutants (±1), a `float` 1 (×(1+δ)).
- Not counted: `in`, `not in`, `is`, `is not`, unary operators, strings and docstrings.

**Where.** Only formula cells: the module-level `def`s and non-underscore `name = lambda` assignments in a `Projection/__init__.py`, each walked whole (nested lambdas, comprehensions, defaults). The built-in checks (`check_*`) and comparisons guarding a `raise` count like any other code. Not counted: module-level references (`name = 175.0`, parameters as in O7), the `Data` spaces (loaders, paths) and the product-level `__init__.py`. Core cells count once, in `core/Core/Projection`; a product counts only the cells its own `Projection` defines, overrides and product-only cells alike. A core cell that a product overrides still counts as a core mutant.

**Forecast.** With P = 1,000 contracts per product and, per product `p`, `f_p = fixed(W)` and `t_p = t_marginal(W)` at W = 24, in seconds:

    T = M_core · (Σ_p f_p + 1,000 · Σ_p t_p) + Σ_p M_p · (f_p + 1,000 · t_p),   M = M_core + Σ_p M_p

The coverage filter is ignored: every mutant runs all 1,000 contracts of each of its products, a conservative assumption. The target speed is one factor `s` on every `t_p` with the fixed costs as measured, `s` solving T = 10 h = 36,000 s:

    s = 1,000 · (M_core · Σ_p t_p + Σ_p M_p · t_p) / (36,000 − M_core · Σ_p f_p − Σ_p M_p · f_p)

If the denominator is not positive, the fixed-cost terms alone exceed 10 h and the fixed cost is the binding target. `f_p` and `t_p` are those of `tools/measure_marginal.py --all --workers 24` of 2026-10-28 (Σ fixed 20.3 s, Σ t 137.8 ms), to 3 decimals; the command holds the same figures, so it and this section cannot disagree.

**Command.** Run from the repository root; it reads only and is deterministic. At the recount commit above it prints the output below it. The counts drift as later entries change cells; this section records them at that commit, and `tests/test_measure_marginal.py` runs the command and fails when its totals differ from the counts `tools/measure_marginal.py` holds.

```sh
uv run python - <<'EOF'
import ast
from pathlib import Path

CMP3 = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)                 # O1: 3 mutants each
CMP2 = (ast.Eq, ast.NotEq)                                 # O2: 2 mutants each
ARITH = (ast.Add, ast.Sub, ast.Mult, ast.Div)              # O3: 1 mutant each

def cells(path):
    """The formula cells of a Projection: module-level defs and non-underscore name = lambda."""
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.FunctionDef):
            yield node
        elif (isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda)
              and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
              and not node.targets[0].id.startswith("_")):
            yield node.value

def count(cell):
    """Mutants per operator O1..O6 in one cell, walked whole."""
    nodes = list(ast.walk(cell))
    skip = set()                                           # literals in slices and range(...) args
    for n in nodes:
        if isinstance(n, ast.Subscript):
            skip |= {id(m) for m in ast.walk(n.slice)}
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "range":
            for a in n.args + [k.value for k in n.keywords]:
                skip |= {id(m) for m in ast.walk(a)}
    o = [0] * 6
    for n in nodes:
        if isinstance(n, ast.Compare):
            o[0] += 3 * sum(isinstance(op, CMP3) for op in n.ops)
            o[1] += 2 * sum(isinstance(op, CMP2) for op in n.ops)
        elif isinstance(n, (ast.BinOp, ast.AugAssign)) and isinstance(n.op, ARITH):
            o[2] += 1
        elif isinstance(n, ast.BoolOp):
            o[3] += len(n.values) - 1
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id in ("max", "min") and len(n.args) >= 2):
            o[4] += 2
        elif (isinstance(n, ast.Constant) and type(n.value) in (int, float)
              and abs(n.value) not in (0, 1) and id(n) not in skip):
            o[5] += 2 if type(n.value) is int else 1
    return o

def space(path):
    o = [0] * 6
    for c in cells(path):
        o = [a + b for a, b in zip(o, count(c))]
    return o

# f_p in s, t_p in ms: tools/measure_marginal.py --all --workers 24, 2026-10-28
FT = {
    "basisrente": (1.886, 9.383),
    "berufsunfaehigkeit": (1.993, 10.031),
    "fondsgebundene_rentenversicherung": (1.969, 8.431),
    "indexpolice": (1.842, 4.515),
    "kapitallebensversicherung": (1.908, 5.659),
    "klassische_rentenversicherung": (2.080, 14.063),
    "pflegerentenversicherung": (2.970, 72.018),
    "riester_rente": (2.007, 4.298),
    "risikolebensversicherung": (1.778, 2.522),
    "sofortrente": (1.861, 6.836),
}
P, NIGHT = 1000, 36000.0

rows = [("core", space(Path("core/Core/Projection/__init__.py")))]
for path in sorted(Path("products").glob("*/*/Projection/__init__.py")):
    rows.append((path.parts[1], space(path)))
assert [r[0] for r in rows[1:]] == sorted(FT)

print(f"{'space':<34}" + "".join(f"{'O%d' % i:>6}" for i in range(1, 7)) + f"{'total':>7}")
for name, o in rows:
    print(f"{name:<34}" + "".join(f"{x:>6}" for x in o) + f"{sum(o):>7}")
m_core = sum(rows[0][1])
m_p = {name: sum(o) for name, o in rows[1:]}
print(f"M_core = {m_core:,}   sum M_p = {sum(m_p.values()):,}   M = {m_core + sum(m_p.values()):,}")

def night(scale):
    """T in seconds with every t_p divided by scale."""
    sf = sum(f for f, _ in FT.values())
    st = sum(t for _, t in FT.values()) / 1000 / scale
    return (m_core * (sf + P * st)
            + sum(m_p[p] * (f + P * t / 1000 / scale) for p, (f, t) in FT.items()))

fixed = m_core * sum(f for f, _ in FT.values()) + sum(m_p[p] * f for p, (f, _) in FT.items())
var = P * (m_core * sum(t for _, t in FT.values()) + sum(m_p[p] * t for p, (_, t) in FT.items())) / 1000
print(f"sum f_p = {sum(f for f, _ in FT.values()):.3f} s   sum t_p = {sum(t for _, t in FT.values()):.3f} ms")
print(f"T today = {night(1.0):,.0f} s = {night(1.0) / 3600:.2f} h   fixed terms = {fixed:,.0f} s = {fixed / 3600:.2f} h")
if fixed >= NIGHT:
    print("fixed terms alone exceed 10 h: no speed-up of t_p reaches the night; the fixed cost is binding")
else:
    s = var / (NIGHT - fixed)
    print(f"s = {s:.3f}   target sum t_p / s = {sum(t for _, t in FT.values()) / s:.3f} ms   "
          f"T at target = {night(s):,.2f} s = {night(s) / 3600:.4f} h")
    for p, (f, t) in FT.items():
        print(f"  {p:<34} t_p = {t:7.3f} ms   target t_p / s = {t / s:6.3f} ms")
EOF
```

Output at `790706b`:

```text
space                                 O1    O2    O3    O4    O5    O6  total
core                                  30    26    95     4     4    27    186
basisrente                           240    74   184    34    56    42    630
berufsunfaehigkeit                   105    32   288     5    42    35    507
fondsgebundene_rentenversicherung     87    64   204     5    36    32    428
indexpolice                           72    60   131     8    46    29    346
kapitallebensversicherung             96    42   190    10    66    18    422
klassische_rentenversicherung        162    64   217    13    54    76    586
pflegerentenversicherung             177    64   440     6    80    55    822
riester_rente                        186    58   243    34    44    33    598
risikolebensversicherung              78    40   134     8    16    19    295
sofortrente                          123    66   182     8    48    58    485
M_core = 186   sum M_p = 5,119   M = 5,305
sum f_p = 20.294 s   sum t_p = 137.756 ms
T today = 132,794 s = 36.89 h   fixed terms = 14,546 s = 4.04 h
s = 5.512   target sum t_p / s = 24.993 ms   T at target = 36,000.00 s = 10.0000 h
  basisrente                         t_p =   9.383 ms   target t_p / s =  1.702 ms
  berufsunfaehigkeit                 t_p =  10.031 ms   target t_p / s =  1.820 ms
  fondsgebundene_rentenversicherung  t_p =   8.431 ms   target t_p / s =  1.530 ms
  indexpolice                        t_p =   4.515 ms   target t_p / s =  0.819 ms
  kapitallebensversicherung          t_p =   5.659 ms   target t_p / s =  1.027 ms
  klassische_rentenversicherung      t_p =  14.063 ms   target t_p / s =  2.551 ms
  pflegerentenversicherung           t_p =  72.018 ms   target t_p / s = 13.066 ms
  riester_rente                      t_p =   4.298 ms   target t_p / s =  0.780 ms
  risikolebensversicherung           t_p =   2.522 ms   target t_p / s =  0.458 ms
  sofortrente                        t_p =   6.836 ms   target t_p / s =  1.240 ms
```

**Result.** M_core = 186, Σ M_p = 5,119, M = 5,305, more than ten times the 500 of phase 1. At the speeds of 2026-10-28 all ten products take T ≈ 132,794 s ≈ 36.9 h, a factor of 3.7 over the night; the fixed-cost terms are 14,546 s ≈ 4.0 h of it, below 10 h, so the night is reachable by the per-contract time alone. The target is `s` ≈ 5.51: Σ t_p from 137.8 ms down to 25.0 ms at W = 24, with the fixed cost unchanged; T at the targets is 36,000 s. The first count at `f07f003` gave Σ M_p = 5,114, M = 5,300, T ≈ 130,216 s ≈ 36.2 h and `s` ≈ 5.38 (target Σ t_p 25.6 ms); of the cells epic-night-run changed since (PRs #26 to #37), those of BU, KLV, RV and Pflege moved the counts (last column).

| Product | M_p | f_p (s) | t_p (ms) | target t_p / s (ms) | M_p at `f07f003` |
|---|---:|---:|---:|---:|---:|
| core (runs all ten) | 186 | | | | 186 |
| `basisrente` | 630 | 1.886 | 9.383 | 1.702 | 630 |
| `berufsunfaehigkeit` | 507 | 1.993 | 10.031 | 1.820 | 550 |
| `fondsgebundene_rentenversicherung` | 428 | 1.969 | 8.431 | 1.530 | 428 |
| `indexpolice` | 346 | 1.842 | 4.515 | 0.819 | 346 |
| `kapitallebensversicherung` | 422 | 1.908 | 5.659 | 1.027 | 418 |
| `klassische_rentenversicherung` | 586 | 2.080 | 14.063 | 2.551 | 582 |
| `pflegerentenversicherung` | 822 | 2.970 | 72.018 | 13.066 | 782 |
| `riester_rente` | 598 | 2.007 | 4.298 | 0.780 | 598 |
| `risikolebensversicherung` | 295 | 1.778 | 2.522 | 0.458 | 295 |
| `sofortrente` | 485 | 1.861 | 6.836 | 1.240 | 485 |
| Σ | 5,119 | 20.294 | 137.756 | 24.993 | 5,114 |

One factor `s` for every product is the bookkeeping of the target, not a plan: a product that gets faster than its `t_p / s` buys time for one that stays slower, as long as T stays at or below 10 h. `pflegerentenversicherung` is about half of Σ t_p and the largest lever.

## Where phase 3 ended

Phase 3 is done (2026-10-31): the common core is delivered (above) and so is the night run. All ten products together, at the new M = 5,300 (M_core = 186, Σ M_p = 5,114, section "The new M"), P = 10,000 contracts (1,000 per product), W = 24, fixed cost per mutant included, are forecast at **5.5 h, within the 10 h night**. Measured by `tools/measure_marginal.py --all --workers 24` on `94294d6` (merge of PR #34, the final code of epic-night-run; details in [performance.md](performance.md), "Phase 3: night measurement"): Σ t_marginal = 15.7 ms, below the target of 25.6 ms (`s` ≈ 5.38), and Σ fixed = 11.21 s, against 137.8 ms and 20.3 s with the core on 2026-10-28 and 36.2 h then. `pflegerentenversicherung` fell from 72.0 to 3.47 ms. The same command on the same code gave 4.7 h before the merge of PR #34 (Σ t 12.9 ms); the cause of the difference is not established, both lie well within the night, and the higher figure is the recorded one. R9, the night-run criterion of the phase-3 initiative, holds, so no decision between the trace rule and the criterion was needed (epic-night-run, N6). The trace stays: every product runs under `--engine modelx` point by point with all checks true and its results equal to its pin.

The forecast keeps the assumptions of "The new M": a linear extrapolation without trace pruning, the coverage filter ignored, the mutant counts at `f07f003`; mutants exist only after phase 4, so it is a forecast, not a measurement.

## Decisions

- Phase 3 goes through all ten products together, not product by product: one commit unifies one quantity in every product, and one PR is one group of quantities (2026-10-25, reported to the strategist the same day). It replaces the product order of 2026-10-24, which started with `risikolebensversicherung` and ended with `pflegerentenversicherung`; `risikolebensversicherung` stayed the probe for the first core cell.
- Lower bound of the core quota: 20 % for every product, no exception (2026-10-28); BU since then its own bound at its measured quota, 28 of 148 (Moritz, 2026-10-29, epic-night-run variant c, as recorded in `3ab6cbc`; story 2.16).
- Contract pool for the night-run criterion: P = 10,000 contracts for now; in phase 2 per product, in phase 3 for all ten products together, 1,000 each.
- Counting the new M (2026-10-28, section "The new M"): numeric literals by Python type, an `int` 2 mutants and a `float` 1, with `0`, `1`, `0.0`, `1.0` excluded by value (F3); the built-in checks and comparisons guarding a `raise` are counted like any other code; the coverage filter is ignored, every mutant runs all 1,000 contracts of its products (conservative); the target speed is one factor `s` on every product's `t_marginal`, with the fixed costs as measured. Recounted with the same command on 2026-11-02 at `790706b` (M = 5,305), the speeds of 2026-10-28 kept.

## Open questions

- Equivalent-mutant sites left in BU for phase 4: the `karenz_months() == 0` branches of `pv_claim_cost_first` and `claim_expenses` read the whole disabled ledger (`pols_dis_first(s)`, `pols_dis(t)`) where the general path sums the same array from slot `karenz_months() + 1` on, which at K = 0 gives the same bits. A mutant that makes the branch take the general path at K = 0 (the condition dropped or its literal changed to a value no shipped point carries) is therefore equivalent and survives. The branches stay because they are the speed: `pols_dis` and `pols_dis_first` are evaluated in every month anyway, so the general path adds one more sum over the cohort vector per month and order; with the branches removed, BU's `t_marginal` at W = 24 rose from 2.53 to 2.64 ms, by more than `main`'s own spread of 0.03 ms (`measure_marginal berufsunfaehigkeit --workers 24 --repeats 5`, four alternating runs each against `main`, 2026-10-31, story "Mutation domain of Pflege and BU before phase 4"). Phase 4 has to mark them as equivalent or exclude them from the mutant count.
- Visibility of this repository: private for now. The licence is MIT, like upstream lifelib and delib-history.
- Contract pool for the night-run criterion: the generator.
