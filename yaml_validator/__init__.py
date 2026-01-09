"""
YAML Schema Validator

A multi-phase YAML schema validator for GroundX prompt/config files.

Usage:
    from yaml_validator import validate_yaml_schema
    
    result = validate_yaml_schema(yaml_text, profile="statement_only")
    if result.success:
        print("Valid!")
    else:
        for error in result.errors:
            print(error)
"""

from yaml_validator.validator import validate_yaml_schema, validate_yaml_file, quick_validate
from yaml_validator.models.validation_result import (
    ValidationResult,
    ValidationIssue,
    Severity,
    ErrorCodes,
)

__version__ = "0.1.0"
__all__ = [
    "validate_yaml_schema",
    "validate_yaml_file", 
    "quick_validate",
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "ErrorCodes",
]
