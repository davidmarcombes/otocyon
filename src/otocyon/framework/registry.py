from typing import Any, Generic, Type, TypeVar

import structlog

from .context import Context
from .logger import NO_LOGGER

StrategyT = TypeVar("StrategyT")


class Registry(Generic[StrategyT]):
    """
    Global registry for tracking strategies and their metadata across the framework.

    Generic over the strategy class type so callers can express ``Registry[MyStrategy]``
    when they need stronger typing downstream.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, dict[str, Any]] = {}
        self.ctx: Context | None = None

    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get the shared logger."""
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    def initialize(self, ctx: Context) -> None:
        """Sets the global context."""
        self.ctx = ctx
        self.logger().info("Registry initialized.")

    def add(self, name: str, cls: Type[StrategyT], metadata: dict[str, Any]) -> None:
        """
        Registers a new strategy class with its metadata.

        Args:
            name: The strategy name.
            cls: The Strategy class itself.
            metadata: Additional metadata like universe requirements.
        """
        if name in self._strategies:
            self.logger().warning(f"Overwriting existing strategy: {name}")
        self._strategies[name] = {"class": cls, **metadata}

    def get_all(self) -> dict[str, dict[str, Any]]:
        """Retrieve all registered strategies."""
        return self._strategies

    def clear(self) -> None:
        """Reset the registry. Useful for testing."""
        self._strategies = {}
        self.ctx = None


# One global instance for the whole framework
REGISTRY: Registry[Any] = Registry()
