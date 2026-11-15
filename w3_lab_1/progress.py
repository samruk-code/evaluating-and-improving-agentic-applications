"""A single-line animated progress indicator for long-running calls.

`evaluate_dataframe(...)` shows its own tqdm progress bar, but tqdm's
carriage-return redraw only animates in place inside a real, unbuffered
terminal. Run through a captured subprocess -- like OpenCode's bash tool,
which reads a command's output as a text blob rather than a live pty -- each
refresh can land as its own line instead of overwriting the last one, so a
single progress bar turns into a wall of near-duplicate lines.

evaluate_dataframe() has no per-row callback to hook into, so this doesn't
try to track exact row counts. It's a plain spinner: one line, animated with
`\\r`, that doesn't care how many rows are left -- just that the call is
still running.

Usage:

    from progress import spinner

    with spinner(f"Evaluating with policy_compliance ({len(train_df)} rows)"):
        results = evaluate_dataframe(dataframe=train_df, evaluators=[policy_compliance], hide_tqdm_bar=True)

Always pass `hide_tqdm_bar=True` alongside this -- otherwise you get both
progress indicators fighting over the same line.
"""

from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager

_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def _spin(label: str, stop: threading.Event, started_at: float, interval: float) -> None:
    i = 0
    while not stop.is_set():
        elapsed = time.monotonic() - started_at
        frame = _FRAMES[i % len(_FRAMES)]
        sys.stdout.write(f"\r{frame} {label}... {elapsed:4.0f}s")
        sys.stdout.flush()
        i += 1
        stop.wait(interval)


@contextmanager
def spinner(label: str, interval: float = 0.12):
    """Animate `label` on a single line for the duration of the `with` block."""
    stop = threading.Event()
    started_at = time.monotonic()
    thread = threading.Thread(target=_spin, args=(label, stop, started_at, interval), daemon=True)
    thread.start()

    ok = True
    try:
        yield
    except BaseException:
        ok = False
        raise
    finally:
        stop.set()
        thread.join()
        elapsed = time.monotonic() - started_at
        mark = "✓" if ok else "✗"
        # Overwrite the spinner line one last time with a static result line,
        # padded to blank out any leftover characters from a longer frame.
        sys.stdout.write(f"\r{mark} {label} ({elapsed:.1f}s)" + " " * 12 + "\n")
        sys.stdout.flush()
