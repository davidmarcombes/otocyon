from abc import ABC, abstractmethod
import polars as pl
from typing import Any, Optional
from dataclasses import dataclass, field
from .loader import BaseLoader
from .context import Context

@dataclass(frozen=True)
class BaseSpec:
    """
    Base interface for all instrument specifications.
    """

    symbol: str
    asset_class: str
    features: dict = field(default_factory=dict, kw_only=True, compare=False, hash=False)


class BaseInstrument(ABC):
    """
    Base interface for all instruments.
    """

    def __init__(self, spec: BaseSpec, loader: Optional[BaseLoader], ctx: Context):
        """
        Initialize the instrument.

        Args:
            spec: The instrument specification.
            loader: The loader.
            ctx: The context.
        """
        self.spec = spec
        self.symbol = spec.symbol
        self._loader = loader
        self._df: Optional[pl.DataFrame] = None  # The "Real" data (initially empty)
        self.ctx = ctx
        self._cursor = 0
        self._pending_features: dict[str, pl.Expr] = {}

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically fallback to DataFrame columns if an attribute isn't found on the class.
        This provides clean access like self.btc.ma_5.
        """
        if self._df is None:
            raise ValueError(f"Data not collected yet to read '{name}'.")
        if name not in self._df.columns:
            raise AttributeError(f"Instrument '{self.symbol}' has no attribute or feature '{name}'")
        return self._df[name][self._cursor]

    def add_features(self, features: dict):
        """Registers a set of polars expressions to be evaluated during compile time."""
        for name, expr in features.items():
            if name not in self._pending_features:
                self._pending_features[name] = expr

    def compile_features(self):
        """Executes all registered Polars expressions in a single rust-native pass."""
        if not self._pending_features or self._df is None:
            return

        self.ctx.logger.info(f"Compiling {len(self._pending_features)} features for {self.symbol}...")
        
        # Batch all pending features into a single with_columns evaluation block
        exprs = [expr.alias(name) for name, expr in self._pending_features.items()]
        self._df = self._df.with_columns(exprs)
        
        # Clear them once calculated
        self._pending_features.clear()

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
                raise ValueError(
                    f"Stat '{name}' not found and no expression provided for calculation."
                )

            self.ctx.logger.info(f"[LAZY STAT] Calculating {name} for {self.symbol}...")
            self._df = self._df.with_columns(expr.alias(name))

        return self._df[name][self._cursor]

    @abstractmethod
    def get_type(self) -> str:
        """Every subclass MUST define its type."""
        pass
