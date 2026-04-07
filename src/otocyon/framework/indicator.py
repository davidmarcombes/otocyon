import time
from typing import Any

import msgspec


class Indicator(msgspec.Struct, frozen=True):
    """
    Represents a specific metric or value detected by a strategy or globally calculated.

    Indicators are produced in the Sensor Pass and consumed in the Brain Pass. They
    are read-only (frozen) to ensure safe multi-strategy execution environments.
    """

    name: str
    value: Any
    symbol: str
    timestamp: float = msgspec.field(default_factory=time.time)
    metadata: dict[str, Any] = msgspec.field(default_factory=dict)
