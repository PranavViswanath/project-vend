"""Calibrated positions for Project Lend food bank.

Run `python3 calibrate.py` and paste your recorded values here.
Each pose is a list of 6 servo positions (units 0-1000), servos 1-6.
"""

# Safe resting position
HOME = [500, 500, 500, 500, 500, 500]

# Donation zone (where people place items)
PICKUP = [500, 500, 500, 500, 500, 500]

# Bin positions
BIN_FRUIT = [500, 500, 500, 500, 500, 500]   # Apples, bananas, oranges
BIN_SNACK = [500, 500, 500, 500, 500, 500]   # Chips, granola bars, candy
BIN_DRINK = [500, 500, 500, 500, 500, 500]   # Water bottles, juice, soda

# Map vision categories to bin positions
CATEGORY_MAP = {
    "fruit": BIN_FRUIT,
    "snack": BIN_SNACK,
    "drink": BIN_DRINK,
}
