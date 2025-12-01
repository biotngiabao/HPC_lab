# analysis/module/api.py
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import logging
from fastapi import HTTPException
from .kafka_producer import KafkaProducerClient
from .datastore import HISTORY, UNITS

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-initialized producer. Read brokers from environment so we can run in k8s.
_producer = None

def get_producer(retries: int = 1, delay: float = 2.0):
  global _producer
  if _producer is not None:
    return _producer

  brokers = os.environ.get("KAFKA_BROKERS", "localhost:9094")
  last_exc = None
  for _ in range(retries):
    try:
      _producer = KafkaProducerClient(broker_addr=brokers)
      return _producer
    except Exception as e:
      last_exc = e
      logger.error(f"Failed to create Kafka producer for {brokers}: {e}")
      time_to_sleep = delay
      try:
        import time
        time.sleep(time_to_sleep)
      except Exception:
        pass

  # If we cannot create a producer, app should return a 503 on requests that need it
  raise HTTPException(status_code=503, detail=f"Kafka unavailable: {last_exc}")


@router.get("/metrics", response_class=JSONResponse)
def api_metrics():
    """
    Returns:
    {
      "hosts": {
        "hostname": {
          "metrics": {
            "cpu": { ... },
            "diskio.read": { ... },
            ...
          }
        }
      }
    }
    """
    hosts: Dict[str, Dict[str, Any]] = {}

    for (host, metric_name), dq in HISTORY.items():
        if not dq:
            continue

        values = [p["value"] for p in dq]
        avg = sum(values) / len(values)
        mx = max(values)
        latest = values[-1]
        unit = UNITS.get((host, metric_name), "")

        h = hosts.setdefault(host, {"metrics": {}})
        h["metrics"][metric_name] = {
            "values": values,
            "avg": avg,
            "max": mx,
            "latest": latest,
            "unit": unit,
        }

    return JSONResponse({"hosts": hosts})


@router.post("/send-commands")
async def send_commands(payload: dict):
    metrics = payload.get("metrics", [])

    if not metrics:
        return JSONResponse(
            {"status": "error", "message": "No metrics selected"}, status_code=400
        )
        
    

    # Lazy-get a producer (may raise HTTPException(503) if Kafka unavailable)
    try:
      prod = get_producer(retries=3, delay=1.0)
    except HTTPException as e:
      logger.error("Cannot obtain Kafka producer: %s", e.detail)
      raise

    try:
      prod.send_message(topic="commands", message=metrics)
    except Exception as e:
      logger.exception("Failed to send commands to Kafka: %s", e)
      raise HTTPException(status_code=503, detail=str(e))

    return JSONResponse({"status": "ok", "sent": metrics})
