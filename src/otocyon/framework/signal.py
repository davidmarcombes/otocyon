import uuid
from typing import Any

import msgspec


class Signal(msgspec.Struct):
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
    signal_id: str = msgspec.field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: dict[str, Any] = msgspec.field(default_factory=dict)

    # Status Flags
    _cancelled: bool = False
    _cancel_reason: str | None = None

    def cancel(self, reason: str = "No reason provided") -> None:
        """Allows a listener to stop this signal from reaching the portfolio."""
        self._cancelled = True
        self._cancel_reason = reason

    @property
    def is_active(self) -> bool:
        return not self._cancelled
