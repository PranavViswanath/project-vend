"""Arm control helpers for Project Lend.

Provides:
- connect(): connect to the xArm over USB
- move_to_pose(pose): move arm to a calibrated position
- gripper_open() / gripper_close(): operate the claw
- sort_to_bin(category): full pick-and-place cycle
"""
from time import sleep
from lend.hardware.positions import HOME, PICKUP, CATEGORY_MAP

try:
    import xarm
except ImportError:
    xarm = None

MOVE_MS = 1500  # movement duration in milliseconds
GRIPPER_OPEN = 50    # adjust based on your calibration
GRIPPER_CLOSE = 700  # adjust based on your calibration

arm = None


def connect():
    """Connect to xArm over USB. Call once before using any arm functions."""
    global arm
    if xarm is None:
        raise RuntimeError("xarm package not installed. Install with: pip install xarm")
    if arm is None:
        arm = xarm.Controller('USB')
        print("Connected to xArm!")
    return arm


def _require_arm():
    if arm is None:
        raise RuntimeError("Call arm_control.connect() before using the arm.")


def move_to_pose(pose: list, duration: int = MOVE_MS):
    """Move all 6 servos to a pose."""
    _require_arm()
    commands = [[i + 1, pose[i]] for i in range(6)]
    arm.setPosition(commands, duration, wait=True)


def move_body(pose: list, duration: int = MOVE_MS):
    """Move servos 2-6 only, leaving the gripper (servo 1) unchanged."""
    _require_arm()
    commands = [[i + 1, pose[i]] for i in range(1, 6)]
    arm.setPosition(commands, duration, wait=True)


def gripper_open():
    """Open the gripper."""
    _require_arm()
    arm.setPosition(1, GRIPPER_OPEN, MOVE_MS, True)
    _gripper_relief()


def gripper_close():
    """Close the gripper (with pressure relief)."""
    _require_arm()
    arm.setPosition(1, GRIPPER_CLOSE, MOVE_MS, True)
    _gripper_relief()


def _gripper_relief():
    """Pressure relief pattern from Duane's examples."""
    actual = arm.getPosition(1)
    arm.servoOff(1)
    sleep(0.1)
    arm.setPosition(1, actual, 500, True)


def sort_to_bin(category: str):
    """Pick item, show it to bin, shake to dispense, return and release.

    Flow: PICKUP → grip → BIN → wrist 180 → wrist 180 back → PICKUP → release → HOME

    Args:
        category: one of 'fruit', 'snack', 'drink'
    """
    _require_arm()
    if category not in CATEGORY_MAP:
        raise ValueError(f"Unknown category: {category}. Use one of {list(CATEGORY_MAP.keys())}")

    bin_pose = CATEGORY_MAP[category]

    print(f"Sorting item to {category} bin...")

    # 1. Bend to pickup zone
    print("  -> PICKUP")
    move_body(PICKUP)
    sleep(0.3)

    # 2. Grip the item
    print("  -> GRIP CLOSE")
    gripper_close()
    sleep(0.3)

    # 3. Move to bin position (still gripping)
    print(f"  -> BIN ({category})")
    move_body(bin_pose)
    sleep(0.3)

    # 4. Wrist rotation 180 (servo 2 / index 1: ~500 center → ~0)
    print("  -> WRIST 180")
    arm.setPosition(2, 0, MOVE_MS, True)
    sleep(0.3)

    # 5. Wrist rotation 180 back (reverse to ~1000)
    print("  -> WRIST 180 REVERSE")
    arm.setPosition(2, 1000, MOVE_MS, True)
    sleep(0.3)

    # 6. Return to pickup (still gripping)
    print("  -> PICKUP (return)")
    move_body(PICKUP)
    sleep(0.3)

    # 7. Open gripper to release
    print("  -> GRIP OPEN")
    gripper_open()
    sleep(0.3)

    # 8. Return home
    print("  -> HOME")
    move_to_pose(HOME)

    print("  Done!")


if __name__ == "__main__":
    # Quick test: cycle through all positions
    connect()
    print("Testing arm control...")
    
    print("\n1. Moving to HOME")
    move_to_pose(HOME)
    gripper_open()
    sleep(1)
    
    print("\n2. Moving to PICKUP")
    move_to_pose(PICKUP)
    sleep(1)
    
    print("\n3. Testing gripper")
    gripper_close()
    sleep(0.5)
    gripper_open()
    sleep(1)
    
    print("\n4. Back to HOME")
    move_to_pose(HOME)
    
    print("\nArm control test complete!")
