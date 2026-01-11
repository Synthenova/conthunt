#!/usr/bin/env python3
import os
import sys
import subprocess

def upload_secrets(env_file_path):
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

    # Enable API
    print("Ensuring Secret Manager API is enabled...")
    subprocess.run(["gcloud", "services", "enable", "secretmanager.googleapis.com"], check=True)
    
    project_id = subprocess.check_output(["gcloud", "config", "get-value", "project"], text=True).strip()
    print(f"Target Project: {project_id}")

    # SA to grant access to
    # Try to find the default compute SA
    project_number = subprocess.check_output(
        ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"], 
        text=True
    ).strip()
    compute_sa = f"{project_number}-compute@developer.gserviceaccount.com"

    for key in keys_to_upload:
        if key not in secrets:
            print(f"Skipping {key} (not found in file)")
            continue

        value = secrets[key]
        print(f"Processing {key}...")

        # Create secret if not exists
        create_proc = subprocess.run(
            ["gcloud", "secrets", "create", key, "--replication-policy=automatic", "--quiet"],
            capture_output=True
        )
        
        # Add new version
        proc = subprocess.Popen(
            ["gcloud", "secrets", "versions", "add", key, "--data-file=-"],
            stdin=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=value)
        
        if proc.returncode == 0:
            print(f" uploaded.")
            # Grant access
            subprocess.run([
                "gcloud", "secrets", "add-iam-policy-binding", key,
                "--member=serviceAccount:" + compute_sa,
                "--role=roles/secretmanager.secretAccessor"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f" failed.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./scripts/sync_secrets.py <path-to-env-file>")
        print("Example: ./scripts/sync_secrets.py backend/.env.prod")
        sys.exit(1)
    
    upload_secrets(sys.argv[1])
