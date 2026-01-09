"""
Pydantic model loader for YAML schema validation.

This module converts parsed YAML dictionaries into Pydantic models,
collecting any validation errors with proper paths.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any

from pydantic import ValidationError

from ..models import (
    ValidationIssue,
    ErrorCodes,
    create_error,
)
from ..models.schema_definitions import (
    Group,
    YAMLSchema,
)
from .syntax_parser import get_line_for_path


def _pydantic_error_to_path(error_loc: tuple) -> List[str]:
    """
    Convert Pydantic error location to our path format.
    
    Args:
        error_loc: Pydantic error location tuple, e.g., ('fields', 'meters', 'prompt')
    
    Returns:
        List of path components as strings
    """
    return [str(item) for item in error_loc]


def _format_pydantic_error(error: dict, group_name: str) -> Tuple[str, List[str]]:
    """
    Format a Pydantic error into a user-friendly message and path.
    
    Args:
        error: A single error dict from Pydantic's ValidationError.errors()
        group_name: The top-level group name for path context
    
    Returns:
        Tuple of (message, full_path)
    """
    error_type = error.get("type", "")
    msg = error.get("msg", "Validation error")
    loc = error.get("loc", ())
    
    # Build full path
    path = [group_name] + _pydantic_error_to_path(loc)
    
    # Customize messages for common errors
    if error_type == "extra_forbidden":
        field_name = loc[-1] if loc else "unknown"
        msg = f"Unknown field '{field_name}' is not allowed"
    elif error_type == "missing":
        field_name = loc[-1] if loc else "unknown"
        msg = f"Required field '{field_name}' is missing"
    elif error_type == "string_type":
        msg = "Expected a string value"
    elif error_type == "list_type":
        msg = "Expected a list"
    elif error_type == "dict_type":
        msg = "Expected a dictionary"
    
    return msg, path


def load_yaml_to_models(
    data: Dict[str, Any],
    line_map: Dict[str, int]
) -> Tuple[Optional[YAMLSchema], List[ValidationIssue]]:
    """
    Convert parsed YAML dictionary to Dict[str, Group].
    
    This function:
    1. Validates that top-level is a dictionary
    2. Loads each group into a Pydantic Group model
    3. Collects all validation errors with paths and line numbers
    
    Args:
        data: Parsed YAML as a plain dictionary
        line_map: Mapping of paths to line numbers
    
    Returns:
        Tuple of (loaded_model, list_of_errors)
        - If successful: (Dict[str, Group], [])
        - If failed: (None, [errors...])
    """
    errors: List[ValidationIssue] = []
    
    # Validate top-level structure
    if not isinstance(data, dict):
        errors.append(create_error(
            code=ErrorCodes.STRUCTURE_ERROR,
            message=f"Top-level must be a dictionary, got {type(data).__name__}",
            suggestion="YAML should start with group names like 'statement:'"
        ))
        return None, errors
    
    if not data:
        errors.append(create_error(
            code=ErrorCodes.STRUCTURE_ERROR,
            message="YAML contains no groups",
            suggestion="Add at least one group, e.g., 'statement:'"
        ))
        return None, errors
    
    # Try to load each group
    result: YAMLSchema = {}
    
    for group_name, group_data in data.items():
        # Validate group_name is a string
        if not isinstance(group_name, str):
            errors.append(create_error(
                code=ErrorCodes.STRUCTURE_ERROR,
                message=f"Group name must be a string, got {type(group_name).__name__}",
                path=[str(group_name)]
            ))
            continue
        
        # Validate group_data is a dict
        if not isinstance(group_data, dict):
            line = line_map.get(group_name)
            errors.append(create_error(
                code=ErrorCodes.STRUCTURE_ERROR,
                message=f"Group '{group_name}' must be a dictionary",
                path=[group_name],
                line=line,
                suggestion=f"Define '{group_name}' as a mapping with 'fields:' and optionally 'prompt:'"
            ))
            continue
        
        # Try to parse as Group model
        try:
            group = Group(**group_data)
            result[group_name] = group
        
        except ValidationError as e:
            # Convert Pydantic errors to our format
            for error in e.errors():
                msg, path = _format_pydantic_error(error, group_name)
                line = get_line_for_path(line_map, path)
                
                errors.append(create_error(
                    code=ErrorCodes.PYDANTIC_VALIDATION_ERROR,
                    message=msg,
                    path=path,
                    line=line
                ))
    
    # If there were errors, return None for model
    if errors:
        return None, errors
    
    return result, []


def validate_structure_only(data: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Quick structural validation without full Pydantic loading.
    
    Useful for fast pre-checks.
    
    Args:
        data: Parsed YAML dictionary
    
    Returns:
        List of structural validation issues
    """
    issues = []
    
    if not isinstance(data, dict):
        issues.append(create_error(
            code=ErrorCodes.STRUCTURE_ERROR,
            message="Top-level must be a dictionary"
        ))
        return issues
    
    for group_name, group_data in data.items():
        if not isinstance(group_data, dict):
            issues.append(create_error(
                code=ErrorCodes.STRUCTURE_ERROR,
                message=f"Group '{group_name}' must be a dictionary",
                path=[group_name]
            ))
            continue
        
        # Check for fields
        if 'fields' in group_data:
            fields = group_data['fields']
            if not isinstance(fields, dict):
                issues.append(create_error(
                    code=ErrorCodes.STRUCTURE_ERROR,
                    message=f"'{group_name}.fields' must be a dictionary",
                    path=[group_name, "fields"]
                ))
    
    return issues