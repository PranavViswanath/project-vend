# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project Lend** is an autonomous food bank system for TreeHacks 2026 that combines:
- Hiwonder xArm 1S robotic arm (USB-connected)
- Camera-based vision classification using Claude API
- State machine pipeline with motion detection and automated sorting

The system detects donated items via motion detection, classifies them into categories (fruit/snack/drink), logs donation data, and sorts items into appropriate bins.

## Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

Required environment variable:
```bash
export ANTHROPIC_API_KEY="sk-..."
```

Optional override for Claude model (defaults to `claude-3-5-haiku-latest`):
```bash
export CLAUDE_VISION_MODEL="claude-3-5-haiku-latest"
```

## Common Commands

### Hardware Calibration
Run FIRST when setting up new positions or after hardware changes:
```bash
python calibrate.py
```
Physically move the arm to each position, press Enter to record servo values, then copy output into `positions.py`.

### Testing Individual Components
```bash
# Detect available cameras
python detect_cameras.py

# Test arm only (no vision)
python test_arm.py

# Test vision only (requires ANTHROPIC_API_KEY)
python test_vision.py

# Test camera preview
python camera_demo.py --camera 0  # or --camera 1 for ArduCam
```

### Running the Full System

**Terminal 1 - Start API server:**
```bash
python api.py                    # runs on http://localhost:5000
python api.py --port 8080        # custom port
```

**Browser - Open dashboard:**
Open `dashboard.html` to view live stats, category breakdown, and donation feed.

**Terminal 2 - Run pipeline:**
```bash
# Manual test mode (press SPACE to capture)
python test_pipeline.py --camera 1

# Auto mode (motion detection)
python main.py --camera 1

# Vision-only mode (no arm control)
python main.py --no-arm
```

Default camera is 1 (ArduCam). Use `--camera 0` for laptop webcam.

## Architecture

### State Machine (main.py)

The core pipeline runs as a 5-state finite state machine:

1. **WARMUP** (60 frames): Camera auto-exposure initialization
2. **WATCHING**: Motion detection via frame differencing
3. **SETTLING**: Wait for motion to stop (1.5s settle time)
4. **CLASSIFYING**: Send frame to Claude for vision classification
5. **COOLDOWN**: 5s pause before next detection cycle

Motion detection parameters:
- `MOTION_THRESHOLD = 30` (pixel intensity change)
- `MOTION_MIN_AREA = 5000` (minimum contour area in px²)
- `SETTLE_TIME = 1.5` (seconds to wait after motion stops)
- `COOLDOWN = 5.0` (seconds between sorts)

### Threading Model

Both `main.py` and `test_pipeline.py` use threading to prevent blocking:
- **Camera capture**: Background thread (continuous frame reading)
- **UI/Display**: Main thread (OpenCV window must be on main thread on Windows)
- **AI/Sorting**: Worker thread in `test_pipeline.py` (async processing)

### Module Responsibilities

**arm_control.py** - Low-level xArm USB control
- `connect()`: Connect to xArm (must call first)
- `move_to_pose(pose)`: Move all 6 servos to a position
- `move_body(pose)`: Move servos 2-6 only (preserves gripper state)
- `gripper_open()` / `gripper_close()`: Gripper control with pressure relief
- `sort_to_bin(category)`: Full pick-and-place sequence (HOME → PICKUP → grip → HOME → BIN → release → HOME)

**positions.py** - Calibrated servo positions
- Each pose is a list of 6 servo values (0-1000): `[gripper, wrist_rotation, wrist, elbow, shoulder, base]`
- Key positions: `HOME`, `PICKUP`, `BIN_FRUIT`, `BIN_SNACK`, `BIN_DRINK`
- `CATEGORY_MAP`: Maps vision categories to bin positions

**vision.py** - Claude-based classification
- `classify_frame(frame_bytes)`: Fast classification (returns category string only)
- `classify_frame_detailed(frame_bytes)`: Full classification with metadata (item_name, weight, expiry)
- Auto-strips markdown code fences from Claude responses
- Validates categories with fallback to "snack"

**donations.py** - JSON-backed donation log
- `log_donation(...)`: Append new donation record
- `get_all()`: Return all records
- `get_stats()`: Summary stats (total items, weight, donors, by_category)
- Data stored in `donations.json` with auto-incrementing IDs

**api.py** - Flask REST API
- `GET /donations`: All donation records
- `GET /donations/recent?limit=N`: Latest N records (default 10)
- `GET /stats`: Summary statistics
- CORS enabled for frontend access

### Servo Control Conventions

Following Hiwonder xArm SDK patterns:
- Servo positions: integers 0-1000
- Gripper (servo 1) uses pressure relief: `setPosition → getPosition → servoOff → wait → setPosition`
- Special value `999.9` in pose means "keep gripper unchanged"
- Movement duration: 1500ms by default

The pressure relief pattern (`_gripper_relief()`) prevents servo strain and motor overheating.

## Data Storage

- **Donations log**: `donations.json` (JSON array)
- **Captured images**: `images/donation_N.jpg`

Each donation record includes:
```json
{
  "id": 1,
  "category": "fruit",
  "item_name": "Granny Smith Apple",
  "estimated_weight_lbs": 0.3,
  "estimated_expiry": "2026-03-01",
  "timestamp": "2026-02-14T12:34:56.789Z",
  "image_path": "images/donation_1.jpg",
  "donor_id": null
}
```

## Common Development Patterns

### Adding a New Bin Position
1. Run `python calibrate.py`
2. Physically move arm to new bin position
3. Copy output to `positions.py` (e.g., `BIN_HYGIENE = [...]`)
4. Add to `CATEGORY_MAP` dict
5. Update `DETAILED_PROMPT` in `vision.py` to recognize new category

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

## Important Notes

- The arm must be connected via USB before calling `arm_control.connect()`
- Camera warm-up (60 frames) is essential for consistent auto-exposure
- Missing `import os` in `main.py` (line 26 uses `os.path` before import) - add `import os` at top
- Claude vision responses sometimes include markdown code fences - stripped by `vision.py`
- All timestamps use UTC timezone for consistency
- Camera uses DirectShow backend (`cv2.CAP_DSHOW`) on Windows with fallback
