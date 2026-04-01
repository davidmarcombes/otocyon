from abc import ABC, abstractmethod
from typing import Any
import polars

from .logger import NO_LOGGER
from .instrument import BaseSpec
from .context import Context

class BaseLoader(ABC):
    def __init__(self, spec: BaseSpec, ctx: Context):
        self.spec = spec
        self.ctx = ctx

    def logger(self):
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    @abstractmethod
    def load(self) -> polars.DataFrame:
        """Fetch data for a specific window and return a Polars DataFrame."""
        pass
