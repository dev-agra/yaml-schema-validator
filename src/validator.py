"""
Main validation orchestrator.

This module provides the main entry point for YAML schema validation,
coordinating the validation pipeline:
1. Parse YAML
2. Load into Pydantic models
3. Run core semantic rules
4. Run profile rules (optional)
"""

from __future__ import annotations

from typing import Optional, List

from .core.models import (
    ValidationResult,
    ValidationIssue,
    Severity,
)
from .core.exceptions import ProfileNotFoundError
from .parser import parse_yaml
from .loader import load_yaml_to_models
from .rules.base import RuleRegistry
from .rules.core_rules import register_core_rules
from .profiles import profile_exists, register_profile


def validate_yaml_schema(
    yaml_text: str,
    profile: Optional[str] = None,
    fail_fast: bool = False
) -> ValidationResult:
    """
    Validate a YAML schema string.
    
    This is the main entry point for validation. It runs the full
    validation pipeline:
    
    1. Parse YAML (fail fast on syntax errors)
    2. Load into Pydantic models (fail fast on structure errors)
    3. Run core semantic rules (collect all issues)
    4. Run profile rules if specified (collect all issues)
    
    Args:
        yaml_text: The YAML content as a string
        profile: Optional profile name (e.g., "statement_only")
        fail_fast: If True, stop at first error in each phase
    
    Returns:
        ValidationResult with success status, errors, and warnings
    
    Raises:
        ProfileNotFoundError: If the specified profile doesn't exist
    """
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []
    
    # Validate profile exists if specified
    if profile and not profile_exists(profile):
        raise ProfileNotFoundError(profile)
    
    # =========================================================================
    # Phase 1: Parse YAML
    # =========================================================================
    parse_result = parse_yaml(yaml_text)
    
    if not parse_result.success:
        return ValidationResult(
            success=False,
            errors=[parse_result.error],
            warnings=[]
        )
    
    # =========================================================================
    # Phase 2: Load into Pydantic models
    # =========================================================================
    model, load_errors = load_yaml_to_models(
        parse_result.data,
        parse_result.line_map
    )
    
    if load_errors:
        return ValidationResult(
            success=False,
            errors=load_errors,
            warnings=[]
        )
    
    # =========================================================================
    # Phase 3: Core semantic rules
    # =========================================================================
    registry = RuleRegistry()
    register_core_rules(registry)
    
    # Register profile if specified
    if profile:
        register_profile(registry, profile)
    
    # Run core rules
    core_issues = registry.run_core_rules(model, parse_result.line_map)
    
    for issue in core_issues:
        if issue.severity == Severity.ERROR:
            errors.append(issue)
        else:
            warnings.append(issue)
    
    # If fail_fast and we have errors, stop here
    if fail_fast and errors:
        return ValidationResult(
            success=False,
            errors=errors,
            warnings=warnings
        )
    
    # =========================================================================
    # Phase 4: Profile rules (if specified)
    # =========================================================================
    if profile:
        profile_issues = registry.run_profile_rules(
            profile,
            model,
            parse_result.line_map
        )
        
        for issue in profile_issues:
            if issue.severity == Severity.ERROR:
                errors.append(issue)
            else:
                warnings.append(issue)
    
    # =========================================================================
    # Build result
    # =========================================================================
    return ValidationResult(
        success=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_yaml_file(
    file_path: str,
    profile: Optional[str] = None
) -> ValidationResult:
    """
    Validate a YAML file.
    
    Convenience function that reads a file and validates it.
    
    Args:
        file_path: Path to the YAML file
        profile: Optional profile name
    
    Returns:
        ValidationResult
    """
    with open(file_path, 'r') as f:
        yaml_text = f.read()
    
    return validate_yaml_schema(yaml_text, profile=profile)


def quick_validate(yaml_text: str) -> bool:
    """
    Quick validation check - returns True if valid, False otherwise.
    
    Use this for simple pass/fail checks without detailed errors.
    
    Args:
        yaml_text: The YAML content
    
    Returns:
        True if valid (no errors), False otherwise
    """
    result = validate_yaml_schema(yaml_text)
    return result.success