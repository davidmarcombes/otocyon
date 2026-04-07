import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from otocyon.framework import REGISTRY
from otocyon.framework.logger import configure_logging, get_logger

# Configure structlog once for the whole test session
configure_logging()


@pytest.fixture(autouse=True)
def clear_registry():
    """
    This runs before EVERY single test automatically.
    It ensures Otocyon starts with a clean slate.
    """
    REGISTRY.clear()
    yield


@pytest.fixture
def logger():
    """A structlog BoundLogger for use in tests that construct a Context."""
    return get_logger("test")
