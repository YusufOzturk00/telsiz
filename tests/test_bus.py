"""Tests for the event bus between the pipeline and the displays."""

import asyncio
import threading

from telsiz.bus import EventBus
from telsiz.events import VoiceEvent


def event(text: str) -> VoiceEvent:
    return VoiceEvent("en", 0.9, text, f"<{text}>", "tr", 100, ts=1.0)


async def take(stream, n):
    out = []
    async for item in stream:
        out.append(item.original)
        if len(out) == n:
            break
    return out


def test_history_keeps_the_latest_events():
    bus = EventBus(history=2)
    for text in ("a", "b", "c"):
        bus.publish(event(text))

    assert [e.original for e in bus.history()] == ["b", "c"]


def test_listeners_are_called_for_each_event():
    bus = EventBus()
    seen = []
    bus.add_listener(lambda e: seen.append(e.original))

    bus.publish(event("a"))

    assert seen == ["a"]


def test_failing_listener_does_not_break_publishing():
    bus = EventBus()
    seen = []

    def broken(_):
        raise RuntimeError("boom")

    bus.add_listener(broken)
    bus.add_listener(lambda e: seen.append(e.original))

    bus.publish(event("a"))

    assert seen == ["a"]


def test_subscriber_gets_history_then_live_events():
    async def scenario():
        bus = EventBus()
        bus.bind(asyncio.get_running_loop())
        bus.publish(event("old"))
        stream = bus.subscribe()
        task = asyncio.create_task(take(stream, 2))
        await asyncio.sleep(0)
        bus.publish(event("new"))
        return await asyncio.wait_for(task, 2)

    assert asyncio.run(scenario()) == ["old", "new"]


def test_events_published_from_another_thread_reach_subscribers():
    async def scenario():
        bus = EventBus()
        bus.bind(asyncio.get_running_loop())
        task = asyncio.create_task(take(bus.subscribe(), 3))
        await asyncio.sleep(0)

        def worker():
            for text in ("a", "b", "c"):
                bus.publish(event(text))

        thread = threading.Thread(target=worker)
        thread.start()
        result = await asyncio.wait_for(task, 2)
        thread.join()
        return result

    assert asyncio.run(scenario()) == ["a", "b", "c"]


def test_closed_subscription_is_removed():
    async def scenario():
        bus = EventBus()
        bus.bind(asyncio.get_running_loop())
        stream = bus.subscribe()
        task = asyncio.create_task(take(stream, 1))
        await asyncio.sleep(0)
        assert bus.subscriber_count == 1
        bus.publish(event("a"))
        await asyncio.wait_for(task, 2)
        await stream.aclose()
        return bus.subscriber_count

    assert asyncio.run(scenario()) == 0


def test_slow_subscriber_drops_oldest_events_instead_of_growing():
    async def scenario():
        bus = EventBus(queue_size=2)
        bus.bind(asyncio.get_running_loop())
        stream = bus.subscribe()
        first = asyncio.create_task(take(stream, 1))
        bus.publish(event("a"))
        assert await asyncio.wait_for(first, 2) == ["a"]
        for text in ("b", "c", "d"):
            bus.publish(event(text))
        await asyncio.sleep(0)
        return await asyncio.wait_for(take(stream, 2), 2)

    assert asyncio.run(scenario()) == ["c", "d"]
