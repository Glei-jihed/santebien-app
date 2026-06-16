import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


async def main() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/api/health")
        summary = await client.get("/api/monitoring/summary")
        metrics = await client.get("/metrics")

    if summary.status_code != 200:
        raise SystemExit(f"Monitoring summary failed: {summary.status_code}")
    if metrics.status_code != 200:
        raise SystemExit(f"Prometheus metrics failed: {metrics.status_code}")
    text = metrics.text
    required = [
        "santebien_requests_total",
        "santebien_request_latency_average_ms",
        "santebien_co2_total_kg",
        "santebien_model_size_bytes",
        "santebien_model_size_reduction_percent",
    ]
    missing = [name for name in required if name not in text]
    if missing:
        raise SystemExit(f"Monitoring metrics missing: {', '.join(missing)}")

    data = summary.json()
    if data["model"]["size_reduction_percent"] < 70:
        raise SystemExit("Model monitoring size reduction is below green threshold")

    print("MONITORING OK")
    print(f"- Requests observed: {data['requests_total']}")
    print(f"- Average latency: {data['average_latency_ms']} ms")
    print(f"- Model INT8 reduction: {data['model']['size_reduction_percent']}%")


if __name__ == "__main__":
    asyncio.run(main())
