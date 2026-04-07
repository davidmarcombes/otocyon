# Framework

Core data structures and the decorator API.

## Context

`Context` is a dataclass that holds all shared state for a simulation run. It is created once and passed into the engine and every strategy instance.

Fields of note:

- `logger` — a `structlog.BoundLogger`; use `.bind(key=value)` to attach structured fields to a log call.
- `duckdb_connection` — shared DuckDB connection used by `DuckDBLoader`.
- `data_root` — path to the directory containing parquet files.
- `instruments` — `dict[str, BaseInstrument]` populated by the engine during `add_strategy`.
- `portfolio` — the `Portfolio` instance for position tracking.

::: otocyon.framework.context.Context
    options:
      show_root_heading: true

---

## Signal

`Signal` is a `msgspec.Struct` (mutable). It expresses a target position intent from a strategy.

Fields: `symbol`, `weight` (0–1), `side` (`"LONG"` / `"SHORT"` / `"FLAT"`), `strategy_id`, `signal_id` (auto UUID), `metadata`.

A signal can be cancelled before execution via `.cancel(reason)`. The engine checks `.is_active` and skips cancelled signals.

::: otocyon.framework.signal.Signal
    options:
      show_root_heading: true

---

## Indicator

`Indicator` is a `msgspec.Struct` (frozen). It carries a named scalar value from an `@on_data` handler to the shared pool consumed by `@on_indicator` handlers.

Fields: `name`, `value`, `symbol`, `timestamp` (auto epoch), `metadata`.

Because it is frozen it is safe to store in sets or use as a dict key, with the caveat that `metadata` is a plain `dict` and therefore not hashable.

::: otocyon.framework.indicator.Indicator
    options:
      show_root_heading: true

---

## Portfolio

Tracks cash and positions. The engine calls `set_position` during the execution pass to move from the current quantity to the target quantity implied by each signal.

::: otocyon.framework.portfolio.Portfolio
    options:
      show_root_heading: true

---

## Decorators

Three decorators mark strategy methods for participation in the simulation loop.

`@on_data(frequency="1d")` — marks a method as a data handler. The method should yield a list of `Indicator` objects.

`@on_indicator()` — marks a method as a signal handler. The method receives the indicator pool as `dict[str, Indicator]` and should yield `Signal` objects.

`@on_setup()` — marks a method for one-time initialization. Called once during `Engine.prepare()`, before the simulation loop.

All three decorators wrap the decorated function with `beartype` for runtime type enforcement.

::: otocyon.framework.decorators
    options:
      members:
        - strategy
        - on_data
        - on_indicator
        - on_setup
      show_root_heading: true

---

## Registry

`Registry` is a generic container (`Registry[StrategyT]`) that maps strategy names to their class and metadata. The `@strategy` decorator writes into it. The engine reads from it in `add_strategies`.

The module-level `REGISTRY` instance is typed `Registry[Any]` and used as a singleton.

::: otocyon.framework.registry.Registry
    options:
      show_root_heading: true

---

## Schemas

Pandera `DataFrameModel` schemas validate loader output. See [index.md](index.md#data-validation) for the hierarchy.

::: otocyon.framework.schemas.OHLCVSchema
    options:
      show_root_heading: true

::: otocyon.framework.schemas.CryptoSchema
    options:
      show_root_heading: true

::: otocyon.framework.schemas.EquitySchema
    options:
      show_root_heading: true

---

## Loaders

`PolarsLoader` reads a parquet file via `polars.scan_parquet` and validates against `CryptoSchema`.

`DuckDBLoader` runs a SQL query with a window function to compute lag returns, then validates against `EquitySchema`. It uses the shared `duckdb_connection` from `Context`.

Both loaders inherit from `BaseLoader`, which holds the spec and context and exposes a `.logger()` method returning a structlog logger bound to the instrument symbol.

::: otocyon.framework.loader.BaseLoader
    options:
      show_root_heading: true

---

## InstrumentFactory

Creates instrument instances from specs. Resolves the loader from the spec type and wires it to the context.

::: otocyon.framework.instrument_factory.InstrumentFactory
    options:
      show_root_heading: true
