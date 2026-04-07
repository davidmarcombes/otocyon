# Otocyon

A Python showcase backtesting framework for systematic trading strategies.

This project illustrates some of the modern python thecnique and libraries for building data processing pipelines and backtesting engines.

The current implementation is limited to a basic event-driven backtesting engine. The data pipeline to build the times series is not covered, nor is the portfolio management and execution logic.

Strategies are declared as Python classes. The `@strategy` decorator registers a class and binds it to a universe of instruments. The `@on_data` and `@on_indicator` decorators mark methods that participate in the simulation loop.

## Example

```python
import polars as pl
from typing import Any, Generator
from otocyon.framework import (
    strategy, on_data, on_indicator,
    CryptoSpec, EquitySpec,
    CryptoInstrument, EquityInstrument,
    Indicator, Signal, features,
)

@strategy("BTC-ETH-TrendFollower")
class TrendFollower:
    # Universe: instruments and their pre-compiled feature expressions
    aapl: EquityInstrument = EquitySpec(  # type: ignore[assignment]
        symbol="AAPL",
        features={
            "ma_20": features.col("ma_20"),   # column pre-calculated on disk
            "vol_20": features.col("vol_20"),
        },
    )
    btc: CryptoInstrument = CryptoSpec(  # type: ignore[assignment]
        symbol="BTC-USDT",
        features={
            "ma_5":   features.sma("close", 5),
            "rsi_14": features.rsi("close", 14),
        },
    )
    eth: CryptoInstrument = CryptoSpec(  # type: ignore[assignment]
        symbol="ETH-USDT",
        features={
            "mom":       features.momentum("close", 1),
            "vol_ratio": pl.col("close").rolling_std(window_size=5)
                         / pl.col("close").rolling_std(window_size=20),
        },
    )

    def __init__(self, ctx: Any) -> None:
        self.ctx = ctx

    @on_data()
    def handle_market_data(self) -> Any:
        yield [
            Indicator("BTC-RSI14", self.btc.rsi_14, "BTC-USDT"),
            Indicator("ETH-Mom",   self.eth.mom,    "ETH-USDT"),
        ]

    @on_indicator()
    def handle_indicator(self, indicators: dict[str, Indicator]) -> Generator[Signal, None, None]:
        if indicators["BTC-RSI14"].value < 40 and indicators["ETH-Mom"].value > 1.0:
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
uv run otocyon generate-data
```

By default this writes to `data/` with 100 bars per symbol. To change either:

```bash
uv run otocyon generate-data --output-dir data --bars 500
```

### List registered strategies

```bash
uv run otocyon strategies
```

### Run a backtest

Run all registered strategies against the data in `data/`:

```bash
uv run otocyon run
```

Run a specific strategy by name:

```bash
uv run otocyon run --strategy BTC-ETH-TrendFollower
```

Enable debug-level log output:

```bash
uv run otocyon run --verbose
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
