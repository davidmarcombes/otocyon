from dataclasses import dataclass
from ..instrument import BaseInstrument, BaseSpec


@dataclass(frozen=True)
class EquitySpec(BaseSpec):
    # We hardcode the asset_class for this subclass
    asset_class: str = "equity"


class EquityInstrument(BaseInstrument):
    def get_type(self) -> str:
        return "equity"

    @property
    def dividend(self) -> float:
        # Only Equities have a 'div' column in the Parquet
        if self._df is None:
            raise ValueError("Data not collected yet.")
        return float(self._df["div"][self._cursor])
