"""
Load pouch_items1 from PostgreSQL, compute embeddings, and save to the file
store (catalogue.json + embeddings.npy).  Works WITHOUT the pgvector extension.

If pgvector IS installed, also writes the vectors back into pouch_items1 so
the faster HNSW index can be used.

Usage:
    python src/embed_pouch_items1.py
    python src/embed_pouch_items1.py --batch-size 128
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import load_all_pouch_items1, count_pouch_items1
from embeddings import embed_batch
from search import save_file_store


def main(batch_size: int) -> None:
    total = count_pouch_items1()
    print(f"pouch_items1 has {total} rows.")

    print("Reading all records from pouch_items1...")
    records = load_all_pouch_items1()
    if not records:
        print("No records found — nothing to do.")
        return

    descriptions = [r["description"] for r in records]
    print(f"Computing embeddings for {len(records)} descriptions "
          f"in batches of {batch_size}...")

    embeddings = embed_batch(descriptions, show_progress=True)

    # Save file store — this is the primary search backend when pgvector is absent
    save_file_store(records, embeddings)
    print(f"File store updated with {len(records)} real pouch_items1 records.")

    # Optionally write vectors into PostgreSQL if pgvector is available
    try:
        from db import migrate_pouch_items1, update_embeddings_batch
        print("pgvector detected — migrating pouch_items1 table...")
        migrate_pouch_items1()
        pairs = [(r["id"], emb) for r, emb in zip(records, embeddings)]
        for start in range(0, len(pairs), batch_size):
            update_embeddings_batch(pairs[start: start + batch_size])
            done = min(start + batch_size, len(pairs))
            print(f"  [{done}/{len(pairs)}] embeddings written to PostgreSQL")
        print("PostgreSQL embeddings updated.")
    except Exception as e:
        print(f"pgvector not available ({e}) — using file store only (that's fine).")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Embed pouch_items1 descriptions and save to file store / PostgreSQL."
    )
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    main(args.batch_size)
