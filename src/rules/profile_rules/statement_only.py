"""
Profile rules for the 'statement_only' validation profile.

This profile enforces:
1. Only 'statement' is allowed at the top level
2. statement.fields must be a dict of ExtractedFields
3. Required fields: meters, charges (configurable)
"""

from __future__ import annotations

from typing import List, Dict, Set

from ...core.models import (
    ValidationIssue,
    Severity,
    ErrorCodes,
    create_error,
    create_warning,
)
from ...loader.schema_models import YAMLSchema
from ..base import Rule, RuleRegistry
from ...parser.yaml_parser import get_line_for_path


class TopLevelKeysRule(Rule):
    """
    Validates that only allowed keys exist at the top level.
    
    For statement_only profile:
    - Required: ['statement']
    - Allowed: ['statement']
    """
    
    def __init__(
        self,
        required_keys: Set[str] = None,
        allowed_keys: Set[str] = None
    ):
        self._required_keys = required_keys or {"statement"}
        self._allowed_keys = allowed_keys or {"statement"}
    
    @property
    def id(self) -> str:
        return ErrorCodes.PROFILE_INVALID_TOP_LEVEL_KEY
    
    @property
    def description(self) -> str:
        return f"Only these top-level keys allowed: {self._allowed_keys}"
    
    @property
    def category(self) -> str:
        return "profile"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        present_keys = set(model.keys())
        
        # Check for required keys
        missing = self._required_keys - present_keys
        for key in missing:
            issues.append(create_error(
                code=ErrorCodes.PROFILE_MISSING_REQUIRED_KEY,
                message=f"Required top-level key '{key}' is missing",
                path=[],
                suggestion=f"Add '{key}:' at the top level"
            ))
        
        # Check for disallowed keys
        extra = present_keys - self._allowed_keys
        for key in extra:
            line = get_line_for_path(line_map, [key])
            issues.append(create_error(
                code=self.id,
                message=f"Top-level key '{key}' is not allowed",
                path=[key],
                line=line,
                suggestion=f"Remove '{key}' - only {self._allowed_keys} allowed"
            ))
        
        return issues


class RequiredFieldsRule(Rule):
    """
    Validates that required fields exist within a group.
    """
    
    def __init__(
        self,
        group_name: str = "statement",
        required_fields: Set[str] = None
    ):
        self._group_name = group_name
        self._required_fields = required_fields or {"meters", "charges"}
    
    @property
    def id(self) -> str:
        return ErrorCodes.PROFILE_MISSING_REQUIRED_FIELD
    
    @property
    def description(self) -> str:
        return f"Group '{self._group_name}' must have fields: {self._required_fields}"
    
    @property
    def category(self) -> str:
        return "profile"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        group = model.get(self._group_name)
        if group is None:
            # Another rule handles missing group
            return issues
        
        if group.fields is None:
            issues.append(create_error(
                code=self.id,
                message=f"Group '{self._group_name}' has no fields",
                path=[self._group_name, "fields"],
                suggestion="Add 'fields:' section with required fields"
            ))
            return issues
        
        present_fields = set(group.fields.keys())
        missing = self._required_fields - present_fields
        
        for field in sorted(missing):
            line = get_line_for_path(line_map, [self._group_name, "fields"])
            issues.append(create_error(
                code=self.id,
                message=f"Required field '{field}' is missing from {self._group_name}.fields",
                path=[self._group_name, "fields", field],
                line=line,
                suggestion=f"Add '{field}:' with prompt containing identifiers and type"
            ))
        
        return issues


class FieldsDictTypeRule(Rule):
    """
    Validates that fields is a dictionary (not a list or other type).
    
    This is usually caught by Pydantic, but we include it for completeness.
    """
    
    def __init__(self, group_name: str = "statement"):
        self._group_name = group_name
    
    @property
    def id(self) -> str:
        return ErrorCodes.PROFILE_INVALID_FIELDS_TYPE
    
    @property
    def description(self) -> str:
        return f"{self._group_name}.fields must be a dictionary"
    
    @property
    def category(self) -> str:
        return "profile"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        group = model.get(self._group_name)
        if group is None:
            return issues
        
        # If we got here with a valid model, fields is already a dict
        if group.fields is not None and not isinstance(group.fields, dict):
            issues.append(create_error(
                code=self.id,
                message=f"{self._group_name}.fields must be a dictionary",
                path=[self._group_name, "fields"],
                suggestion="Use field_name: as keys, not a list"
            ))
        
        return issues


# ============================================================================
# Profile Configuration
# ============================================================================

# Default configuration for statement_only profile
STATEMENT_ONLY_CONFIG = {
    "required_top_level_keys": {"statement"},
    "allowed_top_level_keys": {"statement"},
    "required_fields": {"meters", "charges"},
}


def register_statement_only_rules(
    registry: RuleRegistry,
    config: Dict = None
) -> None:
    """
    Register rules for the 'statement_only' profile.
    
    Args:
        registry: The RuleRegistry to register rules with
        config: Optional configuration override
    """
    cfg = {**STATEMENT_ONLY_CONFIG, **(config or {})}
    
    registry.register_profile("statement_only", TopLevelKeysRule(
        required_keys=cfg["required_top_level_keys"],
        allowed_keys=cfg["allowed_top_level_keys"]
    ))
    
    registry.register_profile("statement_only", RequiredFieldsRule(
        group_name="statement",
        required_fields=cfg["required_fields"]
    ))
    
    registry.register_profile("statement_only", FieldsDictTypeRule(
        group_name="statement"
    ))


def get_profile_rules(profile_name: str) -> List[Rule]:
    """
    Get rule instances for a profile.
    
    Args:
        profile_name: Name of the profile
    
    Returns:
        List of Rule instances
    """
    if profile_name == "statement_only":
        return [
            TopLevelKeysRule(),
            RequiredFieldsRule(),
            FieldsDictTypeRule(),
        ]
    
    return []