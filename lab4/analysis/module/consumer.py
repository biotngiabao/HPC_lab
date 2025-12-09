import ast
import logging
from typing import Dict, Any
from .datastore import HISTORY, UNITS
import os
from module.kafka_consumer import KafkaConsumerClient

logger = logging.getLogger(__name__)


def process_message(msg: Dict[str, Any]):
    """
    Handles analytics messages from monitor agent.

    Structure:
    {
      "timestamp": "...",
      "hostname": "...",
      "metric": "diskio",
      "value": "{'read': 0.0, 'write': 200.0}",
      "unit": "kB/s"
    }
    """

    logger.info(msg)

    ts = msg.get("timestamp")
    host = msg.get("hostname", "unknown")
    metric = msg.get("metric", "unknown")
    raw_value = msg.get("value", 0)
    unit = msg.get("unit", "")

    # ----- Try numeric metric -----
    try:
        v = float(raw_value)
        key = (host, metric)
        HISTORY[key].append({"ts": ts, "value": v})
        UNITS[key] = unit
        return
    except (ValueError, TypeError):
        pass

    # ----- Try dict metric -----
    if isinstance(raw_value, str) and raw_value.strip().startswith("{"):
        try:
            parsed = ast.literal_eval(raw_value)
            if isinstance(parsed, dict):
                for subkey, subval in parsed.items():
                    try:
                        v = float(subval)
                    except:
                        continue
                    metric_name = f"{metric}.{subkey}"
                    key = (host, metric_name)
                    HISTORY[key].append({"ts": ts, "value": v})
                    UNITS[key] = unit
        except Exception as e:
            logger.warning(f"Parse error: {raw_value} ({e})")




logger = logging.getLogger(__name__)


def start_kafka_consumer():
    import time
    brokers = os.environ.get("KAFKA_BROKERS", "localhost:9092")
    logger.info(f"Using Kafka brokers: {brokers}")
    
    # Retry connecting to Kafka indefinitely (analysis should keep trying until Kafka is ready)
    retry_delay = 5
    attempt = 0
    
    while True:
        try:
            attempt += 1
            logger.info(f"Attempting to connect to Kafka at {brokers} (attempt #{attempt})")
            consumer = KafkaConsumerClient(
                topic="monitor_metrics",
                brokers=brokers,
                group_id="analysis-group",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            logger.info("[Kafka] Consumer connected successfully!")
            break
        except Exception as e:
            logger.error(f"Failed to connect to Kafka brokers '{brokers}': {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
    
    try:
        consumer.start_consuming(process_message)
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
