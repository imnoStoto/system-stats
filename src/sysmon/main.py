from __future__ import annotations

from sysmon.analysis import CpuCapacity, cpu_health_label, normalize_load, smt_status
from sysmon.collectors import (
    collect_cpu,
    collect_disk,
    collect_host_os,
    collect_memory,
    fmt_bytes,
    fmt_uptime,
)


def main() -> None:
    host = collect_host_os()
    cpu = collect_cpu(sample_seconds=0.5)
    mem = collect_memory()
    disk = collect_disk("/")

    cap = CpuCapacity(logical=host.cpu_count_logical, physical=host.cpu_count_physical)
    smt = smt_status(cap)
    load_frac = normalize_load(cpu.loadavg_1m, host.cpu_count_logical)
    health = cpu_health_label(cpu.percent, load_frac)

    print("*~system*~*snapshot~*")
    print(f"Host: {host.hostname} ({host.fqdn})")
    print(f"OS:   {host.os_name}  macOS {host.os_version}  {host.machine}")
    print(f"CPU:  physical={host.cpu_count_physical} logical={host.cpu_count_logical} SMT={smt}")
    print(f"Up:   {fmt_uptime(host.boot_time_unix)}")
    print()

    if cpu.loadavg_1m is not None:
        # Normalized load as a percentage of capacity
        norm = f"{(load_frac * 100):.0f}%" if load_frac is not None else "n/a"
        print(
            f"CPU:  {cpu.percent:.1f}%  "
            f"loadavg={cpu.loadavg_1m:.2f} {cpu.loadavg_5m:.2f} {cpu.loadavg_15m:.2f}  "
            f"load_norm(1m)={norm}  "
            f"health={health}"
        )
    else:
        print(f"CPU:  {cpu.percent:.1f}%  health={health}")

    print(
        f"Mem:  {mem.percent:.1f}%  used={fmt_bytes(mem.used_bytes)}  "
        f"avail={fmt_bytes(mem.available_bytes)}  total={fmt_bytes(mem.total_bytes)}"
    )
    print(
        f"Disk: {disk.percent:.1f}%  used={fmt_bytes(disk.used_bytes)}  "
        f"free={fmt_bytes(disk.free_bytes)}  total={fmt_bytes(disk.total_bytes)}  ({disk.path})"
    )


if __name__ == "__main__":
    main()
