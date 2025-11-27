from generated.monitor_pb2_grpc import (
    MonitorServiceServicer,
)
from generated.monitor_pb2 import CommandRequest, CommandResponse
import grpc
from google.protobuf.json_format import MessageToJson
import logging
from module.kafka_producer import KafkaProducerClient


class MetricType:
    CPU = "cpu"
    MEMORY = "memory"
    DISKIO = "diskio"
    NETWORK = "network"
    PROCESS_COUNT = "process_count"


class MonitorService(MonitorServiceServicer):
    def __init__(self, producer: KafkaProducerClient) -> None:
        self.logger = logging.getLogger(__name__)
        self.producer = producer

    def CommandStream(self, request_iterator, context):
        command = MetricType.CPU
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

                if request.metric == MetricType.CPU:
                    command = MetricType.MEMORY
                elif request.metric == MetricType.MEMORY:
                    command = MetricType.DISKIO
                elif request.metric == MetricType.DISKIO:
                    command = MetricType.NETWORK
                elif request.metric == MetricType.NETWORK:
                    command = MetricType.PROCESS_COUNT
                elif request.metric == MetricType.PROCESS_COUNT:
                    command = MetricType.CPU

                yield CommandRequest(command=command)

        except grpc.RpcError as e:
            self.logger.error(f"RPC error in CommandStream: {e.code()} - {e.details()}")
            context.set_code(e.code())
            context.set_details(e.details())
            raise

        except Exception as e:
            self.logger.error(f"Error in CommandStream: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise
