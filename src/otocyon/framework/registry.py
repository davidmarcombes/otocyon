from typing import Optional
from .context import Context
from .logger import NO_LOGGER


class Registry:
    def __init__(self):
        self._strategies = {}
        self.ctx: Optional[Context] = None

    def logger(self):
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER

    def initialize(self, ctx: Context):
        self.ctx = ctx
        self.logger().info("Registry initialized.")

    def add(self, name, cls, metadata):
        if name in self._strategies:
            self.logger().warning(f"Overwriting existing strategy: {name}")
        self._strategies[name] = {"class": cls, **metadata}

    def get_all(self):
        return self._strategies

    def clear(self):
        """Reset the registry. Useful for testing."""
        self._strategies = {}
        self.ctx = None


# One global instance for the whole framework
REGISTRY = Registry()
