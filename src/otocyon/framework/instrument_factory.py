from typing import Optional, Dict, Type

from .context import Context
from .instrument import BaseInstrument, BaseSpec, BaseLoader
from .instruments.swap_instrument import SwapInstrument
from .instruments.equity_instrument import EquityInstrument
from .instruments.crypto_instrument import CryptoInstrument
from .logger import NO_LOGGER


class InstrumentFactory:
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self._cache: Dict[str, BaseInstrument] = {}
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
        loader: Optional[BaseLoader] = None,
    ) -> BaseInstrument:
        if specs.symbol in self._cache:
            return self._cache[specs.symbol]

        self.logger().debug(f"Factory synthesizing: {specs.symbol}")

        # If loader is not provided, try to discover it through the market
        if loader is None:
            loader = self.ctx.market.get_loader(specs, self.ctx)

        klass = self._type_map.get(specs.asset_class, BaseInstrument)
        instr = klass(specs, loader, self.ctx)

        # Call collect() automatically if we have a loader
        if loader is not None:
            instr._collect()

        self._cache[specs.symbol] = instr
        return instr
