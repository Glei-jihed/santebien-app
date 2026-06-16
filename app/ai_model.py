import math
import re
import unicodedata
from dataclasses import dataclass
from time import perf_counter


LABELS = ["prevention", "nutrition", "mental", "dermatologie", "respiratoire", "orientation"]
VOCABULARY = [
    "vaccin",
    "prevention",
    "sport",
    "sommeil",
    "fatigue",
    "alimentation",
    "poids",
    "diabete",
    "sucre",
    "stress",
    "angoisse",
    "deprime",
    "sommeil",
    "peau",
    "bouton",
    "rougeur",
    "eczema",
    "toux",
    "asthme",
    "respiration",
    "fievre",
    "douleur",
    "urgence",
    "medecin",
]

FP32_WEIGHTS = {
    "prevention": [1.8, 2.2, 1.5, 0.9, 0.4, 0.2, 0.1, 0.5, 0.1, 0.2, 0.0, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 0.1, 0.3, 0.2, 0.1, 0.4],
    "nutrition": [0.0, 0.2, 0.6, 0.3, 0.4, 2.4, 1.7, 1.6, 1.9, 0.2, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.0, 0.1],
    "mental": [0.0, 0.2, 0.3, 1.1, 0.8, 0.0, 0.1, 0.0, 0.0, 2.5, 2.4, 2.1, 1.2, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.2, 0.0, 0.4, 0.2, 0.3],
    "dermatologie": [0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 2.4, 2.1, 1.9, 2.2, 0.0, 0.0, 0.0, 0.1, 0.4, 0.1, 0.2],
    "respiratoire": [0.0, 0.1, 0.1, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 2.2, 2.4, 1.5, 0.6, 0.8, 0.7],
    "orientation": [0.2, 0.3, 0.1, 0.2, 0.6, 0.1, 0.1, 0.2, 0.1, 0.5, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2, 0.2, 0.5, 0.3, 0.4, 0.8, 1.4, 2.1, 2.3],
}
FP32_BIAS = {
    "prevention": -0.7,
    "nutrition": -0.6,
    "mental": -0.8,
    "dermatologie": -0.7,
    "respiratoire": -0.7,
    "orientation": -0.4,
}
QUANTIZATION_SCALE = 20
RED_FLAGS = {
    "douleur thoracique",
    "respire plus",
    "difficulte respirer",
    "perte de connaissance",
    "suicide",
    "sang",
    "paralysie",
    "urgence",
}


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    scores: dict[str, float]
    latency_ms: float


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9\s-]", " ", ascii_text)


def vectorize(text: str) -> list[int]:
    normalized = normalize_text(text)
    return [1 if token in normalized else 0 for token in VOCABULARY]


def quantize(value: float) -> int:
    return max(-128, min(127, round(value * QUANTIZATION_SCALE)))


INT8_WEIGHTS = {label: [quantize(value) for value in weights] for label, weights in FP32_WEIGHTS.items()}
INT8_BIAS = {label: quantize(value) for label, value in FP32_BIAS.items()}


def softmax(scores: dict[str, float]) -> dict[str, float]:
    max_score = max(scores.values())
    exp_scores = {label: math.exp(score - max_score) for label, score in scores.items()}
    total = sum(exp_scores.values())
    return {label: value / total for label, value in exp_scores.items()}


def predict(text: str, mode: str = "int8") -> Prediction:
    started = perf_counter()
    features = vectorize(text)
    if mode == "fp32":
        scores = {
            label: FP32_BIAS[label] + sum(weight * feature for weight, feature in zip(weights, features))
            for label, weights in FP32_WEIGHTS.items()
        }
    else:
        scores = {
            label: (INT8_BIAS[label] + sum(weight * feature for weight, feature in zip(weights, features)))
            / QUANTIZATION_SCALE
            for label, weights in INT8_WEIGHTS.items()
        }
    probabilities = softmax(scores)
    label = max(probabilities, key=probabilities.get)
    return Prediction(label=label, confidence=probabilities[label], scores=scores, latency_ms=(perf_counter() - started) * 1000)


def model_size(mode: str) -> int:
    weights_count = len(LABELS) * len(VOCABULARY)
    bias_count = len(LABELS)
    if mode == "fp32":
        return (weights_count + bias_count) * 4
    scale_metadata_bytes = 4
    return weights_count + bias_count + scale_metadata_bytes


def detect_red_flags(text: str) -> list[str]:
    normalized = normalize_text(text)
    return sorted(flag for flag in RED_FLAGS if flag in normalized)


def analyze_question(title: str, description: str, tags: list[str] | None = None, mode: str = "int8") -> dict:
    tags = tags or []
    full_text = " ".join([title, description, " ".join(tags)])
    prediction = predict(full_text, mode=mode)
    red_flags = detect_red_flags(full_text)
    urgency = "urgent_consultation" if red_flags else "normal_discussion"
    fp32_size = model_size("fp32")
    int8_size = model_size("int8")
    compression = round((1 - int8_size / fp32_size) * 100, 2)
    return {
        "category": prediction.label,
        "confidence": round(prediction.confidence, 4),
        "urgency": urgency,
        "red_flags": red_flags,
        "suggested_tags": sorted(set(tags + [prediction.label]))[:5],
        "latency_ms": round(prediction.latency_ms, 4),
        "model": {
            "name": "santebien-mini-orientation",
            "mode": mode,
            "purpose": "classification non diagnostique des questions",
            "fp32_size_bytes": fp32_size,
            "int8_size_bytes": int8_size,
            "compression_percent": compression,
            "features": len(VOCABULARY),
            "classes": len(LABELS),
        },
        "disclaimer": "Ce modèle ne fournit aucun diagnostic médical. En cas de symptôme grave, il faut contacter un professionnel de santé ou les urgences.",
    }
