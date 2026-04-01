from abc import ABC, abstractmethod
import polars as pl
from typing import Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class BaseSpec:
    """Base interface for all instrument specifications."""

    symbol: str
    asset_class: str


class BaseInstrument(ABC):
    def __init__(self, symbol: str, data: pl.LazyFrame, ctx: Any):
        self.symbol = symbol
        self._plan = data  # The "Lazy" blueprint
        self._df: Optional[pl.DataFrame] = None  # The "Real" data (initially empty)
        self.ctx = ctx
        self._cursor = 0

    def _collect(self):
        """Materializes the lazy plan into RAM when the backtest starts."""
        self.ctx.logger.debug(f"Collecting data for {self.symbol}...")
        self._df = self._plan.collect()

    @property
    def price(self) -> float:
        return self._df["close"][self._cursor]

    @abstractmethod
    def get_type(self) -> str:
        """Every subclass MUST define its type."""
        pass
