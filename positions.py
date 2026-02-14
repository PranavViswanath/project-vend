"""Calibrated positions for Project Lend food bank.

Run `python calibrate.py` and paste your recorded values here.
Each pose is a list of 6 servo positions (units 0-1000), servos 1-6.
"""

# Safe resting position
HOME = [505, 501, 109, 526, 511, 508]

# Donation zone (where people place items)
PICKUP = [501, 501, 301, 895, 508, 507]

# Bin positions
BIN_FRUIT = [501, 501, 301, 821, 507, 828]   # Apples, bananas, oranges
BIN_SNACK = [501, 501, 301, 821, 508, 979]   # Chips, granola bars, candy
BIN_DRINK = [501, 501, 301, 801, 509, 720]   # Water bottles, juice, soda

# Map vision categories to bin positions
CATEGORY_MAP = {
    "fruit": BIN_FRUIT,
    "snack": BIN_SNACK,
    "drink": BIN_DRINK,
}
