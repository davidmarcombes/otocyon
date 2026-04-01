import sys
from pathlib import Path

# Add 'src' to sys.path so that tests can import 'otocyon' easily
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from otocyon.framework import REGISTRY


@pytest.fixture(autouse=True)
def clear_registry():
    """
    This runs before EVERY single test automatically.
    It ensures Otocyon starts with a clean ear.
    """
    REGISTRY.clear()
    yield
