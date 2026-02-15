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
print("Recorded positions:")
print("=" * 60)
for name, pose in positions.items():
    print(f"{name} = {pose}")

# Auto-update positions.py
import os
positions_path = os.path.join(os.path.dirname(__file__), "..", "lend", "hardware", "positions.py")
positions_path = os.path.abspath(positions_path)

content = '''"""Calibrated positions for Project Lend food bank.

Run `python tools/calibrate.py` and positions are saved here automatically.
Each pose is a list of 6 servo positions (units 0-1000), servos 1-6.
"""

# Safe resting position
HOME = {HOME}

# Donation zone (where people place items)
PICKUP = {PICKUP}

# Bin positions
BIN_FRUIT = {BIN_FRUIT}   # Apples, bananas, oranges
BIN_SNACK = {BIN_SNACK}   # Chips, granola bars, candy
BIN_DRINK = {BIN_DRINK}   # Water bottles, juice, soda

# Map vision categories to bin positions
CATEGORY_MAP = {{
    "fruit": BIN_FRUIT,
    "snack": BIN_SNACK,
    "drink": BIN_DRINK,
}}
'''.format(**positions)

with open(positions_path, "w") as f:
    f.write(content)
print(f"\nPositions saved to {positions_path}")
