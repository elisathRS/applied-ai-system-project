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

    def collect_tasks(self, owner: Owner) -> list[Task]:
        """Gather all tasks across every pet owned by the given owner."""
        all_tasks = []
        for pet in owner.list_pets():
            all_tasks.extend(pet.list_tasks())
        return all_tasks

    def organize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort and prioritize a list of tasks for the day.

        Primary sort: priority ascending (1=High comes first).
        Secondary sort: due_date_time ascending.
        """
        return sorted(tasks, key=lambda t: (t.priority, t.due_date_time))

    def generate_daily_plan(self, owner: Owner) -> list[Task]:
        """Produce an ordered daily schedule for the owner.

        Collects all pending tasks due today, organizes them, then
        resolves any time conflicts before returning the final plan.
        """
        today = datetime.now().date()
        tasks = [
            t for t in self.collect_tasks(owner)
            if t.status == TaskStatus.PENDING and t.due_date_time.date() == today
        ]
        organized = self.organize_tasks(tasks)
        return self.resolve_conflicts(organized)

    def resolve_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Adjust tasks that overlap in time.

        Tasks are processed in priority order (already sorted by the caller).
        If a task's start time overlaps with the previous task's window,
        it is pushed out to start immediately after the previous task ends.
        """
        resolved: list[Task] = []
        for task in tasks:
            if resolved:
                prev = resolved[-1]
                prev_end = prev.due_date_time + timedelta(minutes=prev.duration_minutes)
                if task.due_date_time < prev_end:
                    task.due_date_time = prev_end
            resolved.append(task)
        return resolved
