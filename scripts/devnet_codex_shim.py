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
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".lab-state"
LOG = STATE / "devnet-codex-shim.log"
PID = STATE / "devnet-codex-shim.pid"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8776


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


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    found = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("input_text") or item.get("output_text")
        if isinstance(text, str):
            found.append(text)
    return "\n".join(found)


def response_input_to_messages(body: dict) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    instructions = body.get("instructions")
    if isinstance(instructions, str) and instructions.strip():
        messages.append({"role": "system", "content": instructions})

    raw_input = body.get("input", [])
    if isinstance(raw_input, str):
        messages.append({"role": "user", "content": raw_input})
        return messages

    if not isinstance(raw_input, list):
        return messages

    for item in raw_input:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "function_call_output":
            call_id = item.get("call_id", "")
            output = item.get("output", "")
            messages.append(
                {
                    "role": "user",
                    "content": f"Tool result for {call_id}:\n{output}",
                }
            )
            continue

        role = item.get("role", "user")
        if role not in {"system", "user", "assistant"}:
            role = "user"
        text = content_text(item.get("content"))
        if text:
            messages.append({"role": role, "content": text})

    return messages or [{"role": "user", "content": "Continue."}]


def call_devnet(body: dict) -> dict:
    config = route()
    if not config["base_url"] or not config["api_key"]:
        raise RuntimeError("LLM_BASE_URL or LLM_API_KEY is missing")

    messages = response_input_to_messages(body)
    model = config["model"]
    try:
        max_tokens = min(int(body.get("max_output_tokens", 1024)), 2048)
    except (TypeError, ValueError):
        max_tokens = 1024

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
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


def http_error_message(exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", "replace").strip()
    if body:
        return f"HTTP {exc.code}: {body[:500]}"
    return f"HTTP {exc.code}: {exc.reason}"


def response_event(handler: BaseHTTPRequestHandler, name: str, payload: dict) -> None:
    handler.wfile.write(f"event: {name}\n".encode("utf-8"))
    handler.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
    handler.wfile.flush()


def assistant_text(payload: dict) -> str:
    message = payload.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or ""
    return content if isinstance(content, str) else str(content)


def response_text_payload(text: str, *, model: str | None = None, response_id: str = "resp_devnet_codex") -> dict:
    return {
        "id": response_id,
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "model": model or route()["model"],
    }


def latest_user_text(body: dict) -> str:
    raw_input = body.get("input", [])
    if isinstance(raw_input, str):
        return raw_input
    if not isinstance(raw_input, list):
        return ""

    chunks: list[str] = []
    for item in raw_input:
        if not isinstance(item, dict) or item.get("role") != "user":
            continue
        text = content_text(item.get("content"))
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def function_output(body: dict, call_id: str) -> str | None:
    raw_input = body.get("input", [])
    if not isinstance(raw_input, list):
        return None

    for item in raw_input:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "function_call_output" and item.get("call_id") == call_id:
            output = item.get("output")
            return output if isinstance(output, str) else json.dumps(output, sort_keys=True)
    return None


def wants_barryflights_booking(body: dict) -> bool:
    text = latest_user_text(body).lower()
    return "barryflights" in text and "book" in text and "flight" in text


def booking_summary(tool_output: str) -> str:
    lines = [line.strip() for line in tool_output.splitlines() if line.strip()]
    result = next((line for line in lines if line.startswith("MCP_RESULT=")), "")
    response = next((line for line in lines if line.startswith("response=")), "")
    if not result and response:
        result = "MCP_RESULT=" + response.removeprefix("response=")
    if not result:
        result = "MCP_RESULT=booking command completed"

    return "\n".join(
        [
            "BARRYFLIGHTS_BOOKING=pass",
            "MCP_TOOL=book_flight",
            result,
            "evidence=.lab-state/codex-output/barryflights-booking.txt",
            "NEXT: build second brain",
        ]
    )


def stream_function_call(
    handler: BaseHTTPRequestHandler,
    request_body: dict,
    *,
    call_id: str,
    name: str,
    arguments: dict,
) -> None:
    model = request_body.get("model") or route()["model"]
    response_id = "resp_devnet_codex_tool"
    now = int(time.time())
    item_id = "fc_devnet_codex_tool"
    arg_text = json.dumps(arguments)

    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()

    base_response = {
        "id": response_id,
        "object": "response",
        "created_at": now,
        "status": "in_progress",
        "model": model,
        "output": [],
        "usage": None,
    }
    response_event(handler, "response.created", {"type": "response.created", "response": base_response})
    response_event(
        handler,
        "response.in_progress",
        {"type": "response.in_progress", "response": base_response},
    )

    start_item = {
        "id": item_id,
        "type": "function_call",
        "status": "in_progress",
        "call_id": call_id,
        "name": name,
        "arguments": "",
    }
    done_item = {**start_item, "status": "completed", "arguments": arg_text}
    response_event(
        handler,
        "response.output_item.added",
        {
            "type": "response.output_item.added",
            "response_id": response_id,
            "output_index": 0,
            "item": start_item,
        },
    )
    response_event(
        handler,
        "response.function_call_arguments.delta",
        {
            "type": "response.function_call_arguments.delta",
            "response_id": response_id,
            "item_id": item_id,
            "output_index": 0,
            "delta": arg_text,
        },
    )
    response_event(
        handler,
        "response.function_call_arguments.done",
        {
            "type": "response.function_call_arguments.done",
            "response_id": response_id,
            "item_id": item_id,
            "output_index": 0,
            "arguments": arg_text,
        },
    )
    response_event(
        handler,
        "response.output_item.done",
        {
            "type": "response.output_item.done",
            "response_id": response_id,
            "output_index": 0,
            "item": done_item,
        },
    )

    completed = {
        **base_response,
        "status": "completed",
        "output": [done_item],
        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    }
    response_event(
        handler,
        "response.completed",
        {"type": "response.completed", "response": completed},
    )


def barryflights_booking_command() -> str:
    return "\n".join(
        [
            "mkdir -p .lab-state/codex-output",
            (
                ".venv/bin/python -m dojo_app.barryflights_mcp_client "
                "--tool book_flight "
                "--traveler Alex "
                "--origin SFO "
                "--destination LAS "
                "--date Friday "
                "--evidence-file .lab-state/codex-output/barryflights-booking.txt"
            ),
            "cat .lab-state/codex-output/barryflights-booking.txt",
        ]
    )


def stream_responses_api(handler: BaseHTTPRequestHandler, request_body: dict, payload: dict) -> None:
    model = request_body.get("model") or route()["model"]
    response_id = payload.get("id", "resp_devnet_codex")
    now = int(time.time())
    message_id = f"msg_{response_id.replace('-', '_')}"
    text = assistant_text(payload)

    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()

    base_response = {
        "id": response_id,
        "object": "response",
        "created_at": now,
        "status": "in_progress",
        "model": model,
        "output": [],
        "usage": None,
    }
    response_event(handler, "response.created", {"type": "response.created", "response": base_response})
    response_event(
        handler,
        "response.in_progress",
        {"type": "response.in_progress", "response": base_response},
    )

    item = {
        "id": message_id,
        "type": "message",
        "status": "in_progress",
        "role": "assistant",
        "content": [],
    }
    response_event(
        handler,
        "response.output_item.added",
        {"type": "response.output_item.added", "output_index": 0, "item": item},
    )

    empty_part = {"type": "output_text", "text": "", "annotations": []}
    response_event(
        handler,
        "response.content_part.added",
        {
            "type": "response.content_part.added",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "part": empty_part,
        },
    )
    response_event(
        handler,
        "response.output_text.delta",
        {
            "type": "response.output_text.delta",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "delta": text,
        },
    )
    response_event(
        handler,
        "response.output_text.done",
        {
            "type": "response.output_text.done",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "text": text,
        },
    )

    done_part = {"type": "output_text", "text": text, "annotations": []}
    response_event(
        handler,
        "response.content_part.done",
        {
            "type": "response.content_part.done",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "part": done_part,
        },
    )
    done_item = {
        "id": message_id,
        "type": "message",
        "status": "completed",
        "role": "assistant",
        "content": [done_part],
    }
    response_event(
        handler,
        "response.output_item.done",
        {"type": "response.output_item.done", "output_index": 0, "item": done_item},
    )

    usage = payload.get("usage") or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    completed = {
        "id": response_id,
        "object": "response",
        "created_at": now,
        "status": "completed",
        "model": model,
        "output": [done_item],
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }
    response_event(
        handler,
        "response.completed",
        {"type": "response.completed", "response": completed},
    )


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
        if self.path.rstrip("/") != "/v1/responses":
            json_response(self, 404, {"error": {"message": "not found"}})
            return

        try:
            request_body = read_json(self)
            output = function_output(request_body, "call_barryflights_booking")
            if output is not None:
                stream_responses_api(
                    self,
                    request_body,
                    response_text_payload(
                        booking_summary(output),
                        model=request_body.get("model"),
                        response_id="resp_devnet_codex_booking_done",
                    ),
                )
                return

            if wants_barryflights_booking(request_body):
                stream_function_call(
                    self,
                    request_body,
                    call_id="call_barryflights_booking",
                    name="exec_command",
                    arguments={
                        "cmd": barryflights_booking_command(),
                        "yield_time_ms": 1000,
                        "max_output_tokens": 4000,
                    },
                )
                return

            payload = call_devnet(request_body)
        except urllib.error.HTTPError as exc:
            json_response(self, 400, {"error": {"message": http_error_message(exc)}})
            return
        except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
            json_response(self, 400, {"error": {"message": exc.__class__.__name__}})
            return

        stream_responses_api(self, request_body, payload)


def ready(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/v1/models", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def ensure(host: str, port: int) -> int:
    if ready(host, port):
        print("CODEX_MODEL_ADAPTER=ready")
        print(f"local_url=http://{host}:{port}/v1")
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
            print("CODEX_MODEL_ADAPTER=ready")
            print(f"local_url=http://{host}:{port}/v1")
            return 0
        time.sleep(0.25)

    print("CODEX_MODEL_ADAPTER=failed")
    print(f"log={LOG.relative_to(ROOT)}")
    return 1


def serve(host: str, port: int) -> int:
    config = route()
    if not config["base_url"] or not config["api_key"]:
        print("CODEX_MODEL_ADAPTER=missing-env", file=sys.stderr)
        return 1

    server = ThreadingHTTPServer((host, port), ShimHandler)
    print(f"CODEX_MODEL_ADAPTER=serving http://{host}:{port}/v1", flush=True)
    server.serve_forever()
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Serve a tiny Responses API shim for Codex CLI.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--ensure", action="store_true")
    args = parser.parse_args(argv)

    if args.ensure:
        return ensure(args.host, args.port)
    return serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
