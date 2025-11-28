from generated.monitor_pb2_grpc import (
    add_MonitorServiceServicer_to_server,
)

import grpc
from concurrent import futures
import logging
from module.grpc_server import MonitorService
from module.kafka_producer import KafkaProducerClient
from module.kafka_consumer import KafkaConsumerClient
import threading


def handler_command(message: dict):
    logging.info(f"[Main] Received command message: {message}")
    # Here you can add logic to handle the command message


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    consumer = KafkaConsumerClient(
        topic="commands",
        brokers="localhost:9094",
        group_id="monitor-server-group",
        auto_offset_reset="earliest",
    )
    producer = KafkaProducerClient(broker_addr="localhost:9094")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_MonitorServiceServicer_to_server(MonitorService(producer, consumer), server)
    server.add_insecure_port("[::]:50051")

    logging.info("Starting gRPC server on port 50051...")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    main()
