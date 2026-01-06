"""Validation rules for YAML schema validation."""

from .base import (
    Rule,
    RuleRegistry,
    get_global_registry,
    register_core_rule,
    register_profile_rule,
)

from .core_rules import (
    GroupPromptInstructionsRule,
    GroupPromptIgnoredAttrsRule,
    FieldPromptRequiredRule,
    FieldIdentifiersRequiredRule,
    FieldTypeRequiredRule,
    FieldRequiredIgnoredRule,
    register_core_rules,
    CORE_RULES,
)

from .profile_rules import (
    register_statement_only_rules,
)

__all__ = [
    # Base
    "Rule",
    "RuleRegistry",
    "get_global_registry",
    "register_core_rule",
    "register_profile_rule",
    
    # Core rules
    "GroupPromptInstructionsRule",
    "GroupPromptIgnoredAttrsRule",
    "FieldPromptRequiredRule",
    "FieldIdentifiersRequiredRule",
    "FieldTypeRequiredRule",
    "FieldRequiredIgnoredRule",
    "register_core_rules",
    "CORE_RULES",
    
    # Profile registration
    "register_statement_only_rules",
]