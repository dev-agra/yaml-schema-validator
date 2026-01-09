"""
Core semantic validation rules.

These rules validate the semantic correctness of the YAML schema
after it has been successfully parsed and loaded into Pydantic models.
"""

from __future__ import annotations

from typing import List, Dict

from yaml_validator.models.validation_result import (
    ValidationIssue,
    Severity,
    ErrorCodes,
    create_error,
    create_warning,
)
from yaml_validator.models.schema_definitions import YAMLSchema
from yaml_validator.rules.rule_base import Rule, RuleRegistry
from yaml_validator.pipeline.syntax_parser import get_line_for_path


class GroupPromptInstructionsRule(Rule):
    """If Group.prompt is present, it must have non-empty instructions."""
    
    @property
    def id(self) -> str:
        return ErrorCodes.GROUP_PROMPT_NO_INSTRUCTIONS
    
    @property
    def description(self) -> str:
        return "If Group.prompt is present, it must have non-empty instructions"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        for group_name, group in model.items():
            if group.prompt is not None:
                if not group.prompt.instructions:
                    path = [group_name, "prompt", "instructions"]
                    line = get_line_for_path(line_map, path)
                    
                    issues.append(create_error(
                        code=self.id,
                        message=f"Group '{group_name}' has a prompt but missing 'instructions'",
                        path=path,
                        line=line,
                        suggestion="Add 'instructions: \"Your instructions here\"' to the prompt"
                    ))
        
        return issues


class GroupPromptIgnoredAttrsRule(Rule):
    """Warn if Group.prompt has attributes that are ignored for groups."""
    
    @property
    def id(self) -> str:
        return ErrorCodes.GROUP_PROMPT_IGNORED_ATTRS
    
    @property
    def description(self) -> str:
        return "Warn when Group.prompt has attributes that are ignored"
    
    @property
    def severity(self) -> Severity:
        return Severity.WARNING
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        for group_name, group in model.items():
            if group.prompt is not None:
                ignored_attrs = group.prompt.has_ignored_group_attrs()
                
                for attr in ignored_attrs:
                    path = [group_name, "prompt", attr]
                    line = get_line_for_path(line_map, path)
                    
                    issues.append(create_warning(
                        code=self.id,
                        message=f"Attribute '{attr}' is ignored for Group prompts",
                        path=path,
                        line=line,
                        suggestion=f"Remove '{attr}' from group prompt (only 'instructions' is used)"
                    ))
        
        return issues


class FieldPromptRequiredRule(Rule):
    """Every ExtractedField must have a prompt."""
    
    @property
    def id(self) -> str:
        return ErrorCodes.FIELD_NO_PROMPT
    
    @property
    def description(self) -> str:
        return "Every ExtractedField must have a prompt"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        for group_name, group in model.items():
            if group.fields:
                for field_name, field in group.fields.items():
                    if field.prompt is None:
                        path = [group_name, "fields", field_name, "prompt"]
                        line = get_line_for_path(line_map, [group_name, "fields", field_name])
                        
                        issues.append(create_error(
                            code=self.id,
                            message=f"Field '{field_name}' is missing 'prompt'",
                            path=path,
                            line=line,
                            suggestion="Add 'prompt:' with 'identifiers:' and 'type:'"
                        ))
        
        return issues


class FieldIdentifiersRequiredRule(Rule):
    """Field.prompt.identifiers must exist and have at least one item."""
    
    @property
    def id(self) -> str:
        return ErrorCodes.FIELD_NO_IDENTIFIERS
    
    @property
    def description(self) -> str:
        return "Field.prompt.identifiers must exist and have at least one item"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        for group_name, group in model.items():
            if group.fields:
                for field_name, field in group.fields.items():
                    if field.prompt is not None:
                        if field.prompt.identifiers is None:
                            path = [group_name, "fields", field_name, "prompt", "identifiers"]
                            line = get_line_for_path(line_map, path)
                            
                            issues.append(create_error(
                                code=self.id,
                                message=f"Field '{field_name}' is missing 'identifiers'",
                                path=path,
                                line=line,
                                suggestion="Add 'identifiers: [\"identifier1\", \"identifier2\"]'"
                            ))
                        elif len(field.prompt.identifiers) == 0:
                            path = [group_name, "fields", field_name, "prompt", "identifiers"]
                            line = get_line_for_path(line_map, path)
                            
                            issues.append(create_error(
                                code=ErrorCodes.FIELD_EMPTY_IDENTIFIERS,
                                message=f"Field '{field_name}' has empty 'identifiers' list",
                                path=path,
                                line=line,
                                suggestion="Add at least one identifier"
                            ))
        
        return issues


class FieldTypeRequiredRule(Rule):
    """Field.prompt.type must exist."""
    
    @property
    def id(self) -> str:
        return ErrorCodes.FIELD_NO_TYPE
    
    @property
    def description(self) -> str:
        return "Field.prompt.type must exist"
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        for group_name, group in model.items():
            if group.fields:
                for field_name, field in group.fields.items():
                    if field.prompt is not None:
                        if field.prompt.type is None:
                            path = [group_name, "fields", field_name, "prompt", "type"]
                            line = get_line_for_path(line_map, path)
                            
                            issues.append(create_error(
                                code=self.id,
                                message=f"Field '{field_name}' is missing 'type'",
                                path=path,
                                line=line,
                                suggestion="Add 'type: str' (or 'int', 'float', 'date', etc.)"
                            ))
        
        return issues


class FieldRequiredIgnoredRule(Rule):
    """Warn if field.prompt.required is set, as it's ignored."""
    
    @property
    def id(self) -> str:
        return ErrorCodes.FIELD_REQUIRED_IGNORED
    
    @property
    def description(self) -> str:
        return "Warn when field.prompt.required is set (it's ignored)"
    
    @property
    def severity(self) -> Severity:
        return Severity.WARNING
    
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        issues = []
        
        for group_name, group in model.items():
            if group.fields:
                for field_name, field in group.fields.items():
                    if field.prompt is not None and field.prompt.required is not None:
                        path = [group_name, "fields", field_name, "prompt", "required"]
                        line = get_line_for_path(line_map, path)
                        
                        issues.append(create_warning(
                            code=self.id,
                            message=f"Field '{field_name}' has 'required' set, but it's ignored",
                            path=path,
                            line=line,
                            suggestion="Remove 'required' - field extraction is always attempted"
                        ))
        
        return issues


# List of all core rule classes
CORE_RULES = [
    GroupPromptInstructionsRule,
    GroupPromptIgnoredAttrsRule,
    FieldPromptRequiredRule,
    FieldIdentifiersRequiredRule,
    FieldTypeRequiredRule,
    FieldRequiredIgnoredRule,
]


def register_core_rules(registry: RuleRegistry) -> None:
    """Register all core rules with the given registry."""
    for rule_class in CORE_RULES:
        registry.register_core(rule_class())


def get_core_rule_by_id(rule_id: str) -> Rule | None:
    """Get a core rule instance by its ID."""
    for rule_class in CORE_RULES:
        instance = rule_class()
        if instance.id == rule_id:
            return instance
    return None