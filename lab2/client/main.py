import grpc
import time
import subprocess

from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandResponse, MetricValue
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
        if parts[-1] == "/":
            return float(parts[4].strip("%"))
    return None


def format_metric(metric, value):
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    hostname = socket.gethostname()
    return (
        f'time="{timestamp}", hostname="{hostname}", metric="{metric}", value="{value}"'
    )


def command_stream():
    while True:
        yield CommandResponse(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hostname=socket.gethostname(),
            metrics=[
                MetricValue(name="cpu", value=str(get_cpu_usage())),
                MetricValue(name="memory", value=str(get_mem_usage())),
                MetricValue(name="disk_usage", value=str(get_disk_usage())),
            ],
        )

        time.sleep(1)


def main():
    channel = grpc.insecure_channel("localhost:50051")
    stub = MonitorServiceStub(channel)
    response = stub.CommandStream(command_stream())
    print(response)


if __name__ == "__main__":
    main()
