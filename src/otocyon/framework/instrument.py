from abc import ABC, abstractmethod
import polars as pl
from typing import Any, Optional
from dataclasses import dataclass
from .loader import BaseLoader


@dataclass(frozen=True)
class BaseSpec:
    """Base interface for all instrument specifications."""

    symbol: str
    asset_class: str


class BaseInstrument(ABC):
    def __init__(self, spec: BaseSpec, loader: Optional[BaseLoader], ctx: Any):
        self.spec = spec
        self.symbol = spec.symbol
        self._loader = loader
        self._df: Optional[pl.DataFrame] = None  # The "Real" data (initially empty)
        self.ctx = ctx
        self._cursor = 0

    def _collect(self):
        """Materializes the raw data through the loader."""
        if self._loader is not None:
            self.ctx.logger.debug(f"Collecting data for {self.symbol}...")
            self._df = self._loader.load()
        else:
            self.ctx.logger.warning(f"No loader for {self.symbol}. Data will be empty.")

    @property
    def price(self) -> float:
        if self._df is None:
            raise ValueError("Data not collected yet. Call _collect() first.")
        return self._df["close"][self._cursor]

    def __len__(self) -> int:
        if self._df is None:
            return 0
        return len(self._df)

    def get_stat(self, name: str, expr: Optional[pl.Expr] = None) -> Any:
        """
        Retrieves a stat. If not present and expr is provided, calculates it lazily 
        and caches it in the internal dataframe.
        """
        if self._df is None:
            raise ValueError("Data not collected yet. Call _collect() first.")

        if name not in self._df.columns:
            if expr is None:
                raise ValueError(f"Stat '{name}' not found and no expression provided for calculation.")
            
            self.ctx.logger.info(f"[LAZY STAT] Calculating {name} for {self.symbol}...")
            self._df = self._df.with_columns(expr.alias(name))

        return self._df[name][self._cursor]

    @abstractmethod
    def get_type(self) -> str:
        """Every subclass MUST define its type."""
        pass
