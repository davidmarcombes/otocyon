from dataclasses import dataclass
import polars as pl
from ..instrument import BaseInstrument, BaseSpec
from ..context import Context


@dataclass(frozen=True)
class SwapSpec(BaseSpec):
    notional: float
    fixed_rate: float
    float_index: str  # e.g., "SOFR"
    maturity: str  # e.g., "2030-01-01"
    pay_fixed: bool = True


class SwapInstrument(BaseInstrument):
    def __init__(self, specs: SwapSpec, data: pl.LazyFrame, ctx: Context):
        super().__init__(specs.symbol, data, ctx)
        self.specs = specs

    def get_type(self) -> str:
        return "swap"
