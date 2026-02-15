"""Calibrated positions for Project Lend food bank.

Run `python tools/calibrate.py` and positions are saved here automatically.
Each pose is a list of 6 servo positions (units 0-1000), servos 1-6.
"""

# Safe resting position
HOME = [500, 501, 108, 486, 509, 509]

# Donation zone (where people place items)
PICKUP = [499, 501, 109, 611, 343, 509]

# Bin positions
BIN_FRUIT = [500, 501, 109, 510, 525, 877]   # Apples, bananas, oranges
BIN_SNACK = [499, 501, 108, 510, 525, 877]   # Chips, granola bars, candy
BIN_DRINK = [500, 501, 108, 510, 525, 109]   # Water bottles, juice, soda

# Map vision categories to bin positions
CATEGORY_MAP = {
    "fruit": BIN_FRUIT,
    "snack": BIN_SNACK,
    "drink": BIN_DRINK,
}
