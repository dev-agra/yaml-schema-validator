"""Interactive wizard for guided YAML schema creation."""

from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from ruamel.yaml import YAML
from io import StringIO


class SchemaWizard:
    """Step-by-step CLI wizard for creating valid YAML schemas."""
    
    def __init__(self):
        self.console = Console()
        self.yaml = YAML()
        self.yaml.default_flow_style = False
    
    def run(self, profile: Optional[str] = None) -> str:
        """Run the interactive wizard and return generated YAML."""
        self.console.print(Panel(
            "[bold cyan]YAML Schema Wizard[/]\n\n"
            "This wizard will guide you through creating a valid extraction schema.",
            title="🧙 Welcome",
            border_style="cyan"
        ))
        
        schema = {}
        
        # Step 1: Group configuration
        self.console.print("\n[bold]Step 1: Group Configuration[/]")
        self.console.print("[dim]Groups organize related fields together.[/]\n")
        
        if profile == "statement_only":
            self.console.print("[yellow]Profile 'statement_only' requires group name: statement[/]")
            group_name = "statement"
        else:
            group_name = Prompt.ask("Group name", default="statement")
        
        schema[group_name] = {"fields": {}}
        
        # Step 2: Group prompt (optional)
        self.console.print("\n[bold]Step 2: Group Instructions (Optional)[/]")
        self.console.print("[dim]Group-level instructions guide the overall extraction.[/]\n")
        
        if Confirm.ask("Add group-level instructions?", default=False):
            instructions = Prompt.ask("Instructions")
            schema[group_name]["prompt"] = {"instructions": instructions}
        
        # Step 3: Fields
        self.console.print("\n[bold]Step 3: Field Configuration[/]")
        self.console.print("[dim]Fields define what data to extract.[/]\n")
        
        required_fields = []
        if profile == "statement_only":
            required_fields = ["meters", "charges"]
            self.console.print(f"[yellow]Profile requires fields: {', '.join(required_fields)}[/]\n")
        
        # Add required fields first
        for field_name in required_fields:
            self.console.print(f"\n[cyan]Configuring required field: {field_name}[/]")
            field_config = self._configure_field(field_name)
            schema[group_name]["fields"][field_name] = field_config
        
        # Add additional fields
        while Confirm.ask("\nAdd another field?", default=True if not required_fields else False):
            field_name = Prompt.ask("Field name")
            if field_name in schema[group_name]["fields"]:
                self.console.print("[red]Field already exists![/]")
                continue
            
            field_config = self._configure_field(field_name)
            schema[group_name]["fields"][field_name] = field_config
        
        # Generate YAML
        self.console.print("\n[bold]Step 4: Generate[/]")
        yaml_output = self._generate_yaml(schema)
        
        self.console.print(Panel(
            yaml_output,
            title="📝 Generated YAML",
            border_style="green"
        ))
        
        return yaml_output
    
    def _configure_field(self, field_name: str) -> dict:
        """Configure a single field."""
        field = {"prompt": {}}
        
        # Identifiers
        self.console.print(f"[dim]Enter identifiers (text patterns to match in documents)[/]")
        identifiers_str = Prompt.ask(
            "Identifiers (comma-separated)",
            default=field_name.replace("_", " ")
        )
        field["prompt"]["identifiers"] = [
            i.strip() for i in identifiers_str.split(",") if i.strip()
        ]
        
        # Type
        field_type = Prompt.ask(
            "Type",
            choices=["str", "int", "float", "date", "bool"],
            default="str"
        )
        field["prompt"]["type"] = field_type
        
        # Optional: description
        if Confirm.ask("Add description?", default=False):
            field["prompt"]["description"] = Prompt.ask("Description")
        
        # Optional: instructions
        if Confirm.ask("Add field-specific instructions?", default=False):
            field["prompt"]["instructions"] = Prompt.ask("Instructions")
        
        return field
    
    def _generate_yaml(self, schema: dict) -> str:
        """Convert schema dict to YAML string."""
        stream = StringIO()
        self.yaml.dump(schema, stream)
        return stream.getvalue()


def run_wizard(profile: Optional[str] = None) -> str:
    """Run the schema wizard and return generated YAML."""
    wizard = SchemaWizard()
    return wizard.run(profile)