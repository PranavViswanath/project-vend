"""REST API for Project Lend donation data.

Endpoints:
    GET /donations          — all donation records
    GET /donations/recent   — last N records (default 10, ?limit=N)
    GET /stats              — summary stats for frontend dashboard

Usage:
    python api.py                   # runs on port 5000
    python api.py --port 8080       # custom port
"""

import argparse
from flask import Flask, jsonify, request
from flask_cors import CORS
import donations

app = Flask(__name__)
CORS(app)  # allow frontend to call from any origin


@app.route("/donations", methods=["GET"])
def all_donations():
    return jsonify(donations.get_all())


@app.route("/donations/recent", methods=["GET"])
def recent_donations():
    limit = request.args.get("limit", 10, type=int)
    records = donations.get_all()
    return jsonify(records[-limit:])


@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(donations.get_stats())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend API")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print(f"Starting API on http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=True)
