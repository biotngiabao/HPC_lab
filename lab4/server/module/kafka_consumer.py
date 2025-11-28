from __future__ import annotations

import json
from typing import Any, Dict, Callable
from kafka import KafkaConsumer
import logging


class KafkaConsumerClient:
    """
    Wrapper around kafka-python KafkaConsumer.
    Features:
    - JSON deserialization
    - consumer groups
    - callback processing
    """

    def __init__(
        self,
        topic: str,
        brokers: str = "localhost:9092",
        group_id: str = "default-group",
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = True,
    ):
        self.topic = topic

        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=brokers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,  # "earliest" or "latest"
            enable_auto_commit=enable_auto_commit,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

    def start_consuming(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Start consuming forever.
        :param callback: function that receives each decoded message.
        """
        logging.info(f"[Kafka] Starting consumer for topic: {self.topic}")

        for message in self.consumer:
            try:
                value = message.value  # already JSON dict
                callback(value)
            except Exception as e:
                logging.error(f"[Kafka] Error processing message: {e}")

    def close(self):
        """Close consumer cleanly."""
        self.consumer.close()
