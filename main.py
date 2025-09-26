# main.py — NutriAI API (FastAPI)
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_VERSION = "v1.2"
SCHEMA_NAME = "per_day_items_v1"


def _as_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


# Lu une fois au démarrage (si vous modifiez l'ENV, redémarrez le serveur)
DEMO_FILL = _as_bool(os.getenv("NUTRIAI_DEMO"), False)

# ------------------- FastAPI app -------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Modèles Pydantic -------------------

class MealItem(BaseModel):
    name: str
    qty: float
    unit: str


class Meal(BaseModel):
    name: str | None = None
    items: List[MealItem] = Field(default_factory=list)


class PlanDay(BaseModel):
    day: int
    meals: List[Meal] = Field(default_factory=list)


class GenerateMealPlanRequest(BaseModel):
    age: int
    gender: str
    weight: float
    goal: str
    days: int = Field(gt=0, le=14)


class GenerateMealPlanResponse(BaseModel):
    per_day: List[PlanDay]


# ------------------- Root & util -------------------

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "message": "NutriAI API OK",
        "schema": SCHEMA_NAME,
        "version": APP_VERSION,
        "demo": DEMO_FILL,
    }


@app.get("/__env")
def env() -> Dict[str, Any]:
    return {
        "demo": DEMO_FILL,
        "NUTRIAI_DEMO": os.getenv("NUTRIAI_DEMO"),
        "schema": SCHEMA_NAME,
        "version": APP_VERSION,
    }


@app.get("/__whoami")
def whoami() -> Dict[str, Any]:
    return {"file": str(Path(__file__).resolve())}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


# ------------------- Generate -------------------

def _demo_meals() -> List[Meal]:
    # Un "repas" démo avec 3 items
    return [
        Meal(
            name="Démo",
            items=[
                MealItem(name="Riz", qty=200, unit="g"),
                MealItem(name="Poulet", qty=150, unit="g"),
                MealItem(name="Pomme", qty=1, unit="pc"),
            ],
        )
    ]


@app.post("/generate_meal_plan", response_model=GenerateMealPlanResponse)
def generate_meal_plan(body: GenerateMealPlanRequest) -> GenerateMealPlanResponse:
    per_day: List[PlanDay] = []
    for i in range(1, body.days + 1):
        per_day.append(PlanDay(day=i, meals=_demo_meals() if DEMO_FILL else []))
    return GenerateMealPlanResponse(per_day=per_day)


# ------------------- Aggregate -------------------
# Accepte:
# A) {"per_day":[{"day":1,"items":[{name,qty,unit}, ...]}, ...]}
# B) {"per_day":[{"day":1,"meals":[{"items":[{name,qty,unit}, ...]}, ...]}, ...]}

@app.post("/shopping_aggregate")
def shopping_aggregate(body: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    if "per_day" not in body or not isinstance(body["per_day"], list):
        raise HTTPException(status_code=422, detail="per_day must be a list")

    per_day = body["per_day"]

    def parse_item(raw: Any) -> MealItem | None:
        try:
            # pydantic v2
            return MealItem.model_validate(raw)
        except Exception:
            return None

    items: List[MealItem] = []

    for day in per_day:
        if not isinstance(day, dict):
            continue

        # Schéma A: per_day[].items
        if "items" in day and isinstance(day["items"], list):
            for it in day["items"]:
                p = parse_item(it)
                if p:
                    items.append(p)

        # Schéma B: per_day[].meals[].items
        elif "meals" in day and isinstance(day["meals"], list):
            for meal in day["meals"]:
                if isinstance(meal, dict) and isinstance(meal.get("items"), list):
                    for it in meal["items"]:
                        p = parse_item(it)
                        if p:
                            items.append(p)
        # sinon on ignore la journée

    # Agrégation par (name normalisé, unit)
    totals: Dict[tuple[str, str], float] = {}
    pretty_name: Dict[tuple[str, str], str] = {}

    for it in items:
        key = (it.name.strip().lower(), it.unit.strip())
        totals[key] = totals.get(key, 0.0) + float(it.qty)
        if key not in pretty_name:
            pretty_name[key] = it.name  # conserve la casse "jolie"

    result: Dict[str, Dict[str, Any]] = {}
    for key, qty in totals.items():
        display = pretty_name[key]
        unit = key[1]
        result[display] = {"qty": qty, "unit": unit}

    return result


# Optionnel: exécution locale (utile en dev)
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT") or "10000")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
