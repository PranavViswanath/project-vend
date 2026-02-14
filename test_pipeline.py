"""Test pipeline: live ArduCam feed + SPACE snapshot + Claude classify + robot sort.

Architecture:
- Camera capture runs in a background thread.
- OpenCV window + key handling run on the main thread (stable on Windows).
- Claude + logging + arm sorting run in a worker thread so video stays smooth.
"""

import argparse
import os
import threading
import time
import cv2

from vision import classify_frame_detailed
import arm_control
import donations
from positions import HOME

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

camera_lock = threading.Lock()
current_frame = None
running = True
status_text = "Idle - press SPACE to capture"
processing = False


def camera_capture_loop(camera_index: int):
    """Capture frames continuously in the background."""
    global current_frame, running
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Cannot open camera {camera_index}")
        running = False
        return

    print(f"Camera {camera_index} capture thread started")
    while running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.02)
            continue
        with camera_lock:
            current_frame = frame
    cap.release()


def process_snapshot(frame):
    """Run Claude classification + logging + sorting in background."""
    global status_text, processing
    try:
        status_text = "Sending snapshot to Claude..."
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            print("Failed to encode frame.")
            status_text = "Encode failed"
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

        status_text = f"Sorting to {category} bin..."
        arm_control.sort_to_bin(category)
        print("Sort complete!")
        status_text = "Done - press SPACE to capture next item"
    except Exception as e:
        print(f"Processing error: {e}")
        status_text = f"Error: {e}"
    finally:
        processing = False


def main(camera_index: int = 1):
    global running, processing, status_text

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first:")
        print('  $env:ANTHROPIC_API_KEY="sk-..."')
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
        running = False
        return

    print("Live feed is running.")
    print("Controls: SPACE capture+classify+sort, Q quit\n")

    try:
        while running:
            with camera_lock:
                frame = None if current_frame is None else current_frame.copy()
            if frame is None:
                time.sleep(0.01)
                continue

            display = frame.copy()
            cv2.putText(display, "ArduCam Feed - SPACE capture | Q quit",
                        (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display, status_text,
                        (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("ArduCam - Continuous Feed", display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Quitting...")
                running = False
                break
            if key == ord(" "):
                if processing:
                    print("Already processing a snapshot; wait for completion.")
                else:
                    processing = True
                    snap = frame.copy()
                    print("\n[SPACE] Snapshot captured. Starting classification...")
                    threading.Thread(target=process_snapshot, args=(snap,), daemon=True).start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        running = False
        time.sleep(0.2)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test pipeline")
    parser.add_argument("--camera", type=int, default=1, help="Camera index (1=ArduCam, 0=laptop)")
    args = parser.parse_args()
    main(args.camera)
