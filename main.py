from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from pawpal_system import Owner, Pet, Task, TaskStatus, Scheduler

console = Console()

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
scheduler   = Scheduler()
pet_lookup  = {pet.id: pet.name for pet in owner.list_pets()}

PRIORITY_STYLE = {1: "[bold red]High[/]", 2: "[yellow]Medium[/]", 3: "[green]Low[/]"}
PRIORITY_LABEL = {1: "High",              2: "Medium",             3: "Low"}
SPECIES_EMOJI  = {"dog": "🐶", "cat": "🐱"}
STATUS_ICON    = {TaskStatus.PENDING: "🔲", TaskStatus.COMPLETED: "✅"}
RECUR_ICON     = {"daily": "🔁 daily", "weekly": "📅 weekly", None: "1️⃣  one-shot"}


def make_task_table(tasks: list, title: str) -> Table:
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold cyan",
        header_style="bold white on dark_blue",
    )
    table.add_column("Status",     justify="center", width=4)
    table.add_column("Pet",        style="cyan")
    table.add_column("Task",       style="bold")
    table.add_column("Date",       style="white")
    table.add_column("Time",       style="white")
    table.add_column("Priority",   justify="center")
    table.add_column("Recurrence", justify="center")

    for task in tasks:
        end_time  = task.due_date_time + timedelta(minutes=task.duration_minutes)
        pet_name  = pet_lookup.get(task.pet_id, "Unknown")
        emoji     = SPECIES_EMOJI.get(
            next((p.species for p in owner.list_pets() if p.id == task.pet_id), ""), "🐾"
        )
        table.add_row(
            STATUS_ICON[task.status],
            f"{emoji} {pet_name}",
            task.description,
            task.due_date_time.strftime("%a %m/%d"),
            f"{task.due_date_time.strftime('%I:%M %p')} – {end_time.strftime('%I:%M %p')}",
            PRIORITY_STYLE[task.priority],
            RECUR_ICON.get(task.recurrence, task.recurrence),
        )
    return table


# ---------------------------------------------------------------------------
# 1. Conflict detection
# ---------------------------------------------------------------------------
console.print()
conflicts = scheduler.detect_conflicts(owner)
if conflicts:
    conflict_lines = "\n".join(f"  ⚠️  {w.removeprefix('WARNING: ')}" for w in conflicts)
    console.print(Panel(
        conflict_lines,
        title="[bold red]⚠️  CONFLICT DETECTION REPORT[/]",
        border_style="red",
    ))
    console.print(f"  [red]{len(conflicts)} conflict(s) detected.[/]\n")
else:
    console.print(Panel("[green]No conflicts found.[/]", title="CONFLICT DETECTION REPORT", border_style="green"))

# ---------------------------------------------------------------------------
# 2. All tasks — raw insertion order
# ---------------------------------------------------------------------------
all_tasks = scheduler.collect_tasks(owner)
console.print(make_task_table(all_tasks, "ALL TASKS — raw order, recurrence labels visible"))
console.print(f"  [dim]{len(all_tasks)} task(s)[/]\n")

# ---------------------------------------------------------------------------
# 3. Complete recurring tasks and one-shot
# ---------------------------------------------------------------------------
morning_walk = next(t for t in mochi.tasks if t.description == "Morning walk")
console.print(f"  [bold]>> Completing[/] '[cyan]{morning_walk.description}[/]' (recurrence=[yellow]{morning_walk.recurrence}[/])")
next_task = scheduler.complete_task(morning_walk, mochi)
if next_task:
    console.print(f"  [green]>> Spawned next:[/] {next_task.description} on {next_task.due_date_time.strftime('%a %m/%d at %I:%M %p')}\n")

litter_box = next(t for t in luna.tasks if t.description == "Clean litter box")
console.print(f"  [bold]>> Completing[/] '[cyan]{litter_box.description}[/]' (recurrence=[yellow]{litter_box.recurrence}[/])")
next_task = scheduler.complete_task(litter_box, luna)
if next_task:
    console.print(f"  [green]>> Spawned next:[/] {next_task.description} on {next_task.due_date_time.strftime('%a %m/%d at %I:%M %p')}\n")

vet = next(t for t in luna.tasks if t.description == "Vet check-up")
console.print(f"  [bold]>> Completing[/] '[cyan]{vet.description}[/]' (recurrence=[yellow]{vet.recurrence}[/])")
result = scheduler.complete_task(vet, luna)
console.print(f"  [dim]>> Next occurrence spawned: {result}[/]\n")

# ---------------------------------------------------------------------------
# 4. All tasks after completions — sorted by time
# ---------------------------------------------------------------------------
pet_lookup = {pet.id: pet.name for pet in owner.list_pets()}
all_tasks  = scheduler.collect_tasks(owner)
console.print(make_task_table(scheduler.sort_by_time(all_tasks), "ALL TASKS AFTER COMPLETIONS — sorted by time"))
console.print(f"  [dim]{len(all_tasks)} task(s)[/]\n")

# ---------------------------------------------------------------------------
# 5. Pending only
# ---------------------------------------------------------------------------
pending = scheduler.filter_by_status(all_tasks, TaskStatus.PENDING)
console.print(make_task_table(pending, "🔲  PENDING TASKS ONLY"))
console.print(f"  [dim]{len(pending)} task(s)[/]\n")

# ---------------------------------------------------------------------------
# 6. Completed only
# ---------------------------------------------------------------------------
completed = scheduler.filter_by_status(all_tasks, TaskStatus.COMPLETED)
console.print(make_task_table(completed, "✅  COMPLETED TASKS ONLY"))
console.print(f"  [dim]{len(completed)} task(s)[/]\n")

# ---------------------------------------------------------------------------
# 7. Today's conflict-free priority-ordered daily plan
# ---------------------------------------------------------------------------
plan = scheduler.generate_daily_plan(owner)
console.print(make_task_table(plan, "📋  TODAY'S DAILY PLAN — priority-sorted, conflicts resolved"))
console.print(f"  [dim]{len(plan)} task(s) scheduled for today[/]\n")
