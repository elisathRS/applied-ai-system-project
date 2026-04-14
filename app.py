import logging
import streamlit as st
from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, TaskStatus, Scheduler
from ai_advisor import suggest_tasks

# Configure root logging once for the whole app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("pawpal.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
_app_logger = logging.getLogger("app")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

scheduler = Scheduler()

# ---------------------------------------------------------------------------
# Section 0 — Owner Info
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Owner Info")

if "owner" not in st.session_state:
    st.session_state.owner = None

with st.form("owner_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        owner_name = st.text_input("Full name")
    with col2:
        owner_phone = st.text_input("Phone number")
    with col3:
        owner_email = st.text_input("Email")
    submitted = st.form_submit_button("Save owner")
    if submitted:
        errors = []
        if not owner_name.strip():
            errors.append("Full name is required.")
        if not owner_phone.strip():
            errors.append("Phone number is required.")
        elif not owner_phone.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            errors.append("Phone number must contain only digits, spaces, or dashes.")
        if not owner_email.strip():
            errors.append("Email is required.")
        elif "@" not in owner_email or "." not in owner_email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.owner = Owner(name=owner_name, phone_number=owner_phone, email=owner_email)
            st.success(f"Owner saved: {owner_name}")

if st.session_state.owner is None:
    st.info("Fill in your info above and click Save owner to get started.")
    st.stop()

owner: Owner = st.session_state.owner
st.write(f"**Owner:** {owner.name} | {owner.phone_number} | {owner.email}")

# ---------------------------------------------------------------------------
# Section 1 — Add a Pet
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Add a Pet")

if "pet_form_key" not in st.session_state:
    st.session_state.pet_form_key = 0

with st.form(f"pet_form_{st.session_state.pet_form_key}"):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name")
        species  = st.selectbox("Species", ["dog", "cat", "other"])
        breed    = st.text_input("Breed")
    with col2:
        age    = st.number_input("Age (years)", min_value=0, max_value=30, value=0)
        gender = st.selectbox("Gender", ["female", "male"])
        weight = st.number_input("Weight (lbs)", min_value=0.0, max_value=300.0, value=0.0)
    add_pet = st.form_submit_button("Add pet")
    if add_pet:
        errors = []
        if not pet_name.strip():
            errors.append("Pet name is required.")
        if not breed.strip():
            errors.append("Breed is required.")
        if age == 0:
            errors.append("Age must be greater than 0.")
        if weight == 0.0:
            errors.append("Weight must be greater than 0.00 lbs.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            new_pet = Pet(name=pet_name, species=species, breed=breed,
                          age=int(age), gender=gender, weight=float(weight))
            owner.add_pet(new_pet)
            st.session_state.pet_form_key += 1
            st.session_state.task_form_key += 1       # reset task form
            st.session_state.default_task_pet = pet_name  # pre-select new pet
            st.rerun()

current_pets = owner.list_pets()

SPECIES_EMOJI = {"dog": "🐶", "cat": "🐱", "other": "🐾"}

if not current_pets:
    st.info("No pets yet. Add one above.")
else:
    st.write(f"**{owner.name} has {len(current_pets)} pet(s):**")
    header = st.columns([0.4, 1.6, 1.2, 1.2, 1, 1.2, 1.2, 1])
    for col, label in zip(header, ["", "Name", "Species", "Breed", "Age", "Gender", "Weight", "Delete"]):
        col.markdown(f"**{label}**")

    for pet in list(current_pets):
        emoji = SPECIES_EMOJI.get(pet.species, "🐾")
        cols = st.columns([0.4, 1.6, 1.2, 1.2, 1, 1.2, 1.2, 1])
        cols[0].write(emoji)
        cols[1].write(pet.name)
        cols[2].write(pet.species)
        cols[3].write(pet.breed)
        cols[4].write(f"{pet.age} yr")
        cols[5].write(pet.gender)
        cols[6].write(f"{pet.weight} lbs")
        if cols[7].button("❌", key=f"del_{pet.id}"):
            owner.remove_pet(pet)
            st.rerun()

# ---------------------------------------------------------------------------
# Section 2 — Add a Task
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Add a Task")

if "task_form_key" not in st.session_state:
    st.session_state.task_form_key = 0
if "default_task_pet" not in st.session_state:
    st.session_state.default_task_pet = None

if not current_pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    with st.form(f"task_form_{st.session_state.task_form_key}"):
        pet_names   = [p.name for p in current_pets]
        default_idx = pet_names.index(st.session_state.default_task_pet) \
            if st.session_state.default_task_pet in pet_names else 0
        target_name = st.selectbox("Assign to pet", pet_names, index=default_idx)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=1)
        confirm_1min = False
        if duration == 1:
            confirm_1min = st.checkbox("⚠️ This task will last only 1 minute. Check to confirm.")
        with col3:
            priority_label = st.selectbox("Priority", ["High", "Medium", "Low"])

        col4, col5, col6 = st.columns(3)
        with col4:
            task_date = st.date_input("Start date", value=datetime.now().date())
        with col5:
            task_time = st.time_input("Due time", value=None)
        with col6:
            recurrence = st.selectbox("Recurrence", ["None", "daily", "weekly"])

        add_task = st.form_submit_button("Add task")
        if add_task:
            errors = []
            if not task_title.strip():
                errors.append("Task title is required.")
            if task_time is None:
                errors.append("Due time is required. Please select a time.")
            if duration == 1 and not confirm_1min:
                errors.append("Please confirm that the task duration will be only 1 minute.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                target_pet = next(p for p in current_pets if p.name == target_name)
                due_dt = datetime(task_date.year, task_date.month, task_date.day,
                                  task_time.hour, task_time.minute, 0)
                priority_map = {"High": 1, "Medium": 2, "Low": 3}
                new_task = Task(
                    description=task_title,
                    due_date_time=due_dt,
                    pet_id=target_pet.id,
                    duration_minutes=int(duration),
                    priority=priority_map[priority_label],
                    recurrence=None if recurrence == "None" else recurrence,
                )
                target_pet.add_task(new_task)
                st.session_state.task_form_key += 1
                st.session_state.default_task_pet = target_name  # keep same pet selected
                st.rerun()

# ---------------------------------------------------------------------------
# Section 3 — Filter & Manage Tasks
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Filter & Manage Tasks")

all_tasks = scheduler.collect_tasks(owner)

if not all_tasks:
    st.info("No tasks yet. Add tasks above.")
else:
    pet_lookup    = {p.id: p.name for p in current_pets}
    priority_map  = {1: "High", 2: "Medium", 3: "Low"}

    col1, col2 = st.columns(2)
    with col1:
        filter_pet = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in current_pets])
    with col2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

    # Apply filters
    filtered = all_tasks
    if filter_pet != "All pets":
        filtered = scheduler.filter_by_pet(owner, filter_pet)
    if filter_status == "Pending":
        filtered = scheduler.filter_by_status(filtered, TaskStatus.PENDING)
    elif filter_status == "Completed":
        filtered = scheduler.filter_by_status(filtered, TaskStatus.COMPLETED)

    filtered = scheduler.sort_by_time(filtered)

    if not filtered:
        st.info("No tasks match the selected filters.")
    else:
        for task in filtered:
            end_time    = task.due_date_time + timedelta(minutes=task.duration_minutes)
            pet_name    = pet_lookup.get(task.pet_id, "Unknown")
            recur_tag   = f" [{task.recurrence}]" if task.recurrence else ""
            status_icon = "✅" if task.status == TaskStatus.COMPLETED else "🔲"
            date_str    = task.due_date_time.strftime("%a, %b %d %Y")

            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f"{status_icon} **{task.description}**{recur_tag} — {pet_name}  \n"
                    f"📅 {date_str} &nbsp; 🕐 {task.due_date_time.strftime('%I:%M %p')} – {end_time.strftime('%I:%M %p')} "
                    f"| {priority_map[task.priority]} priority | {task.status.value}"
                )
            with col_btn:
                if task.status == TaskStatus.PENDING:
                    if st.button("Mark done", key=str(task.id)):
                        pet = next(p for p in current_pets if p.id == task.pet_id)
                        next_task = scheduler.complete_task(task, pet)
                        if next_task:
                            st.success(f"Done! Next '{task.description}' scheduled for {next_task.due_date_time.strftime('%a %m/%d at %I:%M %p')}.")
                        else:
                            st.success("Task marked complete.")
                        st.rerun()

# ---------------------------------------------------------------------------
# Section 4 — Live Conflict Banner
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Scheduling Conflicts")

live_conflicts = scheduler.detect_conflicts(owner)
if not scheduler.collect_tasks(owner):
    st.info("No tasks yet — nothing to check.")
elif not live_conflicts:
    st.success("No conflicts detected — your schedule is clean.")
else:
    st.error(f"{len(live_conflicts)} conflict(s) found. Overlapping tasks will be automatically adjusted when generating your daily schedule.")
    for w in live_conflicts:
        # Strip the leading "WARNING: " prefix — st.warning already signals it visually
        clean = w.removeprefix("WARNING: ")
        st.warning(clean)

# ---------------------------------------------------------------------------
# Section 5 — Generate Today's Schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Generate Today's Schedule")

if st.button("Generate schedule"):
    plan = scheduler.generate_daily_plan(owner)
    if not plan:
        st.warning("No pending tasks scheduled for today.")
    else:
        if live_conflicts:
            st.caption("Overlapping tasks have been pushed to start after the previous one ends.")
        pet_lookup = {p.id: p.name for p in current_pets}
        rows = [
            {
                "Time": t.due_date_time.strftime("%I:%M %p"),
                "Ends": (t.due_date_time + timedelta(minutes=t.duration_minutes)).strftime("%I:%M %p"),
                "Pet": pet_lookup[t.pet_id],
                "Task": t.description,
                "Priority": {1: "High", 2: "Medium", 3: "Low"}[t.priority],
                "Recurrence": t.recurrence or "one-shot",
            }
            for t in plan
        ]
        st.success(f"{len(plan)} task(s) scheduled for today.")
        st.table(rows)

# ---------------------------------------------------------------------------
# Section 6 — AI Care Advisor (RAG + Agentic Workflow)
# ---------------------------------------------------------------------------
st.divider()
st.subheader("AI Care Advisor")
st.caption(
    "Powered by Claude. The AI retrieves care guidelines from the knowledge base "
    "for your pet's species and age, then suggests personalised tasks for today."
)

if not current_pets:
    st.info("Add a pet first to get AI-powered care suggestions.")
else:
    if "ai_suggestions" not in st.session_state:
        st.session_state.ai_suggestions = {}   # pet_id → list[Task] | str
    if "added_suggestions" not in st.session_state:
        st.session_state.added_suggestions = set()  # task ids already added

    advisor_pet_name = st.selectbox(
        "Select pet for AI suggestions",
        [p.name for p in current_pets],
        key="advisor_pet_select",
    )
    advisor_pet = next(p for p in current_pets if p.name == advisor_pet_name)

    col_btn, col_clear = st.columns([2, 1])
    with col_btn:
        get_suggestions = st.button("Get AI suggestions", type="primary")
    with col_clear:
        if st.button("Clear suggestions"):
            st.session_state.ai_suggestions.pop(str(advisor_pet.id), None)
            st.session_state.added_suggestions = set()
            st.rerun()

    if get_suggestions:
        _app_logger.info(
            "User requested AI suggestions for pet '%s' (%s)",
            advisor_pet.name, advisor_pet.species,
        )
        with st.spinner("Retrieving care guidelines and generating suggestions..."):
            result = suggest_tasks(advisor_pet, owner, scheduler)
        st.session_state.ai_suggestions[str(advisor_pet.id)] = result
        st.rerun()

    cached = st.session_state.ai_suggestions.get(str(advisor_pet.id))

    if cached is not None:
        if isinstance(cached, str):
            # Error message returned by the advisor
            st.error(cached)
        else:
            priority_labels = {1: "High", 2: "Medium", 3: "Low"}
            st.success(f"{len(cached)} task suggestion(s) for **{advisor_pet.name}**:")

            for suggestion in cached:
                end_time = suggestion.due_date_time + timedelta(minutes=suggestion.duration_minutes)
                recur_tag = f" [{suggestion.recurrence}]" if suggestion.recurrence else ""
                already_added = str(suggestion.id) in st.session_state.added_suggestions

                col_info, col_add = st.columns([4, 1])
                with col_info:
                    st.markdown(
                        f"**{suggestion.description}**{recur_tag}  \n"
                        f"🕐 {suggestion.due_date_time.strftime('%I:%M %p')} – {end_time.strftime('%I:%M %p')} "
                        f"| {priority_labels[suggestion.priority]} priority "
                        f"| {suggestion.duration_minutes} min"
                    )
                with col_add:
                    if already_added:
                        st.success("Added")
                    else:
                        if st.button("Add to schedule", key=f"add_sug_{suggestion.id}"):
                            advisor_pet.add_task(suggestion)
                            st.session_state.added_suggestions.add(str(suggestion.id))
                            _app_logger.info(
                                "User added AI suggestion to schedule: '%s' for %s",
                                suggestion.description, advisor_pet.name,
                            )
                            st.rerun()
