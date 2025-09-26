# C:\NutriAI_API\main.py
from __future__ import annotations

import os
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


# Active le remplissage démo si NUTRIAI_DEMO=true
DEMO_FILL = _as_bool(os.getenv("NUTRIAI_DEMO"), False)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Modèles ---------
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

# --------- Utilitaires ---------
def _demo_meals() -> List[Meal]:
    # Un repas démo avec 3 items
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

# --------- Endpoints d'info ---------
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
        "schema": SCHEMA_NAME,
        "version": APP_VERSION,
        "demo": DEMO_FILL,
        "NUTRIAI_DEMO": os.getenv("NUTRIAI_DEMO"),
    }

@app.get("/__whoami")
def whoami() -> Dict[str, Any]:
    # Permet de vérifier QUEL fichier tourne réellement
    return {"file": os.path.abspath(__file__)}

# --------- Génération ---------
@app.post("/generate_meal_plan", response_model=GenerateMealPlanResponse)
def generate_meal_plan(body: GenerateMealPlanRequest) -> GenerateMealPlanResponse:
    per_day: List[PlanDay] = []
    for i in range(1, body.days + 1):
        per_day.append(PlanDay(day=i, meals=_demo_meals() if DEMO_FILL else []))
    return GenerateMealPlanResponse(per_day=per_day)

# --------- Agrégation ---------
# Accepte:
#  A) {"per_day":[{"day":1,"items":[{name,qty,unit}, ...]}, ...]}
#  B) {"per_day":[{"day":1,"meals":[{"items":[{name,qty,unit}, ...]}, ...]}, ...]}
@app.post("/shopping_aggregate")
def shopping_aggregate(body: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    if "per_day" not in body or not isinstance(body["per_day"], list):
        raise HTTPException(status_code=422, detail="per_day must be a list")

    per_day = body["per_day"]
    items: List[MealItem] = []

    def parse_item(raw: Any) -> MealItem | None:
        try:
            return MealItem.model_validate(raw)  # pydantic v2
        except Exception:
            return None

    for day in per_day:
        if not isinstance(day, dict):
            continue
        # Schéma A: per_day[].items
        if isinstance(day.get("items"), list):
            for it in day["items"]:
                p = parse_item(it)
                if p:
                    items.append(p)
        # Schéma B: per_day[].meals[].items
        elif isinstance(day.get("meals"), list):
            for meal in day["meals"]:
                if isinstance(meal, dict) and isinstance(meal.get("items"), list):
                    for it in meal["items"]:
                        p = parse_item(it)
                        if p:
                            items.append(p)

    # Somme par (name, unit)
    totals: Dict[tuple[str, str], float] = {}
    display: Dict[tuple[str, str], str] = {}
    for it in items:
        key = (it.name.strip().lower(), it.unit.strip())
        totals[key] = totals.get(key, 0.0) + float(it.qty)
        display.setdefault(key, it.name)

    result: Dict[str, Dict[str, Any]] = {}
    for key, qty in totals.items():
        pretty = display[key]
        unit = key[1]
        result[pretty] = {"qty": qty, "unit": unit}
    return result
