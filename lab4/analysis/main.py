import ast
import logging
import threading
from collections import defaultdict, deque
from typing import Any, Deque, Dict, Optional, Tuple

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from module.kafka_consumer import KafkaConsumerClient

logger = logging.getLogger(__name__)

# key: (hostname, metric_name) -> deque of {"ts": str, "value": float}
HISTORY: Dict[Tuple[str, str], Deque[Dict[str, Any]]] = defaultdict(
    lambda: deque(maxlen=15)  # only keep last 15 samples
)

# (hostname, metric_name) -> unit string (%, kB/s, etc.)
UNITS: Dict[Tuple[str, str], str] = {}


# =========================
# Kafka consumer callback
# =========================
def process_message(msg: dict):
    """
    Expected message structure:

    {
      "timestamp": "2025-11-28 00:10:05",
      "hostname": "tngiabao",
      "metric": "diskio",
      "value": "{'read': 0.0, 'write': 262.05}"  # or "7.1" for cpu
      "unit": "kB/s"
    }
    """
    logger.info(msg)

    ts = msg.get("timestamp")
    host = msg.get("hostname", "unknown")
    metric = msg.get("metric", "unknown")
    raw_value = msg.get("value")
    unit = msg.get("unit", "")

    # 1) Try simple numeric value (cpu, memory, etc.)
    try:
        v = float(raw_value)
        key = (host, metric)
        HISTORY[key].append({"ts": ts, "value": v})
        UNITS[key] = unit
        return
    except (TypeError, ValueError):
        pass

    # 2) Try dict-valued metrics like diskio/network
    #    raw_value is often a string like: "{'read': 0.0, 'write': 262.05}"
    if isinstance(raw_value, str) and raw_value.strip().startswith("{"):
        try:
            parsed = ast.literal_eval(raw_value)
            if isinstance(parsed, dict):
                for subkey, subval in parsed.items():
                    try:
                        v = float(subval)
                    except (TypeError, ValueError):
                        continue
                    metric_name = f"{metric}.{subkey}"  # e.g. "diskio.read"
                    key = (host, metric_name)
                    HISTORY[key].append({"ts": ts, "value": v})
                    UNITS[key] = unit
        except Exception as e:
            logger.warning(f"Failed to parse dict metric: {raw_value} ({e})")


def start_kafka_consumer():
    consumer = KafkaConsumerClient(
        topic="monitor_metrics",
        brokers="localhost:9094",  # change if your broker differs
        group_id="analysis-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    try:
        consumer.start_consuming(process_message)
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")


# =========================
# FastAPI app
# =========================
app = FastAPI()


@app.on_event("startup")
def on_startup():
    t = threading.Thread(target=start_kafka_consumer, daemon=True)
    t.start()
    logger.info("Kafka consumer thread started")


@app.get("/", response_class=HTMLResponse)
def index():
    html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Realtime Monitor Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      margin: 0;
      padding: 20px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #020617;
      color: #e5e7eb;
    }
    h1 {
      margin: 0 0 4px 0;
      font-size: 22px;
    }
    .sub {
      margin-bottom: 12px;
      font-size: 13px;
      color: #9ca3af;
    }
    .top-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    select {
      background: #020617;
      color: #e5e7eb;
      border-radius: 8px;
      border: 1px solid #4b5563;
      padding: 4px 10px;
      font-size: 13px;
    }
    .charts-info {
      margin-bottom: 8px;
      font-size: 12px;
      color: #9ca3af;
    }
    .charts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }
    .chart-card {
      background: #111827;
      border-radius: 12px;
      padding: 10px 12px 12px;
      border: 1px solid #1f2937;
      box-shadow: 0 12px 30px rgba(0,0,0,0.35);
    }
    .chart-title {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 2px;
    }
    .chart-sub {
      font-size: 11px;
      color: #9ca3af;
      margin-bottom: 6px;
    }
    canvas {
      width: 100% !important;
      height: 200px !important;
    }
    .muted {
      font-size: 12px;
      color: #9ca3af;
    }
  </style>
</head>
<body>
  <div class="top-bar">
    <div>
      <h1>Realtime Monitor Dashboard</h1>
      <div class="sub">Streaming from Kafka topic <code>monitor_metrics</code></div>
    </div>
    <div>
      <label for="hostSelect" class="muted">Host: </label>
      <select id="hostSelect"></select>
    </div>
  </div>

  <div id="chartsInfo" class="charts-info"></div>
  <div id="chartsContainer" class="charts-grid"></div>

  <script>
    const hostSelect = document.getElementById('hostSelect');
    const chartsContainer = document.getElementById('chartsContainer');
    const chartsInfo = document.getElementById('chartsInfo');

    let selectedHost = "";

    // groupName -> { chart, subElem }
    const charts = {};

    hostSelect.addEventListener('change', () => {
      selectedHost = hostSelect.value;
    });

    function sanitizeId(name) {
      return name.replace(/[^a-zA-Z0-9_-]/g, "_");
    }

    function createChartIfNeeded(groupName) {
      if (charts[groupName]) {
        return charts[groupName];
      }

      const card = document.createElement('div');
      card.className = 'chart-card';

      const title = document.createElement('div');
      title.className = 'chart-title';
      title.textContent = groupName;

      const sub = document.createElement('div');
      sub.className = 'chart-sub';
      sub.textContent = "Last 15 values";  // will include unit later

      const canvas = document.createElement('canvas');
      canvas.id = "chart_" + sanitizeId(groupName);

      card.appendChild(title);
      card.appendChild(sub);
      card.appendChild(canvas);
      chartsContainer.appendChild(card);

      const ctx = canvas.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: []   // we add datasets dynamically
        },
        options: {
          animation: false,
          plugins: {
            legend: {
              labels: { color: '#e5e7eb', font: { size: 11 } }
            }
          },
          scales: {
            x: {
              ticks: {
                display: false  // no time labels
              },
              grid: { display: false }
            },
            y: {
              ticks: {
                color: '#9ca3af',
                font: { size: 10 }
              },
              grid: {
                color: 'rgba(31,41,55,0.6)'
              }
            }
          }
        }
      });

      charts[groupName] = { chart, subElem: sub };
      return charts[groupName];
    }

    function updateChart(groupName, unit, seriesMap) {
      const { chart, subElem } = createChartIfNeeded(groupName);

      // update subtitle with unit
      if (unit) {
        subElem.textContent = `Last 15 values (${unit})`;
      } else {
        subElem.textContent = "Last 15 values";
      }

      // max length among all series
      let maxLen = 0;
      for (const vals of Object.values(seriesMap)) {
        if (vals.length > maxLen) maxLen = vals.length;
      }
      chart.data.labels = Array(maxLen).fill(""); // no actual x labels

      const datasets = chart.data.datasets;

      function getDatasetIndex(label) {
        return datasets.findIndex(d => d.label === label);
      }

      // update or create datasets
      for (const [seriesName, vals] of Object.entries(seriesMap)) {
        const idx = getDatasetIndex(seriesName);
        if (idx === -1) {
          datasets.push({
            label: seriesName,
            data: vals,
            borderWidth: 2,
            tension: 0.3
          });
        } else {
          datasets[idx].data = vals;
        }
      }

      chart.update();
    }

    async function fetchData() {
      try {
        const resp = await fetch('/api/metrics');
        const data = await resp.json();
        const hosts = data.hosts || {};

        const hostNames = Object.keys(hosts);
        if (hostNames.length === 0) {
          hostSelect.innerHTML = "";
          chartsInfo.textContent = "";
          chartsContainer.innerHTML = "<div class='muted'>Waiting for metrics...</div>";
          return;
        }

        // pick / keep selected host
        if (!selectedHost || !hostNames.includes(selectedHost)) {
          selectedHost = hostNames[0];
        }

        // populate host dropdown
        hostSelect.innerHTML = "";
        for (const h of hostNames) {
          const opt = document.createElement('option');
          opt.value = h;
          opt.textContent = h;
          if (h === selectedHost) opt.selected = true;
          hostSelect.appendChild(opt);
        }

        const hostData = hosts[selectedHost];
        if (!hostData || !hostData.metrics) {
          chartsInfo.textContent = "";
          chartsContainer.innerHTML = "<div class='muted'>No metrics yet for this host.</div>";
          return;
        }

        const metrics = hostData.metrics;

        // Group by base metric (before first dot)
        const groups = {};
        for (const [metricName, meta] of Object.entries(metrics)) {
          const parts = metricName.split(".");
          const groupName = parts[0];
          const seriesName = parts.length > 1 ? parts[1] : parts[0];

          if (!groups[groupName]) {
            groups[groupName] = {
              unit: meta.unit || "",
              series: {}
            };
          }
          const vals = (meta.values || []).slice(-15);
          groups[groupName].series[seriesName] = vals;
        }

        const groupNames = Object.keys(groups);
        chartsInfo.textContent = `Host: ${selectedHost} · ${groupNames.length} chart(s)`;

        // update/create charts
        for (const gName of groupNames) {
          const g = groups[gName];
          updateChart(gName, g.unit, g.series);
        }
      } catch (err) {
        console.error("Error fetching metrics:", err);
      }
    }

    setInterval(fetchData, 1000);
    fetchData();
  </script>
</body>
</html>
    """
    return HTMLResponse(html)


@app.get("/api/metrics", response_class=JSONResponse)
def api_metrics():
    """
    Returns:
    {
      "hosts": {
        "hostname": {
          "metrics": {
            "cpu": {
              "values": [...],
              "avg": ...,
              "max": ...,
              "latest": ...,
              "unit": "%"
            },
            "diskio.read": { ... "unit": "kB/s" },
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


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    uvicorn.run(app, host="0.0.0.0", port=8003)


if __name__ == "__main__":
    main()
