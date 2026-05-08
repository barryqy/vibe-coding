#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".lab-state"
LOG = STATE / "devnet-openai-shim.log"
PID = STATE / "devnet-openai-shim.pid"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def route() -> dict[str, str]:
    return {
        "base_url": os.getenv("LLM_BASE_URL", "").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "model": os.getenv("LLM_MODEL", "gpt-4o"),
    }


def json_response(handler: BaseHTTPRequestHandler, status: int, body: dict) -> None:
    data = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    raw_len = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_len)
    except ValueError:
        length = 0
    body = handler.rfile.read(length).decode("utf-8")
    return json.loads(body or "{}")


def call_devnet(body: dict) -> dict:
    config = route()
    if not config["base_url"] or not config["api_key"]:
        raise RuntimeError("LLM_BASE_URL or LLM_API_KEY is missing")

    clean_body = dict(body)
    clean_body["stream"] = False
    clean_body.pop("stream_options", None)
    clean_body.pop("tools", None)
    clean_body.pop("tool_choice", None)
    clean_body.pop("parallel_tool_calls", None)

    try:
        clean_body["max_tokens"] = min(int(clean_body.get("max_tokens", 1024)), 2048)
    except (TypeError, ValueError):
        clean_body["max_tokens"] = 1024

    data = json.dumps(clean_body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }
    request = urllib.request.Request(
        f"{config['base_url']}/chat/completions",
        data=data,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def event_chunk(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")


def stream_response(handler: BaseHTTPRequestHandler, request_body: dict, payload: dict) -> None:
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    model = request_body.get("model") or route()["model"]
    response_id = payload.get("id", "chatcmpl-devnet-shim")

    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()

    first = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "model": model,
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    }
    done = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    handler.wfile.write(event_chunk(first))
    handler.wfile.write(event_chunk(done))

    stream_options = request_body.get("stream_options") or {}
    if stream_options.get("include_usage"):
        usage = payload.get("usage") or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        handler.wfile.write(event_chunk({"choices": [], "usage": usage}))

    handler.wfile.write(b"data: [DONE]\n\n")


class ShimHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/v1/models":
            model = route()["model"]
            json_response(self, 200, {"object": "list", "data": [{"id": model, "object": "model"}]})
            return
        json_response(self, 404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/v1/chat/completions":
            json_response(self, 404, {"error": {"message": "not found"}})
            return

        try:
            request_body = read_json(self)
            payload = call_devnet(request_body)
        except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            json_response(self, 400, {"error": {"message": exc.__class__.__name__}})
            return

        if request_body.get("stream"):
            stream_response(self, request_body, payload)
            return

        json_response(self, 200, payload)


def ready(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/v1/models", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def ensure(host: str, port: int) -> int:
    if ready(host, port):
        print("DEVNET_OPENAI_SHIM=ready")
        print(f"base_url=http://{host}:{port}/v1")
        return 0

    STATE.mkdir(parents=True, exist_ok=True)
    with LOG.open("ab") as log:
        process = subprocess.Popen(
            [sys.executable, __file__, "--host", host, "--port", str(port)],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    PID.write_text(str(process.pid), encoding="utf-8")

    for _ in range(30):
        if ready(host, port):
            print("DEVNET_OPENAI_SHIM=ready")
            print(f"base_url=http://{host}:{port}/v1")
            return 0
        time.sleep(0.25)

    print("DEVNET_OPENAI_SHIM=failed")
    print(f"log={LOG.relative_to(ROOT)}")
    return 1


def serve(host: str, port: int) -> int:
    config = route()
    if not config["base_url"] or not config["api_key"]:
        print("DEVNET_OPENAI_SHIM=missing-env", file=sys.stderr)
        return 1

    server = ThreadingHTTPServer((host, port), ShimHandler)
    print(f"DEVNET_OPENAI_SHIM=serving http://{host}:{port}/v1", flush=True)
    server.serve_forever()
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Serve a tiny OpenAI-compatible shim for OpenCode.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--ensure", action="store_true")
    args = parser.parse_args(argv)

    if args.ensure:
        return ensure(args.host, args.port)
    return serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
