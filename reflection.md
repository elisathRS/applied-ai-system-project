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
      
      - **"What is a better name for this variable or method?"**
        - Improved readability and clarity.
      
      - **"Give me an example"**
        - Helped me understand concepts faster with simple examples.
      
      - **"What are best practices for this?"**
        - Guided me to write more professional and reliable code.
      
      - **"What edge cases should I consider?"**
        - Helped me think about problems I might miss.
      
      - **"Can you simplify this explanation?"**
        - Made difficult topics easier to understand.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
