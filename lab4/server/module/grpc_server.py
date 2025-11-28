from generated.monitor_pb2_grpc import (
    MonitorServiceServicer,
)
from generated.monitor_pb2 import CommandRequest, CommandResponse
import grpc
from google.protobuf.json_format import MessageToJson
import logging
from module.kafka_producer import KafkaProducerClient
from module.kafka_consumer import KafkaConsumerClient
import threading


class MetricType:
    CPU = "cpu"
    MEMORY = "memory"
    DISKIO = "diskio"
    NETWORK = "network"
    PROCESS_COUNT = "process_count"


class MonitorService(MonitorServiceServicer):
    def __init__(
        self, producer: KafkaProducerClient, consumer: KafkaConsumerClient
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.producer = producer
        self.consumer = consumer
        self.received_commands = []

        t = threading.Thread(
            target=consumer.start_consuming, args=(self.handler_command,), daemon=True
        )

        t.start()

    def CommandStream(self, request_iterator, context):

        try:
            for request in request_iterator:
                request: CommandResponse
                logging.info(MessageToJson(request, indent=2))

                self.producer.send_message(
                    topic="monitor_metrics",
                    message={
                        "timestamp": request.timestamp,
                        "hostname": request.hostname,
                        "metric": request.metric,
                        "value": request.value,
                    },
                )

                yield CommandRequest(commandList=self.received_commands)

        except grpc.RpcError as e:
            self.logger.error(f"RPC error in CommandStream: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Error in CommandStream: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise

    def handler_command(self, commmands):
        self.logger.info(f"[MonitorService] Received commands: {commmands}")
        self.received_commands = commmands
