from __future__ import annotations
import time
from dataclasses import dataclass
import psutil


@dataclass(frozen=True)
class IfaceRate:
    name: str
    is_up: bool
    speed_mbps: int | None
    rx_bps: float
    tx_bps: float
    rx_bytes: int
    tx_bytes: int


@dataclass(frozen=True)
class NetworkRates:
    sample_seconds: float
    total_rx_bps: float
    total_tx_bps: float
    ifaces: list[IfaceRate]


def collect_network_rates(sample_seconds: float = 1.0) -> NetworkRates:
    """
    samples network counters twice and returns per-second RX/TX byte rates.
    """
    if sample_seconds <= 0:
        sample_seconds = 0.1

    stats1 = psutil.net_io_counters(pernic=True)
    ifstats = psutil.net_if_stats()

    time.sleep(sample_seconds)

    stats2 = psutil.net_io_counters(pernic=True)

    ifaces: list[IfaceRate] = []
    total_rx = 0.0
    total_tx = 0.0

    for name, s2 in stats2.items():
        s1 = stats1.get(name)
        if s1 is None:
            continue

        rx_bps = (s2.bytes_recv - s1.bytes_recv) / sample_seconds
        tx_bps = (s2.bytes_sent - s1.bytes_sent) / sample_seconds

        st = ifstats.get(name)
        is_up = bool(st.isup) if st is not None else False
        speed = int(st.speed) if (st is not None and st.speed is not None and st.speed > 0) else None

        ifaces.append(
            IfaceRate(
                name=name,
                is_up=is_up,
                speed_mbps=speed,
                rx_bps=rx_bps,
                tx_bps=tx_bps,
                rx_bytes=int(s2.bytes_recv),
                tx_bytes=int(s2.bytes_sent),
            )
        )
        # Totals: include only interfaces that are up (reduces noise)
        if is_up:
            total_rx += rx_bps
            total_tx += tx_bps

    # Sort with "up" first, then highest traffic
    ifaces.sort(key=lambda x: (not x.is_up, -(x.rx_bps + x.tx_bps), x.name))

    return NetworkRates(
        sample_seconds=sample_seconds,
        total_rx_bps=total_rx,
        total_tx_bps=total_tx,
        ifaces=ifaces,
    )


def fmt_rate(bps: float) -> str:
    # Bytes/sec -> human readable
    units = ["B/s", "KiB/s", "MiB/s", "GiB/s"]
    x = float(bps)
    i = 0
    while x >= 1024.0 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    if i == 0:
        return f"{x:.0f} {units[i]}"
    return f"{x:.2f} {units[i]}"
