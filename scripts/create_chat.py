import argparse
import json
import sys

import httpx


API_URL = "http://localhost:8000/v1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a chat and print chat_id + thread_id.")
    parser.add_argument("token", help="Bearer token for the API")
    parser.add_argument("--title", default="Deep Research Chat", help="Chat title")
    parser.add_argument("--deep-research", action="store_true", help="Enable deep research on the chat")
    args = parser.parse_args()

    headers = {"Authorization": f"Bearer {args.token}", "Content-Type": "application/json"}
    payload = {
        "title": args.title,
        "deep_research_enabled": args.deep_research,
    }

    try:
        resp = httpx.post(f"{API_URL}/chats", headers=headers, json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"Failed to create chat: {exc}", file=sys.stderr)
        if hasattr(exc, "response") and exc.response is not None:
            try:
                print(exc.response.text, file=sys.stderr)
            except Exception:
                pass
        return 1

    chat_id = data.get("id")
    thread_id = data.get("thread_id")


    print(json.dumps({
        "chat_id": chat_id,
        "thread_id": thread_id,
        "x-auth-token": args.token
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
