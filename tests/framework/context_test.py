import logging
from otocyon.framework.context import Context

def test_context_creation():
    logger = logging.getLogger("test")
    ctx = Context(logger=logger, data_root="/tmp/data")
    
    assert ctx.logger == logger
    assert ctx.data_root == "/tmp/data"
    assert ctx.metadata == {}

def test_context_metadata():
    logger = logging.getLogger("test")
    ctx = Context(
        logger=logger,
        data_root="/tmp/data",
        metadata={"foo": "bar"}
    )
    assert ctx.metadata["foo"] == "bar"

def test_context_immutability():
    import pytest
    logger = logging.getLogger("test")
    ctx = Context(logger=logger, data_root="/tmp/data")
    
    with pytest.raises(AttributeError):
        # Ignore linter warning about setting an attribute on a frozen dataclass
        # The test is specifically checking that this raises an error, so we want to do it anyway
        ctx.config_file = "config.yaml" # type: ignore


