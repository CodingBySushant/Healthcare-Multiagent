"""
Orchestrator — FastAPI backend (port 8000)
Features:
  - LLM-based intent classification with full chat history context
  - /chat        : Greeting, Mood, CGM, Interrupt agents (history-aware)
  - /meal-plan   : Dedicated structured meal plan endpoint
  - /login-id    : ID-based login
  - /food-log    : Food intake logging
  - /copilotkit  : CopilotKit AG-UI endpoint
  - /users/*     : REST data endpoints
"""
import os, re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from copilotkit import CopilotKitRemoteEndpoint, Action
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from agents.db import (
    get_user, get_session_flow, set_session_flow,
    get_cgm_history, get_mood_history, get_food_history, user_exists,
)

# ── In-memory session store (user_id → {user, flow, history}) ────────────────
sessions: dict[int, dict] = {}

MAX_HISTORY = 6   # last N message pairs kept for LLM context


# ── LLM intent classifier (history-aware) ────────────────────────────────────

def classify_intent(message: str, current_flow: str, history: list) -> str:
    """
    Uses Groq with the last few messages as context so follow-ups
    (e.g. 'give me the history', 'okay tell me') stay in the right agent.
    Returns: 'mood' | 'cgm' | 'interrupt'
    """
    from groq import Groq as GroqClient
    client = GroqClient(api_key=os.environ.get("GROQ_API_KEY", ""))

    context_note = ""
    if current_flow == "cgm":
        context_note = "The previous conversation was about glucose/CGM. Follow-ups like 'give me the history', 'tell me more', 'okay' likely continue that context."
    elif current_flow == "mood":
        context_note = "The previous conversation was about mood tracking. Follow-ups likely continue that context."

    # Build a compact history string for context
    history_str = ""
    if history:
        recent = history[-MAX_HISTORY:]
        history_str = "\n".join(
            f"{'User' if m['role']=='user' else 'Assistant'}: {m['text'][:120]}"
            for m in recent
        )

    system = f"""You are a routing classifier for a healthcare chatbot.
Classify the LATEST user message into exactly one category and reply with ONLY that word:

mood       — user expressing or logging emotional state (happy, sad, stressed, tired, angry, great, etc.)
cgm        — user logging or asking about blood glucose/sugar reading or glucose history
food       — user asking about their food log, last meal, what they ate, meal history
mealplan   — user asking to generate, create, or suggest a meal plan or diet plan
interrupt  — any other question, health advice, general query

{context_note}

Recent conversation for context:
{history_str}

Reply with only one word: mood, cgm, food, mealplan, or interrupt."""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": message},
            ],
            max_tokens=5,
            temperature=0,
        )
        intent = resp.choices[0].message.content.strip().lower()
        if intent in ("mood", "cgm", "food", "mealplan", "interrupt"):
            return intent
    except Exception:
        pass
    return current_flow if current_flow in ("mood", "cgm", "food", "mealplan") else "interrupt"


# ── Agent runners ─────────────────────────────────────────────────────────────

def _run(agent, prompt: str) -> str:
    result = agent.run(input=prompt, stream=False)
    return (result.content or "").strip()


def run_mood(user_id: int, message: str) -> dict:
    from agents.mood_agent import make_mood_agent
    content = _run(make_mood_agent(), f"user_id={user_id}. Message: {message}")
    set_session_flow(user_id, "mood")
    return {"agent": "MoodTrackerAgent", "message": content, "flow": "mood"}


def run_cgm(user_id: int, message: str) -> dict:
    from agents.cgm_agent import make_cgm_agent
    content = _run(make_cgm_agent(), f"user_id={user_id}. Message: {message}")
    set_session_flow(user_id, "cgm")
    return {"agent": "CGMAgent", "message": content, "flow": "cgm"}


def run_interrupt(user_id: int, message: str, previous_flow: str) -> dict:
    from agents.interrupt_agent import make_interrupt_agent
    content = _run(make_interrupt_agent(),
                   f"user_id={user_id}. Previous flow: {previous_flow}. Query: {message}")
    return {"agent": "InterruptAgent", "message": content, "flow": previous_flow}


def run_food_history(user_id: int, message: str) -> dict:
    msg = message.lower()
    # If asking for history → fetch it
    if any(w in msg for w in ["history", "last meal", "what did i eat", "previous", "log show", "show my"]):
        from agents.food_agent import make_food_agent
        content = _run(make_food_agent(), f"user_id={user_id}. Message: {message}")
        set_session_flow(user_id, "food")
        return {"agent": "FoodIntakeAgent", "message": content, "flow": "food"}
    # Otherwise redirect to the dashboard food form
    set_session_flow(user_id, "food")
    return {
        "agent": "FoodIntakeAgent",
        "message": "To log your meal, please use the 🥗 Log Food form on the right dashboard — type what you ate in the text box and click Submit. It will automatically estimate your macros!",
        "flow": "food",
    }


def run_mealplan_chat(user_id: int, message: str) -> dict:
    set_session_flow(user_id, "meal_plan")
    return {
        "agent": "MealPlannerAgent",
        "message": "Your meal plan is ready! 🍽️ Click the **Generate Meal Plan** button on the right dashboard to see your personalised 3-meal plan with ingredients, macros, and clinical reasons.",
        "flow": "meal_plan",
    }


# ── FastAPI ───────────────────────────────────────────────────────────────────

app = FastAPI(title="HealthPulse API", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ── CopilotKit AG-UI endpoint ─────────────────────────────────────────────────

async def _ck_chat(user_id: int, message: str) -> str:
    uid = int(user_id)
    if uid not in sessions:
        return "Please log in first."
    session  = sessions[uid]
    flow     = get_session_flow(uid)
    history  = session.get("history", [])
    intent   = classify_intent(message, flow, history)
    if intent == "mood":     return run_mood(uid, message)["message"]
    if intent == "cgm":      return run_cgm(uid, message)["message"]
    if intent == "food":     return run_food_history(uid, message)["message"]
    if intent == "mealplan": return run_mealplan_chat(uid, message)["message"]
    return run_interrupt(uid, message, flow)["message"]

sdk = CopilotKitRemoteEndpoint(actions=[
    Action(name="chat", handler=_ck_chat,
           description="Route message to healthcare agent",
           parameters=[
               {"name": "user_id", "type": "number", "description": "User ID"},
               {"name": "message", "type": "string", "description": "Message"},
           ]),
])
add_fastapi_endpoint(app, sdk, "/copilotkit")


# ── /login-id ─────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    user_id: int

@app.post("/login-id")
def login_by_id(req: LoginRequest):
    if not user_exists(req.user_id):
        return {"valid": False,
                "message": f"User ID {req.user_id} not found. Please enter a valid ID between 1 and 100."}
    user = get_user(req.user_id)
    sessions[user["id"]] = {"user": user, "flow": "main", "history": []}
    set_session_flow(user["id"], "main")
    conditions = [c for c in user["conditions"] if c != "None"]
    cond_note = f" I can see you have {', '.join(conditions)} on record." if conditions else ""
    greeting = (
        f"Hello, {user['first_name']}! 👋 Welcome to HealthPulse. "
        f"You're based in {user['city']}.{cond_note} "
        f"I can help you track mood, glucose, and meals. What would you like to do first?"
    )
    return {"valid": True, "message": greeting, "user": user}


# ── /chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: Optional[int] = None
    message: str

class ChatResponse(BaseModel):
    agent: str
    message: str
    flow: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    uid = req.user_id
    if uid is None or uid not in sessions:
        return ChatResponse(agent="System", flow="greeting",
            message="Please enter your User ID (1–100) to get started.")

    session = sessions[uid]
    history = session.setdefault("history", [])
    flow    = get_session_flow(uid)
    intent  = classify_intent(req.message, flow, history)

    if intent == "mood":        result = run_mood(uid, req.message)
    elif intent == "cgm":       result = run_cgm(uid, req.message)
    elif intent == "food":      result = run_food_history(uid, req.message)
    elif intent == "mealplan":  result = run_mealplan_chat(uid, req.message)
    else:                       result = run_interrupt(uid, req.message, flow)

    # Append to session history (keep last MAX_HISTORY*2 messages)
    history.append({"role": "user",      "text": req.message})
    history.append({"role": "assistant", "text": result["message"],
                    "agent": result["agent"]})
    if len(history) > MAX_HISTORY * 2:
        history[:] = history[-(MAX_HISTORY * 2):]

    return ChatResponse(**result)


# ── /meal-plan ────────────────────────────────────────────────────────────────

@app.post("/meal-plan")
def meal_plan(req: ChatRequest):
    if req.user_id is None:
        raise HTTPException(400, "user_id required")
    if not user_exists(req.user_id):
        raise HTTPException(404, "User not found")
    from agents.meal_planner_agent import generate_meal_plan_direct
    custom_pref = req.message if req.message and req.message != "generate" else None
    result = generate_meal_plan_direct(req.user_id, custom_pref=custom_pref)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


# ── /food-log ─────────────────────────────────────────────────────────────────

@app.post("/food-log")
def food_log(req: ChatRequest):
    if req.user_id is None:
        raise HTTPException(400, "user_id required")
    from agents.food_agent import make_food_agent
    content = _run(make_food_agent(), f"user_id={req.user_id}. {req.message}")
    return {"agent": "FoodIntakeAgent", "message": content}


# ── /meal-swap ────────────────────────────────────────────────────────────────

class MealSwapRequest(BaseModel):
    user_id: int
    meal_type: str          # Breakfast | Lunch | Dinner
    requested_ingredient: str
    current_plan: dict      # the full plan object currently shown

@app.post("/meal-swap")
def meal_swap(req: MealSwapRequest):
    if not user_exists(req.user_id):
        raise HTTPException(404, "User not found")
    from agents.meal_planner_agent import swap_single_meal
    result = swap_single_meal(
        req.user_id, req.meal_type,
        req.requested_ingredient, req.current_plan
    )
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result

# ── Data endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/users/{user_id}")
def user_profile(user_id: int):
    user = get_user(user_id)
    if not user: raise HTTPException(404, "User not found")
    return user

@app.get("/users/{user_id}/cgm")
def cgm_hist(user_id: int, limit: int = 21):
    return {"history": get_cgm_history(user_id, limit=limit)}

@app.get("/users/{user_id}/mood")
def mood_hist(user_id: int, days: int = 7):
    return {"history": get_mood_history(user_id, days=days)}

@app.get("/users/{user_id}/food")
def food_hist(user_id: int, limit: int = 10):
    return {"history": get_food_history(user_id, limit=limit)}
