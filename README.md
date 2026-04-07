# Otocyon

A Python showcase backtesting framework for systematic trading strategies.

This project illustrates some of the modern python thecnique and libraries for building data processing pipelines and backtesting engines.

The current implementation is limited to a basic event-driven backtesting engine. The data pipeline to build the times series is not covered, nor is the portfolio management and execution logic.

Strategies are declared as Python classes. The `@strategy` decorator registers a class and binds it to a universe of instruments. The `@on_data` and `@on_indicator` decorators mark methods that participate in the simulation loop.

## Example

```python
from otocyon.framework import (
    strategy, on_data, on_indicator,
    CryptoSpec, Indicator, Signal,
)

@strategy(
    "BTC-ETH-Trend",
    universe={
        "btc": CryptoSpec(symbol="BTC-USDT"),
        "eth": CryptoSpec(symbol="ETH-USDT"),
    },
)
class BtcEthTrend:
    def __init__(self, ctx):
        self.ctx = ctx

    @on_data()
    def on_data(self):
        yield [
            Indicator("BTC-Price", self.btc.price, "BTC-USDT"),
            Indicator("ETH-Price", self.eth.price, "ETH-USDT"),
        ]

    @on_indicator()
    def on_indicator(self, indicators):
        btc = indicators["BTC-Price"]
        eth = indicators["ETH-Price"]

        if btc.value > eth.value * 30:
            yield Signal("BTC-USDT", weight=1.0, side="LONG")
        else:
            yield Signal("ETH-USDT", weight=1.0, side="LONG")
```

Full documentation is in the [`docs/`](docs/) folder:

- [Architecture and design](docs/index.md)
- [Libraries and design choices](docs/libraries.md)
- [Framework reference](docs/framework.md)
- [Instruments](docs/instruments.md)
- [Feature library](docs/features.md)
- [Engine](docs/engine.md)
- [Python techniques](docs/python_techniques.md)

## Getting started

Install dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

### Generate sample data

The framework expects parquet files under `data/{asset_class}/{symbol}.parquet`. The `generate-data` command creates synthetic data for the default universe (BTC-USDT, ETH-USDT, AAPL, MSFT):

```bash
uv run python -m otocyon.cli generate-data
```

By default this writes to `data/` with 100 bars per symbol. To change either:

```bash
uv run python -m otocyon.cli generate-data --output-dir data --bars 500
```

### List registered strategies

```bash
uv run python -m otocyon.cli strategies
```

### Run a backtest

Run all registered strategies against the data in `data/`:

```bash
uv run python -m otocyon.cli run
```

Run a specific strategy by name:

```bash
uv run python -m otocyon.cli run --strategy BTC-ETH-TrendFollower
```

Enable debug-level log output:

```bash
uv run python -m otocyon.cli run --verbose
```

### Serve the documentation

```bash
uv run zensical serve --dev-addr 0.0.0.0:9000
```

## Key Tools Libraries

| Library | Role |
| --- | --- |
| **uv** | Dependency management and package installation. |
| **polars** | DataFrame operations. Feature expressions are compiled in a single Rust pass before the simulation loop. |
| **duckdb** | SQL-based data loading. Used to compute derived columns (e.g. lag returns via window functions) directly in the query. |
| **pyarrow** | Zero-copy memory interchange between DuckDB and Polars. |
| **msgspec** | `Signal` and `Indicator` are `msgspec.Struct` subclasses — faster construction and serialisation than dataclasses. |
| **structlog** | Structured logging. All log calls use `.bind()` for key-value context. |
| **pandera[polars]** | Schema validation at loader boundaries. Catches wrong column names, bad dtypes, and constraint violations before data enters the simulation. |
| **beartype** | Runtime type enforcement applied inside `@on_data`, `@on_indicator`, and `@on_setup` decorator wrappers. |
| **cyclopts** | CLI with three commands: `run`, `strategies`, `generate-data`. |
| **hypothesis** | Property-based tests for `Portfolio` invariants and `Signal`/`Indicator` contracts. |
| **pytest-benchmark** | Feature compilation benchmarks to verify Polars batch compilation scales sub-linearly. |
