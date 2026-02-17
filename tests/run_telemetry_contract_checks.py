#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def check_search_completed_paths() -> None:
    content = read("backend/app/api/v1/search.py")
    assert 'event="search_completed"' in content
    assert "success=True" in content
    assert "success=False" in content


def check_platform_payload_contract_keys() -> None:
    payloads = read("backend/app/services/telemetry_payloads.py")
    for key in [
        "search_id",
        "platform",
        "success",
        "duration_ms",
        "result_count",
        "http_status",
        "error_category",
        "source",
    ]:
        assert f'"{key}"' in payloads


def check_frontend_wiring() -> None:
    checks = {
        "frontend/src/app/app/searches/[id]/page.tsx": [
            "trackSearchNoResults(",
            "trackSearchResultsPageViewed(",
            "trackUserFirstSearch(",
        ],
        "frontend/src/components/dashboard/HomeSearchBox.tsx": [
            "trackDeepSearchToggled(",
        ],
        "frontend/src/components/search/SelectableMediaCard.tsx": [
            "trackSearchResultClicked(",
        ],
        "frontend/src/app/providers.tsx": [
            "trackSessionStarted(",
            "trackSessionDurationMs(",
        ],
        "frontend/src/app/app/boards/page.tsx": [
            "trackUserFirstBoardCreated(",
        ],
    }
    for rel_path, required_tokens in checks.items():
        content = read(rel_path)
        for token in required_tokens:
            assert token in content


def check_docs() -> None:
    content = read("docs/telemetry-contract.md")
    for token in [
        "`source`",
        "`success`",
        "`error_category`",
        "`error_type`",
        "`http_status`",
        "`search_id`",
        "`board_id`",
        "`product_id`",
        "`platform`",
        "`plan`",
        "`role`",
    ]:
        assert token in content


def main() -> int:
    checks = [
        check_search_completed_paths,
        check_platform_payload_contract_keys,
        check_frontend_wiring,
        check_docs,
    ]
    for fn in checks:
        fn()
        print(f"[ok] {fn.__name__}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        raise SystemExit(1)
