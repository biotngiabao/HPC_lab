from generated.monitor_pb2_grpc import (
    add_MonitorServiceServicer_to_server,
)

import grpc
from concurrent import futures
import logging
from module.grpc_server import MonitorService
from module.kafka_producer import KafkaProducerClient


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    producer = KafkaProducerClient(broker_addr="localhost:9094")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_MonitorServiceServicer_to_server(MonitorService(producer), server)
    server.add_insecure_port("[::]:50051")

    logging.info("Starting gRPC server on port 50051...")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    main()
