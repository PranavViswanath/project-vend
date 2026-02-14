"""Test xArm 1S connection and basic movement."""
import xarm

arm = xarm.Controller('USB')
print("Connected to xArm!")

# Read current position of servo 2 (shoulder) in units (0-1000)
pos = arm.getPosition(2, False)
print(f"Servo 2 at: {pos}")

# Small move forward and back
arm.setPosition(2, pos + 50, 1000, True)
print("Moved servo 2 forward")

arm.setPosition(2, pos, 1000, True)
print("Returned to start")

# Read all 6 servo positions (useful for calibrating poses later)
positions = [arm.getPosition(i, False) for i in range(1, 7)]
print(f"All servo positions: {positions}")

print("Done!")
