# analysis/module/api.py
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .kafka_producer import KafkaProducerClient
from .datastore import HISTORY, UNITS

router = APIRouter()
producer = KafkaProducerClient(broker_addr="localhost:9094")


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
        
    

    producer.send_message(topic="commands", message=metrics)

    return JSONResponse({"status": "ok", "sent": metrics})
