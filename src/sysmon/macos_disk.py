from __future__ import annotations

import plistlib
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ApfsSpace:
    path: str
    container: str | None
    total_bytes: int | None
    free_bytes: int | None
    notes: str | None


def _diskutil_info_plist(path: str) -> dict | None:
    try:
        proc = subprocess.run(
            ["diskutil", "info", "-plist", path],
            check=True,
            capture_output=True,
        )
        return plistlib.loads(proc.stdout)
    except Exception:
        return None


def collect_apfs_space(path: str = "/") -> ApfsSpace:
    info = _diskutil_info_plist(path)
    if info is None:
        return ApfsSpace(path, None, None, None, "diskutil info failed")

    container = info.get("APFSContainerReference")
    total = info.get("APFSContainerSize")
    free = info.get("APFSContainerFree")

    if container and isinstance(total, int) and isinstance(free, int):
        return ApfsSpace(
            path=path,
            container=container,
            total_bytes=int(total),
            free_bytes=int(free),
            notes=None,
        )

    return ApfsSpace(
        path=path,
        container=container,
        total_bytes=int(total) if isinstance(total, int) else None,
        free_bytes=int(free) if isinstance(free, int) else None,
        notes="APFS container keys missing or incomplete",
    )
