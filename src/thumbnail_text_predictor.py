"""Estimate thumbnail click-through performance for overlay text.

This implements the "Thumbnail text predictor" roadmap item from
``INSTRUCTIONS.md``. It combines lightweight image statistics with textual
heuristics to approximate how readable and compelling a thumbnail's overlay text
might feel. The implementation deliberately stays local – it relies on
``Pillow`` to extract brightness, contrast, and edge density alongside simple
linguistic features (word count, emphasis, action verbs). Those signals feed a
small logistic model that outputs a normalised CTR score between ``0`` and
``1`` along with human-readable reasoning for the result.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import pathlib
import re
import string
from typing import Any, Dict, List

from PIL import Image, ImageFilter, ImageStat


ACTION_WORDS = {
    "build",
    "make",
    "design",
    "launch",
    "grow",
    "hack",
    "boost",
    "learn",
    "power",
    "save",
    "scale",
    "upgrade",
    "craft",
    "deploy",
}


@dataclasses.dataclass(slots=True)
class ThumbnailCTRPrediction:
    """Structured CTR estimate with supporting context."""

    score: float
    reasons: List[str]
    features: Dict[str, Any]


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _load_image_metrics(path: pathlib.Path) -> Dict[str, float]:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        gray = rgb.convert("L")
        stat = ImageStat.Stat(gray)
        mean = stat.mean[0]
        stddev = stat.stddev[0]
        contrast = min(stddev / 128.0, 1.0)
        brightness = mean / 255.0
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_density = min(edge_stat.mean[0] / 255.0, 1.0)

    brightness_alignment = max(0.0, 1.0 - abs(brightness - 0.6) / 0.6)
    return {
        "width": float(width),
        "height": float(height),
        "contrast": float(contrast),
        "brightness": float(brightness),
        "brightness_alignment": float(brightness_alignment),
        "edge_density": float(edge_density),
    }


def _text_focus_score(word_count: int) -> tuple[float, str]:
    if word_count == 0:
        return 0.1, "missing"
    if 2 <= word_count <= 4:
        return 0.85, "ideal"
    if word_count == 1:
        return 0.6, "short"
    if 5 <= word_count <= 6:
        return 0.45, "long"
    return 0.2, "long"


def _uppercase_balance_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    uppercase = sum(1 for char in letters if char.isupper())
    return uppercase / len(letters)


def _extract_text_metrics(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    words = [w for w in re.split(r"\s+", cleaned) if w]
    bare_words = [
        w.strip(string.punctuation) for w in words if w.strip(string.punctuation)
    ]
    word_count = len(bare_words)
    char_count = len(cleaned)
    avg_word_length = (
        sum(len(w) for w in bare_words) / word_count if word_count else 0.0
    )
    uppercase_ratio = _uppercase_balance_ratio(cleaned)
    punctuation_count = sum(1 for ch in cleaned if ch in string.punctuation)
    punctuation_density = min(1.0, punctuation_count / max(word_count, 1))
    action_hits = sum(1 for w in bare_words if w.lower() in ACTION_WORDS)
    action_ratio = action_hits / word_count if word_count else 0.0
    numbers_flag = 0.5 if any(ch.isdigit() for ch in cleaned) else 0.0

    length_penalty = 0.0
    if char_count > 48:
        length_penalty += 0.5
    if char_count > 32:
        length_penalty += 0.35

    punctuation_penalty = 0.0
    if punctuation_density > 0.45:
        punctuation_penalty = 0.5
    elif punctuation_density > 0.25:
        punctuation_penalty = 0.25

    focus_score, focus_category = _text_focus_score(word_count)

    if not bare_words:
        uppercase_balance_score = 0.3
        uppercase_category = "missing"
    elif 0.3 <= uppercase_ratio <= 0.8:
        uppercase_balance_score = 0.65
        uppercase_category = "balanced"
    else:
        uppercase_balance_score = 0.25
        uppercase_category = "imbalance"

    return {
        "text": cleaned,
        "word_count": word_count,
        "char_count": char_count,
        "avg_word_length": avg_word_length,
        "uppercase_ratio": uppercase_ratio,
        "uppercase_balance_score": uppercase_balance_score,
        "uppercase_category": uppercase_category,
        "punctuation_count": punctuation_count,
        "punctuation_density": punctuation_density,
        "punctuation_penalty": punctuation_penalty,
        "focus_score": focus_score,
        "focus_category": focus_category,
        "action_ratio": action_ratio,
        "action_hits": action_hits,
        "numbers_flag": numbers_flag,
        "length_penalty": length_penalty,
    }


def predict_ctr(image_path: pathlib.Path, text: str) -> ThumbnailCTRPrediction:
    image_metrics = _load_image_metrics(image_path)
    text_metrics = _extract_text_metrics(text)
    features = {**image_metrics, **text_metrics}

    z = -0.4
    z += image_metrics["contrast"] * 2.0
    z += image_metrics["edge_density"] * 1.5
    z += image_metrics["brightness_alignment"] * 1.0
    z += text_metrics["focus_score"] * 1.5
    z += text_metrics["uppercase_balance_score"] * 0.6
    z += text_metrics["action_ratio"] * 1.0
    z += text_metrics["numbers_flag"] * 0.4
    z -= text_metrics["length_penalty"] * 2.2
    z -= text_metrics["punctuation_penalty"] * 1.2

    score = _sigmoid(z)

    reasons: List[str] = []
    contrast = image_metrics["contrast"]
    if contrast >= 0.45:
        reasons.append("High contrast background helps text stand out.")
    elif contrast <= 0.25:
        reasons.append("Low contrast background could make text harder to read.")

    edge_density = image_metrics["edge_density"]
    if edge_density >= 0.25:
        reasons.append("Distinct edges give the eye something to lock onto.")
    elif edge_density <= 0.1:
        reasons.append(
            "Scene looks flat; consider adding texture or subject separation."
        )

    if image_metrics["brightness_alignment"] < 0.4:
        reasons.append(
            "Overall brightness skews very dark or bright; adjust exposure for clarity."
        )

    focus_category = text_metrics["focus_category"]
    word_count = text_metrics["word_count"]
    if focus_category == "ideal":
        reasons.append(f"Concise text ({word_count} words) keeps the hook readable.")
    elif focus_category == "short":
        reasons.append("Single-word text may benefit from an extra clarifier.")
    elif focus_category == "long":
        reasons.append(
            f"Text is lengthy ({word_count} words); trim to 3–4 words for fast scanning."
        )
    elif focus_category == "missing":
        reasons.append("No overlay text detected; add a punchy phrase.")

    if text_metrics["length_penalty"] > 0:
        reasons.append(
            f"Text is lengthy at {text_metrics['char_count']} characters; keep it under 32."
        )

    uppercase_category = text_metrics["uppercase_category"]
    if uppercase_category == "balanced":
        reasons.append("Mixed case lettering stays legible without feeling shouty.")
    elif uppercase_category == "imbalance":
        reasons.append(
            "Consider mixing upper and lower case; heavy caps can feel like shouting."
        )

    if text_metrics["action_hits"] > 0:
        reasons.append("Action verbs add urgency and promise value.")

    if text_metrics["numbers_flag"] > 0:
        reasons.append("Specific numbers make the promise feel concrete.")

    if text_metrics["punctuation_penalty"] >= 0.25:
        reasons.append("Multiple punctuation marks may feel noisy.")

    if not reasons:
        reasons.append("Prediction generated; adjust text and colours to improve CTR.")

    return ThumbnailCTRPrediction(score=score, reasons=reasons, features=features)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Estimate thumbnail CTR from overlay text and image cues",
    )
    parser.add_argument("image", type=pathlib.Path, help="Path to thumbnail image")
    parser.add_argument(
        "--text",
        required=True,
        help="Thumbnail overlay text to evaluate",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of formatted text",
    )
    args = parser.parse_args(argv)

    prediction = predict_ctr(args.image, args.text)
    if args.json:
        print(json.dumps(dataclasses.asdict(prediction), indent=2))
    else:
        print(f"Predicted CTR: {prediction.score:.1%}")
        for reason in prediction.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
