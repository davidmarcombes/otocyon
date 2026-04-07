# Otocyon

A Python backtesting framework for systematic trading strategies.

## Design

The simulation loop has four sequential passes per bar:

1. **Data pass** (`@on_data`): each strategy method reads instrument prices and features, then yields a list of `Indicator` objects.
2. **Middleware pass**: the engine aggregates the indicator pool and computes any cross-instrument meta-indicators (e.g. universe average price).
3. **Signal pass** (`@on_indicator`): each strategy method reads the indicator pool and yields `Signal` objects expressing a target position.
4. **Execution pass**: the engine resolves signals through the `Portfolio`, converting weights to quantities and updating positions.

Instruments are injected into the strategy instance as named attributes before the loop starts. Each instrument wraps a Polars DataFrame and exposes a cursor that the engine advances on each step, so `self.btc.price` always returns the scalar value at the current bar.

Feature expressions (SMA, RSI, volatility, etc.) are declared in the instrument spec and compiled in a single Polars pass before the loop. This keeps per-bar access to a dictionary lookup against pre-computed columns.

## Data validation

Loader output passes through a pandera schema before entering the simulation:

- `OHLCVSchema` — requires a positive `close` column; all other columns are permitted.
- `CryptoSchema` — adds optional non-negative `volume`.
- `EquitySchema` — adds required nullable `returns` (the first row is null because there is no prior bar).

Validation runs once at load time and raises `SchemaError` immediately if the contract is violated.

## Sections

- [Libraries and Design](libraries.md) — library choices and the reasoning behind each one: Polars, DuckDB, msgspec, structlog, beartype, pandera, hypothesis, cyclopts.
- [Framework](framework.md) — core data structures: `Context`, `Signal`, `Indicator`, `Portfolio`, decorators, registry.
- [Instruments](instruments.md) — `CryptoInstrument`, `EquityInstrument`, `SwapInstrument`, and the `InstrumentFactory`.
- [Feature Library](features.md) — column references, predefined technical-analysis expressions, and inline custom expressions.
- [Engine](engine.md) — simulation loop, `add_strategy`, `prepare`, `run`.
- [Python Techniques](python_techniques.md) — language patterns used in the codebase: protocols, generics, decorators, dataclasses, `cached_property`, generators, `__getattr__`, `TYPE_CHECKING`.
