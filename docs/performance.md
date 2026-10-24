# Performance: reference measurement of phase 2a, and the phase-2b, phase-2c and phase-2d measurements next to it

The marginal time per contract of every product, measured with `tools/measure_marginal.py` on the unchanged phase-1 runner. Later phase-2 changes are measured with the same tool against this table.

The 2a reference was measured at `10c2ad8`, before the runner had per-contract cleanup. Since phase 2b the runner cleans up by default, since phase 2c it runs on the exported model by default, and since phase 2d it can run the points in worker processes and the tool measures at several worker counts with K = 32 by default; reproducing the 2a table with the current tool needs `--factor 2 --engine modelx --no-cleanup`, the 2b table `--factor 2 --engine modelx`, the 2c table `--factor 2 --workers 1`. The phase-2b, phase-2c and phase-2d measurements follow in their own sections below.

**Timings depend on the machine.** They compare changes on one machine; they are not a property of the model.

- Date: 2026-10-23
- Commit: `10c2ad819fc00cf967dc0993d1be3a85a96c0682`, clean tree
- Machine: 12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2a.json` (defaults: factor K = 2, repeats R = 3, M = 500, P = 10,000, W = 1); exit 0, every run verified, wall time 27 min

## Method

Each product runs at two sizes in scratch copies: its shipped `n` points and `K·n` points whose ids `n+1 … K·n` repeat ids `1 … n`. Every (size, repeat) is a fresh process, one at a time, sizes alternating. `T` is the median time of `run_product` (`read_model`, `result_cf`, all checks, hashing); the import of the runner and modelx is timed separately.

- `t_marginal = (T(K·n) − T(n)) / ((K−1)·n)`
- `fixed = import + T(n) − n·t_marginal`
- `MB/contract = (RSS(K·n) − RSS(n)) / ((K−1)·n)`, from the median peak RSS

Every run is verified: no point failed, every id present, every replicated point's `result_cf` equal to its original's, and points `1 … n` reproduce `baseline/<product>/result_cf.csv` byte for byte.

## Result

| Product | n | K·n | T(n) s | T(K·n) s | import s | fixed s | t_marginal ms | RSS(n) MB | RSS(K·n) MB | MB/contract |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 13 | 26 | 7.00 | 13.83 | 0.10 | 0.27 | 525 | 516 | 944 | 32.9 |
| berufsunfaehigkeit | 13 | 26 | 6.85 | 12.19 | 0.09 | 1.59 | 411 | 640 | 1194 | 42.6 |
| fondsgebundene_rentenversicherung | 13 | 26 | 6.40 | 14.02 | 0.10 | −1.13 | 586 | 487 | 886 | 30.7 |
| indexpolice | 13 | 26 | 3.09 | 6.08 | 0.10 | 0.19 | 230 | 231 | 373 | 10.9 |
| kapitallebensversicherung | 14 | 28 | 10.45 | 17.04 | 0.10 | 3.96 | 471 | 731 | 1374 | 46.0 |
| klassische_rentenversicherung | 14 | 28 | 56.58 | 114.04 | 0.10 | −0.78 | 4105 | 4583 | 9076 | 320.9 |
| pflegerentenversicherung | 14 | 28 | 47.93 | 97.13 | 0.10 | −1.17 | 3514 | 2416 | 4756 | 167.1 |
| riester_rente | 13 | 26 | 5.32 | 10.40 | 0.10 | 0.33 | 391 | 465 | 842 | 29.0 |
| risikolebensversicherung | 14 | 28 | 5.02 | 9.92 | 0.10 | 0.22 | 350 | 460 | 833 | 26.6 |
| sofortrente | 14 | 28 | 6.14 | 12.64 | 0.10 | −0.27 | 465 | 499 | 909 | 29.3 |

Status `ok` for all ten products.

Observations:

- The run is almost entirely per-contract cost. The fixed cost (import and `read_model`) is a fraction of a second to about 4 s; for four products it comes out slightly negative, that is, `T(K·n)` is a little more than twice `T(n)`. That is within noise of the medians or a first hint that time per contract grows with `n` while every ItemSpace stays alive; two sizes cannot tell which.
- Memory grows linearly with the contracts held: 11 to 46 MB per contract for eight products, 167 MB for `pflegerentenversicherung` and 321 MB for `klassische_rentenversicherung`.

## Forecast

Assumptions: M = 500 mutants, P = 10,000 contracts, W = 1 worker, for each product on its own; the slope is taken from each product's shipped point mix; two sizes only, so linearity is assumed, not tested. This is a linear extrapolation without trace pruning, and a forecast, not a measurement: mutants exist only after phase 4. The night is 10 h, the exit criterion of phase 2 in the README; it needs `t_marginal ≤ 7.2 ms` at W = 1.

| Product | M·P·t_marginal/W | M·(fixed + P·t_marginal)/W | MB/contract × P, one process |
|---|---:|---:|---:|
| basisrente | 729.3 h | 729.4 h | 321.5 GB |
| berufsunfaehigkeit | 571.1 h | 571.3 h | 416.0 GB |
| fondsgebundene_rentenversicherung | 814.5 h | 814.3 h | 299.5 GB |
| indexpolice | 319.7 h | 319.8 h | 106.9 GB |
| kapitallebensversicherung | 653.6 h | 654.1 h | 448.7 GB |
| klassische_rentenversicherung | 5700.7 h | 5700.6 h | 3134.1 GB |
| pflegerentenversicherung | 4880.4 h | 4880.3 h | 1631.9 GB |
| riester_rente | 543.6 h | 543.6 h | 283.0 GB |
| risikolebensversicherung | 486.0 h | 486.0 h | 260.0 GB |
| sofortrente | 645.4 h | 645.4 h | 286.2 GB |

No product fits the 10 h night: the gap is a factor of about 32 (`indexpolice`) to 570 (`klassische_rentenversicherung`). For every product the extrapolated memory of one process exceeds the machine's 62.8 GiB, so a run over the pool needs per-contract cleanup before anything else.

# Phase 2b: per-contract cleanup

The same measurement with the runner's per-contract cleanup on (the default since phase 2b): after a point's `result_cf` and checks are read, its ItemSpace is deleted (`del model.Projection[point_id]`). Nothing else changed; how cells are computed and traced is the same.

- Date: 2026-10-24
- Commit: `822591f20093968c7d809524b765f5fb0d865f58`, clean tree
- Machine: the same as for 2a (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2b.json` (defaults: cleanup on, factor K = 2, repeats R = 3, M = 500, P = 10,000, W = 1); exit 0, every run verified, wall time 28 min

## Result

| Product | n | K·n | T(n) s | T(K·n) s | import s | fixed s | t_marginal ms | RSS(n) MB | RSS(K·n) MB | MB/contract (noise) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 13 | 26 | 8.71 | 17.21 | 0.10 | 0.31 | 654 | 139 | 142 | 0.2 |
| berufsunfaehigkeit | 13 | 26 | 8.01 | 15.77 | 0.10 | 0.36 | 597 | 157 | 159 | 0.2 |
| fondsgebundene_rentenversicherung | 13 | 26 | 8.19 | 16.45 | 0.10 | 0.04 | 635 | 141 | 143 | 0.1 |
| indexpolice | 13 | 26 | 3.15 | 6.11 | 0.10 | 0.27 | 228 | 107 | 108 | 0.1 |
| kapitallebensversicherung | 14 | 28 | 12.09 | 23.08 | 0.10 | 1.19 | 785 | 144 | 144 | −0.0 |
| klassische_rentenversicherung | 14 | 28 | 73.09 | 131.42 | 0.10 | 14.86 | 4166 | 542 | 544 | 0.1 |
| pflegerentenversicherung | 14 | 28 | 52.28 | 108.36 | 0.10 | −3.70 | 4005 | 389 | 395 | 0.4 |
| riester_rente | 13 | 26 | 6.04 | 11.92 | 0.09 | 0.26 | 452 | 136 | 139 | 0.2 |
| risikolebensversicherung | 14 | 28 | 5.52 | 10.89 | 0.09 | 0.24 | 384 | 149 | 150 | 0.1 |
| sofortrente | 14 | 28 | 7.57 | 14.95 | 0.09 | 0.28 | 528 | 132 | 134 | 0.1 |

Status `ok` for all ten products: replicas equal their originals and points `1 … n` reproduce `baseline/` byte for byte, as in 2a. Separately, for every product the runner's sha256 and `--write` bytes are identical with and without `--no-cleanup`.

**Memory figure under cleanup: peak RSS per size.** With cleanup, at most one point's ItemSpace is alive, so the peak RSS hardly depends on the number of points: `RSS(n)` and `RSS(K·n)` differ by 0 to 6 MB. `MB/contract` is the difference of two nearly equal medians divided by `n`, that is noise (it even comes out slightly negative for `kapitallebensversicherung`), and so is its extrapolation `MB/contract × P` in the tool's forecast lines. The peak RSS of one process is the figure to use, and it is not expected to grow with P.

## Comparison with 2a

| Product | t_marginal 2a ms | t_marginal 2b ms | change | RSS(n) 2a MB | RSS(n) 2b MB | RSS(K·n) 2a MB | RSS(K·n) 2b MB | RSS(K·n) 2a / 2b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 525 | 654 | +25 % | 516 | 139 | 944 | 142 | 6.7× |
| berufsunfaehigkeit | 411 | 597 | +45 % | 640 | 157 | 1194 | 159 | 7.5× |
| fondsgebundene_rentenversicherung | 586 | 635 | +8 % | 487 | 141 | 886 | 143 | 6.2× |
| indexpolice | 230 | 228 | −1 % | 231 | 107 | 373 | 108 | 3.5× |
| kapitallebensversicherung | 471 | 785 | +67 % | 731 | 144 | 1374 | 144 | 9.5× |
| klassische_rentenversicherung | 4105 | 4166 | +1 % | 4583 | 542 | 9076 | 544 | 16.7× |
| pflegerentenversicherung | 3514 | 4005 | +14 % | 2416 | 389 | 4756 | 395 | 12.0× |
| riester_rente | 391 | 452 | +16 % | 465 | 136 | 842 | 139 | 6.1× |
| risikolebensversicherung | 350 | 384 | +10 % | 460 | 149 | 833 | 150 | 5.5× |
| sofortrente | 465 | 528 | +13 % | 499 | 132 | 909 | 134 | 6.8× |

- **Memory:** peak RSS at K·n falls by a factor of 3.5 (`indexpolice`) to 17 (`klassische_rentenversicherung`); every product now peaks between 108 and 544 MB, against 373 to 9,076 MB in 2a, and no longer grows with the points held. The extrapolated RAM blocker of 2a is gone.
- **Time:** cleanup does not make the run faster. `t_marginal` lies between −1 % and +67 % of the 2a value; the large changes come with a large spread of the single runs (`kapitallebensversicherung` K·n: 21.8, 23.1 and 28.9 s; `klassische_rentenversicherung` n: 63.8 to 88.8 s). A same-day control with both modes back to back on three products (R = 3, not committed as a table) gave with/without cleanup: `risikolebensversicherung` 395 / 324 ms, `kapitallebensversicherung` 506 / 567 ms, `berufsunfaehigkeit` 473 / 463 ms. The effect of cleanup on time is therefore within the noise of this measurement, perhaps a small cost for the cheap products; it is not a speed-up. So the time per contract is not driven by the memory that the live ItemSpaces held in 2a.

## Forecast

Assumptions as in 2a: M = 500 mutants, P = 10,000 contracts, W = 1 worker, each product on its own, slope from the shipped point mix, linearity assumed, not tested; a linear extrapolation without trace pruning and a forecast, not a measurement. The night needs `t_marginal ≤ 7.2 ms` at W = 1.

| Product | M·P·t_marginal/W | M·(fixed + P·t_marginal)/W | gap to 10 h |
|---|---:|---:|---:|
| basisrente | 908.0 h | 908.0 h | 91× |
| berufsunfaehigkeit | 828.7 h | 828.8 h | 83× |
| fondsgebundene_rentenversicherung | 881.9 h | 881.9 h | 88× |
| indexpolice | 317.2 h | 317.3 h | 32× |
| kapitallebensversicherung | 1090.8 h | 1091.0 h | 109× |
| klassische_rentenversicherung | 5786.5 h | 5788.6 h | 579× |
| pflegerentenversicherung | 5563.2 h | 5562.7 h | 556× |
| riester_rente | 627.9 h | 628.0 h | 63× |
| risikolebensversicherung | 532.8 h | 532.9 h | 53× |
| sofortrente | 732.7 h | 732.7 h | 73× |

No product fits the 10 h night: the gap is a factor of about 32 (`indexpolice`) to 579 (`klassische_rentenversicherung`), as in 2a. Memory no longer limits a run over the pool: one process stays at its peak RSS of 108 to 544 MB, so many processes fit side by side in 62.8 GiB. The remaining gap is time; it is what process parallelism (planned as 2c at the time, now phase 2d) addresses, even perfect scaling over the 24 logical CPUs (W = 24) would leave a factor of about 1.3 to 24.

# Phase 2c: export engine

The same measurement with the runner's export engine (the default since phase 2c): the runner reads the model with modelx, exports it with `mx.export_model` into a package in a temporary folder and runs the points and checks on the exported model, which computes the same formulas without modelx's per-cell trace and dependency graph. Per-contract cleanup is on, as in 2b. The export lands in `run_product` and so in `T` and the fixed cost.

- Date: 2026-10-24
- Commit: `eb36f86d0684cb3950566c3a7007194a9fd9ee04`, clean tree (measured as `5160484`; rebasing a docstring-only rewording into the runner commit gave it this hash, the code is identical)
- Machine: the same as for 2a and 2b (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2c.json` (defaults: engine export, cleanup on, factor K = 2, repeats R = 3, M = 500, P = 10,000, W = 1); exit 0, every run verified, wall time 4.2 min

## Result

| Product | n | K·n | T(n) s | T(K·n) s | import s | fixed s | t_marginal ms | RSS(n) MB | RSS(K·n) MB | MB/contract |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 13 | 26 | 2.23 | 3.35 | 0.10 | 1.20 | 86 | 127 | 138 | 0.8 |
| berufsunfaehigkeit | 13 | 26 | 2.17 | 3.21 | 0.09 | 1.22 | 80 | 233 | 254 | 1.6 |
| fondsgebundene_rentenversicherung | 13 | 26 | 2.07 | 2.87 | 0.09 | 1.37 | 61 | 122 | 134 | 0.9 |
| indexpolice | 13 | 26 | 1.91 | 2.69 | 0.09 | 1.23 | 60 | 120 | 121 | 0.1 |
| kapitallebensversicherung | 14 | 28 | 2.31 | 3.25 | 0.10 | 1.46 | 67 | 123 | 124 | 0.0 |
| klassische_rentenversicherung | 14 | 28 | 2.96 | 4.51 | 0.09 | 1.50 | 111 | 132 | 135 | 0.2 |
| pflegerentenversicherung | 14 | 28 | 10.24 | 18.43 | 0.09 | 2.14 | 585 | 141 | 142 | 0.1 |
| riester_rente | 13 | 26 | 1.84 | 2.34 | 0.10 | 1.43 | 39 | 126 | 142 | 1.2 |
| risikolebensversicherung | 14 | 28 | 1.52 | 1.90 | 0.10 | 1.24 | 27 | 120 | 120 | −0.0 |
| sofortrente | 14 | 28 | 2.05 | 2.83 | 0.10 | 1.37 | 56 | 127 | 146 | 1.3 |

Status `ok` for all ten products: replicas equal their originals and points `1 … n` reproduce `baseline/` byte for byte. Separately, for every product the runner's sha256 and `--write` bytes are identical in the export and the modelx engine, and equal to `baseline/`.

The single runs are close together: the spread of `T` within a size is at most 0.3 s, except `pflegerentenversicherung` n (9.55 to 12.48 s).

**Memory.** Peak RSS stays between 120 and 254 MB. Unlike in 2b, `RSS(K·n)` lies above `RSS(n)` by the same amount in every repeat for five products (11 to 21 MB: `basisrente`, `berufsunfaehigkeit`, `fondsgebundene_rentenversicherung`, `riester_rente`, `sofortrente`). Checked on `basisrente` with `--repeats 1` (2026-10-24):

- In the exported code every ItemSpace sits in a reference cycle (`_mx_roots` in `modelx/export/exporter.py`), so `del Projection[point_id]` frees a point only when Python's cyclic garbage collector runs: over the 13 points the live `Projection` instances go 2, 3, 4, 2, … up to 9 without, and stay at 2 with a `gc.collect()` after each delete.
- The peak RSS grows with the points, but sublinearly: at n = 13 against K·n it is 127 / 137 MB at K = 2, 126 / 152 MB at K = 8, 126 / 170 MB at K = 16, about 0.2 MB per contract beyond 26 points rather than the 0.8 to 1.6 MB of the table's `MB/contract`, so the tool's linear `MB/contract × P` overstates it.
- A `gc.collect()` after each delete does not stop the growth (121 / 153 MB at K = 16) and raises `t_marginal` from about 83 to 129 ms, so the runner does not do it.

The remaining cause of the growth was open for phase 2d, and 2d answers it: it is the CSV lines the runner collected for every point of the run, whether or not they were written (a `tracemalloc` probe on `basisrente` at K = 16 showed +24.8 MiB from `csv_lines` between point 40 and point 207, with the count of Python objects flat), not the export engine; under modelx in 2b the same growth was hidden in the noise. Since 2d the runner collects the lines only with `--write`, and the measuring tool's child only those of the shipped points, comparing replicas by a digest per point. Checked by hand on `basisrente` without `--write` (2026-10-24): peak RSS 128 MB at 13 points, 138 MB at 26, 140 MB at 104, 142 MB at 208 and 142 MB at 832; it no longer grows with the points.

## Comparison with 2b

| Product | t_marginal 2b ms | t_marginal 2c ms | 2b / 2c | fixed 2b s | fixed 2c s |
|---|---:|---:|---:|---:|---:|
| basisrente | 654 | 86 | 7.6× | 0.31 | 1.20 |
| berufsunfaehigkeit | 597 | 80 | 7.5× | 0.36 | 1.22 |
| fondsgebundene_rentenversicherung | 635 | 61 | 10.4× | 0.04 | 1.37 |
| indexpolice | 228 | 60 | 3.8× | 0.27 | 1.23 |
| kapitallebensversicherung | 785 | 67 | 11.7× | 1.19 | 1.46 |
| klassische_rentenversicherung | 4166 | 111 | 37.7× | 14.86 | 1.50 |
| pflegerentenversicherung | 4005 | 585 | 6.8× | −3.70 | 2.14 |
| riester_rente | 452 | 39 | 11.6× | 0.26 | 1.43 |
| risikolebensversicherung | 384 | 27 | 14.2× | 0.24 | 1.24 |
| sofortrente | 528 | 56 | 9.4× | 0.28 | 1.37 |

- **Time per contract:** the export engine cuts `t_marginal` by a factor of 3.8 (`indexpolice`) to 38 (`klassische_rentenversicherung`); eight products now take 27 to 111 ms per contract, `pflegerentenversicherung` 585 ms. This confirms that most of the 2b cost was modelx's per-cell machinery, not the formulas.
- **Fixed cost:** it rises to 1.2 to 2.1 s, which is the export (about 1 s) plus `read_model`. The 2b fixed costs were noisy (from −3.7 to 14.9 s); the 2c ones are consistent.

## Forecast

Assumptions as in 2a and 2b: M = 500 mutants, P = 10,000 contracts, W = 1 worker, each product on its own, slope from the shipped point mix, linearity assumed, not tested; a linear extrapolation without trace pruning and a forecast, not a measurement. The night needs `t_marginal ≤ 7.2 ms` at W = 1.

| Product | M·P·t_marginal/W | M·(fixed + P·t_marginal)/W | gap to 10 h | gap at W = 24 |
|---|---:|---:|---:|---:|
| basisrente | 119.9 h | 120.0 h | 12× | 0.5× |
| berufsunfaehigkeit | 111.2 h | 111.4 h | 11× | 0.5× |
| fondsgebundene_rentenversicherung | 85.2 h | 85.4 h | 9× | 0.4× |
| indexpolice | 83.1 h | 83.3 h | 8× | 0.3× |
| kapitallebensversicherung | 93.5 h | 93.7 h | 9× | 0.4× |
| klassische_rentenversicherung | 153.7 h | 153.9 h | 15× | 0.6× |
| pflegerentenversicherung | 812.6 h | 812.9 h | 81× | 3.4× |
| riester_rente | 54.1 h | 54.3 h | 5× | 0.2× |
| risikolebensversicherung | 37.6 h | 37.7 h | 4× | 0.2× |
| sofortrente | 77.9 h | 78.1 h | 8× | 0.3× |

Still no product fits the 10 h night with one worker: the gap is a factor of about 4 (`risikolebensversicherung`) to 15 (`klassische_rentenversicherung`), and 81 for `pflegerentenversicherung`, against 32 to 579 in 2b. Under perfect scaling over the 24 logical CPUs (W = 24, phase 2d) nine products would fit, `pflegerentenversicherung` would not (factor 3.4). Perfect scaling is an assumption: 24 logical CPUs are not 24 full cores. The memory growth noted above is a point to watch in 2d, where it would add up over the workers.

# Phase 2d: process parallelism

The same measurement with the runner's worker processes (`--workers W`, new in 2d): the parent reads and exports the model once and forks `W` workers, which run single points on the exported model with per-contract cleanup; the parent takes their results in point order. The tool now runs every product at W = 1, 4, 8, 12, 16 and 24, each (W, size, repeat) in a fresh child, and `t_marginal(W)` is wall time per contract across all workers. Two further changes since 2c: the runner no longer collects the CSV lines of every point (see the memory paragraph of 2c), and every process runs with one BLAS/OpenMP thread.

- Date: 2026-10-24
- Commit: `433004b791e03f8382e6b12c7d4cce04139476d5`, clean tree
- Machine: the same as for 2a to 2c (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2d.json` (defaults: engine export, cleanup on, workers W = 1, 4, 8, 12, 16, 24, factor K = 32, repeats R = 3, M = 500, P = 10,000); exit 0, every run verified, wall time 63 min

K is 32 instead of 2: with many workers, the slope of the export engine is small against its fixed cost of about 1.4 s, and K·n = 416 or 448 points gives every worker at W = 24 about 18 points. At a large W, `T(n)` is a single wave of 13 or 14 points in parallel, so `t_marginal(W)` and `fixed(W)` are biased slightly low there; this is stated, not corrected.

**Memory figure: `mem`.** For W = 1 it is the peak RSS of the one process. For W > 1 it is the parent's peak RSS plus, summed over the workers, each worker's largest Pss after a point (read from `/proc/self/smaps_rollup` after every point's cleanup), so pages the workers share copy-on-write with the parent are not counted once per worker. Two biases are stated, not corrected: the Pss after a point's cleanup understates a worker's true peak during the point, and the pages the workers share with the parent are counted close to twice (fully in the parent's RSS, plus each worker's share in its Pss), so at W > 1 `mem` overstates by up to the parent's shared footprint (about 100 MB). `MB/contract` is given at W = 1 only.

## Result

Speed-up is `t_marginal(1) / t_marginal(W)` of the same product.

| Product | W | T(n) s | T(K·n) s | fixed s | t_marginal ms | speed-up | mem(n) MB | mem(K·n) MB | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| basisrente | 1 | 2.37 | 35.56 | 1.40 | 82.4 | 1.0× | 130 | 141 | ok |
| basisrente | 4 | 1.65 | 10.92 | 1.45 | 23.0 | 3.6× | 287 | 443 | ok |
| basisrente | 8 | 1.48 | 7.99 | 1.37 | 16.2 | 5.1× | 317 | 724 | ok |
| basisrente | 12 | 1.51 | 7.16 | 1.42 | 14.0 | 5.9× | 362 | 996 | ok |
| basisrente | 16 | 1.47 | 6.52 | 1.40 | 12.5 | 6.6× | 360 | 1254 | ok |
| basisrente | 24 | 1.54 | 6.14 | 1.49 | 11.4 | 7.2× | 340 | 1762 | ok |
| berufsunfaehigkeit | 1 | 2.14 | 30.11 | 1.33 | 69.4 | 1.0× | 238 | 262 | ok |
| berufsunfaehigkeit | 4 | 1.72 | 10.27 | 1.54 | 21.2 | 3.3× | 406 | 924 | ok |
| berufsunfaehigkeit | 8 | 1.48 | 7.59 | 1.37 | 15.2 | 4.6× | 432 | 1649 | ok |
| berufsunfaehigkeit | 12 | 1.48 | 6.60 | 1.41 | 12.7 | 5.5× | 479 | 2385 | ok |
| berufsunfaehigkeit | 16 | 1.55 | 6.43 | 1.49 | 12.1 | 5.7× | 475 | 3081 | ok |
| berufsunfaehigkeit | 24 | 1.62 | 6.08 | 1.57 | 11.1 | 6.3× | 454 | 4375 | ok |
| fondsgebundene_rentenversicherung | 1 | 2.07 | 28.37 | 1.32 | 65.3 | 1.0× | 123 | 146 | ok |
| fondsgebundene_rentenversicherung | 4 | 1.46 | 9.30 | 1.30 | 19.5 | 3.4× | 250 | 457 | ok |
| fondsgebundene_rentenversicherung | 8 | 1.40 | 6.79 | 1.32 | 13.4 | 4.9× | 300 | 734 | ok |
| fondsgebundene_rentenversicherung | 12 | 1.38 | 6.10 | 1.32 | 11.7 | 5.6× | 344 | 1016 | ok |
| fondsgebundene_rentenversicherung | 16 | 1.40 | 5.56 | 1.36 | 10.3 | 6.3× | 343 | 1204 | ok |
| fondsgebundene_rentenversicherung | 24 | 1.47 | 5.31 | 1.44 | 9.5 | 6.9× | 322 | 1471 | ok |
| indexpolice | 1 | 1.87 | 24.75 | 1.23 | 56.8 | 1.0× | 121 | 122 | ok |
| indexpolice | 4 | 1.37 | 8.50 | 1.23 | 17.7 | 3.2× | 235 | 347 | ok |
| indexpolice | 8 | 1.28 | 5.87 | 1.22 | 11.4 | 5.0× | 285 | 537 | ok |
| indexpolice | 12 | 1.24 | 5.23 | 1.20 | 9.9 | 5.7× | 327 | 720 | ok |
| indexpolice | 16 | 1.26 | 4.75 | 1.23 | 8.7 | 6.6× | 324 | 897 | ok |
| indexpolice | 24 | 1.32 | 4.47 | 1.31 | 7.8 | 7.3× | 305 | 1226 | ok |
| kapitallebensversicherung | 1 | 2.21 | 30.22 | 1.40 | 64.5 | 1.0× | 123 | 124 | ok |
| kapitallebensversicherung | 4 | 1.54 | 10.49 | 1.34 | 20.6 | 3.1× | 243 | 359 | ok |
| kapitallebensversicherung | 8 | 1.52 | 7.80 | 1.42 | 14.5 | 4.5× | 295 | 557 | ok |
| kapitallebensversicherung | 12 | 1.50 | 6.89 | 1.42 | 12.4 | 5.2× | 337 | 746 | ok |
| kapitallebensversicherung | 16 | 1.51 | 6.17 | 1.46 | 10.7 | 6.0× | 348 | 939 | ok |
| kapitallebensversicherung | 24 | 1.48 | 5.82 | 1.43 | 10.0 | 6.4× | 326 | 1270 | ok |
| klassische_rentenversicherung | 1 | 3.05 | 53.33 | 1.52 | 115.9 | 1.0× | 133 | 136 | ok |
| klassische_rentenversicherung | 4 | 1.79 | 15.77 | 1.43 | 32.2 | 3.6× | 357 | 426 | ok |
| klassische_rentenversicherung | 8 | 1.67 | 11.06 | 1.46 | 21.6 | 5.4× | 460 | 694 | ok |
| klassische_rentenversicherung | 12 | 1.76 | 10.69 | 1.57 | 20.6 | 5.6× | 399 | 944 | ok |
| klassische_rentenversicherung | 16 | 1.66 | 9.42 | 1.51 | 17.9 | 6.5× | 389 | 1201 | ok |
| klassische_rentenversicherung | 24 | 1.68 | 8.51 | 1.56 | 15.7 | 7.4× | 366 | 1687 | ok |
| pflegerentenversicherung | 1 | 10.75 | 294.06 | 1.71 | 652.8 | 1.0× | 141 | 143 | ok |
| pflegerentenversicherung | 4 | 4.50 | 79.71 | 2.16 | 173.3 | 3.8× | 416 | 453 | ok |
| pflegerentenversicherung | 8 | 3.69 | 55.71 | 2.10 | 119.9 | 5.4× | 635 | 731 | ok |
| pflegerentenversicherung | 12 | 3.84 | 50.94 | 2.41 | 108.5 | 6.0× | 772 | 1007 | ok |
| pflegerentenversicherung | 16 | 3.76 | 46.95 | 2.47 | 99.5 | 6.6× | 770 | 1277 | ok |
| pflegerentenversicherung | 24 | 3.57 | 43.33 | 2.38 | 91.6 | 7.1× | 752 | 1794 | ok |
| riester_rente | 1 | 1.45 | 10.94 | 1.23 | 23.5 | 1.0× | 126 | 146 | ok |
| riester_rente | 4 | 1.31 | 4.24 | 1.29 | 7.3 | 3.2× | 351 | 460 | ok |
| riester_rente | 8 | 1.20 | 3.13 | 1.22 | 4.8 | 4.9× | 309 | 759 | ok |
| riester_rente | 12 | 1.24 | 2.93 | 1.26 | 4.2 | 5.6× | 359 | 1040 | ok |
| riester_rente | 16 | 1.26 | 2.86 | 1.29 | 4.0 | 5.9× | 354 | 1311 | ok |
| riester_rente | 24 | 1.31 | 2.80 | 1.34 | 3.7 | 6.4× | 335 | 1594 | ok |
| risikolebensversicherung | 1 | 1.18 | 9.27 | 1.00 | 18.6 | 1.0× | 120 | 122 | ok |
| risikolebensversicherung | 4 | 1.05 | 3.62 | 1.05 | 5.9 | 3.2× | 233 | 360 | ok |
| risikolebensversicherung | 8 | 1.10 | 2.72 | 1.13 | 3.7 | 5.0× | 282 | 565 | ok |
| risikolebensversicherung | 12 | 1.07 | 2.62 | 1.10 | 3.6 | 5.2× | 322 | 741 | ok |
| risikolebensversicherung | 16 | 1.08 | 2.53 | 1.12 | 3.3 | 5.6× | 333 | 912 | ok |
| risikolebensversicherung | 24 | 1.11 | 2.46 | 1.15 | 3.1 | 6.0× | 313 | 1263 | ok |
| sofortrente | 1 | 1.70 | 23.09 | 1.09 | 49.3 | 1.0× | 129 | 150 | ok |
| sofortrente | 4 | 1.29 | 7.66 | 1.17 | 14.7 | 3.4× | 318 | 473 | ok |
| sofortrente | 8 | 1.16 | 5.33 | 1.12 | 9.6 | 5.1× | 302 | 796 | ok |
| sofortrente | 12 | 1.18 | 4.84 | 1.14 | 8.4 | 5.8× | 343 | 1093 | ok |
| sofortrente | 16 | 1.18 | 4.57 | 1.16 | 7.8 | 6.3× | 356 | 1396 | ok |
| sofortrente | 24 | 1.19 | 4.27 | 1.17 | 7.1 | 6.9× | 335 | 1830 | ok |

Status `ok` for all 60 (product, W) pairs: replicas equal their originals by digest and points `1 … n` reproduce `baseline/` byte for byte at every W. Separately, for every product the runner's sha256 and `--write` bytes are identical at W = 1 and W = 8, and equal to `baseline/`.

The single runs are close together: at W = 24 the three `T(K·n)` of a product lie within 0.2 s of each other (`pflegerentenversicherung` 42.5 to 44.6 s); at W = 1 the spread is up to 5 s for most products and 40 s for `pflegerentenversicherung` (264 to 304 s).

Observations:

- **Scaling:** every product gains from every step in W, but less than linearly: about 3.1 to 3.8× at W = 4, 4.5 to 5.4× at W = 8 and 6.0 to 7.4× at W = 24. The 24 logical CPUs are 16 cores (8 performance cores with two threads each and 8 efficiency cores), so W = 24 cannot give 24×; the gain from 16 to 24 workers is 7 to 14 %. The best W is 24 for every product.
- **W = 1 against 2c:** `t_marginal(1)` lies between −40 % (`riester_rente` 23.5 against 39 ms, `risikolebensversicherung` 18.6 against 27 ms) and +12 % (`pflegerentenversicherung` 653 against 585 ms) of the 2c value. 2c used K = 2, where the slope of nine products rested on a difference `T(K·n) − T(n)` of 0.4 to 1.6 s (`pflegerentenversicherung` 8 s); K = 32 measures it on a difference of 8 to 283 s. The effect of the single BLAS thread is not separable from this; it is not a large speed-up at W = 1.
- **Memory:** at W = 1 the peak RSS no longer grows with the points: `MB/contract` is 0.00 to 0.06, against 0.0 to 1.6 in 2c. With workers, `mem` grows with W, not with the points: each worker adds about 45 to 80 MB of its own (`berufsunfaehigkeit` about 170 MB), so `mem(K·n)` at W = 24 is 1.2 to 1.8 GB (`berufsunfaehigkeit` 4.4 GB), far below the machine's 62.8 GiB. `mem(n)` is lower than `mem(K·n)` because at n most workers have run one point or none.

## Forecast

Assumptions: M = 500 mutants, P = 10,000 contracts, each product on its own, slope from the shipped point mix, linearity assumed, not tested; a linear extrapolation without trace pruning and a forecast, not a measurement. Unlike in 2a to 2c, the forecast does not divide by W: `t_marginal(W)` is measured with W workers. The night is 10 h, which needs `t_marginal(W) ≤ 7.2 ms`.

| Product | t_marginal(1) ms | best W | t_marginal(best) ms | speed-up | M·P·t_marginal(1) | M·P·t_marginal(best) | M·(fixed + P·t_marginal), best | gap to 10 h, best W | mem(K·n) at best W MB | MB/contract at W = 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 82.4 | 24 | 11.4 | 7.2× | 114.4 h | 15.8 h | 16.1 h | 1.58× | 1762 | 0.03 |
| berufsunfaehigkeit | 69.4 | 24 | 11.1 | 6.3× | 96.4 h | 15.4 h | 15.6 h | 1.54× | 4375 | 0.06 |
| fondsgebundene_rentenversicherung | 65.3 | 24 | 9.5 | 6.9× | 90.6 h | 13.2 h | 13.4 h | 1.32× | 1471 | 0.06 |
| indexpolice | 56.8 | 24 | 7.8 | 7.3× | 78.9 h | 10.9 h | 11.0 h | 1.09× | 1226 | 0.00 |
| kapitallebensversicherung | 64.5 | 24 | 10.0 | 6.4× | 89.7 h | 13.9 h | 14.1 h | 1.39× | 1270 | 0.00 |
| klassische_rentenversicherung | 115.9 | 24 | 15.7 | 7.4× | 160.9 h | 21.9 h | 22.1 h | 2.19× | 1687 | 0.01 |
| pflegerentenversicherung | 652.8 | 24 | 91.6 | 7.1× | 906.7 h | 127.3 h | 127.6 h | 12.73× | 1794 | 0.00 |
| riester_rente | 23.5 | 24 | 3.7 | 6.4× | 32.7 h | 5.1 h | 5.3 h | 0.51× | 1594 | 0.05 |
| risikolebensversicherung | 18.6 | 24 | 3.1 | 6.0× | 25.9 h | 4.3 h | 4.5 h | 0.43× | 1263 | 0.00 |
| sofortrente | 49.3 | 24 | 7.1 | 6.9× | 68.5 h | 9.9 h | 10.0 h | 0.99× | 1830 | 0.05 |

With process parallelism at the best worker count, three products fit the 10 h night by the forecast: `risikolebensversicherung` (4.3 h), `riester_rente` (5.1 h) and, just, `sofortrente` (9.9 h, 10.0 h with the fixed cost per mutant). Six miss it by a factor of 1.1 (`indexpolice`) to 2.2 (`klassische_rentenversicherung`), and `pflegerentenversicherung` by a factor of 12.7. Against 2c at W = 1 (factor 4 to 15, `pflegerentenversicherung` 81) this is the gain of the workers; it is smaller than the "perfect scaling over 24 CPUs" of the 2c forecast (gap at W = 24 of 0.2 to 0.6, `pflegerentenversicherung` 3.4), because the measured speed-up at W = 24 is about 7×, not 24×.

This is as fast as the runner gets at runner level (export engine, per-contract cleanup, process parallelism), which is phase 2's exit criterion in the README. The remaining gap is documented here and is not a condition of phase 2; closing it needs changes to the model (phase 3) or trace pruning, more cores, or fewer mutants or contracts per night.
