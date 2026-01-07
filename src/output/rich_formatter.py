"""Rich terminal output formatter."""

from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.core.models import ValidationResult, ValidationIssue, Severity


class RichFormatter:
    """Colorized terminal output with code context."""
    
    def __init__(self):
        self.console = Console()
    
    def print_result(
        self, 
        result: ValidationResult, 
        yaml_text: Optional[str] = None,
        verbose: bool = False
    ):
        """Print validation result with rich formatting."""
        # Header
        if result.success:
            self.console.print("\n[bold green]✅ Validation PASSED[/]")
        else:
            self.console.print("\n[bold red]❌ Validation FAILED[/]")
        
        # Summary
        self.console.print(f"   [dim]{result.error_count} error(s), {result.warning_count} warning(s)[/]\n")
        
        # Timing (verbose mode)
        if verbose and any([result.parse_time_ms, result.load_time_ms, result.rules_time_ms]):
            self._print_timing(result)
        
        # Errors
        for error in result.errors:
            self._print_issue(error, yaml_text, "red")
        
        # Warnings
        for warning in result.warnings:
            self._print_issue(warning, yaml_text, "yellow")
    
    def _print_timing(self, result: ValidationResult):
        """Print timing information."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim")
        table.add_column(style="cyan")
        
        if result.parse_time_ms:
            table.add_row("Parse:", f"{result.parse_time_ms:.1f}ms")
        if result.load_time_ms:
            table.add_row("Load:", f"{result.load_time_ms:.1f}ms")
        if result.rules_time_ms:
            table.add_row("Rules:", f"{result.rules_time_ms:.1f}ms")
        
        total = (result.parse_time_ms or 0) + (result.load_time_ms or 0) + (result.rules_time_ms or 0)
        table.add_row("Total:", f"{total:.1f}ms")
        
        self.console.print(Panel(table, title="[dim]Timing[/]", border_style="dim", box=box.ROUNDED))
        self.console.print()
    
    def _print_issue(self, issue: ValidationIssue, yaml_text: Optional[str], color: str):
        """Print a single issue with code context."""
        # Header
        severity_icon = "🔴" if issue.severity == Severity.ERROR else "🟡"
        self.console.print(f"{severity_icon} [{color} bold]{issue.code}[/]", end=" ")
        self.console.print(f"[dim]{issue.format_path()}[/]")
        
        # Message
        self.console.print(f"   {issue.message}")
        
        # Code context
        if issue.line and yaml_text:
            context = self._get_code_context(yaml_text, issue.line)
            if context:
                self.console.print(Panel(
                    context,
                    border_style=color,
                    box=box.ROUNDED,
                    padding=(0, 1)
                ))
        
        # Suggestion
        if issue.suggestion:
            self.console.print(f"   [dim]💡 {issue.suggestion}[/]")
        
        self.console.print()
    
    def _get_code_context(self, yaml_text: str, line: int, context_lines: int = 2) -> Text:
        """Get code context around the error line."""
        lines = yaml_text.splitlines()
        start = max(0, line - context_lines - 1)
        end = min(len(lines), line + context_lines)
        
        text = Text()
        for i in range(start, end):
            line_num = i + 1
            is_error_line = line_num == line
            
            # Line number
            prefix = "→ " if is_error_line else "  "
            style = "bold red" if is_error_line else "dim"
            
            text.append(f"{prefix}{line_num:3d} │ ", style="dim")
            text.append(f"{lines[i]}\n", style=style if is_error_line else None)
        
        return text
    
    def print_rules(self, rules: List[dict]):
        """Print all available rules."""
        table = Table(title="Available Validation Rules", box=box.ROUNDED)
        table.add_column("Code", style="cyan", width=10)
        table.add_column("Severity", width=8)
        table.add_column("Description")
        
        for rule in rules:
            severity_style = "red" if rule["severity"] == "error" else "yellow"
            table.add_row(
                rule["code"],
                f"[{severity_style}]{rule['severity']}[/]",
                rule["description"]
            )
        
        self.console.print(table)
    
    def print_verbose_phase(self, phase: str, status: str = "running", time_ms: float = None):
        """Print verbose phase information."""
        icon = "🔍" if status == "running" else ("✓" if status == "done" else "✗")
        color = "yellow" if status == "running" else ("green" if status == "done" else "red")
        
        time_str = f" ({time_ms:.1f}ms)" if time_ms else ""
        self.console.print(f"[{color}]{icon}[/] {phase}{time_str}")