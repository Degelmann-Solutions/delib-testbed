# Upstream provenance: `BU_DE_S` (lifelib `delib`)

This folder is the berufsunfaehigkeit product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. Nothing is edited, added or removed; line endings are upstream's (LF).

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/berufsunfaehigkeit/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file is byte-identical to upstream at the pinned commit. `tests/test_provenance.py` checks these SHA-256 values and that the folder holds no other file than these and this one.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `BU_DE_S/Data/__init__.py` | `61347cbba2a91ffe8e3ed5006a89a48916648832897fb39eb04284d9c89bc867` |
| `BU_DE_S/Projection/__init__.py` | `7f7995aee8396d865610a5f9c8d2d837a4ccfce9be43588fd0f7c744df6ac58b` |
| `BU_DE_S/__init__.py` | `31de3675cc422cf47541b8019b1341c6ae2eab4064f17ed01eeef0b4fd5f77d0` |
| `BU_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `claim_duration_table.csv` | `de41d11a4d202f83236f00760ef5475f17a52d678e5af44e82fa6dfa390a9a33` |
| `freq_loading_table.csv` | `03cd7eb5efbe9fcf7c6af1c463f1e406c9b3a146f5d55eee38bb39d3424c5884` |
| `inception_table.csv` | `4d51914dd3cdb70795da61dc98608306721408d2a6be5bf546daf6f374c246fe` |
| `lapse_table.csv` | `abbf17332dafc3f3864953945f8b0bf9d6c30abdd002cba166d0288456ddee39` |
| `model.md` | `2bf60e9c2bd7afe288c5084a79ce43d082fa19518b39630bed84886a7680e505` |
| `model_point_table.csv` | `3793f9ec73c007713e9d47c8099169126fafc5fe420e4e1bb001b90f9c7416c4` |
| `mortality_table.csv` | `ec4d334670e68f4e587ef8857cb0913a9ba30fcecbb4127054f5ccad90a65694` |
| `occupation_table.csv` | `a905517d626ae46e1d00f2278a94a3134e78771be239e5357e5e899ff0fc4079` |
| `product-spec.md` | `3dc97d44e47491e26f19eded33fa9d397fe45001cf373f44903bbd32a8ab2d31` |
| `run.py` | `020503cb6fd4bcd21383dd075505542ee7c08750f62d2f5ab507d4fb9dfce946` |
| `sources.md` | `53f9da0b94c2f924fbd68a851dd57ab873e7d983c18b36d9f41f76aec63ba0fa` |
| `technical-notes.md` | `070495160795d46606e91bf5c4fe4258209a94fdeb373cbdd8b179663758a544` |
