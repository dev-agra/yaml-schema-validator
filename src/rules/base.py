"""
Rule engine base classes for YAML validation.

This module provides:
- Rule: Abstract base class for all validation rules
- RuleRegistry: Registry for managing and executing rules
- Decorators for easy rule registration
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type, Callable

from ..core.models import ValidationIssue, Severity
from ..loader.schema_models import YAMLSchema


class Rule(ABC):
    """
    Abstract base class for all validation rules.
    
    Each rule should:
    - Have a unique ID (e.g., "GXVAL101")
    - Have a human-readable description
    - Implement validate() to check the model and return issues
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique rule identifier.
        
        Convention:
        - Core rules: GXVAL100-199
        - Profile rules: GXVAL200-299
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule checks."""
        pass
    
    @property
    def category(self) -> str:
        """
        Rule category: 'core' or 'profile'.
        
        Core rules always run. Profile rules only run when that profile is selected.
        """
        return "core"
    
    @property
    def severity(self) -> Severity:
        """Default severity for issues from this rule."""
        return Severity.ERROR
    
    @abstractmethod
    def validate(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        """
        Run validation and return any issues found.
        
        Args:
            model: The loaded YAML schema (Dict[str, Group])
            line_map: Mapping of paths to line numbers
        
        Returns:
            List of ValidationIssue instances (can be empty)
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


class RuleRegistry:
    """
    Registry for managing and executing validation rules.
    
    Rules are organized into:
    - Core rules: Always run
    - Profile rules: Only run when that profile is selected
    """
    
    def __init__(self):
        self._core_rules: List[Rule] = []
        self._profile_rules: Dict[str, List[Rule]] = {}
    
    def register_core(self, rule: Rule) -> None:
        """Register a core rule that always runs."""
        self._core_rules.append(rule)
    
    def register_profile(self, profile_name: str, rule: Rule) -> None:
        """Register a rule for a specific profile."""
        if profile_name not in self._profile_rules:
            self._profile_rules[profile_name] = []
        self._profile_rules[profile_name].append(rule)
    
    def get_core_rules(self) -> List[Rule]:
        """Get all registered core rules."""
        return self._core_rules.copy()
    
    def get_profile_rules(self, profile_name: str) -> List[Rule]:
        """Get rules for a specific profile."""
        return self._profile_rules.get(profile_name, []).copy()
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profile names."""
        return list(self._profile_rules.keys())
    
    def has_profile(self, profile_name: str) -> bool:
        """Check if a profile exists."""
        return profile_name in self._profile_rules
    
    def run_core_rules(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        """
        Run all core rules and collect issues.
        
        Args:
            model: The loaded YAML schema
            line_map: Mapping of paths to line numbers
        
        Returns:
            List of all issues from core rules
        """
        issues = []
        for rule in self._core_rules:
            try:
                rule_issues = rule.validate(model, line_map)
                issues.extend(rule_issues)
            except Exception as e:
                # Don't let one rule break the whole validation
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="GXVAL000",
                    message=f"Rule {rule.id} failed: {str(e)}",
                    path=[]
                ))
        return issues
    
    def run_profile_rules(
        self,
        profile_name: str,
        model: YAMLSchema,
        line_map: Dict[str, int]
    ) -> List[ValidationIssue]:
        """
        Run rules for a specific profile.
        
        Args:
            profile_name: Name of the profile to run
            model: The loaded YAML schema
            line_map: Mapping of paths to line numbers
        
        Returns:
            List of all issues from profile rules
        """
        if profile_name not in self._profile_rules:
            return []
        
        issues = []
        for rule in self._profile_rules[profile_name]:
            try:
                rule_issues = rule.validate(model, line_map)
                issues.extend(rule_issues)
            except Exception as e:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="GXVAL000",
                    message=f"Profile rule {rule.id} failed: {str(e)}",
                    path=[]
                ))
        return issues
    
    def run_all(
        self,
        model: YAMLSchema,
        line_map: Dict[str, int],
        profile_name: Optional[str] = None
    ) -> List[ValidationIssue]:
        """
        Run core rules and optionally profile rules.
        
        Args:
            model: The loaded YAML schema
            line_map: Mapping of paths to line numbers
            profile_name: Optional profile to also run
        
        Returns:
            Combined list of all issues
        """
        issues = self.run_core_rules(model, line_map)
        
        if profile_name:
            issues.extend(self.run_profile_rules(profile_name, model, line_map))
        
        return issues
    
    def clear(self) -> None:
        """Clear all registered rules (useful for testing)."""
        self._core_rules = []
        self._profile_rules = {}
    
    def __repr__(self) -> str:
        core_count = len(self._core_rules)
        profile_count = sum(len(rules) for rules in self._profile_rules.values())
        return f"<RuleRegistry core={core_count} profile={profile_count}>"


# Global registry instance
_global_registry = RuleRegistry()


def get_global_registry() -> RuleRegistry:
    """Get the global rule registry."""
    return _global_registry


def register_core_rule(rule_class: Type[Rule]) -> Type[Rule]:
    """
    Decorator to register a rule class as a core rule.
    
    Usage:
        @register_core_rule
        class MyRule(Rule):
            ...
    """
    instance = rule_class()
    _global_registry.register_core(instance)
    return rule_class


def register_profile_rule(profile_name: str) -> Callable[[Type[Rule]], Type[Rule]]:
    """
    Decorator factory to register a rule class for a profile.
    
    Usage:
        @register_profile_rule("statement_only")
        class MyProfileRule(Rule):
            ...
    """
    def decorator(rule_class: Type[Rule]) -> Type[Rule]:
        instance = rule_class()
        _global_registry.register_profile(profile_name, instance)
        return rule_class
    return decorator