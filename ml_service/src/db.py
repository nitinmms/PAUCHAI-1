"""
Database connection and schema management.
Requires PostgreSQL with the pgvector extension (docker-compose.yml).
"""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "PouchAi"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "Asimov78*%#"),
}

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


@contextmanager
def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)
    try:
        yield conn
    finally:
        conn.close()


# ── pouch_items1 plain read (no pgvector needed) ──────────────────────────────

def load_all_pouch_items1() -> list[dict]:
    """Read every row from pouch_items1; no pgvector required.
    Returns records normalised to the field names used by the API / file store.
    """
    import psycopg2 as _pg
    from psycopg2.extras import RealDictCursor as _RDC
    conn = _pg.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=_RDC) as cur:
            cur.execute("""
                SELECT
                    record_id                                   AS id,
                    COALESCE(item_name, '')                     AS item_name,
                    COALESCE(item_category, '')                 AS item_category,
                    description_for_semantic_search             AS description,
                    width_cm::float                             AS width,
                    height_cm::float                            AS height,
                    gusset_cm::float                            AS gusset,
                    COALESCE(material_type, '')                 AS material_type,
                    thickness_micron::int                       AS thickness,
                    COALESCE(printing_type, '')                 AS printing_type,
                    COALESCE(recommended_pouch_type, '')        AS pouch_type,
                    CASE WHEN zip_lock  THEN 'yes' ELSE 'no' END AS zip_lock,
                    CASE WHEN food_grade THEN 'yes' ELSE 'no' END AS food_grade,
                    COALESCE(barrier_level, '')                 AS barrier_level,
                    COALESCE(shelf_life_months, 0)              AS shelf_life_months,
                    COALESCE(quantity, 0)                       AS quantity,
                    COALESCE(actual_cost_per_pouch_inr, 0)::float AS cost_per_pouch
                FROM pouch_items1
                ORDER BY record_id
            """)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def count_pouch_items1() -> int:
    import psycopg2 as _pg
    conn = _pg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pouch_items1")
            return cur.fetchone()[0]
    finally:
        conn.close()


# ── pouch_items1 pgvector search (requires pgvector extension) ────────────────

def migrate_pouch_items1() -> None:
    """Add embedding VECTOR column + HNSW index to pouch_items1."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                ALTER TABLE pouch_items1
                ADD COLUMN IF NOT EXISTS embedding VECTOR({EMBEDDING_DIM})
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS pouch_items1_hnsw_idx
                ON pouch_items1 USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
        conn.commit()
    print("pouch_items1 migration done (embedding column + HNSW index ready).")


def get_records_without_embeddings() -> list[dict]:
    sql = """
        SELECT record_id, description_for_semantic_search
        FROM pouch_items1
        WHERE embedding IS NULL
        ORDER BY record_id
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]


def update_embeddings_batch(id_embedding_pairs: list[tuple]) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for record_id, embedding in id_embedding_pairs:
                cur.execute(
                    "UPDATE pouch_items1 SET embedding = %s WHERE record_id = %s",
                    (embedding, record_id),
                )
        conn.commit()


def search_pouch_items1(
    query_embedding,
    limit: int = 5,
    food_safe_only: bool = False,
    material_type: str | None = None,
    zip_lock: str | None = None,
) -> list[dict]:
    filters, params = [], []

    if food_safe_only:
        filters.append("food_grade = true")
    if material_type:
        filters.append("material_type = %s")
        params.append(material_type)
    if zip_lock:
        filters.append("zip_lock = %s")
        params.append(zip_lock == "yes")   # convert "yes"/"no" → boolean

    where = ("WHERE embedding IS NOT NULL AND " + " AND ".join(filters)) if filters \
        else "WHERE embedding IS NOT NULL"

    sql = f"""
        SELECT
            record_id                                       AS id,
            COALESCE(item_name, '')                         AS item_name,
            COALESCE(item_category, '')                     AS item_category,
            description_for_semantic_search                 AS description,
            width_cm::float                                 AS width,
            height_cm::float                                AS height,
            gusset_cm::float                                AS gusset,
            COALESCE(material_type, '')                     AS material_type,
            thickness_micron::int                           AS thickness,
            COALESCE(printing_type, '')                     AS printing_type,
            COALESCE(recommended_pouch_type, '')            AS pouch_type,
            CASE WHEN zip_lock  THEN 'yes' ELSE 'no' END   AS zip_lock,
            CASE WHEN food_grade THEN 'yes' ELSE 'no' END  AS food_grade,
            COALESCE(barrier_level, '')                     AS barrier_level,
            COALESCE(shelf_life_months, 0)                  AS shelf_life_months,
            COALESCE(quantity, 0)                           AS quantity,
            COALESCE(actual_cost_per_pouch_inr, 0)::float  AS cost_per_pouch,
            ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS similarity
        FROM pouch_items1
        {where}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    params = [query_embedding, query_embedding] + params + [limit]

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


# ── Legacy pouches table (kept for backward compatibility) ────────────────────

def create_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS pouches (
                    id              SERIAL PRIMARY KEY,
                    description     TEXT NOT NULL,
                    width           FLOAT NOT NULL,
                    height          FLOAT NOT NULL,
                    gusset          FLOAT NOT NULL DEFAULT 0,
                    material_type   VARCHAR(50),
                    thickness       INT,
                    printing_type   VARCHAR(50) DEFAULT 'none',
                    pouch_type      VARCHAR(50),
                    zip_lock        VARCHAR(5) DEFAULT 'no',
                    quantity_range  VARCHAR(50),
                    food_safe       BOOLEAN DEFAULT false,
                    embedding       VECTOR({EMBEDDING_DIM})
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS pouches_hnsw_idx
                ON pouches USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
        conn.commit()
    print("Schema ready.")


def count_pouches() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pouches")
            return cur.fetchone()[0]


def insert_pouches(records: list[dict]) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for r in records:
                cur.execute(
                    """
                    INSERT INTO pouches
                        (description, width, height, gusset, material_type, thickness,
                         printing_type, pouch_type, zip_lock, quantity_range,
                         food_safe, embedding)
                    VALUES
                        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        r["description"], r["width"], r["height"], r["gusset"],
                        r["material_type"], r["thickness"], r["printing_type"],
                        r["pouch_type"], r["zip_lock"], r["quantity_range"],
                        r["food_safe"], r["embedding"],
                    ),
                )
        conn.commit()


def search_similar(
    query_embedding,
    limit: int = 5,
    food_safe_only: bool = False,
    material_type: str | None = None,
    zip_lock: str | None = None,
) -> list[dict]:
    filters, params = [], []

    if food_safe_only:
        filters.append("food_safe = true")
    if material_type:
        filters.append("material_type = %s")
        params.append(material_type)
    if zip_lock:
        filters.append("zip_lock = %s")
        params.append(zip_lock)

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = f"""
        SELECT id, description, width, height, gusset, material_type, thickness,
               printing_type, pouch_type, zip_lock, quantity_range, food_safe,
               ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS similarity
        FROM pouches
        {where}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    params = [query_embedding, query_embedding] + params + [limit]

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
