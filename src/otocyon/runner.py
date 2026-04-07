from .engine import Engine
from .strategies.btc_eth_trend import TrendFollower  # noqa: F401 — registers strategy on import
from .framework import Context
from .framework.logger import configure_logging, get_logger

configure_logging()
logger = get_logger("otocyon.runner")

with Context(logger=logger) as ctx:
    engine = Engine(ctx)
    engine.add_strategies()
    engine.prepare()
    engine.run()
