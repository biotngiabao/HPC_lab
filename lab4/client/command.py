import re
import subprocess

# enum for metric types
class MetricType:
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"


def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_cpu_usage():
    out = run_cmd(["top", "-bn1"])
    cpu_line = ""
    for line in out.splitlines():
        if "Cpu(s):" in line:
            cpu_line = line
            break

    m = re.search(r"([\d\.]+)\s+id", cpu_line)
    if not m:
        return None
    idle = float(m.group(1))

    return round(100.0 - idle, 2)


def get_mem_usage():
    out = run_cmd(["free", "-m"])
    for line in out.splitlines():
        if line.startswith("Mem:"):
            parts = line.split()
            total = float(parts[1])
            used = float(parts[2])
            usage = (used / total) * 100.0
            return round(usage, 2)
    return None


def get_disk_usage():
    out = run_cmd(["df", "-h", "/"])
    # parse the line for '/'
    for line in out.splitlines()[1:]:
        parts = line.split()
        if parts[-1] == "/":
            return float(parts[4].strip("%"))
    return None


def get_metric_value(metric: str):
    if metric == MetricType.CPU:
        return get_cpu_usage()
    elif metric == MetricType.MEMORY:
        return get_mem_usage()
    elif metric == MetricType.DISK:
        return get_disk_usage()
    else:
        return None
