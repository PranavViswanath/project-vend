"""Entry point for the Project Lend detection/sorting pipeline."""

from lend.pipeline.main import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Lend pipeline")
    parser.add_argument("--camera", type=int, default=1, help="Camera index (1=ArduCam, 0=laptop)")
    parser.add_argument("--no-arm", action="store_true", help="Vision-only mode (no arm)")
    args = parser.parse_args()
    main(args.camera, use_arm=not args.no_arm)
