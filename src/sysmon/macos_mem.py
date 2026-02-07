from __future__ import annotations
import re
import subprocess
from dataclasses import dataclass
import psutil


@dataclass(frozen=True)
class VmStat:
    page_size_bytes: int
    pages_free: int | None
    pages_active: int | None
    pages_inactive: int | None
    pages_speculative: int | None
    pages_wired: int | None
    pages_compressed: int | None
    pageins: int | None
    pageouts: int | None
    swapins: int | None
    swapouts: int | None


@dataclass(frozen=True)
class MacMemory:
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float

    swap_total_bytes: int
    swap_used_bytes: int
    swap_free_bytes: int
    swap_percent: float

    vm_stat: VmStat | None

    # availability estimate
    # (free + inactive + speculative) * page_size
    available_est_bytes: int | None


_VMSTAT_KEYMAP: dict[str, str] = {
    "Pages free": "pages_free",
    "Pages active": "pages_active",
    "Pages inactive": "pages_inactive",
    "Pages speculative": "pages_speculative",
    "Pages wired down": "pages_wired",
    "Pages occupied by compressor": "pages_compressed",
    "Pageins": "pageins",
    "Pageouts": "pageouts",
    "Swapins": "swapins",
    "Swapouts": "swapouts",
}


def _run_vm_stat() -> VmStat | None:
    """
    Parse `vm_stat` output (macOS). No sudo required.
    Example header:
      Mach Virtual Memory Statistics: (page size of 16384 bytes)
    Then lines like:
      Pages free:                               12345.
    """
    try:
        proc = subprocess.run(["vm_stat"], check=True, capture_output=True, text=True)
    except Exception:
        return None

    text = proc.stdout.splitlines()
    if not text:
        return None

    # extract page size
    m = re.search(r"page size of (\d+) bytes", text[0])
    if not m:
        return None
    page_size = int(m.group(1))

    values: dict[str, int] = {}
    for line in text[1:]:
        line = line.strip()
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip().rstrip(".")
        v = v.replace(",", "")  # sometimes comma-separated
        if not v or not v.isdigit():
            continue
        values[k] = int(v)

    def get(key: str) -> int | None:
        return values.get(key)

    return VmStat(
        page_size_bytes=page_size,
        pages_free=get("Pages free"),
        pages_active=get("Pages active"),
        pages_inactive=get("Pages inactive"),
        pages_speculative=get("Pages speculative"),
        pages_wired=get("Pages wired down"),
        pages_compressed=get("Pages occupied by compressor"),
        pageins=get("Pageins"),
        pageouts=get("Pageouts"),
        swapins=get("Swapins"),
        swapouts=get("Swapouts"),
    )


def collect_macos_memory() -> MacMemory:
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    vs = _run_vm_stat()

    available_est: int | None = None
    if vs is not None:
        # free + inactive + speculative is a useful approximation.
        if vs.pages_free is not None and vs.pages_inactive is not None and vs.pages_speculative is not None:
            pages = vs.pages_free + vs.pages_inactive + vs.pages_speculative
            available_est = pages * vs.page_size_bytes

    return MacMemory(
        total_bytes=int(vm.total),
        used_bytes=int(vm.used),
        available_bytes=int(vm.available),
        percent=float(vm.percent),
        swap_total_bytes=int(sm.total),
        swap_used_bytes=int(sm.used),
        swap_free_bytes=int(sm.free),
        swap_percent=float(sm.percent),
        vm_stat=vs,
        available_est_bytes=available_est,
    )
