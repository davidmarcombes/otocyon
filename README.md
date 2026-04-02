# Otocyon

A  declarative strategy backtesting framework.

## 🚀  Example Strategy

```python
@strategy(
    "BTC-ETH-Rebalancer",
    universe={
        "btc": CryptoSpec(symbol="BTC-USDT"),
        "eth": CryptoSpec(symbol="ETH-USDT"),
    },
)
class TrendFollower:
    def __init__(self, ctx):
        self.ctx = ctx

    @on_data()
    def handle_market_data(self):
        yield [
            Indicator("BTC-Price", self.btc.price, self.btc.symbol),
            Indicator("ETH-Price", self.eth.price, self.eth.symbol),
        ]

    @on_indicator()
    def handle_indicator(self, indicators):
        btc = indicators["BTC-Price"]
        eth = indicators["ETH-Price"]

        if btc.value > eth.value * 30:
            yield Signal("BTC-USDT", weight=1.0, side="LONG")
        else:
            yield Signal("ETH-USDT", weight=1.0, side="LONG")
```
## Libs we use

## Polars
Super efficient data manipulation and analysis library.
Implemented in Rust and easy to extend with Rust analytics.

## DuckDb
In-process OLAP database engine, supports loading wide range of files including parquet, csv, json, etc.
Supports **zero copy integration** with Polars and Arrow.
Easy to implement vectorized C++ user defined functions.

## PyArrow
The connective tissue of the modern data stack.
Provides the in-memory format and IPC mechanics that allow DuckDB to hand over data to Polars without copying memory buffers.

## Numpy
The fundamental package for scientific computing with Python.
Used for efficient numerical operations and data generation.
