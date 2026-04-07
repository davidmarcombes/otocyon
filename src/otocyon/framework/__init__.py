from .registry import REGISTRY
from .decorators import strategy, on_data, on_setup, on_indicator
from .context import Context
from .instrument import BaseSpec, BaseInstrument, SpecProtocol, InstrumentProtocol
from .instrument_factory import InstrumentFactory
from .loader import BaseLoader, LoaderProtocol
from .loaders.DuckDbLoader import DuckDBLoader
from .loaders.PolarsLoader import PolarsLoader
from .logger import NO_LOGGER
from .instruments.crypto_instrument import CryptoSpec, CryptoInstrument
from .instruments.equity_instrument import EquitySpec, EquityInstrument
from .instruments.swap_instrument import SwapSpec, SwapInstrument
from .signal import Signal
from .indicator import Indicator
from .schemas import OHLCVSchema, CryptoSchema, EquitySchema
from . import features

__all__ = [
    "REGISTRY",
    "strategy",
    "on_data",
    "on_setup",
    "on_indicator",
    "Context",
    "BaseSpec",
    "BaseInstrument",
    "SpecProtocol",
    "InstrumentProtocol",
    "InstrumentFactory",
    "BaseLoader",
    "LoaderProtocol",
    "DuckDBLoader",
    "PolarsLoader",
    "NO_LOGGER",
    "CryptoSpec",
    "CryptoInstrument",
    "EquitySpec",
    "EquityInstrument",
    "SwapSpec",
    "SwapInstrument",
    "Signal",
    "Indicator",
    "OHLCVSchema",
    "CryptoSchema",
    "EquitySchema",
    "features",
]
