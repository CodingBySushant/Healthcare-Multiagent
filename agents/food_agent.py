import os, json
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
from agents.db import log_food, get_food_history, get_user

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


@tool
def log_and_estimate(user_id: int, description: str, logged_at: str = "") -> dict:
    """Recognise the food, estimate macros, flag if high-carb for diabetics."""
    from groq import Groq as GroqClient
    client = GroqClient(api_key=GROQ_API_KEY)

    prompt = f"""A user described their meal as: "{description}"
Identify the dish and estimate macros.
Respond ONLY with valid JSON (no markdown):
{{"dish_name":"<clean short dish name>","carbs_g":0,"protein_g":0,"fat_g":0,"calories_kcal":0}}"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120, temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content.strip())
    except Exception:
        data = {"dish_name": description, "carbs_g": 0,
                "protein_g": 0, "fat_g": 0, "calories_kcal": 0}

    dish    = data.get("dish_name", description)
    carbs   = data.get("carbs_g", 0) or 0
    protein = data.get("protein_g", 0) or 0
    fat     = data.get("fat_g", 0) or 0
    cals    = data.get("calories_kcal", 0) or 0

    log_food(user_id, dish, logged_at or None, carbs, protein, fat)

    user = get_user(user_id)
    conditions = user.get("conditions", []) if user else []
    is_diabetic = "Type 2 Diabetes" in conditions
    flag = ""
    if carbs > 40:
        flag = f"⚠️ High-carb meal ({carbs}g carbs)."
        if is_diabetic:
            flag += " As you have Type 2 Diabetes, please factor this into your meal planning."

    return {"dish": dish, "carbs": carbs, "protein": protein,
            "fat": fat, "calories": cals, "flag": flag}


@tool
def get_recent_meals(user_id: int) -> dict:
    """Return the last 10 food log entries."""
    return {"meals": get_food_history(user_id, limit=10)}


def make_food_agent() -> Agent:
    return Agent(
        name="FoodIntakeAgent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API_KEY),
        tools=[log_and_estimate, get_recent_meals],
        instructions=[
            "Call log_and_estimate with user_id and the meal description from the message.",
            "Output in EXACTLY this format:",
            "✅ <dish_name>",
            "Carbs: <carbs>g | Protein: <protein>g | Fat: <fat>g | <calories> kcal",
            "If flag is not empty, add it on a new line.",
            "No extra words. No headers. No bullet points.",
        ],
        markdown=False,
    )
