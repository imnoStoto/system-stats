from __future__ import annotations
import argparse
import os
import sys
import time
from sysmon.analysis import CpuCapacity, cpu_health_label, normalize_load, smt_status
from sysmon.collectors import collect_cpu, collect_disk, collect_host_os, collect_memory, fmt_bytes, fmt_uptime
from sysmon.network import collect_network_rates, fmt_rate, likely_uplink


def render_snapshot(interval: float) -> None:
    host = collect_host_os()
    cpu = collect_cpu(sample_seconds=0.5)
    mem = collect_memory()
    disk = collect_disk("/")

    cap = CpuCapacity(logical=host.cpu_count_logical, physical=host.cpu_count_physical)
    smt = smt_status(cap)
    load_frac = normalize_load(cpu.loadavg_1m, host.cpu_count_logical)
    health = cpu_health_label(cpu.percent, load_frac)

    # network sampling uses a slice of the interval
    net_sample = min(max(interval * 0.75, 0.5), 2.0)
    net = collect_network_rates(sample_seconds=net_sample)
    uplink = likely_uplink(net.ifaces)
    uplink_name = uplink.name if uplink is not None else "n/a"

    print("*~system*~*snapshot~*")
    print(f"Host: {host.hostname} ({host.fqdn})")
    print(f"OS:   {host.os_name}  macOS {host.os_version}  {host.machine}")
    print(f"CPU:  physical={host.cpu_count_physical} logical={host.cpu_count_logical} SMT={smt}")
    print(f"Up:   {fmt_uptime(host.boot_time_unix)}")
    print()

    if cpu.loadavg_1m is not None and load_frac is not None:
        norm = f"{(load_frac * 100):.0f}%"
        print(f"CPU:  {cpu.percent:.1f}%  loadavg={cpu.loadavg_1m:.2f} {cpu.loadavg_5m:.2f} {cpu.loadavg_15m:.2f}  load_norm(1m)={norm}  health={health}")
    else:
        print(f"CPU:  {cpu.percent:.1f}%  health={health}")

    print(f"Mem:  {mem.percent:.1f}%  used={fmt_bytes(mem.used_bytes)}  avail={fmt_bytes(mem.available_bytes)}  total={fmt_bytes(mem.total_bytes)}")
    print(f"Disk: {disk.percent:.1f}%  used={fmt_bytes(disk.used_bytes)}  free={fmt_bytes(disk.free_bytes)}  total={fmt_bytes(disk.total_bytes)}  ({disk.path})")
    print()

    if uplink is not None:
        print(
            f"Net:  rx={fmt_rate(net.total_rx_bps)}  tx={fmt_rate(net.total_tx_bps)}  "
            f"(sample={net.sample_seconds:.1f}s)  uplink={uplink_name}  "
            f"uplink_totals rx={uplink.rx_bytes} tx={uplink.tx_bytes}"
        )
        # print uplink line always; it will be useful when it starts moving
        print(f"  - {uplink.name}: up  rx={fmt_rate(uplink.rx_bps)}  tx={fmt_rate(uplink.tx_bps)}")
    else:
        print(f"Net:  rx={fmt_rate(net.total_rx_bps)}  tx={fmt_rate(net.total_tx_bps)}  (sample={net.sample_seconds:.1f}s)  uplink=n/a")


def main() -> None:
    p = argparse.ArgumentParser(prog="sysmon")
    p.add_argument("--interval", type=float, default=0.0, help="Seconds between refreshes. 0 prints once.")
    args = p.parse_args()

    interval = max(0.0, args.interval)

    try:
        while True:
            # clear screen for live mode
            if interval > 0:
                os.system("clear")
            render_snapshot(interval if interval > 0 else 1.5)
            if interval <= 0:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
