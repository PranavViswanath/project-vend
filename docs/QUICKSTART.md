# Quick Start Guide - Project Lend Dashboard

## One-Time Setup

```bash
cd /Users/vikvang/Projects/project-vend/dashboard
npm install  # Already done, but run if needed
```

## Running the Dashboard

### Option 1: Dashboard Only (No Live Camera)

**Terminal 1 - Start Flask API:**
```bash
cd /Users/vikvang/Projects/project-vend
python api.py --camera 1
```

**Terminal 2 - Start Dashboard:**
```bash
cd dashboard
npm run dev
```

**Browser:**
Open `http://localhost:3000`

**What you'll see:**
- "Camera Offline" placeholder
- Stats (if donations exist in `donations.json`)
- Category breakdown
- Recent donations

---

### Option 2: Full System (Live Camera + Pipeline)

**Terminal 1 - Start Flask API:**
```bash
cd /Users/vikvang/Projects/project-vend
python api.py --camera 1
```

**Terminal 2 - Start Main Pipeline:**
```bash
cd /Users/vikvang/Projects/project-vend
python main.py --camera 1
```

**Terminal 3 - Start Dashboard:**
```bash
cd dashboard
npm run dev
```

**Browser:**
Open `http://localhost:3000`

**What you'll see:**
- Live camera feed from ArduCam
- Real-time state indicator (WARMUP → WATCHING → SETTLING → CLASSIFYING → COOLDOWN)
- Motion area when items detected
- Stats updating every 2 seconds
- New donations appearing in feed

---

## Testing Without Hardware

**Use laptop webcam:**
```bash
# Terminal 1
python api.py --camera 0  # Note: --camera 0 for built-in webcam

# Terminal 2
python main.py --camera 0  # Note: --camera 0

# Terminal 3
cd dashboard && npm run dev
```

**Vision-only mode (no arm):**
```bash
python main.py --camera 1 --no-arm
```

---

## Stopping Everything

Press `Ctrl+C` in each terminal:
1. Stop dashboard (Terminal 3)
2. Stop main pipeline (Terminal 2)
3. Stop API (Terminal 1)

---

## Troubleshooting

**Camera not opening:**
```bash
# Check available cameras
python detect_cameras.py

# Try different index
python api.py --camera 0  # Built-in webcam
```

**Dashboard shows "Camera Offline":**
- Make sure `main.py` is running (not just API)
- Check `main.py` terminal for camera errors

**No donations showing:**
- Run `main.py` to classify items
- Check `donations.json` has data

**Port already in use:**
```bash
# Use different port
python api.py --port 8080

# Update dashboard/.env.local
# NEXT_PUBLIC_API_URL=http://localhost:8080
```

---

## File Locations

- **API**: `/Users/vikvang/Projects/project-vend/api.py`
- **Pipeline**: `/Users/vikvang/Projects/project-vend/main.py`
- **Dashboard**: `/Users/vikvang/Projects/project-vend/dashboard/`
- **Config**: `/Users/vikvang/Projects/project-vend/dashboard/.env.local`

---

## Common Workflows

### Demo Mode (for presentations)
```bash
# Terminal 1: API + Camera stream
python api.py --camera 1

# Terminal 2: Dashboard
cd dashboard && npm run dev
```

### Full Pipeline Test
```bash
# Terminal 1: API
python api.py --camera 1

# Terminal 2: Main pipeline
python main.py --camera 1

# Terminal 3: Dashboard
cd dashboard && npm run dev

# Place an item in front of camera and watch it classify!
```

### Development (Backend only)
```bash
# Test API endpoints
python api.py --camera 1

# In browser or curl:
# http://localhost:5000/stats
# http://localhost:5000/state
# http://localhost:5000/video_feed
```

---

## Production Build

```bash
cd dashboard
npm run build
npm start
```

Dashboard will be available at `http://localhost:3000`

---

## Architecture Summary

```
┌─────────────┐     HTTP      ┌──────────────┐
│   Browser   │◄──────────────►│  Flask API   │
│ (Next.js)   │   REST + MJPEG │  (api.py)    │
└─────────────┘                └──────────────┘
      ▲                              ▲
      │                              │
      │ SWR Polling                  │ State Updates
      │ (1-2s)                       │ (Real-time)
      │                              │
      │                        ┌─────┴──────┐
      │                        │  main.py   │
      │                        │ (Pipeline) │
      └────────────────────────┴────────────┘
         /stats, /state,
         /donations, /video_feed
```

---

## Key Features

✅ Live MJPEG camera stream
✅ Real-time pipeline state (WARMUP, WATCHING, SETTLING, CLASSIFYING, COOLDOWN)
✅ Motion detection visualization
✅ Donation statistics
✅ Category breakdown with animations
✅ Recent donations feed
✅ Responsive design
✅ SWR deduplication (no duplicate requests)
✅ Beautiful gradient UI

---

**Ready to start? Run the commands above!** 🚀
