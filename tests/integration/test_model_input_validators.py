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

from app.models.file_models import File, FileCreate, FileUpdate


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


