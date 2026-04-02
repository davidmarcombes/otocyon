import polars

from ..loader import BaseLoader
from ..instrument import BaseSpec
from ..context import Context


class PolarsLoader(BaseLoader):
    def __init__(self, spec: BaseSpec, ctx: Context):
        super().__init__(spec, ctx)
    
    def load(self) -> polars.DataFrame:
        # Determine file path based on asset class and symbol
        path = f"{self.ctx.data_root}/{self.spec.asset_class}/{self.spec.symbol}.parquet"
        self.logger().debug(f"Polars scanning: {path}")

        return (
            polars.scan_parquet(path)
            .with_columns([
                # Calclate MA_5 as part of the load plan
                polars.col("close").rolling_mean(window_size=5).alias("ma_5")
            ])
            .collect()  # Materialize into RAM
        )
