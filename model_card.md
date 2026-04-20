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

All 40 tests pass. The Gemini API is mocked in all AI tests — the suite runs in under 2 seconds with no internet connection or API credits required.

### tests/test_ai_advisor.py (24 tests)

**Knowledge Base Loading (4 tests)**
| Test | What it verifies |
|---|---|
| `test_loads_dog_kb` | `dog.json` loads correctly and contains `general` and `feeding` sections |
| `test_loads_cat_kb` | `cat.json` loads correctly and contains a `general` section |
| `test_unknown_species_falls_back_to_other` | An unknown species (e.g. "dragon") loads `other.json` without crashing |
| `test_returns_empty_dict_on_missing_file` | If the knowledge base directory is empty, returns `{}` instead of raising an exception |

**Guideline Retrieval by Age (5 tests)**
| Test | What it verifies |
|---|---|
| `test_puppy_gets_puppy_section` | A dog aged 0 receives guidelines containing "puppy" or "young" |
| `test_senior_gets_senior_section` | A dog aged 10 receives guidelines containing "senior" |
| `test_adult_gets_adult_section` | A dog aged 4 receives guidelines containing "adult" |
| `test_returns_non_empty_string` | Retrieved guidelines are always a non-empty string for a known species |
| `test_empty_kb_returns_empty_string` | An empty knowledge base returns `""` without crashing |

**Guardrail Validation (11 tests)**
| Test | What it verifies |
|---|---|
| `test_valid_json_returns_task_list` | A well-formed JSON array produces a list of 3 `Task` objects |
| `test_tasks_have_correct_pet_id` | Every parsed task is linked to the correct pet's UUID |
| `test_tasks_are_pending_by_default` | All parsed tasks start with `status = PENDING` |
| `test_strips_markdown_code_fences` | Input wrapped in ` ```json ` fences is cleaned and parsed correctly |
| `test_invalid_json_returns_error_string` | Completely invalid JSON (e.g. `"not json at all"`) returns an error string, not a crash |
| `test_non_array_json_returns_error_string` | A JSON object instead of an array returns an error string |
| `test_missing_required_fields_skips_item` | An item missing `duration_minutes` or `priority` is skipped; valid items still parse |
| `test_priority_clamped_to_valid_range` | A priority of `99` is clamped to `3` (max valid value) |
| `test_invalid_recurrence_set_to_none` | `"recurrence": "monthly"` is reset to `null` automatically |
| `test_all_invalid_items_returns_error_string` | If every item is invalid, returns an error string instead of an empty list |
| `test_description_truncated_to_80_chars` | A 200-character description is truncated to 80 characters |

**API Integration (4 tests)**
| Test | What it verifies |
|---|---|
| `test_missing_api_key_returns_error_string` | Missing `GEMINI_API_KEY` returns a clear error message, not a crash |
| `test_returns_task_list_on_valid_api_response` | A mocked valid API response produces a list of 3 `Task` objects |
| `test_auth_error_returns_clear_message` | A mocked 401/permission error returns a user-readable message |
| `test_output_is_consistent_format` | The same pet profile always returns `list[Task]` or `str` — never raises an exception |

---

### tests/test_pawpal.py (16 tests)

**Core Operations (2 tests)**
| Test | What it verifies |
|---|---|
| `test_mark_complete_changes_status` | Calling `mark_complete()` changes a task's status from `PENDING` to `COMPLETED` |
| `test_add_task_increases_pet_task_count` | Adding 2 tasks to a pet results in `len(pet.list_tasks()) == 2` |

**Sorting (3 tests)**
| Test | What it verifies |
|---|---|
| `test_sort_by_time_returns_chronological_order` | Tasks given out of order (2 PM, 8 AM, 11 AM) come back sorted earliest → latest |
| `test_sort_by_time_preserves_all_tasks` | Sorting 4 tasks always returns exactly 4 tasks — no drops or duplicates |
| `test_sort_by_time_already_sorted_is_unchanged` | Tasks already in order remain in the same order after sorting |

**Recurrence (5 tests)**
| Test | What it verifies |
|---|---|
| `test_complete_daily_task_creates_next_day_task` | Completing a daily task spawns a new task exactly 24 hours later |
| `test_complete_daily_task_adds_to_pet` | The spawned task appears in the pet's task list (total = 2) |
| `test_complete_daily_task_marks_original_done` | The original task is `COMPLETED` after the chain spawns |
| `test_complete_daily_task_inherits_recurrence` | The new task keeps `recurrence="daily"` so the chain continues indefinitely |
| `test_complete_oneshot_task_returns_none` | A task with `recurrence=None` returns `None` and adds nothing to the schedule |
| `test_complete_weekly_task_creates_next_week_task` | Completing a weekly task spawns a new task exactly 7 days later |

**Conflict Detection (5 tests)**
| Test | What it verifies |
|---|---|
| `test_detect_conflicts_flags_overlapping_tasks` | Two tasks with a 15-minute overlap (9:00–9:30 and 9:15–9:45) produce at least one warning |
| `test_detect_conflicts_warning_contains_task_names` | The warning message names both conflicting tasks ("Morning Walk" and "Feeding") |
| `test_detect_conflicts_no_warning_for_sequential_tasks` | Back-to-back tasks (9:00–9:30 and 9:30–10:00) produce zero warnings |
| `test_detect_conflicts_no_warning_when_no_tasks` | An owner with no tasks produces zero warnings |
| `test_detect_conflicts_flags_cross_pet_overlap` | Overlapping tasks assigned to different pets are still flagged |

---

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
