"""Event bus between the pipeline (worker threads) and the displays (asyncio, Qt).

The pipeline publishes from its own thread. Async subscribers (WebSocket
clients) receive events on the event loop the bus is bound to; plain
listeners (console, overlay) are called directly in the publishing thread.
New subscribers first get the recent history so a phone that connects late
still sees the last lines.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from collections.abc import AsyncIterator, Callable

from telsiz.events import VoiceEvent

log = logging.getLogger(__name__)

Listener = Callable[[VoiceEvent], None]


class EventBus:
    def __init__(self, history: int = 20, queue_size: int = 100) -> None:
        self._history: deque[VoiceEvent] = deque(maxlen=history)
        self._queue_size = queue_size
        self._queues: set[asyncio.Queue[VoiceEvent]] = set()
        self._listeners: list[Listener] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: int | None = None

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        """Deliver to async subscribers on ``loop``; call from that loop's thread."""
        self._loop = loop
        self._loop_thread = threading.get_ident()

    def add_listener(self, listener: Listener) -> None:
        self._listeners.append(listener)

    @property
    def subscriber_count(self) -> int:
        return len(self._queues)

    def history(self) -> list[VoiceEvent]:
        return list(self._history)

    def publish(self, event: VoiceEvent) -> None:
        """Thread-safe."""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                log.exception("Event listener failed")
        loop = self._loop
        if loop is None or threading.get_ident() == self._loop_thread:
            self._deliver(event)
            return
        try:
            loop.call_soon_threadsafe(self._deliver, event)
        except RuntimeError:  # loop already closed during shutdown
            self._history.append(event)

    def _deliver(self, event: VoiceEvent) -> None:
        self._history.append(event)
        for queue in self._queues:
            if queue.full():
                queue.get_nowait()  # a slow client loses the oldest line, not memory
            queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[VoiceEvent]:
        """Recent history, then live events. Close the generator to unsubscribe."""
        queue: asyncio.Queue[VoiceEvent] = asyncio.Queue(maxsize=self._queue_size)
        self._queues.add(queue)
        try:
            for event in list(self._history):
                yield event
            while True:
                yield await queue.get()
        finally:
            self._queues.discard(queue)
