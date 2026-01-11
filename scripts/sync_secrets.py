#!/usr/bin/env python3
import os
import sys
import subprocess

import argparse

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
        keys_to_upload = secrets.keys()
    else:
        keys_to_upload = [k.strip() for k in confirm.split(',') if k.strip()]

    if not keys_to_upload:
        print("No keys selected.")
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

    for key in keys_to_upload:
        if key not in secrets:
            print(f"Skipping {key} (not found in file)")
            continue

        value = secrets[key]
        print(f"Processing {key}...")

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
        
        if proc.returncode == 0:
            print(f" uploaded.")
            # Grant access
            subprocess.run(gcloud_cmd + [
                "secrets", "add-iam-policy-binding", key,
                "--member=serviceAccount:" + compute_sa,
                "--role=roles/secretmanager.secretAccessor"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f" failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload .env secrets to GCP Secret Manager")
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument("--project", help="GCP Project ID", default=None)
    
    args = parser.parse_args()
    
    upload_secrets(args.env_file, args.project)
