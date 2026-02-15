"""Test pipeline: live ArduCam feed + Claude classify + robot sort.

Runs headless (no OpenCV window). Camera feed is served to the React
frontend via the MJPEG endpoint in api.py.

Modes:
  --auto       Motion detection triggers capture automatically
  (default)    Press ENTER in the terminal to capture + classify + sort

Publishes:
- latest_frame.jpg  (for frontend camera panel)
- pipeline_state.json (for frontend mode + latest Claude result)
"""

import argparse
import os
import sys
import threading
import time
import cv2
import numpy as np

from lend import PROJECT_ROOT
from lend.vision.classifier import classify_frame_detailed
from lend.hardware import arm_control
from lend.data import donations
from lend.hardware.positions import HOME
from lend.data.runtime_state import write_pipeline_state, LATEST_FRAME_PATH

IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ── Motion detection tuning ──────────────────────────────────────────────────
MOTION_THRESHOLD = 30        # pixel intensity change to count as motion
MOTION_MIN_AREA  = 5000      # minimum contour area (px²)
SETTLE_TIME      = 1.5       # seconds after motion stops before classifying
COOLDOWN         = 5.0       # seconds after a sort before watching again
WARMUP_FRAMES    = 60        # frames to skip for camera auto-exposure
# ─────────────────────────────────────────────────────────────────────────────

camera_lock = threading.Lock()
current_frame = None
running = True
status_text = "Idle - press SPACE to capture"
processing = False
latest_result = None
_use_arm = True


def _set_state(mode: str, text: str, result=None):
    write_pipeline_state({
        "mode": mode,
        "status_text": text,
        "last_result": result,
    })


def camera_capture_loop(camera_index: int):
    """Capture frames continuously in background and publish latest frame for frontend."""
    global current_frame, running
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Cannot open camera {camera_index}")
        _set_state("error", f"Cannot open camera {camera_index}")
        running = False
        return

    print(f"Camera {camera_index} capture thread started")
    _set_state("streaming", "Camera live - waiting for SPACE capture")

    last_frame_save = 0.0
    while running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.02)
            continue
        
        # Enhance brightness for better visibility
        frame = cv2.convertScaleAbs(frame, alpha=1.3, beta=20)
        
        with camera_lock:
            current_frame = frame
        now = time.time()
        if now - last_frame_save >= 0.033:  # ~30 FPS for smooth continuous feed
            cv2.imwrite(LATEST_FRAME_PATH, frame)
            last_frame_save = now
    cap.release()


def process_snapshot(frame):
    """Run Claude classification + logging + sorting in background."""
    global status_text, processing, latest_result
    try:
        status_text = "Sending snapshot to Claude..."
        _set_state("processing", status_text, None)
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            print("Failed to encode frame.")
            status_text = "Encode failed"
            _set_state("error", status_text, None)
            return

        info = classify_frame_detailed(buf.tobytes())
        category = info["category"]

        print("=" * 40)
        print(f"  CATEGORY : {category.upper()}")
        print(f"  ITEM     : {info.get('item_name', 'unknown')}")
        print(f"  WEIGHT   : {info.get('estimated_weight_lbs', '?')} lbs")
        print(f"  EXPIRY   : {info.get('estimated_expiry', 'N/A')}")
        print("=" * 40)

        status_text = f"Classified: {category} | Logging donation..."
        img_name = f"donation_{len(donations.get_all()) + 1}.jpg"
        img_path = os.path.join(IMAGES_DIR, img_name)
        cv2.imwrite(img_path, frame)

        record = donations.log_donation(
            category=category,
            item_name=info.get("item_name", "unknown"),
            estimated_weight_lbs=info.get("estimated_weight_lbs"),
            estimated_expiry=info.get("estimated_expiry"),
            image_path=img_path,
        )
        print(f"  Logged donation #{record['id']}")

        latest_result = {
            "donation_id": record["id"],
            "category": category,
            "item_name": info.get("item_name", "unknown"),
            "estimated_weight_lbs": info.get("estimated_weight_lbs"),
            "estimated_expiry": info.get("estimated_expiry"),
            "image_path": img_path,
        }

        # Frontend should now switch off camera and show formatted Claude result.
        if _use_arm:
            status_text = f"Sorting to {category} bin..."
            _set_state("classified", status_text, latest_result)
            arm_control.sort_to_bin(category)
            print("Sort complete!")
        else:
            print("(no-arm mode — skipping sort)")
        status_text = "Done - press SPACE to capture next item"
        _set_state("classified", status_text, latest_result)
    except Exception as e:
        print(f"Processing error: {e}")
        status_text = f"Error: {e}"
        _set_state("error", status_text, latest_result)
    finally:
        processing = False


def detect_motion(gray_prev, gray_curr):
    """Return True + largest contour area if significant motion is detected."""
    diff = cv2.absdiff(gray_prev, gray_curr)
    _, thresh = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = max((cv2.contourArea(c) for c in contours), default=0)
    return max_area >= MOTION_MIN_AREA, max_area


def auto_detection_loop():
    """Motion-detection loop: WARMUP → WATCHING → SETTLING → CLASSIFYING → COOLDOWN."""
    global running, processing, status_text, latest_result

    print("[AUTO] Motion detection active.")
    _set_state("streaming", "Warming up camera...")

    prev_gray = None
    frame_count = 0
    motion_stopped_at = None
    state = "WARMUP"

    while running:
        with camera_lock:
            frame = None if current_frame is None else current_frame.copy()
        if frame is None:
            time.sleep(0.02)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        frame_count += 1

        if state == "WARMUP":
            if frame_count >= WARMUP_FRAMES:
                prev_gray = gray.copy()
                state = "WATCHING"
                _set_state("streaming", "Watching for item...")
                print("[STATE] WATCHING – waiting for item...")

        elif state == "WATCHING":
            motion, area = detect_motion(prev_gray, gray)
            if motion:
                state = "SETTLING"
                motion_stopped_at = None
                _set_state("streaming", f"Item detected, settling... (area={area})")
                print(f"[STATE] SETTLING – motion detected (area={area})")
            prev_gray = gray.copy()

        elif state == "SETTLING":
            motion, area = detect_motion(prev_gray, gray)
            if motion:
                motion_stopped_at = None
            else:
                if motion_stopped_at is None:
                    motion_stopped_at = time.time()
                elif time.time() - motion_stopped_at >= SETTLE_TIME:
                    if not processing:
                        processing = True
                        snap = frame.copy()
                        print("[STATE] CLASSIFYING – sending frame to Claude...")
                        _set_state("processing", "Classifying with Claude...")
                        threading.Thread(target=process_snapshot, args=(snap,), daemon=True).start()
                    state = "COOLDOWN"
                    cooldown_start = time.time()
            prev_gray = gray.copy()

        elif state == "COOLDOWN":
            remaining = max(0, COOLDOWN - (time.time() - cooldown_start))
            if remaining <= 0:
                prev_gray = gray.copy()
                state = "WATCHING"
                _set_state("streaming", "Watching for item...")
                print("[STATE] WATCHING – ready for next item...")

        time.sleep(0.02)  # ~50 FPS check rate


def main(camera_index: int = 0, use_arm: bool = True, auto: bool = False):
    global running, processing, status_text, latest_result, _use_arm
    _use_arm = use_arm

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first:")
        print('  $env:ANTHROPIC_API_KEY="sk-..."')
        _set_state("error", "ANTHROPIC_API_KEY is not set")
        raise SystemExit(1)

    if use_arm:
        print("Connecting to arm...")
        arm_control.connect()
        print("Moving to HOME, gripper open...")
        arm_control.move_to_pose(HOME)
        arm_control.gripper_open()
        print("Arm ready.\n")
    else:
        print("Running in no-arm mode (vision-only).\n")

    cam_thread = threading.Thread(target=camera_capture_loop, args=(camera_index,), daemon=True)
    cam_thread.start()

    # Wait for first frame
    t0 = time.time()
    while running and current_frame is None and (time.time() - t0) < 5:
        time.sleep(0.05)
    if not running or current_frame is None:
        print("Camera did not start.")
        _set_state("error", "Camera did not start", latest_result)
        running = False
        return

    print("Live feed is running (headless — view at http://localhost:5173).")

    if auto:
        print("Mode: AUTO (motion detection)\n")
        try:
            auto_detection_loop()
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupted by user")
    else:
        print("Controls: ENTER = capture+classify+sort | q + ENTER = quit\n")
        try:
            while running:
                line = input("> ").strip().lower()
                if line == "q":
                    print("Quitting...")
                    running = False
                    break
                with camera_lock:
                    frame = None if current_frame is None else current_frame.copy()
                if frame is None:
                    print("No frame available yet.")
                    continue
                if processing:
                    print("Already processing — wait for completion.")
                    continue
                processing = True
                snap = frame.copy()
                print("\n[CAPTURE] Snapshot taken. Classifying...")
                status_text = "Snapshot captured - processing..."
                _set_state("processing", status_text, latest_result)
                threading.Thread(target=process_snapshot, args=(snap,), daemon=True).start()
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupted by user")

    running = False
    _set_state("idle", "Pipeline stopped", latest_result)
    time.sleep(0.2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test pipeline")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (0=laptop, 1=ArduCam)")
    parser.add_argument("--no-arm", action="store_true", help="Vision-only mode (no arm)")
    parser.add_argument("--auto", action="store_true", help="Auto mode: motion detection triggers capture")
    args = parser.parse_args()
    main(args.camera, use_arm=not args.no_arm, auto=args.auto)
