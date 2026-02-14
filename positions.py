"""Calibrated positions for Project Lend food bank.

Run `python3 calibrate.py` and paste your recorded values here.
Each pose is a list of 6 servo positions (units 0-1000), servos 1-6.
"""

# Safe resting position
HOME = [500, 500, 500, 500, 500, 500]

# Donation zone (where people place items)
PICKUP = [500, 500, 500, 500, 500, 500]

# Bin positions
BIN_NONPERISHABLE = [500, 500, 500, 500, 500, 500]  # Cans, boxes, pasta
BIN_SNACKS = [500, 500, 500, 500, 500, 500]         # Chips, granola bars, candy
BIN_PROTEIN = [500, 500, 500, 500, 500, 500]         # Protein bars, peanut butter

# Map vision categories to bin positions
CATEGORY_MAP = {
    "nonperishable": BIN_NONPERISHABLE,
    "snack": BIN_SNACKS,
    "protein": BIN_PROTEIN,
}
