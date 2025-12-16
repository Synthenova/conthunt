# Conthunt Backend - 12Labs Video Analysis Integration

**Date:** 2025-12-15

## Overview

Integrated TwelveLabs AI video analysis API to enable AI-powered content insights for videos. Analysis results (hooks, CTAs, topics, summaries) are cached globally - first request triggers upload/index/analyze workflow, subsequent requests return instantly from cache.

---

## Completed Work

### 1. Database Layer
- **Migration**: `backend/.sqls/003_twelvelabs.sql`
    - `twelvelabs_indexes`: Track 12Labs indexes we create
    - `twelvelabs_assets`: Link content_items to 12Labs assets (upload + index status)
    - `video_analyses`: Global cache for analysis results (shared across all users)
- **No RLS**: Analyses are shared globally, not per-user

### 2. Configuration
- **Settings**: `TWELVELABS_API_KEY`, `TWELVELABS_DEFAULT_INDEX_NAME`, timeouts
- **Environment**: Added to `.env.example`

### 3. Service Client
- `backend/app/services/twelvelabs_client.py`
    - `TwelvelabsClient` class wrapping SDK
    - Methods: `upload_asset`, `wait_for_asset_ready`, `index_asset`, `wait_for_indexing_ready`, `analyze_video`
    - Returns raw responses for GCS archiving

### 4. Database Queries
- `backend/app/db/queries/twelvelabs.py` (modularized)
    - `get_or_create_twelvelabs_index`
    - `upsert_twelvelabs_asset`, `update_twelvelabs_asset_status`
    - `get_video_analysis_by_content_item`, `insert_video_analysis`
    - `get_content_item_by_id`

### 5. API Endpoint
- **Router**: `backend/app/api/v1/twelvelabs.py`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/video-analysis/{content_item_id}` | Async analysis. Returns status="processing" immediately. |

### 6. Background Processing
- `backend/app/services/twelvelabs_processing.py`
    - Handles the long-running Upload -> Index -> Analyze workflow
    - Triggered via FastAPI `BackgroundTasks`
    - Updates DB with intermediate statuses (`processing`, `failed`, `ready`)

### 7. Raw Response Archiving
- Full raw responses from upload/index/analyze archived to GCS
- URI stored in DB: `upload_raw_gcs_uri`, `index_raw_gcs_uri`, `raw_gcs_uri`

### 8. Code Modularization
- Split `queries.py` (1014 lines) into:
    - `queries/search.py`
    - `queries/boards.py`
    - `queries/twelvelabs.py`
- Backwards compatible via `__init__.py` re-exports

---

## Analysis Response Schema

```json
{
  "id": "uuid",
  "content_item_id": "uuid",
  "status": "processing | completed | failed",
  "analysis": {
    "hook": "Opening attention-grabber",
    "call_to_action": "Subscribe, like, follow requests",
    "on_screen_texts": ["Text overlay 1", "Text overlay 2"],
    "key_topics": ["Topic 1", "Topic 2"],
    "summary": "2-3 sentence summary",
    "hashtags": ["#tag1", "#tag2"]
  },
  "cached": true
}
```

---

## Files Created/Modified

```
backend/
├── .sqls/
│   └── 003_twelvelabs.sql         # [NEW] DB migration
├── app/
│   ├── core/
│   │   └── settings.py            # [MODIFIED] Added 12Labs config
│   ├── services/
│   │   ├── __init__.py            # [NEW]
│   │   ├── twelvelabs_client.py   # [NEW] SDK wrapper
│   │   └── twelvelabs_processing.py # [NEW] Background task service
│   ├── schemas/
│   │   └── twelvelabs.py          # [NEW] Pydantic schemas (with status)
│   ├── db/
│   │   └── queries/               # [NEW] Modular package
│   │       ├── __init__.py
│   │       ├── search.py
│   │       ├── boards.py
│   │       └── twelvelabs.py
│   └── api/v1/
│       ├── router.py              # [MODIFIED] Added 12Labs router
│       └── twelvelabs.py          # [NEW] Async API endpoint
└── .env.example                   # [MODIFIED] Added 12Labs vars
```