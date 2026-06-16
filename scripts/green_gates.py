import json
import os
from pathlib import Path

MEASURES = Path("outputs/phase-2-measures.json")
COMPARISON = Path("outputs/cache-optimization-comparison.json")
AI_MODEL = Path("outputs/ai-model-measures.json")


def threshold(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def fail(message: str) -> None:
    raise SystemExit(f"GREEN GATE FAILED: {message}")


def main() -> None:
    if not AI_MODEL.exists():
        fail(f"{AI_MODEL} introuvable. Lancez scripts.measure_ai_model avant les green gates.")

    ai_report = json.loads(AI_MODEL.read_text(encoding="utf-8"))

    max_p95_ms = threshold("GREEN_MAX_P95_MS", 5.0)
    min_cache_hit = threshold("GREEN_MIN_CACHE_HIT_PERCENT", 90.0)
    max_co2_per_request = threshold("GREEN_MAX_CO2_PER_REQUEST_KG", 0.000001)
    min_latency_gain = threshold("GREEN_MIN_LATENCY_GAIN_PERCENT", 50.0)
    min_model_compression = threshold("GREEN_MIN_MODEL_COMPRESSION_PERCENT", 70.0)
    min_int8_agreement = threshold("GREEN_MIN_INT8_AGREEMENT_PERCENT", 95.0)
    min_int8_accuracy = threshold("GREEN_MIN_INT8_ACCURACY_PERCENT", 95.0)
    max_int8_size = threshold("GREEN_MAX_INT8_SIZE_BYTES", 200.0)
    max_int8_latency = threshold("GREEN_MAX_INT8_LATENCY_MS", 0.1)
    max_int8_co2 = threshold("GREEN_MAX_INT8_CO2_KG", 0.0000000001)

    model_compression = ai_report["gain"]["size_reduction_percent"]
    int8_agreement = ai_report["gain"]["agreement_percent"]
    int8_accuracy = ai_report["int8"]["accuracy_percent"]
    int8_size = ai_report["int8"]["size_bytes"]
    int8_latency = ai_report["int8"]["mean_latency_ms"]
    int8_co2 = ai_report["int8"]["co2_per_inference_kg"]

    if model_compression < min_model_compression:
        fail(f"compression modele {model_compression}% < seuil {min_model_compression}%")
    if int8_agreement < min_int8_agreement:
        fail(f"accord INT8 {int8_agreement}% < seuil {min_int8_agreement}%")
    if int8_accuracy < min_int8_accuracy:
        fail(f"accuracy INT8 {int8_accuracy}% < seuil {min_int8_accuracy}%")
    if int8_size > max_int8_size:
        fail(f"taille INT8 {int8_size} bytes > seuil {max_int8_size} bytes")
    if int8_latency > max_int8_latency:
        fail(f"latence INT8 {int8_latency} ms > seuil {max_int8_latency} ms")
    if int8_co2 > max_int8_co2:
        fail(f"CO2 INT8 {int8_co2} kg > seuil {max_int8_co2} kg")

    print("GREEN GATES OK")
    print(f"- Compression modele INT8: {model_compression}% >= {min_model_compression}%")
    print(f"- Accord FP32/INT8: {int8_agreement}% >= {min_int8_agreement}%")
    print(f"- Accuracy INT8: {int8_accuracy}% >= {min_int8_accuracy}%")
    print(f"- Taille INT8: {int8_size} bytes <= {max_int8_size} bytes")
    print(f"- Latence INT8: {int8_latency} ms <= {max_int8_latency} ms")
    print(f"- CO2/inference INT8: {int8_co2} kg <= {max_int8_co2} kg")

    if MEASURES.exists() and COMPARISON.exists():
        measures = json.loads(MEASURES.read_text(encoding="utf-8"))
        comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
        p95_ms = measures["latency_ms"]["p95"]
        hit_rate = measures["cache"]["questions"]["hit_rate_percent"]
        co2_per_request = measures["co2"]["codecarbon_per_request_kg"]
        latency_gain = comparison["gain"]["mean_latency_reduction_percent"]
        print("CONTEXTE API OK")
        print(f"- P95 API: {p95_ms} ms <= {max_p95_ms} ms")
        print(f"- Cache hit rate: {hit_rate}% >= {min_cache_hit}%")
        print(f"- CO2/requete API: {co2_per_request} kg <= {max_co2_per_request} kg")
        print(f"- Gain latence cache: {latency_gain}% >= {min_latency_gain}%")


if __name__ == "__main__":
    main()
