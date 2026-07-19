#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dojo_app.lab_output import print_status

STATE = ROOT / ".lab-state"
LOG = STATE / "devnet-openai-shim.log"
PID = STATE / "devnet-openai-shim.pid"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SHIM_VERSION = "opencode-vibe-coding-20260719-fail-closed"
MAX_UPSTREAM_ERROR_BYTES = 4096


class InvalidClientRequest(ValueError):
    pass


class ModelRouteConfigurationError(RuntimeError):
    pass


class ProviderInvalidResponseError(RuntimeError):
    pass


def output_limit() -> int:
    try:
        value = int(os.getenv("LAB_LLM_MAX_OUTPUT_TOKENS", "512"))
    except ValueError:
        value = 512
    return min(max(value, 128), 1024)


def route() -> dict[str, str]:
    return {
        "base_url": os.getenv("LLM_BASE_URL", "").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "model": os.getenv("LLM_MODEL", "gpt-5-nano"),
    }


def advertised_models() -> list[str]:
    default_model = route()["model"]
    maze_model = os.getenv("LLM_MAZE_MODEL") or default_model
    retry_model = os.getenv("MAZE_RETRY_MODEL") or maze_model
    return list(dict.fromkeys([default_model, maze_model, retry_model]))


def flatten_content(content) -> str:
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return "" if content is None else str(content)

    chunks = []
    for part in content:
        if isinstance(part, str):
            chunks.append(part)
            continue

        if not isinstance(part, dict):
            chunks.append(str(part))
            continue

        for key in ("text", "content", "input"):
            value = part.get(key)
            if isinstance(value, str) and value:
                chunks.append(value)
                break
        else:
            part_type = part.get("type", "attachment")
            chunks.append(f"[{part_type} omitted]")

    return "\n".join(chunks)


def normalize_messages(messages) -> list[dict]:
    clean = []
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        item = dict(message)
        item["content"] = flatten_content(item.get("content"))
        clean.append(item)
    return clean


def json_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    body: dict,
    extra_headers: dict[str, str] | None = None,
) -> None:
    data = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    for name, value in (extra_headers or {}).items():
        handler.send_header(name, value)
    handler.end_headers()
    handler.wfile.write(data)


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    raw_len = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_len)
    except ValueError:
        length = 0
    try:
        body = handler.rfile.read(length).decode("utf-8")
        payload = json.loads(body or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidClientRequest("request body is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise InvalidClientRequest("request body must be a JSON object")
    return payload


def call_devnet(body: dict) -> dict:
    config = route()
    if not config["base_url"] or not config["api_key"]:
        raise ModelRouteConfigurationError("LLM_BASE_URL or LLM_API_KEY is missing")

    clean_body = dict(body)
    clean_body["stream"] = False
    clean_body["messages"] = normalize_messages(clean_body.get("messages", []))
    clean_body.pop("stream_options", None)

    try:
        requested_tokens = int(clean_body.get("max_tokens", output_limit()))
        clean_body["max_tokens"] = min(max(requested_tokens, 1), output_limit())
    except (TypeError, ValueError):
        clean_body["max_tokens"] = output_limit()

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
        try:
            payload = json.loads(response.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderInvalidResponseError("upstream response is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ProviderInvalidResponseError("upstream response must be a JSON object")
        choices = payload.get("choices")
        if (
            not isinstance(choices, list)
            or not choices
            or not isinstance(choices[0], dict)
            or not isinstance(choices[0].get("message"), dict)
        ):
            raise ProviderInvalidResponseError("upstream response is missing a completion message")
        return payload


def safe_error_text(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    return "".join(char for char in text if char in "\r\n\t" or ord(char) >= 32).strip()


def safe_header_value(value, limit: int) -> str:
    text = str(value)
    clean = "".join(char if char.isalnum() or char in "-._:/" else "_" for char in text)
    return clean[:limit]


def retry_after_seconds(value) -> str:
    text = str(value or "").strip()
    if not text.isdigit():
        return ""
    return str(min(int(text), 3600))


def error_field(value, default):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value if value not in ("", None) else default
    return default


def upstream_http_error(exc: urllib.error.HTTPError) -> tuple[int, dict, dict[str, str]]:
    status = exc.code if isinstance(exc.code, int) and 400 <= exc.code <= 599 else 502
    headers = exc.headers
    reason = exc.reason
    try:
        raw = exc.read(MAX_UPSTREAM_ERROR_BYTES + 1)
    finally:
        exc.close()
    truncated = len(raw) > MAX_UPSTREAM_ERROR_BYTES
    body_text = safe_error_text(raw[:MAX_UPSTREAM_ERROR_BYTES])

    upstream_error = {}
    if body_text:
        try:
            parsed = json.loads(body_text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
            upstream_error = parsed["error"]

    default_message = body_text or str(reason or "upstream request failed")
    error = {
        "message": error_field(upstream_error.get("message"), default_message),
        "type": error_field(upstream_error.get("type"), "upstream_http_error"),
        "param": error_field(upstream_error.get("param"), None),
        "code": error_field(upstream_error.get("code"), f"upstream_http_{status}"),
        "upstream_status": status,
    }
    if body_text:
        error["upstream_body"] = body_text
    if truncated:
        error["upstream_body_truncated"] = True

    response_headers = {}
    if headers:
        request_id = (
            headers.get("x-upstream-request-id")
            or headers.get("x-request-id")
            or headers.get("apim-request-id")
        )
        cache_status = headers.get("x-llm-cache")
        retry_after = retry_after_seconds(headers.get("retry-after"))
        provider = headers.get("x-upstream-provider")
        provider_status = str(headers.get("x-upstream-status") or "").strip()
        if request_id:
            error["upstream_request_id"] = safe_header_value(request_id, 128)
        if cache_status:
            error["cache_status"] = safe_header_value(cache_status, 64)
        if provider:
            error["upstream_provider"] = safe_header_value(provider, 64)
        if provider_status.isdigit() and 400 <= int(provider_status) <= 599:
            error["provider_status"] = int(provider_status)
        if retry_after:
            error["retry_after_seconds"] = int(retry_after)
            response_headers["Retry-After"] = retry_after
    return status, {"error": error}, response_headers


def has_tool_result(body: dict) -> bool:
    for message in body.get("messages", []):
        if message.get("role") == "tool":
            return True

        content = message.get("content")
        if not isinstance(content, list):
            continue

        for part in content:
            if isinstance(part, dict) and "tool" in str(part.get("type", "")).lower():
                return True
    return False


def event_chunk(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")


def stream_response(handler: BaseHTTPRequestHandler, request_body: dict, payload: dict) -> None:
    message = payload.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or ""
    tool_calls = message.get("tool_calls") or []
    model = request_body.get("model") or route()["model"]
    response_id = payload.get("id", "chatcmpl-devnet-shim")

    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()

    if tool_calls:
        for index, tool_call in enumerate(tool_calls):
            function = tool_call.get("function") or {}
            chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": index,
                                    "id": tool_call.get("id"),
                                    "type": tool_call.get("type", "function"),
                                    "function": {
                                        "name": function.get("name", ""),
                                        "arguments": function.get("arguments", ""),
                                    },
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ],
            }
            handler.wfile.write(event_chunk(chunk))
        finish_reason = "tool_calls"
    else:
        first = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
        }
        handler.wfile.write(event_chunk(first))
        finish_reason = "stop"

    done = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
    }
    handler.wfile.write(event_chunk(done))

    stream_options = request_body.get("stream_options") or {}
    usage = payload.get("usage")
    if stream_options.get("include_usage") and isinstance(usage, dict):
        handler.wfile.write(event_chunk({"choices": [], "usage": usage}))

    handler.wfile.write(b"data: [DONE]\n\n")


class ShimHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/v1/devnet-shim-info":
            json_response(self, 200, {"version": SHIM_VERSION})
            return
        if self.path.rstrip("/") == "/v1/models":
            models = [
                {"id": model, "object": "model"}
                for model in advertised_models()
            ]
            json_response(self, 200, {"object": "list", "data": models})
            return
        json_response(self, 404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/v1/chat/completions":
            json_response(self, 404, {"error": {"message": "not found"}})
            return

        try:
            request_body = read_json(self)
        except InvalidClientRequest:
            json_response(
                self,
                400,
                {
                    "error": {
                        "message": "request body must be valid JSON object",
                        "type": "invalid_request_error",
                        "code": "invalid_json",
                    }
                },
            )
            return

        try:
            payload = call_devnet(request_body)
        except urllib.error.HTTPError as exc:
            status, error_body, response_headers = upstream_http_error(exc)
            error = error_body["error"]
            print(
                " ".join(
                    [
                        "OPENCODE_UPSTREAM_HTTP_ERROR",
                        f"status={status}",
                        f"tool_result={'yes' if has_tool_result(request_body) else 'no'}",
                        f"stream={'yes' if request_body.get('stream') else 'no'}",
                        f"request_id={error.get('upstream_request_id', 'unknown')}",
                        f"cache={error.get('cache_status', 'unknown')}",
                    ]
                ),
                flush=True,
            )
            json_response(self, status, error_body, response_headers)
            return
        except TimeoutError:
            json_response(
                self,
                504,
                {
                    "error": {
                        "message": "the lab model request timed out",
                        "type": "provider_timeout_error",
                        "code": "upstream_timeout",
                    }
                },
            )
            return
        except (urllib.error.URLError, OSError):
            json_response(
                self,
                502,
                {
                    "error": {
                        "message": "the lab model endpoint is unavailable",
                        "type": "provider_connection_error",
                        "code": "upstream_connection_error",
                    }
                },
            )
            return
        except ProviderInvalidResponseError:
            json_response(
                self,
                502,
                {
                    "error": {
                        "message": "the lab model returned an invalid response",
                        "type": "provider_invalid_response",
                        "code": "upstream_invalid_response",
                    }
                },
            )
            return
        except ModelRouteConfigurationError:
            json_response(
                self,
                503,
                {
                    "error": {
                        "message": "the lab model route is not configured",
                        "type": "configuration_error",
                        "code": "upstream_not_configured",
                    }
                },
            )
            return

        if request_body.get("stream"):
            stream_response(self, request_body, payload)
            return

        json_response(self, 200, payload)


def ready(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/v1/devnet-shim-info", timeout=1) as response:
            if response.status != 200:
                return False
            body = json.loads(response.read().decode("utf-8"))
            return body.get("version") == SHIM_VERSION
    except Exception:
        return False


def port_has_listener(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/v1/models", timeout=0.5):
            return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def stop_existing(host: str, port: int) -> None:
    pids = []
    if PID.exists():
        raw = PID.read_text(encoding="utf-8").strip()
        if raw.isdigit():
            pids.append(int(raw))

    for command in (
        ["ss", "-ltnp"],
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
        if command[:2] == ["ss", "-ltnp"]:
            for match in re.finditer(rf":{port}\b.*?pid=(\d+)", combined):
                pids.append(int(match.group(1)))
            continue
        for token in combined.replace("\n", " ").split():
            if token.isdigit():
                pids.append(int(token))

    for pid in sorted(set(pids)):
        if pid == os.getpid():
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            continue

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if not port_has_listener(host, port):
            return
        time.sleep(0.1)


def ensure(host: str, port: int) -> int:
    if ready(host, port):
        print_status("OPENCODE_MODEL_ADAPTER=ready")
        print_status(f"local_url=http://{host}:{port}/v1")
        print_status(f"shim_version={SHIM_VERSION}")
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
            print_status("OPENCODE_MODEL_ADAPTER=ready")
            print_status(f"local_url=http://{host}:{port}/v1")
            print_status(f"shim_version={SHIM_VERSION}")
            return 0
        time.sleep(0.25)

    print_status("OPENCODE_MODEL_ADAPTER=failed")
    print_status(f"log={LOG.relative_to(ROOT)}")
    return 1


def serve(host: str, port: int) -> int:
    config = route()
    if not config["base_url"] or not config["api_key"]:
        print("OPENCODE_MODEL_ADAPTER=missing-env", file=sys.stderr)
        return 1

    server = ThreadingHTTPServer((host, port), ShimHandler)
    print(f"OPENCODE_MODEL_ADAPTER=serving http://{host}:{port}/v1", flush=True)
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
