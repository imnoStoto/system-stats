from __future__ import annotations
import os
import platform
import socket
import time
from dataclasses import dataclass
import psutil

def safe_fqdn(hostname: str) -> str:
    """
    socket.getfqdn() can return reverse-DNS artifacts
    """
    fq = socket.getfqdn()
    fq = (fq or "").strip().lower()

    # if it looks like reverse DNS or is otherwise unhelpful, fall back
    if not fq or fq.endswith(".ip6.arpa") or fq.endswith(".in-addr.arpa"):
        return hostname

    if "." not in fq:
        return hostname

    return socket.getfqdn()


@dataclass(frozen=True)
class HostOS:
    hostname: str
    fqdn: str
    os_name: str
    os_version: str
    kernel: str
    machine: str
    cpu_count_logical: int
    cpu_count_physical: int | None
    boot_time_unix: float


def collect_host_os() -> HostOS:
    u = platform.uname()
    hostname = socket.gethostname()
    return HostOS(
        hostname=hostname,
        fqdn=safe_fqdn(hostname),
        os_name=f"{u.system} {u.release}",
        os_version=platform.mac_ver()[0] or "unknown",
        kernel=u.version,
        machine=u.machine,
        cpu_count_logical=psutil.cpu_count(logical=True) or os.cpu_count() or 0,
        cpu_count_physical=psutil.cpu_count(logical=False),
        boot_time_unix=psutil.boot_time(),
    )


@dataclass(frozen=True)
class CPU:
    percent: float
    loadavg_1m: float | None
    loadavg_5m: float | None
    loadavg_15m: float | None


def collect_cpu(sample_seconds: float = 0.5) -> CPU:
    # cpu_percent uses a sampling interval
    pct = psutil.cpu_percent(interval=sample_seconds)
    try:
        la1, la5, la15 = os.getloadavg()  # macOS supports this
    except (AttributeError, OSError):
        la1 = la5 = la15 = None
    return CPU(percent=pct, loadavg_1m=la1, loadavg_5m=la5, loadavg_15m=la15)


@dataclass(frozen=True)
class Memory:
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float


def collect_memory() -> Memory:
    vm = psutil.virtual_memory()
    return Memory(
        total_bytes=int(vm.total),
        used_bytes=int(vm.used),
        available_bytes=int(vm.available),
        percent=float(vm.percent),
    )


@dataclass(frozen=True)
class Disk:
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


def collect_disk(path: str = "/") -> Disk:
    du = psutil.disk_usage(path)
    return Disk(
        path=path,
        total_bytes=int(du.total),
        used_bytes=int(du.used),
        free_bytes=int(du.free),
        percent=float(du.percent),
    )


def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    x = float(n)
    i = 0
    while x >= 1024 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    if i == 0:
        return f"{int(x)} {units[i]}"
    return f"{x:.2f} {units[i]}"


def fmt_uptime(boot_time_unix: float) -> str:
    seconds = int(time.time() - boot_time_unix)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m {secs}s"
