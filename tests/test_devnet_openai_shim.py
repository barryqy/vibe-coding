from __future__ import annotations

import http.client
import io
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from scripts import devnet_openai_shim


ERRORS = {
    400: {
        "message": "tool result is malformed",
        "type": "invalid_request_error",
        "param": "messages",
        "code": "bad_tool_result",
    },
    429: {
        "message": "request rate limit exceeded",
        "type": "rate_limit_error",
        "param": None,
        "code": "rate_limit_exceeded",
    },
    502: {
        "message": "model deployment is unavailable",
        "type": "upstream_error",
        "param": None,
        "code": "bad_gateway",
    },
}


class UpstreamState:
    def __init__(self):
        self.status = 400
        self.success_body = b"not-json"
        self.requests: list[dict] = []


def upstream_handler(state: UpstreamState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            return

        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            state.requests.append(json.loads(body.decode("utf-8")))

            if state.status == 200:
                payload = state.success_body
            else:
                payload = json.dumps({"error": ERRORS[state.status]}).encode("utf-8")
            self.send_response(state.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Request-ID", f"request-{state.status}")
            self.send_header("X-LLM-Cache", "BYPASS")
            self.send_header("X-Upstream-Provider", "azure")
            self.send_header("X-Upstream-Status", str(state.status))
            if state.status == 429:
                self.send_header("Retry-After", "7")
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def start_server(server: ThreadingHTTPServer) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


class DevnetOpenAIShimTests(unittest.TestCase):
    def setUp(self):
        self.upstream_state = UpstreamState()
        self.upstream = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            upstream_handler(self.upstream_state),
        )
        self.upstream_thread = start_server(self.upstream)

        self.shim = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            devnet_openai_shim.ShimHandler,
        )
        self.shim_thread = start_server(self.shim)
        self.url = f"http://127.0.0.1:{self.shim.server_port}/v1/chat/completions"

        env = {
            "LLM_BASE_URL": f"http://127.0.0.1:{self.upstream.server_port}/v1",
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "gpt-5-nano",
        }
        self.env = patch.dict(os.environ, env)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.shim.shutdown()
        self.shim.server_close()
        self.shim_thread.join(3)
        self.upstream.shutdown()
        self.upstream.server_close()
        self.upstream_thread.join(3)

    def post_tool_result(self, stream: bool) -> tuple[int, str, dict, str]:
        body = {
            "model": "gpt-5-nano",
            "stream": stream,
            "messages": [
                {"role": "user", "content": "Update the Maze."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "tool-1",
                            "type": "function",
                            "function": {"name": "edit", "arguments": "{}"},
                        }
                    ],
                },
                {"role": "tool", "tool_call_id": "tool-1", "content": "edited"},
            ],
        }
        request = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as exc:
            response = exc
        else:
            self.fail("the shim returned success for an upstream HTTP error")

        content_type = response.headers.get("Content-Type", "")
        retry_after = response.headers.get("Retry-After", "")
        code = response.code
        try:
            payload = json.loads(response.read().decode("utf-8"))
        finally:
            response.close()
        return code, content_type, payload, retry_after

    def test_models_include_task_and_retry_overrides(self):
        env = {
            "LLM_MAZE_MODEL": "gpt-5-cache",
            "MAZE_RETRY_MODEL": "gpt-5-nano-cache",
        }
        url = f"http://127.0.0.1:{self.shim.server_port}/v1/models"
        with (
            patch.dict(os.environ, env),
            urllib.request.urlopen(url, timeout=3) as response,
        ):
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(
            [item["id"] for item in payload["data"]],
            ["gpt-5-nano", "gpt-5-cache", "gpt-5-nano-cache"],
        )

    def test_log_metadata_cannot_add_lines(self):
        self.assertEqual(
            devnet_openai_shim.safe_header_value("request-1\nforged=yes", 128),
            "request-1_forged_yes",
        )

    def assert_errors_stay_fail_closed(self, stream: bool) -> None:
        for status, expected in ERRORS.items():
            with self.subTest(status=status, stream=stream):
                self.upstream_state.status = status
                code, content_type, payload, retry_after = self.post_tool_result(stream)

                self.assertEqual(code, status)
                self.assertEqual(content_type, "application/json")
                self.assertNotIn("choices", payload)
                error = payload["error"]
                self.assertEqual(error["message"], expected["message"])
                self.assertEqual(error["type"], expected["type"])
                self.assertEqual(error["param"], expected["param"])
                self.assertEqual(error["code"], expected["code"])
                self.assertEqual(error["upstream_status"], status)
                self.assertEqual(error["upstream_request_id"], f"request-{status}")
                self.assertEqual(error["cache_status"], "BYPASS")
                self.assertEqual(error["upstream_provider"], "azure")
                self.assertEqual(error["provider_status"], status)
                self.assertIn(expected["message"], error["upstream_body"])
                self.assertNotIn("Done. Please run", json.dumps(payload))
                self.assertFalse(self.upstream_state.requests[-1]["stream"])
                if status == 429:
                    self.assertEqual(retry_after, "7")
                    self.assertEqual(error["retry_after_seconds"], 7)
                else:
                    self.assertEqual(retry_after, "")

    def test_retry_after_rejects_non_numeric_and_caps_large_values(self):
        self.assertEqual(devnet_openai_shim.retry_after_seconds("soon"), "")
        self.assertEqual(devnet_openai_shim.retry_after_seconds("99999"), "3600")

    def test_connection_failure_is_reported_as_a_provider_error(self):
        with patch.dict(
            os.environ,
            {"LLM_BASE_URL": "http://127.0.0.1:1/v1", "LLM_API_KEY": "test-key"},
        ):
            request = urllib.request.Request(
                self.url,
                data=json.dumps({"messages": [{"role": "user", "content": "hi"}]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=3)

        response = caught.exception
        try:
            payload = json.loads(response.read().decode("utf-8"))
        finally:
            response.close()
        self.assertEqual(response.code, 502)
        self.assertEqual(payload["error"]["type"], "provider_connection_error")
        self.assertNotIn("127.0.0.1", json.dumps(payload))

    def test_remote_disconnect_is_reported_as_a_provider_error(self):
        body = {"messages": [{"role": "user", "content": "hi"}]}
        request = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with (
            patch.object(
                devnet_openai_shim,
                "call_devnet",
                side_effect=http.client.RemoteDisconnected("closed"),
            ),
            self.assertRaises(urllib.error.HTTPError) as caught,
        ):
            urllib.request.urlopen(request, timeout=3)

        response = caught.exception
        try:
            payload = json.loads(response.read().decode("utf-8"))
        finally:
            response.close()
        self.assertEqual(response.code, 502)
        self.assertEqual(payload["error"]["type"], "provider_connection_error")
        self.assertEqual(payload["error"]["code"], "upstream_connection_error")
        self.assertNotIn("closed", json.dumps(payload))

    def test_provider_timeout_stays_fail_closed_for_streaming_and_nonstreaming(self):
        for stream in (False, True):
            with self.subTest(stream=stream):
                body = {
                    "stream": stream,
                    "messages": [{"role": "user", "content": "hi"}],
                }
                request = urllib.request.Request(
                    self.url,
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with (
                    patch.object(devnet_openai_shim, "call_devnet", side_effect=TimeoutError),
                    self.assertRaises(urllib.error.HTTPError) as caught,
                ):
                    urllib.request.urlopen(request, timeout=3)

                response = caught.exception
                try:
                    payload = json.loads(response.read().decode("utf-8"))
                finally:
                    response.close()
                self.assertEqual(response.code, 504)
                self.assertEqual(payload["error"]["type"], "provider_timeout_error")
                self.assertEqual(payload["error"]["code"], "upstream_timeout")
                self.assertNotIn("choices", payload)

    def test_invalid_upstream_success_is_a_provider_error(self):
        self.upstream_state.status = 200
        body = {"stream": True, "messages": [{"role": "user", "content": "hi"}]}
        request = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=3)

        response = caught.exception
        try:
            payload = json.loads(response.read().decode("utf-8"))
        finally:
            response.close()
        self.assertEqual(response.code, 502)
        self.assertEqual(payload["error"]["type"], "provider_invalid_response")
        self.assertEqual(payload["error"]["code"], "upstream_invalid_response")
        self.assertNotIn("choices", payload)

    def test_incomplete_upstream_success_stays_fail_closed(self):
        self.upstream_state.status = 200
        for upstream_payload in ({}, {"choices": []}, {"error": {"message": "failed"}}):
            for stream in (False, True):
                with self.subTest(upstream_payload=upstream_payload, stream=stream):
                    self.upstream_state.success_body = json.dumps(upstream_payload).encode()
                    body = {
                        "stream": stream,
                        "messages": [{"role": "user", "content": "hi"}],
                    }
                    request = urllib.request.Request(
                        self.url,
                        data=json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with self.assertRaises(urllib.error.HTTPError) as caught:
                        urllib.request.urlopen(request, timeout=3)

                    response = caught.exception
                    try:
                        payload = json.loads(response.read().decode("utf-8"))
                    finally:
                        response.close()
                    self.assertEqual(response.code, 502)
                    self.assertEqual(payload["error"]["type"], "provider_invalid_response")
                    self.assertNotIn("choices", payload)

    def test_post_tool_400_429_and_502_stay_errors_for_nonstreaming_requests(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assert_errors_stay_fail_closed(stream=False)

        self.assertIn(
            "status=429 tool_result=yes stream=no request_id=request-429 cache=BYPASS",
            output.getvalue(),
        )

    def test_post_tool_400_429_and_502_stay_errors_for_streaming_requests(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assert_errors_stay_fail_closed(stream=True)

        self.assertIn(
            "status=502 tool_result=yes stream=yes request_id=request-502 cache=BYPASS",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
