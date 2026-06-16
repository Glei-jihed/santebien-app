from collections import defaultdict
from pathlib import Path
from threading import Lock

from app.ai_model import model_size

AI_MEASURES = Path("outputs/ai-model-measures.json")


class MonitoringRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self.requests_total = 0
        self.requests_by_status: dict[str, int] = defaultdict(int)
        self.total_latency_ms = 0.0
        self.total_co2_kg = 0.0
        self.max_latency_ms = 0.0

    def record_request(self, status_code: int, latency_ms: float, co2_kg: float) -> None:
        with self._lock:
            self.requests_total += 1
            self.requests_by_status[str(status_code)] += 1
            self.total_latency_ms += latency_ms
            self.total_co2_kg += co2_kg
            self.max_latency_ms = max(self.max_latency_ms, latency_ms)

    def snapshot(self) -> dict:
        with self._lock:
            average_latency = self.total_latency_ms / self.requests_total if self.requests_total else 0.0
            return {
                "requests_total": self.requests_total,
                "requests_by_status": dict(self.requests_by_status),
                "average_latency_ms": round(average_latency, 6),
                "max_latency_ms": round(self.max_latency_ms, 6),
                "total_co2_kg": self.total_co2_kg,
                "model": {
                    "fp32_size_bytes": model_size("fp32"),
                    "int8_size_bytes": model_size("int8"),
                    "size_reduction_percent": round((1 - model_size("int8") / model_size("fp32")) * 100, 2),
                },
            }

    def prometheus_text(self) -> str:
        data = self.snapshot()
        lines = [
            "# HELP santebien_requests_total Total HTTP requests observed by the app.",
            "# TYPE santebien_requests_total counter",
            f"santebien_requests_total {data['requests_total']}",
            "# HELP santebien_request_latency_average_ms Average request latency in milliseconds.",
            "# TYPE santebien_request_latency_average_ms gauge",
            f"santebien_request_latency_average_ms {data['average_latency_ms']}",
            "# HELP santebien_request_latency_max_ms Maximum request latency in milliseconds.",
            "# TYPE santebien_request_latency_max_ms gauge",
            f"santebien_request_latency_max_ms {data['max_latency_ms']}",
            "# HELP santebien_co2_total_kg Estimated total application CO2 in kilograms.",
            "# TYPE santebien_co2_total_kg counter",
            f"santebien_co2_total_kg {data['total_co2_kg']:.12f}",
            "# HELP santebien_model_size_bytes Model size by mode.",
            "# TYPE santebien_model_size_bytes gauge",
            f"santebien_model_size_bytes{{mode=\"fp32\"}} {data['model']['fp32_size_bytes']}",
            f"santebien_model_size_bytes{{mode=\"int8\"}} {data['model']['int8_size_bytes']}",
            "# HELP santebien_model_size_reduction_percent INT8 size reduction versus FP32.",
            "# TYPE santebien_model_size_reduction_percent gauge",
            f"santebien_model_size_reduction_percent {data['model']['size_reduction_percent']}",
        ]
        for status, count in sorted(data["requests_by_status"].items()):
            lines.append(f'santebien_requests_by_status_total{{status="{status}"}} {count}')
        return "\n".join(lines) + "\n"


monitoring = MonitoringRegistry()
