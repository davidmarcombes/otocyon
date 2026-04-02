import functools
from typing import Type, List, Optional, Callable, Dict, Any, Union
from .registry import REGISTRY


def strategy(name: str, universe: Optional[Union[List[Any], Dict[str, Any]]] = None):
    """
    Class-level decorator to register a strategy.
    Usage: @strategy("TrendFollower", universe={"btc": CryptoSpec(...)})
    """

    def wrapper(cls: Type):
        # Store the class and its metadata in both the global Registry and on the class itself
        REGISTRY.add(name, cls, {"universe": universe or []})
        cls._otocyon_name = name
        cls._otocyon_universe = universe or []
        return cls

    return wrapper


def on_setup():
    """
    Method-level decorator to tag setup handlers.
    Usage: @on_setup()
    """

    def decorator(func: Callable):
        func._is_setup_handler = True  # type: ignore

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def on_data(frequency: str = "1d"):
    """
    Method-level decorator to tag data handlers.
    Usage: @on_data(frequency="1h")
    """

    def decorator(func: Callable):
        # We attach attributes to the function object itself
        func._is_data_handler = True  # type: ignore
        func._frequency = frequency  # type: ignore

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def on_indicator():
    """
    Method-level decorator to tag indicator handlers.
    Usage: @on_indicator()
    """

    def decorator(func: Callable):
        # We attach attributes to the function object itself
        func._is_indicator_handler = True  # type: ignore

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
