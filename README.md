# YAML Schema Validator

A multi-phase YAML schema validator for GroundX prompt/config files with line numbers, suggestions, and extensible rules.

## Features

- **4-Phase Validation:** Parse → Load → Core Rules → Profile Rules
- **Line Numbers:** Every error shows exact location
- **Suggestions:** Actionable fix recommendations
- **Profiles:** Domain-specific rule sets
- **Multiple Outputs:** Text or JSON format

## Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install
pip install -e .
```

## CLI Usage

```bash
# Basic validation
yaml-validate config.yaml

# With profile
yaml-validate config.yaml --profile statement_only

# JSON output
yaml-validate config.yaml --format json

# List profiles
yaml-validate --list-profiles
```

### Exit Codes

| Code | Meaning |
| ---- | ------- |
| `0`  | Passed  |
| `1`  | Failed  |
| `2`  | Error   |

## Python API

```python
from src import validate_yaml_schema

result = validate_yaml_schema(yaml_text, profile="statement_only")

if result.success:
    print("Valid!")
else:
    for error in result.errors:
        print(f"Line {error.line}: [{error.code}] {error.message}")
```

## Error Codes

| Range     | Category      | Examples                     |
| --------- | ------------- | ---------------------------- |
| `001-009` | Parse         | Tabs, syntax errors          |
| `010-099` | Load          | Unknown fields, wrong types  |
| `100-149` | Core Errors   | Missing identifiers, type    |
| `150-199` | Core Warnings | Ignored attributes           |
| `200-299` | Profile       | Invalid keys, missing fields |

### Key Errors

| Code       | Description                      |
| ---------- | -------------------------------- |
| `GXVAL003` | Tab character found              |
| `GXVAL011` | Unknown field                    |
| `GXVAL104` | Missing identifiers              |
| `GXVAL105` | Missing type                     |
| `GXVAL203` | Missing required field (profile) |

## Adding Custom Rules

```python
# src/rules/core_rules.py

class MyRule(Rule):
    @property
    def id(self) -> str:
        return "GXVAL109"

    @property
    def description(self) -> str:
        return "What this rule checks"

    def validate(self, model: YAMLSchema, line_map: Dict[str, int]) -> List[ValidationIssue]:
        issues = []
        for group_name, group in model.items():
            if some_condition_fails:
                issues.append(create_error(
                    code=self.id,
                    message="Error message",
                    path=[group_name, "..."],
                    line=get_line_for_path(line_map, [...]),
                    suggestion="How to fix"
                ))
        return issues

# Add to CORE_RULES list
CORE_RULES = [..., MyRule]
```

## Adding Custom Profiles

Create `src/profiles/configs/my_profile.yaml`:

```yaml
name: my_profile
description: "My custom profile"
version: "1.0.0"

rules:
  top_level:
    required: [my_group]
    allowed: [my_group]

  groups:
    my_group:
      fields:
        required: [field1, field2]
```

Use it:

```bash
yaml-validate config.yaml --profile my_profile
```

## Project Structure

```
yaml-schema-validator/
├── main.py                 # CLI entry point
├── pyproject.toml
├── src/
│   ├── validator.py        # Main orchestrator
│   ├── core/               # Models, exceptions
│   ├── parser/             # YAML parsing
│   ├── loader/             # Pydantic loading
│   ├── rules/              # Validation rules
│   └── profiles/           # Profile configs
├── tests/
└── examples/
```

## Testing

```bash
pytest                      # Run all
pytest -v                   # Verbose
pytest --cov=src            # With coverage
```

## License

MIT
