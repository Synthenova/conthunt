from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_search_completed_emitted_for_success_and_failure_paths() -> None:
    content = _read("backend/app/api/v1/search.py")
    assert 'event="search_completed"' in content
    assert "success=True" in content
    assert "success=False" in content


def test_platform_payload_contract_keys_present() -> None:
    payloads = _read("backend/app/services/telemetry_payloads.py")
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


def test_frontend_tracking_helpers_are_wired_to_feature_flows() -> None:
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
        content = _read(rel_path)
        for token in required_tokens:
            assert token in content


def test_docs_include_standardized_contract_fields() -> None:
    content = _read("docs/telemetry-contract.md")
    required = [
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
    ]
    for token in required:
        assert token in content
