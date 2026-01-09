"""
Integration tests for the complete validation pipeline.
"""

import pytest

from yaml_validator.validator import (
    validate_yaml_schema,
    validate_yaml_file,
    quick_validate,
    ValidationResult,
    Severity,
)
from yaml_validator.models.validation_result import ErrorCodes


class TestValidateYAMLSchema:
    """Tests for the main validate_yaml_schema function."""
    
    def test_valid_yaml_returns_success(self, valid_minimal_yaml):
        """Valid YAML should return success."""
        result = validate_yaml_schema(valid_minimal_yaml)
        
        assert isinstance(result, ValidationResult)
        assert result.success is True
        assert len(result.errors) == 0
    
    def test_invalid_syntax_returns_failure(self, invalid_tab_yaml):
        """Invalid YAML syntax should return failure."""
        result = validate_yaml_schema(invalid_tab_yaml)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert result.errors[0].line is not None
    
    def test_missing_required_field_returns_failure(self, missing_type_yaml):
        """Missing required field should return failure."""
        result = validate_yaml_schema(missing_type_yaml)
        
        assert result.success is False
        assert any(e.code == ErrorCodes.FIELD_NO_TYPE for e in result.errors)
    
    def test_warnings_dont_cause_failure(self, field_required_set_yaml):
        """Warnings should not cause validation to fail."""
        result = validate_yaml_schema(field_required_set_yaml)
        
        assert result.success is True
        assert len(result.warnings) > 0


class TestValidationResultFormat:
    """Tests for ValidationResult output formats."""
    
    def test_to_dict(self, valid_minimal_yaml):
        """Result should convert to dict."""
        result = validate_yaml_schema(valid_minimal_yaml)
        
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "success" in d
        assert "errors" in d
        assert "warnings" in d
    
    def test_to_json(self, valid_minimal_yaml):
        """Result should convert to JSON."""
        result = validate_yaml_schema(valid_minimal_yaml)
        
        json_str = result.to_json()
        assert isinstance(json_str, str)
        assert '"success"' in json_str


class TestQuickValidate:
    """Tests for the quick_validate helper."""
    
    def test_quick_validate_valid(self, valid_minimal_yaml):
        """quick_validate should return True for valid YAML."""
        assert quick_validate(valid_minimal_yaml) is True
    
    def test_quick_validate_invalid(self, invalid_tab_yaml):
        """quick_validate should return False for invalid YAML."""
        assert quick_validate(invalid_tab_yaml) is False


class TestValidateYAMLFile:
    """Tests for file-based validation."""
    
    def test_validate_file(self, tmp_yaml_file, valid_minimal_yaml):
        """Should validate a file from path."""
        file_path = tmp_yaml_file(valid_minimal_yaml)
        
        result = validate_yaml_file(str(file_path))
        
        assert result.success is True


class TestComplexYAML:
    """Tests for complex YAML structures."""
    
    def test_multiline_instructions(self):
        """Should handle multi-line instructions."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
        instructions: |
          - Look for the amount
          - It may be labeled as "total"
          - Check near the bottom of the page
"""
        result = validate_yaml_schema(yaml_text)
        
        assert result.success is True
    
    def test_many_fields(self):
        """Should handle many fields."""
        yaml_text = """
statement:
  fields:
    field1:
      prompt:
        identifiers: ["f1"]
        type: str
    field2:
      prompt:
        identifiers: ["f2"]
        type: str
    field3:
      prompt:
        identifiers: ["f3"]
        type: int
    field4:
      prompt:
        identifiers: ["f4"]
        type: float
    field5:
      prompt:
        identifiers: ["f5"]
        type: ["int", "float"]
"""
        result = validate_yaml_schema(yaml_text)
        
        assert result.success is True


class TestErrorAccumulation:
    """Tests for error accumulation behavior."""
    
    def test_multiple_errors_collected(self):
        """Multiple errors should be collected."""
        yaml_text = """
statement:
  fields:
    field1:
      prompt:
        type: str
    field2:
      prompt:
        identifiers: ["f2"]
"""
        result = validate_yaml_schema(yaml_text)
        
        assert result.success is False
        assert len(result.errors) >= 2