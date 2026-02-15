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
import cv2
import threading
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import donations
import pipeline_state

app = Flask(__name__)
CORS(app)  # allow frontend to call from any origin

# Camera streaming globals
camera_lock = threading.Lock()
latest_frame = None
camera_thread = None
camera_running = False


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


@app.route("/state", methods=["GET"])
def state():
    """Get current pipeline state for real-time UI updates."""
    return jsonify(pipeline_state.get_state())


@app.route("/video_feed")
def video_feed():
    """MJPEG streaming endpoint for live camera feed."""
    return Response(
        generate_mjpeg(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def generate_mjpeg():
    """Generator function for MJPEG stream."""
    global latest_frame
    while True:
        with camera_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        # Encode frame as JPEG
        ret, jpeg = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        # Yield MJPEG frame
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        )


def camera_capture_thread(camera_index):
    """Background thread for continuous camera capture."""
    global latest_frame, camera_running

    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)  # Fallback without DirectShow

    if not cap.isOpened():
        print(f"❌ Failed to open camera {camera_index}")
        return

    print(f"✅ Camera {camera_index} opened for streaming")
    camera_running = True

    while camera_running:
        ret, frame = cap.read()
        if not ret:
            break

        with camera_lock:
            latest_frame = frame

    cap.release()
    print("Camera capture thread stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend API")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--camera", type=int, default=1, help="Camera index (default: 1 for ArduCam)")
    args = parser.parse_args()

    # Start camera capture in background thread
    camera_thread = threading.Thread(
        target=camera_capture_thread,
        args=(args.camera,),
        daemon=True
    )
    camera_thread.start()

    print(f"Starting API on http://localhost:{args.port}")
    print(f"Camera streaming from index {args.camera}")
    print(f"Video feed: http://localhost:{args.port}/video_feed")

    try:
        app.run(host="0.0.0.0", port=args.port, debug=True, use_reloader=False)
    finally:
        camera_running = False
        if camera_thread:
            camera_thread.join(timeout=2.0)
