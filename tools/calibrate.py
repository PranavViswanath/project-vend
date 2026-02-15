"""Record positions by moving arm by hand.

Usage:
    python calibrate.py

Physically move the arm to each position, then press Enter to record.
Copy the output into positions.py.
"""
import xarm

arm = xarm.Controller('USB')
print("=== Position Calibration ===")
print("Physically move the arm to each position, then press Enter")
print("Servos will go limp so you can move the arm by hand.\n")

# Turn off all servo motors so arm can be freely moved
for i in range(1, 7):
    arm.servoOff(i)

positions = {}
instructions = {
    "HOME": "Safe resting position (arm up, out of the way)",
    "PICKUP": "Gripper over donation zone (where people place items)",
    "BIN_FRUIT": "Gripper over fruit bin (apples, bananas, oranges)",
    "BIN_SNACK": "Gripper over snack bin (chips, granola bars, candy)",
    "BIN_DRINK": "Gripper over drink bin (water bottles, juice, soda)",
}

for name, instruction in instructions.items():
    print(f"\n{name}:")
    print(f"  -> {instruction}")
    input("  Press Enter when ready...")

    pose = [arm.getPosition(i) for i in range(1, 7)]
    positions[name] = pose
    print(f"  Recorded: {pose}")

    # Re-disable servos for next position
    for i in range(1, 7):
        arm.servoOff(i)

print("\n" + "=" * 60)
print("Copy these into positions.py:")
print("=" * 60)
for name, pose in positions.items():
    print(f"{name} = {pose}")
