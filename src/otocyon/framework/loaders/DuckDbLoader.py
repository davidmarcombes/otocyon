from typing import Any
from pathlib import Path
import duckdb
import polars
from ..loader import BaseLoader
from ..instrument import BaseSpec
from ..context import Context


class DuckDBLoader(BaseLoader):
    def __init__(self, spec: BaseSpec, ctx: Context):
        super().__init__(spec, ctx)

    def load(self) -> polars.DataFrame:
        self.logger().debug(f"DuckDB querying symbol: {self.spec.symbol}")

        # We use a parameterized query for safety and speed
        query = """
            SELECT * FROM market_data 
            WHERE symbol = ? 
        """

        # .pl() is the magic method that turns a DuckDB result
        # into a Polars DataFrame without copying memory.
        return self.ctx.duckdb_connection.execute(query, [self.spec.symbol]).pl()
