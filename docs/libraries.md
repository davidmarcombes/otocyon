# Libraries and Design Choices

This page explains the library choices made in this project and the reasoning behind each one. The project is a showcase of modern Python patterns for data-intensive systems — each choice reflects a concrete problem being solved, not a preference.

---

## Data Layer

### Polars

Polars is a DataFrame library written in Rust. It uses the Apache Arrow columnar memory format internally, which means operations that scan or transform columns avoid row-by-row Python overhead entirely.

The key reason Polars is used here rather than Pandas is the **expression API**. A Polars expression (`pl.Expr`) is a lazy computation descriptor — it describes *what* to compute without executing it. This allows the framework to collect all feature definitions from every instrument spec and submit them to Polars in a single `with_columns()` call before the simulation loop starts. Polars executes that batch in one Rust pass over the data. The alternative — computing each feature separately — would make the number of passes proportional to the number of features.

The benchmark in `tests/benchmark/test_features.py` confirms that compilation time grows sub-linearly with the number of features and bars, which is the expected behavior from a vectorized engine.

Polars supports custom expression plugins written in Rust via `pyo3`. A plugin compiles to a native shared library and registers new `pl.Expr` nodes that participate in the same query optimizer and execution engine as built-in expressions. This means a custom feature — say, a bespoke rolling statistic — can be written in Rust and called identically to `pl.col("close").rolling_mean(5)`, with the same zero-copy, multi-threaded execution guarantees.

### DuckDB

DuckDB is an in-process analytical database. It runs inside the Python process with no server, no network, and no serialization overhead. It can read a wide variety of data formats including parquet, csv, json, sql, excel, etc.

The reason DuckDB is used alongside Polars rather than instead of it is SQL window functions. Computing lag-1 returns (`(close - lag(close)) / lag(close)`) in SQL is one line. The equivalent in Polars is more verbose. DuckDB handles the SQL, then hands the result to Polars via the Arrow IPC format — zero bytes are copied between the two.

DuckDB is used specifically for the `DuckDBLoader`, which loads equity data and adds a `returns` column via a window function query. Crypto data uses `PolarsLoader` directly since no derived column is needed at load time.

DuckDB an polars coexist very well together thanks to PyArrow zero copy dataframe transfer protocol.

DuckDB supports vectorized user-defined functions (UDFs) implemented in C++ via its extension API. These execute inside the DuckDB engine at native speed, bypassing Python entirely for the hot path. This makes it possible to express custom aggregations or transforms in SQL while paying no Python overhead per row.

### PyArrow

PyArrow provides the Arrow in-memory format and the IPC protocol that lets DuckDB transfer query results to Polars without copying memory. The `.pl()` call on a DuckDB result set invokes this path. It is a dependency of both DuckDB and Polars and requires no explicit usage in application code — it is the shared memory contract between them.

---

## Application Layer

### msgspec

`Signal` and `Indicator` are the two objects created on every bar of the simulation. In a backtest over several years of daily data across a multi-instrument universe, millions of these objects are constructed and discarded.

`msgspec.Struct` is faster to construct than a Python dataclass because it uses a fixed-layout C struct internally rather than a `__dict__`. It also supports JSON and MessagePack serialization out of the box, at speeds 10–100x faster than the standard library, which matters if signals or indicators are ever logged to disk or sent over a wire.

`Signal` uses a mutable `Struct` to allow cancellation (`signal.cancel(reason)`). `Indicator` uses a frozen `Struct` (`frozen=True`) because indicators are read-only once produced.

### structlog

structlog replaces the stdlib `logging` module. The difference is that structlog log calls carry **key-value pairs** rather than formatted strings:

```python
log.bind(symbol="BTC-USDT", step=42).debug("instrument.compile_features", count=5)
```

This produces a structured log record that a log aggregation system (Datadog, Loki, etc.) can query by field. With stdlib logging you would format a string and lose the structure. In development the same call renders as a readable console line; in production you swap `ConsoleRenderer` for `JSONRenderer` in the processor chain without changing any call sites.

The `NO_LOGGER` sentinel in `logger.py` is a structlog-wrapped NullHandler logger used as the default in `Context`. This means code that calls `self.ctx.logger.bind(...).debug(...)` works correctly whether or not logging has been configured, with no `if logger is not None` guards scattered through the codebase.

### beartype

beartype applies runtime type enforcement to function signatures using the annotations already present in the code. The cost is O(1) per call for most types — it uses PEP 526 annotations directly without generating wrapper code at import time.

It is applied inside the `@on_data`, `@on_indicator`, and `@on_setup` decorator wrappers:

```python
checked_func = beartype(func)
```

This means any strategy method that is decorated with these will raise a `BeartypeException` immediately if a caller passes the wrong type, rather than producing a confusing error later in the simulation loop. It catches mistakes at the framework boundary without requiring manual validation code.

### pandera\[polars\]

pandera provides DataFrame schema validation using a class-based API (`DataFrameModel`). The schema hierarchy used here is:

```
OHLCVSchema        — requires close > 0
  └── CryptoSchema — adds optional volume >= 0
        └── EquitySchema — adds required nullable returns
```

Each loader validates its output against the appropriate schema before returning the DataFrame. If the parquet file has the wrong column name, a column with the wrong dtype, or a close price that is zero or negative, `SchemaError` is raised immediately at load time. Without this, a bad value would silently propagate through feature compilation and produce wrong indicator values with no error.

The `coerce = False` setting in the schema config means pandera will never silently cast types. If the column is the wrong type, the validation fails loudly.

---

## Type System

### typing.Protocol + runtime_checkable

The framework uses `Protocol` from the standard library to define structural interfaces for `SpecProtocol`, `InstrumentProtocol`, and `LoaderProtocol`. Structural typing means any class that has the right attributes and methods satisfies the protocol without inheriting from it.

This is the standard way to express duck typing in modern Python with static type checker support. It means the framework does not force user-defined loaders or instruments to inherit from a specific base class — they just need to have a `load()` method, or a `price` property, etc.

`@runtime_checkable` adds support for `isinstance()` checks against the protocol, which is used in tests.

### Generic Registry

`Registry` is typed as `Registry(Generic[StrategyT])`. This allows the registry to be instantiated for a specific strategy type if needed (`Registry[TrendFollower]`), while the module-level singleton uses `Registry[Any]` to accept any strategy class. The generic parameter is a documentation and tooling aid — it communicates that the registry contains typed objects, and a stricter downstream usage can opt into the type parameter.

---

## Testing

### hypothesis

hypothesis is a property-based testing library. Rather than writing test cases with specific inputs, you describe the space of valid inputs and hypothesis generates examples, including edge cases it finds by shrinking failing inputs to their minimal form.

It is used in `tests/framework/test_portfolio_properties.py` to verify invariants such as:

- Equity is always cash plus the value of positions (conservation)
- A trade that exceeds available cash does not execute
- Cancelling a signal is idempotent

During development, hypothesis found that `Indicator` is not hashable when `metadata` contains a `dict`, because `dict` is unhashable. This is a real design constraint that a hand-written unit test would not have found unless someone thought to test that specific case.

### pytest-benchmark

pytest-benchmark measures the wall-clock time of code under test and reports statistics across multiple rounds. It is used to verify that Polars feature compilation scales correctly: compiling 10 features on 10k bars should not take 10x longer than compiling 1 feature on 1k bars.

The benchmark results confirm sub-linear scaling, which validates the batch compilation design. If someone changed the feature compilation to call `with_columns()` once per feature instead of once for all features, the benchmark would regress and make the change visible.

---

## CLI

### cyclopts

cyclopts is a CLI framework built on Python type annotations. Commands are plain functions with annotated parameters; cyclopts generates the argument parser from the annotations. It is used here over argparse (too low-level) and Click (decorator-heavy) because the resulting code is closer to a plain Python function:

```python
@app.command
def run(*, strategy: Annotated[str | None, Parameter(help="Strategy name")] = None) -> None:
    ...
```

The `Annotated[type, Parameter(...)]` pattern keeps the type annotation and the CLI metadata in one place. cyclopts validates input types automatically and generates `--help` output from the annotations and docstrings.
