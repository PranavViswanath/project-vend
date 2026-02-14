"""Record positions by moving arm by hand.

Usage:
    python3 calibrate.py

Physically move the arm to each position, then press Enter to record.
Copy the output into positions.py.
"""
import xarm

arm = xarm.Controller('USB')
print("=== Position Calibration ===")
print("Physically move the arm to each position, then press Enter\n")

positions = {}
instructions = {
    "HOME": "Safe resting position (arm up, out of the way)",
    "PICKUP": "Gripper over donation zone (where people place items)",
    "BIN_NONPERISHABLE": "Gripper over canned goods / boxed items bin",
    "BIN_SNACKS": "Gripper over chips / granola bars / candy bin",
    "BIN_PROTEIN": "Gripper over protein bars / peanut butter bin",
}

for name, instruction in instructions.items():
    print(f"\n{name}:")
    print(f"  -> {instruction}")
    input("  Press Enter when ready...")

    pose = [arm.getPosition(i) for i in range(1, 7)]
    positions[name] = pose
    print(f"  Recorded: {pose}")

print("\n" + "=" * 60)
print("Copy these into positions.py:")
print("=" * 60)
for name, pose in positions.items():
    print(f"{name} = {pose}")
