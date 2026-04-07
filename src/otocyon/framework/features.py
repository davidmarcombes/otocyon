"""
Framework Feature Library
=========================

Provides three categories of features for use in instrument specs:

1. **Column References** – features already present in the loaded data (e.g. ``ma_20`` written
   by the data generation script). Use :func:`col` to reference them by name.

2. **Predefined Routines** – common technical-analysis expressions built here and reusable
   across any strategy (SMA, EMA, RSI, volatility, momentum, VWAP, …).

3. **Custom Inline Expressions** – raw ``pl.Expr`` objects written directly in the spec's
   ``features={}`` dict for one-off calculations that don't deserve a shared name.

All helpers return a ``pl.Expr`` that can be passed directly into the ``features`` dict of a
``BaseSpec`` subclass::

    btc: CryptoInstrument = CryptoSpec(
        symbol="BTC-USDT",
        features={
            "ma_5":  features.sma("close", 5),
            "rsi_14": features.rsi("close", 14),
            "vol_20": features.volatility("close", 20),
        },
    )
"""

import polars as pl


# ---------------------------------------------------------------------------
# Category 1 – Column Reference
# Reference a column that already exists in the loaded file / query result.
# ---------------------------------------------------------------------------


def col(name: str) -> pl.Expr:
    """
    Reference a feature column that is already present in the loaded data.

    Use this when the column was pre-calculated by a data-generation script
    (e.g. ``ma_20``, ``vol_20`` produced by ``generate_data.py``) or added
    by the SQL query in the DuckDB loader.

    Args:
        name: The exact column name expected in the DataFrame.

    Returns:
        A pass-through Polars expression for the named column.

    Example::

        aapl: EquityInstrument = EquitySpec(
            symbol="AAPL",
            features={
                "ma_20":  features.col("ma_20"),   # pre-computed in parquet
                "returns": features.col("returns"), # added by DuckDB SQL
            },
        )
    """
    return pl.col(name)


# ---------------------------------------------------------------------------
# Category 2 – Predefined Routines
# Common technical-analysis building blocks.
# ---------------------------------------------------------------------------


def sma(source: str = "close", window: int = 20) -> pl.Expr:
    """
    Simple Moving Average.

    Args:
        source: Source column name.
        window: Rolling window size in bars.

    Returns:
        Polars rolling-mean expression.
    """
    return pl.col(source).rolling_mean(window_size=window)


def ema(source: str = "close", window: int = 20) -> pl.Expr:
    """
    Exponential Moving Average via Polars ``ewm_mean``.

    Args:
        source: Source column name.
        window: Span (number of periods). Equivalent to ``alpha = 2 / (window + 1)``.

    Returns:
        Polars EWM expression.
    """
    return pl.col(source).ewm_mean(span=window)


def volatility(source: str = "close", window: int = 20) -> pl.Expr:
    """
    Historical (rolling) Volatility – annualised standard deviation of log returns.

    Args:
        source: Source column name.
        window: Rolling window size in bars.

    Returns:
        Polars expression for annualised vol.
    """
    log_ret = (pl.col(source) / pl.col(source).shift(1)).log(base=2.718281828)
    annualised: pl.Expr = log_ret.rolling_std(window_size=window) * (252**0.5)
    return annualised


def returns(source: str = "close", periods: int = 1) -> pl.Expr:
    """
    Simple percentage return over *periods* bars.

    Args:
        source: Source column name.
        periods: Lookback period.

    Returns:
        Polars expression for percentage return (not annualised).
    """
    return pl.col(source) / pl.col(source).shift(periods) - 1


def log_returns(source: str = "close", periods: int = 1) -> pl.Expr:
    """
    Log return over *periods* bars.

    Args:
        source: Source column name.
        periods: Lookback period.

    Returns:
        Polars expression for log return.
    """
    return (pl.col(source) / pl.col(source).shift(periods)).log(base=2.718281828)


def momentum(source: str = "close", window: int = 20) -> pl.Expr:
    """
    Price momentum – ratio of current price to price *window* bars ago.
    A value > 1 means upward momentum; < 1 means downward.

    Args:
        source: Source column name.
        window: Lookback period in bars.

    Returns:
        Polars expression for momentum ratio.
    """
    return pl.col(source) / pl.col(source).shift(window)


def rsi(source: str = "close", window: int = 14) -> pl.Expr:
    """
    Relative Strength Index (Wilder's method approximated with EWM).

    Args:
        source: Source column name.
        window: RSI period (default 14).

    Returns:
        Polars expression for RSI in the range [0, 100].
    """
    delta = pl.col(source).diff()
    gain = pl.when(delta > 0).then(delta).otherwise(0).ewm_mean(span=window)
    loss = pl.when(delta < 0).then(-delta).otherwise(0).ewm_mean(span=window)
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def bollinger_upper(source: str = "close", window: int = 20, k: float = 2.0) -> pl.Expr:
    """
    Bollinger Band upper band: SMA + k * rolling std.

    Args:
        source: Source column name.
        window: Rolling window.
        k: Number of standard deviations.

    Returns:
        Polars expression for the upper Bollinger band.
    """
    return sma(source, window) + k * pl.col(source).rolling_std(window_size=window)


def bollinger_lower(source: str = "close", window: int = 20, k: float = 2.0) -> pl.Expr:
    """
    Bollinger Band lower band: SMA - k * rolling std.

    Args:
        source: Source column name.
        window: Rolling window.
        k: Number of standard deviations.

    Returns:
        Polars expression for the lower Bollinger band.
    """
    return sma(source, window) - k * pl.col(source).rolling_std(window_size=window)


def vwap(
    price_col: str = "close", volume_col: str = "volume", window: int = 20
) -> pl.Expr:
    """
    Rolling Volume-Weighted Average Price.

    Args:
        price_col: Column containing price data.
        volume_col: Column containing volume data.
        window: Rolling window size.

    Returns:
        Polars expression for rolling VWAP.
    """
    pv = pl.col(price_col) * pl.col(volume_col)
    return pv.rolling_mean(window_size=window) / pl.col(volume_col).rolling_mean(
        window_size=window
    )


def z_score(source: str = "close", window: int = 20) -> pl.Expr:
    """
    Rolling Z-Score: how many standard deviations the current price is from its
    rolling mean (useful for mean-reversion signals).

    Args:
        source: Source column name.
        window: Rolling window.

    Returns:
        Polars expression for rolling Z-score.
    """
    mean = pl.col(source).rolling_mean(window_size=window)
    std = pl.col(source).rolling_std(window_size=window)
    return (pl.col(source) - mean) / std
