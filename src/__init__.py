"""YAML Schema Validator package."""

__version__ = "0.1.0"

from src.validator import (
    validate_yaml_schema,
    validate_yaml_file,
    quick_validate,
)

from src.core.models import (
    ValidationResult,
    ValidationIssue,
    Severity,
    ErrorCodes,
)

from src.core.exceptions import (
    YAMLValidatorError,
    ProfileNotFoundError,
)

__all__ = [
    "validate_yaml_schema",
    "validate_yaml_file", 
    "quick_validate",
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "ErrorCodes",
    "YAMLValidatorError",
    "ProfileNotFoundError",
    "__version__",
]