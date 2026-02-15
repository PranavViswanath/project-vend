"""Entry point for the Project Lend REST API server."""

from lend.api.server import app
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend API")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    print(f"Starting API on http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=True)
