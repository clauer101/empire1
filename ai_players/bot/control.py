"""Embedded localhost HTTP control server for strategy overrides.

  GET  /status   → current strategy + snapshot
  POST /strategy → {"type": "attack", "params": {"target_uid": 42}, "duration_hours": 2}
  POST /reroll   → force re-roll on next cycle
"""

from __future__ import annotations

import json
import logging
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

log = logging.getLogger("bot.control")


class ControlServer:
    def __init__(self, port: int):
        self.port = port
        self.commands: queue.Queue[dict[str, Any]] = queue.Queue()
        self.status: dict[str, Any] = {}
        self._httpd: ThreadingHTTPServer | None = None

    def start(self) -> None:
        ctrl = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silence default access log
                pass

            def _json(self, code: int, payload: dict) -> None:
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/status":
                    self._json(200, ctrl.status)
                else:
                    self._json(404, {"error": "not found"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(raw or b"{}")
                except json.JSONDecodeError:
                    self._json(400, {"error": "invalid JSON"})
                    return
                if self.path == "/strategy":
                    ctrl.commands.put({"cmd": "strategy", "payload": payload})
                    self._json(200, {"accepted": True})
                elif self.path == "/reroll":
                    ctrl.commands.put({"cmd": "reroll"})
                    self._json(200, {"accepted": True})
                else:
                    self._json(404, {"error": "not found"})

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        thread.start()
        log.info("control server on 127.0.0.1:%d", self.port)

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()

    def drain(self) -> list[dict[str, Any]]:
        cmds = []
        while True:
            try:
                cmds.append(self.commands.get_nowait())
            except queue.Empty:
                return cmds
