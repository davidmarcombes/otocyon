"""
Otocyon CLI
===========

Entry point for the ``otocyon`` command.  Three sub-commands are available:

    otocyon run            — execute a backtest simulation
    otocyon strategies     — list all registered strategies
    otocyon generate-data  — write sample parquet data to disk
"""

import logging
from typing import Annotated

from cyclopts import App, Parameter

app = App(
    name="otocyon",
    help="Otocyon quantitative backtesting framework.",
)


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


@app.command
def run(
    *,
    strategy: Annotated[
        str | None,
        Parameter(help="Strategy name to run. Runs all registered strategies if omitted."),
    ] = None,
    data_root: Annotated[
        str,
        Parameter(help="Root directory for market data parquet files."),
    ] = "data",
    config: Annotated[
        str,
        Parameter(help="Path to the YAML / TOML / JSON config file."),
    ] = "config.yaml",
    verbose: Annotated[
        bool,
        Parameter(help="Enable DEBUG-level log output."),
    ] = False,
) -> None:
    """Run a backtest simulation."""
    from .framework.logger import configure_logging, get_logger
    from .framework import Context
    from .engine import Engine

    # Import strategies to trigger their @strategy decorator registration.
    # In a real project this would be auto-discovered via importlib.
    from .strategies import btc_eth_trend  # noqa: F401

    configure_logging(level=logging.DEBUG if verbose else logging.INFO)
    logger = get_logger("otocyon.runner")

    with Context(logger=logger, data_root=data_root, config_file=config) as ctx:
        engine = Engine(ctx)
        engine.add_strategies(names=[strategy] if strategy else None)
        engine.prepare()
        engine.run()


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------


@app.command
def strategies() -> None:
    """List all strategies registered in the global registry."""
    # Import to trigger registration
    from .strategies import btc_eth_trend  # noqa: F401
    from .framework import REGISTRY

    all_strategies = REGISTRY.get_all()
    if not all_strategies:
        print("No strategies registered.")
        return

    print(f"{'NAME':<30}  UNIVERSE")
    print("-" * 60)
    for name, meta in all_strategies.items():
        universe = meta.get("universe", {})
        symbols = list(universe.keys()) if isinstance(universe, dict) else list(universe)
        print(f"{name:<30}  {', '.join(symbols)}")


# ---------------------------------------------------------------------------
# generate-data
# ---------------------------------------------------------------------------


@app.command
def generate_data(
    *,
    output_dir: Annotated[
        str,
        Parameter(help="Root output directory (creates {output_dir}/{asset_class}/*.parquet)."),
    ] = "data",
    bars: Annotated[
        int,
        Parameter(help="Number of daily bars to generate per symbol."),
    ] = 100,
) -> None:
    """Generate sample market data parquet files for the default universe."""
    import os
    import numpy as np
    import polars as pl
    from datetime import datetime, timedelta

    universe = [
        ("BTC-USDT", "crypto", 100.0, 42),
        ("ETH-USDT", "crypto", 100.0, 123),
        ("AAPL", "equity", 200.0, 7),
        ("MSFT", "equity", 200.0, 99),
    ]

    for symbol, asset_class, start_price, seed in universe:
        np.random.seed(seed)
        prices = start_price * np.exp(np.cumsum(np.random.normal(0, 0.01, bars)))
        start_dt = datetime(2024, 1, 1)
        end_dt = start_dt + timedelta(days=bars - 1)

        df = pl.DataFrame({
            "timestamp": pl.datetime_range(start=start_dt, end=end_dt, interval="1d", eager=True),
            "close": prices,
            "volume": np.random.uniform(100, 1000, bars),
        })

        if asset_class == "equity":
            df = df.with_columns([
                pl.col("close").rolling_mean(window_size=20).alias("ma_20"),
                pl.col("close").rolling_std(window_size=20).alias("vol_20"),
            ])

        dir_path = os.path.join(output_dir, asset_class)
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, f"{symbol}.parquet")
        df.write_parquet(path)
        print(f"  generated  {path}  ({bars} bars)")
