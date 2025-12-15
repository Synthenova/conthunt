import os
import re
import urllib.request
from urllib.parse import urlparse
import ssl

# Configuration
SOURCE_FILE = 'docs/12labs/12labsdocs.md'
BASE_OUTPUT_DIR = 'docs/12labs'

def download_and_replace():
    # Handle SSL context for simple scripts
    ssl._create_default_https_context = ssl._create_unverified_context
    
    try:
        with open(SOURCE_FILE, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Source file {SOURCE_FILE} not found.")
        return

    # Regex to find markdown links with http/https
    # Captures: 1=Text, 2=URL
    link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')

    def replace_match(match):
        text_label = match.group(1)
        url = match.group(2)
        
        # Only process twelvelabs docs to avoid downloading random external links if any
        if 'twelvelabs.io' not in url:
            return match.group(0)

        # Parse URL
        parsed_url = urlparse(url)
        path = parsed_url.path # e.g. /docs/get-started/introduction.mdx
        
        # Handle cases where path is empty or just '/'
        if not path or path == '/':
            # Use a fallback name based on domain or query? 
            # For now skip or use 'index.md'
            return match.group(0)

        # Remove leading slash for os.path.join
        relative_path_segment = path.lstrip('/')
        
        # Determine local filename
        # Change extension .mdx to .md if present
        if relative_path_segment.endswith('.mdx'):
            local_rel_path = relative_path_segment[:-4] + '.md'
        elif relative_path_segment.endswith('.md'):
            local_rel_path = relative_path_segment
        else:
            # If no extension or other extension, append .md or keep?
            # User specifically said "downloaded .mds".
            # If it ends in /, treat as index.md?
            if relative_path_segment.endswith('/'):
                local_rel_path = relative_path_segment + 'index.md'
            else:
                local_rel_path = relative_path_segment + '.md'

        # Full local path
        local_full_path = os.path.join(BASE_OUTPUT_DIR, local_rel_path)
        
        # Create directory if needed
        try:
            os.makedirs(os.path.dirname(local_full_path), exist_ok=True)
        except OSError as e:
            print(f"Error creating directory for {local_full_path}: {e}")
            return match.group(0)
        
        # Download
        print(f"Downloading {url} to {local_full_path}...")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    print(f"Failed to download {url}: Status {response.status}")
                    return match.group(0)
                
                data = response.read()
                # Decode assuming utf-8
                text_content = data.decode('utf-8')
                
            with open(local_full_path, 'w') as out_f:
                out_f.write(text_content)
                
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return match.group(0)
            
        # Return new link
        return f'[{text_label}]({local_rel_path})'

    new_content = link_pattern.sub(replace_match, content)

    with open(SOURCE_FILE, 'w') as f:
        f.write(new_content)
    
    print("Done processing file.")

if __name__ == "__main__":
    download_and_replace()
