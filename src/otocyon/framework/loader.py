from abc import ABC, abstractmethod
from logging import Logger
from polars import DataFrame

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .instrument import BaseSpec
from .context import Context
from .logger import NO_LOGGER


class BaseLoader(ABC):
    """
    Base class for all loaders.
    """

    def __init__(self, spec: "BaseSpec", ctx: Context):
        """
        Initialize the loader.

        Args:
            spec: The instrument specification.
            ctx: The context.
        """
        self.spec = spec
        self.ctx = ctx

    def logger(self) -> Logger:
        """
        Safely get logger from context
        """
        # We assume ctx has a logger or we use NO_LOGGER
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    @abstractmethod
    def load(self) -> DataFrame:
        """
        Fetch data into Polars DataFrame.

        Todo: add parameters for time window

        Returns:
            DataFrame: The fetched data.
        """
        pass
