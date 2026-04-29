"""
Generate ~120 diverse pouch records, embed their descriptions, and store in PostgreSQL.

Usage:
    python src/seed_db.py
    python src/seed_db.py --reset    # drop existing rows first
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from embeddings import embed_batch
from search import save_file_store

# ── Description building ────────────────────────────────────────────────────

MATERIAL_PROPS = {
    "PET+PE":    "transparent high-barrier moisture-proof food-grade PET/PE laminate, FDA approved, excellent for preserving freshness",
    "BOPP+CPP":  "crystal-clear BOPP/CPP laminate with outstanding moisture barrier and glossy surface finish",
    "Paper":     "eco-friendly kraft paper laminate, biodegradable and sustainable, natural look and feel",
    "Foil":      "aluminium foil laminate with maximum barrier against moisture, light and oxygen, ideal for long shelf life",
}

MATERIAL_USES = {
    "PET+PE":    "dry foods, snacks, spices, grains, pulses, rice, flour, confectionery, bakery products, pet food",
    "BOPP+CPP":  "chips, biscuits, cookies, crackers, dry snacks, cereals, confectionery, bakery products",
    "Paper":     "coffee, tea, flour, sugar, dry goods, organic products, natural foods, spices, gift packaging",
    "Foil":      "coffee beans, ground coffee, pharmaceuticals, nutraceuticals, chemicals, health supplements, moisture-sensitive products",
}

FOOD_SAFE = {"PET+PE": True, "BOPP+CPP": True, "Paper": True, "Foil": False}

POUCH_TYPE_NAMES = {
    "stand-up":    "stand-up doy pack pouch",
    "3-side-seal": "3-side seal flat pouch",
    "center-seal": "center seal pillow pouch",
}

PRINTING_DESC = {
    "none":        "plain unprinted",
    "flexo":       "flexo printed (up to 8 colors, vibrant graphics)",
    "rotogravure": "rotogravure printed (photographic quality, high-volume)",
}

MOQ_RANGES = ["1,000-5,000", "5,000-25,000", "25,000-100,000", "100,000+"]


def capacity_and_use(w: float, h: float) -> tuple[str, str]:
    area = w * h
    if area < 180:
        return "50g-200g", "sachets, samples, spices, trial packs, single-serve units"
    if area < 330:
        return "200g-400g", "snack packs, 250g products, condiments, spices, dry fruits"
    if area < 500:
        return "400g-700g", "500g food products, dry fruits, pulses, snacks, coffee, cereals"
    if area < 750:
        return "700g-1.5kg", "1kg grains, flour, rice, bulk snacks, pet food, industrial food"
    return "1.5kg-5kg", "2kg-5kg bulk packaging, commercial grains, large-format food products"


def make_description(r: dict) -> str:
    w, h, g = r["width"], r["height"], r["gusset"]
    mat     = r["material_type"]
    cap, uses = capacity_and_use(w, h)

    gusset_part = f"{g}cm bottom gusset for self-standing stability, " if g > 0 else ""
    zip_part    = ("resealable zip-lock closure to preserve freshness after opening"
                   if r["zip_lock"] == "yes" else "heat-seal closure")
    fs_part     = "food-grade FDA-approved food-safe material" if r["food_safe"] else "industrial-grade material"

    return (
        f"{w}x{h}cm {POUCH_TYPE_NAMES[r['pouch_type']]} {gusset_part}"
        f"made from {mat} laminate ({MATERIAL_PROPS[mat]}), "
        f"{r['thickness']} micron thickness. "
        f"{zip_part}. {PRINTING_DESC[r['printing_type']]}. "
        f"Capacity approximately {cap}. "
        f"Suitable for: {uses}. Also ideal for {MATERIAL_USES[mat]}. "
        f"{fs_part}. Minimum order quantity: {r['quantity_range']}."
    )


# ── Record generation ────────────────────────────────────────────────────────

SIZES = [
    (10, 15, 0),
    (12, 18, 0),
    (15, 22, 5),
    (18, 28, 6),
    (25, 35, 8),
]
THICKNESSES = [50, 75, 100, 125, 150, 200]


def generate_records() -> list[dict]:
    records = []
    for material in ["PET+PE", "BOPP+CPP", "Paper", "Foil"]:
        for pouch_type in ["stand-up", "3-side-seal", "center-seal"]:
            for zip_lock in ["yes", "no"]:
                for idx, (w, h, g) in enumerate(SIZES):
                    # 3-side-seal and center-seal have no gusset
                    gusset = g if pouch_type == "stand-up" else 0
                    for printing in ["none", "flexo"]:
                        thick = THICKNESSES[idx % len(THICKNESSES)]
                        records.append({
                            "width":          w,
                            "height":         h,
                            "gusset":         gusset,
                            "material_type":  material,
                            "thickness":      thick,
                            "printing_type":  printing,
                            "pouch_type":     pouch_type,
                            "zip_lock":       zip_lock,
                            "quantity_range": MOQ_RANGES[idx % len(MOQ_RANGES)],
                            "food_safe":      FOOD_SAFE[material],
                        })

    # Extra rotogravure records for large premium pouches
    for material in ["PET+PE", "Foil"]:
        for w, h, g in [(15, 22, 5), (18, 28, 6), (25, 35, 8)]:
            records.append({
                "width": w, "height": h, "gusset": g,
                "material_type": material, "thickness": 150,
                "printing_type": "rotogravure",
                "pouch_type": "stand-up", "zip_lock": "yes",
                "quantity_range": "25,000-100,000",
                "food_safe": FOOD_SAFE[material],
            })

    return records


# ── Main ─────────────────────────────────────────────────────────────────────

def seed(reset: bool = False) -> None:
    records = generate_records()
    print(f"Generated {len(records)} pouch records. Embedding descriptions...")

    descriptions = [make_description(r) for r in records]
    for r, d in zip(records, descriptions):
        r["description"] = d
        r["id"] = records.index(r) + 1   # stable id for file store

    embeddings = embed_batch(descriptions, show_progress=True)

    # Always save file-based store (works without PostgreSQL)
    save_file_store(records, embeddings)

    # Also persist to PostgreSQL if available
    try:
        from db import create_schema, insert_pouches, count_pouches
        create_schema()
        existing = count_pouches()
        if existing > 0 and not reset:
            print(f"PostgreSQL already has {existing} pouches. Use --reset to reseed.")
        else:
            if reset:
                from db import get_conn
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("TRUNCATE TABLE pouches RESTART IDENTITY")
                    conn.commit()
            for r, emb in zip(records, embeddings):
                r["embedding"] = emb
            insert_pouches(records)
            print(f"Also seeded {len(records)} pouches into PostgreSQL.")
    except Exception as e:
        print(f"PostgreSQL not available ({e}) — using file store only.")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    seed(args.reset)
