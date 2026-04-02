import logging
from .engine import Engine
from .strategies.btc_eth_trend import TrendFollower
from .framework import Context

# Simple logging setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("otocyon")

with Context(logger=logger) as ctx:
    engine = Engine(ctx)
    engine.add_strategies()
    engine.prepare()
    engine.run()
