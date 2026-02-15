"""Record only the PICKUP position by moving arm by hand.

Usage:
    python calibrate_pickup.py

Physically move the arm to the pickup position, then press Enter to record.
"""
import xarm

arm = xarm.Controller('USB')
print("=== PICKUP Position Calibration ===")
print("Physically move the arm to the pickup position, then press Enter")
print("Servos will go limp so you can move the arm by hand.\n")

# Turn off all servo motors so arm can be freely moved
for i in range(1, 7):
    arm.servoOff(i)

print("\nPICKUP:")
print("  -> Gripper over donation zone (where people place items)")
input("  Press Enter when ready...")

pose = [arm.getPosition(i) for i in range(1, 7)]
print(f"  Recorded: {pose}")

print("\n" + "=" * 60)
print("Copy this into positions.py:")
print("=" * 60)
print(f"PICKUP = {pose}")
