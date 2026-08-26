"""Preview or execute one bounded PermitPulse CALL-E call."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from permitpulse.core import dumps_preview, execute, parse_request


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-authorized-project", action="store_true")
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        with args.request.open(encoding="utf-8") as handle:
            request = parse_request(json.load(handle))

        if not args.execute:
            sys.stdout.write(dumps_preview(request) + "\n")
            return 0

        if not args.confirm_authorized_project:
            raise ValueError("--execute requires --confirm-authorized-project")
        if request.support_phone not in set(args.allow):
            raise ValueError("--execute requires the exact destination in --allow")
        if os.environ.get("CALLE_LIVE_CALLS_ENABLED", "").lower() != "true":
            raise ValueError("--execute requires CALLE_LIVE_CALLS_ENABLED=true")
        if args.timeout_seconds <= 0:
            raise ValueError("--timeout-seconds must be positive")
        api_key = os.environ.get("CALLE_API_KEY")
        if not api_key:
            raise ValueError("CALLE_API_KEY is required for --execute")

        from calle import CalleClient

        with CalleClient(api_key=api_key) as client:
            payload = execute(request, client.calls, timeout_seconds=args.timeout_seconds)
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
