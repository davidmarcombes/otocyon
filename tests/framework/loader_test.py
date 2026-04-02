import pytest
import polars as pl
from pathlib import Path
from otocyon.framework.loaders.PolarsLoader import PolarsLoader
from otocyon.framework.loaders.DuckDbLoader import DuckDBLoader
from otocyon.framework.instrument import BaseSpec
from otocyon.framework.context import Context
import logging

def test_polars_loader_basic_usage(tmp_path: Path):
    """
    Shows how PolarsLoader fetches data from a Parquet file
    organized by asset class and symbol.
    """
    # 1. Setup sample data
    data_root = tmp_path / "data"
    asset_class = "crypto"
    symbol = "BTC"
    
    symbol_dir = data_root / asset_class
    symbol_dir.mkdir(parents=True)
    
    file_path = symbol_dir / f"{symbol}.parquet"
    
    # Create simple dataframe
    df = pl.DataFrame({
        "close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    })
    df.write_parquet(file_path)
    
    # 2. Setup loader dependencies
    spec = BaseSpec(symbol=symbol, asset_class=asset_class)
    ctx = Context(logger=logging.getLogger("test"), data_root=str(data_root))
    
    # 3. Use loader
    loader = PolarsLoader(spec, ctx)
    loaded_df = loader.load()
    
    # 4. Verify results
    assert "close" in loaded_df.columns
    assert "ma_5" in loaded_df.columns # PolarsLoader adds a MA_5 column by default
    assert len(loaded_df) == 6
    assert loaded_df["ma_5"][4] == 12.0 # (10+11+12+13+14)/5 = 12.0


def test_duckdb_loader_sql_calculation(tmp_path: Path):
    """
    Shows how DuckDBLoader uses DuckDB's SQL engine to calculate returns.
    """
    # 1. Setup sample data
    data_root = tmp_path / "data"
    asset_class = "equities"
    symbol = "NVDA"
    
    symbol_dir = data_root / asset_class
    symbol_dir.mkdir(parents=True)
    
    file_path = symbol_dir / f"{symbol}.parquet"
    
    # Create simple dataframe with timestamp
    df = pl.DataFrame({
        "timestamp": [1, 2, 3],
        "close": [100.0, 110.0, 121.0]
    })
    df.write_parquet(file_path)
    
    # 2. Setup loader dependencies
    spec = BaseSpec(symbol=symbol, asset_class=asset_class)
    ctx = Context(logger=logging.getLogger("test"), data_root=str(data_root))
    
    # 3. Use loader
    loader = DuckDBLoader(spec, ctx)
    loaded_df = loader.load()
    
    # 4. Verify results
    assert "close" in loaded_df.columns
    assert "returns" in loaded_df.columns # DuckDBLoader calculates returns via SQL
    assert len(loaded_df) == 3
    # 110/100 - 1 = 0.1
    assert loaded_df["returns"][1] == pytest.approx(0.1)
    # 121/110 - 1 = 0.1
    assert loaded_df["returns"][2] == pytest.approx(0.1)
