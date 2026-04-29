"""
Import pouch records from CSV into file store and (optionally) PostgreSQL.

Usage:
    python src/import_csv.py                    # append to existing data
    python src/import_csv.py --replace          # replace all existing data
    python src/import_csv.py --csv path/to.csv  # custom CSV path
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from embeddings import embed_batch
from search import save_file_store, DATA_DIR, CATALOGUE_PATH, EMBEDDINGS_PATH


CSV_PATH = Path(__file__).parent.parent / "data" / "pouch_semantic_search_1000_records.csv"


def qty_to_range(qty: int) -> str:
    if qty < 5_000:
        return "1,000-5,000"
    if qty < 25_000:
        return "5,000-25,000"
    if qty < 100_000:
        return "25,000-100,000"
    return "100,000+"


def load_csv(path: Path) -> list[dict]:
    records = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                qty = int(float(row["quantity"]))
                records.append({
                    "id":             int(row["record_id"]),
                    "description":    row["description_for_semantic_search"].strip(),
                    "width":          float(row["width_cm"]),
                    "height":         float(row["height_cm"]),
                    "gusset":         float(row["gusset_cm"]),
                    "material_type":  row["material_type"].strip(),
                    "thickness":      int(float(row["thickness_micron"])),
                    "printing_type":  row["printing_type"].strip(),
                    "pouch_type":     row["recommended_pouch_type"].strip(),
                    "zip_lock":       row["zip_lock"].strip().lower(),
                    "quantity_range": qty_to_range(qty),
                    "food_safe":      row["food_grade"].strip().lower() == "yes",
                })
            except (ValueError, KeyError) as e:
                print(f"  Skipping row {row.get('record_id', '?')}: {e}")
    return records


def load_existing_file_store() -> tuple[list[dict], np.ndarray | None]:
    if not CATALOGUE_PATH.exists():
        return [], None
    with open(CATALOGUE_PATH) as f:
        records = json.load(f)
    embeddings = np.load(EMBEDDINGS_PATH) if EMBEDDINGS_PATH.exists() else None
    return records, embeddings


def import_to_postgres(records: list[dict], embeddings: list[np.ndarray]) -> None:
    try:
        from db import create_schema, insert_pouches, get_conn, count_pouches
        create_schema()
        for r, emb in zip(records, embeddings):
            r["embedding"] = emb
        insert_pouches(records)
        print(f"  Inserted {len(records)} rows into PostgreSQL.")
    except Exception as e:
        print(f"  PostgreSQL not available ({e}) — skipped.")


def main(csv_path: Path, replace: bool) -> None:
    print(f"Reading CSV: {csv_path}")
    new_records = load_csv(csv_path)
    print(f"  Loaded {len(new_records)} records from CSV.")

    if replace:
        all_records, existing_embeddings = [], None
        print("  Replace mode: discarding existing file store.")
    else:
        all_records, existing_embeddings = load_existing_file_store()
        print(f"  Existing file store: {len(all_records)} records.")

    # Assign consecutive IDs starting after existing records
    offset = len(all_records)
    for i, r in enumerate(new_records):
        r["id"] = offset + i + 1

    print(f"Generating embeddings for {len(new_records)} descriptions…")
    descriptions = [r["description"] for r in new_records]
    new_embeddings = embed_batch(descriptions, show_progress=True)

    # Combine with existing
    combined_records = all_records + new_records
    if existing_embeddings is not None and len(existing_embeddings) > 0:
        combined_embeddings = list(existing_embeddings) + list(new_embeddings)
    else:
        combined_embeddings = list(new_embeddings)

    save_file_store(combined_records, combined_embeddings)
    print(f"File store updated: {len(combined_records)} total records.")

    # Also insert new records into PostgreSQL if available
    print("Inserting into PostgreSQL…")
    if replace:
        try:
            from db import create_schema, get_conn
            create_schema()
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("TRUNCATE TABLE pouches RESTART IDENTITY")
                conn.commit()
            print("  Cleared existing PostgreSQL rows.")
            import_to_postgres(combined_records, combined_embeddings)
        except Exception as e:
            print(f"  PostgreSQL not available ({e}) — skipped.")
    else:
        import_to_postgres(new_records, new_embeddings)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSV into PauchAI pouch database")
    parser.add_argument("--csv",     default=str(CSV_PATH), help="Path to CSV file")
    parser.add_argument("--replace", action="store_true",   help="Replace all existing data")
    args = parser.parse_args()
    main(Path(args.csv), args.replace)
