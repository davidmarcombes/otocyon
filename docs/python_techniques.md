# Python Techniques

This page describes the Python language features and patterns used in this project. Each section explains what the feature is, where it is used, and why it matters in this context.

---

## Type annotations

Python type annotations (PEP 526) attach type information to variables, parameters, and return values. They have no runtime effect by default — they are metadata that tools such as mypy, pyright, and beartype can read.

This project uses the modern syntax available from Python 3.10+:

```python
# Union types with | instead of Union[X, Y]
def get_loader(self, spec: SpecProtocol, ctx: Context) -> BaseLoader | None: ...

# Built-in generics instead of typing.Dict / typing.List
self._strategies: dict[str, dict[str, Any]] = {}

# Optional via X | None instead of Optional[X]
loader: LoaderProtocol | None = None
```

Annotations are enforced at runtime on strategy handler methods via beartype (see [Libraries and Design](libraries.md#beartype)), and checked statically by mypy during development.

---

## typing.Protocol — structural subtyping

`Protocol` defines an interface by the methods and attributes an object must have, rather than by the class it inherits from. Any class that has the right shape satisfies the protocol without explicit inheritance.

```python
@runtime_checkable
class LoaderProtocol(Protocol):
    def load(self) -> DataFrame: ...
```

Any class with a `load() -> DataFrame` method satisfies `LoaderProtocol`, whether it inherits from `BaseLoader` or not. This is called structural subtyping, or duck typing with static checker support.

`@runtime_checkable` adds `isinstance()` support so the check can also be done at runtime:

```python
assert isinstance(my_loader, LoaderProtocol)  # checks for load() method
```

This is used in tests and in the factory to verify loader contracts without requiring inheritance.

---

## Generic classes

`Registry` is parameterised over a strategy type using `TypeVar` and `Generic`:

```python
StrategyT = TypeVar("StrategyT")

class Registry(Generic[StrategyT]):
    def add(self, name: str, cls: Type[StrategyT], ...) -> None: ...
```

The module-level singleton uses `Registry[Any]` to accept any strategy. A downstream consumer that works with a specific strategy type can instantiate `Registry[MyStrategy]` and get typed access to the contained objects. The generic parameter is checked by mypy but erased at runtime.

---

## Decorators

Decorators are functions that wrap other functions or classes to extend their behaviour. This project uses them at both the class level and the method level.

### Class decorator — `@strategy`

`@strategy` registers a class in the global `REGISTRY` and attaches metadata to it:

```python
@strategy("BTC-ETH-Trend", universe={...})
class TrendFollower:
    ...
```

The decorator reads class-level spec assignments (`btc = CryptoSpec(...)`), merges them with the `universe` argument, stores the result on the class as `_otocyon_universe`, and calls `REGISTRY.add()`. The class itself is returned unchanged.

### Method decorators — `@on_data`, `@on_indicator`, `@on_setup`

These mark methods for discovery by the engine. The decorator sets a flag attribute on the function object, then wraps it with beartype for runtime type enforcement:

```python
def on_data(frequency: str = "1d"):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._is_data_handler = True
        func._frequency = frequency
        checked_func = beartype(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return checked_func(*args, **kwargs)

        return wrapper
    return decorator
```

`functools.wraps(func)` copies the original function's `__name__`, `__doc__`, and `__dict__` onto the wrapper. The `__dict__` copy is what preserves `_is_data_handler = True` on the wrapper, which is how the engine finds decorated methods by inspecting `dir(strategy_instance)`.

---

## Dataclasses

`@dataclass` generates `__init__`, `__repr__`, and `__eq__` from class-level field annotations. `frozen=True` also generates `__hash__` and makes instances immutable (all field writes raise `FrozenInstanceError`).

```python
@dataclass(frozen=True)
class BaseSpec:
    symbol: str
    asset_class: str
    features: dict[str, Any] = field(default_factory=dict, kw_only=True)
```

`field(default_factory=dict)` is required for mutable defaults — Python does not allow `features: dict = {}` on a dataclass because all instances would share the same dict object. `kw_only=True` means `features` must be passed as a keyword argument, preventing positional ambiguity.

`Context` is also a frozen dataclass, making it safe to share across strategies without accidental mutation.

---

## cached_property

`@cached_property` computes a value on first access and stores it as an instance attribute, replacing itself. Subsequent accesses return the stored value directly with no re-computation.

```python
@cached_property
def duckdb_connection(self) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(self.duckdb_path or ":memory:")
    conn.execute(f"SET home_directory='{self.data_root}'")
    return conn
```

`Context` uses this for `portfolio`, `factory`, `market`, `duckdb_connection`, and `config`. These are expensive to initialise and not always needed. `cached_property` defers the cost to first use without requiring explicit initialisation code in `__init__`.

Note: `cached_property` writes to the instance `__dict__`, which conflicts with `frozen=True` on a plain dataclass. This works in Python because `cached_property` bypasses the dataclass frozen check by writing directly to `__dict__` via the descriptor protocol.

---

## Context managers

A context manager is any object that implements `__enter__` and `__exit__`. It is used with the `with` statement to guarantee cleanup code runs even if an exception is raised.

```python
class Context:
    def __enter__(self) -> "Context":
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb) -> None:
        if 'duckdb_connection' in self.__dict__:
            self.duckdb_connection.close()
```

Usage in `runner.py`:

```python
with Context(logger=logger, data_root="data") as ctx:
    engine = Engine(ctx)
    engine.run()
# duckdb_connection is closed here, even if engine.run() raises
```

The `'duckdb_connection' in self.__dict__` check is necessary because `duckdb_connection` is a `cached_property` — it may never have been accessed, in which case there is nothing to close.

---

## Generator functions

A function that contains `yield` is a generator function. Calling it returns a generator object; the function body runs only when the generator is iterated.

Strategy handlers use `yield` to produce `Indicator` and `Signal` objects:

```python
@on_data()
def handle_market_data(self):
    yield [
        Indicator("BTC-Price", self.btc.price, "BTC-USDT"),
        Indicator("ETH-Price", self.eth.price, "ETH-USDT"),
    ]
```

The engine collects results by iterating over the return value of each handler. Handlers that yield nothing (e.g. early return with no signal) are handled by the `if result:` guard in the engine loop. The generator pattern means a handler does not need to build and return a list explicitly — it can yield items as it computes them.

---

## `__getattr__` — dynamic attribute dispatch

`__getattr__` is called by Python only when normal attribute lookup fails. `BaseInstrument` uses it to expose DataFrame columns as attributes:

```python
def __getattr__(self, name: str) -> Any:
    if self._df is None:
        raise ValueError(f"Data not collected yet to read '{name}'.")
    if name not in self._df.columns:
        raise AttributeError(f"Instrument '{self.symbol}' has no attribute or feature '{name}'")
    return self._df[name][self._cursor]
```

This is what makes `self.btc.ma_5` work in a strategy without declaring `ma_5` as a class attribute. The engine advances `_cursor` before each bar, so `self._df[name][self._cursor]` always returns the scalar value at the current bar.

`__getattr__` is only invoked as a fallback — if `ma_5` were a real class attribute it would be found first. This keeps the fast path (defined attributes) unaffected.

---

## TYPE_CHECKING guard

`TYPE_CHECKING` is a constant that is `False` at runtime but `True` when a static type checker is running. Imports inside `if TYPE_CHECKING:` are only visible to the type checker, not to the running program.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .portfolio import Portfolio
    from .instrument_factory import InstrumentFactory
    from .market import Market
```

This is used in `context.py` to annotate the return types of `cached_property` methods without creating circular imports. At runtime, the imports never execute. The type checker sees them and validates the return type annotations. The string literal form `-> "Portfolio"` is required for forward references that the type checker resolves against the `TYPE_CHECKING` imports.

---

## Annotated — metadata on type hints

`Annotated[T, metadata]` attaches arbitrary metadata to a type annotation without changing the type itself. It is used by the CLI to pass cyclopts `Parameter` configuration alongside the type:

```python
from typing import Annotated
from cyclopts import Parameter

def run(
    *,
    strategy: Annotated[str | None, Parameter(help="Strategy name to run")] = None,
    verbose: Annotated[bool, Parameter(negative="")] = False,
) -> None:
    ...
```

cyclopts reads the `Parameter` objects at import time to generate the argument parser. Any library that ignores `Annotated` sees only `str | None` and `bool` — the metadata is transparent to tools that do not understand it.

---

## Google-style docstrings

Docstrings in this project follow the Google style, which mkdocstrings parses to generate the API reference pages:

```python
def create(self, specs: SpecProtocol, loader: LoaderProtocol | None = None) -> BaseInstrument:
    """
    Creates a new instrument or returns a cached one based on the given specification.

    Args:
        specs: The structural specifications of the instrument to create.
        loader: An optional data loader. If unset, it will be auto-resolved via the Market.

    Returns:
        The instantiated and hydrated instrument.
    """
```

The `docstring_style = "google"` setting in `zensical.toml` instructs mkdocstrings to parse `Args:`, `Returns:`, and `Raises:` sections and render them as structured documentation.
