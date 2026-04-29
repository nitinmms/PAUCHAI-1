"""
Generates synthetic but realistic pouch production cost data for training.
Replace this with your actual Excel dataset when available.
"""

import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)

MATERIAL_BASE_COST = {
    "Foil":     0.015,   # ₹/cm²
    "PET+PE":   0.010,
    "BOPP+CPP": 0.007,
    "Paper":    0.005,
}
PRINTING_ADDON = {"none": 0.0, "flexo": 0.50, "rotogravure": 1.20}
POUCH_MULTIPLIER = {"center-seal": 1.0, "3-side-seal": 1.15, "stand-up": 1.40}
ZIPLOCK_COST = 0.30


def quantity_discount(qty: float) -> float:
    if qty < 1_000:
        return 1.35
    if qty < 10_000:
        return 1.15
    if qty < 100_000:
        return 1.00
    return 0.82


def compute_cost(row: dict) -> float:
    area = 2 * row["width"] * row["height"] + row["gusset"] * (row["width"] + row["height"])
    thickness_factor = row["thickness"] / 100.0
    material = area * MATERIAL_BASE_COST[row["material_type"]] * thickness_factor
    printing = PRINTING_ADDON[row["printing_type"]]
    ziplock = ZIPLOCK_COST if row["zip_lock"] == "yes" else 0.0
    base = (material + printing + ziplock) * POUCH_MULTIPLIER[row["pouch_type"]]
    cost = base * quantity_discount(row["quantity"])
    noise = rng.normal(0, cost * 0.04)  # ±4% noise
    return max(round(cost + noise, 4), 0.50)


def generate(n: int = 2000) -> pd.DataFrame:
    materials   = rng.choice(list(MATERIAL_BASE_COST), n)
    printings   = rng.choice(list(PRINTING_ADDON), n, p=[0.20, 0.45, 0.35])
    pouch_types = rng.choice(list(POUCH_MULTIPLIER), n, p=[0.25, 0.40, 0.35])
    zip_locks   = rng.choice(["yes", "no"], n, p=[0.45, 0.55])

    widths     = rng.uniform(8, 35, n).round(1)
    heights    = rng.uniform(10, 50, n).round(1)
    gussets    = rng.uniform(0, 12, n).round(1)
    thicknesses = rng.choice([50, 75, 100, 125, 150, 200], n)
    quantities = rng.choice(
        [500, 1000, 2000, 5000, 10000, 25000, 50000, 100000, 250000], n,
        p=[0.05, 0.10, 0.15, 0.15, 0.20, 0.15, 0.10, 0.07, 0.03],
    )

    # Stand-up and center-seal pouches typically have a gusset; 3-side usually 0
    for i, pt in enumerate(pouch_types):
        if pt == "3-side-seal":
            gussets[i] = 0.0
        elif pt == "stand-up" and gussets[i] < 3:
            gussets[i] = rng.uniform(3, 10)

    rows = []
    for i in range(n):
        row = dict(
            width=widths[i], height=heights[i], gusset=gussets[i],
            material_type=materials[i], thickness=thicknesses[i],
            printing_type=printings[i], quantity=int(quantities[i]),
            pouch_type=pouch_types[i], zip_lock=zip_locks[i],
        )
        row["actual_cost_per_pouch"] = compute_cost(row)
        rows.append(row)

    df = pd.DataFrame(rows)

    # Inject ~3% missing values to simulate real data
    for col in ["gusset", "thickness", "printing_type"]:
        mask = rng.random(n) < 0.03
        df.loc[mask, col] = np.nan

    return df


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "data" / "pouches_sample.xlsx"
    df = generate(2000)
    df.to_excel(out, index=False)
    print(f"Saved {len(df)} rows -> {out}")
    print(df.describe())
