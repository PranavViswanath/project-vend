"""Test pipeline: live ArduCam feed + SPACE snapshot + Claude classify + robot sort.

Runs headless (no OpenCV window). Camera feed is served to the React
frontend via the MJPEG endpoint in api.py.  Press ENTER in the terminal
to capture + classify + sort, or type 'q' + ENTER to quit.

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

from vision import classify_frame_detailed
import arm_control
import donations
from positions import HOME
from runtime_state import write_pipeline_state, LATEST_FRAME_PATH

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

camera_lock = threading.Lock()
current_frame = None
running = True
status_text = "Idle - press SPACE to capture"
processing = False
latest_result = None


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
        status_text = f"Sorting to {category} bin..."
        _set_state("classified", status_text, latest_result)
        arm_control.sort_to_bin(category)
        print("Sort complete!")
        status_text = "Done - press SPACE to capture next item"
        _set_state("classified", status_text, latest_result)
    except Exception as e:
        print(f"Processing error: {e}")
        status_text = f"Error: {e}"
        _set_state("error", status_text, latest_result)
    finally:
        processing = False


def main(camera_index: int = 0):
    global running, processing, status_text, latest_result

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first:")
        print('  $env:ANTHROPIC_API_KEY="sk-..."')
        _set_state("error", "ANTHROPIC_API_KEY is not set")
        raise SystemExit(1)

    print("Connecting to arm...")
    arm_control.connect()
    print("Moving to HOME, gripper open...")
    arm_control.move_to_pose(HOME)
    arm_control.gripper_open()
    print("Arm ready.\n")

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
    print("Controls: ENTER = capture+classify+sort | q + ENTER = quit\n")

    try:
        while running:
            line = input("> ").strip().lower()
            if line == "q":
                print("Quitting...")
                running = False
                break
            # Any other input (including empty ENTER) triggers a capture
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
    finally:
        running = False
        _set_state("idle", "Pipeline stopped", latest_result)
        time.sleep(0.2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test pipeline")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (0=laptop, 1=ArduCam)")
    args = parser.parse_args()
    main(args.camera)
