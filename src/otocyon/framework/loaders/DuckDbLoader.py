import polars

from ..loader import BaseLoader
from ..schemas import EquitySchema


class DuckDBLoader(BaseLoader):
    def load(self) -> polars.DataFrame:
        path = f"{self.ctx.data_root}/{self.spec.asset_class}/{self.spec.symbol}.parquet"
        self.logger().bind(symbol=self.spec.symbol, path=path).debug("loader.duckdb.scan")

        # SQL calculation: daily returns via window function
        query = """
            SELECT *,
                   (close - lag(close) OVER (ORDER BY timestamp)) / lag(close) OVER (ORDER BY timestamp) as returns
            FROM read_parquet(?)
        """
        df = self.ctx.duckdb_connection.execute(query, [path]).pl()
        return EquitySchema.validate(df)
