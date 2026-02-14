#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed


def _sync_one_secret(key, value, gcloud_cmd, compute_sa):
    """Upload a single secret (create + add version + grant IAM)."""
    # Create secret if not exists
    subprocess.run(
        gcloud_cmd + ["secrets", "create", key, "--replication-policy=automatic", "--quiet"],
        capture_output=True
    )

    # Add new version
    proc = subprocess.Popen(
        gcloud_cmd + ["secrets", "versions", "add", key, "--data-file=-"],
        stdin=subprocess.PIPE,
        text=True
    )
    proc.communicate(input=value)

    if proc.returncode != 0:
        return key, False

    # Grant access
    subprocess.run(gcloud_cmd + [
        "secrets", "add-iam-policy-binding", key,
        "--member=serviceAccount:" + compute_sa,
        "--role=roles/secretmanager.secretAccessor"
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return key, True


def upload_secrets(env_file_path, target_project=None):
    """Reads an env file and uploads non-empty keys to Secret Manager."""
    
    if not os.path.exists(env_file_path):
        print(f"Error: File {env_file_path} not found.")
        sys.exit(1)

    print(f"Reading secrets from {env_file_path}...")
    
    # Simple parser for .env files
    secrets = {}
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Strip inline comments (e.g. "120 # seconds" -> "120")
                if '#' in value:
                    value = value.split('#', 1)[0].strip()

                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                if value:
                    secrets[key] = value

    # Interactive confirmation
    print("Found the following keys:")
    for k in secrets.keys():
        print(f" - {k}")
    
    confirm = input("\nUpload specific keys? (Enter comma-separated keys, or 'all'): ")
    
    keys_to_upload = []
    if confirm.lower() == 'all':
        keys_to_upload = list(secrets.keys())
    else:
        keys_to_upload = [k.strip() for k in confirm.split(',') if k.strip()]

    if not keys_to_upload:
        print("No keys selected.")
        return

    # Filter out missing keys
    valid_keys = [k for k in keys_to_upload if k in secrets]
    skipped = [k for k in keys_to_upload if k not in secrets]
    for k in skipped:
        print(f"Skipping {k} (not found in file)")

    if not valid_keys:
        print("No valid keys to upload.")
        return

    # Determine Project ID
    if target_project:
        project_id = target_project
    else:
        print("No project specified, using current gcloud config...")
        project_id = subprocess.check_output(["gcloud", "config", "get-value", "project"], text=True).strip()
    
    print(f"Target Project: {project_id}")

    # Base gcloud command
    gcloud_cmd = ["gcloud", "--project", project_id]

    # Enable API
    print("Ensuring Secret Manager API is enabled...")
    subprocess.run(gcloud_cmd + ["services", "enable", "secretmanager.googleapis.com"], check=True)

    # SA to grant access to (Default Compute SA)
    project_number = subprocess.check_output(
        gcloud_cmd + ["projects", "describe", project_id, "--format=value(projectNumber)"], 
        text=True
    ).strip()
    compute_sa = f"{project_number}-compute@developer.gserviceaccount.com"
    print(f"Granting access to: {compute_sa}")

    # Upload all secrets in parallel
    print(f"\nUploading {len(valid_keys)} secrets in parallel...")
    succeeded, failed = [], []

    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {
            pool.submit(_sync_one_secret, key, secrets[key], gcloud_cmd, compute_sa): key
            for key in valid_keys
        }
        for future in as_completed(futures):
            key, ok = future.result()
            if ok:
                succeeded.append(key)
                print(f"  ✓ {key}")
            else:
                failed.append(key)
                print(f"  ✗ {key}")

    print(f"\nDone: {len(succeeded)} uploaded, {len(failed)} failed.")
    if failed:
        print(f"Failed keys: {', '.join(failed)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload .env secrets to GCP Secret Manager")
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument("--project", help="GCP Project ID", default=None)
    
    args = parser.parse_args()
    
    upload_secrets(args.env_file, args.project)
