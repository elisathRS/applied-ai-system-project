from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Scheduler, Task, TaskStatus


def make_pet(name="Mochi"):
    return Pet(name=name, species="dog", age=3, gender="female", weight=12.5, breed="Shiba Inu")


def make_task(pet_id, hour=9, minute=0, description="Test task", duration=30, recurrence=None):
    return Task(
        description=description,
        due_date_time=datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0),
        pet_id=pet_id,
        duration_minutes=duration,
        recurrence=recurrence,
    )


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    pet = make_pet()
    task = make_task(pet.id)

    assert task.status == TaskStatus.PENDING
    task.mark_complete()
    assert task.status == TaskStatus.COMPLETED


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Luna", species="cat", age=5, gender="female", weight=8.0, breed="Tabby")

    assert len(pet.list_tasks()) == 0
    pet.add_task(make_task(pet.id, hour=8))
    pet.add_task(make_task(pet.id, hour=10))
    assert len(pet.list_tasks()) == 2


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks provided out-of-order must come back sorted earliest → latest."""
    scheduler = Scheduler()
    pet = make_pet()

    t1 = make_task(pet.id, hour=14)  # 2 PM
    t2 = make_task(pet.id, hour=8)   # 8 AM
    t3 = make_task(pet.id, hour=11)  # 11 AM

    sorted_tasks = scheduler.sort_by_time([t1, t2, t3])

    times = [t.due_date_time.strftime("%H:%M") for t in sorted_tasks]
    assert times == sorted(times), f"Expected sorted times, got: {times}"


def test_sort_by_time_preserves_all_tasks():
    """Sorting must not drop or duplicate any tasks."""
    scheduler = Scheduler()
    pet = make_pet()
    tasks = [make_task(pet.id, hour=h) for h in [15, 7, 12, 9]]

    result = scheduler.sort_by_time(tasks)
    assert len(result) == 4


def test_sort_by_time_already_sorted_is_unchanged():
    """Tasks already in order should remain in the same order."""
    scheduler = Scheduler()
    pet = make_pet()

    tasks = [make_task(pet.id, hour=h) for h in [8, 10, 13, 17]]
    result = scheduler.sort_by_time(tasks)
    times = [t.due_date_time.strftime("%H:%M") for t in result]
    assert times == ["08:00", "10:00", "13:00", "17:00"]


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_day_task():
    """Completing a daily task must spawn a new task exactly 1 day later."""
    scheduler = Scheduler()
    pet = make_pet()
    task = make_task(pet.id, hour=9, recurrence="daily")
    pet.add_task(task)

    original_dt = task.due_date_time
    new_task = scheduler.complete_task(task, pet)

    assert new_task is not None
    assert new_task.due_date_time == original_dt + timedelta(days=1)


def test_complete_daily_task_adds_to_pet():
    """The spawned daily task must appear in the pet's task list."""
    scheduler = Scheduler()
    pet = make_pet()
    task = make_task(pet.id, hour=9, recurrence="daily")
    pet.add_task(task)

    scheduler.complete_task(task, pet)

    assert len(pet.list_tasks()) == 2  # original + new


def test_complete_daily_task_marks_original_done():
    """The original task must be COMPLETED after calling complete_task."""
    scheduler = Scheduler()
    pet = make_pet()
    task = make_task(pet.id, recurrence="daily")
    pet.add_task(task)

    scheduler.complete_task(task, pet)

    assert task.status == TaskStatus.COMPLETED


def test_complete_daily_task_inherits_recurrence():
    """The spawned task must keep recurrence='daily' so the chain continues."""
    scheduler = Scheduler()
    pet = make_pet()
    task = make_task(pet.id, recurrence="daily")
    pet.add_task(task)

    new_task = scheduler.complete_task(task, pet)

    assert new_task.recurrence == "daily"


def test_complete_oneshot_task_returns_none():
    """A task with no recurrence must return None (no follow-up task created)."""
    scheduler = Scheduler()
    pet = make_pet()
    task = make_task(pet.id, recurrence=None)
    pet.add_task(task)

    result = scheduler.complete_task(task, pet)

    assert result is None
    assert len(pet.list_tasks()) == 1  # no new task added


def test_complete_weekly_task_creates_next_week_task():
    """Completing a weekly task must spawn a new task exactly 7 days later."""
    scheduler = Scheduler()
    pet = make_pet()
    task = make_task(pet.id, recurrence="weekly")
    pet.add_task(task)

    original_dt = task.due_date_time
    new_task = scheduler.complete_task(task, pet)

    assert new_task is not None
    assert new_task.due_date_time == original_dt + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def _make_owner_with_two_overlapping_tasks():
    """Helper: owner with one pet that has two tasks whose windows overlap."""
    owner = Owner(name="Ada", phone_number="555-0100", email="ada@example.com")
    pet = make_pet("Biscuit")
    owner.add_pet(pet)

    # Task A: 9:00–9:30  |  Task B: 9:15–9:45  → 15-minute overlap
    t_a = make_task(pet.id, hour=9, minute=0, description="Morning Walk", duration=30)
    t_b = make_task(pet.id, hour=9, minute=15, description="Feeding", duration=30)
    pet.add_task(t_a)
    pet.add_task(t_b)
    return owner


def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap must produce at least one warning."""
    scheduler = Scheduler()
    owner = _make_owner_with_two_overlapping_tasks()

    warnings = scheduler.detect_conflicts(owner)

    assert len(warnings) >= 1


def test_detect_conflicts_warning_contains_task_names():
    """The warning message must mention both conflicting task descriptions."""
    scheduler = Scheduler()
    owner = _make_owner_with_two_overlapping_tasks()

    warnings = scheduler.detect_conflicts(owner)

    assert any("Morning Walk" in w and "Feeding" in w for w in warnings)


def test_detect_conflicts_no_warning_for_sequential_tasks():
    """Tasks that do not overlap must produce zero warnings."""
    scheduler = Scheduler()
    owner = Owner(name="Ada", phone_number="555-0100", email="ada@example.com")
    pet = make_pet("Biscuit")
    owner.add_pet(pet)

    # Task A: 9:00–9:30  |  Task B: 9:30–10:00 → back-to-back, no overlap
    t_a = make_task(pet.id, hour=9, minute=0, description="Walk", duration=30)
    t_b = make_task(pet.id, hour=9, minute=30, description="Feed", duration=30)
    pet.add_task(t_a)
    pet.add_task(t_b)

    warnings = scheduler.detect_conflicts(owner)

    assert warnings == []


def test_detect_conflicts_no_warning_when_no_tasks():
    """An owner with no tasks must produce zero warnings."""
    scheduler = Scheduler()
    owner = Owner(name="Ada", phone_number="555-0100", email="ada@example.com")
    owner.add_pet(make_pet())

    warnings = scheduler.detect_conflicts(owner)

    assert warnings == []


def test_detect_conflicts_flags_cross_pet_overlap():
    """Overlapping tasks assigned to *different* pets must still be flagged."""
    scheduler = Scheduler()
    owner = Owner(name="Ada", phone_number="555-0100", email="ada@example.com")

    pet1 = make_pet("Rex")
    pet2 = make_pet("Luna")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    t1 = make_task(pet1.id, hour=10, minute=0, description="Rex Walk", duration=30)
    t2 = make_task(pet2.id, hour=10, minute=10, description="Luna Feeding", duration=30)
    pet1.add_task(t1)
    pet2.add_task(t2)

    warnings = scheduler.detect_conflicts(owner)

    assert len(warnings) >= 1
