import os
import re

backend_dir = "/Users/nirmal/Desktop/conthunt/backend"
log_pattern = re.compile(r'logger\.(info|error|debug|warning|critical|exception)\((.*?)\)', re.DOTALL)

logs = []

for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = log_pattern.finditer(content)
                for match in matches:
                    level = match.group(1)
                    message = match.group(2).strip()
                    # Get line number
                    line_no = content.count('\n', 0, match.start()) + 1
                    logs.append({
                        "file": os.path.relpath(path, backend_dir),
                        "line": line_no,
                        "level": level,
                        "message": message
                    })

for log in logs:
    print(f"{log['file']}:{log['line']} [{log['level'].upper()}] {log['message']}")
