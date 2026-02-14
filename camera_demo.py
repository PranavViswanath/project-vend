"""Laptop webcam → Claude classification demo.

Modes:
- manual: press SPACE to classify current frame
- auto: classify continuously every N seconds

Controls:
- SPACE = classify now
- A = toggle auto/manual
- Q = quit

Usage:
    python camera_demo.py
    python camera_demo.py --camera 1
    python camera_demo.py --camera 2
    python camera_demo.py --mode auto --interval 1.5
"""
import argparse
import time
import cv2
from vision import classify_frame

# Colors for display (BGR)
COLORS = {
    "fruit": (0, 255, 0),    # Green
    "snack": (0, 165, 255),  # Orange
    "drink": (255, 0, 0),    # Blue
}


def main(camera_index: int = 0, mode: str = "manual", interval: float = 2.0):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        print("Try: python camera_demo.py --camera 1 (or --camera 2)")
        return

    auto_mode = mode.lower() == "auto"
    last_result = None
    last_ts = 0.0

    print("=" * 60)
    print("PROJECT LEND - Camera Classification Demo")
    print("=" * 60)
    print("Controls:")
    print("  SPACE = classify current frame now")
    print("  A     = toggle auto/manual")
    print("  Q     = quit")
    print(f"Starting in: {'AUTO' if auto_mode else 'MANUAL'} mode")
    print("=" * 60)

    def classify_current(frame):
        nonlocal last_result, last_ts
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            print("Failed to encode frame.")
            return

        print("\n[Sending frame to Claude...]")
        try:
            result = classify_frame(buffer.tobytes())
            last_result = result
            last_ts = time.time()
            print("=" * 40)
            print(f"  CLASSIFICATION: {result.upper()}")
            print("=" * 40)
        except Exception as e:
            print(f"Error during classification: {e}")
            print("Check ANTHROPIC_API_KEY and network.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break

        display = frame.copy()
        mode_text = "AUTO" if auto_mode else "MANUAL"
        cv2.putText(
            display,
            f"Mode: {mode_text} | SPACE classify | A toggle | Q quit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        if last_result:
            color = COLORS.get(last_result, (255, 255, 255))
            cv2.putText(
                display,
                f"Last: {last_result.upper()}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                color,
                3,
            )

        cv2.imshow("Project Lend - Food Classifier", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("\nQuitting...")
            break
        if key == ord("a"):
            auto_mode = not auto_mode
            print(f"Switched to {'AUTO' if auto_mode else 'MANUAL'} mode")
        if key == ord(" "):
            classify_current(frame)

        if auto_mode and (time.time() - last_ts) >= interval:
            classify_current(frame)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Camera classification demo")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    args = parser.parse_args()
    main(args.camera)
