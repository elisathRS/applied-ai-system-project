# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class goes beyond a simple sorted list. Here's what it can do:

- **Recurring tasks** — Tasks can be marked `"daily"` or `"weekly"`. Calling `complete_task()` marks the task done and automatically adds the next occurrence to the pet's task list. One-shot tasks are completed without spawning a follow-up.

- **Conflict detection** — `detect_conflicts()` scans every pair of pending tasks and reports any whose time windows overlap, regardless of which pet they belong to. Warnings include the task names, pets, and exact time ranges.

- **Conflict resolution** — `resolve_conflicts()` fixes overlaps in the daily plan by pushing lower-priority tasks to start immediately after the previous task ends, so no two tasks run at the same time.

- **Filtering** — `filter_by_status()` returns only pending or completed tasks; `filter_by_pet()` narrows the list to a single pet by name.

- **Daily plan** — `generate_daily_plan()` combines all of the above: it collects today's pending tasks, sorts by priority, and resolves any time conflicts before returning the final schedule.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
