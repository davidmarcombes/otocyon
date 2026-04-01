from typing import Optional, Union, Dict, Type
import polars as pl

from .context import Context
from .instrument import BaseInstrument, BaseSpec
from .instruments.swap_instrument import SwapSpecs, SwapInstrument
from .instruments.equity_insturment import EquityInstrument
from .instruments.crypto_instrument import CryptoInstrument
from .logger import NO_LOGGER


class InstrumentFactory:
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self._type_map: Dict[str, Type[BaseInstrument]] = {
            "equity": EquityInstrument,
            "crypto": CryptoInstrument,
            "swap": SwapInstrument,
            "base": BaseInstrument,
        }

    def logger(self):
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    def create(
        self,
        specs: BaseSpec,
        plan: Optional[pl.LazyFrame] = None,
    ) -> BaseInstrument:
        """
        Create an instrument using the factory's internal context.
        """
        self.logger().debug(f"Factory synthesizing: {specs.symbol}")

        # 1. Resolve the Class
        klass = self._type_map.get(specs.asset_class, BaseInstrument)

        # 2. Build plan
        if plan is None:
            # Todo : build the plan from name or spec
            pass

        return klass(specs, plan, self.ctx)
