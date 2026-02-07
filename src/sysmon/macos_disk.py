from __future__ import annotations
import plistlib
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ApfsSpace:
    path: str
    total_bytes: int | None
    free_bytes: int | None
    purgeable_bytes: int | None
    effective_free_bytes: int | None
    notes: str | None


def _diskutil_info_plist(path: str) -> dict | None:
    """
    `diskutil info -plist <path>` returns a plist with various keys.
    """
    try:
        proc = subprocess.run(
            ["diskutil", "info", "-plist", path],
            check=True,
            capture_output=True,
        )
    except Exception:
        return None

    try:
        return plistlib.loads(proc.stdout)
    except Exception:
        return None


def collect_apfs_space(path: str = "/") -> ApfsSpace:
    info = _diskutil_info_plist(path)
    if info is None:
        return ApfsSpace(
            path=path,
            total_bytes=None,
            free_bytes=None,
            purgeable_bytes=None,
            effective_free_bytes=None,
            notes="diskutil info -plist failed",
        )

    # attempt plausible keys
    # on many APFS systems, container-level keys exist:
    total = (
        info.get("APFSContainerTotalSpace")
        or info.get("TotalSize")
        or info.get("VolumeTotalSpace")  # sometimes seen
    )
    free = (
        info.get("APFSContainerFreeSpace")
        or info.get("FreeSpace")
        or info.get("VolumeFreeSpace")
    )

    # purgeable keys vary a lot across versions and contexts.
    purgeable = (
        info.get("PurgeableSpace")
        or info.get("APFSPurgeableSpace")
        or info.get("PurgeableSpaceBytes")
    )

    # normalize to ints
    total_i = int(total) if isinstance(total, (int, float)) else None
    free_i = int(free) if isinstance(free, (int, float)) else None
    purge_i = int(purgeable) if isinstance(purgeable, (int, float)) else None

    effective_free: int | None = None
    notes: str | None = None

    if free_i is not None and purge_i is not None:
        effective_free = free_i + purge_i
    elif free_i is not None and purge_i is None:
        notes = "purgeable not available via diskutil plist on this system"
    else:
        notes = "free/total not available via diskutil plist on this system"

    return ApfsSpace(
        path=path,
        total_bytes=total_i,
        free_bytes=free_i,
        purgeable_bytes=purge_i,
        effective_free_bytes=effective_free,
        notes=notes,
    )
