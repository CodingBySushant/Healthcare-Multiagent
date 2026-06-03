# Agent Sequence Diagrams

## 1. Login Flow
```
User          Frontend        Backend (/login-id)     DB
 |                |                  |                  |
 |-- Enter ID --> |                  |                  |
 |                |-- POST /login-id |                  |
 |                |                  |-- user_exists? ->|
 |                |                  |<-- user data  ---|
 |                |<-- greeting msg --|                  |
 |<-- Dashboard --| (profile loaded)  |                  |
```

## 2. Mood Tracking Flow
```
User          Frontend        Backend (/chat)     MoodTrackerAgent     DB
 |                |                |                    |               |
 |-- "I feel sad" |                |                    |               |
 |                |-- POST /chat --|                    |               |
 |                |                |-- LLM classify: mood               |
 |                |                |-- make_mood_agent()                |
 |                |                |                    |-- record_mood |
 |                |                |                    |               |-- INSERT mood_log
 |                |                |                    |<-- score, avg |
 |                |<-- response ---|                    |               |
 |<-- mood logged |                |                    |               |
 | + chart updates|                |                    |               |
```

## 3. CGM Logging Flow
```
User              Frontend      Backend (/chat)    CGMAgent          DB
 |                    |               |                |              |
 |-- "glucose is 240" |               |                |              |
 |                    |-- POST /chat  |                |              |
 |                    |               |-- LLM classify: cgm           |
 |                    |               |-- make_cgm_agent()            |
 |                    |               |                |-- log_glucose|
 |                    |               |                |              |-- INSERT cgm_log
 |                    |               |                |<-- alert: high
 |                    |<-- response --| (above target) |              |
 |<-- CGM chart live  |               |                |              |
     refresh          |               |                |              |
```

## 4. Interrupt Flow (with routing back)
```
User              Frontend      Backend (/chat)    InterruptAgent      DB
 |                    |               |                  |              |
 |-- "what to eat     |               |                  |              |
 |    with GERD?" --> |               |                  |              |
 |                    |-- POST /chat  |                  |              |
 |                    |               |-- LLM classify: interrupt       |
 |                    |               |-- save prev_flow = "cgm"        |
 |                    |               |-- make_interrupt_agent()        |
 |                    |               |                  |-- get_user --|
 |                    |               |                  |<-- GERD cond |
 |                    |               |                  |-- Groq call  |
 |                    |               |                  | (personalised)
 |                    |<-- answer + --|                  |              |
 |                    |  "Back to     |                  |              |
 |<-- personalised    |   glucose     |                  |              |
     advice + route   |   logging"    |                  |              |
     back             |               |                  |              |
```

## 5. Meal Plan Flow
```
User          Frontend        Backend (/meal-plan)    Groq LLM          DB
 |                |                  |                    |               |
 |-- Click btn    |                  |                    |               |
 |                |-- POST /meal-plan|                    |               |
 |                |                  |-- get_user() ------|               |
 |                |                  |-- get_latest_cgm() |               |
 |                |                  |-- get_mood_history()|              |
 |                |                  |-- build prompt ---->|              |
 |                |                  |<-- JSON plan -------|              |
 |                |<-- structured    |                    |               |
 |<-- 3 meal cards|   plan JSON      |                    |               |
 | with reasons   |                  |                    |               |
 |-- type pref -->|                  |                    |               |
 |                |-- POST /meal-plan|                    |               |
 |                |  (custom_pref)   |-- build new prompt->|              |
 |                |<-- new plan -----|                    |               |
 |<-- plan replaces               |                    |               |
     previous                     |                    |               |
```
