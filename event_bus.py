# NicheSignal v5 — event_bus.py — rewritten 2026-04-24
"""Thread-safe event bus for real-time UI logging from pipeline agents."""

import queue as _queue

_event_queue = _queue.Queue()


def emit_event(msg: str):
    """Emit a log event that the UI can consume in real-time."""
    _event_queue.put(msg)


def get_events() -> list[str]:
    """Drain all pending events from the queue."""
    events = []
    while not _event_queue.empty():
        try:
            events.append(_event_queue.get_nowait())
        except _queue.Empty:
            break
    return events


def clear_events():
    """Clear all pending events."""
    while not _event_queue.empty():
        try:
            _event_queue.get_nowait()
        except _queue.Empty:
            break
