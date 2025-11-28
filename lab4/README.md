# Realtime Monitor (gRPC + Kafka + FastAPI)

A lightweight monitoring demo that uses a gRPC agent (client) to stream periodic system metrics to a gRPC server. The server forwards metrics into Kafka, and an analysis service consumes Kafka messages to power a realtime dashboard served via FastAPI.

This repository contains three main components:

- client — a monitoring agent that collects metrics using plugins and streams them to the server over gRPC
- server — a gRPC server that receives metrics and publishes them to a Kafka topic
- analysis — a Kafka consumer that maintains recent history and serves a realtime dashboard (FastAPI + Chart.js)

Key details
- gRPC server port: `50051` (insecure by default)
- Kafka topic used: `monitor_metrics`
- Kafka bootstrap/external port (docker): `9094`
- Analysis dashboard (FastAPI): `http://localhost:8003/` (serves HTML dashboard)
- Kafka UI included in docker-compose is exposed on `http://localhost:9095`

---

## Quickstart (recommended)

1. Start Kafka (and Kafka UI) via docker-compose

```bash
# from repo root
docker-compose up -d
```

2. Create a Python virtualenv and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Generate gRPC code (if you modify proto files or if generated code is missing)

```bash
make gen_code
```

**Note**: change import monitor_pb2 as monitor__pb2 -> import generated.monitor_pb2 as monitor__pb2


4. Launch the components (each in its own terminal)

- Start the server (gRPC -> Kafka)

```bash
make server
# or: cd server && python main.py
```

- Start the client (agent that streams metrics)

```bash
make client
# or: cd client && python main.py
```

- Start the analysis/dashboard

```bash
make analysis
# or: cd analysis && python main.py
```

Open the dashboard: http://localhost:8003/
Open Kafka UI: http://localhost:9095/ (check `monitor_metrics` topic)

---

## Components and flow

1. client/module/plugins — collect system metrics using plugins (cpu, memory, diskio, network, process_count)
2. client/module/grpc_client — opens a streaming connection to server MonitorService.CommandStream and sends CommandResponse messages with metrics
3. server/module/grpc_server — receives CommandResponse from the agent, forwards the metric into Kafka, and responds with a CommandRequest directing which metric the client should send next
4. analysis/module/kafka_consumer — subscribes to `monitor_metrics`, keeps last ~15 samples per metric, and powers the FastAPI endpoints

The analysis dashboard polls `/api/metrics` every second and renders charts using Chart.js for the latest time-series.

---

## Development notes

- Code generation: proto files are in `_protos/monitor.proto`. Use `make gen_code` to regenerate client/server stub files.
- Default broker address used in code is `localhost:9094` (see `server/main.py` and `analysis/main.py`). Update these if you run Kafka elsewhere.
- The demo uses insecure gRPC and local Kafka; production deployments should add authentication, TLS, and robust error handling.

---

## Troubleshooting

- If you see no metrics on the dashboard: ensure Kafka is running and both client and server are connected to the same broker/ports.
- To inspect Kafka messages use Kafka UI at `http://localhost:9095` or use kafka-console-consumer if available.

---

## License

MIT — see `LICENSE` if you add one.

---

If you'd like, I can expand the README with contribution guidelines, tests, or CI instructions — tell me what you'd prefer next.