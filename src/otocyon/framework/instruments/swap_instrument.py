from dataclasses import dataclass
from typing import Optional
from ..instrument import BaseInstrument, BaseSpec
from ..loader import LoaderProtocol
from ..context import Context


@dataclass(frozen=True)
class SwapSpec(BaseSpec):
    notional: float
    fixed_rate: float
    float_index: str  # e.g., "SOFR"
    maturity: str  # e.g., "2030-01-01"
    pay_fixed: bool = True


class SwapInstrument(BaseInstrument):
    def __init__(self, specs: SwapSpec, loader: Optional[LoaderProtocol], ctx: Context):
        super().__init__(specs, loader, ctx)
        self.specs = specs

    def get_type(self) -> str:
        return "swap"
