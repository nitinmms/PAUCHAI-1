"""
Generate records 101–1000 and append to the existing CSV.
Run: python src/generate_csv_records.py
"""

import csv
import random
import math
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "data" / "pouch_semantic_search_1000_records.csv"

random.seed(42)

ITEMS = [
    ("Wheat Flour",        "dry food",    500,   "stand-up",     "Paper",       True,  "low",    12),
    ("Rice",               "dry food",    1000,  "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Sugar",              "dry food",    500,   "3-side seal",  "PET+PE",      True,  "medium", 18),
    ("Salt",               "dry food",    1000,  "3-side seal",  "PET+PE",      True,  "low",    24),
    ("Namkeen",            "snack",       100,   "center seal",  "BOPP+CPP",    True,  "low",    6),
    ("Namkeen",            "snack",       200,   "center seal",  "PET+PE",      True,  "medium", 6),
    ("Namkeen",            "snack",       500,   "stand-up",     "BOPP+CPP",    True,  "low",    6),
    ("Chips",              "snack",       25,    "3-side seal",  "MET BOPP+CPP",True,  "medium", 6),
    ("Chips",              "snack",       50,    "center seal",  "BOPP+CPP",    True,  "low",    6),
    ("Chips",              "snack",       150,   "center seal",  "MET BOPP+CPP",True,  "medium", 6),
    ("Biscuits",           "snack",       100,   "3-side seal",  "BOPP+CPP",    True,  "low",    9),
    ("Cookies",            "snack",       200,   "stand-up",     "BOPP+CPP",    True,  "low",    6),
    ("Crackers",           "snack",       150,   "3-side seal",  "BOPP+CPP",    True,  "low",    6),
    ("Popcorn",            "snack",       100,   "center seal",  "PET+PE",      True,  "medium", 6),
    ("Dry Fruits",         "premium food",100,   "stand-up",     "PET+ALU+PE",  True,  "high",   12),
    ("Dry Fruits",         "premium food",250,   "stand-up",     "PET+ALU+PE",  True,  "high",   12),
    ("Dry Fruits",         "premium food",500,   "stand-up",     "PET+ALU+PE",  True,  "high",   12),
    ("Almonds",            "premium food",200,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Cashews",            "premium food",250,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Pistachios",         "premium food",200,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Walnuts",            "premium food",250,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Raisins",            "premium food",200,   "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Mixed Nuts",         "premium food",300,   "stand-up",     "PET+ALU+PE",  True,  "high",   12),
    ("Tea Leaves",         "dry food",    100,   "3-side seal",  "PET+PE",      True,  "medium", 12),
    ("Tea Leaves",         "dry food",    250,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Tea Leaves",         "dry food",    500,   "stand-up",     "PET+ALU+PE",  True,  "high",   24),
    ("Green Tea",          "dry food",    100,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Herbal Tea",         "dry food",    50,    "3-side seal",  "PET+PE",      True,  "medium", 12),
    ("Coffee Powder",      "dry food",    200,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Coffee Beans",       "dry food",    250,   "stand-up",     "PET+ALU+PE",  True,  "high",   24),
    ("Ground Coffee",      "dry food",    500,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Instant Coffee",     "dry food",    100,   "3-side seal",  "PET+ALU+PE",  True,  "high",   24),
    ("Protein Powder",     "nutrition",   250,   "flat bottom",  "PET+ALU+PE",  True,  "high",   18),
    ("Protein Powder",     "nutrition",   500,   "flat bottom",  "PET+ALU+PE",  True,  "high",   18),
    ("Protein Powder",     "nutrition",   1000,  "flat bottom",  "PET+ALU+PE",  True,  "high",   18),
    ("Whey Protein",       "nutrition",   500,   "flat bottom",  "PET+ALU+PE",  True,  "high",   18),
    ("Mass Gainer",        "nutrition",   1000,  "flat bottom",  "PET+ALU+PE",  True,  "high",   18),
    ("Pre-workout",        "nutrition",   300,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("BCAA Powder",        "nutrition",   300,   "stand-up",     "PET+ALU+PE",  True,  "high",   18),
    ("Multivitamins",      "pharma",      100,   "stand-up",     "PET+ALU+PE",  False, "high",   24),
    ("Capsules",           "pharma",      50,    "3-side seal",  "PET+ALU+PE",  False, "high",   24),
    ("Tablets",            "pharma",      100,   "3-side seal",  "PET+ALU+PE",  False, "high",   36),
    ("Spices",             "dry food",    50,    "3-side seal",  "PET+PE",      True,  "medium", 12),
    ("Spices",             "dry food",    100,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Turmeric Powder",    "dry food",    100,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Chilli Powder",      "dry food",    100,   "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Coriander Powder",   "dry food",    100,   "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Garam Masala",       "dry food",    100,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Pulses",             "dry food",    500,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Pulses",             "dry food",    1000,  "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Lentils",            "dry food",    500,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Chickpeas",          "dry food",    500,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Rajma",              "dry food",    500,   "stand-up",     "PET+PE",      True,  "medium", 18),
    ("Cereals",            "dry food",    500,   "stand-up",     "BOPP+CPP",    True,  "low",    12),
    ("Oats",               "dry food",    500,   "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Muesli",             "dry food",    500,   "stand-up",     "BOPP+CPP",    True,  "low",    12),
    ("Cornflakes",         "dry food",    500,   "stand-up",     "BOPP+CPP",    True,  "low",    12),
    ("Granola",            "dry food",    300,   "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Pet Food",           "pet",         500,   "stand-up",     "PET+PE",      False, "medium", 18),
    ("Pet Food",           "pet",         1000,  "stand-up",     "PET+PE",      False, "medium", 18),
    ("Dog Treats",         "pet",         200,   "stand-up",     "PET+PE",      False, "medium", 12),
    ("Cat Food",           "pet",         500,   "stand-up",     "PET+PE",      False, "medium", 18),
    ("Fertilizer",        "agri",         500,   "side gusset",  "LDPE",        False, "low",    24),
    ("Fertilizer",        "agri",         1000,  "side gusset",  "LDPE",        False, "low",    24),
    ("Fertilizer",        "agri",         2000,  "side gusset",  "PET+PE",      False, "medium", 24),
    ("Seeds",              "agri",        100,   "3-side seal",  "BOPP+CPP",    False, "low",    18),
    ("Seeds",              "agri",        250,   "3-side seal",  "PET+PE",      False, "medium", 18),
    ("Pesticide",          "agri",        500,   "stand-up",     "LDPE",        False, "medium", 18),
    ("Herbicide",          "agri",        500,   "stand-up",     "NYLON+PE",    False, "high",   24),
    ("Fungicide",          "agri",        250,   "stand-up",     "NYLON+PE",    False, "high",   24),
    ("Organic Fertilizer", "agri",        1000,  "side gusset",  "Kraft+PE",    False, "medium", 18),
    ("Chocolate",          "confectionery",50,   "3-side seal",  "PET+ALU+PE",  True,  "high",   12),
    ("Chocolate",          "confectionery",100,  "stand-up",     "PET+ALU+PE",  True,  "high",   12),
    ("Candy",              "confectionery",200,  "stand-up",     "BOPP+CPP",    True,  "low",    12),
    ("Toffee",             "confectionery",200,  "stand-up",     "BOPP+CPP",    True,  "low",    12),
    ("Gummies",            "confectionery",100,  "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Bakery Mix",         "bakery",       500,  "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Cake Mix",           "bakery",       500,  "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Pancake Mix",        "bakery",       500,  "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Bread Mix",          "bakery",       500,  "stand-up",     "PET+PE",      True,  "medium", 12),
    ("Flour",              "bakery",       1000, "stand-up",     "Paper",       True,  "low",    12),
    ("Cocoa Powder",       "bakery",       200,  "stand-up",     "PET+ALU+PE",  True,  "high",   24),
    ("Yeast",              "bakery",       100,  "3-side seal",  "PET+ALU+PE",  True,  "high",   24),
    ("Washing Powder",     "household",   500,   "stand-up",     "LDPE",        False, "low",    24),
    ("Detergent Powder",   "household",  1000,   "stand-up",     "LDPE",        False, "low",    24),
    ("Soap Powder",        "household",   500,   "stand-up",     "LDPE",        False, "low",    24),
    ("Dish Soap",          "household",   500,   "stand-up",     "LDPE",        False, "low",    24),
    ("Bleach Powder",      "household",   500,   "stand-up",     "NYLON+PE",    False, "high",   24),
    ("Fertilizer Sample",  "agri",       1000,  "side gusset",   "PET+PE",      True,  "medium", 18),
    ("Fertilizer Sample",  "agri",       1500,  "side gusset",   "LDPE",        False, "low",    18),
    ("Fertilizer Sample",  "agri",       2000,  "side gusset",   "PET+PE",      False, "medium", 18),
    ("Organic Seeds",      "agri",        100,  "3-side seal",   "Kraft+PE",    False, "low",    18),
    ("Microgreens Seeds",  "agri",         50,  "3-side seal",   "Kraft+PE",    False, "low",    12),
    ("Sauce Powder",       "dry food",    100,  "3-side seal",   "PET+ALU+PE",  True,  "high",   18),
    ("Gravy Mix",          "dry food",    100,  "3-side seal",   "PET+PE",      True,  "medium", 12),
    ("Soup Powder",        "dry food",    100,  "3-side seal",   "PET+ALU+PE",  True,  "high",   18),
    ("Noodles",            "dry food",    70,   "center seal",   "BOPP+CPP",    True,  "low",    12),
    ("Pasta",              "dry food",    500,  "stand-up",      "BOPP+CPP",    True,  "low",    18),
]

POUCH_TYPE_SIZES = {
    "stand-up":    [(10,15,0),(12,18,3),(15,22,5),(18,28,6),(20,30,6),(22,32,7),(25,35,8),(30,40,10)],
    "3-side seal": [(8,12,0),(10,14,0),(12,16,0),(15,20,0),(18,25,0),(22,30,0)],
    "center seal": [(8,14,0),(10,16,0),(12,18,0),(15,22,0),(18,28,0)],
    "side gusset": [(20,35,8),(25,40,10),(30,45,12),(35,50,12),(40,55,15)],
    "flat bottom": [(12,18,5),(15,22,6),(18,28,7),(20,30,8),(22,32,9)],
}

THICKNESS_BY_MATERIAL = {
    "PET+PE":      [75, 90, 100, 125],
    "BOPP+CPP":    [50, 65, 80, 100],
    "PET+ALU+PE":  [90, 110, 130, 150],
    "LDPE":        [70, 80, 90, 100],
    "NYLON+PE":    [80, 100, 125, 150],
    "Kraft+PE":    [80, 90, 100, 120],
    "MET BOPP+CPP":[60, 70, 80, 90],
    "Foil":        [90, 110, 130, 150],
    "Paper":       [80, 100, 120, 150],
}

MATERIAL_RATE = {
    "PET+PE":      (130, 180),
    "BOPP+CPP":    (100, 160),
    "PET+ALU+PE":  (220, 310),
    "LDPE":        (90, 130),
    "NYLON+PE":    (180, 260),
    "Kraft+PE":    (110, 160),
    "MET BOPP+CPP":(140, 200),
    "Foil":        (200, 280),
    "Paper":       (80, 130),
}

PRINTING_TYPES = ["none", "1 color", "2 color", "full color"]
QUANTITIES = [500, 1000, 2000, 5000, 10000, 25000, 50000, 100000]
PRINTING_COST = {"none": 0.0, "1 color": 0.5, "2 color": 0.85, "full color": 1.3}
MAKING_COST_RANGE = (0.8, 8.0)
WASTAGE_RANGE = (3, 9)
MARGIN_RANGE = (8, 22)


def get_size(pouch_type: str, weight_g: int):
    sizes = POUCH_TYPE_SIZES.get(pouch_type, POUCH_TYPE_SIZES["stand-up"])
    # Choose size proportional to weight
    idx = min(int(math.log2(max(weight_g, 10) / 20)), len(sizes) - 1)
    idx = max(0, min(idx, len(sizes) - 1))
    return sizes[idx]


def compute_costs(w, h, g, material, thickness, printing, quantity):
    area_cm2 = (w + g) * (h + g + 3)  # rough film area
    film_wt = round(area_cm2 * thickness * 1.25 / 1000, 2)  # grams (density ~1.25 g/cm³ * microns/10000)
    lo, hi = MATERIAL_RATE[material]
    mat_rate = round(random.uniform(lo, hi), 2)
    mat_cost = round(film_wt * mat_rate / 1000, 4)
    print_cost = round(PRINTING_COST.get(printing, 0) + random.uniform(-0.1, 0.2), 2)
    print_cost = max(0, print_cost)
    making = round(random.uniform(*MAKING_COST_RANGE), 2)
    wastage_pct = random.randint(*WASTAGE_RANGE)
    margin_pct = random.randint(*MARGIN_RANGE)
    base = mat_cost + print_cost + making
    actual = round(base * (1 + wastage_pct / 100) * (1 + margin_pct / 100), 2)
    return film_wt, mat_rate, print_cost, making, wastage_pct, margin_pct, actual


def make_desc(name, category, weight, pouch_type, material, thickness, printing, zip_lock, barrier, quantity):
    pl = "with zip lock" if zip_lock == "yes" else "without zip lock"
    return (
        f"{weight}g {name.lower()} {pouch_type} pouch {material} {thickness} micron "
        f"{printing} printing {pl} {barrier} barrier suitable for {category}"
    )


def generate_rows(start_id: int, count: int) -> list[list]:
    rows = []
    item_pool = ITEMS * (count // len(ITEMS) + 2)
    random.shuffle(item_pool)

    for i in range(count):
        rec_id = start_id + i
        name, cat, base_wt, ptype_hint, mat_hint, fg, barrier, shelf = item_pool[i]

        # slight weight variation
        weight = base_wt + random.choice([-50, 0, 0, 50, 100, 200]) if base_wt > 100 else base_wt
        weight = max(25, weight)

        pouch_type = ptype_hint
        material = mat_hint
        thick_choices = THICKNESS_BY_MATERIAL.get(material, [80, 100, 120])
        thickness = random.choice(thick_choices)
        w, h, g = get_size(pouch_type, weight)
        # small random variation on dimensions
        w = round(w + random.uniform(-1.5, 1.5), 1)
        h = round(h + random.uniform(-2, 2), 1)
        g = round(g + random.uniform(-0.5, 0.5), 1) if g > 0 else 0

        printing = random.choice(PRINTING_TYPES)
        zip_lk = "yes" if (fg and random.random() < 0.5) else "no"
        qty = random.choice(QUANTITIES)

        film_wt, mat_rate, print_cost, making, wastage, margin, actual = compute_costs(
            w, h, g, material, thickness, printing, qty
        )

        desc = make_desc(name, cat, weight, pouch_type, material, thickness, printing, zip_lk, barrier, qty)

        rows.append([
            rec_id, name, cat, weight, pouch_type, material,
            w, h, g, thickness, printing, zip_lk,
            "yes" if fg else "no", barrier, shelf, qty,
            film_wt, mat_rate, print_cost, making, wastage, margin, actual,
            desc
        ])
    return rows


def main():
    # Count existing rows
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        existing = sum(1 for _ in f) - 1  # subtract header
    print(f"Existing rows: {existing}")

    needed = 1000 - existing
    if needed <= 0:
        print("CSV already has 1000 rows — nothing to do.")
        return

    rows = generate_rows(start_id=existing + 1, count=needed)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Appended {len(rows)} rows. CSV now has {existing + len(rows)} data rows.")


if __name__ == "__main__":
    main()
