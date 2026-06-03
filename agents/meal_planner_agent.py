"""
Meal Planner Agent — called directly from the /meal-plan endpoint.
Returns structured JSON with meals, macros and clinical reasons.
"""
import os, json
from agents.db import get_user, get_latest_cgm, get_mood_history

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def generate_meal_plan_direct(user_id: int, custom_pref: str = None) -> dict:
    """
    Called directly (not via Agno) so we have full control over the prompt
    and get back clean structured data, not agent narration.
    """
    from groq import Groq as GroqClient

    user = get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found."}

    latest_cgm  = get_latest_cgm(user_id)
    mood_hist   = get_mood_history(user_id, days=1)
    latest_mood = mood_hist[0]["mood"] if mood_hist else None
    conditions  = [c for c in user["conditions"] if c != "None"]
    cond_str    = ", ".join(conditions) if conditions else "none"

    # Build clinical context
    cgm_note = ""
    if latest_cgm and latest_cgm > 200:
        cgm_note = f"Latest glucose is HIGH at {latest_cgm} mg/dL. Prioritise low-GI foods (GI<55), avoid refined carbs and sugar."
    elif latest_cgm and latest_cgm < 90:
        cgm_note = f"Latest glucose is LOW at {latest_cgm} mg/dL. Include moderate complex carbs, add a mid-morning snack."
    elif latest_cgm:
        cgm_note = f"Latest glucose is {latest_cgm} mg/dL (within target range)."

    mood_note = ""
    if latest_mood in ("tired", "sad", "anxious"):
        mood_note = f"User is feeling {latest_mood} — include energy-boosting foods: complex carbs, nuts, omega-3, B vitamins."

    diet_line = f"- Dietary preference: {custom_pref} (user-requested override)" if custom_pref else f"- Dietary preference: {user['dietary_pref']}"

    prompt = f"""You are a clinical dietitian. Generate a 3-meal plan for today.

PATIENT PROFILE:
- Name: {user['first_name']}
{diet_line}
- Medical conditions: {cond_str}
- Physical limitations: {user['limitations']}

CLINICAL CONTEXT:
{cgm_note}
{mood_note}

RULES:
- Exactly 3 meals: Breakfast, Lunch, Dinner
- Strictly respect dietary preference (no meat for vegetarian/vegan, no dairy for vegan)
- Each meal must have: name, ingredients (list), macros (carbs_g, protein_g, fat_g, calories_kcal), reason (1 sentence explaining WHY this meal suits the patient's condition)
- Prefer practical Indian household meals
- Respond ONLY with valid JSON, no markdown, no extra text:

{{"plan_reason": "<2-sentence overall clinical rationale>",
  "meals": [
    {{"meal_type": "Breakfast", "name": "<name>", "ingredients": ["..."], "macros": {{"carbs_g": 0, "protein_g": 0, "fat_g": 0, "calories_kcal": 0}}, "reason": "<why this meal>"}},
    {{"meal_type": "Lunch",     "name": "<name>", "ingredients": ["..."], "macros": {{"carbs_g": 0, "protein_g": 0, "fat_g": 0, "calories_kcal": 0}}, "reason": "<why this meal>"}},
    {{"meal_type": "Dinner",    "name": "<name>", "ingredients": ["..."], "macros": {{"carbs_g": 0, "protein_g": 0, "fat_g": 0, "calories_kcal": 0}}, "reason": "<why this meal>"}}
  ],
  "hydration_tip": "<tip>",
  "alert": "<clinical alert or empty string>"
}}"""

    client = GroqClient(api_key=GROQ_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200, temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        plan = json.loads(raw)
    except Exception as e:
        return {"error": f"Could not generate plan: {e}"}

    return {
        "user_name":   user["first_name"],
        "dietary_pref": user["dietary_pref"],
        "conditions":  conditions,
        "latest_cgm":  latest_cgm,
        "latest_mood": latest_mood,
        "plan":        plan,
    }
