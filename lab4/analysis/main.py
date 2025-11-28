# analysis/main.py
import logging
import threading

import uvicorn
from fastapi import FastAPI

from module.consumer import start_kafka_consumer
from module.ui import router as ui_router
from module.api import router as api_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI()

    @app.on_event("startup")
    def on_startup():
        t = threading.Thread(target=start_kafka_consumer, daemon=True)
        t.start()
        logger.info("Kafka consumer thread started")

    # UI at "/"
    app.include_router(ui_router)

    # API under "/api"
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    uvicorn.run(app, host="0.0.0.0", port=8003)


if __name__ == "__main__":
    main()
