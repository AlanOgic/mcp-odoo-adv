"""Shared logging helpers for the transport runners."""
from __future__ import annotations

import atexit
import os
import sys
from datetime import datetime
from typing import IO


class TeeLogger:
    """Write every message to both ``sys.stderr`` and a log file.

    Registered with :mod:`atexit` so the underlying file is closed on
    interpreter exit (not via ``__del__`` which runs during shutdown with
    modules already torn down).
    """

    def __init__(self, file_path: str) -> None:
        self.terminal: IO[str] = sys.stderr
        self.log: IO[str] = open(file_path, "a", encoding="utf-8")
        atexit.register(self.close)

    def write(self, message: str) -> None:
        self.terminal.write(message)
        if not self.log.closed:
            self.log.write(message)
            self.log.flush()

    def flush(self) -> None:
        self.terminal.flush()
        if not self.log.closed:
            self.log.flush()

    def close(self) -> None:
        if not self.log.closed:
            try:
                self.log.close()
            except Exception:
                pass


def setup_file_logging(transport_name: str, log_dir: str = "logs") -> str:
    """Redirect ``sys.stderr`` to a tee that writes to file + terminal.

    Returns the resolved log-file path. The file lives under ``log_dir``
    with a name of ``mcp_server_<transport>_<timestamp>.log``.
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"mcp_server_{transport_name}_{timestamp}.log")
    sys.stderr = TeeLogger(log_file)  # type: ignore[assignment]
    return log_file
