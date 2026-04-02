import polars as pl
from ..framework import (
    strategy,
    on_data,
    on_indicator,
    CryptoSpec,
    EquitySpec,
    Indicator,
    Signal,
)
from typing import Dict


@strategy(
    "BTC-ETH-TrendFollower",
    universe={
        "btc": CryptoSpec(symbol="BTC-USDT"),
        "eth": CryptoSpec(symbol="ETH-USDT"),
        "aapl": EquitySpec(symbol="AAPL"),
        "msft": EquitySpec(symbol="MSFT"),
    },
)
class TrendFollower:
    def __init__(self, ctx):
        self.ctx = ctx
        self.lookback = 20

    @on_data()
    def handle_market_data(self):
        # 1. BTC: Uses the Polars load-time plan for 'ma_5'
        # 2. AAPL: Uses pre-calculated 'ma_20' from Parquet file
        # 3. MSFT: Uses DuckDB SQL-calculated 'returns'
        # 4. ETH: Demonstrates lazy on-the-fly calculation
        
        yield [
            Indicator("BTC-MA5", self.btc.get_stat("ma_5"), "BTC-USDT"),
            Indicator("AAPL-MA20", self.aapl.get_stat("ma_20"), "AAPL"),
            Indicator("MSFT-Ret", self.msft.get_stat("returns"), "MSFT"),
            Indicator("ETH-Mom", self.eth.get_stat("mom", pl.col("close") / pl.col("close").shift(1)), "ETH-USDT")
        ]

    @on_indicator()
    def handle_indicator(self, indicators: Dict[str, Indicator]):

        btc_ma = indicators["BTC-MA5"]
        eth_mom = indicators["ETH-Mom"]

        # Noddy logic using mixed sources
        if btc_ma.value > 100 and eth_mom.value > 1.01:
            yield Signal("BTC-USDT", weight=1.0, side="LONG")
        else:
            yield Signal("ETH-USDT", weight=1.0, side="LONG")
