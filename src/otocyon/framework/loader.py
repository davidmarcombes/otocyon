from typing import Any, Protocol, runtime_checkable

from polars import DataFrame
from structlog.stdlib import BoundLogger

from .context import Context
from .logger import NO_LOGGER


@runtime_checkable
class LoaderProtocol(Protocol):
    """
    Structural interface for any data loader.

    Any class implementing ``load() -> DataFrame`` satisfies this protocol —
    no inheritance required.
    """

    def load(self) -> DataFrame: ...


class BaseLoader:
    """
    Concrete base providing shared ``__init__`` and ``logger`` utilities.

    Subclass this for the shared implementation, but type-annotate parameters
    with ``LoaderProtocol`` to remain open to structural duck-typed loaders.
    """

    def __init__(self, spec: Any, ctx: Context) -> None:
        """
        Initialize the loader.

        Args:
            spec: The instrument specification.
            ctx: The context.
        """
        self.spec = spec
        self.ctx = ctx

    def logger(self) -> BoundLogger:
        """Safely get logger from context."""
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    def load(self) -> DataFrame:
        """
        Fetch data into a Polars DataFrame.

        Todo: add parameters for time window

        Returns:
            DataFrame: The fetched data.
        """
        raise NotImplementedError
