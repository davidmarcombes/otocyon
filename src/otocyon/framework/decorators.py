import functools
from typing import Any, Callable, Type

from beartype import beartype

from .registry import REGISTRY
from .instrument import BaseSpec


def strategy(name: str, universe: list[Any] | dict[str, Any] | None = None) -> Callable[[Type[Any]], Type[Any]]:
    """
    Class-level decorator to register a strategy.

    Args:
        name: The unique string identifier for the strategy.
        universe: A list or dictionary of instrument specifications the strategy requires.
                  If a dict is provided, instruments will be automatically injected
                  as class properties.
    """

    def wrapper(cls: Type[Any]) -> Type[Any]:
        dict_universe: dict[str, Any] = {}

        # 1. Parse class-level assigned descriptors (e.g. btc = CryptoSpec(...))
        for attr_name, value in vars(cls).items():
            if isinstance(value, BaseSpec):
                dict_universe[attr_name] = value

        # 2. Merge explicitly provided universe (if any)
        final_universe: list[Any] | dict[str, Any]
        if isinstance(universe, dict):
            dict_universe.update(universe)
            final_universe = dict_universe
        elif isinstance(universe, list):
            final_universe = universe
        else:
            final_universe = dict_universe

        # Store the class and its metadata in both the global Registry and on the class itself
        REGISTRY.add(name, cls, {"universe": final_universe})
        cls._otocyon_name = name
        cls._otocyon_universe = final_universe
        return cls

    return wrapper


def on_setup() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Method-level decorator to tag setup handlers.
    Usage: @on_setup()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._is_setup_handler = True  # type: ignore[attr-defined]

        @functools.wraps(func)  # copies __dict__ (incl. _is_setup_handler) onto wrapper
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return beartype(func)(*args, **kwargs)

        return wrapper

    return decorator


def on_data(frequency: str = "1d") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Method-level decorator to tag data handlers.
    Usage: @on_data(frequency="1h")
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._is_data_handler = True  # type: ignore[attr-defined]
        func._frequency = frequency  # type: ignore[attr-defined]

        checked_func = beartype(func)

        @functools.wraps(func)  # copies __dict__ (incl. _is_data_handler) onto wrapper
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return checked_func(*args, **kwargs)

        return wrapper

    return decorator


def on_indicator() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Method-level decorator to tag indicator handlers.
    Usage: @on_indicator()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._is_indicator_handler = True  # type: ignore[attr-defined]

        checked_func = beartype(func)

        @functools.wraps(func)  # copies __dict__ (incl. _is_indicator_handler) onto wrapper
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return checked_func(*args, **kwargs)

        return wrapper

    return decorator
