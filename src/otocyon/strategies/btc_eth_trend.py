import polars as pl
from typing import Dict
from ..framework import (
    strategy,
    on_data,
    on_indicator,
    Indicator,
    Signal,
    CryptoSpec,
    EquitySpec,
    CryptoInstrument,
    EquityInstrument,
    features,
)


@strategy("BTC-ETH-TrendFollower")
class TrendFollower:
    # ── Category 1: column already in the parquet/sql data ────────────────────
    # AAPL ma_20 and vol_20 are written by generate_data.py
    # MSFT 'returns' is added by the DuckDB SQL query in DuckDBLoader
    aapl: EquityInstrument = EquitySpec(
        symbol="AAPL",
        features={
            "ma_20":   features.col("ma_20"),    # pre-calculated on disk
            "vol_20":  features.col("vol_20"),   # pre-calculated on disk
        },
    )

    msft: EquityInstrument = EquitySpec(
        symbol="MSFT",
        features={
            "returns": features.col("returns"),  # added by DuckDB loader SQL
        },
    )

    # ── Category 2: predefined routines from features.py ──────────────────────
    btc: CryptoInstrument = CryptoSpec(
        symbol="BTC-USDT",
        features={
            "ma_5":   features.sma("close", 5),
            "rsi_14": features.rsi("close", 14),
            "vol_20": features.volatility("close", 20),
        },
    )

    # ── Category 3: custom inline expression ──────────────────────────────────
    eth: CryptoInstrument = CryptoSpec(
        symbol="ETH-USDT",
        features={
            # framework shorthand
            "mom": features.momentum("close", 1),
            # raw polars expression – one-off, not worth a named routine
            "vol_ratio": pl.col("close").rolling_std(window_size=5) / pl.col("close").rolling_std(window_size=20),
        },
    )

    def __init__(self, ctx):
        self.ctx = ctx
        self.lookback = 20

    @on_data()
    def handle_market_data(self):
        # Access is clean and type-safe for instrument-level attributes
        # Dynamic feature access falls through to __getattr__ -> DataFrame column

        yield [
            # Category 1: passthrough columns already in data
            Indicator("AAPL-MA20",  self.aapl.ma_20,    "AAPL"),
            Indicator("AAPL-Vol20", self.aapl.vol_20,   "AAPL"),
            Indicator("MSFT-Ret",   self.msft.returns,  "MSFT"),
            # Category 2: predefined framework routines
            Indicator("BTC-MA5",    self.btc.ma_5,      "BTC-USDT"),
            Indicator("BTC-RSI14",  self.btc.rsi_14,    "BTC-USDT"),
            # Category 3: inline custom expression
            Indicator("ETH-Mom",    self.eth.mom,        "ETH-USDT"),
        ]

    @on_indicator()
    def handle_indicator(self, indicators: Dict[str, Indicator]):

        btc_rsi = indicators["BTC-RSI14"]
        eth_mom = indicators["ETH-Mom"]

        # RSI + momentum signal
        if btc_rsi.value < 40 and eth_mom.value > 1.0:
            yield Signal("BTC-USDT", weight=1.0, side="LONG")
        else:
            yield Signal("ETH-USDT", weight=1.0, side="LONG")
