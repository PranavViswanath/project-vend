"""Quick test: capture one frame from laptop webcam and classify it via Claude."""

import os
import cv2
from lend.vision.classifier import classify_frame

if not os.getenv("ANTHROPIC_API_KEY"):
    print("Set ANTHROPIC_API_KEY first:")
    print('  $env:ANTHROPIC_API_KEY="sk-..."')
    raise SystemExit(1)

print("Opening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Could not open camera. Try changing index in the script.")
    raise SystemExit(1)

print("Live preview open. Press SPACE to capture, Q to quit.")
frame = None
while True:
    ret, f = cap.read()
    if not ret:
        print("Failed to read from camera.")
        raise SystemExit(1)
    cv2.imshow("Test Vision - SPACE to capture", f)
    key = cv2.waitKey(1) & 0xFF
    if key == ord(" "):
        frame = f
        break
    if key == ord("q"):
        cap.release()
        cv2.destroyAllWindows()
        print("Cancelled.")
        raise SystemExit(0)

cap.release()
cv2.destroyAllWindows()
print("Captured! Sending to Claude...")

ok, buf = cv2.imencode(".jpg", frame)
if not ok:
    print("Failed to encode frame.")
    raise SystemExit(1)

result = classify_frame(buf.tobytes())
print(f"\nClassification: {result}")
