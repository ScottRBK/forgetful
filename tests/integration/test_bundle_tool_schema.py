"""Nested schemas compose without changing legacy tool parameter schemas."""
import copy

import pytest

from app.models.tool_registry_models import ToolCategory, ToolMetadata, ToolParameter


def tool(parameters):
    return ToolMetadata(name="schema", category=ToolCategory.SKILL, description="schema", parameters=parameters, returns="value")


def test_nested_definitions_hoist_and_merge():
    schema = {"$defs": {"Entry": {"type": "string"}}, "$ref": "#/$defs/Entry"}
    original = copy.deepcopy(schema)
    result = tool([ToolParameter(name=n, type="dict", description=n, json_schema=schema) for n in ("left", "right")])._generate_json_schema()
    assert result["$defs"] == schema["$defs"]
    assert result["properties"]["left"]["$ref"] == "#/$defs/Entry"
    assert schema == original


def test_conflicting_definition_rejected():
    parameters = [ToolParameter(name=n, type="dict", description=n, json_schema={"$defs": {"Entry": {"type": kind}}, "$ref": "#/$defs/Entry"})
                  for n, kind in (("left", "string"), ("right", "integer"))]
    with pytest.raises(ValueError, match="Conflicting JSON schema definition"):
        tool(parameters)._generate_json_schema()


def test_legacy_schemas_unchanged():
    # Every existing legacy type retains the precise old generated representation.
    for name, kind in (("str", "string"), ("int", "integer"), ("float", "number"), ("bool", "boolean"), ("dict", "object"), ("List[str]", "array"), ("Optional[int]", "integer")):
        assert tool([ToolParameter(name="value", type=name, description="value", required=True)])._generate_json_schema() == {
            "type": "object", "properties": {"value": {"description": "value", "type": kind}}, "required": ["value"]}
