import polars as pl
from otocyon.framework.instrument import BaseInstrument, BaseSpec
from otocyon.framework.loader import BaseLoader
from otocyon.framework.context import Context


# 1. Custom Specification
class CryptoSpec(BaseSpec):
    pass

# 2. Custom Instrument
class CryptoInstrument(BaseInstrument):
    def get_type(self) -> str:
        return "crypto"

# 3. Simple Mock Loader
class MockLoader(BaseLoader):
    def load(self) -> pl.DataFrame:
        return pl.DataFrame({
            "close": [100.0, 101.0, 102.0],
            "volume": [10.0, 15.0, 20.0]
        })

def test_instrument_data_collection(logger):
    """
    Shows how an instrument uses its loader to collect data.
    """
    # 1. Setup
    ctx = Context(logger=logger, data_root="/tmp")
    spec = CryptoSpec(symbol="ETH", asset_class="crypto")
    loader = MockLoader(spec, ctx)
    instrument = CryptoInstrument(spec, loader, ctx)

    # 2. Action
    instrument._collect()

    # 3. Verification
    assert len(instrument) == 3
    assert instrument.price == 100.0
    assert instrument.get_type() == "crypto"

def test_lazy_stat_calculation(logger):
    """
    Shows how get_stat() can lazily calculate attributes using Polars expressions.
    """
    # 1. Setup instrument with data
    ctx = Context(logger=logger, data_root="/tmp")
    spec = CryptoSpec(symbol="ETH", asset_class="crypto")
    loader = MockLoader(spec, ctx)
    instrument = CryptoInstrument(spec, loader, ctx)
    instrument._collect()

    # 2. Action: Calculate a new stat lazily
    # Here we multiply volume by price
    expr = pl.col("close") * pl.col("volume")
    value = instrument.get_stat("notional", expr)

    # 3. Verification
    assert value == 1000.0 # 100.0 * 10.0
    # Ensure it's now present in the internal dataframe
    assert "notional" in instrument._df.columns
