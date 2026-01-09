"""
YAML Parser with line number preservation.

This module provides YAML parsing functionality that:
1. Pre-validates for common issues (tabs, basic indent problems)
2. Parses YAML using ruamel.yaml for line number preservation
3. Builds a line map for error reporting
"""

from __future__ import annotations

from io import StringIO
from typing import Dict, Any, Optional, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError

from ..models import (
    ParseResult,
    ValidationIssue,
    ErrorCodes,
    create_error,
)


def _check_for_tabs(yaml_text: str) -> Optional[ValidationIssue]:
    """
    Pre-check for tab characters in the YAML.
    
    Returns a ValidationIssue if tabs are found, None otherwise.
    """
    lines = yaml_text.splitlines()
    for i, line in enumerate(lines, start=1):
        if '\t' in line:
            col = line.index('\t') + 1
            return create_error(
                code=ErrorCodes.YAML_TAB_ERROR,
                message="Tab character found. Use spaces for indentation.",
                path=[],
                line=i,
                suggestion=f"Replace tab at column {col} with spaces"
            )
    return None


def _build_line_map(data: Any, prefix: str = "") -> Dict[str, int]:
    """
    Recursively build a mapping of YAML paths to line numbers.
    
    Args:
        data: Parsed YAML data (CommentedMap, CommentedSeq, or scalar)
        prefix: Current path prefix (e.g., "statement.fields")
    
    Returns:
        Dict mapping paths like "statement.fields.meters" to line numbers
    """
    line_map = {}
    
    if isinstance(data, CommentedMap):
        for key in data:
            path = f"{prefix}.{key}" if prefix else key
            
            # Get line number for this key
            if hasattr(data, 'lc') and data.lc.key(key):
                line_num = data.lc.key(key)[0] + 1  # 0-indexed to 1-indexed
                line_map[path] = line_num
            
            # Recurse into value
            value = data[key]
            if isinstance(value, (CommentedMap, CommentedSeq)):
                line_map.update(_build_line_map(value, path))
    
    elif isinstance(data, CommentedSeq):
        for i, item in enumerate(data):
            path = f"{prefix}[{i}]"
            if isinstance(item, (CommentedMap, CommentedSeq)):
                line_map.update(_build_line_map(item, path))
    
    return line_map


def _convert_to_plain_dict(data: Any) -> Any:
    """
    Convert ruamel.yaml CommentedMap/Seq to plain Python dict/list.
    
    This makes the data easier to work with downstream.
    """
    if isinstance(data, CommentedMap):
        return {k: _convert_to_plain_dict(v) for k, v in data.items()}
    elif isinstance(data, CommentedSeq):
        return [_convert_to_plain_dict(item) for item in data]
    else:
        return data


def _extract_yaml_error_info(error: YAMLError) -> Tuple[int, str]:
    """
    Extract line number and message from a YAML error.
    
    Returns:
        Tuple of (line_number, error_message)
    """
    line = None
    message = str(error)
    
    # Try to get line from problem_mark
    if hasattr(error, 'problem_mark') and error.problem_mark:
        line = error.problem_mark.line + 1  # 0-indexed to 1-indexed
    
    # Try to get cleaner message
    if hasattr(error, 'problem') and error.problem:
        message = error.problem
        if hasattr(error, 'context') and error.context:
            message = f"{error.context}: {message}"
    
    return line, message


def parse_yaml(yaml_text: str) -> ParseResult:
    """
    Parse YAML text with line number preservation.
    
    This function:
    1. Pre-checks for tabs and basic indent issues
    2. Parses using ruamel.yaml
    3. Builds a line map for error reporting
    4. Converts to plain Python dicts
    
    Args:
        yaml_text: The YAML content as a string
    
    Returns:
        ParseResult with success status, data, line_map, or error
    """
    # Pre-check for tabs
    tab_error = _check_for_tabs(yaml_text)
    if tab_error:
        return ParseResult(success=False, error=tab_error)
    
    # Parse with ruamel.yaml
    yaml = YAML()
    yaml.preserve_quotes = True
    
    try:
        stream = StringIO(yaml_text)
        data = yaml.load(stream)
        
        # Handle empty YAML
        if data is None:
            return ParseResult(
                success=False,
                error=create_error(
                    code=ErrorCodes.YAML_PARSE_ERROR,
                    message="YAML file is empty or contains only comments",
                    suggestion="Add content to the YAML file"
                )
            )
        
        # Build line map before converting
        line_map = _build_line_map(data)
        
        # Convert to plain dict
        plain_data = _convert_to_plain_dict(data)
        
        return ParseResult(
            success=True,
            data=plain_data,
            line_map=line_map
        )
    
    except YAMLError as e:
        line, message = _extract_yaml_error_info(e)
        
        # Determine error code based on message content
        code = ErrorCodes.YAML_PARSE_ERROR
        if "indent" in message.lower():
            code = ErrorCodes.YAML_INDENT_ERROR
        elif "mapping" in message.lower():
            code = ErrorCodes.YAML_MAPPING_ERROR
        
        return ParseResult(
            success=False,
            error=create_error(
                code=code,
                message=message,
                line=line
            )
        )


def get_line_for_path(line_map: Dict[str, int], path: list) -> Optional[int]:
    """
    Get line number for a given path.
    
    Args:
        line_map: The line map from parsing
        path: List of path components, e.g., ["statement", "fields", "meters"]
    
    Returns:
        Line number if found, None otherwise
    """
    # Try exact path first
    path_str = ".".join(path)
    if path_str in line_map:
        return line_map[path_str]
    
    # Try parent paths
    for i in range(len(path) - 1, 0, -1):
        parent_path = ".".join(path[:i])
        if parent_path in line_map:
            return line_map[parent_path]
    
    return None