from kafka import KafkaProducer
import json


class KafkaProducerClient:
    def __init__(
        self,
        broker_addr: str,
        linger_ms: int = 5,
        retries: int = 3,
    ) -> None:
        """
        :param broker_addr: Kafka bootstrap servers
        :param linger_ms: Batch delay for better throughput
        :param retries: Retry count for failed sends
        """
        self.producer = KafkaProducer(
            bootstrap_servers=broker_addr,
            linger_ms=linger_ms,
            retries=retries,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def send_message(self, topic: str, message: dict) -> None:
        future = self.producer.send(topic, value=message)
        return future

    def close(self) -> None:
        self.producer.flush()
        self.producer.close()
