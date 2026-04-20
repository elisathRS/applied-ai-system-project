# Model Card: PawPal+

## 1. Model Name

**PawPal+ AI Care Advisor**
Built on **Gemini 2.5 Flash** (Google Generative AI API), integrated via a RAG + agentic workflow.

---

## 2. Intended Use

**Who it is for:** Pet owners who want personalized daily care suggestions based on their pet's species, age, and weight.

**What it does:** Retrieves species- and age-specific veterinary guidelines from a local knowledge base, then uses Gemini to suggest 3–5 structured care tasks that avoid conflicts with the existing schedule.

**What it does not do:** It does not provide medical diagnoses, replace veterinary advice, or persist data across sessions.

---

## 3. How the Model Works

The system follows a 4-step agentic workflow:

1. **RAG Retrieval** — `load_knowledge_base()` loads the species-specific JSON file (`dog.json`, `cat.json`, or `other.json`). `retrieve_relevant_guidelines()` filters sections by the pet's age (puppy, adult, or senior) and returns them as text context.
2. **Prompt Construction** — The pet profile (name, species, breed, age, weight, gender), retrieved guidelines, and existing pending tasks are assembled into a single prompt.
3. **Gemini Call** — The prompt is sent to Gemini 2.5 Flash, which returns a JSON array of 3–5 task suggestions with fields: `description`, `hour`, `minute`, `duration_minutes`, `priority`, and `recurrence`.
4. **Guardrail Validation** — `_parse_and_validate()` parses the JSON, clamps out-of-range values, rejects malformed items, and converts valid items into `Task` objects. The user then reviews and approves suggestions before they enter the schedule.

---

## 4. Data

**Knowledge base:** Hand-written JSON files covering dogs, cats, and a generic fallback. Each file contains sections for general care, feeding, exercise, grooming, veterinary checkups, and age-specific care (puppy/kitten, adult, senior).

**No user data is stored:** All owner, pet, and task data lives in Streamlit session state and is lost on page refresh. No data is sent to external services beyond the Gemini API call.

**Training data:** The underlying Gemini 2.5 Flash model was trained by Google. No fine-tuning or additional training was performed for this project.

---

## 5. Strengths

- **Grounded output:** RAG retrieval ensures suggestions are based on real veterinary guidelines, not generic AI responses. A 10-year-old senior dog receives different suggestions than a 2-year-old adult dog.
- **Conflict awareness:** The prompt includes existing scheduled tasks, so Gemini avoids suggesting tasks that overlap with the current schedule.
- **Robust guardrail:** `_parse_and_validate()` handles all known Gemini failure modes — markdown code fences, single objects instead of arrays, invalid recurrence values, out-of-range priorities — without crashing the app.
- **Human in the loop:** Suggestions are never added automatically. The user reviews and approves each one before it enters the schedule.

---

## 6. Limitations and Bias

**Knowledge base coverage:** The knowledge base does not cover breed-specific conditions (e.g., hip dysplasia in large-breed dogs, brachycephalic issues in bulldogs) or individual medical history. A 10-year-old Chihuahua and a 10-year-old Great Dane receive the same senior dog guidelines.

**Fixed age thresholds:** The system uses fixed rules (age ≤ 1 = puppy, age ≥ 8 = senior) that may not apply equally across all breeds and species.

**No cultural or regional context:** The knowledge base was written from a general Western veterinary perspective. Feeding habits, exercise norms, and care routines may differ across regions.

**AI output variability:** Gemini does not always produce identical suggestions for the same input. The guardrail ensures structural validity, but content may vary between runs.

**No persistence:** All data is lost on page refresh. The system cannot learn from a user's history or adapt suggestions over time.

---

## 7. Evaluation

| Test File | Tests | What It Covers |
|---|---|---|
| `tests/test_ai_advisor.py` | 24 | RAG loading, guideline retrieval by age, guardrail validation, API error handling, output consistency |
| `tests/test_pawpal.py` | 16 | Task completion, recurrence chaining, conflict detection, sorting, filtering |
| **Total** | **40** | **All 40 pass** |

The Gemini API is mocked in all tests — the suite runs in under 2 seconds with no internet connection or API credits required.

**What surprised me during testing:** Gemini violated the output schema in predictable, repeatable ways rather than random failures. It wrapped JSON in markdown code fences even when the prompt said not to, used `"monthly"` as a recurrence value (plausible in English but invalid in the schema), and occasionally returned a single object instead of an array. These patterns suggested the model draws on common JSON examples from training data rather than strictly following the prompt. Each failure mode is now caught by the guardrail.

---

## 8. Future Work

- Add a SQLite or Firebase database for persistence across sessions.
- Replace the rule-based RAG filter with vector embeddings for semantic retrieval across a larger, more detailed knowledge base.
- Add breed-specific care sections to the knowledge base.
- Sanitize pet input fields to prevent prompt injection beyond the current 80-character truncation.
- Add a conversational AI chat so owners can ask follow-up questions like *"Is it normal for my senior dog to drink more water?"*

---

## 9. Personal Reflection

Building PawPal+ taught me that AI integration is less about the model and more about the layers around it. What matters is what you feed it (RAG), how you validate what comes out (guardrail), and how you keep the human informed and in control (review step). The intelligence in this system is in the retrieval and prompt design, not just the model itself.
