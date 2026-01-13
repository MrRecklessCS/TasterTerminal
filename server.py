import asyncio
import functools
import http.server
import json
import os
import pty
import signal
import socketserver
import struct
import termios
import fcntl
from typing import Optional

import websockets

HOST = "0.0.0.0"
HTTP_PORT = 8000
WS_PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SHELL = os.environ.get("SHELL", "/bin/bash")


def set_pty_window_size(fd: int, cols: int, rows: int) -> None:
    size = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, size)


async def handle_terminal(websocket: websockets.WebSocketServerProtocol) -> None:
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(SHELL, [SHELL])

    loop = asyncio.get_running_loop()

    async def send_output(data: bytes) -> None:
        if websocket.closed:
            return
        await websocket.send(data.decode(errors="ignore"))

    def on_fd_readable() -> None:
        try:
            data = os.read(fd, 1024)
        except OSError:
            data = b""
        if data:
            asyncio.create_task(send_output(data))
        else:
            asyncio.create_task(websocket.close())

    loop.add_reader(fd, on_fd_readable)

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                os.write(fd, message)
                continue

            payload: Optional[dict]
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                payload = None

            if payload and payload.get("type") == "resize":
                cols = int(payload.get("cols", 80))
                rows = int(payload.get("rows", 24))
                set_pty_window_size(fd, cols, rows)
            else:
                data = payload.get("data") if payload else message
                os.write(fd, str(data).encode())
    finally:
        loop.remove_reader(fd)
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


async def main() -> None:
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=STATIC_DIR,
    )
    httpd = socketserver.TCPServer((HOST, HTTP_PORT), handler)

    http_thread = asyncio.to_thread(httpd.serve_forever)

    async with websockets.serve(handle_terminal, HOST, WS_PORT):
        print(f"HTTP server running at http://{HOST}:{HTTP_PORT}")
        print(f"WebSocket server running at ws://{HOST}:{WS_PORT}")
        await http_thread


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
