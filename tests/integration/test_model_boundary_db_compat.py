"""Input models must reject values the database cannot store.

PostgreSQL text/varchar/jsonb columns cannot hold a NUL character, JSONB cannot hold
NaN/Infinity, documents.size_bytes is a 32-bit INTEGER and skills.tags is GIN indexed
(an index key above roughly 2.7KB is refused). SQLite accepts all of these and then
stores values that poison later reads (NaN in a JSON column makes every graph response
fail). The request models are the one place both backends share, so that is where the
values are refused, with an error the REST routes can return as a 400.
"""
import json

import pytest
from pydantic import ValidationError

from app.config.settings import settings
from app.models.document_models import DocumentCreate, DocumentUpdate
from app.models.entity_models import (
    EntityRelationship,
    EntityRelationshipCreate,
    EntityRelationshipUpdate,
)
from app.models.plan_models import (
    CriterionCreate,
    CriterionUpdate,
    Plan,
    PlanCreate,
    PlanUpdate,
    TaskCreate,
    TaskUpdate,
)
from app.models.skill_models import Skill, SkillCreate, SkillUpdate

NUL = "\x00"
INT32_MAX = 2_147_483_647

REL = {"source_entity_id": 1, "target_entity_id": 2, "relationship_type": "knows"}
SKILL = {"name": "a-skill", "description": "d", "content": "c"}
NOW = "2026-01-01T00:00:00Z"


def _rejected(model, payload):
    """Validate like the routes do; return the errors after proving they are JSON safe."""
    with pytest.raises(ValidationError) as caught:
        model(**payload)
    errors = caught.value.errors()
    # The REST routes return e.errors() as the 400 body: it must serialise, and must not
    # echo the offending value back (NaN cannot be written by a strict JSON encoder).
    json.dumps(errors, allow_nan=False)
    return errors


class TestRelationshipMetadata:
    @pytest.mark.parametrize("model,base", [
        (EntityRelationshipCreate, REL),
        (EntityRelationshipUpdate, {}),
    ])
    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_number_is_rejected(self, model, base, bad):
        errors = _rejected(model, {**base, "metadata": {"w": bad}})
        assert errors[0]["loc"] == ("metadata", "w")
        assert errors[0]["type"] == "non_finite_number"

    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e999"])
    def test_non_finite_number_in_json_text_is_rejected(self, token):
        body = json.dumps({"metadata": {"deep": [1, {"w": "TOKEN"}]}}).replace('"TOKEN"', token)
        with pytest.raises(ValidationError) as caught:
            EntityRelationshipUpdate.model_validate_json(body)
        errors = caught.value.errors()
        assert errors[0]["loc"] == ("metadata", "deep", 1, "w")
        json.dumps(errors, allow_nan=False)

    @pytest.mark.parametrize("model,base", [
        (EntityRelationshipCreate, REL),
        (EntityRelationshipUpdate, {}),
    ])
    @pytest.mark.parametrize("metadata,loc", [
        ({"a": f"x{NUL}y"}, ("metadata", "a")),
        ({"a": [f"x{NUL}y"]}, ("metadata", "a", 0)),
        ({f"k{NUL}": "v"}, ("metadata",)),
    ])
    def test_nul_character_is_rejected(self, model, base, metadata, loc):
        errors = _rejected(model, {**base, "metadata": metadata})
        assert errors[0]["loc"] == loc
        assert errors[0]["type"] == "nul_character"

    def test_storable_metadata_is_unchanged(self):
        metadata = {"w": 1, "f": 0.5, "big": 1e300, "neg": -2.5, "none": None, "flag": True,
                    "text": "tab\tnewline\n emoji \U0001f600 é", "nested": {"l": [1, 2.5, "x"]}}
        assert EntityRelationshipCreate(**REL, metadata=metadata).metadata == metadata
        assert EntityRelationshipUpdate(metadata=metadata).metadata == metadata
        assert EntityRelationshipUpdate(metadata={}).metadata == {}

    def test_error_does_not_echo_the_value(self):
        errors = _rejected(EntityRelationshipCreate, {**REL, "metadata": {"a": "secret" + NUL}})
        assert "secret" not in json.dumps(errors)

    def test_deeply_nested_metadata_does_not_overflow_the_stack(self):
        value: object = float("nan")
        for _ in range(5000):
            value = [value]
        errors = _rejected(EntityRelationshipUpdate, {"metadata": {"w": value}})
        assert errors[0]["type"] == "non_finite_number"
        assert len(errors[0]["loc"]) == 5002

    def test_response_model_still_reads_rows_stored_earlier(self):
        row = {**REL, "id": 1, "created_at": NOW, "updated_at": NOW,
               "metadata": {"w": float("nan"), "a": f"x{NUL}"}}
        relationship = EntityRelationship(**row)
        assert relationship.metadata is not None
        assert relationship.metadata["a"] == f"x{NUL}"


class TestSkill:
    @pytest.mark.parametrize("model,base", [(SkillCreate, SKILL), (SkillUpdate, {})])
    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_metadata_is_rejected(self, model, base, bad):
        errors = _rejected(model, {**base, "metadata": {"score": bad}})
        assert errors[0]["loc"] == ("metadata", "score")

    def test_non_finite_metadata_in_json_text_is_rejected(self):
        with pytest.raises(ValidationError):
            SkillCreate.model_validate_json(
                '{"name": "a-skill", "description": "d", "content": "c", "metadata": {"x": NaN}}',
            )

    @pytest.mark.parametrize("field", ["description", "content", "license", "compatibility", "source_repo"])
    def test_create_rejects_nul_in_text(self, field):
        errors = _rejected(SkillCreate, {**SKILL, field: f"a{NUL}b"})
        assert errors[0]["loc"] == (field,)
        assert errors[0]["type"] == "nul_character"

    @pytest.mark.parametrize("field", ["description", "content", "license", "compatibility"])
    def test_update_rejects_nul_in_text(self, field):
        errors = _rejected(SkillUpdate, {field: f"a{NUL}b"})
        assert errors[0]["loc"] == (field,)

    @pytest.mark.parametrize("payload,loc", [
        ({"tags": [f"a{NUL}b"]}, ("tags", 0)),
        ({"allowed_tools": ["Read", f"a{NUL}"]}, ("allowed_tools", 1)),
        ({"source_files": [f"p{NUL}"]}, ("source_files", 0)),
    ])
    def test_nul_inside_lists_is_rejected(self, payload, loc):
        assert _rejected(SkillCreate, {**SKILL, **payload})[0]["loc"] == loc
        assert _rejected(SkillUpdate, payload)[0]["loc"] == loc

    def test_response_model_still_reads_rows_stored_earlier(self):
        long_tag = "t" * (settings.SKILL_TAG_MAX_LENGTH + 50)
        row = {**SKILL, "content": f"a{NUL}b", "id": 1, "created_at": NOW, "updated_at": NOW}
        skill = Skill(**row, tags=[long_tag], metadata={"x": float("nan")})
        assert skill.tags == [long_tag]
        assert skill.content == f"a{NUL}b"

    def test_storable_values_are_unchanged(self):
        skill = SkillCreate(**SKILL, metadata={"score": 1.5, "t": ["a", 2]}, tags=["x", "y"])
        assert skill.metadata == {"score": 1.5, "t": ["a", 2]}
        assert skill.tags == ["x", "y"]


class TestSkillTagLength:
    """skills.tags carries a GIN index, so one oversized tag fails the whole INSERT."""

    def test_default_limit_is_well_below_the_index_key_limit(self):
        # 4 bytes per character in UTF-8, index key limit about 2700 bytes
        assert 0 < settings.SKILL_TAG_MAX_LENGTH * 4 < 2700

    def test_create_accepts_tag_at_the_limit_and_rejects_one_more(self):
        limit = settings.SKILL_TAG_MAX_LENGTH
        assert SkillCreate(**SKILL, tags=["t" * limit]).tags == ["t" * limit]
        errors = _rejected(SkillCreate, {**SKILL, "tags": ["ok", "t" * (limit + 1)]})
        assert errors[0]["loc"] == ("tags",)
        assert errors[0]["type"] == "tag_too_long"
        assert str(limit) in errors[0]["msg"]

    def test_update_accepts_tag_at_the_limit_and_rejects_one_more(self):
        limit = settings.SKILL_TAG_MAX_LENGTH
        assert SkillUpdate(tags=["t" * limit]).tags == ["t" * limit]
        assert _rejected(SkillUpdate, {"tags": ["t" * (limit + 1)]})[0]["type"] == "tag_too_long"

    def test_padding_does_not_count_towards_the_limit(self):
        limit = settings.SKILL_TAG_MAX_LENGTH
        assert SkillCreate(**SKILL, tags=["  " + "t" * limit + "  "]).tags == ["t" * limit]
        assert SkillUpdate(tags=[" " + "t" * limit + " "]).tags == ["t" * limit]

    def test_the_limit_is_configurable(self, monkeypatch):
        monkeypatch.setattr(settings, "SKILL_TAG_MAX_LENGTH", 5)
        assert SkillCreate(**SKILL, tags=["abcde"]).tags == ["abcde"]
        assert _rejected(SkillCreate, {**SKILL, "tags": ["abcdef"]})[0]["type"] == "tag_too_long"
        assert _rejected(SkillUpdate, {"tags": ["abcdef"]})[0]["type"] == "tag_too_long"

    def test_existing_count_limit_still_applies(self):
        too_many = [f"t{i}" for i in range(settings.SKILL_TAGS_MAX_COUNT + 1)]
        with pytest.raises(ValidationError):
            SkillCreate(**SKILL, tags=too_many)


class TestPlanningText:
    """Task, plan and criterion text columns are PostgreSQL text/varchar."""

    @pytest.mark.parametrize("model,payload,loc", [
        (PlanCreate, {"title": f"a{NUL}b", "project_id": 1}, ("title",)),
        (PlanCreate, {"title": "t", "project_id": 1, "goal": f"a{NUL}b"}, ("goal",)),
        (PlanCreate, {"title": "t", "project_id": 1, "context": f"a{NUL}b"}, ("context",)),
        (PlanCreate, {"title": "t", "project_id": 1, "source_files": [f"a{NUL}"]}, ("source_files", 0)),
        (PlanUpdate, {"title": f"a{NUL}b"}, ("title",)),
        (PlanUpdate, {"goal": f"a{NUL}b"}, ("goal",)),
        (PlanUpdate, {"context": f"a{NUL}b"}, ("context",)),
        (TaskCreate, {"title": f"a{NUL}b", "plan_id": 1}, ("title",)),
        (TaskCreate, {"title": "t", "plan_id": 1, "description": f"a{NUL}b"}, ("description",)),
        (TaskCreate, {"title": "t", "plan_id": 1, "assigned_agent": f"a{NUL}b"}, ("assigned_agent",)),
        (TaskCreate, {"title": "t", "plan_id": 1, "source_url": f"a{NUL}b"}, ("source_url",)),
        (TaskCreate, {"title": "t", "plan_id": 1, "criteria": [{"description": "ok"}, {"description": f"a{NUL}"}]},
         ("criteria", 1, "description")),
        (TaskUpdate, {"title": f"a{NUL}b"}, ("title",)),
        (TaskUpdate, {"description": f"a{NUL}b"}, ("description",)),
        (CriterionCreate, {"description": f"a{NUL}b"}, ("description",)),
        (CriterionUpdate, {"description": f"a{NUL}b"}, ("description",)),
    ])
    def test_nul_is_rejected(self, model, payload, loc):
        errors = _rejected(model, payload)
        assert errors[0]["loc"] == loc
        assert errors[0]["type"] == "nul_character"

    def test_storable_text_is_unchanged(self):
        text = "line one\nline two\ttab \U0001f600 éè \x01 control"
        assert PlanCreate(title="t", project_id=1, goal=text).goal == text
        assert TaskCreate(title="t", plan_id=1, description=text).description == text
        assert CriterionCreate(description=text).description == text

    def test_response_model_still_reads_rows_stored_earlier(self):
        plan = Plan(id=1, title="t", goal=f"a{NUL}b", project_id=1, status="draft",
                    user_id="00000000-0000-0000-0000-000000000001", created_at=NOW, updated_at=NOW)
        assert plan.goal == f"a{NUL}b"


class TestDocumentSizeBytes:
    """documents.size_bytes is a 32-bit INTEGER on PostgreSQL."""

    DOC = {"title": "t", "description": "d", "content": "c"}

    def test_create_accepts_the_largest_int32(self):
        assert DocumentCreate(**self.DOC, size_bytes=INT32_MAX).size_bytes == INT32_MAX

    def test_create_rejects_a_value_above_int32(self):
        errors = _rejected(DocumentCreate, {**self.DOC, "size_bytes": INT32_MAX + 1})
        assert errors[0]["loc"] == ("size_bytes",)
        assert errors[0]["type"] == "less_than_equal"

    def test_update_accepts_the_largest_int32(self):
        assert DocumentUpdate(size_bytes=INT32_MAX).size_bytes == INT32_MAX

    def test_update_rejects_a_value_above_int32(self):
        errors = _rejected(DocumentUpdate, {"size_bytes": 3_000_000_000})
        assert errors[0]["loc"] == ("size_bytes",)
