from dataclasses import dataclass
from ..instrument import BaseInstrument, BaseSpec


@dataclass(frozen=True)
class CryptoSpec(BaseSpec):
    """
    Specification for a crypto instrument.
    """

    asset_class: str = "crypto"


class CryptoInstrument(BaseInstrument):
    """
    Instrument for a crypto asset.
    """

    def get_type(self) -> str:
        return "crypto"
