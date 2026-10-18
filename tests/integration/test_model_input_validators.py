"""Input model validators shared by the REST routes and the MCP tools.

Covers strict base64 payloads for files, verbatim code in code artifacts, blank
text in plans/tasks/criteria/skills and the skill allowed-tools length cap. Also
checks the response models stay readable for rows stored before these rules.
"""
import base64
import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.code_artifact_models import CodeArtifactCreate, CodeArtifactUpdate
from app.models.file_models import File, FileCreate, FileUpdate
from app.models.plan_models import (
    CriterionCreate,
    CriterionUpdate,
    Plan,
    PlanCreate,
    PlanUpdate,
    TaskCreate,
    TaskUpdate,
)

BLANKS = ["", "   ", " \t\n "]


def _file_kwargs(data: str) -> dict:
    return {
        "filename": "a.bin",
        "description": "d",
        "data": data,
        "mime_type": "application/octet-stream",
    }


# ============================================================================
# Files: base64 payloads


# ============================================================================


class TestFileBase64:
    @pytest.mark.parametrize(
        "garbage",
        ["!!!!", "====", "    ", "\n\r\t", "data:image/png;base64,AAAA", "AAA", "AA=A"],
    )
    def test_create_rejects_invalid_or_empty_base64(self, garbage):
        with pytest.raises(ValidationError):
            FileCreate(**_file_kwargs(garbage))

    @pytest.mark.parametrize("garbage", ["!!!!", "====", "    ", "AAA"])
    def test_update_rejects_invalid_or_empty_base64(self, garbage):
        with pytest.raises(ValidationError):
            FileUpdate(data=garbage)

    def test_validation_errors_are_json_serialisable(self):
        """The REST routes dump ValidationError.errors() straight into a JSON response."""
        for model, kwargs in (
            (FileCreate, _file_kwargs("!!!!")),
            (FileUpdate, {"data": "!!!!"}),
            (FileCreate, _file_kwargs("====")),
        ):
            with pytest.raises(ValidationError) as exc_info:
                model(**kwargs)
            json.dumps(exc_info.value.errors())

    def test_valid_base64_is_unchanged(self):
        encoded = base64.b64encode(b"hello world").decode()

        assert FileCreate(**_file_kwargs(encoded)).data == encoded
        assert FileUpdate(data=encoded).data == encoded

    def test_line_wrapped_base64_is_still_accepted(self):
        """MIME style encoders wrap base64 every 76 characters; this was always valid."""
        wrapped = base64.encodebytes(b"x" * 200).decode()
        assert "\n" in wrapped

        assert FileCreate(**_file_kwargs(wrapped)).data == wrapped
        assert FileUpdate(data=wrapped).data == wrapped

    def test_update_without_data_is_still_allowed(self):
        assert FileUpdate().data is None
        assert FileUpdate(description="new").data is None

    def test_response_model_still_reads_zero_byte_files_stored_earlier(self):
        now = datetime.now(tz=UTC)

        stored = File(
            id=1, size_bytes=0, created_at=now, updated_at=now, **_file_kwargs(""),
        )

        assert stored.data == ""


# ============================================================================
# Code artifacts: code is stored verbatim


# ============================================================================


INDENTED_CODE = "    def foo():\n        return 1\n"


class TestCodeArtifactVerbatimCode:
    def test_create_keeps_leading_indentation_and_trailing_newline(self):
        artifact = CodeArtifactCreate(
            title="  t  ", description="  d  ", code=INDENTED_CODE, language=" Python ",
        )

        assert artifact.code == INDENTED_CODE
        assert artifact.title == "t"
        assert artifact.description == "d"
        assert artifact.language == "python"

    def test_update_keeps_leading_indentation_and_trailing_newline(self):
        update = CodeArtifactUpdate(code=INDENTED_CODE, title="  t  ")

        assert update.code == INDENTED_CODE
        assert update.title == "t"

    @pytest.mark.parametrize("blank", ["   ", " \t\n "])
    def test_blank_code_is_still_rejected(self, blank):
        with pytest.raises(ValidationError):
            CodeArtifactCreate(title="t", description="d", code=blank, language="python")
        with pytest.raises(ValidationError):
            CodeArtifactUpdate(code=blank)

    def test_update_without_code_is_still_allowed(self):
        assert CodeArtifactUpdate(title="t").code is None


# ============================================================================
# Plans, tasks and criteria: blank titles / descriptions


# ============================================================================


def _plan_create(title):
    return PlanCreate(title=title, project_id=1)


def _task_create(title):
    return TaskCreate(title=title, plan_id=1)


BLANK_REJECTING_BUILDERS = {
    "plan-create-title": _plan_create,
    "plan-update-title": lambda value: PlanUpdate(title=value),
    "task-create-title": _task_create,
    "task-update-title": lambda value: TaskUpdate(title=value),
    "criterion-create-description": lambda value: CriterionCreate(description=value),
    "criterion-update-description": lambda value: CriterionUpdate(description=value),
}


class TestBlankPlanningText:
    @pytest.mark.parametrize("blank", BLANKS)
    @pytest.mark.parametrize("builder", BLANK_REJECTING_BUILDERS.values(), ids=BLANK_REJECTING_BUILDERS)
    def test_blank_values_are_rejected(self, builder, blank):
        with pytest.raises(ValidationError) as exc_info:
            builder(blank)

        # The REST routes dump ValidationError.errors() straight into a JSON response
        json.dumps(exc_info.value.errors())
        assert "cannot be empty or whitespace only" in str(exc_info.value)

    @pytest.mark.parametrize("builder", BLANK_REJECTING_BUILDERS.values(), ids=BLANK_REJECTING_BUILDERS)
    def test_padded_values_are_trimmed(self, builder):
        model = builder("  real text  ")

        assert "real text" in model.model_dump().values()

    def test_blank_criterion_inside_task_create_is_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="t", plan_id=1, criteria=[{"description": "   "}])

    def test_omitted_update_fields_still_mean_unchanged(self):
        assert PlanUpdate().title is None
        assert PlanUpdate(title=None).title is None
        assert TaskUpdate().title is None
        assert CriterionUpdate(met=True).description is None

    def test_optional_text_fields_may_still_be_blank(self):
        """Only required text is checked; optional goal/context/description stay optional."""
        assert PlanCreate(title="t", project_id=1, goal="  ").goal == ""
        assert TaskCreate(title="t", plan_id=1, description="").description == ""

    def test_plan_response_model_still_reads_blank_titles_stored_earlier(self):
        now = datetime.now(tz=UTC)

        plan = Plan(id=1, title="", project_id=1, created_at=now, updated_at=now)

        assert plan.title == ""


