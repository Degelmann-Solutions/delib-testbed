"""Fixtures the test files share."""
from __future__ import annotations

import modelx as mx
import pytest

from helpers import MODELS, PRODUCTS_DIR

FIXTURE = "product_models"
_models = {}


def _close_models() -> None:
    for model in _models.values():
        model.close()
    _models.clear()


@pytest.fixture(scope="session")
def product_models():
    """Every product's modelx model, read once for the files that share it.

    Shared by ``tests/test_core.py`` and the files ``tests/test_core_*.py`` split from it, so
    the ten models are read once, not once per file. A test that changes a model works on a
    scratch copy (``helpers.product_copy``), never on these. The models are closed when the
    next test's file does not use the fixture (``pytest_runtest_teardown``), so no other test
    file runs beside ten open models, as none did when one module held them.
    """
    def read(product):
        if product not in _models:
            _models[product] = mx.read_model(PRODUCTS_DIR / product / MODELS[product])
        return _models[product]

    yield read
    _close_models()


def pytest_collection_modifyitems(session, config, items):
    """Note the test files that use ``product_models``."""
    config.stash[_USERS] = {item.path for item in items if FIXTURE in item.fixturenames}


def pytest_runtest_teardown(item, nextitem):
    """Close the shared models before a test file that does not use them."""
    if _models and (nextitem is None or nextitem.path not in item.config.stash[_USERS]):
        _close_models()


_USERS = pytest.StashKey[set]()
