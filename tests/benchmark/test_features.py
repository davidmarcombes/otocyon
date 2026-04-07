"""
Benchmarks for the feature compilation pipeline.

Run with:
    uv run pytest tests/benchmark/ --benchmark-only -v

The goal is to verify that feature compilation stays in the sub-millisecond
range even on large datasets — the Rust-native Polars pass makes this possible.
"""

import polars as pl
import numpy as np
import pytest

from otocyon.framework.instrument import BaseInstrument, BaseSpec
from otocyon.framework.context import Context
from otocyon.framework import features
from otocyon.framework.logger import configure_logging, get_logger


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def configure():
    configure_logging()


@pytest.fixture
def ctx():
    return Context(logger=get_logger("benchmark"))


def _make_ohlcv(n: int) -> pl.DataFrame:
    """Generate a synthetic OHLCV DataFrame with n rows."""
    rng = np.random.default_rng(42)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pl.DataFrame({
        "close": close,
        "volume": rng.uniform(100, 10_000, n),
    })


def _make_instrument(ctx: Context, df: pl.DataFrame) -> BaseInstrument:
    spec = BaseSpec(symbol="BTC-TEST", asset_class="crypto")

    class _Instr(BaseInstrument):
        def get_type(self) -> str:
            return "crypto"

    instr = _Instr(spec, loader=None, ctx=ctx)
    instr._df = df
    return instr


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


def test_compile_5_features_1k_bars(benchmark, ctx):
    """
    Baseline: compile 5 common features on 1 000 bars.
    All expressions are fused into a single Polars with_columns call.
    """
    df = _make_ohlcv(1_000)

    def run():
        instr = _make_instrument(ctx, df.clone())
        instr.add_features({
            "sma_20":   features.sma("close", 20),
            "ema_20":   features.ema("close", 20),
            "vol_20":   features.volatility("close", 20),
            "rsi_14":   features.rsi("close", 14),
            "mom_5":    features.momentum("close", 5),
        })
        instr.compile_features()

    benchmark(run)


def test_compile_5_features_10k_bars(benchmark, ctx):
    """
    Scale test: same feature set on 10 000 bars.
    Demonstrates that the Polars Rust engine scales sub-linearly.
    """
    df = _make_ohlcv(10_000)

    def run():
        instr = _make_instrument(ctx, df.clone())
        instr.add_features({
            "sma_20":   features.sma("close", 20),
            "ema_20":   features.ema("close", 20),
            "vol_20":   features.volatility("close", 20),
            "rsi_14":   features.rsi("close", 14),
            "mom_5":    features.momentum("close", 5),
        })
        instr.compile_features()

    benchmark(run)


def test_compile_10_features_10k_bars(benchmark, ctx):
    """
    Feature-density test: 10 features fused into a single pass on 10 000 bars.
    Checks that adding more expressions doesn't degrade per-expression cost.
    """
    df = _make_ohlcv(10_000)

    def run():
        instr = _make_instrument(ctx, df.clone())
        instr.add_features({
            "sma_5":    features.sma("close", 5),
            "sma_20":   features.sma("close", 20),
            "ema_20":   features.ema("close", 20),
            "vol_20":   features.volatility("close", 20),
            "vol_5":    features.volatility("close", 5),
            "rsi_14":   features.rsi("close", 14),
            "mom_5":    features.momentum("close", 5),
            "mom_20":   features.momentum("close", 20),
            "bb_upper": features.bollinger_upper("close", 20),
            "zscore":   features.z_score("close", 20),
        })
        instr.compile_features()

    benchmark(run)


def test_signal_creation_throughput(benchmark):
    """
    Throughput test: create 10 000 Signal structs in a tight loop.
    Demonstrates msgspec.Struct construction overhead vs plain dataclasses.
    """
    from otocyon.framework.signal import Signal

    def run():
        for _ in range(10_000):
            Signal(symbol="BTC-USDT", weight=0.5, side="LONG")

    benchmark(run)


def test_indicator_creation_throughput(benchmark):
    """
    Throughput test: create 10 000 frozen Indicator structs.
    Frozen msgspec.Struct has zero copy overhead — values are stored inline.
    """
    from otocyon.framework.indicator import Indicator

    def run():
        for i in range(10_000):
            Indicator(name=f"RSI-{i}", value=float(i % 100), symbol="BTC-USDT")

    benchmark(run)
