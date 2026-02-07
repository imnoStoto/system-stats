from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass

from sysmon.analysis import CpuCapacity, cpu_health_label, normalize_load, smt_status
from sysmon.collectors import (
    collect_cpu,
    collect_disk,
    collect_host_os,
    collect_memory,
    fmt_bytes,
    fmt_uptime,
)
from sysmon.network import collect_network_rates, fmt_rate, likely_uplink


@dataclass(frozen=True)
class Snapshot:
    host: object
    cpu: object
    mem: object
    disk: object
    smt: str
    load_norm_1m: float | None
    cpu_health: str
    net: object
    uplink: object | None


def build_snapshot(live_interval: float) -> Snapshot:
    host = collect_host_os()
    cpu = collect_cpu(sample_seconds=0.5)
    mem = collect_memory()
    disk = collect_disk("/")

    cap = CpuCapacity(logical=host.cpu_count_logical, physical=host.cpu_count_physical)
    smt = smt_status(cap)
    load_norm = normalize_load(cpu.loadavg_1m, host.cpu_count_logical)
    health = cpu_health_label(cpu.percent, load_norm)

    # keep network sampling short in live mode so the ui is responsive.
    # (if printing once, give it a longer window for nicer rates)
    net_sample = 0.5 if live_interval > 0 else 1.5
    net = collect_network_rates(sample_seconds=net_sample)
    uplink = likely_uplink(net.ifaces)

    return Snapshot(
        host=host,
        cpu=cpu,
        mem=mem,
        disk=disk,
        smt=smt,
        load_norm_1m=load_norm,
        cpu_health=health,
        net=net,
        uplink=uplink,
    )


def render_snapshot(s: Snapshot) -> None:
    host = s.host
    cpu = s.cpu
    mem = s.mem
    disk = s.disk
    net = s.net
    uplink = s.uplink
    uplink_name = uplink.name if uplink is not None else "n/a"

    print("*~system*~*snapshot~*")
    print(f"Host: {host.hostname} ({host.fqdn})")
    print(f"OS:   {host.os_name}  macOS {host.os_version}  {host.machine}")
    print(f"CPU:  physical={host.cpu_count_physical} logical={host.cpu_count_logical} SMT={s.smt}")
    print(f"Up:   {fmt_uptime(host.boot_time_unix)}")
    print()

    if cpu.loadavg_1m is not None and s.load_norm_1m is not None:
        norm = f"{(s.load_norm_1m * 100):.0f}%"
        print(
            f"CPU:  {cpu.percent:.1f}%  "
            f"loadavg={cpu.loadavg_1m:.2f} {cpu.loadavg_5m:.2f} {cpu.loadavg_15m:.2f}  "
            f"load_norm(1m)={norm}  health={s.cpu_health}"
        )
    else:
        print(f"CPU:  {cpu.percent:.1f}%  health={s.cpu_health}")

    print(
        f"Mem:  {mem.percent:.1f}%  used={fmt_bytes(mem.used_bytes)}  "
        f"avail={fmt_bytes(mem.available_bytes)}  total={fmt_bytes(mem.total_bytes)}"
    )
    print(
        f"Disk: {disk.percent:.1f}%  used={fmt_bytes(disk.used_bytes)}  "
        f"free={fmt_bytes(disk.free_bytes)}  total={fmt_bytes(disk.total_bytes)}  ({disk.path})"
    )
    print()

    if uplink is not None:
        print(
            f"Net:  rx={fmt_rate(net.total_rx_bps)}  tx={fmt_rate(net.total_tx_bps)}  "
            f"(sample={net.sample_seconds:.1f}s)  uplink={uplink_name}  "
            f"uplink_totals rx={uplink.rx_bytes} tx={uplink.tx_bytes}"
        )
        print(f"  - {uplink.name}: up  rx={fmt_rate(uplink.rx_bps)}  tx={fmt_rate(uplink.tx_bps)}")
    else:
        print(
            f"Net:  rx={fmt_rate(net.total_rx_bps)}  tx={fmt_rate(net.total_tx_bps)}  "
            f"(sample={net.sample_seconds:.1f}s)  uplink=n/a"
        )


def main() -> None:
    p = argparse.ArgumentParser(prog="sysmon")
    p.add_argument("--interval", type=float, default=0.0, help="Seconds between refreshes. 0 prints once.")
    p.add_argument("--no-clear", action="store_true", help="Do not clear the terminal between refreshes.")
    args = p.parse_args()

    interval = max(0.0, args.interval)

    try:
        while True:
            t0 = time.time()

            # collect while the previous snapshot remains visible (prevents flashing).
            snap = build_snapshot(interval)

            if interval > 0 and not args.no_clear:
                os.system("clear")

            render_snapshot(snap)

            if interval <= 0:
                break

            elapsed = time.time() - t0
            time.sleep(max(0.0, interval - elapsed))

    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
