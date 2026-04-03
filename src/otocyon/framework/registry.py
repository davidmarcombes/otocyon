from typing import Optional
from .context import Context
from .logger import NO_LOGGER


class Registry:
    """
    Global registry for tracking strategies and their metadata across the framework.
    """
    def __init__(self):
        self._strategies = {}
        self.ctx: Optional[Context] = None

    def logger(self):
        """ Get the shared logger. """
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    def initialize(self, ctx: Context):
        """ Sets the global context. """
        self.ctx = ctx
        self.logger().info("Registry initialized.")

    def add(self, name, cls, metadata):
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

    def get_all(self):
        """ Retrieve all registered strategies. """
        return self._strategies

    def clear(self):
        """Reset the registry. Useful for testing."""
        self._strategies = {}
        self.ctx = None


# One global instance for the whole framework
REGISTRY = Registry()
