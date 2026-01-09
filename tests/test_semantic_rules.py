"""
Tests for core semantic validation rules.
"""

import pytest

from yaml_validator.pipeline.syntax_parser import parse_yaml
from yaml_validator.pipeline.schema_loader import load_yaml_to_models
from yaml_validator.rules.rule_base import RuleRegistry
from yaml_validator.rules.semantic_rules import (
    GroupPromptInstructionsRule,
    GroupPromptIgnoredAttrsRule,
    FieldPromptRequiredRule,
    FieldIdentifiersRequiredRule,
    FieldTypeRequiredRule,
    FieldRequiredIgnoredRule,
    register_core_rules,
)
from yaml_validator.models.validation_result import Severity, ErrorCodes


def load_and_validate(yaml_text, rule):
    """Helper to parse, load, and run a single rule."""
    parse_result = parse_yaml(yaml_text)
    assert parse_result.success, f"Parse failed: {parse_result.error}"
    
    model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
    assert not errors, f"Load failed: {errors}"
    
    return rule.validate(model, parse_result.line_map)


class TestGroupPromptInstructionsRule:
    """Tests for GroupPromptInstructionsRule."""
    
    def test_no_error_when_group_has_no_prompt(self, valid_no_group_prompt_yaml):
        """No error when group doesn't have a prompt at all."""
        rule = GroupPromptInstructionsRule()
        issues = load_and_validate(valid_no_group_prompt_yaml, rule)
        
        assert len(issues) == 0
    
    def test_no_error_when_prompt_has_instructions(self, valid_full_yaml):
        """No error when group.prompt has instructions."""
        rule = GroupPromptInstructionsRule()
        issues = load_and_validate(valid_full_yaml, rule)
        
        assert len(issues) == 0
    
    def test_error_when_prompt_missing_instructions(self, group_prompt_no_instructions_yaml):
        """Error when group.prompt exists but has no instructions."""
        rule = GroupPromptInstructionsRule()
        issues = load_and_validate(group_prompt_no_instructions_yaml, rule)
        
        assert len(issues) == 1
        assert issues[0].severity == Severity.ERROR
        assert issues[0].code == ErrorCodes.GROUP_PROMPT_NO_INSTRUCTIONS


class TestFieldPromptRequiredRule:
    """Tests for FieldPromptRequiredRule."""
    
    def test_no_error_when_field_has_prompt(self, valid_minimal_yaml):
        """No error when field has a prompt."""
        rule = FieldPromptRequiredRule()
        issues = load_and_validate(valid_minimal_yaml, rule)
        
        assert len(issues) == 0
    
    def test_error_when_field_missing_prompt(self, missing_prompt_yaml):
        """Error when field is missing prompt."""
        rule = FieldPromptRequiredRule()
        issues = load_and_validate(missing_prompt_yaml, rule)
        
        assert len(issues) == 1
        assert issues[0].severity == Severity.ERROR
        assert issues[0].code == ErrorCodes.FIELD_NO_PROMPT


class TestFieldIdentifiersRequiredRule:
    """Tests for FieldIdentifiersRequiredRule."""
    
    def test_no_error_when_identifiers_present(self, valid_minimal_yaml):
        """No error when field.prompt has identifiers."""
        rule = FieldIdentifiersRequiredRule()
        issues = load_and_validate(valid_minimal_yaml, rule)
        
        assert len(issues) == 0
    
    def test_error_when_identifiers_missing(self, missing_identifiers_yaml):
        """Error when field.prompt is missing identifiers."""
        rule = FieldIdentifiersRequiredRule()
        issues = load_and_validate(missing_identifiers_yaml, rule)
        
        assert len(issues) == 1
        assert issues[0].severity == Severity.ERROR
        assert issues[0].code == ErrorCodes.FIELD_NO_IDENTIFIERS


class TestFieldTypeRequiredRule:
    """Tests for FieldTypeRequiredRule."""
    
    def test_no_error_when_type_present(self, valid_minimal_yaml):
        """No error when field.prompt has type."""
        rule = FieldTypeRequiredRule()
        issues = load_and_validate(valid_minimal_yaml, rule)
        
        assert len(issues) == 0
    
    def test_error_when_type_missing(self, missing_type_yaml):
        """Error when field.prompt is missing type."""
        rule = FieldTypeRequiredRule()
        issues = load_and_validate(missing_type_yaml, rule)
        
        assert len(issues) == 1
        assert issues[0].severity == Severity.ERROR
        assert issues[0].code == ErrorCodes.FIELD_NO_TYPE
    
    def test_type_as_list_is_valid(self):
        """Type as list should be valid."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: ["int", "float"]
"""
        rule = FieldTypeRequiredRule()
        issues = load_and_validate(yaml_text, rule)
        
        assert len(issues) == 0


class TestFieldRequiredIgnoredRule:
    """Tests for FieldRequiredIgnoredRule."""
    
    def test_no_warning_when_required_not_set(self, valid_minimal_yaml):
        """No warning when field.prompt.required is not set."""
        rule = FieldRequiredIgnoredRule()
        issues = load_and_validate(valid_minimal_yaml, rule)
        
        assert len(issues) == 0
    
    def test_warning_when_required_is_set(self, field_required_set_yaml):
        """Warning when field.prompt.required is set."""
        rule = FieldRequiredIgnoredRule()
        issues = load_and_validate(field_required_set_yaml, rule)
        
        assert len(issues) == 1
        assert issues[0].severity == Severity.WARNING
        assert issues[0].code == ErrorCodes.FIELD_REQUIRED_IGNORED


class TestRuleRegistry:
    """Tests for RuleRegistry functionality."""
    
    def test_register_core_rules(self):
        """Should register all core rules."""
        registry = RuleRegistry()
        register_core_rules(registry)
        
        rules = registry.get_core_rules()
        assert len(rules) > 0
    
    def test_run_core_rules(self, valid_minimal_yaml):
        """Should run all core rules and return issues."""
        registry = RuleRegistry()
        register_core_rules(registry)
        
        parse_result = parse_yaml(valid_minimal_yaml)
        model, _ = load_yaml_to_models(parse_result.data, parse_result.line_map)
        
        issues = registry.run_core_rules(model, parse_result.line_map)
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0