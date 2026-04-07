import polars as pl
from typing import Any, Generator
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


# The strategy class decorator tells
# the engine that this class is a strategy
# and gives it a name.
# It will get registered and inspected automatically
# when imported
@strategy("BTC-ETH-TrendFollower")
class TrendFollower:
    # Class members are used to define the universe of the strategy
    # This allow us to also define features for each instrument
    # The features are computed in a single pass using polars rust engine

    # Feature Category 1: column already in the parquet/sql data
    # AAPL ma_20 and vol_20 are written by generate_data.py
    # MSFT 'returns' is added by the DuckDB SQL query in DuckDBLoader
    aapl: EquityInstrument = EquitySpec(  # type: ignore[assignment]
        symbol="AAPL",
        features={
            # Columns pre-calculated on disk
            "ma_20": features.col("ma_20"),
            "vol_20": features.col("vol_20"),
        },
    )

    msft: EquityInstrument = EquitySpec(  # type: ignore[assignment]
        symbol="MSFT",
        features={
            # Column added by DuckDB loader SQL
            "returns": features.col("returns"),
        },
    )

    #  Feature Category 2: predefined routines from features.py
    btc: CryptoInstrument = CryptoSpec(  # type: ignore[assignment]
        symbol="BTC-USDT",
        features={
            # Shorthands predefined in framework
            # Standardisation and reuse
            "ma_5": features.sma("close", 5),
            "rsi_14": features.rsi("close", 14),
            "vol_20": features.volatility("close", 20),
        },
    )

    #  Feature Category 3: custom inline user defined expression
    eth: CryptoInstrument = CryptoSpec(  # type: ignore[assignment]
        symbol="ETH-USDT",
        features={
            # Framework shorthand
            "mom": features.momentum("close", 1),
            # Raw polars expression – one-off, not worth a named routine
            "vol_ratio": pl.col("close").rolling_std(window_size=5)
            / pl.col("close").rolling_std(window_size=20),
        },
    )

    # Constructor
    # Context in injected from the engine
    def __init__(self, ctx: Any) -> None:
        self.ctx = ctx

    # The on_data decorator registers the function with the engine
    # It will be called once per data change
    @on_data()
    def handle_market_data(self) -> Any:

        # Most trivial example: just pass through all features
        # Real strateggies would compute their own signals here
        yield [
            Indicator("AAPL-MA20", self.aapl.ma_20, "AAPL"),
            Indicator("AAPL-Vol20", self.aapl.vol_20, "AAPL"),
            Indicator("MSFT-Ret", self.msft.returns, "MSFT"),
            Indicator("BTC-MA5", self.btc.ma_5, "BTC-USDT"),
            Indicator("BTC-RSI14", self.btc.rsi_14, "BTC-USDT"),
            Indicator("ETH-Mom", self.eth.mom, "ETH-USDT"),
        ]

    # The on_indicator decorator registers the function with the engine
    # It will be called once after indicators are computed
    # Delegating call back to engine allows for middleware hooking
    # For example, one could add a feature to the global indicator pool
    # Or one could hook logging, saving features to disk for relay
    @on_indicator()
    def handle_indicator(self, indicators: dict[str, Indicator]) -> Generator[Signal, None, None]:

        btc_rsi = indicators["BTC-RSI14"]
        eth_mom = indicators["ETH-Mom"]

        # RSI + momentum signal
        if btc_rsi.value < 40 and eth_mom.value > 1.0:
            yield Signal("BTC-USDT", weight=1.0, side="LONG")
        else:
            yield Signal("ETH-USDT", weight=1.0, side="LONG")
