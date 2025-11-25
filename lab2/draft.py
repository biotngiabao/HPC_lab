import subprocess
import socket
import datetime
import re


def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_cpu_usage():
    # Use top to get idle, then compute usage
    out = run_cmd(["top", "-bn1"])
    m = re.search(r"Cpu\(s\):\s+([\d\.]+)\%us,\s+([\d\.]+)\%sy,\s+([\d\.]+)\%id", out)
    if m:
        user = float(m.group(1))
        sys = float(m.group(2))
        idle = float(m.group(3))
        usage = user + sys
        return usage
    return None


def get_mem_usage():
    out = run_cmd(["free", "-m"])
    # parse the line starting with “Mem:”
    for line in out.splitlines():
        if line.startswith("Mem:"):
            parts = line.split()
            total = float(parts[1])
            used = float(parts[2])
            pct = used / total * 100.0
            return pct
    return None


def get_disk_usage():
    out = run_cmd(["df", "-h", "/"])
    # parse the line for '/'
    for line in out.splitlines()[1:]:
        parts = line.split()
        # usage is in column 5 like “23%”
        if parts[-1] == "/":
            return float(parts[4].strip("%"))
    return None


def get_network_usage():
    # We’ll take total bytes transmitted and received from /proc/net/dev for interface eth0
    out = run_cmd(["cat", "/proc/net/dev"])
    for line in out.splitlines():
        if "eth0:" in line:
            parts = line.split()
            # Example line: “eth0:  1234 0 0 0 0 0 0 0 5678 0 0 0 0 0 0 0 0”
            recv_bytes = float(parts[1])
            trans_bytes = float(parts[9])
            return recv_bytes + trans_bytes
    return None


def format_metric(metric, value):
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    hostname = socket.gethostname()
    return (
        f'time="{timestamp}", hostname="{hostname}", metric="{metric}", value="{value}"'
    )


if __name__ == "__main__":
    cpu = get_cpu_usage()
    mem = get_mem_usage()
    disk = get_disk_usage()
    net = get_network_usage()

    if cpu is not None:
        print(format_metric("cpu", cpu))
    if mem is not None:
        print(format_metric("memory", mem))
    if disk is not None:
        print(format_metric("disk_usage", disk))
    if net is not None:
        print(format_metric("network_bytes", net))
