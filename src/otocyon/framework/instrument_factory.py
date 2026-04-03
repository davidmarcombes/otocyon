from typing import Optional, Dict, Type

from .context import Context
from .instrument import BaseInstrument, BaseSpec, BaseLoader
from .instruments.swap_instrument import SwapInstrument
from .instruments.equity_instrument import EquityInstrument
from .instruments.crypto_instrument import CryptoInstrument
from .logger import NO_LOGGER


class InstrumentFactory:
    """
    Responsible for creating and caching instrument instances from their 
    specifications. It manages the lifecycle and ensures singletons of instruments.
    """
    def __init__(self, ctx: Context):
        """
        Initializes the factory.
        
        Args:
            ctx: The shared context containing configuration.
        """
        self.ctx = ctx
        self._cache: Dict[str, BaseInstrument] = {}
        self._type_map: Dict[str, Type[BaseInstrument]] = {
            "equity": EquityInstrument,
            "crypto": CryptoInstrument,
            "swap": SwapInstrument,
            "base": BaseInstrument,
        }

    def logger(self):
        """ Return the configured logger. """
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    def create(
        self,
        specs: BaseSpec,
        loader: Optional[BaseLoader] = None,
    ) -> BaseInstrument:
        """
        Creates a new instrument or returns a cached one based on the given specification.

        Args:
            specs: The structural specifications of the instrument to create.
            loader: An optional data loader. If unset, it will be auto-resolved via the Market.
            
        Returns:
            The instantiated and hydrated instrument.
        """
        if specs.symbol in self._cache:
            instr = self._cache[specs.symbol]
            instr.add_features(specs.features)
            return instr

        self.logger().debug(f"Factory synthesizing: {specs.symbol}")

        # If loader is not provided, try to discover it through the market
        if loader is None:
            loader = self.ctx.market.get_loader(specs, self.ctx)

        klass = self._type_map.get(specs.asset_class, BaseInstrument)
        instr = klass(specs, loader, self.ctx)

        # Register any pending features requested by the spec
        instr.add_features(specs.features)

        # Call collect() automatically if we have a loader
        if loader is not None:
            instr._collect()

        self._cache[specs.symbol] = instr
        return instr
