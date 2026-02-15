"""REST API for Project Lend donation data.

Endpoints:
    GET /donations          — all donation records
    GET /donations/recent   — last N records (default 10, ?limit=N)
    GET /stats              — summary stats for frontend dashboard

Usage:
    python api.py                   # runs on port 5000
    python api.py --port 8080       # custom port
"""

import argparse
import os
import time
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import donations
from runtime_state import read_pipeline_state, LATEST_FRAME_PATH

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend API")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print(f"Starting API on http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=True)
