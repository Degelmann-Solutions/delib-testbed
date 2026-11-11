"""The stored per-product baseline of phase 1.

For every product the runner runs on the shipped model points and writes its
``result_cf.csv`` to a temporary folder. The tests pin the check cells, the recipe hash
the runner prints and the SHA-256 of ``baseline/<product>/result_cf.csv``, and read the
stored file back to the recipe hash, which proves that the file round-trips exactly.

A commit that moves a result changes these pins on purpose and updates them in the same
commit. The hashes are taken from raw 64-bit floats and have been confirmed on one machine.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_baseline.py"
BASELINE_DIR = ROOT / "baseline"

# product: (model points, check cells, recipe hash, SHA-256 of baseline/<product>/result_cf.csv)
BASELINE = {
    "basisrente": (
        13,
        ("check_annuity_roll_fwd", "check_av_roll_fwd", "check_conversion", "check_net_cf",
         "check_no_capital", "check_pols_roll_fwd"),
        "1a956a09391fd7075cf89bafc470f7a68149f393e808f88872cacb16fe29f46b",
        "76e715d858300d3c3bc696505ec952e16fa56165d619487c6454475055aa6c17",
    ),
    "berufsunfaehigkeit": (
        13,
        ("check_cover_end", "check_dis_roll_fwd", "check_net_cf", "check_pols_roll_fwd",
         "check_prem_split", "check_runoff_roll_fwd", "check_states"),
        "1200bb75e64ee2717bd1be199946da5a9fc74396feab045e8dd57602fd103962",
        "aa7631f2343f699dc075440b0928f648520fb7575fdf730d7fe2b0b150e8566a",
    ),
    "fondsgebundene_rentenversicherung": (
        13,
        ("check_acq_charge", "check_av_roll_fwd", "check_benefit_funding", "check_net_cf",
         "check_pols_roll_fwd", "check_prem_split", "check_units_roll_fwd"),
        "5192889291029e236a6a3e596fd21d7c116431c58e9cd707d160a7b6751478a6",
        "c85973f4cfe6c96547900d10bd0d8d711467cad5373bb696961d07e17a38a865",
    ),
    "indexpolice": (
        13,
        ("check_av_roll_fwd", "check_index_credit", "check_lock_in", "check_net_cf",
         "check_pols_roll_fwd", "check_surplus_alloc"),
        "262bdd337e4ecdfe2ec2da67e3fb84b645bd60fe8ee3667ac3d3bc173b72b060",
        "7f734e5bf6ab90dfc9717bdae4519542c8f27125f94918440d4e3edeb7635449",
    ),
    "kapitallebensversicherung": (
        14,
        ("check_decrement_closure", "check_equivalence", "check_net_cf", "check_pols_roll_fwd",
         "check_rechnungszins_cap", "check_res_roll_fwd", "check_surplus_roll_fwd",
         "check_surr_floor", "check_surr_nonneg", "check_zillmer_cap"),
        "b4eb8092ced889e9ac0f229dc4a374a709246836daf2899fecfeb6298ae7d311",
        "851a9b74cbb5fc499dbafa16aeb3993654fd55f38a2a01774623167d831092fd",
    ),
    "klassische_rentenversicherung": (
        14,
        ("check_annuity_conv", "check_annuity_guarantee", "check_av_roll_fwd",
         "check_av_sur_roll_fwd", "check_cv_floor", "check_decrement_closure", "check_net_cf",
         "check_pols_roll_fwd", "check_prem_split"),
        "dcbda7929a0ec5d654c368061c5380528efc8dc8712851e385db86ae8e80ce5b",
        "cf9e4b3a2d781b3de18883f996bdf95415ad34607e1e446cf97b14cf3e6720fb",
    ),
    "pflegerentenversicherung": (
        14,
        ("check_esc_ledger", "check_net_cf", "check_pols_roll_fwd", "check_prem_equiv",
         "check_states", "check_waiver"),
        "4ac42207035fadf16fbc4ea56ed3bbf21068a6263de3ee473c3f4708204d0111",
        "99ae33f23a1894ec84deebbc309267cc290cb1707e80918ee98d0d709382c7a7",
    ),
    "riester_rente": (
        13,
        ("check_av_roll_fwd", "check_conversion", "check_guar_roll_fwd", "check_net_cf",
         "check_pols_roll_fwd", "check_zulage_lag"),
        "91b6a3faf175b0d437c1ccf19113f6543a73cc8add4c07ad1c58d231ed6be03a",
        "736388e3f32fa5593af50116e88d4b2a5935efe61f80cba50105b7d861e673d7",
    ),
    "risikolebensversicherung": (
        14,
        ("check_net_cf", "check_no_cash_value", "check_pols_roll_fwd", "check_prem_split",
         "check_res_roll_fwd"),
        "e0f605d443fc56b06e776ffd27c007928caa42cd91ebd05ddeb8c643d026097f",
        "a1740feecc92fd41a7312ccbcbfa849798e586f47de8c1e3a011e05b462627e2",
    ),
    "sofortrente": (
        14,
        ("check_annuity_roll_fwd", "check_death_option_xor", "check_equivalence",
         "check_guarantee_certain", "check_lives_roll_fwd", "check_net_cf",
         "check_payment_factor", "check_refund_run_off", "check_tariff_int_rate"),
        "fb4644f8a7f74d09d2d0f73029cb8c9c9f5e026f4237fbbca6d3e48d15afdffd",
        "195d2c63fdd3dec208aa070b8f70d4224c5d01abe69cd49c87629d2f9b92f3b4",
    ),
}


def parse_output(stdout: str) -> dict[str, str]:
    return dict(line.split(": ", 1) for line in stdout.splitlines() if ": " in line)


def recipe_hash_of_csv(data: bytes) -> str:
    """The runner's hash recipe, recomputed from a stored ``result_cf.csv``."""
    lines = data.decode("ascii").split("\n")
    assert lines[-1] == "", "the file ends with a line end"
    header = lines[0].split(",")
    assert header[:2] == ["point_id", "t"]
    columns = header[2:]
    rows: dict[int, list[list[str]]] = {}
    for line in lines[1:-1]:
        fields = line.split(",")
        assert len(fields) == len(header)
        rows.setdefault(int(fields[0]), []).append(fields[1:])
    assert list(rows) == sorted(rows), "points are ascending"
    digest = hashlib.sha256()
    for point_id, point_rows in rows.items():
        index = np.array([int(r[0]) for r in point_rows], dtype="<i8")
        values = np.array([[float(v) for v in r[1:]] for r in point_rows], dtype="<f8")
        digest.update((f"point_id={point_id}\n"
                       f"columns={','.join(columns)}\n"
                       f"shape={values.shape[0]},{values.shape[1]}\n").encode("utf-8"))
        digest.update(index.tobytes())
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


@pytest.fixture(scope="session")
def runs(tmp_path_factory):
    """Run every product with ``--write`` to a temporary folder, all in parallel processes."""
    out = tmp_path_factory.mktemp("baseline")
    processes = {
        product: subprocess.Popen(
            [sys.executable, str(RUNNER), product, "--write", "--out", str(out / product)],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for product in BASELINE}
    results = {}
    for product, process in processes.items():
        stdout, stderr = process.communicate(timeout=900)
        results[product] = (process.returncode, parse_output(stdout), stderr,
                            out / product / "result_cf.csv")
    return results


def test_every_product_has_a_baseline():
    assert {p.name for p in (ROOT / "products").iterdir() if p.is_dir()} == set(BASELINE)
    assert {p.name for p in BASELINE_DIR.iterdir()} == set(BASELINE)
    for product in BASELINE:
        assert [p.name for p in (BASELINE_DIR / product).iterdir()] == ["result_cf.csv"]


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_runner_finds_the_pinned_checks(runs, product):
    _, checks, _, _ = BASELINE[product]
    assert runs[product][1]["check cells"] == ",".join(checks)


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_product_runs_with_all_checks_true_and_the_pinned_hash(runs, product):
    points, _, recipe_hash, _ = BASELINE[product]
    code, output, stderr, _ = runs[product]
    assert code == 0, stderr
    assert output["checks"] == "all true"
    assert int(output["model points"]) == points
    assert output["sha256"] == recipe_hash


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_written_file_equals_the_stored_baseline(runs, product):
    _, _, _, file_hash = BASELINE[product]
    stored = (BASELINE_DIR / product / "result_cf.csv").read_bytes()
    assert hashlib.sha256(stored).hexdigest() == file_hash
    assert runs[product][3].read_bytes() == stored


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_stored_baseline_reads_back_to_the_recipe_hash(product):
    points, _, recipe_hash, _ = BASELINE[product]
    stored = (BASELINE_DIR / product / "result_cf.csv").read_bytes()
    assert b"\r" not in stored
    assert recipe_hash_of_csv(stored) == recipe_hash
    assert len({line.split(b",", 1)[0] for line in stored.split(b"\n")[1:-1]}) == points


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_run_script_prints_without_error(product):
    """Each product's ``run.py``, the hand-run demo, exits 0 and prints its checks.

    No other test runs these scripts; Sofort's crashed at its check loop for nine days
    because it called the core's ``check_net_cf_tol(t)`` without ``t``.
    """
    done = subprocess.run([sys.executable, str(ROOT / "products" / product / "run.py")],
                          capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr
    assert "checks" in done.stdout
