"""
AI Care Advisor — RAG + Agentic Workflow module for PawPal+

Flow:
  1. RAG: load species knowledge base, retrieve guidelines relevant to this pet
  2. Agent Step 1: Gemini analyzes pet profile + retrieved guidelines + existing tasks
  3. Agent Step 2: Gemini generates task suggestions and self-checks for conflicts
  4. Guardrail: validate and sanitize JSON output before converting to Task objects
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from google import genai
from dotenv import load_dotenv

from pawpal_system import Owner, Pet, Scheduler, Task

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

if not logger.handlers:
    _handler_file = logging.FileHandler("pawpal.log", encoding="utf-8")
    _handler_file.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    _handler_console = logging.StreamHandler()
    _handler_console.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_handler_file)
    logger.addHandler(_handler_console)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Knowledge base (RAG)
# ---------------------------------------------------------------------------

KB_DIR = Path(__file__).parent / "knowledge_base"

_SYSTEM_PROMPT = """You are an expert veterinary pet care scheduler. Suggest daily care tasks based on the provided guidelines.

Respond with a JSON array only — no markdown, no explanation, no extra text.

Each element must have exactly these fields:
{
  "description": "short task name (max 60 chars)",
  "hour": 8,
  "minute": 0,
  "duration_minutes": 30,
  "priority": 1,
  "recurrence": "daily"
}

Field rules:
- priority: 1=High (health/medical), 2=Medium (feeding/exercise), 3=Low (grooming/enrichment)
- recurrence: "daily", "weekly", or null
- hour: integer 0-23
- minute: integer 0 or 30
- Suggest 3-5 tasks spread across the day
- Avoid times that overlap with existing scheduled tasks"""


def load_knowledge_base(species: str) -> dict:
    """Load the care-guideline JSON for the given species. Falls back to 'other'."""
    path = KB_DIR / f"{species.lower()}.json"
    if not path.exists():
        path = KB_DIR / "other.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.info("Loaded knowledge base: %s", path.name)
        return data
    except Exception as exc:
        logger.error("Could not load knowledge base (%s): %s", path, exc)
        return {}


def retrieve_relevant_guidelines(pet: Pet, kb: dict) -> str:
    """
    RAG retrieval step: pick the sections of the knowledge base most relevant
    to this specific pet's age, weight, and species, and return them as text.
    """
    sections: list[str] = []

    if "general" in kb:
        sections.append(f"General care:\n{kb['general']}")

    if pet.age <= 1 and "puppy_kitten" in kb:
        sections.append(f"Young animal care (age ≤1 year):\n{kb['puppy_kitten']}")
    elif pet.age >= 8 and "senior" in kb:
        sections.append(f"Senior care (age 8+ years):\n{kb['senior']}")
    elif "adult" in kb:
        sections.append(f"Adult care:\n{kb['adult']}")

    for key, label in [
        ("feeding", "Feeding guidelines"),
        ("exercise", "Exercise recommendations"),
        ("grooming", "Grooming schedule"),
        ("vet_checkups", "Veterinary care"),
    ]:
        if key in kb:
            sections.append(f"{label}:\n{kb[key]}")

    retrieved = "\n\n".join(sections)
    logger.info(
        "Retrieved %d guideline sections for %s (%s, %d yr, %.1f lbs)",
        len(sections), pet.name, pet.species, pet.age, pet.weight,
    )
    return retrieved


# ---------------------------------------------------------------------------
# Agentic workflow
# ---------------------------------------------------------------------------

def suggest_tasks(pet: Pet, owner: Owner, scheduler: Scheduler) -> "list[Task] | str":
    """
    Main entry point for the AI Care Advisor.

    Agentic steps:
      1. RAG  — retrieve guidelines from knowledge base
      2. Build context — existing tasks, pet profile
      3. Call Gemini — generate suggestions that avoid conflicts
      4. Validate — guardrail parses and sanitises Gemini's JSON
      5. Return — list[Task] ready to add to the schedule, or an error string
    """
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set")
        return "API key not configured. Add GEMINI_API_KEY to your .env file."

    # Step 1 — RAG
    kb = load_knowledge_base(pet.species)
    guidelines = retrieve_relevant_guidelines(pet, kb)
    if not guidelines:
        logger.warning("Empty knowledge base for species '%s'", pet.species)

    # Step 2 — Build context
    pending_tasks = [t for t in pet.list_tasks() if t.status.value == "pending"]
    if pending_tasks:
        existing_block = "Existing pending tasks (avoid overlapping these times):\n" + "\n".join(
            f"  - {t.description}: {t.due_date_time.strftime('%I:%M %p')}, "
            f"{t.duration_minutes} min"
            for t in pending_tasks
        )
    else:
        existing_block = "No existing tasks yet — you can use any time slots."

    today_str = datetime.now().strftime("%A, %B %d %Y")

    full_prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"Today is {today_str}.\n\n"
        f"Pet profile:\n"
        f"  Name:    {pet.name}\n"
        f"  Species: {pet.species}\n"
        f"  Breed:   {pet.breed}\n"
        f"  Age:     {pet.age} year(s)\n"
        f"  Weight:  {pet.weight} lbs\n"
        f"  Gender:  {pet.gender}\n\n"
        f"Retrieved care guidelines:\n{guidelines}\n\n"
        f"{existing_block}\n\n"
        f"Suggest 3-5 appropriate care tasks for {pet.name} today. "
        f"Space them across the day (morning, midday, evening). "
        f"Respond with JSON only."
    )

    logger.info(
        "Calling Gemini for '%s' (%s, %d yr, %.1f lbs) — %d existing tasks",
        pet.name, pet.species, pet.age, pet.weight, len(pending_tasks),
    )

    # Step 3 — Call Gemini (with retry on rate limit)
    import time
    client = genai.Client(api_key=api_key)
    raw = None
    last_exc = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            raw = response.text.strip()
            logger.info("Gemini responded (%d chars) on attempt %d", len(raw), attempt + 1)
            logger.debug("Raw Gemini response: %s", raw)
            break  # success

        except Exception as exc:
            last_exc = exc
            error_msg = str(exc).lower()

            if "api_key" in error_msg or "api key" in error_msg or "permission" in error_msg or "401" in error_msg:
                logger.error("Authentication failed: %s", exc)
                return "Invalid API key. Check your GEMINI_API_KEY in .env."
            if "connect" in error_msg or "network" in error_msg:
                logger.error("Connection error: %s", exc)
                return "Could not connect to Gemini. Check your internet connection."

            # Rate limit or transient error — wait and retry
            wait = 2 ** attempt  # 1s, 2s, 4s
            logger.warning("Attempt %d failed (%s). Retrying in %ds...", attempt + 1, exc, wait)
            time.sleep(wait)

    if raw is None:
        logger.error("All Gemini attempts failed: %s", last_exc)
        return "Could not reach Gemini after 3 attempts. Please try again in a moment."

    # Step 4 — Validate and convert
    return _parse_and_validate(raw, pet)


# ---------------------------------------------------------------------------
# Guardrail: parse + validate Gemini's JSON output
# ---------------------------------------------------------------------------

def _parse_and_validate(raw: str, pet: Pet) -> "list[Task] | str":
    """
    Parse the JSON Gemini returned and convert each item to a Task object.
    Malformed or out-of-range values are either clamped or skipped with a warning.
    Returns a non-empty list[Task] or an error string.
    """
    cleaned = raw
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) >= 2 else cleaned
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse error: %s | raw: %.200s", exc, cleaned)
        return "The AI returned an unexpected format. Please try again."

    if not isinstance(data, list):
        logger.error("Expected JSON array, got %s", type(data).__name__)
        return "The AI returned an unexpected format. Please try again."

    today = datetime.now().date()
    tasks: list[Task] = []

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning("Skipping non-object item at index %d", idx)
            continue

        required = {"description", "hour", "minute", "duration_minutes", "priority"}
        missing = required - item.keys()
        if missing:
            logger.warning("Skipping item %d — missing fields: %s", idx, missing)
            continue

        try:
            description = str(item["description"]).strip()[:80]
            hour = max(0, min(int(item["hour"]), 23))
            minute = max(0, min(int(item["minute"]), 59))
            duration = max(1, min(int(item["duration_minutes"]), 240))
            priority = max(1, min(int(item["priority"]), 3))
            recurrence = item.get("recurrence")
            if recurrence not in ("daily", "weekly", None):
                logger.warning(
                    "Item %d: invalid recurrence '%s', setting to None", idx, recurrence
                )
                recurrence = None

            due_dt = datetime(today.year, today.month, today.day, hour, minute, 0)

            tasks.append(
                Task(
                    description=description,
                    due_date_time=due_dt,
                    pet_id=pet.id,
                    duration_minutes=duration,
                    priority=priority,
                    recurrence=recurrence,
                )
            )
            logger.debug(
                "Parsed suggestion %d: '%s' at %02d:%02d (%d min, p%d, %s)",
                idx, description, hour, minute, duration, priority, recurrence,
            )

        except (ValueError, TypeError) as exc:
            logger.warning("Skipping item %d due to bad values: %s", idx, exc)
            continue

    if not tasks:
        logger.error("No valid tasks parsed from Gemini response")
        return "The AI could not generate valid tasks. Please try again."

    logger.info("Successfully parsed %d task suggestion(s) for '%s'", len(tasks), pet.name)
    return tasks
