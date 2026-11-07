"""Portable transport rejects malformed packages before any repository is called."""
import copy

import pytest
from pydantic import ValidationError

from app.config.settings import settings
from app.models.skill_bundle_models import SkillBundle
from tests.skill_bundle_cases import skill_bundle


@pytest.mark.parametrize("path", ["a", "a/b", "references/café.md"])
def test_portable_relative_paths(path):
    value = skill_bundle()
    value["resources"][0]["path"] = path
    assert SkillBundle.model_validate(value).resources[0].path == path


@pytest.mark.parametrize("path", ["cafe\u0301.md", "a\x00b", "../x", "x/../y", "x/", "x/aux.py", "x/y "])
def test_nonportable_path(path):
    value = skill_bundle()
    value["resources"][0]["path"] = path
    with pytest.raises(ValidationError):
        SkillBundle.model_validate(value)


@pytest.mark.parametrize("other_path", ["references/nested/refresh.md", "REFERENCES/NESTED/REFRESH.MD",
                                        "references/nested/refresh.md/child"])
def test_paths_cannot_collide(other_path):
    value = skill_bundle()
    other = copy.deepcopy(value["resources"][0])
    other["path"] = other_path
    value["resources"].append(other)
    with pytest.raises(ValidationError, match="collide"):
        SkillBundle.model_validate(value)


@pytest.mark.parametrize("data", ["", " ", "%%", "YQ==garbage", "Y Q=="])
def test_binary_requires_nonempty_strict_base64(data):
    value = skill_bundle()
    value["resources"][2]["data"] = data
    with pytest.raises(ValidationError):
        SkillBundle.model_validate(value)


def test_configured_count_and_decoded_size_limits(monkeypatch):
    value = skill_bundle()
    monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_RESOURCES", 2)
    with pytest.raises(ValidationError, match="MAX_RESOURCES"):
        SkillBundle.model_validate(value)
    monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_RESOURCES", 100)
    monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", 10)
    with pytest.raises(ValidationError, match="MAX_BYTES"):
        SkillBundle.model_validate(value)


@pytest.mark.parametrize("field", ["resource_id", "user_id", "project_id", "source_repo"])
def test_portable_entries_cannot_carry_instance_authority(field):
    value = skill_bundle()
    value["resources"][0][field] = 1
    with pytest.raises(ValidationError):
        SkillBundle.model_validate(value)


@pytest.mark.parametrize("value", ["\x00", "\ud800"])
def test_text_storage_constraints(value):
    package = skill_bundle()
    package["resources"][0]["content"] = value
    with pytest.raises(ValidationError):
        SkillBundle.model_validate(package)


@pytest.mark.parametrize("paths", [["docs", "docs.md", "docs/x.md"],
                                   ["a", "a-b", "a/c"], ["A", "a-b", "a/C"]])
def test_nonadjacent_parent_collision(paths):
    from app.models.skill_bundle_models import validate_bundle_paths

    with pytest.raises(ValueError, match="collide"):
        validate_bundle_paths(paths)


def test_exact_decoded_value_budget_and_per_file_padding(monkeypatch):
    from app.models.skill_bundle_models import _bundle_bytes, bundle_text_bytes

    value = skill_bundle()
    value["resources"] = [{"path": f"assets/{i}.bin", "kind": "file", "description": "x",
                           "mime_type": "x", "data": "YQ=="} for i in range(2)]
    canonical = SkillBundle.model_validate(value).model_dump()
    size = bundle_text_bytes(canonical["skill_md"]) + sum(_bundle_bytes(r) for r in canonical["resources"])
    # Independent fixed-shape arithmetic: schema field names contribute zero.
    expected = len(canonical["skill_md"].encode("utf-8")) + sum(
        len(r["path"].encode("utf-8")) + len(r["kind"]) + len(r["description"])
        + len(r["mime_type"]) + 1 for r in canonical["resources"]
    )
    assert size == expected
    monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", size)
    assert len(SkillBundle.model_validate(value).resources) == 2
    value["resources"][1]["data"] = "YWI="  # One more decoded byte, same base64 length.
    with pytest.raises(ValidationError, match="MAX_BYTES"):
        SkillBundle.model_validate(value)
