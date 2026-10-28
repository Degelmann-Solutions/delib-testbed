"""List every baseline deviation from the tag ``phase-2-baseline`` with its marked commit.

    uv run python tools/baseline_deviations.py
    uv run python tools/baseline_deviations.py --json /tmp/deviations.json
    uv run python tools/baseline_deviations.py --repo path/to/repo --tag phase-2-baseline

The tool reads git only (``git`` in a subprocess, no modelx) and never writes to the
repository. ``--repo`` defaults to this repository's root, ``--tag`` to ``phase-2-baseline``.

Definition
----------
A **deviation** is a commit in ``<tag>..HEAD`` that changes a product's baseline
``baseline/<product>/result_cf.csv`` (R6, ``docs/core.md``, section "Commit trailers"). It is
the commit, not the net difference tag to HEAD: two commits that change one product's
baseline are two deviations, and a change reverted later is still one. Adding or removing the
file is a change. The products are every ``baseline/<product>/result_cf.csv`` at the tag, at
HEAD or touched by a commit in the range.

- A non-merge commit changes a baseline when the file differs from its parent's
  (``git log --full-history --no-merges``, so no side branch is simplified away).
- A merge commit changes a baseline only when the file (its blob, absent counting as one
  value) differs from every parent's: content no parent brings (an evil merge). A PR's change
  is listed at its branch commit.

A deviation is **marked** when its commit's trailer block has ``Result-Change`` naming the
product (comma-separated product folder names) and a non-empty ``Reason`` and ``Checked-By``.
The trailer block is the trailing paragraphs of the message, after the subject, that consist
only of ``Key: value`` lines, so trailers in their own paragraph before a ``Co-Authored-By``
paragraph are found and a key word inside a body sentence is not a trailer.

Checks
------
- **UNMARKED**: a deviation whose commit's ``Result-Change`` does not name the product.
- **INCOMPLETE**: a commit with ``Result-Change`` but without a non-empty ``Reason`` or
  ``Checked-By``; its deviations are not marked.
- **NO CHANGE**: a commit whose ``Result-Change`` names a product whose baseline that commit
  does not change.

Output
------
Without any deviation or problem: ``no baseline deviation from <tag> (<full sha>)``.
Otherwise a header line and one line per marked deviation, by product and oldest first:
``<product> <sha> <subject> -- Reason: <reason>``. Every problem goes to stderr, one line each,
starting with its check name. With ``--json FILE`` the tool also writes ``{"tag": sha,
"head": sha, "deviations": [{"product", "commit", "subject", "reason", "checked_by",
"marked"}], "problems": [...]}``.

Exit status: 0 if every deviation is marked and no problem is found; 1 otherwise; 2 on a usage
error (no git repository, a tag that does not resolve -- fetch it with ``git fetch --tags``).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TAG = "phase-2-baseline"
BASELINE_RE = re.compile(r"^baseline/([^/]+)/result_cf\.csv$")
TRAILER_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9-]*):[ \t]*(.*)$")
REQUIRED = (("result-change", "Result-Change"), ("reason", "Reason"), ("checked-by", "Checked-By"))
# Settings a user's git config could set that would change the output parsed here.
GIT_CONFIG = ["-c", "log.showSignature=false", "-c", "log.follow=false",
              "-c", "core.quotepath=off", "-c", "log.decorate=false"]


class UsageError(Exception):
    pass


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *GIT_CONFIG, *args],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def resolve(repo: Path, rev: str) -> str | None:
    """The full commit SHA ``rev`` names, or None."""
    result = subprocess.run(
        ["git", "-C", str(repo), *GIT_CONFIG, "rev-parse", "--verify", "--quiet",
         f"{rev}^{{commit}}"],
        capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def parse_trailers(message: str) -> dict[str, list[str]]:
    """The trailer block of a commit message: key to its values, in message order.

    The block is the trailing paragraphs after the subject paragraph that consist only of
    ``Key: value`` lines (a line starting with whitespace continues the value before it).
    """
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for line in message.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)
    block: list[list[tuple[str, str]]] = []
    for paragraph in reversed(paragraphs[1:]):
        pairs: list[tuple[str, str]] = []
        for line in paragraph:
            match = TRAILER_RE.match(line)
            if match:
                pairs.append((match.group(1), match.group(2).strip()))
            elif line[0] in " \t" and pairs:
                key, value = pairs[-1]
                pairs[-1] = (key, f"{value} {line.strip()}".strip())
            else:
                pairs = []
                break
        if not pairs:
            break
        block.insert(0, pairs)
    trailers: dict[str, list[str]] = {}
    for pairs in block:
        for key, value in pairs:
            trailers.setdefault(key.lower(), []).append(value)
    return trailers


def named_products(trailers: dict[str, list[str]]) -> list[str]:
    """The products ``Result-Change`` names, in order, without duplicates."""
    names: list[str] = []
    for value in trailers.get("result-change", []):
        for name in value.split(","):
            name = name.strip()
            if name and name not in names:
                names.append(name)
    return names


def joined(trailers: dict[str, list[str]], key: str) -> str:
    return "; ".join(value for value in trailers.get(key, []) if value)


def baseline_blobs(repo: Path, rev: str) -> dict[str, str]:
    """Product to the blob id of its ``result_cf.csv`` at ``rev``."""
    blobs = {}
    for line in git(repo, "ls-tree", "-r", rev, "--", "baseline").splitlines():
        meta, path = line.split("\t", 1)
        match = BASELINE_RE.match(path)
        if match:
            blobs[match.group(1)] = meta.split()[2]
    return blobs


def commits(repo: Path, tag: str, head: str) -> list[dict]:
    """Every commit in ``tag..head``, oldest first (topological): sha, parents, subject, trailers."""
    out = git(repo, "log", "--reverse", "--topo-order", "--format=%H%x1f%P%x1f%s%x1f%B%x1e",
              f"{tag}..{head}")
    found = []
    for record in out.split("\x1e"):
        record = record.lstrip("\n")
        if not record:
            continue
        sha, parents, subject, message = record.split("\x1f", 3)
        found.append({"sha": sha, "parents": parents.split(), "subject": subject,
                      "trailers": parse_trailers(message)})
    return found


def changes(repo: Path, tag: str, head: str, history: list[dict]) -> dict[str, set[str]]:
    """Commit SHA to the products whose baseline it changes (see module docstring)."""
    changed: dict[str, set[str]] = {}
    out = git(repo, "log", "--full-history", "--no-merges", "--no-renames", "--name-only",
              "--format=%x1e%H", f"{tag}..{head}", "--", "baseline")
    for record in out.split("\x1e"):
        lines = [line for line in record.splitlines() if line.strip()]
        if not lines:
            continue
        sha, paths = lines[0], lines[1:]
        products = {m.group(1) for m in map(BASELINE_RE.match, paths) if m}
        if products:
            changed.setdefault(sha, set()).update(products)
    trees: dict[str, dict[str, str]] = {}

    def blobs(rev: str) -> dict[str, str]:
        if rev not in trees:
            trees[rev] = baseline_blobs(repo, rev)
        return trees[rev]

    for commit in history:
        if len(commit["parents"]) < 2:
            continue
        own = blobs(commit["sha"])
        parents = [blobs(parent) for parent in commit["parents"]]
        products = set(own).union(*parents)
        for product in products:
            if all(own.get(product) != parent.get(product) for parent in parents):
                changed.setdefault(commit["sha"], set()).add(product)
    return changed


def collect(repo: Path, tag: str) -> dict:
    """The listing: tag and HEAD SHAs, the deviations and the problems."""
    inside = subprocess.run(["git", "-C", str(repo), "rev-parse", "--git-dir"],
                            capture_output=True, text=True)
    if inside.returncode != 0:
        raise UsageError(f"{repo} is not a git repository")
    tag_sha = resolve(repo, tag)
    if tag_sha is None:
        raise UsageError(f"the tag {tag!r} does not resolve to a commit in {repo}; "
                         f"fetch it with `git fetch --tags`")
    head_sha = resolve(repo, "HEAD")
    if head_sha is None:
        raise UsageError(f"HEAD does not resolve to a commit in {repo}")
    history = commits(repo, tag_sha, head_sha)
    changed = changes(repo, tag_sha, head_sha, history)
    order = {commit["sha"]: i for i, commit in enumerate(history)}
    by_sha = {commit["sha"]: commit for commit in history}

    deviations = []
    for sha in sorted(changed, key=order.__getitem__):
        commit = by_sha[sha]
        trailers = commit["trailers"]
        named = named_products(trailers)
        reason, checked_by = joined(trailers, "reason"), joined(trailers, "checked-by")
        for product in sorted(changed[sha]):
            deviations.append({
                "product": product, "commit": sha, "subject": commit["subject"],
                "reason": reason, "checked_by": checked_by,
                "marked": product in named and bool(reason) and bool(checked_by)})
    deviations.sort(key=lambda d: (d["product"], order[d["commit"]]))

    problems = []
    for deviation in deviations:
        if deviation["product"] not in named_products(by_sha[deviation["commit"]]["trailers"]):
            problems.append(f"UNMARKED: {deviation['product']} {deviation['commit']} "
                            f"{deviation['subject']} -- changes the baseline without "
                            f"Result-Change naming {deviation['product']}")
    for commit in history:
        named = named_products(commit["trailers"])
        if "result-change" not in commit["trailers"]:
            continue
        missing = [label for key, label in REQUIRED if not joined(commit["trailers"], key)]
        if missing:
            problems.append(f"INCOMPLETE: {commit['sha']} {commit['subject']} -- Result-Change "
                            f"without {' and '.join(missing)}")
        for product in named:
            if product not in changed.get(commit["sha"], set()):
                problems.append(f"NO CHANGE: {product} {commit['sha']} {commit['subject']} -- "
                                f"Result-Change names {product}, whose baseline this commit "
                                f"does not change")
    return {"tag": tag_sha, "head": head_sha, "deviations": deviations, "problems": problems}


def report(listing: dict, tag: str) -> int:
    """Print the listing and every problem on stderr; the exit code."""
    marked = [d for d in listing["deviations"] if d["marked"]]
    if not listing["deviations"] and not listing["problems"]:
        print(f"no baseline deviation from {tag} ({listing['tag']})")
    else:
        print(f"baseline deviations from {tag} ({listing['tag']}) to HEAD ({listing['head']}): "
              f"{len(listing['deviations'])}, marked {len(marked)}")
        for d in marked:
            print(f"{d['product']} {d['commit']} {d['subject']} -- Reason: {d['reason']}")
    for problem in listing["problems"]:
        print(problem, file=sys.stderr)
    return 1 if listing["problems"] or len(marked) < len(listing["deviations"]) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="baseline_deviations.py",
        description="List every commit since a tag that changes a baseline, with its trailers.")
    parser.add_argument("--repo", type=Path, default=ROOT,
                        help="the git repository (default: this repository's root)")
    parser.add_argument("--tag", default=DEFAULT_TAG,
                        help=f"the baseline tag (default: {DEFAULT_TAG})")
    parser.add_argument("--json", type=Path, metavar="FILE", help="also write the listing to FILE")
    args = parser.parse_args(argv)
    try:
        listing = collect(args.repo, args.tag)
    except UsageError as exc:
        parser.print_usage(sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json is not None:
        args.json.write_text(json.dumps(listing, indent=1) + "\n", encoding="utf-8")
    return report(listing, args.tag)


if __name__ == "__main__":
    sys.exit(main())
