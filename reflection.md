# PawPal+ Project Reflection

## 1. System Design

### a. Initial Design

- **Briefly describe your initial UML design:**  
  The design models a pet care system with four main classes: **Owner, Pet, Task, and Scheduler**. It organizes the relationships between owners, their pets, and tasks, while separating task management logic from the data.

- **What classes did you include, and what responsibilities did you assign to each?**  

  **Classes:**  
  - **Owner** – represents a pet owner.  
  - **Pet** – represents an individual pet.  
  - **Task** – represents a pet-related task.  
  - **Scheduler** – manages and organizes tasks across pets.  

  **Responsibilities:**  
  - **Owner:** Manage pets (add, list, remove).  
  - **Pet:** Store pet info and manage its tasks (add, list, remove).  
  - **Task:** Track task details and completion status (mark complete).  
  - **Scheduler:** Collect all tasks, organize them, generate daily plans, and resolve conflicts.  

**b. Design changes**

- Did your design change during implementation?
    Yes
- If yes, describe at least one change and why you made it.

   These changes make the code safer, clearer, and easier to manage.

  **Renamed `type` → `species`**
  - `type` is a Python built-in function.
  - Using it can cause confusing bugs.
  - `species` is clearer and safer.
  
  **Added `TaskStatus` enum**
  - Replaced text status with a fixed set of values.
  - Prevents mistakes like spelling errors.
  - Only `PENDING` and `COMPLETED` are allowed.
  
  **Added `id: UUID` to Task and Pet**
  - Names can be repeated.
  - UUID gives each object a unique ID.
  - Ensures the correct item is removed or found.
  
  **Added `pet_id: UUID` to Task**
  - Keeps track of which pet each task belongs to.
  - Important when all tasks are in one list.
  - Maintains the connection between task and pet.
  
  **Added `duration_minutes` to Task**
  - Helps know how long a task takes.
  - Needed to detect time conflicts.
  - Default is 30 minutes.
  
  **Added `priority` to Task**
  - Allows tasks to be sorted by importance.
  - Levels:
    - `1 = High`
    - `2 = Medium` (default)
    - `3 = Low`
  - Improves scheduling beyond just time.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  
   - **Design brainstorming**
      - I used AI to plan the structure of the app.
      - It helped me decide the main classes and their roles.
  
  - **Code explanation**
    - I asked AI to explain code step by step.
    - This helped me understand difficult concepts.
  
  - **Debugging**
    - AI helped me find and fix errors in my code.
    - It explained why the code was not working.
  
  - **Refactoring**
    - AI suggested cleaner and more organized code.
    - It improved readability and structure.
  
  - **Naming improvements**
    - AI helped me choose clearer names for variables and methods.
  
  - **Best practices**
    - AI suggested improvements like using enums and unique IDs.
    - This made my code more reliable.
  
  - **Documentation**
    - AI helped me write clear summaries and explanations.
    - It improved my GitHub README.

- What kinds of prompts or questions were most helpful?

  - **"Explain this code step by step"**
    - Helped me understand complex logic in simple terms.
      
  - **"Why is this code not working?"**
    - Useful for debugging and finding errors.
      
  - **"How can I improve this code?"**
    - Helped with refactoring and making code cleaner.
      
  - **"Give me an example"**
    - Helped me understand concepts faster with simple examples.
      
  - **"What are best practices for this?"**
    - Guided me to write more professional and reliable code.
      
  - **"What edge cases should I consider?"**
    - Helped me think about problems I might miss.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  
  I asked an AI to help handle overlapping tasks in my Scheduler class, and it suggested simply deleting conflicts. I realized this would remove important tasks, so I didn’t accept it as-is and      designed a method to adjust overlapping tasks instead.
  
- How did you evaluate or verify what the AI suggested?
  
  I evaluated the suggestion by reasoning through multiple task scenarios to see if any tasks would be lost. Then I wrote test cases simulating overlapping tasks for multiple pets and confirmed      that deleting conflicts would indeed remove tasks. This verification guided me to implement a safer approach that maintains all tasks while resolving conflicts automatically.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

| Test | Why |
|------|-----|
| Task marked complete changes status | Core operation — the whole system depends on knowing what's done vs pending |
| Adding tasks increases pet's task count | Ensures tasks are actually stored, not silently dropped |
| Sort returns tasks earliest → latest | Daily plan is built on sorted order; wrong order = broken schedule |
| Sort doesn't drop or duplicate tasks | A sort that loses tasks would corrupt the plan with no error |
| Daily task spawns new task 1 day later | Recurring care (feeding, walks) must continue automatically |
| New task inherits `recurrence="daily"` | Without this, the chain breaks after one completion |
| Original task marked COMPLETED after recurring | Prevents the same task from appearing twice in the plan |
| Weekly task spawns 1 week later | Same chain logic, different interval |
| One-shot task returns None, adds nothing | Prevents phantom tasks from cluttering the schedule |
| Overlapping tasks produce a warning | Owner needs to know when two tasks can't both happen as scheduled |
| Warning includes both task names | A vague warning is useless — user needs to know *which* tasks conflict |
| Back-to-back tasks produce no warning | Avoids false alarms for a perfectly valid schedule |
| Empty task list produces no warning | Edge case — app shouldn't crash or warn on a fresh setup |
| Conflicts across different pets are flagged | Owner can't be in two places at once regardless of which pet the task belongs to |

**b. Confidence**

- How confident are you that your scheduler works correctly?
  
    I am fairly confident, about 4 out of 5. Every main feature has at least one test. Status changes, sorting, recurrence, and conflict detection all pass. It is not a 5 because the UI and full       user flows are not tested. Also, resolve_conflicts changes task times directly, which could cause problems if the same tasks are used in other parts of the app.
  
- What edge cases would you test next if you had more time?
  
    - **Owner with no pets**  
      Verify that `generate_daily_plan` returns an empty list and does not crash when the owner has no pets.
    
    - **Two pets with the same name**  
      Check how `filter_by_pet` behaves, since it stops at the first match and may ignore tasks from the second pet.
    
    - **Task with `duration_minutes = 0`**  
      Ensure this does not create false positives or missed conflicts in `detect_conflicts`.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  
    I am most satisfied with the Scheduler class because it brings everything together. It can collect tasks, organize them, detect conflicts, and generate a daily plan. It shows how different         parts of the system work together in one place.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  
   I would improve the performance of detect_conflicts. It currently compares every task with every other task, which is not efficient. I would optimize it by sorting tasks first and checking only    nearby ones.t.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  
  I learned that AI can be very helpful for brainstorming design ideas, explaining code, or debugging, but I still need to carefully review suggestions and make sure they fit the system’s design     principles.
