# Project Lend Dashboard - Implementation Guide

## Overview

Successfully implemented a modern Next.js 15 dashboard with live camera streaming and real-time pipeline state monitoring for Project Lend.

## What Was Built

### Backend Extensions (Python Flask)

1. **`pipeline_state.py`** - Thread-safe state management
   - Shared state between `main.py` and `api.py`
   - Thread-safe using `threading.Lock()`
   - Stores: state, timestamp, camera_active, motion_area, last_category, last_item, cooldown_remaining

2. **Extended `api.py`**
   - `/video_feed` - MJPEG camera stream endpoint
   - `/state` - Real-time pipeline state JSON endpoint
   - Background camera capture thread
   - Non-blocking video streaming

3. **Updated `main.py`**
   - Added `import os` (fixed bug mentioned in CLAUDE.md)
   - State broadcasting at each transition:
     - WARMUP → camera initialized
     - WATCHING → motion area updates
     - SETTLING → motion tracking
     - CLASSIFYING → category/item broadcast
     - COOLDOWN → remaining time updates
     - IDLE → shutdown state

### Frontend (Next.js 15 + TypeScript)

**Project Structure:**
```
dashboard/
├── app/
│   ├── page.tsx              # Main dashboard (composed view)
│   └── layout.tsx            # Root layout
├── components/
│   ├── CameraFeed.tsx        # Live MJPEG + state overlay
│   ├── StatsCards.tsx        # Animated stats cards
│   ├── CategoryBreakdown.tsx # Category distribution bars
│   └── DonationFeed.tsx      # Recent donations list
├── lib/
│   ├── types.ts              # TypeScript interfaces
│   └── api.ts                # API client
├── hooks/
│   └── useApi.ts             # SWR hooks with deduplication
└── .env.local                # Configuration
```

**Key Features:**
- **Live Camera Feed**: MJPEG stream with color-coded state indicator
- **Real-time Updates**: SWR polling every 1-2 seconds with deduplication
- **Beautiful UI**: Gradient backgrounds, glass-morphism effects, smooth animations
- **Responsive**: Mobile-friendly grid layout

**Vercel Best Practices Applied:**
- ✅ `client-swr-dedup` - SWR with `dedupingInterval`
- ✅ `bundle-dynamic-imports` - Framer Motion optimized
- ✅ `rerender-memo` - Memoized calculations in CategoryBreakdown
- ✅ `rendering-conditional-render` - Proper ternary operators

## How to Use

### Step 1: Start Flask API (Terminal 1)

```bash
cd /Users/vikvang/Projects/project-vend
python api.py --camera 1
```

This starts:
- REST API on `http://localhost:5000`
- Camera streaming thread
- All endpoints: `/donations`, `/stats`, `/state`, `/video_feed`

### Step 2: Start Next.js Dashboard (Terminal 2)

```bash
cd dashboard
npm run dev
```

Open `http://localhost:3000` to view the dashboard.

**You'll see:**
- Camera feed (if `main.py` is running) or "Camera Offline" placeholder
- Stats cards (total items, weight, donors)
- Category breakdown (if donations exist)
- Recent donations feed

### Step 3: Run Main Pipeline (Terminal 3) - Optional

To see live state updates and camera feed:

```bash
python main.py --camera 1
```

Watch the dashboard automatically update as the pipeline transitions through states:
- **WARMUP** (yellow) - Camera initializing
- **WATCHING** (green) - Waiting for item
- **SETTLING** (orange) - Motion detected
- **CLASSIFYING** (blue) - Sending to Claude
- **COOLDOWN** (purple) - Pause before next cycle

## API Endpoints Reference

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/donations` | GET | All donation records | `Donation[]` |
| `/donations/recent?limit=10` | GET | Recent N donations | `Donation[]` |
| `/stats` | GET | Summary statistics | `Stats` |
| `/state` | GET | Current pipeline state | `PipelineState` |
| `/video_feed` | GET | MJPEG stream | `multipart/x-mixed-replace` |

## Configuration

**`.env.local`** (dashboard directory):
```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

Change this if running the API on a different port or deploying to production.

## Production Build

```bash
cd dashboard
npm run build
npm start
```

## Troubleshooting

**Problem: Camera feed shows "Camera Offline"**
- ✅ Check Flask API is running: `python api.py --camera 1`
- ✅ Verify camera index (try `--camera 0` for laptop webcam)

**Problem: State not updating**
- ✅ Ensure `main.py` is running (API alone won't change state)
- ✅ Check browser Network tab for `/state` requests

**Problem: MJPEG stream not loading**
- ✅ Verify camera access permissions
- ✅ Check Flask terminal for camera errors
- ✅ Try accessing `http://localhost:5000/video_feed` directly

**Problem: No donations showing**
- ✅ Run `main.py` to classify and log donations
- ✅ Check `donations.json` exists and has data

## Architecture Notes

**MJPEG vs WebSocket:**
- Chose MJPEG for simplicity (works with standard `<img>` tag)
- No complex WebSocket/WebRTC infrastructure needed
- Sufficient for local deployment

**Polling vs SSE:**
- SWR handles polling with built-in deduplication
- Simpler than Server-Sent Events
- Excellent developer experience

**Thread Safety:**
- `pipeline_state.py` uses `threading.Lock()` for safe access
- Camera capture runs in background daemon thread
- Non-blocking API responses

## File Changes Summary

**Created:**
- `pipeline_state.py` - Shared state module
- `dashboard/` - Entire Next.js project
  - 4 components
  - 2 lib files
  - 1 hooks file
  - Configuration files

**Modified:**
- `api.py` - Added streaming endpoints and camera thread
- `main.py` - Added state broadcasting and fixed `import os` bug

**Lines of Code:**
- Backend: ~100 lines
- Frontend: ~500 lines
- Total: ~600 lines of new code

## Next Steps (Future Enhancements)

- Historical charts (donations over time)
- Browser notifications when items classified
- Camera controls (pause/resume, snapshot)
- WebSocket upgrade for lower latency
- Mobile app (React Native)
- Multi-camera support
- Export reports (CSV, PDF)

## Resources

- Dashboard README: `dashboard/README.md`
- Main README: `README.md` (if exists)
- Project instructions: `CLAUDE.md`
