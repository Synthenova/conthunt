"""GCS-backed virtual filesystem for Deep Agents."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import fnmatch
import posixpath
import re
from typing import Iterable, Optional

from google.cloud import storage

from deepagents.backends.protocol import BackendProtocol, WriteResult, EditResult
from deepagents.backends.utils import FileInfo, GrepMatch


@dataclass
class GCSBackend(BackendProtocol):
    """Virtual filesystem backed by a GCS bucket."""

    bucket_name: str
    root_prefix: str = "deepagents"

    def __post_init__(self) -> None:
        self._client = storage.Client()
        self._bucket = self._client.bucket(self.bucket_name)
        self.root_prefix = self.root_prefix.strip("/")

    def _normalize_path(self, path: str) -> Optional[str]:
        if not path or not path.startswith("/"):
            return None
        normalized = posixpath.normpath(path)
        if not normalized.startswith("/"):
            return None
        if ".." in normalized.split("/"):
            return None
        return normalized

    def _key(self, path: str) -> Optional[str]:
        normalized = self._normalize_path(path)
        if not normalized:
            return None
        suffix = normalized.lstrip("/")
        if self.root_prefix:
            return f"{self.root_prefix}/{suffix}"
        return suffix

    def _list_blobs(self, prefix: str) -> Iterable[storage.Blob]:
        return self._client.list_blobs(self.bucket_name, prefix=prefix)

    def ls_info(self, path: str) -> list[FileInfo]:
        key = self._key(path)
        if not key:
            return []
        if not key.endswith("/"):
            key = f"{key}/"

        iterator = self._client.list_blobs(
            self.bucket_name,
            prefix=key,
            delimiter="/",
        )

        results: list[FileInfo] = []

        for prefix in getattr(iterator, "prefixes", []):
            rel = prefix[len(self.root_prefix) + 1 :] if self.root_prefix else prefix
            results.append(FileInfo(path=f"/{rel.rstrip('/')}", is_dir=True))

        for blob in iterator:
            rel = blob.name[len(self.root_prefix) + 1 :] if self.root_prefix else blob.name
            results.append(
                FileInfo(
                    path=f"/{rel}",
                    is_dir=False,
                    size=blob.size,
                    modified_at=blob.updated,
                )
            )

        return sorted(results, key=lambda f: f["path"] if isinstance(f, dict) else f.path)

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        key = self._key(file_path)
        if not key:
            return f"Error: File '{file_path}' not found"
        blob = self._bucket.blob(key)
        if not blob.exists():
            return f"Error: File '{file_path}' not found"

        end = offset + limit - 1 if limit and limit > 0 else None
        data = blob.download_as_bytes(start=offset or None, end=end)
        text = data.decode("utf-8", errors="replace")

        lines = text.splitlines()
        numbered = "\n".join(f"{idx + 1} | {line}" for idx, line in enumerate(lines))
        return numbered

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        base_key = self._key(path)
        if not base_key:
            return []
        if not base_key.endswith("/"):
            base_key = f"{base_key}/"

        matches: list[FileInfo] = []
        for blob in self._list_blobs(base_key):
            rel = blob.name[len(self.root_prefix) + 1 :] if self.root_prefix else blob.name
            rel_path = f"/{rel}"
            if fnmatch.fnmatch(rel_path, pattern):
                matches.append(
                    FileInfo(
                        path=rel_path,
                        is_dir=False,
                        size=blob.size,
                        modified_at=blob.updated,
                    )
                )
        return sorted(matches, key=lambda f: f["path"] if isinstance(f, dict) else f.path)

    def grep_raw(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> list[GrepMatch] | str:
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return f"Invalid regex pattern: {exc}"

        base_path = path or "/"
        base_key = self._key(base_path)
        if not base_key:
            return []
        if not base_key.endswith("/"):
            base_key = f"{base_key}/"

        results: list[GrepMatch] = []
        for blob in self._list_blobs(base_key):
            rel = blob.name[len(self.root_prefix) + 1 :] if self.root_prefix else blob.name
            rel_path = f"/{rel}"
            if glob and not fnmatch.fnmatch(rel_path, glob):
                continue

            text = blob.download_as_text()
            for idx, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    results.append(GrepMatch(path=rel_path, line=idx, text=line))

        return results

    def write(self, file_path: str, content: str) -> WriteResult:
        key = self._key(file_path)
        if not key:
            return WriteResult(error=f"Invalid path: {file_path}")
        blob = self._bucket.blob(key)
        if blob.exists():
            return WriteResult(error=f"File already exists: {file_path}")
        blob.upload_from_string(content.encode("utf-8"), content_type="text/plain")
        return WriteResult(path=file_path, files_update=None)

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        key = self._key(file_path)
        if not key:
            return EditResult(error=f"Invalid path: {file_path}")
        blob = self._bucket.blob(key)
        if not blob.exists():
            return EditResult(error=f"File not found: {file_path}")

        text = blob.download_as_text()
        occurrences = text.count(old_string)
        if occurrences == 0:
            return EditResult(error=f"'{old_string}' not found in {file_path}")
        if not replace_all and occurrences > 1:
            return EditResult(error="Multiple occurrences found. Use replace_all=True.")

        updated = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
        blob.upload_from_string(updated.encode("utf-8"), content_type="text/plain")
        return EditResult(path=file_path, files_update=None, occurrences=occurrences)
