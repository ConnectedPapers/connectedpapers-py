import json
import socket
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Iterator

import pytest

from connectedpapers import ConnectedPapersClient


def pytest_addoption(parser: Any) -> None:
    parser.addoption("--live-api", action="store_true", help="Allow live API tests")


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    if not config.getoption("--live-api"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="requires --live-api"))


@pytest.fixture(autouse=True)
def local_connections_only(monkeypatch: Any, request: Any) -> None:
    if request.config.getoption("--live-api") and "integration" in request.keywords:
        return
    original = socket.socket.connect

    def connect(sock: Any, address: Any) -> Any:
        if address[0] not in ("127.0.0.1", "::1"):
            raise AssertionError("Offline tests may only connect to localhost")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", connect)


class LocalAPI:
    def __init__(self) -> None:
        self.responses: Any = deque()
        self.requests: Any = []
        self.delays: Any = []
        self.url = ""

    def reply(self, payload: Any, status: int = 200) -> None:
        self.responses.append((status, json.dumps(payload)))

    def client(self, **kwargs: Any) -> ConnectedPapersClient:
        return ConnectedPapersClient(
            access_token="local-key", server_addr=self.url, **kwargs
        )


@pytest.fixture
def api(monkeypatch: Any) -> Iterator[LocalAPI]:
    api = LocalAPI()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            api.requests.append((self.path, self.headers.get("X-Api-Key")))
            status, body = (
                api.responses.popleft()
                if api.responses
                else (500, '{"error": "Unexpected request"}')
            )
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, format: str, *args: Any) -> None:
            pass

    async def sleep(delay: float) -> None:
        api.delays.append(delay)

    monkeypatch.setattr("connectedpapers.connected_papers_client.asyncio.sleep", sleep)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    api.url = "http://127.0.0.1:{}".format(server.server_port)
    thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.05), daemon=True
    )
    thread.start()
    try:
        yield api
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
