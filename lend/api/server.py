"""REST API for Project Lend donation data.

Endpoints:
    GET /donations          — all donation records
    GET /donations/recent   — last N records (default 10, ?limit=N)
    GET /stats              — summary stats for frontend dashboard
    GET /state              — current pipeline state (motion, classification, cooldown)
    GET /video_feed         — MJPEG camera stream

Usage:
    python api.py                   # runs on port 5000, camera 1
    python api.py --port 8080       # custom port
    python api.py --camera 0        # use laptop webcam
"""

import argparse
import os
import threading
import time
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
from lend import PROJECT_ROOT
from lend.data import donations
from lend.data.runtime_state import read_pipeline_state, write_pipeline_state, LATEST_FRAME_PATH
from lend.vision.classifier import classify_frame_detailed

IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

_capture_lock = threading.Lock()

app = Flask(__name__)
CORS(app)  # allow frontend to call from any origin


@app.route("/donations", methods=["GET"])
def all_donations():
    return jsonify(donations.get_all())


@app.route("/donations/recent", methods=["GET"])
def recent_donations():
    limit = request.args.get("limit", 10, type=int)
    records = donations.get_all()
    return jsonify(records[-limit:])


@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(donations.get_stats())


@app.route("/pipeline/state", methods=["GET"])
def pipeline_state():
    return jsonify(read_pipeline_state())


@app.route("/pipeline/frame", methods=["GET"])
def pipeline_frame():
    if not os.path.exists(LATEST_FRAME_PATH):
        return jsonify({"error": "no frame available"}), 404
    return send_file(LATEST_FRAME_PATH, mimetype="image/jpeg")


def _generate_mjpeg():
    """Yield MJPEG frames for smooth browser video."""
    last_data = None
    while True:
        if os.path.exists(LATEST_FRAME_PATH):
            try:
                with open(LATEST_FRAME_PATH, "rb") as f:
                    frame = f.read()
                # Only send valid JPEGs (starts with FFD8, ends with FFD9)
                if frame and frame[:2] == b'\xff\xd8' and frame[-2:] == b'\xff\xd9':
                    last_data = frame
            except Exception:
                pass
        if last_data:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + last_data + b"\r\n")
        time.sleep(0.033)  # ~30 FPS


@app.route("/pipeline/stream")
def pipeline_stream():
    """MJPEG stream for smooth live camera feed."""
    return Response(_generate_mjpeg(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/pipeline/capture", methods=["POST"])
def pipeline_capture():
    """Capture the current frame, classify with Claude, and log the donation."""
    if not _capture_lock.acquire(blocking=False):
        return jsonify({"error": "Capture already in progress"}), 409

    try:
        write_pipeline_state({
            "mode": "processing",
            "status_text": "Classifying with Claude...",
            "last_result": None,
        })

        if not os.path.exists(LATEST_FRAME_PATH):
            write_pipeline_state({
                "mode": "error",
                "status_text": "No camera frame available",
            })
            return jsonify({"error": "No frame available"}), 404

        with open(LATEST_FRAME_PATH, "rb") as f:
            frame_bytes = f.read()

        info = classify_frame_detailed(frame_bytes)
        category = info["category"]

        img_name = f"donation_{len(donations.get_all()) + 1}.jpg"
        img_path = os.path.join(IMAGES_DIR, img_name)
        with open(img_path, "wb") as f:
            f.write(frame_bytes)

        record = donations.log_donation(
            category=category,
            item_name=info.get("item_name", "unknown"),
            estimated_weight_lbs=info.get("estimated_weight_lbs"),
            estimated_expiry=info.get("estimated_expiry"),
            image_path=img_path,
        )

        result = {
            "donation_id": record["id"],
            "category": category,
            "item_name": info.get("item_name", "unknown"),
            "estimated_weight_lbs": info.get("estimated_weight_lbs"),
            "estimated_expiry": info.get("estimated_expiry"),
            "image_path": img_path,
        }

        write_pipeline_state({
            "mode": "classified",
            "status_text": f"Classified: {info.get('item_name', 'unknown')} ({category})",
            "last_result": result,
        })

        return jsonify(result)

    except Exception as e:
        write_pipeline_state({
            "mode": "error",
            "status_text": f"Classification error: {e}",
        })
        return jsonify({"error": str(e)}), 500

    finally:
        _capture_lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend API")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    print(f"Starting API on http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=True)
