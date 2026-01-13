# TasterTerminal

A simple Python web server that provides a real terminal in the browser for classroom demos.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Open `http://localhost:8000` in a browser. The terminal connects to the WebSocket server on port `8765`.

## How it works

- The Python server serves a static page with an xterm.js terminal.
- Each browser connection spawns a PTY-backed shell on the host.
- The terminal input/output is streamed over a WebSocket connection.

## Safety note

This demo is designed for sandboxed or classroom environments only. Running arbitrary commands on a host machine can be dangerous, so ensure the server runs inside a locked-down environment.
