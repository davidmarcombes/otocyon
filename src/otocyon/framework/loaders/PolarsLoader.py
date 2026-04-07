import polars

from ..loader import BaseLoader
from ..schemas import CryptoSchema


class PolarsLoader(BaseLoader):
    def load(self) -> polars.DataFrame:
        path = f"{self.ctx.data_root}/{self.spec.asset_class}/{self.spec.symbol}.parquet"
        self.logger().bind(symbol=self.spec.symbol, path=path).debug("loader.polars.scan")

        df = polars.scan_parquet(path).collect()
        return CryptoSchema.validate(df)
