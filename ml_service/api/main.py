"""
PauchAI API
  - POST /predict          single pouch cost prediction
  - POST /predict/batch    batch cost prediction
  - POST /search           semantic search over pouch catalogue

Run:  uvicorn api.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from embeddings import load_model as load_embedding_model, embed

MODEL_PATH = Path(__file__).parent.parent / "models" / "pouch_cost_model.joblib"

_cost_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cost_model
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Model not found at {MODEL_PATH}. Run 'python src/train.py' first."
        )
    _cost_model = joblib.load(MODEL_PATH)
    load_embedding_model()   # warm up sentence-transformer
    yield
    _cost_model = None


app = FastAPI(
    title="PauchAI API",
    version="2.0.0",
    description="Cost prediction + semantic search for flexible packaging pouches.",
    lifespan=lifespan,
)


# ── Shared models ─────────────────────────────────────────────────────────────

class PouchInput(BaseModel):
    width: float          = Field(..., gt=0)
    height: float         = Field(..., gt=0)
    gusset: float         = Field(0.0, ge=0)
    material_type: Literal["PET+PE", "BOPP+CPP", "Paper", "Foil"]
    thickness: float      = Field(..., gt=0)
    printing_type: Literal["none", "flexo", "rotogravure"]
    quantity: int         = Field(..., gt=0)
    pouch_type: Literal["3-side-seal", "stand-up", "center-seal"]
    zip_lock: Literal["yes", "no"]

    model_config = {"json_schema_extra": {"example": {
        "width": 15.0, "height": 22.0, "gusset": 5.0,
        "material_type": "PET+PE", "thickness": 100,
        "printing_type": "flexo", "quantity": 10000,
        "pouch_type": "stand-up", "zip_lock": "yes",
    }}}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "cost_model_loaded": _cost_model is not None}


# ── Cost prediction ───────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    predicted_cost_per_pouch: float
    total_estimated_cost: float
    currency: str = "INR"


class BatchPredictionItem(BaseModel):
    row: int
    predicted_cost_per_pouch: float
    total_estimated_cost: float
    currency: str = "INR"


def _predict_df(df: pd.DataFrame) -> np.ndarray:
    if _cost_model is None:
        raise HTTPException(503, "Cost model not loaded")
    return _cost_model.predict(df)


@app.post("/predict", response_model=PredictionResponse)
def predict(pouch: PouchInput):
    df = pd.DataFrame([pouch.model_dump(exclude={"quantity"})])
    df["quantity"] = pouch.quantity
    cost = round(max(float(_predict_df(df)[0]), 0.01), 4)
    return PredictionResponse(
        predicted_cost_per_pouch=cost,
        total_estimated_cost=round(cost * pouch.quantity, 2),
    )


@app.post("/predict/batch", response_model=list[BatchPredictionItem])
def predict_batch(pouches: list[PouchInput]):
    if not pouches:
        return []
    df = pd.DataFrame([p.model_dump() for p in pouches])
    costs = _predict_df(df)
    return [
        BatchPredictionItem(
            row=i + 1,
            predicted_cost_per_pouch=round(max(float(c), 0.01), 4),
            total_estimated_cost=round(max(float(c), 0.01) * p.quantity, 2),
        )
        for i, (p, c) in enumerate(zip(pouches, costs))
    ]


# ── Semantic search ───────────────────────────────────────────────────────────

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500,
                       example="500g food pouch with zip lock for snacks")
    limit: int = Field(5, ge=1, le=20)
    food_safe_only: bool = False
    material_type: str | None = None
    zip_lock: Literal["yes", "no"] | None = None


class SearchResultItem(BaseModel):
    id: int
    item_name: str = ""
    item_category: str = ""
    description: str
    similarity: float
    width: float
    height: float
    gusset: float
    material_type: str
    thickness: int
    printing_type: str
    pouch_type: str
    zip_lock: str
    food_grade: str = "no"
    barrier_level: str = ""
    shelf_life_months: int = 0
    quantity: int = 0
    cost_per_pouch: float = 0.0


@app.post("/search", response_model=list[SearchResultItem])
def search(q: SearchQuery):
    from search import search as do_search
    query_vec = embed(q.query)
    rows = do_search(
        query_vec,
        limit=q.limit,
        food_safe_only=q.food_safe_only,
        material_type=q.material_type,
        zip_lock=q.zip_lock,
    )
    return [SearchResultItem(**r) for r in rows]
