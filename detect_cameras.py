"""Detect all available camera devices."""

import cv2

print("Scanning for cameras...")
print("=" * 50)

working_cameras = []

for i in range(10):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            backend = cap.getBackendName()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Camera {i}: FOUND")
            print(f"  Backend: {backend}")
            print(f"  Resolution: {width}x{height}")
            working_cameras.append(i)
        cap.release()

print("=" * 50)
if working_cameras:
    print(f"\nFound {len(working_cameras)} camera(s): {working_cameras}")
    print(f"\nTesting camera {working_cameras[-1]} (newest)...")
    
    cap = cv2.VideoCapture(working_cameras[-1], cv2.CAP_DSHOW)
    print("\nPress Q to quit preview")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        
        cv2.putText(frame, f"Camera {working_cameras[-1]} - Press Q to quit", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Camera {working_cameras[-1]} Preview", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
else:
    print("\nNo cameras found!")
