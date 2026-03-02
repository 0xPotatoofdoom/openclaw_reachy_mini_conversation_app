"""
Telegram Bridge — watches /tmp/reachy_inbox.txt and injects messages
into the active OpenAI realtime session.
"""

import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

INBOX_FILE = Path("/tmp/reachy_inbox.txt")
POLL_INTERVAL = 1.0


class TelegramBridge:
    def __init__(self) -> None:
        self._connection = None
        self._loop = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        INBOX_FILE.touch(exist_ok=True)
        self._last_size = INBOX_FILE.stat().st_size

    def register_connection(self, connection: object, loop: asyncio.AbstractEventLoop) -> None:
        with self._lock:
            self._connection = connection
            self._loop = loop
        logger.info("TelegramBridge: connection registered")

    def unregister_connection(self) -> None:
        with self._lock:
            self._connection = None
            self._loop = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="telegram-bridge")
        self._thread.start()
        logger.info("TelegramBridge: watcher started on %s", INBOX_FILE)

    def stop(self) -> None:
        self._stop.set()

    def _watch_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._check_inbox()
            except Exception as e:
                logger.warning("TelegramBridge error: %s", e)
            time.sleep(POLL_INTERVAL)

    def _check_inbox(self) -> None:
        if not INBOX_FILE.exists():
            INBOX_FILE.touch()
            self._last_size = 0
            return
        current_size = INBOX_FILE.stat().st_size
        if current_size <= self._last_size:
            return
        with open(INBOX_FILE, "r") as f:
            f.seek(self._last_size)
            new_content = f.read()
        self._last_size = current_size
        for line in new_content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                text = msg.get("text", "")
            except json.JSONDecodeError:
                text = line
            if text:
                self._inject(text)

    def _inject(self, text: str) -> None:
        with self._lock:
            conn = self._connection
            loop = self._loop
        if conn is None or loop is None:
            logger.warning("TelegramBridge: no active connection for: %s", text[:60])
            return
        try:
            asyncio.run_coroutine_threadsafe(self._send(conn, text), loop)
        except Exception as e:
            logger.warning("TelegramBridge: inject error: %s", e)

    async def _send(self, conn: object, text: str) -> None:
        try:
            await conn.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}],
                }
            )
            await conn.response.create()
            logger.info("TelegramBridge: injected: %r", text[:80])
        except Exception as e:
            logger.warning("TelegramBridge: send failed: %s", e)


bridge = TelegramBridge()
