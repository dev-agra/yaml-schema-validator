# YAML Schema Validator

A production-ready, multi-phase YAML schema validator for GroundX prompt/config files with line numbers, actionable suggestions, and extensible rules.

## Features

- **4-Phase Validation:** Parse → Load → Core Rules → Profile Rules
- **Precise Error Locations:** Every error includes exact line number
- **Actionable Suggestions:** Clear fix recommendations for each issue
- **Auto-Fix:** Automatically repair tabs, indentation, and ignored attributes
- **Rich Output:** Colorized terminal output with code context
- **Multiple Formats:** Text, JSON, or HTML reports
- **Extensible Profiles:** Add domain-specific rules via YAML config
- **Interactive Wizard:** Guided schema creation for beginners

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Zero-to-Hero Tutorial](#zero-to-hero-tutorial)
3. [CLI Reference](#cli-reference)
4. [Error Code Reference](#error-code-reference)
5. [Profiles](#profiles)
6. [Customization](#customization)
7. [CI/CD Integration](#cicd-integration)

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Validate a file
yaml-validate config.yaml

# With profile
yaml-validate config.yaml --profile statement_only

# Auto-fix issues
yaml-validate config.yaml --fix
```

---

## Zero-to-Hero Tutorial

### Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/dev-agra/yaml-schema-validator.git
cd yaml-schema-validator

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
yaml-validate --help
```

You should see:

```
usage: yaml-validate [-h] [--profile NAME] [--format {text,json,rich}] ...

Validate GroundX YAML configuration files
```

---

### Step 2: Create Your First YAML File

Create a file called `my_config.yaml`:

```yaml
statement:
  prompt:
    instructions: "Extract utility bill information"

  fields:
    account_number:
      prompt:
        identifiers:
          - "Account Number"
          - "Account #"
        type: str

    total_amount:
      prompt:
        identifiers:
          - "Total Due"
          - "Amount Owed"
        type: float
```

---

### Step 3: Validate Your File

```bash
yaml-validate my_config.yaml
```

**Output (success):**

```
✅ Validation PASSED
   0 error(s), 0 warning(s)
```

---

### Step 4: Introduce an Error

Edit `my_config.yaml` and remove the `type` field:

```yaml
statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - "Account Number"
        # type is missing!
```

Run validation again:

```bash
yaml-validate my_config.yaml
```

**Output (failure):**

```
❌ Validation FAILED
   1 error(s), 0 warning(s)

🔴 GXVAL205 statement.fields.account_number.prompt.type
   Field 'account_number' is missing 'type'
   ╭──────────────────────────────────────────────────────╮
   │   4 │       prompt:                                  │
   │   5 │         identifiers:                           │
   │ → 6 │           - "Account Number"                   │
   ╰──────────────────────────────────────────────────────╯
   💡 Add 'type: str' (or 'int', 'float', 'date', etc.)
```

---

### Step 5: Fix the Error

Add the missing `type` field:

```yaml
statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - "Account Number"
        type: str # Fixed!
```

Validate again:

```bash
yaml-validate my_config.yaml
```

```
✅ Validation PASSED
```

---

### Step 6: Use Auto-Fix

Create a file with tabs (`bad_config.yaml`):

```yaml
statement:
	fields:    # This line has a TAB character
		amount:
			prompt:
				identifiers: ["amount"]
				type: str
```

Run auto-fix:

```bash
yaml-validate bad_config.yaml --fix
```

**Output:**

```
🔧 Auto-fixed issues:
  ✓ Line 2: Replaced tabs with spaces
  ✓ Line 3: Replaced tabs with spaces
  ✓ Line 4: Replaced tabs with spaces
  ✓ Line 5: Replaced tabs with spaces
  ✓ Line 6: Replaced tabs with spaces

📝 Saved to: bad_config.fixed.yaml
```

---

### Step 7: Use a Profile

Profiles add domain-specific rules. The `statement_only` profile requires:

- Only `statement` at top level
- Must have `meters` and `charges` fields

```bash
yaml-validate my_config.yaml --profile statement_only
```

**Output:**

```
❌ Validation FAILED
   2 error(s), 0 warning(s)

🔴 GXVAL403 statement.fields.meters
   Required field 'meters' is missing from statement.fields
   💡 Add 'meters:' with prompt containing identifiers and type

🔴 GXVAL403 statement.fields.charges
   Required field 'charges' is missing from statement.fields
   💡 Add 'charges:' with prompt containing identifiers and type
```

---

### Step 8: Use the Interactive Wizard

Don't want to write YAML manually? Use the wizard:

```bash
yaml-validate --wizard --profile statement_only
```

**Interactive session:**

```
🧙 YAML Schema Wizard

Step 1: Group Configuration
Profile 'statement_only' requires group name: statement

Step 2: Group Instructions (Optional)
Add group-level instructions? [y/N]: y
Instructions: Extract utility bill data

Step 3: Field Configuration
Profile requires fields: meters, charges

Configuring required field: meters
Identifiers (comma-separated): meter number, meter id
Type [str/int/float/date/bool]: str

Configuring required field: charges
Identifiers (comma-separated): total charges, amount due
Type [str/int/float/date/bool]: float

Add another field? [y/N]: n

Step 4: Generate
📝 Generated YAML

Save to file? [Y/n]: y
Filename [schema.yaml]: my_config.yaml
✓ Saved to my_config.yaml
```

---

### Step 9: Generate an HTML Report

```bash
yaml-validate my_config.yaml --report validation-report.html
```

Open `validation-report.html` in your browser for a professional report with:

- Pass/fail status
- Error/warning counts
- Code snippets with context
- Fix suggestions

---

### Step 10: Add a Custom Rule

Create a new rule in `src/rules/core_rules.py`:

```python
class FieldDescriptionRecommendedRule(Rule):
    """Recommend adding descriptions to fields."""

    @property
    def id(self) -> str:
        return "GXVAL306"

    @property
    def description(self) -> str:
        return "Recommend adding description to fields"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    def validate(self, model: YAMLSchema, line_map: Dict[str, int]) -> List[ValidationIssue]:
        issues = []

        for group_name, group in model.items():
            if group.fields:
                for field_name, field in group.fields.items():
                    if field.prompt and not field.prompt.description:
                        issues.append(create_warning(
                            code=self.id,
                            message=f"Field '{field_name}' has no description",
                            path=[group_name, "fields", field_name, "prompt", "description"],
                            suggestion="Add 'description:' to document this field's purpose"
                        ))

        return issues

# Add to CORE_RULES list
CORE_RULES = [
    # ... existing rules ...
    FieldDescriptionRecommendedRule,
]
```

---

## CLI Reference

```
yaml-validate [OPTIONS] [FILE]

Arguments:
  FILE                    YAML file to validate

Options:
  --profile, -p NAME      Validation profile (e.g., 'statement_only')
  --format, -f FORMAT     Output format: text, json, rich (default: rich)
  --fix                   Auto-fix all issues, save to .fixed.yaml
  --fix-tabs              Fix only tab characters (in-place)
  --fix-indent            Fix tabs and normalize indentation (in-place)
  --report, -r FILE       Generate HTML report
  --wizard, -w            Interactive schema creation wizard
  --list-rules            List all validation rules
  --list-profiles         List available profiles
  --verbose, -v           Show timing and detailed output
  --quiet, -q             Only output on errors
  --help, -h              Show help message

Exit Codes:
  0                       Validation passed
  1                       Validation failed
  2                       Runtime error (file not found, invalid profile, etc.)
```

### Examples

```bash
# Basic validation
yaml-validate config.yaml

# JSON output for CI/CD
yaml-validate config.yaml --format json

# Auto-fix and save
yaml-validate config.yaml --fix

# Fix tabs in-place
yaml-validate config.yaml --fix-tabs

# With profile
yaml-validate config.yaml --profile statement_only

# Generate report
yaml-validate config.yaml --report report.html

# Verbose with timing
yaml-validate config.yaml --verbose

# Interactive wizard
yaml-validate --wizard
yaml-validate --wizard --profile statement_only

# List available rules
yaml-validate --list-rules
```

---

## Error Code Reference

Error codes follow this pattern: `GXVAL` + 3-digit number

### Code Ranges

| Range | Category          | Description                  |
| ----- | ----------------- | ---------------------------- |
| `0xx` | Parse Errors      | YAML syntax issues           |
| `1xx` | Load Errors       | Structure/schema issues      |
| `2xx` | Semantic Errors   | Core rule violations         |
| `3xx` | Semantic Warnings | Core rule recommendations    |
| `4xx` | Profile Errors    | Profile rule violations      |
| `5xx` | Profile Warnings  | Profile rule recommendations |

---

### Parse Errors (0xx)

#### GXVAL001 - YAML Parse Error

**What:** Generic YAML syntax error  
**Why:** Invalid YAML syntax that the parser cannot understand  
**Example:**

```yaml
key: [unclosed bracket
```

**Fix:** Check for unclosed brackets, quotes, or invalid characters

#### GXVAL002 - Indentation Error

**What:** YAML indentation problem  
**Why:** Inconsistent or invalid indentation  
**Example:**

```yaml
parent:
   child: value    # 3 spaces
  sibling: value   # 2 spaces (inconsistent)
```

**Fix:** Use consistent 2-space indentation, or run `--fix-indent`

#### GXVAL003 - Tab Character Found

**What:** Tab character used for indentation  
**Why:** YAML requires spaces, not tabs  
**Fix:** Replace tabs with spaces, or run `--fix-tabs`

#### GXVAL004 - Mapping Error

**What:** Invalid YAML mapping syntax  
**Why:** Missing colon, invalid key format  
**Fix:** Add colon after keys: `key: value`

#### GXVAL005 - Empty File

**What:** YAML file is empty  
**Fix:** Add valid YAML content

---

### Load Errors (1xx)

#### GXVAL101 - Pydantic Validation Error

**What:** Schema validation failed  
**Why:** Content doesn't match expected model structure  
**Fix:** Check error details for specific field issues

#### GXVAL102 - Unknown Field

**What:** Field not defined in schema  
**Why:** Extra field that isn't recognized  
**Example:**

```yaml
prompt:
  identifiers: ["amount"]
  type: str
  unknown_field: "not allowed"
```

**Fix:** Remove the unknown field

#### GXVAL103 - Type Error

**What:** Wrong type for field  
**Why:** Expected string but got list, or vice versa  
**Fix:** Use correct type

#### GXVAL104 - Structure Error

**What:** Invalid structure  
**Why:** Expected dictionary but got something else  
**Fix:** Use proper YAML mapping structure

---

### Semantic Errors (2xx)

#### GXVAL201 - Group Prompt Missing Instructions

**What:** Group has prompt but no instructions  
**Why:** If a group has a prompt, it must include instructions  
**Example:**

```yaml
statement:
  prompt:
    description: "Wrong field" # Should be 'instructions'
```

**Fix:** Add `instructions:` to the group prompt

#### GXVAL202 - Field Missing Prompt

**What:** ExtractedField has no prompt  
**Why:** Every field must have a prompt  
**Example:**

```yaml
fields:
  amount: {} # Empty!
```

**Fix:** Add prompt with identifiers and type

#### GXVAL203 - Field Missing Identifiers

**What:** Field prompt has no identifiers  
**Why:** Identifiers are required to locate fields  
**Fix:** Add `identifiers: ["pattern1", "pattern2"]`

#### GXVAL204 - Empty Identifiers List

**What:** Identifiers list is empty  
**Why:** At least one identifier is required  
**Fix:** Add at least one identifier string

#### GXVAL205 - Field Missing Type

**What:** Field prompt has no type  
**Why:** Type is required for parsing values  
**Fix:** Add `type: str` (or int, float, date, bool)

---

### Semantic Warnings (3xx)

#### GXVAL301 - Group Prompt Ignored Attributes

**What:** Group prompt has field-only attributes  
**Why:** `identifiers`, `type` are ignored for group prompts  
**Fix:** Remove ignored attributes (only `instructions` is used)

#### GXVAL302 - Field Required Attribute Ignored

**What:** `required` attribute is set but ignored  
**Why:** All fields are always attempted  
**Fix:** Remove `required` - it does nothing

---

### Profile Errors (4xx)

#### GXVAL401 - Invalid Top-Level Key

**What:** Top-level key not allowed by profile  
**Example (statement_only):**

```yaml
invoice: # Not allowed!
```

**Fix:** Use only allowed keys (`statement`)

#### GXVAL402 - Missing Required Top-Level Key

**What:** Required top-level key is missing  
**Fix:** Add the required key

#### GXVAL403 - Missing Required Field

**What:** Required field missing from group  
**Example (statement_only):** Missing `meters` or `charges`  
**Fix:** Add required fields

#### GXVAL404 - Invalid Fields Type

**What:** `fields` is not a dictionary  
**Fix:** Use `field_name:` format, not list

---

### Profile Warnings (5xx)

#### GXVAL501 - Extra Field

**What:** Field not in profile's allowlist  
**Fix:** Remove extra field or update profile

---

## Profiles

### Built-in: `statement_only`

**Rules:**

- Only `statement` at top level
- Required fields: `meters`, `charges`

```bash
yaml-validate config.yaml --profile statement_only
```

### Creating Custom Profiles

Create `src/profiles/configs/my_profile.yaml`:

```yaml
name: my_profile
description: "My custom profile"
version: "1.0.0"

rules:
  top_level:
    required: [invoice]
    allowed: [invoice, metadata]

  groups:
    invoice:
      fields:
        required: [invoice_number, total_amount]
```

---

## Customization

### Adding Custom Rules

```python
# src/rules/core_rules.py

class MyRule(Rule):
    @property
    def id(self) -> str:
        return "GXVAL207"

    @property
    def description(self) -> str:
        return "What this rule checks"

    def validate(self, model, line_map):
        issues = []
        # Validation logic
        return issues

CORE_RULES = [..., MyRule]
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate YAML
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -e .
      - run: yaml-validate config.yaml
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: yaml-validate
        name: Validate YAML
        entry: yaml-validate
        language: system
        files: \.yaml$
```

### Docker

```bash
docker build -t yaml-validator .
docker run -v $(pwd):/data yaml-validator /data/config.yaml
```

---

## Uninstall

```bash
pip uninstall yaml-schema-validator
# Or remove venv
deactivate && rm -rf venv
```

---
