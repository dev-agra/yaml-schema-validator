"""
Tests for Pydantic model loading.
"""

import pytest

from yaml_validator.pipeline.syntax_parser import parse_yaml
from yaml_validator.pipeline.schema_loader import load_yaml_to_models, Group
from yaml_validator.models.schema_definitions import Prompt, ExtractedField


class TestLoadYAMLToModels:
    """Tests for load_yaml_to_models function."""
    
    def test_valid_structure_loads_successfully(self, valid_minimal_yaml):
        """Valid YAML should load into Pydantic models."""
        parse_result = parse_yaml(valid_minimal_yaml)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert errors == []
        assert model is not None
        assert "statement" in model
        assert isinstance(model["statement"], Group)
    
    def test_loaded_model_has_fields(self, valid_minimal_yaml):
        """Loaded model should have fields dict."""
        parse_result = parse_yaml(valid_minimal_yaml)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert errors == []
        statement = model["statement"]
        assert statement.fields is not None
        assert "meters" in statement.fields
        assert isinstance(statement.fields["meters"], ExtractedField)
    
    def test_field_has_prompt(self, valid_minimal_yaml):
        """Fields should have prompt objects."""
        parse_result = parse_yaml(valid_minimal_yaml)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        meters = model["statement"].fields["meters"]
        assert meters.prompt is not None
        assert isinstance(meters.prompt, Prompt)
        assert meters.prompt.identifiers == ["meter number"]
        assert meters.prompt.type == "str"
    
    def test_type_can_be_list(self):
        """Type field should accept list values like ['int', 'float']."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: ["int", "float"]
"""
        parse_result = parse_yaml(yaml_text)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert errors == []
        amount = model["statement"].fields["amount"]
        assert amount.prompt.type == ["int", "float"]


class TestLoadErrors:
    """Tests for error handling during loading."""
    
    def test_unknown_field_causes_error(self):
        """Unknown fields should cause validation errors."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
        unknown_field: "should error"
"""
        parse_result = parse_yaml(yaml_text)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert len(errors) > 0
        assert model is None
        assert any("unknown" in e.message.lower() for e in errors)
    
    def test_non_dict_group_causes_error(self):
        """Non-dict group value should cause error."""
        yaml_text = """
statement: "not a dict"
"""
        parse_result = parse_yaml(yaml_text)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert len(errors) > 0
        assert model is None
    
    def test_error_includes_path(self):
        """Errors should include the path to the problem."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
        bad_field: 123
"""
        parse_result = parse_yaml(yaml_text)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert len(errors) > 0
        error = errors[0]
        assert len(error.path) > 0
        assert "statement" in error.path


class TestOptionalFields:
    """Tests for optional field handling."""
    
    def test_group_prompt_is_optional(self, valid_no_group_prompt_yaml):
        """Group.prompt should be optional."""
        parse_result = parse_yaml(valid_no_group_prompt_yaml)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert errors == []
        assert model["statement"].prompt is None
    
    def test_description_is_optional(self, valid_minimal_yaml):
        """prompt.description should be optional."""
        parse_result = parse_yaml(valid_minimal_yaml)
        model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        assert errors == []
        meters = model["statement"].fields["meters"]
        assert meters.prompt.description is None


class TestPromptModel:
    """Tests for the Prompt Pydantic model."""
    
    def test_has_ignored_group_attrs_empty(self):
        """has_ignored_group_attrs should return empty list for minimal prompt."""
        prompt = Prompt(instructions="test")
        
        ignored = prompt.has_ignored_group_attrs()
        assert ignored == []
    
    def test_has_ignored_group_attrs_with_identifiers(self):
        """has_ignored_group_attrs should include identifiers if set."""
        prompt = Prompt(
            instructions="test",
            identifiers=["id1"]
        )
        
        ignored = prompt.has_ignored_group_attrs()
        assert "identifiers" in ignored
    
    def test_empty_identifiers_raises_error(self):
        """Empty identifiers list should raise validation error."""
        with pytest.raises(ValueError) as exc_info:
            Prompt(identifiers=[])
        
        assert "empty" in str(exc_info.value).lower()