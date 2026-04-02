from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
import polars as pl

if TYPE_CHECKING:
    from .instrument import BaseSpec


class BaseLoader(ABC):
    def __init__(self, spec: "BaseSpec", ctx: Any):
        self.spec = spec
        self.ctx = ctx

    def logger(self):
        # We assume ctx has a logger or we use NO_LOGGER
        return getattr(self.ctx, "logger", None)

    @abstractmethod
    def load(self) -> pl.DataFrame:
        """Fetch data for a specific window and return a Polars DataFrame."""
        pass
