# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Project Lend** is an autonomous food bank system for TreeHacks 2026 that uses:
- **Hardware**: Hiwonder xArm 1S robotic arm (USB-connected) and laptop/ArduCam webcam
- **AI Vision**: Claude (Anthropic) for real-time food classification
- **Architecture**: State-machine-based pipeline with motion detection, vision classification, and robotic sorting

The system automatically detects donated items, classifies them into categories (fruit/snack/drink), logs donation data, and sorts items into appropriate bins.

## Development Environment

### Setup
```bash
python -m venv venv
source venv/bin/activate  # On Unix/Mac
# .\\venv\\Scripts\\Activate.ps1 on Windows PowerShell
pip install -r requirements.txt
```

### Environment Variables
Set `ANTHROPIC_API_KEY` before running any vision features:
```bash
export ANTHROPIC_API_KEY="sk-..."
# On Windows: $env:ANTHROPIC_API_KEY="sk-..."
```

Override Claude model (optional):
```bash
export CLAUDE_VISION_MODEL="claude-3-5-haiku-latest"  # default
```

## Key Commands

### Hardware Calibration
**Important**: Run calibration first when setting up new positions or after hardware changes:
```bash
python calibrate.py
```
Physically move the arm to each position, press Enter to record servo values, then copy output to `positions.py`.

### Testing

**Detect available cameras**:
```bash
python detect_cameras.py
```

**Test arm only** (no vision):
```bash
python test_arm.py
```
Tests all 6 servos with Hiwonder-style sequence patterns.

**Test vision only** (requires ANTHROPIC_API_KEY):
```bash
python test_vision.py
```

**Test camera preview**:
```bash
python camera_demo.py --camera 0  # or --camera 1 for ArduCam
```

### Running the Full System

**1. Start the API server** (terminal 1):
```bash
python api.py
# Or custom port: python api.py --port 8080
```
Runs on http://localhost:5000

**2. Open dashboard** (browser):
Open `dashboard.html` to view live stats, category breakdown, and donation feed.

**3. Run the pipeline** (terminal 2):

**Manual test mode** (press SPACE to capture):
```bash
python test_pipeline.py --camera 1
```

**Auto mode** (motion detection):
```bash
python main.py --camera 1
```
Default camera is 1 (ArduCam). Use `--camera 0` for laptop webcam.

**Vision-only mode** (no arm control):
```bash
python main.py --no-arm
```

## Code Architecture

### State Machine Pipeline (main.py)
The core pipeline is a state machine with 5 states:
1. **WARMUP**: Camera auto-exposure initialization (60 frames)
2. **WATCHING**: Motion detection via frame differencing
3. **SETTLING**: Wait for motion to stop (1.5s settle time)
4. **CLASSIFYING**: Send frame to Claude for vision classification
5. **COOLDOWN**: 5s pause before next detection

Motion detection uses:
- `MOTION_THRESHOLD = 30` (pixel intensity delta)
- `MOTION_MIN_AREA = 5000` (minimum contour area in px²)

### Module Responsibilities

**arm_control.py**: Low-level xArm control
- `connect()`: Connect to xArm over USB (must call first)
- `move_to_pose(pose)`: Move all 6 servos to a position
- `move_body(pose)`: Move servos 2-6 only (preserves gripper state)
- `gripper_open()` / `gripper_close()`: Gripper control with pressure relief
- `sort_to_bin(category)`: Full pick-and-place sequence

**positions.py**: Calibrated servo positions
- Each pose is a list of 6 servo values (0-1000)
- `HOME`: Safe resting position
- `PICKUP`: Donation zone (where items are placed)
- `BIN_FRUIT`, `BIN_SNACK`, `BIN_DRINK`: Target bins
- `CATEGORY_MAP`: Maps vision categories to bin positions

**vision.py**: Claude-based classification
- `classify_frame(frame_bytes)`: Fast classification (returns category string)
- `classify_frame_detailed(frame_bytes)`: Full classification with metadata (item_name, weight, expiry)
- Uses `claude-3-5-haiku-latest` by default
- Returns structured JSON with category validation fallback

**donations.py**: JSON-backed donation log
- `log_donation(...)`: Append new donation record
- `get_all()`: Return all records
- `get_stats()`: Summary stats for dashboard API
- Stores data in `donations.json` with auto-incrementing IDs

**api.py**: Flask REST API for dashboard
- `GET /donations`: All donation records
- `GET /donations/recent?limit=N`: Latest N records (default 10)
- `GET /stats`: Summary statistics (total items, weight, donors, by_category)
- CORS enabled for frontend access

**test_pipeline.py**: Manual testing harness
- Runs camera capture in background thread
- OpenCV window + key handling on main thread
- Worker thread for Claude + arm sorting (keeps video smooth)
- Press SPACE to capture and classify, Q to quit

### Threading Architecture
Both `main.py` and `test_pipeline.py` use threading to prevent blocking:
- **Camera capture**: Background thread (continuous frame reading)
- **UI/Display**: Main thread (OpenCV window must be on main thread on Windows)
- **AI/Sorting**: Worker thread (async processing, updates status text)

### Servo Control Conventions
Following Hiwonder xArm conventions:
- Servo positions are integers 0-1000
- Gripper (servo 1) uses pressure relief pattern: setPosition → getPosition → servoOff → wait → setPosition
- Pose arrays: `[gripper, wrist_rotation, wrist, elbow, shoulder, base]`
- Special value `999.9` in pose means "keep gripper unchanged"

## Data Storage

- **Donations log**: `donations.json` (JSON array with auto-incrementing IDs)
- **Captured images**: `images/donation_N.jpg` (saved during classification)
- Each donation record includes:
  - category, item_name, estimated_weight_lbs, estimated_expiry
  - timestamp (ISO-8601 UTC)
  - image_path, optional donor_id

## Camera Configuration

- **Default**: Camera index 1 (ArduCam)
- **Laptop webcam**: Camera index 0
- Uses DirectShow backend (`cv2.CAP_DSHOW`) on Windows with fallback
- Run `detect_cameras.py` to enumerate available cameras

## Common Development Patterns

### Adding a New Bin Position
1. Run `python calibrate.py`
2. Physically move arm to new bin position
3. Copy output to `positions.py` (e.g., `BIN_HYGIENE = [...]`)
4. Add to `CATEGORY_MAP` dict
5. Update `vision.py` prompts to recognize new category

### Modifying Vision Classification
- Edit `DETAILED_PROMPT` or `SIMPLE_PROMPT` in `vision.py`
- Test with: `python test_vision.py` or `python vision.py` (uses `camera-test.jpg`)
- Classification includes automatic fallback if JSON parsing fails

### Tuning Motion Detection
Edit constants in `main.py`:
- `MOTION_THRESHOLD`: Lower = more sensitive (default 30)
- `MOTION_MIN_AREA`: Larger = ignore small movements (default 5000 px²)
- `SETTLE_TIME`: Wait time after motion stops (default 1.5s)
- `COOLDOWN`: Pause between sorts (default 5.0s)

### Adding API Endpoints
1. Add route function in `api.py` with `@app.route(...)`
2. Import data helpers from `donations.py`
3. Return `jsonify(data)` for JSON responses
4. Update `dashboard.html` to consume new endpoint

## Dependencies

- **xarm==0.0.4**: Hiwonder xArm Python SDK
- **anthropic>=0.40.0**: Claude API client
- **opencv-python>=4.8.0**: Computer vision and camera capture
- **flask>=3.0.0**: REST API server
- **flask-cors>=4.0.0**: Cross-origin resource sharing

## Testing Strategy

When testing changes:
1. Test individual components first (arm, vision, camera)
2. Use `test_pipeline.py` for manual integration testing
3. Use `main.py --no-arm` to test vision without arm (safer)
4. Always verify arm has clear workspace before enabling auto mode
5. Check `donations.json` and `images/` directory after runs

## Notes

- The arm must be connected via USB before calling `arm_control.connect()`
- Camera warm-up is essential for consistent lighting (60 frames in main.py)
- Claude vision responses sometimes include markdown code fences - strip them in `vision.py`
- Gripper pressure relief prevents servo strain (implemented in `_gripper_relief()`)
- All timestamps use UTC timezone for consistency
