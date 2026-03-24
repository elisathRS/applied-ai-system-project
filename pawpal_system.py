from dataclasses import dataclass, field
from datetime import datetime
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
        pass


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
        pass

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass

    def remove_task(self, _task: Task) -> None:
        """Remove a task from this pet."""
        pass


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
        pass

    def list_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's list."""
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Service layer — coordinates task management across all pets."""

    def collect_tasks(self, owner: Owner) -> list[Task]:
        """Gather all tasks across every pet owned by the given owner."""
        pass

    def organize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort and prioritize a list of tasks for the day."""
        pass

    def generate_daily_plan(self, owner: Owner) -> list[Task]:
        """Produce an ordered daily schedule for the owner."""
        pass

    def resolve_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Adjust tasks that overlap in time or priority."""
        pass
