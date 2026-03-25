from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    description: str
    due_date_time: datetime
    pet_id: UUID
    duration_minutes: int = 30        # how long the task takes; used to detect overlaps
    priority: int = 2                 # 1 = High, 2 = Medium, 3 = Low
    recurrence: str | None = None     # "daily", "weekly", or None for one-shot tasks
    status: TaskStatus = TaskStatus.PENDING
    id: UUID = field(default_factory=uuid4)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.status = TaskStatus.COMPLETED


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    gender: str
    weight: float
    breed: str
    tasks: list[Task] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def add_task(self, _task: Task) -> None:
        """Add a new task to this pet."""
        self.tasks.append(_task)

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def remove_task(self, _task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(_task)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, phone_number: str, email: str) -> None:
        self.name = name
        self.phone_number = phone_number
        self.email = email
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list."""
        self.pets.append(pet)

    def list_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's list."""
        self.pets.remove(pet)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Service layer — coordinates task management across all pets."""

    def complete_task(self, task: Task, pet: Pet) -> Task | None:
        """Mark a task done and schedule the next occurrence if it recurs; returns the new Task or None."""
        task.mark_complete()

        if task.recurrence == "daily":
            delta = timedelta(days=1)
        elif task.recurrence == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None  # one-shot task — nothing to spawn

        next_task = Task(
            description=task.description,
            due_date_time=task.due_date_time + delta,
            pet_id=task.pet_id,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            recurrence=task.recurrence,
        )
        pet.add_task(next_task)
        return next_task

    def collect_tasks(self, owner: Owner) -> list[Task]:
        """Gather all tasks across every pet owned by the given owner."""
        all_tasks = []
        for pet in owner.list_pets():
            all_tasks.extend(pet.list_tasks())
        return all_tasks

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by their due time (HH:MM), earliest first."""
        return sorted(tasks, key=lambda t: t.due_date_time.strftime("%H:%M"))

    def filter_by_status(self, tasks: list[Task], status: TaskStatus) -> list[Task]:
        """Return only tasks that match the given status (PENDING or COMPLETED)."""
        return [t for t in tasks if t.status == status]

    def filter_by_pet(self, owner: Owner, pet_name: str) -> list[Task]:
        """Return all tasks belonging to the pet with the given name (case-insensitive)."""
        for pet in owner.list_pets():
            if pet.name.lower() == pet_name.lower():
                return pet.list_tasks()
        return []

    def organize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority (1=High first), then by due date and time."""
        return sorted(tasks, key=lambda t: (t.priority, t.due_date_time))

    def generate_daily_plan(self, owner: Owner) -> list[Task]:
        """Return today's conflict-free, priority-ordered task schedule for the owner."""
        today = datetime.now().date()
        tasks = [
            t for t in self.collect_tasks(owner)
            if t.status == TaskStatus.PENDING and t.due_date_time.date() == today
        ]
        organized = self.organize_tasks(tasks)
        return self.resolve_conflicts(organized)

    def detect_conflicts(self, owner: Owner) -> list[str]:
        """Return a warning string for every pair of pending tasks whose time windows overlap."""
        pet_lookup = {pet.id: pet.name for pet in owner.list_pets()}
        pending = [
            t for t in self.collect_tasks(owner)
            if t.status == TaskStatus.PENDING
        ]
        warnings: list[str] = []

        for i in range(len(pending)):
            for j in range(i + 1, len(pending)):
                a, b = pending[i], pending[j]
                a_end = a.due_date_time + timedelta(minutes=a.duration_minutes)
                b_end = b.due_date_time + timedelta(minutes=b.duration_minutes)
                if a.due_date_time < b_end and b.due_date_time < a_end:
                    warnings.append(
                        f"WARNING: '{a.description}' ({pet_lookup[a.pet_id]}, "
                        f"{a.due_date_time.strftime('%I:%M %p')}-{a_end.strftime('%I:%M %p')}) "
                        f"overlaps with '{b.description}' ({pet_lookup[b.pet_id]}, "
                        f"{b.due_date_time.strftime('%I:%M %p')}-{b_end.strftime('%I:%M %p')})"
                    )
        return warnings

    def resolve_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Push any overlapping task to start immediately after the previous one ends."""
        resolved: list[Task] = []
        for task in tasks:
            if resolved:
                prev = resolved[-1]
                prev_end = prev.due_date_time + timedelta(minutes=prev.duration_minutes)
                if task.due_date_time < prev_end:
                    task.due_date_time = prev_end
            resolved.append(task)
        return resolved
