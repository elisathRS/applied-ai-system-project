import streamlit as st
from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, TaskStatus, Scheduler

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
        new_pet = Pet(name=pet_name, species=species, breed=breed,
                      age=int(age), gender=gender, weight=float(weight))
        owner.add_pet(new_pet)
        st.session_state.pet_form_key += 1
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

if not current_pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    with st.form(f"task_form_{st.session_state.task_form_key}"):
        pet_names   = [p.name for p in current_pets]
        target_name = st.selectbox("Assign to pet", pet_names)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=1)
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

    filtered = sorted(filtered, key=lambda t: t.due_date_time)

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
# Section 4 — Conflict Detection
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Conflict Detection")

if st.button("Check for conflicts"):
    warnings = scheduler.detect_conflicts(owner)
    if not warnings:
        st.success("No scheduling conflicts found.")
    else:
        for w in warnings:
            st.warning(w)

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
