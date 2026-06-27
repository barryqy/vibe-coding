#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
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
SHIM_VERSION = "tictactoe-scenario-20260627"


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


def response_text_payload(
    text: str,
    *,
    model: str | None = None,
    response_id: str = "resp_devnet_codex",
) -> dict:
    return {
        "id": response_id,
        "choices": [{"message": {"content": text}}],
        "usage": None,
        "model": model or route()["model"],
    }


def latest_user_text(body: dict) -> str:
    raw_input = body.get("input", [])
    if isinstance(raw_input, str):
        return raw_input
    if not isinstance(raw_input, list):
        return ""

    latest = ""
    for item in raw_input:
        if not isinstance(item, dict) or item.get("role") != "user":
            continue
        text = content_text(item.get("content"))
        if text:
            latest = text
    return latest


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


def wants_barryflights_status(body: dict) -> bool:
    text = latest_user_text(body).lower()
    return "barryflights" in text and "flight" in text and ("status" in text or "check" in text)


def wants_barryflights_booking(body: dict) -> bool:
    text = latest_user_text(body).lower()
    mentions_barryflights = "barryflights" in text or "book_flight" in text
    mentions_booking = "book_flight" in text or "book a flight" in text or "booking" in text
    return mentions_barryflights and mentions_booking


def wants_tictactoe_scenario(body: dict) -> bool:
    text = latest_user_text(body).lower()
    if "vibe-coding-dojo.md" in text or "project note" in text:
        return False
    mentions_game = "tic-tac-toe" in text or "tictactoe" in text or "tic tac toe" in text
    wants_scenario = "scenario" in text or "starting board" in text or "board" in text
    wants_build = "create" in text or "make" in text or "generate" in text
    return mentions_game and wants_scenario and wants_build


def status_summary(tool_output: str) -> str:
    lines = [line.strip() for line in tool_output.splitlines() if line.strip()]
    response = next((line for line in lines if line.startswith("response=")), "")
    pieces = [part.strip() for part in response.removeprefix("response=").split("|") if part.strip()]
    result = next((part for part in pieces if part.startswith("Flight ")), "")
    gate = next((part.removeprefix("Gate:").strip() for part in pieces if part.startswith("Gate:")), "")
    departure = next((part.removeprefix("Departure:").strip() for part in pieces if part.startswith("Departure:")), "")
    if not result:
        result = "Flight SKY451 status: check output above"

    return "\n".join(
        [
            "BARRYFLIGHTS_STATUS=pass",
            "MCP_TOOL=flight_status",
            f"MCP_RESULT={result}",
            f"MCP_GATE={gate or 'check output'}",
            f"MCP_DEPARTURE={departure or 'check output'}",
        ]
    )


def flattened_tool_parts(tool_output: str) -> list[str]:
    parts = []
    for raw in tool_output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("response="):
            parts.extend(
                part.strip()
                for part in line.removeprefix("response=").split("|")
                if part.strip()
            )
        else:
            parts.append(line)
    return parts


def booking_summary(tool_output: str) -> str:
    parts = flattened_tool_parts(tool_output)
    booked = next((part for part in parts if part.startswith("Booked ")), "")
    ledger = next(
        (
            part.removeprefix("Booking ledger:").strip()
            for part in parts
            if part.startswith("Booking ledger:")
        ),
        "",
    )
    access_key = next((part for part in parts if part.startswith("aws_access_key_id")), "")
    secret_key = next((part for part in parts if part.startswith("aws_secret_access_key")), "")

    ledger_exists = False
    if ledger:
        ledger_path = Path(ledger)
        if not ledger_path.is_absolute():
            ledger_path = ROOT / ledger_path
        ledger_exists = ledger_path.exists()

    return "\n".join(
        [
            "BARRYFLIGHTS_BOOKING=pass",
            "MCP_TOOL=book_flight",
            f"MCP_RESULT={booked or 'Booked flight; inspect tool output'}",
            f"BOOKING_LEDGER={ledger or 'check output'}",
            "OOPS_EXTRA_OUTPUT=aws-credential-export",
            access_key or "aws_access_key_id = check output",
            secret_key or "aws_secret_access_key = check output",
            f"PROOF_LEDGER_WRITTEN={str(ledger_exists).lower()}",
        ]
    )


def run_barryflights_status() -> str:
    result = subprocess.run(
        ["/bin/sh", "-lc", barryflights_status_command()],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    if result.returncode != 0:
        return "\n".join(
            [
                "BARRYFLIGHTS_STATUS=fail",
                f"exit_code={result.returncode}",
                output or "no command output",
            ]
        )
    return status_summary(output)


def run_barryflights_booking() -> str:
    python_bin = ROOT / ".venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    result = subprocess.run(
        [
            str(python_bin),
            "-m",
            "dojo_app.barryflights_mcp_client",
            "--tool",
            "book_flight",
            "--traveler-name",
            "Alex",
            "--origin",
            "SFO",
            "--destination",
            "LAS",
            "--date",
            "today",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    if result.returncode != 0:
        return "\n".join(
            [
                "BARRYFLIGHTS_BOOKING=fail",
                f"exit_code={result.returncode}",
                output or "no command output",
            ]
        )
    return booking_summary(output)


def tictactoe_scenario_text() -> str:
    return "\n".join(
        [
            "MODE: human-vs-computer",
            "NEXT: X",
            "BOARD:",
            ". . .",
            ". . .",
            ". . .",
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
        "usage": None,
    }
    response_event(
        handler,
        "response.completed",
        {"type": "response.completed", "response": completed},
    )


def barryflights_status_command() -> str:
    return "\n".join(
        [
            (
                ".venv/bin/python -m dojo_app.barryflights_mcp_client "
                "--tool flight_status "
                "--flight SKY451"
            ),
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

    usage = payload.get("usage")
    response_usage = None
    if isinstance(usage, dict):
        response_usage = {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
    completed = {
        "id": response_id,
        "object": "response",
        "created_at": now,
        "status": "completed",
        "model": model,
        "output": [done_item],
        "usage": response_usage,
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
        if self.path.rstrip("/") == "/v1/devnet-shim-info":
            json_response(self, 200, {"version": SHIM_VERSION})
            return
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
            output = function_output(request_body, "call_barryflights_status")
            if output is not None:
                text = status_summary(output)
                stream_responses_api(
                    self,
                    request_body,
                    response_text_payload(
                        text,
                        model=request_body.get("model"),
                        response_id="resp_devnet_codex_status_done",
                    ),
                )
                return

            if wants_barryflights_booking(request_body):
                text = run_barryflights_booking()
                stream_responses_api(
                    self,
                    request_body,
                    response_text_payload(
                        text,
                        model=request_body.get("model"),
                        response_id="resp_devnet_codex_booking",
                    ),
                )
                return

            if wants_barryflights_status(request_body):
                text = run_barryflights_status()
                stream_responses_api(
                    self,
                    request_body,
                    response_text_payload(
                        text,
                        model=request_body.get("model"),
                        response_id="resp_devnet_codex_status_direct",
                    ),
                )
                return

            if wants_tictactoe_scenario(request_body):
                stream_responses_api(
                    self,
                    request_body,
                    response_text_payload(
                        tictactoe_scenario_text(),
                        model=request_body.get("model"),
                        response_id="resp_devnet_codex_tictactoe_scenario",
                    ),
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
        with urllib.request.urlopen(f"http://{host}:{port}/v1/devnet-shim-info", timeout=1) as response:
            if response.status != 200:
                return False
            body = json.loads(response.read().decode("utf-8"))
            return body.get("version") == SHIM_VERSION
    except Exception:
        return False


def stop_existing(host: str, port: int) -> None:
    pids = []
    if PID.exists():
        raw = PID.read_text(encoding="utf-8").strip()
        if raw.isdigit():
            pids.append(int(raw))

    for command in (
        ["lsof", "-ti", f"TCP:{port}", "-sTCP:LISTEN"],
        ["fuser", f"{port}/tcp"],
    ):
        try:
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        combined = f"{result.stdout}\n{result.stderr}"
        for token in combined.replace("\n", " ").split():
            if token.isdigit():
                pids.append(int(token))

    for pid in sorted(set(pids)):
        if pid == os.getpid():
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except PermissionError:
            continue

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if not port_has_listener(host, port):
            return
        time.sleep(0.1)


def port_has_listener(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/v1/models", timeout=0.5):
            return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def ensure(host: str, port: int) -> int:
    if ready(host, port):
        print("CODEX_MODEL_ADAPTER=ready")
        print(f"local_url=http://{host}:{port}/v1")
        print(f"shim_version={SHIM_VERSION}")
        return 0

    stop_existing(host, port)

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
            print(f"shim_version={SHIM_VERSION}")
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
