import subprocess
import socket
import datetime
import re


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
        # usage is in column 5 like “23%”
        if parts[-1] == "/":
            return float(parts[4].strip("%"))
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

    if cpu is not None:
        print(format_metric("cpu", cpu))
    if mem is not None:
        print(format_metric("memory", mem))
    if disk is not None:
        print(format_metric("disk_usage", disk))

