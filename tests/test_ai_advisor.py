"""
Reliability tests for the AI Care Advisor.

These tests verify the system's behaviour WITHOUT calling the real Claude API:
  - Knowledge base loading (RAG retrieval)
  - JSON guardrail: valid input produces correct Task objects
  - JSON guardrail: malformed / missing fields are handled safely
  - API key guard: missing key returns a clear error string
  - Output consistency: same pet profile always produces parseable tasks
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ai_advisor import (
    _parse_and_validate,
    load_knowledge_base,
    retrieve_relevant_guidelines,
    suggest_tasks,
)
from pawpal_system import Owner, Pet, Scheduler, Task, TaskStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_pet(species="dog", age=3, weight=20.0, name="Buddy", breed="Labrador"):
    return Pet(name=name, species=species, age=age, gender="male",
               weight=weight, breed=breed)


def make_owner(pet: Pet) -> Owner:
    owner = Owner(name="Test User", phone_number="555-0000", email="test@example.com")
    owner.add_pet(pet)
    return owner


def valid_json_response(pet: Pet) -> str:
    """Return a well-formed JSON string that the guardrail should accept."""
    today = datetime.now().date()
    return json.dumps([
        {
            "description": "Morning walk",
            "hour": 8,
            "minute": 0,
            "duration_minutes": 30,
            "priority": 2,
            "recurrence": "daily",
        },
        {
            "description": "Evening feeding",
            "hour": 18,
            "minute": 30,
            "duration_minutes": 15,
            "priority": 1,
            "recurrence": "daily",
        },
        {
            "description": "Grooming brush",
            "hour": 10,
            "minute": 0,
            "duration_minutes": 10,
            "priority": 3,
            "recurrence": None,
        },
    ])


# ---------------------------------------------------------------------------
# Knowledge base (RAG) tests
# ---------------------------------------------------------------------------

class TestLoadKnowledgeBase:
    def test_loads_dog_kb(self):
        kb = load_knowledge_base("dog")
        assert isinstance(kb, dict)
        assert "general" in kb
        assert "feeding" in kb

    def test_loads_cat_kb(self):
        kb = load_knowledge_base("cat")
        assert isinstance(kb, dict)
        assert "general" in kb

    def test_unknown_species_falls_back_to_other(self):
        kb = load_knowledge_base("dragon")
        assert isinstance(kb, dict)
        # Should load the 'other.json' fallback, not crash
        assert len(kb) > 0

    def test_returns_empty_dict_on_missing_file(self, tmp_path, monkeypatch):
        """If knowledge_base dir is empty, return {} without raising."""
        import ai_advisor
        monkeypatch.setattr(ai_advisor, "KB_DIR", tmp_path)
        result = load_knowledge_base("dog")
        assert result == {}


class TestRetrieveRelevantGuidelines:
    def test_puppy_gets_puppy_section(self):
        pet = make_pet(age=0)
        kb = load_knowledge_base("dog")
        text = retrieve_relevant_guidelines(pet, kb)
        assert "puppy" in text.lower() or "young" in text.lower()

    def test_senior_gets_senior_section(self):
        pet = make_pet(age=10)
        kb = load_knowledge_base("dog")
        text = retrieve_relevant_guidelines(pet, kb)
        assert "senior" in text.lower()

    def test_adult_gets_adult_section(self):
        pet = make_pet(age=4)
        kb = load_knowledge_base("dog")
        text = retrieve_relevant_guidelines(pet, kb)
        assert "adult" in text.lower()

    def test_returns_non_empty_string(self):
        pet = make_pet(species="cat", age=2)
        kb = load_knowledge_base("cat")
        text = retrieve_relevant_guidelines(pet, kb)
        assert isinstance(text, str) and len(text) > 0

    def test_empty_kb_returns_empty_string(self):
        pet = make_pet()
        text = retrieve_relevant_guidelines(pet, {})
        assert text == ""


# ---------------------------------------------------------------------------
# Guardrail (_parse_and_validate) tests
# ---------------------------------------------------------------------------

class TestParseAndValidate:
    def test_valid_json_returns_task_list(self):
        pet = make_pet()
        raw = valid_json_response(pet)
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(t, Task) for t in result)

    def test_tasks_have_correct_pet_id(self):
        pet = make_pet()
        raw = valid_json_response(pet)
        result = _parse_and_validate(raw, pet)
        assert all(t.pet_id == pet.id for t in result)

    def test_tasks_are_pending_by_default(self):
        pet = make_pet()
        raw = valid_json_response(pet)
        result = _parse_and_validate(raw, pet)
        assert all(t.status == TaskStatus.PENDING for t in result)

    def test_strips_markdown_code_fences(self):
        pet = make_pet()
        raw = "```json\n" + valid_json_response(pet) + "\n```"
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, list) and len(result) > 0

    def test_invalid_json_returns_error_string(self):
        pet = make_pet()
        result = _parse_and_validate("not json at all", pet)
        assert isinstance(result, str)
        assert "format" in result.lower() or "unexpected" in result.lower()

    def test_non_array_json_returns_error_string(self):
        pet = make_pet()
        result = _parse_and_validate('{"key": "value"}', pet)
        assert isinstance(result, str)

    def test_missing_required_fields_skips_item(self):
        pet = make_pet()
        raw = json.dumps([
            {"description": "Walk", "hour": 8, "minute": 0},  # missing duration + priority
            {
                "description": "Feed",
                "hour": 12,
                "minute": 0,
                "duration_minutes": 20,
                "priority": 1,
                "recurrence": None,
            },
        ])
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].description == "Feed"

    def test_priority_clamped_to_valid_range(self):
        pet = make_pet()
        raw = json.dumps([{
            "description": "Walk",
            "hour": 8,
            "minute": 0,
            "duration_minutes": 30,
            "priority": 99,   # out of range
            "recurrence": None,
        }])
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, list)
        assert result[0].priority == 3  # clamped to max valid value

    def test_invalid_recurrence_set_to_none(self):
        pet = make_pet()
        raw = json.dumps([{
            "description": "Walk",
            "hour": 8,
            "minute": 0,
            "duration_minutes": 30,
            "priority": 2,
            "recurrence": "monthly",  # not valid
        }])
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, list)
        assert result[0].recurrence is None

    def test_all_invalid_items_returns_error_string(self):
        pet = make_pet()
        raw = json.dumps([{"foo": "bar"}, {"baz": 1}])
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, str)

    def test_description_truncated_to_80_chars(self):
        pet = make_pet()
        long_desc = "A" * 200
        raw = json.dumps([{
            "description": long_desc,
            "hour": 9,
            "minute": 0,
            "duration_minutes": 30,
            "priority": 2,
            "recurrence": None,
        }])
        result = _parse_and_validate(raw, pet)
        assert isinstance(result, list)
        assert len(result[0].description) <= 80


# ---------------------------------------------------------------------------
# suggest_tasks integration tests (Claude API mocked)
# ---------------------------------------------------------------------------

class TestSuggestTasks:
    def test_missing_api_key_returns_error_string(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        pet = make_pet()
        owner = make_owner(pet)
        result = suggest_tasks(pet, owner, Scheduler())
        assert isinstance(result, str)
        assert "api key" in result.lower()

    def test_returns_task_list_on_valid_api_response(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        pet = make_pet()
        owner = make_owner(pet)
        mock_text = valid_json_response(pet)

        mock_response = MagicMock()
        mock_response.text = mock_text

        with patch("ai_advisor.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            result = suggest_tasks(pet, owner, Scheduler())

        assert isinstance(result, list)
        assert len(result) == 3

    def test_auth_error_returns_clear_message(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "bad-key")
        pet = make_pet()
        owner = make_owner(pet)

        with patch("ai_advisor.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.side_effect = Exception(
                "permission denied: api_key invalid"
            )
            result = suggest_tasks(pet, owner, Scheduler())

        assert isinstance(result, str)
        assert "key" in result.lower() or "invalid" in result.lower()

    def test_output_is_consistent_format(self, monkeypatch):
        """Same pet profile → always returns list[Task] or str (never crashes)."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        pet = make_pet()
        owner = make_owner(pet)
        mock_text = valid_json_response(pet)

        mock_response = MagicMock()
        mock_response.text = mock_text

        with patch("ai_advisor.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            for _ in range(3):
                result = suggest_tasks(pet, owner, Scheduler())
                assert isinstance(result, (list, str))
