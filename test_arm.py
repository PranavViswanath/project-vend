"""Test all xArm servos using Hiwonder-style armSequence conventions.

Conventions mirrored from Hiwonder-xArmMove.py:
- armSequence entries can be:
  - [gripper_target] (single value for servo 1)
  - [s1,s2,s3,s4,s5,s6] full pose
  - [999.9,s2,s3,s4,s5,s6] keep gripper unchanged while moving servos 2..6
- moveGripper uses readback + servoOff pressure-relief pattern.
"""

from time import sleep
import xarm

MIN_POS = 0
MAX_POS = 1000
MOVE_MS = 1800
PAUSE_S = 1.2

# Confirmed mapping from your hardware
SERVO_NAMES = {
    1: "Gripper",
    2: "Wrist Rotation",
    3: "Wrist",
    4: "Elbow",
    5: "Shoulder",
    6: "Base",
}

# Bigger movement for shoulder so motion is easier to see
DELTA_BY_SERVO = {
    2: 120,
    3: 120,
    4: 120,
    5: 180,
    6: 120,
}


def clamp(v: int) -> int:
    return max(MIN_POS, min(MAX_POS, int(v)))


def choose_target(current: int, delta: int) -> int:
    if current + delta <= MAX_POS:
        return clamp(current + delta)
    return clamp(current - delta)


arm = xarm.Controller('USB')
print("Connected to xArm!\n")


def moveGripper(pos: int):
    target = clamp(pos)
    arm.setPosition(1, target, MOVE_MS, True)
    real = clamp(arm.getPosition(1, False))
    arm.servoOff(1)
    sleep(0.2)
    arm.setPosition(1, real, MOVE_MS, True)
    print(f"  Gripper commanded={target}, measured={real} (relief cycle applied)")


def make_non_gripper_sequence_pose(positions):
    # 999.9 convention: keep gripper unchanged
    return [999.9, positions[1], positions[2], positions[3], positions[4], positions[5]]


start = [clamp(arm.getPosition(i, False)) for i in range(1, 7)]
print(f"Start positions [1..6]: {start}")
print("Servo map:")
for sid in range(1, 7):
    print(f"  {sid}: {SERVO_NAMES[sid]}")
print()

# Build a sequence that tests each servo in order with clear movement and return.
home = start.copy()
g_open = choose_target(home[0], 180)
home_open = home.copy()
home_open[0] = g_open

armSequence = []
labels = []

# Step 1: open gripper first
armSequence.append([g_open])
labels.append("Test Servo 1 (Gripper): open")

# Steps 2-6: test each non-gripper servo, then return
for sid in [2, 3, 4, 5, 6]:
    moved = home_open.copy()
    moved[sid - 1] = choose_target(home_open[sid - 1], DELTA_BY_SERVO[sid])

    armSequence.append(make_non_gripper_sequence_pose(moved))
    labels.append(f"Test Servo {sid} ({SERVO_NAMES[sid]}): move")

    armSequence.append(make_non_gripper_sequence_pose(home_open))
    labels.append(f"Test Servo {sid} ({SERVO_NAMES[sid]}): return")

# Final gripper close/open test
if g_open >= home[0]:
    g_close = clamp(g_open - 220)
else:
    g_close = clamp(g_open + 220)

armSequence.append([g_close])
labels.append("Test Servo 1 (Gripper): close")

armSequence.append([g_open])
labels.append("Test Servo 1 (Gripper): re-open")

# Final full return to original start pose
armSequence.append(home)
labels.append("Return to original start pose")

for idx, s in enumerate(armSequence, start=1):
    print(f"Step {idx}/{len(armSequence)} - {labels[idx - 1]}")

    if len(s) == 1:
        moveGripper(s[0])

    elif len(s) == 6 and s[0] == 999.9:
        arm.setPosition([[2, s[1]], [3, s[2]], [4, s[3]], [5, s[4]], [6, s[5]]], duration=MOVE_MS, wait=True)
        print(f"  Moved servos 2..6 (gripper unchanged)")

    elif len(s) == 6:
        arm.setPosition([[1, s[0]], [2, s[1]], [3, s[2]], [4, s[3]], [5, s[4]], [6, s[5]]], duration=MOVE_MS, wait=True)
        print("  Moved full pose (servos 1..6)")

    else:
        raise ValueError("Each armSequence item must have length 1 or 6")

    current = [clamp(arm.getPosition(i, False)) for i in range(1, 7)]
    print(f"  Readback [1..6]: {current}\n")
    sleep(PAUSE_S)

print("Done: all servos tested with Hiwonder-style sequence patterns.")
