from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable

import polars as pl

from .loader import LoaderProtocol
from .context import Context


# ---------------------------------------------------------------------------
# Structural Protocols — type-annotate with these; no inheritance required
# ---------------------------------------------------------------------------


@runtime_checkable
class SpecProtocol(Protocol):
    """
    Structural interface for any instrument specification.

    Any object with ``symbol``, ``asset_class``, and ``features`` attributes
    satisfies this protocol.
    """

    @property
    def symbol(self) -> str: ...
    @property
    def asset_class(self) -> str: ...
    @property
    def features(self) -> dict[str, Any]: ...


@runtime_checkable
class InstrumentProtocol(Protocol):
    """
    Structural interface for any instrument.

    Type-annotate function parameters with this to remain open to custom
    instrument implementations that don't inherit from ``BaseInstrument``.
    """

    symbol: str
    _cursor: int

    @property
    def price(self) -> float: ...

    def __len__(self) -> int: ...

    def get_type(self) -> str: ...

    def add_features(self, features: dict[str, Any]) -> None: ...

    def compile_features(self) -> None: ...


# ---------------------------------------------------------------------------
# Concrete base classes — subclass for shared implementation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaseSpec:
    """
    Base implementation for all instrument specifications.
    """

    symbol: str
    asset_class: str
    features: dict[str, Any] = field(default_factory=dict, kw_only=True, compare=False, hash=False)


class BaseInstrument:
    """
    Base implementation for all instruments.
    """

    def __init__(self, spec: BaseSpec, loader: Optional[LoaderProtocol], ctx: Context) -> None:
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

    def add_features(self, features: dict[str, Any]) -> None:
        """Registers a set of polars expressions to be evaluated during compile time."""
        for name, expr in features.items():
            if name not in self._pending_features:
                self._pending_features[name] = expr

    def compile_features(self) -> None:
        """Executes all registered Polars expressions in a single rust-native pass."""
        if not self._pending_features or self._df is None:
            return

        log = self.ctx.logger.bind(symbol=self.symbol)
        log.info("instrument.compile_features", count=len(self._pending_features))

        # Batch all pending features into a single with_columns evaluation block
        exprs = [expr.alias(name) for name, expr in self._pending_features.items()]
        self._df = self._df.with_columns(exprs)

        # Clear them once calculated
        self._pending_features.clear()

    def _collect(self) -> None:
        """Materializes the raw data through the loader."""
        log = self.ctx.logger.bind(symbol=self.symbol)
        if self._loader is not None:
            log.debug("instrument.collect")
            self._df = self._loader.load()
        else:
            log.warning("instrument.collect.no_loader")

    @property
    def price(self) -> float:
        if self._df is None:
            raise ValueError("Data not collected yet. Call _collect() first.")
        return float(self._df["close"][self._cursor])

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

    def get_type(self) -> str:
        """Every subclass MUST define its type."""
        raise NotImplementedError
