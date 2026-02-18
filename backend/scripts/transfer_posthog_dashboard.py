#!/usr/bin/env python3
"""
PostHog Dashboard Migration Script (fixed)
- Creates target dashboard (metadata only)
- Copies actions (optional)
- Copies insights AND attaches them to the new dashboard using `dashboards: [id]`
"""

import argparse
import json
import sys
import requests
from typing import Dict, Any, Optional, List, Set


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def export_insight(host: str, api_key: str, project_id: str, insight_id: int) -> Optional[Dict[str, Any]]:
    url = f"{host}/api/projects/{project_id}/insights/{insight_id}/"
    try:
        r = requests.get(url, headers=_headers(api_key))
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to export insight {insight_id}: {e}")
        return None


def export_action(host: str, api_key: str, project_id: str, action_id: int) -> Optional[Dict[str, Any]]:
    url = f"{host}/api/projects/{project_id}/actions/{action_id}/"
    try:
        r = requests.get(url, headers=_headers(api_key))
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to export action {action_id}: {e}")
        return None


def import_action(host: str, api_key: str, project_id: str, action_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = f"{host}/api/projects/{project_id}/actions/"
    payload = {
        "name": action_data.get("name"),
        "description": action_data.get("description", ""),
        "tags": action_data.get("tags", []),
        "steps": action_data.get("steps", []),
        "post_to_slack": False,
    }
    try:
        r = requests.post(url, headers=_headers(api_key), json=payload)
        r.raise_for_status()
        new_action = r.json()
        print(f"   ✅ Copied action: {new_action.get('name')}")
        return new_action
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to import action: {e}")
        if getattr(e, "response", None) is not None:
            print(f"   Error: {e.response.text}")
        return None


def check_insight_dependencies(insight_data: Dict[str, Any]) -> Dict[str, Set]:
    dependencies = {"actions": set(), "cohorts": set(), "feature_flags": set()}

    filters = insight_data.get("filters", {}) or {}
    query = insight_data.get("query", {}) or {}

    # Actions (legacy)
    if "actions" in filters:
        for action in filters.get("actions", []):
            if isinstance(action, dict) and "id" in action:
                dependencies["actions"].add(action["id"])

    # Actions (query-based)
    if "series" in query:
        for s in query.get("series", []):
            if isinstance(s, dict) and s.get("kind") == "ActionsNode" and "id" in s:
                dependencies["actions"].add(s["id"])

    def extract_cohorts_from_properties(props):
        if not props:
            return
        if isinstance(props, list):
            for p in props:
                if isinstance(p, dict):
                    if p.get("type") == "cohort" and "value" in p:
                        dependencies["cohorts"].add(p["value"])
                    if "values" in p:
                        extract_cohorts_from_properties(p["values"])
        elif isinstance(props, dict):
            if props.get("type") == "cohort" and "value" in props:
                dependencies["cohorts"].add(props["value"])

    extract_cohorts_from_properties(filters.get("properties"))
    extract_cohorts_from_properties(query.get("properties"))
    if isinstance(query.get("source"), dict):
        extract_cohorts_from_properties(query["source"].get("properties"))

    if "feature_flag" in filters:
        dependencies["feature_flags"].add(filters["feature_flag"])

    return dependencies


def extract_insight_id(insight_value: Any) -> Optional[int]:
    if insight_value is None:
        return None
    if isinstance(insight_value, int):
        return insight_value
    if isinstance(insight_value, dict):
        return insight_value.get("id")
    # short_id string can't be used directly here
    return None


def export_dashboard(host: str, api_key: str, project_id: str, dashboard_id: int) -> Optional[Dict[str, Any]]:
    url = f"{host}/api/projects/{project_id}/dashboards/{dashboard_id}/"
    print(f"📥 Exporting dashboard {dashboard_id} from project {project_id}...")
    try:
        r = requests.get(url, headers=_headers(api_key))
        r.raise_for_status()
        data = r.json()
        print(f"✅ Successfully exported dashboard: {data.get('name')}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to export dashboard: {e}")
        if getattr(e, "response", None) is not None:
            print(f"Error: {e.response.text}")
        return None


def create_dashboard(host: str, api_key: str, project_id: str, dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create dashboard metadata only.
    Then we attach insights via insight create with dashboards=[new_dashboard_id].
    """
    url = f"{host}/api/projects/{project_id}/dashboards/"
    payload = {
        "name": dashboard_data.get("name"),
        "description": dashboard_data.get("description", "") or "",
        "tags": dashboard_data.get("tags", []) or [],
        "filters": dashboard_data.get("filters", {}) or {},
    }

    print(f"📤 Creating dashboard in target project {project_id}...")
    try:
        r = requests.post(url, headers=_headers(api_key), json=payload)
        r.raise_for_status()
        new_dashboard = r.json()
        print(f"✅ Dashboard created: {new_dashboard.get('name')} (ID: {new_dashboard.get('id')})")
        return new_dashboard
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create dashboard: {e}")
        if getattr(e, "response", None) is not None:
            print(f"Error: {e.response.text}")
        return None


def import_insight(
    host: str,
    api_key: str,
    project_id: str,
    insight_data: Dict[str, Any],
    action_id_mapping: Optional[Dict[int, int]] = None,
    attach_to_dashboard_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    url = f"{host}/api/projects/{project_id}/insights/"

    # IMPORTANT:
    # Insights create supports `dashboards` on request. We'll set it to [attach_to_dashboard_id].
    # See request parameters in PostHog Insights API reference. (dashboards: array) :contentReference[oaicite:4]{index=4}
    EXCLUDE_FIELDS = {
        "id",
        "short_id",
        "created_at",
        "updated_at",
        "created_by",
        "last_modified_at",
        "last_modified_by",
        "result",
        "last_refresh",
        "is_sample",
        "effective_restriction_level",
        "privilege_level",
        "dive_dashboard",
        "is_cached",
        "filters_hash",
        "dashboard_tiles",
        "order",  # we'll allow new order
        # NOTE: we do NOT exclude "dashboards" anymore; we control it explicitly below
    }

    payload = {k: v for k, v in insight_data.items() if k not in EXCLUDE_FIELDS}

    if not payload.get("name") and insight_data.get("derived_name"):
        payload["name"] = insight_data["derived_name"]

    # Prefer query-based insights; keep filters if that's all you have.
    # The Insights create endpoint documents `query` as the primary config input. :contentReference[oaicite:5]{index=5}
    # (Many PostHog instances still return `filters` too, and PostHog often accepts it, but query is safer.)
    if insight_data.get("query"):
        payload["query"] = json.loads(json.dumps(insight_data["query"]))
    elif insight_data.get("filters"):
        payload["filters"] = json.loads(json.dumps(insight_data["filters"]))

    # Attach to the newly created dashboard
    if attach_to_dashboard_id is not None:
        payload["dashboards"] = [attach_to_dashboard_id]

    # Remap action IDs inside filters/query
    if action_id_mapping:
        if payload.get("filters"):
            f = payload["filters"]
            if isinstance(f, dict) and "actions" in f:
                for a in f.get("actions", []):
                    if isinstance(a, dict) and "id" in a and a["id"] in action_id_mapping:
                        a["id"] = action_id_mapping[a["id"]]

        if payload.get("query"):
            q = payload["query"]
            if isinstance(q, dict) and "series" in q:
                for s in q.get("series", []):
                    if isinstance(s, dict) and s.get("kind") == "ActionsNode" and "id" in s:
                        if s["id"] in action_id_mapping:
                            s["id"] = action_id_mapping[s["id"]]

            if isinstance(q, dict) and isinstance(q.get("source"), dict):
                src = q["source"]
                if "series" in src:
                    for s in src.get("series", []):
                        if isinstance(s, dict) and s.get("kind") == "ActionsNode" and "id" in s:
                            if s["id"] in action_id_mapping:
                                s["id"] = action_id_mapping[s["id"]]

    try:
        r = requests.post(url, headers=_headers(api_key), json=payload)
        r.raise_for_status()
        new_insight = r.json()
        print(f"   ✅ Copied insight: {new_insight.get('name') or new_insight.get('derived_name')}")
        return new_insight
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to import insight: {e}")
        if getattr(e, "response", None) is not None:
            print(f"   Error: {e.response.text}")
            print(f"   Payload sample: {json.dumps(payload)[:500]}...")
        return None


def list_dashboards(host: str, api_key: str, project_id: str) -> List[Dict[str, Any]]:
    url = f"{host}/api/projects/{project_id}/dashboards/"
    dashboards: List[Dict[str, Any]] = []
    next_url = url
    print(f"📋 Listing dashboards from project {project_id}...")
    while next_url:
        try:
            r = requests.get(next_url, headers=_headers(api_key))
            r.raise_for_status()
            data = r.json()
            dashboards.extend(data.get("results", []))
            next_url = data.get("next")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to list dashboards: {e}")
            if getattr(e, "response", None) is not None:
                print(f"Error: {e.response.text}")
            return []
    print(f"✅ Found {len(dashboards)} dashboards.")
    return dashboards


def delete_dashboard(host: str, api_key: str, project_id: str, dashboard_id: int) -> bool:
    url = f"{host}/api/projects/{project_id}/dashboards/{dashboard_id}/"
    try:
        r = requests.patch(url, headers=_headers(api_key), json={"deleted": True})
        if r.status_code in (200, 204):
            print(f"✅ Successfully deleted dashboard {dashboard_id}")
            return True
        print(f"❌ Failed to delete dashboard {dashboard_id}: {r.status_code} {r.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to delete dashboard {dashboard_id}: {e}")
        return False


def transfer_dashboard_with_insights(
    host: str,
    source_key: str,
    target_key: str,
    source_project: str,
    target_project: str,
    dashboard_id: int,
    copy_actions: bool = True,
) -> bool:
    # 1) Export dashboard
    dashboard_data = export_dashboard(host, source_key, source_project, dashboard_id)
    if not dashboard_data:
        return False

    # 2) Create target dashboard first (metadata only)
    new_dashboard = create_dashboard(host, target_key, target_project, dashboard_data)
    if not new_dashboard or not new_dashboard.get("id"):
        return False
    new_dashboard_id = int(new_dashboard["id"])

    # 3) Extract insight IDs from tiles (source dashboard)
    insight_ids: Set[int] = set()
    for tile in dashboard_data.get("tiles", []) or []:
        insight_id = extract_insight_id(tile.get("insight"))
        if insight_id:
            insight_ids.add(insight_id)

    print(f"📊 Found {len(insight_ids)} insights to copy...")

    # 4) Export insights and collect dependencies
    all_actions: Set[int] = set()
    all_cohorts: Set[int] = set()
    all_feature_flags: Set[Any] = set()
    insight_data_map: Dict[int, Dict[str, Any]] = {}

    for iid in insight_ids:
        data = export_insight(host, source_key, source_project, iid)
        if data:
            insight_data_map[iid] = data
            deps = check_insight_dependencies(data)
            all_actions.update(deps["actions"])
            all_cohorts.update(deps["cohorts"])
            all_feature_flags.update(deps["feature_flags"])

    if all_actions or all_cohorts or all_feature_flags:
        print("\n⚠️  Dependencies detected:")
        if all_actions:
            print(f"   📋 Actions: {len(all_actions)} - {list(all_actions)[:5]}{' ...' if len(all_actions) > 5 else ''}")
        if all_cohorts:
            print(f"   👥 Cohorts: {len(all_cohorts)} - {list(all_cohorts)[:5]}{' ...' if len(all_cohorts) > 5 else ''}")
            print("      ⚠️  WARNING: Cohorts cannot be automatically copied. Insights may not work correctly.")
        if all_feature_flags:
            print(f"   🚩 Feature Flags: {len(all_feature_flags)}")
            print("      ⚠️  WARNING: Feature flags cannot be automatically copied. Insights may not work correctly.")

    # 5) Copy actions
    action_id_mapping: Dict[int, int] = {}
    if copy_actions and all_actions:
        print(f"\n📋 Copying {len(all_actions)} actions...")
        for old_action_id in all_actions:
            action_data = export_action(host, source_key, source_project, old_action_id)
            if not action_data:
                print(f"   ⚠️ Skipping action {old_action_id}")
                continue
            new_action = import_action(host, target_key, target_project, action_data)
            if new_action and "id" in new_action:
                action_id_mapping[old_action_id] = int(new_action["id"])
        print(f"✅ Successfully copied {len(action_id_mapping)}/{len(all_actions)} actions")

    # 6) Copy insights AND attach to new dashboard
    print(f"\n📊 Copying insights into dashboard {new_dashboard_id}...")
    ok = 0
    for _, insight_data in insight_data_map.items():
        new_insight = import_insight(
            host,
            target_key,
            target_project,
            insight_data,
            action_id_mapping=action_id_mapping,
            attach_to_dashboard_id=new_dashboard_id,
        )
        if new_insight:
            ok += 1

    print(f"✅ Copied {ok}/{len(insight_data_map)} insights onto the dashboard.")
    print(f"🔗 Dashboard URL: {host}/project/{target_project}/dashboard/{new_dashboard_id}")
    return ok > 0


def main():
    p = argparse.ArgumentParser(description="Transfer PostHog dashboards from one project to another.")
    p.add_argument("--source-key", required=True, help="Personal API Key for the Source Project")
    p.add_argument("--target-key", required=True, help="Personal API Key for the Target Project")
    p.add_argument("--source-project", required=True, help="Source Project ID")
    p.add_argument("--target-project", required=True, help="Target Project ID")
    p.add_argument("--dashboard", type=int, help="ID of the dashboard to transfer (optional if --all is used)")
    p.add_argument("--all", action="store_true", help="Transfer ALL dashboards from source project")
    p.add_argument("--host", default="https://us.posthog.com", help="PostHog Host (default: https://us.posthog.com)")
    p.add_argument("--skip-actions", action="store_true", help="Skip copying actions (faster but may break funnels)")
    args = p.parse_args()

    if not args.dashboard and not args.all:
        print("❌ Error: You must specify either --dashboard <ID> or --all")
        sys.exit(1)

    dashboards_to_transfer: List[Dict[str, Any]] = []
    if args.dashboard:
        dashboards_to_transfer.append({"id": args.dashboard, "name": f"Dashboard {args.dashboard}"})
    else:
        dashboards_to_transfer = list_dashboards(args.host, args.source_key, args.source_project)

    if not dashboards_to_transfer:
        print("⚠️ No dashboards to transfer.")
        sys.exit(0)

    print(f"\nReady to transfer {len(dashboards_to_transfer)} dashboard(s) from project {args.source_project} to target project {args.target_project}.")
    if args.all:
        print("\n⚠️  WARNING: You have selected --all.")
        print("This will DELETE ALL existing dashboards in the TARGET project before importing.")
    confirm = input("Continue? (y/N): ")
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    if args.all:
        print("\n🗑️  Deleting existing dashboards in target project...")
        target_dashboards = list_dashboards(args.host, args.target_key, args.target_project)
        for td in target_dashboards:
            delete_dashboard(args.host, args.target_key, args.target_project, td["id"])

    success = 0
    fail = 0
    for d in dashboards_to_transfer:
        d_id = d.get("id")
        d_name = d.get("name")
        print(f"\n{'='*60}\nProcessing '{d_name}' (ID: {d_id})...\n{'='*60}")
        if transfer_dashboard_with_insights(
            args.host,
            args.source_key,
            args.target_key,
            args.source_project,
            args.target_project,
            int(d_id),
            copy_actions=not args.skip_actions,
        ):
            success += 1
        else:
            fail += 1

    print(f"\n{'='*60}\n🏁 Transfer complete.\n✅ Successful: {success}\n❌ Failed: {fail}\n{'='*60}")


if __name__ == "__main__":
    main()
