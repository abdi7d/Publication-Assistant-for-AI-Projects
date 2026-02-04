from dataclasses import dataclass
from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPMessage:
    topic: str
    payload: Any


class MCPBus:
    """A tiny in-memory publish/subscribe bus used for tests and simple local orchestration.

    This is a minimal implementation sufficient for unit tests and local runs.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[MCPMessage], None]]] = {}

    def publish(self, topic: str, payload: Any):
        msg = MCPMessage(topic=topic, payload=payload)
        subs = list(self._subscribers.get(topic, []))
        logger.debug("MCPBus.publish topic=%s subs=%d", topic, len(subs))
        for cb in subs:
            try:
                cb(msg)
            except Exception:
                logger.exception("Subscriber callback raised")

    def subscribe(self, topic: str, callback: Callable[[MCPMessage], None]):
        self._subscribers.setdefault(topic, []).append(callback)

    def clear(self):
        self._subscribers.clear()
