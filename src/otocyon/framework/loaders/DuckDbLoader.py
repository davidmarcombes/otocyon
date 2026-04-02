import polars
from ..loader import BaseLoader
from ..instrument import BaseSpec
from ..context import Context


class DuckDBLoader(BaseLoader):
    def __init__(self, spec: BaseSpec, ctx: Context):
        super().__init__(spec, ctx)

    def load(self) -> polars.DataFrame:
        path = f"{self.ctx.data_root}/{self.spec.asset_class}/{self.spec.symbol}.parquet"
        self.logger().debug(f"DuckDB scanning: {path}")

        # SQL calculation: daily returns via window function
        query = """
            SELECT *, 
                   (close - lag(close) OVER (ORDER BY timestamp)) / lag(close) OVER (ORDER BY timestamp) as returns
            FROM read_parquet(?)
        """
        return self.ctx.duckdb_connection.execute(query, [path]).pl()
