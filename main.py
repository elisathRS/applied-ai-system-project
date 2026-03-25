from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, TaskStatus, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", phone_number="555-1234", email="jordan@example.com")

mochi = Pet(name="Mochi", species="dog", age=3, gender="female", weight=12.5, breed="Shiba Inu")
luna  = Pet(name="Luna",  species="cat", age=5, gender="female", weight=8.0,  breed="Tabby")

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Tasks added OUT OF ORDER intentionally ---
today = datetime.now().replace(second=0, microsecond=0)

# Mochi's tasks — added latest-first, morning walk is a daily recurring task
mochi.add_task(Task(
    description="Flea & tick medication",
    due_date_time=today.replace(hour=8, minute=0),
    pet_id=mochi.id,
    duration_minutes=5,
    priority=2,
))
mochi.add_task(Task(
    description="Evening walk",
    due_date_time=today.replace(hour=17, minute=30),
    pet_id=mochi.id,
    duration_minutes=30,
    priority=2,
    recurrence="daily",
))
mochi.add_task(Task(
    description="Morning walk",
    due_date_time=today.replace(hour=7, minute=0),
    pet_id=mochi.id,
    duration_minutes=30,
    priority=1,
    recurrence="daily",
))

# Luna's tasks — vet check-up is one-shot; clean litter box recurs weekly
luna.add_task(Task(
    description="Vet check-up",
    due_date_time=today.replace(hour=10, minute=0),
    pet_id=luna.id,
    duration_minutes=60,
    priority=1,
))
luna.add_task(Task(
    description="Clean litter box",
    due_date_time=today.replace(hour=7, minute=30),
    pet_id=luna.id,
    duration_minutes=10,
    priority=2,
    recurrence="weekly",
))
luna.add_task(Task(
    description="Brush fur",
    due_date_time=today.replace(hour=9, minute=0),
    pet_id=luna.id,
    duration_minutes=15,
    priority=3,
))

# --- Deliberate conflicts ---
# Conflict 1 (same pet): Mochi has a bath at 7:10 AM — overlaps her Morning walk (7:00-7:30)
mochi.add_task(Task(
    description="Bath time",
    due_date_time=today.replace(hour=7, minute=10),
    pet_id=mochi.id,
    duration_minutes=20,
    priority=2,
))
# Conflict 2 (different pets): Luna has feeding at 9:05 AM — overlaps her Brush fur (9:00-9:15)
luna.add_task(Task(
    description="Feeding",
    due_date_time=today.replace(hour=9, minute=5),
    pet_id=luna.id,
    duration_minutes=10,
    priority=1,
))

# --- Scheduler ---
scheduler = Scheduler()
pet_lookup = {pet.id: pet.name for pet in owner.list_pets()}
priority_label = {1: "High", 2: "Medium", 3: "Low"}

def print_tasks(tasks: list, title: str) -> None:
    print(f"\n{'=' * 52}")
    print(f"  {title}")
    print(f"{'=' * 52}")
    if not tasks:
        print("  (no tasks)")
        return
    for task in tasks:
        end_time = task.due_date_time + timedelta(minutes=task.duration_minutes)
        pet_name = pet_lookup.get(task.pet_id, "Unknown")
        recur_label = f"[{task.recurrence}]" if task.recurrence else "[one-shot]"
        print(
            f"  {task.due_date_time.strftime('%a %m/%d %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            f"  [{priority_label[task.priority]:6}]"
            f"  [{task.status.value:9}]"
            f"  {recur_label:8}"
            f"  {pet_name}: {task.description}"
        )
    print(f"  {len(tasks)} task(s)")

# 1. Conflict detection — run before anything else so warnings appear first
print(f"\n{'=' * 52}")
print("  CONFLICT DETECTION REPORT")
print(f"{'=' * 52}")
conflicts = scheduler.detect_conflicts(owner)
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")
print(f"  {len(conflicts)} conflict(s) detected.")

# 2. All tasks — raw insertion order, showing recurrence field
all_tasks = scheduler.collect_tasks(owner)
print_tasks(all_tasks, "ALL TASKS — raw order, recurrence labels visible")

# 2. Complete Mochi's morning walk (daily) — should spawn tomorrow's
morning_walk = next(t for t in mochi.tasks if t.description == "Morning walk")
print(f"\n  >> Completing '{morning_walk.description}' (recurrence={morning_walk.recurrence})")
next_task = scheduler.complete_task(morning_walk, mochi)
if next_task:
    print(f"  >> Spawned next occurrence: {next_task.description} on {next_task.due_date_time.strftime('%a %m/%d at %I:%M %p')}")

# 3. Complete Luna's litter box (weekly) — should spawn next week's
litter_box = next(t for t in luna.tasks if t.description == "Clean litter box")
print(f"\n  >> Completing '{litter_box.description}' (recurrence={litter_box.recurrence})")
next_task = scheduler.complete_task(litter_box, luna)
if next_task:
    print(f"  >> Spawned next occurrence: {next_task.description} on {next_task.due_date_time.strftime('%a %m/%d at %I:%M %p')}")

# 4. Complete Luna's vet check-up (one-shot) — should NOT spawn anything
vet = next(t for t in luna.tasks if t.description == "Vet check-up")
print(f"\n  >> Completing '{vet.description}' (recurrence={vet.recurrence})")
result = scheduler.complete_task(vet, luna)
print(f"  >> Next occurrence spawned: {result}")   # expected: None

# 5. All tasks after completions — new occurrences now visible
pet_lookup = {pet.id: pet.name for pet in owner.list_pets()}   # refresh in case new pets added
all_tasks = scheduler.collect_tasks(owner)
print_tasks(scheduler.sort_by_time(all_tasks), "ALL TASKS AFTER COMPLETIONS — sorted by time")

# 6. Pending only
pending = scheduler.filter_by_status(all_tasks, TaskStatus.PENDING)
print_tasks(pending, "PENDING TASKS ONLY")

# 7. Completed only
completed = scheduler.filter_by_status(all_tasks, TaskStatus.COMPLETED)
print_tasks(completed, "COMPLETED TASKS ONLY")
