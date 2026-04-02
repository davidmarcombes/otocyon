import pytest
import logging
from pathlib import Path
from otocyon.framework.market import Market, MockLoader
from otocyon.framework.context import Context
from otocyon.framework.instrument import BaseSpec
from otocyon.framework.loaders.PolarsLoader import PolarsLoader
from otocyon.framework.loaders.DuckDbLoader import DuckDBLoader

def test_market_dispatch_mock_loader(tmp_path: Path):
    """
    Shows how the Market assigns a MockLoader when the parquet file
    is missing.
    """
    ctx = Context(logger=logging.getLogger("test"), data_root=str(tmp_path))
    spec = BaseSpec(symbol="UNKNOWN", asset_class="crypto")
    market = Market()
    
    loader = market.get_loader(spec, ctx)
    assert isinstance(loader, MockLoader)

def test_market_dispatch_polars(tmp_path: Path):
    """
    Shows how the Market assigns a PolarsLoader for 'crypto' assets
    when the data file is present.
    """
    # 1. Setup mock data file
    data_root = tmp_path / "data"
    asset_class = "crypto"
    symbol = "BTC"
    
    symbol_dir = data_root / asset_class
    symbol_dir.mkdir(parents=True)
    file_path = symbol_dir / f"{symbol}.parquet"
    file_path.touch() # Create empty file to bypass MockLoader fallback
    
    # 2. Get loader from Market
    ctx = Context(logger=logging.getLogger("test"), data_root=str(data_root))
    spec = BaseSpec(symbol=symbol, asset_class=asset_class)
    market = Market()
    
    loader = market.get_loader(spec, ctx)
    
    # 3. Verify
    assert isinstance(loader, PolarsLoader)

def test_market_dispatch_duckdb(tmp_path: Path):
    """
    Shows how the Market assigns a DuckDBLoader for 'equity' assets
    when the data file is present.
    """
    # 1. Setup mock data file
    data_root = tmp_path / "data"
    asset_class = "equity"
    symbol = "AAPL"
    
    symbol_dir = data_root / asset_class
    symbol_dir.mkdir(parents=True)
    file_path = symbol_dir / f"{symbol}.parquet"
    file_path.touch()
    
    # 2. Get loader from Market
    ctx = Context(logger=logging.getLogger("test"), data_root=str(data_root))
    spec = BaseSpec(symbol=symbol, asset_class=asset_class)
    market = Market()
    
    loader = market.get_loader(spec, ctx)
    
    # 3. Verify
    assert isinstance(loader, DuckDBLoader)
