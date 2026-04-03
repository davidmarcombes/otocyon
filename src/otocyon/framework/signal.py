from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid


@dataclass
class Signal:
    """
    Represents an intent to trade or hold a position.

    Signals are produced by strategies in the Brain Pass and executed by the Engine 
    against the Portfolio in the Muscle Pass. They express targets natively as weights.
    """
    symbol: str
    weight: float  # Target portfolio weight (e.g., 0.5 for 50%)
    side: str  # "LONG", "SHORT", "FLAT"

    # Internal Tracking
    strategy_id: str = "unknown"
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Status Flags
    _cancelled: bool = False
    _cancel_reason: Optional[str] = None

    def cancel(self, reason: str = "No reason provided"):
        """Allows a listener to stop this signal from reaching the portfolio."""
        self._cancelled = True
        self._cancel_reason = reason

    @property
    def is_active(self) -> bool:
        return not self._cancelled
