"""
Command-line interface for YAML schema validator.

Usage:
    yaml-validate config.yaml
    yaml-validate config.yaml --profile statement_only
    yaml-validate config.yaml --format json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.validator import validate_yaml_schema
from src.core.models import ValidationResult
from src.core.exceptions import ProfileNotFoundError
from src.profiles import get_available_profiles


def print_result_text(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation result in human-readable format."""
    
    # Header
    if result.success:
        print("✅ Validation PASSED")
    else:
        print("❌ Validation FAILED")
    
    print(f"   {result.error_count} error(s), {result.warning_count} warning(s)")
    print()
    
    # Errors
    if result.errors:
        print("ERRORS:")
        print("-" * 60)
        for error in result.errors:
            print(f"  {error}")
            print()
    
    # Warnings
    if result.warnings:
        print("WARNINGS:")
        print("-" * 60)
        for warning in result.warnings:
            print(f"  {warning}")
            print()


def print_result_json(result: ValidationResult) -> None:
    """Print validation result as JSON."""
    print(result.to_json())


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="yaml-validate",
        description="Validate GroundX YAML configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  yaml-validate config.yaml
  yaml-validate config.yaml --profile statement_only
  yaml-validate config.yaml --format json
  yaml-validate config.yaml --verbose

Available profiles:
  - statement_only: Validates utility statement extraction schemas
        """
    )
    
    parser.add_argument(
        "file",
        type=Path,
        nargs="?",
        help="YAML file to validate"
    )
    
    parser.add_argument(
        "--profile", "-p",
        type=str,
        default=None,
        metavar="NAME",
        help="Validation profile (e.g., 'statement_only')"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show more detailed output"
    )
    
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available validation profiles"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors (no success message)"
    )
    
    return parser


def main(args: list = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        args: Command-line arguments (uses sys.argv if None)
    
    Returns:
        Exit code (0 for success, 1 for validation failure, 2 for errors)
    """
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    # Handle --list-profiles
    if parsed.list_profiles:
        print("Available profiles:")
        for profile in get_available_profiles():
            print(f"  - {profile}")
        return 0
    
    # Check file is provided
    if parsed.file is None:
        parser.print_help()
        return 2
    
    # Check file exists
    if not parsed.file.exists():
        print(f"Error: File not found: {parsed.file}", file=sys.stderr)
        return 2
    
    # Read file
    try:
        yaml_text = parsed.file.read_text()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 2
    
    # Validate
    try:
        result = validate_yaml_schema(yaml_text, profile=parsed.profile)
    except ProfileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Available profiles: {', '.join(get_available_profiles())}")
        return 2
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 2
    
    # Output result
    if parsed.format == "json":
        print_result_json(result)
    else:
        if not (parsed.quiet and result.success):
            print_result_text(result, verbose=parsed.verbose)
    
    # Exit code
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())