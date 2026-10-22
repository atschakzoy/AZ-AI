# Stage 09 — Decision-Support Solutions & Anomaly Detection

## What is this and why does it matter?

Decision-support solutions help systems automatically detect problems, flag unusual behaviour, and alert humans before issues become critical. The main service here is **Azure AI Anomaly Detector** — it analyses time-series data (metrics over time) and identifies points that don't fit the expected pattern.

The December 2025 AI-102 study guide merged this topic into other domains, but the exam readiness series still covers it as its own preparation area (10–15% of the exam in older versions). Questions about anomaly detection can still appear — know it.

---

## What you will learn

- What anomaly detection is and when to use it
- How Azure AI Anomaly Detector works
- Univariate vs multivariate detection
- Calling Anomaly Detector from Python
- Azure Metrics Advisor (built on Anomaly Detector)

---

## Part 1 — What is Anomaly Detection?

Anomaly detection identifies data points that are significantly different from expected behaviour in a time-series dataset.

**Examples:**
- A server's CPU usage is normally 40–60%. It spikes to 95% — anomaly.
- A website normally gets 500 requests/minute. It drops to 10 — anomaly.
- A temperature sensor reads 22°C every hour. One reading is 80°C — anomaly.

**Why AI and not just thresholds?**
- Thresholds are static — "alert if CPU > 80%"
- Anomaly detection is adaptive — it learns the expected pattern including seasonality, trends, and normal variance, then flags what genuinely doesn't fit

---

## Part 2 — Azure AI Anomaly Detector

A Foundry Tool (formerly Azure Cognitive Service) that analyses time-series data for anomalies.

**Two modes:**

| Mode | What it does | When to use |
|------|-------------|------------|
| **Univariate** | Analyses one metric over time | Single sensor, single KPI |
| **Multivariate** | Analyses many metrics together — detects anomalies that only appear when multiple signals are considered | Complex systems (e.g. a machine with 10 sensors that fail together) |

**Three detection types:**

| Type | What it does |
|------|-------------|
| **Entire series** | Analyses the whole historical dataset at once — good for batch analysis |
| **Last point** | Tells you whether the most recent data point is an anomaly — good for real-time streaming |
| **Change point detection** | Detects where the trend or baseline permanently changed |

---

## Part 3 — Calling Anomaly Detector from Python

```bash
pip install azure-ai-anomalydetector azure-identity
```

```python
import os
from datetime import datetime, timedelta
from azure.ai.anomalydetector import AnomalyDetectorClient
from azure.ai.anomalydetector.models import (
    UnivariateDetectionOptions,
    TimeSeriesPoint,
    TimeGranularity
)
from azure.identity import DefaultAzureCredential

client = AnomalyDetectorClient(
    endpoint=os.environ["ANOMALY_DETECTOR_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Build a time series — e.g. hourly CPU usage for 1 week
base_time = datetime(2026, 10, 1, 0, 0, 0)
series = [
    TimeSeriesPoint(timestamp=base_time + timedelta(hours=i), value=float(v))
    for i, v in enumerate([
        42, 45, 43, 44, 46, 43, 41, 44,  # day 1 — normal
        43, 45, 42, 44, 47, 43, 44, 42,  # day 2 — normal
        44, 43, 45, 41, 42, 44, 45, 43,  # day 3 — normal
        42, 95, 43, 44, 46, 43, 41, 44,  # day 4 — anomaly at hour 25
        43, 45, 42, 44, 47, 43, 44, 42,  # day 5 — normal
        44, 43, 45, 41, 42, 44, 45, 43,  # day 6 — normal
        42, 45, 43, 44, 4, 43, 41, 44,   # day 7 — anomaly (drop) at hour 52
    ])
]

request = UnivariateDetectionOptions(
    series=series,
    granularity=TimeGranularity.HOURLY,
    sensitivity=95   # 0–99: higher = more sensitive (detects more anomalies)
)

# Analyse entire series
result = client.detect_univariate_entire_series(request)

print(f"Expected values computed: {len(result.expected_values)}")
for i, (is_anomaly, value, expected) in enumerate(
    zip(result.is_anomaly, series, result.expected_values)
):
    if is_anomaly:
        timestamp = series[i].timestamp
        print(f"Anomaly at {timestamp}: value={value.value:.0f}, expected≈{expected:.0f}")
```

**Detect whether the latest point is anomalous (streaming/real-time):**

```python
from azure.ai.anomalydetector.models import UnivariateLastDetectionOptions

result = client.detect_univariate_last_point(
    UnivariateLastDetectionOptions(
        series=series,
        granularity=TimeGranularity.HOURLY
    )
)

print(f"Latest point is anomaly: {result.is_anomaly}")
print(f"Latest point severity: {result.severity}")  # 0 (none) to 1 (high)
print(f"Score: {result.score}")
```

---

## Part 4 — Multivariate Anomaly Detection

For systems where multiple metrics interact — e.g. a machine with temperature, pressure, and vibration sensors. An anomaly in one sensor might mean nothing, but anomalies in all three together signal failure.

```python
from azure.ai.anomalydetector.models import (
    MultivariateBatchDetectionOptions,
    VariableValues
)

# Train a multivariate model first (requires historical data in Blob Storage)
# Then detect anomalies on new data

request = MultivariateBatchDetectionOptions(
    data_source="https://mystorageaccount.blob.core.windows.net/data/metrics.csv",
    start_time=datetime(2026, 10, 1),
    end_time=datetime(2026, 10, 7),
    top_contributor_count=3   # how many variables contributed to each anomaly
)

poller = client.begin_detect_multivariate_batch_anomaly(
    model_id=trained_model_id,
    options=request
)
result = poller.result()

for anomaly in result.results:
    if anomaly.value.is_anomaly:
        print(f"Anomaly at {anomaly.timestamp}")
        for contributor in anomaly.value.interpretation:
            print(f"  Top contributor: {contributor.variable} ({contributor.contribution_score:.2%})")
```

---

## Part 5 — Azure Metrics Advisor

Metrics Advisor is a higher-level service built on top of Anomaly Detector. It adds:
- A web UI for configuring and monitoring metrics
- Automatic grouping of related anomalies into **incidents**
- Root cause analysis — which metric caused the cascade
- Alerting (email, Teams, webhook)

**When to use Anomaly Detector vs Metrics Advisor:**

| | Anomaly Detector | Metrics Advisor |
|--|----------------|----------------|
| Interface | API/SDK | Web UI + API |
| Alerting | You build it | Built-in |
| Incident grouping | No | Yes |
| Root cause analysis | No | Yes |
| Use case | Custom apps needing anomaly signals | Operations teams monitoring many metrics |

---

## Part 6 — Provisioning

```bash
# Anomaly Detector is a single-service resource
az cognitiveservices account create \
  --name anomaly-myapp-dev \
  --resource-group rg-ai-dev \
  --kind AnomalyDetector \
  --sku S0 \
  --location eastus
```

---

## AI-102 Exam Checklist — Decision-Support & Anomaly Detection

- [ ] What is anomaly detection and how does it differ from threshold-based alerting?
- [ ] What is the difference between univariate and multivariate detection?
- [ ] What are the three detection types (entire series, last point, change point)?
- [ ] What does the `sensitivity` parameter control?
- [ ] What does `severity` on a detected anomaly represent?
- [ ] What is the difference between Anomaly Detector and Metrics Advisor?
- [ ] When would you use multivariate vs univariate detection?

---

## Exercises

1. Create an Anomaly Detector resource. Generate 168 data points (7 days × 24 hours) of simulated CPU usage with 2–3 manually inserted spikes. Run entire-series detection and print all detected anomalies.
2. Run last-point detection on the same series. Manually change the last value to a spike and confirm it is detected.
3. Change the `sensitivity` from 50 to 95 and compare how many anomalies are detected. Explain why.
