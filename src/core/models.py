"""
Core data models for the YAML schema validator.
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
    INFO = "info"


class ErrorCodes:
    """
    Error code ranges:
    - 0xx: Parse/syntax errors (YAML level)
    - 1xx: Load/structure errors (Pydantic level)  
    - 2xx: Core semantic rule errors
    - 3xx: Core semantic rule warnings
    - 4xx: Profile rule errors
    - 5xx: Profile rule warnings
    """
    
    # Parse errors (0xx) - YAML syntax level
    YAML_PARSE_ERROR = "GXVAL001"
    YAML_INDENT_ERROR = "GXVAL002"
    YAML_TAB_ERROR = "GXVAL003"
    YAML_MAPPING_ERROR = "GXVAL004"
    YAML_EMPTY_ERROR = "GXVAL005"
    
    # Load/structure errors (1xx) - Pydantic level
    PYDANTIC_VALIDATION_ERROR = "GXVAL101"
    UNKNOWN_FIELD_ERROR = "GXVAL102"
    TYPE_ERROR = "GXVAL103"
    STRUCTURE_ERROR = "GXVAL104"
    
    # Core semantic rule errors (2xx)
    GROUP_PROMPT_NO_INSTRUCTIONS = "GXVAL201"
    FIELD_NO_PROMPT = "GXVAL202"
    FIELD_NO_IDENTIFIERS = "GXVAL203"
    FIELD_EMPTY_IDENTIFIERS = "GXVAL204"
    FIELD_NO_TYPE = "GXVAL205"
    
    # Core semantic rule warnings (3xx)
    GROUP_PROMPT_IGNORED_ATTRS = "GXVAL301"
    FIELD_REQUIRED_IGNORED = "GXVAL302"
    
    # Profile rule errors (4xx)
    PROFILE_INVALID_TOP_LEVEL_KEY = "GXVAL401"
    PROFILE_MISSING_REQUIRED_KEY = "GXVAL402"
    PROFILE_MISSING_REQUIRED_FIELD = "GXVAL403"
    PROFILE_INVALID_FIELDS_TYPE = "GXVAL404"
    
    # Profile rule warnings (5xx)
    PROFILE_EXTRA_FIELD = "GXVAL501"


# Mapping for error code descriptions (for --list-rules)
ERROR_CODE_DESCRIPTIONS = {
    "GXVAL001": "Generic YAML parse error",
    "GXVAL002": "YAML indentation error",
    "GXVAL003": "Tab character found (use spaces)",
    "GXVAL004": "Invalid YAML mapping syntax",
    "GXVAL005": "YAML file is empty",
    "GXVAL101": "Pydantic validation failed",
    "GXVAL102": "Unknown field not in schema",
    "GXVAL103": "Wrong type for field",
    "GXVAL104": "Invalid structure (expected dict)",
    "GXVAL201": "Group.prompt missing instructions",
    "GXVAL202": "Field missing prompt",
    "GXVAL203": "Field missing identifiers",
    "GXVAL204": "Field has empty identifiers list",
    "GXVAL205": "Field missing type",
    "GXVAL301": "Group.prompt has ignored attributes",
    "GXVAL302": "Field.prompt.required is ignored",
    "GXVAL401": "Invalid top-level key for profile",
    "GXVAL402": "Missing required top-level key",
    "GXVAL403": "Missing required field in group",
    "GXVAL404": "Fields must be a dictionary",
    "GXVAL501": "Extra field not in profile allowlist",
}


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: Severity
    code: str
    message: str
    path: List[str] = field(default_factory=list)
    line: Optional[int] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "suggestion": self.suggestion
        }
    
    def format_path(self) -> str:
        return ".".join(self.path) if self.path else "(root)"
    
    def __str__(self) -> str:
        line_info = f" (line {self.line})" if self.line else ""
        path_str = self.format_path()
        base = f"[{self.code}] {path_str}{line_info}: {self.message}"
        if self.suggestion:
            base += f"\n    → {self.suggestion}"
        return base


@dataclass
class ValidationResult:
    """Complete result of a validation run."""
    success: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    parse_time_ms: Optional[float] = None
    load_time_ms: Optional[float] = None
    rules_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "timing": {
                "parse_ms": self.parse_time_ms,
                "load_ms": self.load_time_ms,
                "rules_ms": self.rules_time_ms,
            }
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)


@dataclass
class ParseResult:
    """Result of YAML parsing phase."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    line_map: Dict[str, int] = field(default_factory=dict)
    error: Optional[ValidationIssue] = None


def create_error(
    code: str,
    message: str,
    path: Optional[List[str]] = None,
    line: Optional[int] = None,
    suggestion: Optional[str] = None
) -> ValidationIssue:
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
    return ValidationIssue(
        severity=Severity.WARNING,
        code=code,
        message=message,
        path=path or [],
        line=line,
        suggestion=suggestion
    )