"""Project Lend – main pipeline.

Laptop webcam watches the pickup zone. When an item is detected (via motion /
frame-difference), the frame is sent to Claude for classification. The arm then
picks the item and drops it in the correct bin.

Usage:
    python main.py                 # default camera 0
    python main.py --camera 1      # use a different camera index
    python main.py --no-arm        # vision-only mode (skip arm sort)

Controls (OpenCV window):
    Q = quit
"""

import argparse
import os
import time
import cv2
import numpy as np

from vision import classify_frame_detailed
import arm_control
import donations
import pipeline_state
from positions import HOME

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ── Tuning knobs ──────────────────────────────────────────────────────────────
MOTION_THRESHOLD = 30        # pixel intensity change to count as motion
MOTION_MIN_AREA  = 5000      # minimum contour area (px²) to count as "item placed"
SETTLE_TIME      = 1.5       # seconds to wait after motion stops before classifying
COOLDOWN         = 5.0       # seconds after a sort before watching for the next item
WARMUP_FRAMES    = 60        # frames to skip at startup while camera auto-exposes
# ─────────────────────────────────────────────────────────────────────────────


def detect_motion(gray_prev, gray_curr):
    """Return True + largest contour area if significant motion is detected."""
    diff = cv2.absdiff(gray_prev, gray_curr)
    _, thresh = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = max((cv2.contourArea(c) for c in contours), default=0)
    return max_area >= MOTION_MIN_AREA, max_area


def main(camera_index: int = 1, use_arm: bool = True):  # Default to ArduCam
    # ── Camera setup ──────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: cannot open camera {camera_index}")
        print("Try: python main.py --camera 1")
        return

    # ── Arm setup ─────────────────────────────────────────────────────────────
    if use_arm:
        try:
            arm_control.connect()
            arm_control.move_to_pose(HOME)
            arm_control.gripper_open()
            print("Arm at HOME, gripper open – ready.")
        except Exception as e:
            print(f"Arm connection failed: {e}")
            print("Continuing in vision-only mode.")
            use_arm = False

    # ── State machine ─────────────────────────────────────────────────────────
    # States: WATCHING → SETTLING → CLASSIFYING → SORTING → COOLDOWN → WATCHING
    state = "WARMUP"
    frame_count = 0
    motion_stopped_at = None
    prev_gray = None

    print("\n" + "=" * 60)
    print("PROJECT LEND – Pipeline Running")
    print("=" * 60)
    print(f"  Camera : {camera_index}")
    print(f"  Arm    : {'ENABLED' if use_arm else 'DISABLED (vision-only)'}")
    print(f"  Settle : {SETTLE_TIME}s after motion stops")
    print(f"  Cooldown: {COOLDOWN}s between sorts")
    print("  Press Q in the window to quit.")
    print("=" * 60 + "\n")

    # Broadcast initial state
    pipeline_state.set_state("WARMUP", camera_active=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera read failed.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        frame_count += 1

        display = frame.copy()

        # ── WARMUP: let camera auto-expose ────────────────────────────────────
        if state == "WARMUP":
            cv2.putText(display, "Warming up camera...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            if frame_count >= WARMUP_FRAMES:
                prev_gray = gray.copy()
                state = "WATCHING"
                pipeline_state.set_state("WATCHING", motion_area=0)
                print("[STATE] WATCHING – waiting for item...")

        # ── WATCHING: look for motion (item being placed) ─────────────────────
        elif state == "WATCHING":
            motion, area = detect_motion(prev_gray, gray)
            cv2.putText(display, "WATCHING for item...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            pipeline_state.set_state("WATCHING", motion_area=area)
            if motion:
                state = "SETTLING"
                motion_stopped_at = None
                pipeline_state.set_state("SETTLING", motion_area=area)
                print(f"[STATE] SETTLING – motion detected (area={area})")
            prev_gray = gray.copy()

        # ── SETTLING: motion detected, wait for it to stop ────────────────────
        elif state == "SETTLING":
            motion, area = detect_motion(prev_gray, gray)
            cv2.putText(display, "Item detected, settling...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            pipeline_state.set_state("SETTLING", motion_area=area)
            if motion:
                motion_stopped_at = None   # still moving
            else:
                if motion_stopped_at is None:
                    motion_stopped_at = time.time()
                elif time.time() - motion_stopped_at >= SETTLE_TIME:
                    state = "CLASSIFYING"
                    pipeline_state.set_state("CLASSIFYING")
                    print("[STATE] CLASSIFYING – sending frame to Claude...")
            prev_gray = gray.copy()

        # ── CLASSIFYING: send frame to Claude ─────────────────────────────────
        elif state == "CLASSIFYING":
            cv2.putText(display, "Classifying with Claude...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.imshow("Project Lend", display)
            cv2.waitKey(1)

            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                print("Failed to encode frame, returning to WATCHING.")
                state = "WATCHING"
                continue

            try:
                info = classify_frame_detailed(buf.tobytes())
                category = info["category"]
                item_name = info.get('item_name', 'unknown')
                print("=" * 40)
                print(f"  CATEGORY : {category.upper()}")
                print(f"  ITEM     : {item_name}")
                print(f"  WEIGHT   : {info.get('estimated_weight_lbs', '?')} lbs")
                print(f"  EXPIRY   : {info.get('estimated_expiry', 'N/A')}")
                print("=" * 40)

                # Broadcast classification result
                pipeline_state.set_state("CLASSIFYING", last_category=category, last_item=item_name)

                # Save frame and log
                img_name = f"donation_{len(donations.get_all()) + 1}.jpg"
                img_path = os.path.join(IMAGES_DIR, img_name)
                cv2.imwrite(img_path, frame)
                donations.log_donation(
                    category=category,
                    item_name=info.get("item_name", "unknown"),
                    estimated_weight_lbs=info.get("estimated_weight_lbs"),
                    estimated_expiry=info.get("estimated_expiry"),
                    image_path=img_path,
                )
            except Exception as e:
                print(f"Classification error: {e}")
                state = "WATCHING"
                prev_gray = gray.copy()
                continue

            if use_arm:
                state = "SORTING"
                print(f"[STATE] SORTING – moving {category} to bin...")
                try:
                    arm_control.sort_to_bin(category)
                    print("[STATE] Sort complete.")
                except Exception as e:
                    print(f"Arm sort error: {e}")
            else:
                print("(vision-only mode – skipping arm sort)")

            state = "COOLDOWN"
            cooldown_start = time.time()
            print(f"[STATE] COOLDOWN – {COOLDOWN}s pause before next detection")

        # ── COOLDOWN: pause before watching again ─────────────────────────────
        elif state == "COOLDOWN":
            remaining = max(0, COOLDOWN - (time.time() - cooldown_start))
            cv2.putText(display, f"Cooldown {remaining:.1f}s", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
            pipeline_state.set_state("COOLDOWN", cooldown_remaining=remaining)
            if remaining <= 0:
                prev_gray = gray.copy()
                state = "WATCHING"
                pipeline_state.set_state("WATCHING", motion_area=0)
                print("[STATE] WATCHING – ready for next item...")

        # ── HUD ───────────────────────────────────────────────────────────────
        cv2.putText(display, "Q = quit", (10, display.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.imshow("Project Lend", display)
        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            print("\nQuitting...")
            break

    cap.release()
    cv2.destroyAllWindows()

    # Broadcast shutdown state
    pipeline_state.set_state("IDLE", camera_active=False)

    if use_arm:
        try:
            arm_control.move_to_pose(HOME)
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend pipeline")
    parser.add_argument("--camera", type=int, default=1, help="Camera index (1=ArduCam, 0=laptop)")
    parser.add_argument("--no-arm", action="store_true", help="Vision-only mode (no arm)")
    args = parser.parse_args()
    main(args.camera, use_arm=not args.no_arm)
