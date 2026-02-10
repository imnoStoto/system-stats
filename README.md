# system-stats

Read-only system monitoring utility designed for operational diagnostics, documentation, and first-level troubleshooting.  
This tool provides structured, human-readable output to support incident response, validation checks, and escalation workflows.

## Purpose
`system-stats` is intended for situational awareness, not system modification.  
It surfaces current system state (OS, CPU, memory, disk, uptime, and network activity) to help operators:

- Confirm baseline system health
- Identify abnormal conditions
- Capture consistent snapshots during incidents
- Support documentation and escalation with reproducible evidence

## Data Collected
Depending on platform support, output may include:
- Operating system and kernel version
- CPU utilization and load averages
- Memory usage (total, used, available)
- Disk usage for mounted volumes
- System uptime
- Basic network throughput statistics

All data is collected via standard OS interfaces.

## Typical Use Cases
- Verifying system health
- Capturing a “point-in-time” snapshot for documentation
- Validating that system resources align with expected baselines
