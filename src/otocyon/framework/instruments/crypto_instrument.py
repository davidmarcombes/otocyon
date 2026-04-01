from dataclasses import dataclass
from ..instrument import BaseInstrument, BaseSpec


@dataclass(frozen=True)
class CryptoSpec(BaseSpec):
    # We hardcode the asset_class for this subclass
    asset_class: str = "crypto"


class CryptoInstrument(BaseInstrument):
    def get_type(self):
        return "crypto"
