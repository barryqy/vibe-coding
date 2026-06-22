#!/usr/bin/env python3
from __future__ import annotations

from devnet_openai_shim import DEFAULT_HOST, DEFAULT_PORT, ensure


def main() -> int:
    return ensure(DEFAULT_HOST, DEFAULT_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
