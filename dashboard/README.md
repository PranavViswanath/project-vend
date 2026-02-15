# Project Lend Dashboard

Modern Next.js 15 dashboard for real-time monitoring of the autonomous food bank system.

## Features

- **Live Camera Feed**: MJPEG stream from ArduCam with state overlay
- **Real-time Stats**: Total items, weight, and unique donors
- **Category Breakdown**: Animated horizontal bars showing distribution
- **Donation Feed**: Scrollable list of recent donations
- **Pipeline State**: Live state machine visualization (WARMUP → WATCHING → SETTLING → CLASSIFYING → COOLDOWN)

## Tech Stack

- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first styling
- **SWR**: Data fetching with automatic deduplication
- **Framer Motion**: Smooth animations

## Development

### Prerequisites

The Flask API must be running before starting the dashboard:

```bash
# Terminal 1 - Start Flask API (from project root)
cd /Users/vikvang/Projects/project-vend
python api.py --camera 1
```

### Running the Dashboard

```bash
# Terminal 2 - Start Next.js (from dashboard directory)
cd dashboard
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Optional: Run Main Pipeline

To see live camera feed and state updates:

```bash
# Terminal 3 - Run main pipeline (from project root)
cd /Users/vikvang/Projects/project-vend
python main.py --camera 1
```

## Configuration

Edit `.env.local` to change the API URL:

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## API Endpoints

The dashboard consumes these Flask endpoints:

- `GET /donations` - All donation records
- `GET /donations/recent?limit=10` - Recent donations
- `GET /stats` - Summary statistics
- `GET /state` - Current pipeline state
- `GET /video_feed` - MJPEG camera stream

## Project Structure

```
dashboard/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Main dashboard page
│   └── globals.css             # Tailwind styles
├── components/
│   ├── CameraFeed.tsx          # Live MJPEG stream + state overlay
│   ├── StatsCards.tsx          # Total items, weight, donors
│   ├── CategoryBreakdown.tsx   # Animated category bars
│   └── DonationFeed.tsx        # Recent donations list
├── lib/
│   ├── api.ts                  # API client functions
│   └── types.ts                # TypeScript interfaces
└── hooks/
    └── useApi.ts               # SWR hooks with deduplication
```

## Performance Optimizations

This dashboard implements Vercel React best practices:

- **SWR Deduplication**: Prevents duplicate API requests
- **Bundle Optimization**: Framer Motion optimized with `optimizePackageImports`
- **Memoization**: Percentage calculations memoized in CategoryBreakdown
- **Conditional Rendering**: Proper ternary operators, no `&&` misuse

## Building for Production

```bash
npm run build
npm start
```

## Troubleshooting

**Camera feed not showing:**
- Ensure Flask API is running: `python api.py --camera 1`
- Check browser console for errors
- Verify API URL in `.env.local`

**State not updating:**
- Ensure `main.py` is running to broadcast state changes
- Check Network tab for `/state` requests

**CORS errors:**
- Flask API has CORS enabled by default
- If deploying to production, update CORS settings in `api.py`
