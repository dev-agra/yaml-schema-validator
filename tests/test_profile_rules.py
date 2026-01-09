"""
Tests for profile-based validation.
"""

import pytest

from yaml_validator.validator import validate_yaml_schema
from yaml_validator.pipeline.syntax_parser import parse_yaml
from yaml_validator.pipeline.schema_loader import load_yaml_to_models
from yaml_validator.rules.rule_base import RuleRegistry
from yaml_validator.rules.profile_rules.statement_only import (
    TopLevelKeysRule,
    RequiredFieldsRule,
    register_statement_only_rules,
)
from yaml_validator.profiles.profile_loader import (
    profile_exists,
    get_available_profiles,
    load_profile_config,
)
from yaml_validator.models.validation_result import Severity, ErrorCodes
from yaml_validator.exceptions import ProfileNotFoundError


def load_and_validate(yaml_text, rule):
    """Helper to parse, load, and run a single rule."""
    parse_result = parse_yaml(yaml_text)
    assert parse_result.success, f"Parse failed: {parse_result.error}"
    
    model, errors = load_yaml_to_models(parse_result.data, parse_result.line_map)
    assert not errors, f"Load failed: {errors}"
    
    return rule.validate(model, parse_result.line_map)


class TestTopLevelKeysRule:
    """Tests for TopLevelKeysRule."""
    
    def test_valid_top_level_key(self, valid_statement_only_yaml):
        """No error when top-level key is 'statement'."""
        rule = TopLevelKeysRule(
            required_keys={"statement"},
            allowed_keys={"statement"}
        )
        issues = load_and_validate(valid_statement_only_yaml, rule)
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0
    
    def test_invalid_top_level_key(self, invalid_top_level_key_yaml):
        """Error when top-level key is not allowed."""
        rule = TopLevelKeysRule(
            required_keys={"statement"},
            allowed_keys={"statement"}
        )
        issues = load_and_validate(invalid_top_level_key_yaml, rule)
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) >= 1


class TestRequiredFieldsRule:
    """Tests for RequiredFieldsRule."""
    
    def test_all_required_fields_present(self, valid_statement_only_yaml):
        """No error when all required fields are present."""
        rule = RequiredFieldsRule(
            group_name="statement",
            required_fields={"meters", "charges"}
        )
        issues = load_and_validate(valid_statement_only_yaml, rule)
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0
    
    def test_missing_required_field(self, missing_required_fields_yaml):
        """Error when required field is missing."""
        rule = RequiredFieldsRule(
            group_name="statement",
            required_fields={"meters", "charges"}
        )
        issues = load_and_validate(missing_required_fields_yaml, rule)
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 2  # Both 'meters' and 'charges' missing


class TestProfileRegistration:
    """Tests for profile registration and management."""
    
    def test_profile_exists(self):
        """statement_only profile should exist."""
        assert profile_exists("statement_only")
    
    def test_nonexistent_profile(self):
        """Nonexistent profile should return False."""
        assert not profile_exists("nonexistent_profile")
    
    def test_get_available_profiles(self):
        """Should return list of available profiles."""
        profiles = get_available_profiles()
        
        assert isinstance(profiles, list)
        assert "statement_only" in profiles


class TestProfileIntegration:
    """Integration tests for profile validation."""
    
    def test_validate_with_profile(self, valid_statement_only_yaml):
        """Validation with profile should work."""
        result = validate_yaml_schema(
            valid_statement_only_yaml,
            profile="statement_only"
        )
        
        assert result.success
    
    def test_profile_rules_only_run_when_selected(self, invalid_top_level_key_yaml):
        """Profile rules should only run when profile is selected."""
        result_no_profile = validate_yaml_schema(invalid_top_level_key_yaml)
        result_with_profile = validate_yaml_schema(
            invalid_top_level_key_yaml,
            profile="statement_only"
        )
        
        assert result_no_profile.success
        assert not result_with_profile.success
    
    def test_invalid_profile_raises_error(self, valid_minimal_yaml):
        """Invalid profile name should raise error."""
        with pytest.raises(ProfileNotFoundError):
            validate_yaml_schema(
                valid_minimal_yaml,
                profile="nonexistent_profile"
            )