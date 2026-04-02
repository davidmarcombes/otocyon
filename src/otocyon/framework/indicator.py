from dataclasses import dataclass, field
from typing import Any, Dict
import time


@dataclass(frozen=True)
class Indicator:
    name: str
    value: Any
    symbol: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
