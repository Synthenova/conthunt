"""Send a signed Dodo-style webhook to the local/backend endpoint."""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from standardwebhooks.webhooks import Webhook


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload_file", help="Path to JSON payload file")
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8000/webhooks/dodo",
        help="Webhook endpoint URL",
    )
    parser.add_argument(
        "--webhook-id",
        default=None,
        help="Optional explicit webhook id",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="HTTP timeout in seconds",
    )
    args = parser.parse_args()

    env_local = Path(__file__).resolve().parents[1] / ".env.local"
    _load_env_file(env_local)

    secret = os.getenv("DODO_WEBHOOK_SECRET")
    if not secret:
        print("Missing DODO_WEBHOOK_SECRET", file=sys.stderr)
        return 1

    payload_path = Path(args.payload_file)
    payload = json.loads(payload_path.read_text())
    body = json.dumps(payload, separators=(",", ":"))

    webhook_id = args.webhook_id or f"msg_{uuid.uuid4().hex}"
    timestamp = datetime.now(timezone.utc)
    signer = Webhook(secret)
    signature = signer.sign(webhook_id, timestamp, body)

    headers = {
        "content-type": "application/json",
        "webhook-id": webhook_id,
        "webhook-timestamp": str(int(timestamp.timestamp())),
        "webhook-signature": signature,
    }

    response = httpx.post(args.endpoint, content=body, headers=headers, timeout=args.timeout)
    print(json.dumps(
        {
            "status_code": response.status_code,
            "response_text": response.text,
            "webhook_id": webhook_id,
            "endpoint": args.endpoint,
            "payload_file": str(payload_path),
        },
        indent=2,
    ))
    return 0 if response.is_success else 2


if __name__ == "__main__":
    raise SystemExit(main())
