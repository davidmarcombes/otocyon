import polars as pl
from typing import Dict
from .loader import BaseLoader
from .instrument import BaseSpec
from .context import Context

class MockLoader(BaseLoader):
    """Generates dummy data for the POC."""
    def load(self) -> pl.DataFrame:
        self.logger().info(f"Generating dummy data for {self.spec.symbol}")
        import numpy as np
        from datetime import datetime, timedelta
        dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(100)]
        prices = 100 + np.random.randn(100).cumsum()
        return pl.DataFrame({
            "date": dates,
            "close": prices
        })

class Market:
    """A simple central authority for data loaders."""
    def __init__(self):
        self._loaders: Dict[str, BaseLoader] = {}

    def get_loader(self, spec: BaseSpec, ctx: Context) -> BaseLoader:
        """Determines the best loader for the resource."""
        import os
        from .loaders.PolarsLoader import PolarsLoader
        from .loaders.DuckDbLoader import DuckDBLoader
        
        # Determine path based on asset class
        path = f"{ctx.data_root}/{spec.asset_class}/{spec.symbol}.parquet"
        
        if not os.path.exists(path):
            from .market import MockLoader
            return MockLoader(spec, ctx)

        # Logic: Crypto -> Polars, Equity -> DuckDB
        if spec.asset_class == "crypto":
            return PolarsLoader(spec, ctx)
        elif spec.asset_class == "equity":
            return DuckDBLoader(spec, ctx)

        # Fallback to Polars
        return PolarsLoader(spec, ctx)
