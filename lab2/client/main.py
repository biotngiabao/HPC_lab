import grpc
import time
import subprocess

from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandResponse


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.decode().strip()}"


def command_stream():
    while True:

        yield CommandResponse(
            time="2021-09-06T16:05:06Z", hostname="node1", metric="cpu", value="CPU"
        )
        time.sleep(1)


def main():
    print(run_command("top -b -n1 | head -5"))
    channel = grpc.insecure_channel("localhost:50051")
    stub = MonitorServiceStub(channel)
    response = stub.CommandStream(command_stream())
    print(response)


if __name__ == "__main__":
    main()
