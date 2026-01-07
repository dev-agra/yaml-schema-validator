"""Auto-fixer for deterministic validation issues."""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import re

from src.core.models import ValidationIssue, ErrorCodes


@dataclass
class FixResult:
    """Result of auto-fix operation."""
    fixed_yaml: str
    changes: List[str]
    unfixable: List[ValidationIssue]


class AutoFixer:
    """Automatically fix deterministic validation issues."""
    
    # Issues that can be auto-fixed
    FIXABLE_CODES = {
        ErrorCodes.YAML_TAB_ERROR: "_fix_tabs",
        ErrorCodes.YAML_INDENT_ERROR: "_fix_indentation",
        ErrorCodes.GROUP_PROMPT_IGNORED_ATTRS: "_fix_ignored_group_attrs",
        ErrorCodes.FIELD_REQUIRED_IGNORED: "_fix_required_attr",
    }
    
    def fix(self, yaml_text: str, issues: List[ValidationIssue]) -> FixResult:
        """
        Apply auto-fixes and return result.
        
        Args:
            yaml_text: Original YAML content
            issues: List of validation issues
            
        Returns:
            FixResult with fixed YAML, changes made, and unfixable issues
        """
        fixed = yaml_text
        changes = []
        unfixable = []
        
        # Always fix tabs first (affects line numbers)
        fixed, tab_changes = self._fix_all_tabs(fixed)
        changes.extend(tab_changes)
        
        # Process other fixable issues
        for issue in issues:
            if issue.code == ErrorCodes.YAML_TAB_ERROR:
                continue  # Already handled
            
            if issue.code in self.FIXABLE_CODES:
                method = getattr(self, self.FIXABLE_CODES[issue.code])
                fixed, change = method(fixed, issue)
                if change:
                    changes.append(change)
            else:
                unfixable.append(issue)
        
        return FixResult(
            fixed_yaml=fixed,
            changes=changes,
            unfixable=unfixable
        )
    
    def fix_tabs_only(self, yaml_text: str) -> Tuple[str, List[str]]:
        """Fix only tab characters (--fix-tabs command)."""
        return self._fix_all_tabs(yaml_text)
    
    def fix_all(self, yaml_text: str) -> Tuple[str, List[str]]:
        """Fix tabs and normalize indentation (--fix-all command)."""
        changes = []
        
        # Step 1: Fix tabs
        fixed, tab_changes = self._fix_all_tabs(yaml_text)
        changes.extend(tab_changes)
        
        # Step 2: Normalize indentation
        fixed, indent_changes = self._normalize_indentation(fixed)
        changes.extend(indent_changes)
        
        return fixed, changes
    
    def _fix_all_tabs(self, yaml_text: str) -> Tuple[str, List[str]]:
        """Replace all tabs with spaces."""
        changes = []
        lines = yaml_text.splitlines()
        
        for i, line in enumerate(lines):
            if '\t' in line:
                lines[i] = line.replace('\t', '  ')
                changes.append(f"Line {i + 1}: Replaced tabs with spaces")
        
        return '\n'.join(lines), changes
    
    def _normalize_indentation(self, yaml_text: str, indent_size: int = 2) -> Tuple[str, List[str]]:
        """
        Normalize indentation to consistent spacing.
        
        Ensures all indentation is a multiple of indent_size.
        """
        changes = []
        lines = yaml_text.splitlines()
        result_lines = []
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                result_lines.append(line)
                continue
            
            # Skip pure comment lines but preserve their indentation
            if line.lstrip().startswith('#'):
                result_lines.append(line)
                continue
            
            # Count leading spaces
            stripped = line.lstrip(' ')
            current_indent = len(line) - len(stripped)
            
            if current_indent == 0:
                result_lines.append(line)
                continue
            
            # Check if indentation is a clean multiple of indent_size
            if current_indent % indent_size != 0:
                # Round to nearest multiple
                level = round(current_indent / indent_size)
                new_indent = level * indent_size
                
                new_line = ' ' * new_indent + stripped
                result_lines.append(new_line)
                changes.append(f"Line {i + 1}: Fixed indentation ({current_indent} → {new_indent} spaces)")
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines), changes
    
    def _fix_ignored_group_attrs(self, yaml_text: str, issue: ValidationIssue) -> Tuple[str, Optional[str]]:
        """Remove ignored attributes from group prompts."""
        if len(issue.path) < 3:
            return yaml_text, None
        
        # Path like: ["statement", "prompt", "identifiers"]
        attr_name = issue.path[-1]
        
        # Find and remove the line with this attribute
        lines = yaml_text.splitlines()
        if issue.line and 0 < issue.line <= len(lines):
            line_idx = issue.line - 1
            line = lines[line_idx]
            
            # Check if this line contains the attribute
            if f"{attr_name}:" in line or f"{attr_name} :" in line:
                # Remove this line
                del lines[line_idx]
                return '\n'.join(lines), f"Line {issue.line}: Removed ignored '{attr_name}' from group prompt"
        
        return yaml_text, None
    
    def _fix_required_attr(self, yaml_text: str, issue: ValidationIssue) -> Tuple[str, Optional[str]]:
        """Remove ignored 'required' attribute from field prompts."""
        lines = yaml_text.splitlines()
        
        if issue.line and 0 < issue.line <= len(lines):
            line_idx = issue.line - 1
            line = lines[line_idx]
            
            if "required:" in line or "required :" in line:
                del lines[line_idx]
                return '\n'.join(lines), f"Line {issue.line}: Removed ignored 'required' attribute"
        
        return yaml_text, None


def get_fixable_codes() -> List[str]:
    """Get list of error codes that can be auto-fixed."""
    return list(AutoFixer.FIXABLE_CODES.keys())


def fix_yaml(yaml_text: str, fix_tabs: bool = True, fix_indent: bool = True) -> Tuple[str, List[str]]:
    """
    Convenience function to fix common YAML issues.
    
    Args:
        yaml_text: Original YAML content
        fix_tabs: Replace tabs with spaces
        fix_indent: Normalize indentation
    
    Returns:
        Tuple of (fixed_yaml, list_of_changes)
    """
    fixer = AutoFixer()
    changes = []
    fixed = yaml_text
    
    if fix_tabs:
        fixed, tab_changes = fixer._fix_all_tabs(fixed)
        changes.extend(tab_changes)
    
    if fix_indent:
        fixed, indent_changes = fixer._normalize_indentation(fixed)
        changes.extend(indent_changes)
    
    return fixed, changes