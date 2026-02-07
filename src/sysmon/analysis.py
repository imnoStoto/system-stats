from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CpuCapacity:
    logical: int
    physical: int | None


def smt_status(cap: CpuCapacity) -> str:
    """
    returns 'on', 'off', or 'unknown' based on logical vs physical.
    """
    if cap.physical is None or cap.physical <= 0 or cap.logical <= 0:
        return "unknown"
    if cap.logical > cap.physical:
        return "on"
    if cap.logical == cap.physical:
        return "off"
    
    return "unknown"


def normalize_load(load_1m: float | None, logical_cpus: int) -> float | None:
    """
    convert loadavg (runnable tasks) into a rough utilization fraction.
    example: load_1m=3 on a 6-logical CPU machine => 0.50 (50%).
    """
    if load_1m is None:
        return None
    if logical_cpus <= 0:
        return None
    return load_1m / logical_cpus


def cpu_health_label(cpu_percent: float, load_frac_1m: float | None) -> str:
    """
    very simple label. uses both CPU percent and normalized load.
    - load_frac ~ 1.0 means the machine is saturated (queueing likely).
    """
    if load_frac_1m is not None:
        if load_frac_1m < 0.60:
            return "OK"
        if load_frac_1m < 0.90:
            return "BUSY"
        if load_frac_1m < 1.10:
            return "SATURATED"
        return "OVERLOADED"

    if cpu_percent < 60.0:
        return "OK"
    if cpu_percent < 85.0:
        return "BUSY"
    if cpu_percent < 95.0:
        return "SATURATED"
    return "OVERLOADED"
