# HealthPulse — Personalized Healthcare MultiAgent System

A production-grade proof-of-concept multi-agent healthcare demo built for the GenAI assignment.

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | **Agno 2.x** |
| LLM | **Groq LLaMA 3.3 70B** |
| AG-UI / CopilotKit | **CopilotKit Python SDK** — `/copilotkit` SSE endpoint |
| Backend API | **FastAPI** + uvicorn |
| Intent routing | **LLM-based classifier** (history-aware, no keyword lists) |
| Database | **SQLite** — 100-user synthetic dataset |
| Data generation | **Faker** + **Groq LLM** (health notes) |
| Frontend | **React 18** + Vite + Chart.js |
| Deployment | **Docker** + Docker Compose |

---

## Architecture

```
Browser (localhost:3000)
  │
  ├─ Chat panel ──── POST /api/chat ──────► FastAPI Orchestrator
  │                                               │
  │                                    LLM intent classifier
  │                                    (with chat history context)
  │                                               │
  │                              ┌────────────────┼────────────────┐
  │                              ▼                ▼                ▼
  │                        MoodTrackerAgent   CGMAgent      InterruptAgent
  │                              │                │                │
  │                              └────────────────┴────────────────┘
  │                                               │
  │                                          SQLite DB
  │
  ├─ Meal plan btn ── POST /api/meal-plan ──► MealPlannerAgent (direct Groq)
  ├─ Food log form ── POST /api/food-log ───► FoodIntakeAgent
  ├─ CGM chart ────── GET /api/users/{id}/cgm
  └─ Mood chart ───── GET /api/users/{id}/mood
```

---

## Agents

| Agent | Trigger | Key behaviour |
|---|---|---|
| **GreetingAgent** | Login (User ID 1–100) | Validates ID, greets by name, loads profile |
| **MoodTrackerAgent** | Emotional expression detected by LLM | Logs mood, score, rolling 7-day average + trend |
| **CGMAgent** | Glucose number or history request | Logs reading, validates 80–300 range, flags alerts |
| **FoodIntakeAgent** | Food log form | LLM identifies dish, estimates macros, flags high-carb |
| **MealPlannerAgent** | Generate Meal Plan button | 3-meal plan with macros + clinical reason per meal |
| **InterruptAgent** | General health query detected | Answers using stored profile, routes back to previous flow |

### Design Decisions

**LLM-based intent routing** — instead of fragile keyword lists, the orchestrator makes a tiny Groq call (`max_tokens=5, temperature=0`) with the last 6 messages as context. This handles natural language ("today I am very stressed"), follow-ups ("give me the history"), and edge cases automatically.

**Chat history context** — the last 6 message pairs are passed to the classifier so follow-ups stay in the correct agent without re-stating context.

**Meal planner as direct Groq call** — bypasses Agno's agent narration to return clean structured JSON with `dish_name`, `macros`, and `reason` per meal. This avoids "## Step 1: Analysis..." style responses.

**CopilotKit on backend** — the `/copilotkit` endpoint uses the CopilotKit Python SDK and AG-UI protocol. The React frontend uses `CopilotKit` as a context provider. `CopilotSidebar` was not used because it requires a LangGraph agent — we use `Action`-based integration instead, which is the correct pattern for custom agent frameworks like Agno.

---

## Quick Start

### Prerequisites
- Docker Desktop
- Groq API key → [console.groq.com](https://console.groq.com) (free)

### Run

```bash
git clone https://github.com/your-username/healthcare-multiagent.git
cd healthcare-multiagent
cp .env.example .env
# Edit .env → add your GROQ_API_KEY
cd deploy
docker-compose up --build
```

Open **http://localhost:3000**

Database is auto-generated on first boot (100 users + 7 days of historical data).

### Local Development (without Docker)

```bash
# Backend
pip install -r backend/requirements.txt
python data/generate_dataset.py
export GROQ_API_KEY=your_key DB_PATH=./data/healthcare.db
uvicorn agents.orchestrator:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
# Edit vite.config.js: change 'http://backend:8000' → 'http://localhost:8000'
npm run dev
```

---

## Directory Structure

```
healthcare-multiagent/
├── data/
│   └── generate_dataset.py        # Faker + Groq LLM → 100-user SQLite dataset
├── agents/
│   ├── db.py                      # Shared typed DB helpers
│   ├── orchestrator.py            # FastAPI + LLM router + CopilotKit endpoint
│   ├── greeting_agent.py          # Agno: validate ID, greet by name
│   ├── mood_agent.py              # Agno: mood log + rolling average + trend
│   ├── cgm_agent.py               # Agno: glucose log + 80-300 validation + history
│   ├── food_agent.py              # Agno: food log + LLM macro estimation
│   ├── meal_planner_agent.py      # Direct Groq: adaptive 3-meal plan with reasons
│   └── interrupt_agent.py         # Agno: personalised Q&A + flow restoration
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # CopilotKit provider root
│   │   ├── Dashboard.jsx          # Main UI: chat + dashboard + charts
│   │   ├── CGMChart.jsx           # Chart.js line chart (live refresh)
│   │   ├── MoodChart.jsx          # Chart.js bar chart (live refresh)
│   │   └── FoodForm.jsx           # Food log form
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── Dockerfile
│   ├── main.py                    # Entrypoint (auto-seeds DB if missing)
│   └── requirements.txt
├── deploy/
│   ├── docker-compose.yml         # backend :8000 + frontend :3000 + shared volume
│   └── nginx.conf                 # SPA + /api + /copilotkit SSE proxy
├── docs/
│   ├── agent_schemas.json         # Formal agent input/output specs
│   └── sequence_diagram.md        # Agent conversation flow diagrams
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/login-id` | `{user_id}` → validate and return greeting |
| POST | `/chat` | `{user_id, message}` → route to correct agent |
| POST | `/meal-plan` | `{user_id, message}` → structured meal plan JSON |
| POST | `/food-log` | `{user_id, message}` → log food + estimate macros |
| GET | `/users/{id}` | User profile |
| GET | `/users/{id}/cgm?limit=21` | CGM history |
| GET | `/users/{id}/mood?days=7` | Mood history |
| GET | `/users/{id}/food?limit=10` | Food log |
| POST | `/copilotkit` | CopilotKit AG-UI SSE endpoint |
| GET | `/health` | Health check |
