# Project Lend

Autonomous food bank for TreeHacks 2026. xArm 1S sorts donated food, Claude agents coordinate donors + shelters.

## Hardware

- Hiwonder xArm 1S over USB (connected to laptop)
- Laptop webcam for vision classification

## Setup (Laptop)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your API key before running vision features:

```powershell
$env:ANTHROPIC_API_KEY="YOUR_API_KEY"
```

## Calibrate Arm Positions

Physically move the arm to each position and record servo values:

```powershell
python calibrate.py
```

Copy the output into `positions.py`.

## Run the Full System

### 1. Start the API (terminal 1)

```powershell
python api.py
```

Runs on http://localhost:5000

### 2. Open the Dashboard

Open `dashboard.html` in your browser. It will show:
- Live stats (items, weight, donors)
- Category breakdown (fruit/snack/drink)
- Real-time donation feed with Claude's detailed classifications

### 3. Run the Pipeline (terminal 2)

**Test mode (manual capture):**
```powershell
python test_pipeline.py
```
Press SPACE to capture and classify.

**Auto mode (motion detection):**
```powershell
python main.py
```
Watches for items placed in front of camera, auto-classifies and sorts.

**Vision-only (no arm):**
```powershell
python main.py --no-arm
```

## Quick Tests

**Test arm:**
```powershell
python test_arm.py
```

**Test camera + vision:**
```powershell
python test_vision.py
```

**Test camera demo:**
```powershell
python camera_demo.py --camera 0
```

## Data

- Donations logged to: `donations.json`
- Captured images saved to: `images/`
- API endpoints:
  - GET `/donations` - all records
  - GET `/donations/recent?limit=10` - latest N
  - GET `/stats` - summary stats
