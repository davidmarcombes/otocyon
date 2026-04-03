import functools
from typing import Type, List, Optional, Callable, Dict, Any, Union
from .registry import REGISTRY
from .instrument import BaseSpec


def strategy(name: str, universe: Optional[Union[List[Any], Dict[str, Any]]] = None):
    """
    Class-level decorator to register a strategy.

    Args:
        name: The unique string identifier for the strategy.
        universe: A list or dictionary of instrument specifications the strategy requires.
                  If a dict is provided, instruments will be automatically injected 
                  as class properties.
    """

    def wrapper(cls: Type):
        final_universe = {}
        
        # 1. Parse class-level assigned descriptors (e.g. btc = RegisterCrypto(...))
        for attr_name, value in vars(cls).items():
            if isinstance(value, BaseSpec):
                final_universe[attr_name] = value

        # 2. Merge explicitly provided universe (if any)
        if isinstance(universe, dict):
            final_universe.update(universe)
        elif isinstance(universe, list):
            final_universe = universe

        # Store the class and its metadata in both the global Registry and on the class itself
        REGISTRY.add(name, cls, {"universe": final_universe})
        cls._otocyon_name = name
        cls._otocyon_universe = final_universe
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
