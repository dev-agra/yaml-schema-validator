"""
YAML Schema Validator for GroundX prompt/config files.

This package provides comprehensive validation for YAML configuration files,
including:
- YAML syntax validation with line numbers
- Pydantic model validation with detailed error paths
- Core semantic rule validation
- Configurable profile-based validation

Usage:
    from yaml_validator import validate_yaml_schema
    
    result = validate_yaml_schema(yaml_text)
    
    if result.success:
        print("Valid!")
    else:
        for error in result.errors:
            print(error)
"""

__version__ = "0.1.0"

from ..validator import (
    validate_yaml_schema,
    validate_yaml_file,
    quick_validate,
)

from ..core.models import (
    ValidationResult,
    ValidationIssue,
    Severity,
    ErrorCodes,
)

from core.exceptions import (
    YAMLValidatorError,
    ProfileNotFoundError,
)

__all__ = [
    # Main API
    "validate_yaml_schema",
    "validate_yaml_file",
    "quick_validate",
    
    # Result types
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "ErrorCodes",
    
    # Exceptions
    "YAMLValidatorError",
    "ProfileNotFoundError",
    
    # Version
    "__version__",
]