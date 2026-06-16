import json
from pathlib import Path
from statistics import mean

from app.ai_model import analyze_question, model_size

ESTIMATED_SERVER_WATTS = 35
FRANCE_KG_CO2_PER_KWH = 0.052
RUNS_PER_SAMPLE = 250

SAMPLES = [
    {
        "title": "Comment mieux dormir et prévenir la fatigue ?",
        "description": "Je cherche une routine de sommeil simple avec prévention et sport doux.",
        "tags": ["sommeil"],
        "expected": "prevention",
    },
    {
        "title": "Alimentation et sucre avec diabète",
        "description": "Je veux comprendre comment adapter mon alimentation et réduire le sucre.",
        "tags": ["nutrition"],
        "expected": "nutrition",
    },
    {
        "title": "Stress et angoisse depuis plusieurs semaines",
        "description": "Je dors mal, je suis anxieux et je cherche des habitudes pour gérer le stress.",
        "tags": ["stress"],
        "expected": "mental",
    },
    {
        "title": "Rougeur sur la peau et eczéma",
        "description": "J'ai une rougeur et des boutons sur la peau, sans douleur forte.",
        "tags": ["peau"],
        "expected": "dermatologie",
    },
    {
        "title": "Toux et respiration difficile après effort",
        "description": "Je tousse souvent et ma respiration devient gênante quand je fais du sport.",
        "tags": ["toux"],
        "expected": "respiratoire",
    },
    {
        "title": "Douleur et besoin de voir un médecin",
        "description": "Je ne sais pas si je dois consulter un médecin rapidement pour cette douleur.",
        "tags": ["orientation"],
        "expected": "orientation",
    },
]


def co2_for_latency(mean_latency_ms: float) -> float:
    duration_seconds = mean_latency_ms / 1_000
    return ESTIMATED_SERVER_WATTS * duration_seconds / 3_600_000 * FRANCE_KG_CO2_PER_KWH


def evaluate(mode: str) -> dict:
    predictions = []
    latencies = []
    for sample in SAMPLES:
        result = analyze_question(sample["title"], sample["description"], sample["tags"], mode=mode)
        predictions.append(result["category"])
        for _ in range(RUNS_PER_SAMPLE):
            measured = analyze_question(sample["title"], sample["description"], sample["tags"], mode=mode)
            latencies.append(measured["latency_ms"])
    accuracy = sum(prediction == sample["expected"] for prediction, sample in zip(predictions, SAMPLES)) / len(SAMPLES)
    mean_latency = round(mean(latencies), 4)
    co2_per_inference = co2_for_latency(mean_latency)
    return {
        "size_bytes": model_size(mode),
        "accuracy_percent": round(accuracy * 100, 2),
        "mean_latency_ms": mean_latency,
        "co2_per_inference_kg": co2_per_inference,
        "co2_campaign_kg": co2_per_inference * len(latencies),
        "inferences_measured": len(latencies),
        "predictions": predictions,
    }


def main() -> None:
    fp32 = evaluate("fp32")
    int8 = evaluate("int8")
    agreement = sum(left == right for left, right in zip(fp32["predictions"], int8["predictions"])) / len(SAMPLES)
    report = {
        "scenario": "baseline modele FP32 vs optimisation INT8",
        "before": "fp32",
        "after": "int8",
        "samples": len(SAMPLES),
        "runs_per_sample": RUNS_PER_SAMPLE,
        "fp32": fp32,
        "int8": int8,
        "gain": {
            "size_reduction_percent": round((1 - int8["size_bytes"] / fp32["size_bytes"]) * 100, 2),
            "agreement_percent": round(agreement * 100, 2),
            "latency_delta_percent": round((int8["mean_latency_ms"] - fp32["mean_latency_ms"]) / fp32["mean_latency_ms"] * 100, 2),
            "co2_reduction_percent": round((1 - int8["co2_per_inference_kg"] / fp32["co2_per_inference_kg"]) * 100, 2),
        },
        "safety": "classification d'orientation uniquement, sans diagnostic medical",
    }
    output = Path("outputs/ai-model-measures.json")
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
