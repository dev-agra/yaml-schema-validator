"""
Core data models for the YAML schema validator.

This module contains the fundamental data structures used throughout
the validation pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict


class Severity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"


class ErrorCodes:
    """
    Constants for validation error codes.
    
    Ranges:
    - 001-099: Parse/load errors
    - 100-199: Core semantic rule errors/warnings
    - 200-299: Profile rule errors/warnings
    """
    
    # Parse errors (001-009)
    YAML_PARSE_ERROR = "GXVAL001"
    YAML_INDENT_ERROR = "GXVAL002"
    YAML_TAB_ERROR = "GXVAL003"
    YAML_MAPPING_ERROR = "GXVAL004"
    
    # Pydantic/Load errors (010-099)
    PYDANTIC_VALIDATION_ERROR = "GXVAL010"
    UNKNOWN_FIELD_ERROR = "GXVAL011"
    TYPE_ERROR = "GXVAL012"
    STRUCTURE_ERROR = "GXVAL013"
    
    # Core semantic rules - Errors (100-149)
    GROUP_PROMPT_NO_INSTRUCTIONS = "GXVAL101"
    FIELD_NO_PROMPT = "GXVAL103"
    FIELD_NO_IDENTIFIERS = "GXVAL104"
    FIELD_NO_TYPE = "GXVAL105"
    FIELD_EMPTY_IDENTIFIERS = "GXVAL107"
    
    # Core semantic rules - Warnings (150-199)
    GROUP_PROMPT_IGNORED_ATTRS = "GXVAL102"
    FIELD_REQUIRED_IGNORED = "GXVAL106"
    UNKNOWN_TYPE_VALUE = "GXVAL108"
    
    # Profile rules - Errors (200-249)
    PROFILE_INVALID_TOP_LEVEL_KEY = "GXVAL201"
    PROFILE_MISSING_REQUIRED_KEY = "GXVAL202"
    PROFILE_MISSING_REQUIRED_FIELD = "GXVAL203"
    PROFILE_INVALID_FIELDS_TYPE = "GXVAL204"
    
    # Profile rules - Warnings (250-299)
    PROFILE_EXTRA_FIELD = "GXVAL250"


@dataclass
class ValidationIssue:
    """
    Represents a single validation issue (error or warning).
    
    Attributes:
        severity: Whether this is an error or warning
        code: Stable error code (e.g., "GXVAL001")
        message: Human-readable description of the issue
        path: Location in the YAML structure (e.g., ["statement", "fields", "meters"])
        line: Line number where the issue occurs (if available)
        suggestion: Optional fix suggestion
    """
    severity: Severity
    code: str
    message: str
    path: List[str] = field(default_factory=list)
    line: Optional[int] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "suggestion": self.suggestion
        }
    
    def format_path(self) -> str:
        """Format path as dot-notation string."""
        return ".".join(self.path) if self.path else "(root)"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        line_info = f" (line {self.line})" if self.line else ""
        path_str = self.format_path()
        base = f"[{self.code}] {path_str}{line_info}: {self.message}"
        if self.suggestion:
            base += f"\n    → Suggestion: {self.suggestion}"
        return base


@dataclass
class ValidationResult:
    """
    Complete result of a validation run.
    
    Attributes:
        success: True if no errors (warnings are OK)
        errors: List of error-level issues
        warnings: List of warning-level issues
    """
    success: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return len(self.warnings)
    
    @property
    def total_issues(self) -> int:
        """Total number of issues (errors + warnings)."""
        return self.error_count + self.warning_count
    
    def __str__(self) -> str:
        """Human-readable summary."""
        status = "✅ PASSED" if self.success else "❌ FAILED"
        return f"{status} - {self.error_count} error(s), {self.warning_count} warning(s)"


@dataclass
class ParseResult:
    """
    Result of YAML parsing phase.
    
    Attributes:
        success: True if parsing succeeded
        data: Parsed YAML as dictionary (if successful)
        line_map: Mapping of key paths to line numbers
        error: ValidationIssue if parsing failed
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    line_map: Dict[str, int] = field(default_factory=dict)
    error: Optional[ValidationIssue] = None


# ============================================================================
# Factory Functions
# ============================================================================

def create_error(
    code: str,
    message: str,
    path: Optional[List[str]] = None,
    line: Optional[int] = None,
    suggestion: Optional[str] = None
) -> ValidationIssue:
    """Create an error-level validation issue."""
    return ValidationIssue(
        severity=Severity.ERROR,
        code=code,
        message=message,
        path=path or [],
        line=line,
        suggestion=suggestion
    )


def create_warning(
    code: str,
    message: str,
    path: Optional[List[str]] = None,
    line: Optional[int] = None,
    suggestion: Optional[str] = None
) -> ValidationIssue:
    """Create a warning-level validation issue."""
    return ValidationIssue(
        severity=Severity.WARNING,
        code=code,
        message=message,
        path=path or [],
        line=line,
        suggestion=suggestion
    )