"""
Command-line interface for YAML schema validator.

Usage:
    yaml-validate config.yaml
    yaml-validate config.yaml --profile statement_only
    yaml-validate config.yaml --fix
    yaml-validate config.yaml --report report.html
    yaml-validate --wizard
    yaml-validate --list-rules
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.validator import validate_yaml_schema
from src.core.models import ValidationResult, ERROR_CODE_DESCRIPTIONS
from src.core.exceptions import ProfileNotFoundError
from src.profiles import get_available_profiles


def print_result_text(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation result in plain text format."""
    if result.success:
        print("\n✅ Validation PASSED")
    else:
        print("\n❌ Validation FAILED")
    
    print(f"   {result.error_count} error(s), {result.warning_count} warning(s)\n")
    
    if verbose and any([result.parse_time_ms, result.load_time_ms, result.rules_time_ms]):
        print("Timing:")
        if result.parse_time_ms:
            print(f"  Parse: {result.parse_time_ms:.1f}ms")
        if result.load_time_ms:
            print(f"  Load:  {result.load_time_ms:.1f}ms")
        if result.rules_time_ms:
            print(f"  Rules: {result.rules_time_ms:.1f}ms")
        print()
    
    if result.errors:
        print("ERRORS:")
        print("-" * 60)
        for error in result.errors:
            print(f"  {error}\n")
    
    if result.warnings:
        print("WARNINGS:")
        print("-" * 60)
        for warning in result.warnings:
            print(f"  {warning}\n")


def print_result_rich(result: ValidationResult, yaml_text: str = None, verbose: bool = False) -> None:
    """Print validation result with rich formatting."""
    from src.output import RichFormatter
    formatter = RichFormatter()
    formatter.print_result(result, yaml_text, verbose)


def print_rules_list() -> None:
    """Print all available rules."""
    try:
        from src.output import RichFormatter
        formatter = RichFormatter()
        
        rules = []
        for code, desc in sorted(ERROR_CODE_DESCRIPTIONS.items()):
            # Determine severity from code range
            code_num = int(code[5:])
            if code_num < 100:
                severity = "error"  # Parse errors
            elif code_num < 200:
                severity = "error"  # Load errors
            elif code_num < 300:
                severity = "error"  # Core semantic errors
            elif code_num < 400:
                severity = "warning"  # Core semantic warnings
            elif code_num < 500:
                severity = "error"  # Profile errors
            else:
                severity = "warning"  # Profile warnings
            
            rules.append({"code": code, "severity": severity, "description": desc})
        
        formatter.print_rules(rules)
    except ImportError:
        # Fallback to plain text
        print("\nAvailable Validation Rules:")
        print("-" * 60)
        for code, desc in sorted(ERROR_CODE_DESCRIPTIONS.items()):
            print(f"  {code}: {desc}")
        print()


def run_fix(yaml_text: str, issues: list, output_path: Path) -> int:
    """Run auto-fix and save result."""
    from src.fixer import AutoFixer
    from rich.console import Console
    
    console = Console()
    fixer = AutoFixer()
    
    # First, fix tabs and indentation (syntax issues)
    fixed, syntax_changes = fixer.fix_all(yaml_text)
    
    # Then fix semantic issues (ignored attributes, etc.)
    result = fixer.fix(fixed, issues)
    
    all_changes = syntax_changes + result.changes
    
    if all_changes:
        console.print("\n[bold green]🔧 Auto-fixed issues:[/]")
        for change in all_changes:
            console.print(f"  [green]✓[/] {change}")
        
        # Save fixed file
        fixed_path = output_path.with_suffix('.fixed.yaml')
        fixed_path.write_text(result.fixed_yaml)
        console.print(f"\n[bold]📝 Saved to:[/] {fixed_path}")
    else:
        console.print("\n[yellow]No auto-fixable issues found.[/]")
    
    if result.unfixable:
        console.print(f"\n[bold red]Remaining issues ({len(result.unfixable)}):[/]")
        for issue in result.unfixable:
            console.print(f"  [red]•[/] [{issue.code}] {issue.message}")
        return 1
    
    return 0


def run_fix_tabs(yaml_text: str, file_path: Path) -> int:
    """Fix tabs only and save in place."""
    from src.fixer import AutoFixer
    from rich.console import Console
    
    console = Console()
    fixer = AutoFixer()
    fixed, changes = fixer.fix_tabs_only(yaml_text)
    
    if changes:
        file_path.write_text(fixed)
        console.print(f"\n[bold green]🔧 Fixed {len(changes)} tab issue(s)[/]")
        for change in changes:
            console.print(f"  [green]✓[/] {change}")
        console.print(f"\n[bold]📝 File updated:[/] {file_path}")
        return 0
    else:
        console.print("\n[green]No tab characters found.[/]")
        return 0


def run_fix_indent(yaml_text: str, file_path: Path) -> int:
    """Fix tabs and normalize indentation, save in place."""
    from src.fixer import AutoFixer
    from rich.console import Console
    
    console = Console()
    fixer = AutoFixer()
    fixed, changes = fixer.fix_all(yaml_text)
    
    if changes:
        file_path.write_text(fixed)
        console.print(f"\n[bold green]🔧 Fixed {len(changes)} issue(s)[/]")
        for change in changes:
            console.print(f"  [green]✓[/] {change}")
        console.print(f"\n[bold]📝 File updated:[/] {file_path}")
        return 0
    else:
        console.print("\n[green]No indentation issues found.[/]")
        return 0


def run_wizard(profile: str = None) -> int:
    """Run interactive schema wizard."""
    from src.wizard import run_wizard as wizard_run
    from rich.console import Console
    from rich.prompt import Confirm
    
    console = Console()
    yaml_output = wizard_run(profile)
    
    if Confirm.ask("\nSave to file?", default=True):
        from rich.prompt import Prompt
        filename = Prompt.ask("Filename", default="schema.yaml")
        Path(filename).write_text(yaml_output)
        console.print(f"\n[green]✓ Saved to {filename}[/]")
    
    return 0


def generate_html_report(result: ValidationResult, yaml_text: str, output_path: str, filename: str, profile: str) -> None:
    """Generate and save HTML report."""
    from src.output import ReportGenerator
    generator = ReportGenerator()
    generator.save(result, output_path, yaml_text, filename, profile)
    print(f"📊 Report saved to: {output_path}")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="yaml-validate",
        description="Validate GroundX YAML configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  yaml-validate config.yaml                    # Basic validation
  yaml-validate config.yaml --profile statement_only
  yaml-validate config.yaml --format rich      # Colored output
  yaml-validate config.yaml --fix              # Auto-fix issues
  yaml-validate config.yaml --fix-tabs         # Fix only tabs
  yaml-validate config.yaml --report out.html  # HTML report
  yaml-validate --wizard                       # Interactive creation
  yaml-validate --list-rules                   # Show all rules
  yaml-validate --list-profiles                # Show all profiles
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
        choices=["text", "json", "rich"],
        default="rich",
        help="Output format (default: rich)"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix all issues (tabs, indentation, ignored attrs)"
    )
    
    parser.add_argument(
        "--fix-tabs",
        action="store_true",
        help="Fix only tab characters (in-place)"
    )
    
    parser.add_argument(
        "--fix-indent",
        action="store_true",
        help="Fix tabs and normalize indentation (in-place)"
    )
    
    parser.add_argument(
        "--report", "-r",
        type=str,
        metavar="FILE",
        help="Generate HTML report to FILE"
    )
    
    parser.add_argument(
        "--wizard", "-w",
        action="store_true",
        help="Interactive schema creation wizard"
    )
    
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List all validation rules"
    )
    
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available validation profiles"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output with timing"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output on errors"
    )
    
    return parser


def main(args: list = None) -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0=success, 1=validation failure, 2=runtime error)
    """
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    # Handle --list-profiles
    if parsed.list_profiles:
        print("Available profiles:")
        for profile in get_available_profiles():
            print(f"  - {profile}")
        return 0
    
    # Handle --list-rules
    if parsed.list_rules:
        print_rules_list()
        return 0
    
    # Handle --wizard
    if parsed.wizard:
        return run_wizard(parsed.profile)
    
    # Check file is provided for validation commands
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
    
    # Handle --fix-tabs (before validation)
    if parsed.fix_tabs:
        return run_fix_tabs(yaml_text, parsed.file)
    
    # Handle --fix-indent (before validation)
    if parsed.fix_indent:
        return run_fix_indent(yaml_text, parsed.file)
    
    # Validate
    try:
        start_time = time.time()
        result = validate_yaml_schema(yaml_text, profile=parsed.profile)
        total_time = (time.time() - start_time) * 1000
        
        if parsed.verbose:
            result.rules_time_ms = total_time  # Approximate
            
    except ProfileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Available profiles: {', '.join(get_available_profiles())}")
        return 2
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 2
    
    # Handle --fix
    if parsed.fix:
        return run_fix(yaml_text, result.errors + result.warnings, parsed.file)
    
    # Handle --report
    if parsed.report:
        generate_html_report(
            result, yaml_text, parsed.report,
            parsed.file.name, parsed.profile
        )
    
    # Output result
    if parsed.format == "json":
        print(result.to_json())
    elif parsed.format == "rich":
        if not (parsed.quiet and result.success):
            print_result_rich(result, yaml_text, parsed.verbose)
    else:
        if not (parsed.quiet and result.success):
            print_result_text(result, parsed.verbose)
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())