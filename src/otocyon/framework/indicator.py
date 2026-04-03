from dataclasses import dataclass, field
from typing import Any, Dict
import time


@dataclass(frozen=True)
class Indicator:
    """
    Represents a specific metric or value detected by a strategy or globally calculated.
    
    Indicators are produced in the Sensor Pass and consumed in the Brain Pass. They
    are read-only (frozen) to ensure safe multi-strategy execution environments.
    """
    name: str
    value: Any
    symbol: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
