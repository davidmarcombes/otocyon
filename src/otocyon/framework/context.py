from dataclasses import dataclass, field
import logging


@dataclass(frozen=True)  # Frozen makes it immutable and thread-safe
class Context:
    """
    The Context object is a thread-safe container for runtime information.
    It is passed to every Strategy instance during execution.
    """
    logger: logging.Logger
    data_root: str
    env: str = "research"  
    timezone: str = "UTC"
    metadata: dict = field(default_factory=dict)
