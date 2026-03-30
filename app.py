"""Audiogram Interpreter - Flask application."""

from __future__ import annotations

import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from PIL import Image
import io

load_dotenv()

from config import Config
from interpretation.models import AudiogramData, FullInterpretation, EarInterpretation, SpeechData, EarThresholds
from interpretation.indices import calculate_fh, calculate_fhi, calculate_air_bone_gaps
from interpretation.classifier import classify_degree, classify_type, classify_configuration
from interpretation.speech import interpret_speech
from interpretation.masking import detect_masking_errors
from interpretation.diagnosis import generate_diagnoses
from interpretation.report import generate_report

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE


MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "bmp": "image/bmp",
    "webp": "image/webp",
}


def get_extractor():
    """Get the appropriate extraction function based on config."""
    backend = Config.VISION_BACKEND
    if backend == "anthropic" and Config.ANTHROPIC_API_KEY:
        from extraction.claude_extractor import extract_audiogram_claude
        return extract_audiogram_claude
    elif Config.GEMINI_API_KEY:
        from extraction.gemini_extractor import extract_audiogram_gemini
        return extract_audiogram_gemini
    elif Config.ANTHROPIC_API_KEY:
        from extraction.claude_extractor import extract_audiogram_claude
        return extract_audiogram_claude
    else:
        return None


@app.route("/")
def index():
    has_vision = bool(Config.GEMINI_API_KEY or Config.ANTHROPIC_API_KEY)
    return render_template("index.html", has_vision=has_vision)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Accept an audiogram image and return full interpretation."""
    extractor = get_extractor()
    if extractor is None:
        return jsonify({
            "error": "No API key configured. Set GEMINI_API_KEY (free) or ANTHROPIC_API_KEY "
                     "in environment variables, or use Manual Entry mode."
        }), 400

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type: .{ext}. Use JPG, PNG, or similar."}), 400

    try:
        image_bytes = file.read()

        # Validate it's a real image
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()

        mime_type = MIME_MAP.get(ext, "image/jpeg")

        # Step 1: Extract data from image
        data = extractor(image_bytes, mime_type)

        # Step 2: Interpret
        result = run_interpretation(data)

        return jsonify(_serialize(result, data))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/interpret", methods=["POST"])
def interpret_manual():
    """Accept manually entered audiogram data and return interpretation.

    No API key needed - pure computation.
    """
    try:
        raw = request.get_json()
        if not raw:
            return jsonify({"error": "No data provided"}), 400

        data = _parse_manual_input(raw)
        result = run_interpretation(data)
        return jsonify(_serialize(result, data))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Interpretation failed: {str(e)}"}), 500


def _parse_manual_input(raw: dict) -> AudiogramData:
    """Parse manual input JSON into AudiogramData."""
    data = AudiogramData()
    data.extraction_confidence = "high"
    data.extraction_notes = ["Data entered manually"]

    pt = raw.get("pure_tone", {})
    sp = raw.get("speech", {})

    for side, ear_key in [("right", "right_ear"), ("left", "left_ear")]:
        ear_raw = pt.get(ear_key, {})
        ear = EarThresholds(side=side)
        ear.air_conduction = _parse_manual_thresholds(ear_raw.get("air_conduction", {}))
        ear.air_masked = _parse_manual_thresholds(ear_raw.get("air_masked", {}))
        ear.bone_conduction = _parse_manual_thresholds(ear_raw.get("bone_conduction", {}))
        ear.bone_masked = _parse_manual_thresholds(ear_raw.get("bone_masked", {}))

        if side == "right":
            data.right_ear = ear
        else:
            data.left_ear = ear

    for side, ear_key in [("right", "right_ear"), ("left", "left_ear")]:
        sp_raw = sp.get(ear_key, {})
        speech = SpeechData(
            side=side,
            srt=_safe_float(sp_raw.get("srt")),
            max_discrimination=_safe_float(sp_raw.get("max_discrimination")),
            db_at_max_discrimination=_safe_float(sp_raw.get("db_at_max_discrimination")),
            discrimination_at_highest_level=_safe_float(sp_raw.get("discrimination_at_highest_level")),
            db_at_highest_level=_safe_float(sp_raw.get("db_at_highest_level")),
        )
        if side == "right":
            data.right_speech = speech
        else:
            data.left_speech = speech

    return data


def _parse_manual_thresholds(raw: dict) -> dict[int, float | None]:
    result = {}
    for freq_str, value in raw.items():
        try:
            freq = int(freq_str)
            if value is not None and value != "":
                result[freq] = float(value)
        except (ValueError, TypeError):
            continue
    return result


def _safe_float(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def run_interpretation(data: AudiogramData) -> FullInterpretation:
    """Run the full interpretation pipeline on extracted audiogram data."""
    interp = FullInterpretation(
        extraction_confidence=data.extraction_confidence,
        extraction_notes=data.extraction_notes,
    )

    # Per-ear interpretation
    for ear_data, speech_data, side in [
        (data.right_ear, data.right_speech, "right"),
        (data.left_ear, data.left_speech, "left"),
    ]:
        ear_interp = EarInterpretation(side=side)

        # Indices
        ear_interp.fh = calculate_fh(ear_data)
        ear_interp.fhi = calculate_fhi(ear_data)

        # Classification
        ear_interp.degree = classify_degree(ear_interp.fh)
        ear_interp.loss_type = classify_type(ear_data)
        ear_interp.configuration = classify_configuration(ear_data)

        # Air-bone gaps
        ear_interp.air_bone_gaps = calculate_air_bone_gaps(ear_data)
        if ear_interp.air_bone_gaps:
            gaps = [v for v in ear_interp.air_bone_gaps.values() if v is not None]
            ear_interp.avg_air_bone_gap = round(sum(gaps) / len(gaps), 1) if gaps else None

        # Store thresholds for display (prefer masked)
        ear_interp.ac_thresholds = _get_display_thresholds(ear_data, "ac")
        ear_interp.bc_thresholds = _get_display_thresholds(ear_data, "bc")

        # Speech
        ear_interp.srt = speech_data.srt
        ear_interp.max_discrimination = speech_data.max_discrimination
        speech_result = interpret_speech(speech_data, ear_interp.fh)
        ear_interp.srt_fh_concordance = speech_result["srt_fh_concordance"]
        ear_interp.discrimination_rating = speech_result["discrimination_rating"]
        ear_interp.rollover_index = speech_result["rollover_index"]

        if side == "right":
            interp.right = ear_interp
        else:
            interp.left = ear_interp

    # Masking errors
    right_errors, left_errors = detect_masking_errors(data)
    interp.right.masking_errors = right_errors
    interp.left.masking_errors = left_errors

    # Bilateral notes
    interp.bilateral_notes = _generate_bilateral_notes(data, interp)

    # Diagnoses
    interp.diagnoses = generate_diagnoses(interp, data)

    # Dutch clinical report
    interp.report = generate_report(interp)

    return interp


def _get_display_thresholds(ear_data, conduction_type: str) -> dict[int, float | None]:
    result = {}
    if conduction_type == "ac":
        for freq in Config.ALL_FREQUENCIES:
            masked = ear_data.air_masked.get(freq)
            unmasked = ear_data.air_conduction.get(freq)
            result[freq] = masked if masked is not None else unmasked
    else:
        for freq in Config.ALL_FREQUENCIES:
            masked = ear_data.bone_masked.get(freq)
            unmasked = ear_data.bone_conduction.get(freq)
            result[freq] = masked if masked is not None else unmasked
    return result


def _generate_bilateral_notes(data: AudiogramData, interp: FullInterpretation) -> list[str]:
    notes = []

    from interpretation.indices import best_ac_threshold
    for freq in [500, 1000, 2000, 4000]:
        r = best_ac_threshold(data.right_ear, freq)
        l = best_ac_threshold(data.left_ear, freq)
        if r is not None and l is not None and abs(r - l) > 20:
            notes.append(
                f"Significant asymmetry at {freq} Hz: right={r:.0f} dB, left={l:.0f} dB "
                f"(difference: {abs(r - l):.0f} dB). Consider MRI to rule out retrocochlear pathology."
            )
            break

    for side_interp in [interp.right, interp.left]:
        speech_result = interpret_speech(
            data.right_speech if side_interp.side == "right" else data.left_speech,
            side_interp.fh,
        )
        notes.extend(speech_result["notes"])

    return notes


def _serialize(interp: FullInterpretation, data: AudiogramData) -> dict:
    def ear_dict(ear: EarInterpretation) -> dict:
        return {
            "side": ear.side,
            "fh": ear.fh,
            "fhi": ear.fhi,
            "degree": ear.degree,
            "loss_type": ear.loss_type,
            "configuration": ear.configuration,
            "ac_thresholds": {str(k): v for k, v in ear.ac_thresholds.items()},
            "bc_thresholds": {str(k): v for k, v in ear.bc_thresholds.items()},
            "air_bone_gaps": {str(k): v for k, v in ear.air_bone_gaps.items()},
            "srt": ear.srt,
            "max_discrimination": ear.max_discrimination,
            "srt_fh_concordance": ear.srt_fh_concordance,
            "discrimination_rating": ear.discrimination_rating,
            "rollover_index": ear.rollover_index,
            "avg_air_bone_gap": ear.avg_air_bone_gap,
            "masking_errors": ear.masking_errors,
        }

    return {
        "report": interp.report,
        "right": ear_dict(interp.right),
        "left": ear_dict(interp.left),
        "diagnoses": [
            {"name": d.name, "reasoning": d.reasoning, "confidence": d.confidence}
            for d in interp.diagnoses
        ],
        "bilateral_notes": interp.bilateral_notes,
        "extraction_confidence": interp.extraction_confidence,
        "extraction_notes": interp.extraction_notes,
        "metadata": data.metadata,
    }


@app.route("/api/health")
def health():
    has_vision = bool(Config.GEMINI_API_KEY or Config.ANTHROPIC_API_KEY)
    return jsonify({"status": "ok", "vision_available": has_vision,
                    "backend": Config.VISION_BACKEND if has_vision else "none"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
