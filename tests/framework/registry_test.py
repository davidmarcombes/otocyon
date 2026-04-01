import pytest
from otocyon.framework import REGISTRY, strategy

def test_strategy_registration():
    # 1. Define a dummy strategy
    @strategy("TestAlpha", universe=["AAPL", "MSFT"])
    class MockStrategy:
        pass

    # 2. Assert it exists in the registry
    reg = REGISTRY.get_all()
    assert "TestAlpha" in reg
    assert reg["TestAlpha"]["universe"] == ["AAPL", "MSFT"]
    assert reg["TestAlpha"]["class"] == MockStrategy

def test_registry_overwrite():
    @strategy("OverwriteMe")
    class Version1: version = 1

    @strategy("OverwriteMe")
    class Version2: version = 2

    reg = REGISTRY.get_all()
    assert reg["OverwriteMe"]["class"].version == 2

def test_registry_initialization():
    import logging
    from otocyon.framework.context import Context
    
    ctx = Context(logger=logging.getLogger("test"), data_root="/tmp")
    REGISTRY.initialize(ctx)
    
    assert REGISTRY.ctx == ctx