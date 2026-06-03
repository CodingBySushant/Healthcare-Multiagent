"""
Meal Planner Agent — direct Groq call returning structured JSON.
Features:
- Indian food by default
- Custom dietary preference override
- Single meal swap with medical validation
"""
import os, json
from agents.db import get_user, get_latest_cgm, get_mood_history

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def _build_clinical_context(user: dict, latest_cgm, latest_mood) -> str:
    conditions = [c for c in user["conditions"] if c != "None"]
    cond_str   = ", ".join(conditions) if conditions else "none"
    cgm_note   = ""
    if latest_cgm and latest_cgm > 200:
        cgm_note = f"Latest glucose is HIGH at {latest_cgm} mg/dL. Prioritise low-GI Indian foods (GI<55) — prefer dal, roti, sabzi over white rice."
    elif latest_cgm and latest_cgm < 90:
        cgm_note = f"Latest glucose is LOW at {latest_cgm} mg/dL. Include moderate complex carbs — add a mid-morning snack like poha or chivda."
    elif latest_cgm:
        cgm_note = f"Latest glucose is {latest_cgm} mg/dL (within target range)."
    mood_note = ""
    if latest_mood in ("tired", "sad", "anxious"):
        mood_note = f"User is feeling {latest_mood} — include energy-boosting Indian foods: dal, nuts, banana, ghee in moderation."
    return cond_str, cgm_note, mood_note


def generate_meal_plan_direct(user_id: int, custom_pref: str = None) -> dict:
    """Generate a full 3-meal Indian plan, optionally with a custom preference override."""
    from groq import Groq as GroqClient

    user = get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found."}

    latest_cgm  = get_latest_cgm(user_id)
    mood_hist   = get_mood_history(user_id, days=1)
    latest_mood = mood_hist[0]["mood"] if mood_hist else None
    cond_str, cgm_note, mood_note = _build_clinical_context(user, latest_cgm, latest_mood)

    base_diet = user["dietary_pref"]
    if custom_pref:
        diet_line = f"- Dietary preference: {custom_pref} (user-requested). Base preference is {base_diet} — still respect it unless the custom pref explicitly changes it."
    else:
        diet_line = f"- Dietary preference: {base_diet}"

    prompt = f"""You are a clinical Indian dietitian. Generate a 3-meal plan using traditional Indian meals.

PATIENT PROFILE:
- Name: {user['first_name']}
{diet_line}
- Medical conditions: {cond_str}
- Physical limitations: {user['limitations']}

CLINICAL CONTEXT:
{cgm_note}
{mood_note}

RULES:
- Use ONLY authentic Indian meals (dal, sabzi, roti, rice, idli, dosa, poha, upma, khichdi, curry, biryani, etc.)
- Strictly respect dietary preference
- Each meal: name, ingredients (list), macros (carbs_g, protein_g, fat_g, calories_kcal), reason (why this suits the patient)
- Respond ONLY with valid JSON, no markdown:

{{"plan_reason":"<2-sentence clinical rationale>",
  "meals":[
    {{"meal_type":"Breakfast","name":"<Indian name>","ingredients":["..."],"macros":{{"carbs_g":0,"protein_g":0,"fat_g":0,"calories_kcal":0}},"reason":"<why>"}},
    {{"meal_type":"Lunch","name":"<Indian name>","ingredients":["..."],"macros":{{"carbs_g":0,"protein_g":0,"fat_g":0,"calories_kcal":0}},"reason":"<why>"}},
    {{"meal_type":"Dinner","name":"<Indian name>","ingredients":["..."],"macros":{{"carbs_g":0,"protein_g":0,"fat_g":0,"calories_kcal":0}},"reason":"<why>"}}
  ],
  "hydration_tip":"<tip>",
  "alert":""
}}"""

    client = GroqClient(api_key=GROQ_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200, temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]
        plan = json.loads(raw)
    except Exception as e:
        return {"error": f"Could not generate plan: {e}"}

    return {
        "user_name":    user["first_name"],
        "dietary_pref": base_diet,
        "conditions":   [c for c in user["conditions"] if c != "None"],
        "latest_cgm":   latest_cgm,
        "latest_mood":  latest_mood,
        "plan":         plan,
    }


def swap_single_meal(user_id: int, meal_type: str, requested_ingredient: str, current_plan: dict) -> dict:
    """
    Swap one meal in an existing plan.
    First validates if the requested ingredient is safe for the user's conditions.
    If safe → replaces only that meal. If not → explains why and keeps original.
    meal_type: 'Breakfast' | 'Lunch' | 'Dinner'
    """
    from groq import Groq as GroqClient

    user = get_user(user_id)
    if not user:
        return {"error": "User not found.", "swapped": False}

    latest_cgm  = get_latest_cgm(user_id)
    mood_hist   = get_mood_history(user_id, days=1)
    latest_mood = mood_hist[0]["mood"] if mood_hist else None
    cond_str, cgm_note, _ = _build_clinical_context(user, latest_cgm, latest_mood)
    base_diet = user["dietary_pref"]

    # Find the current meal being replaced
    current_meal = next(
        (m for m in current_plan.get("meals", []) if m["meal_type"].lower() == meal_type.lower()),
        None
    )

    prompt = f"""You are a clinical Indian dietitian. A patient wants to swap their {meal_type} meal.

PATIENT PROFILE:
- Dietary preference: {base_diet}
- Medical conditions: {cond_str}

CLINICAL CONTEXT:
{cgm_note}

CURRENT {meal_type.upper()} MEAL: {current_meal['name'] if current_meal else 'unknown'}
PATIENT REQUESTS: Include {requested_ingredient} in the {meal_type} meal.

TASK:
1. First check if {requested_ingredient} is medically safe and appropriate for this patient given their conditions.
2. If SAFE: Create a new authentic Indian {meal_type} meal featuring {requested_ingredient}.
3. If NOT SAFE: Explain why in one sentence and keep the original meal.

Respond ONLY with valid JSON (no markdown):
{{"safe": true/false,
  "reason": "<why it is or isn't safe>",
  "meal": {{"meal_type": "{meal_type}", "name": "<Indian meal name>", "ingredients": ["..."], "macros": {{"carbs_g": 0, "protein_g": 0, "fat_g": 0, "calories_kcal": 0}}, "reason": "<clinical reason>"}}
}}

If not safe, set the meal to the original meal unchanged."""

    client = GroqClient(api_key=GROQ_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400, temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]
        result = json.loads(raw)
    except Exception as e:
        return {"error": f"Could not process swap: {e}", "swapped": False}

    return {
        "swapped":      result.get("safe", False),
        "safe":         result.get("safe", False),
        "reason":       result.get("reason", ""),
        "meal":         result.get("meal", current_meal),
        "meal_type":    meal_type,
        "requested":    requested_ingredient,
    }
