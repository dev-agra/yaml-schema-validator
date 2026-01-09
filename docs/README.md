# YAML schema validator

## Context

We need a user-facing YAML schema validator that can validate our prompt/config YAML files before they're used. The validator must be strict about indentation/layout, load into our Pydantic models, and then apply additional semantic rules with clear, actionable feedback. After core validation, we also need a configurable mechanism to layer on custom validations for specific YAML "profiles" (e.g., a "statement-only" schema).

## YAML Structure Being Validated

Top-level YAML must be:

- `Dict[str, Group]` (each top-level key maps to a `Group`)

[`Group` is our Pydantic class](https://github.com/eyelevelai/groundx-python/blob/main/src/groundx/extract/classes/group.py) from the [groundx Python Library](https://github.com/eyelevelai/groundx-python).

In the YAML, `groundx.extract.classes.group.Group` may have:

- (optional) [`prompt`](https://github.com/eyelevelai/groundx-python/blob/main/src/groundx/extract/classes/prompt.py)
- (optional) `fields`

`Group.fields` contains [`ExtractedField` instances](https://github.com/eyelevelai/groundx-python/blob/main/src/groundx/extract/classes/field.py).

For this validator, we enforce the schema rules described in the next section.

## Core Validation

1. Validate indentation/layout first (before semantic validation)

- The very first step must validate YAML indentation and layout.
- If indentation/layout is invalid:
  - Return an error referencing the first line that violates indentation/layout.
  - Provide the line number and a clear fix suggestion (e.g., "unexpected indent", "tab used", "mapping value not allowed here", etc.).

Notes/expectations

- YAML indentation errors often come from parser exceptions. We want the earliest failure with line number.
- Prefer a YAML loader that can preserve line numbers and give helpful parse errors.

2. Load YAML into `Dict[str, Group]`

- After indentation/layout passes, load YAML into `Dict[str, Group]`.
- `Group` and `ExtractedField` Pydantic validation handles basic typing/shape errors.
- Any Pydantic validation errors must be surfaced cleanly:
  - include the path (top-level key / field key)
  - include a human readable message

3. Apply core semantic rules (post-load)

After successfully loading into Pydantic models, enforce the following additional rules:

**`Group` rules**

- A `Group` may or may not have a `prompt`.
- If `Group.prompt` is present:
  - it must have `instructions` (non-empty).
  - other `prompt` attributes (`attr_name`, `default`, `description`, `format`, `identifiers`, `type`, `required`) are ignored for `Group` prompts.
  - if any of those other attributes are populated, emit a warning (not failure) that they are ignored.

**`ExtractedField` rules**
For each field in `Group.fields` that is an `ExtractedField`:

- Must have `prompt`.
- `prompt.identifiers` must exist and contain at least 1 string.
- `prompt.type` must exist.
- Optional-but-used (allowed, no warning): `attr_name`, `default`, `description`, `format`.
- `prompt.required` is not used:
  - if populated (true/false explicitly set), emit a warning that it's ignored.

**Feedback format**
For any violation, output must be clear and actionable, referencing:

- the top-level dict key (group name) (e.g., "statement")
- the field key (attribute name) when relevant (e.g., "statement_date")
- what is wrong and how to fix it

Also:

- If the YAML indentation/layout is invalid, include line number.
- If the YAML loads but semantic checks fail, include:
- group key and/or field key
- prompt attribute name
- (line number is "nice to have" if we can map it; not required unless indentation/layout invalid)

## Custom Validation (Configurable Rule Sets)

After core validation is implemented, add a mechanism to selectively apply additional rule sets ("profiles") on top of core rules.

### Example custom profile to implement (as demonstration)

Create a custom configuration/profile demonstrating these rules:

**Top-level rules**

- Only one allowed top-level key: `statement`
- i.e. required keys = {statement} and no other keys allowed

**`statement` group rules**

- `statement.fields` must be a `Dict[str, ExtractedField]` (i.e., no list, no nested groups, etc. — only extracted fields)
- Within `statement.fields`, the keys `meters` and `charges` must exist

These custom rules must:

- run after core validation
- be optional (enabled via config / profile selection)
- produce the same style of actionable errors (and ideally warnings)

## Suggested Implementation Approach

### Validator pipeline

Implement a pipeline with explicit phases:

1. Parse/indentation phase

- Parse YAML and fail fast on indentation/layout issues with line number.

2. Model load phase

- Convert parsed YAML -> Dict[str, Group] via Pydantic.

3. Core semantic phase

- Run core semantic rules described above.

4. Custom rule phase

- Run selected custom rule sets ("profiles").

### Rule engine / plugin model (for custom validations)

Implement a small "rule" interface and registry:

- `ValidationIssue`:
  - `severity`: "error" | "warning"
  - `message`: string
  - `path`: list/tuple (e.g. ["statement", "fields", "meters", "prompt", "type"])
  - `line`: optional int (when available)
  - `code`: optional stable identifier (e.g. GXVAL001)
- Rule interface:
  - `id`, `description`, `applies_to` (core vs profile)
  - `validate(model, raw_yaml_meta) -> list[ValidationIssue]`
- Validator:
  - runs `core_rules` always
  - runs `profile_rules[profile_name]` when chosen
  - returns a list of issues; if any error, validation fails
- Profile config:
  - can be a small Python dict/class or YAML/JSON file that declares:
    - required top-level keys
    - allowed top-level keys
    - per-group field constraints
    - required field keys under a specific group
  - The example "statement-only" profile should be implemented using this mechanism (not hardcoded).

This keeps us from hardcoding Arcadia/other customer schemas in the library logic.

## Deliverables

1. A validator entrypoint function, e.g.:

- validate_yaml_schema(yaml_text: str, profile: Optional[str] = None) -> ValidationResult

2. CLI helper or callable utility (either is fine) that prints issues clearly
3. Core rules + warnings implemented as described
4. Pluggable custom profile mechanism + one demo profile:

- profile name suggestion: "statement_only"

5. Unit tests covering:

- indentation failure with correct first-line reporting
- Pydantic load errors are readable and correctly located by group/field key
- each core rule violation produces expected issue format
- profile rules work and are optional

## Acceptance Criteria

- Indentation/layout invalid YAML fails with:
  - first violating line number
  - actionable message
- Valid indentation but invalid schema fails with:
  - group key / field key and exact missing/invalid attribute(s)
- Group prompt rules enforced:
  - missing instructions => error
  - extra group prompt attrs => warnings
- Field prompt rules enforced:
  - missing prompt / identifiers / type => error
  - required populated => warning
- Custom profile support:
  - core validation always runs
  - profile validation runs only when selected
  - demo profile "statement_only" works:
    - only top-level key statement
    - statement.fields must be dict of fields
    - meters and charges required

## Notes / Constraints

- We already have dynamic field inflation in Group.\_inflate_fields; validator must be compatible with that behavior.
- Prefer producing a structured result that can be shown in CLI/UI later (not just raising a raw exception).

## Implementation Checklist

- Choose YAML parser approach that provides parse errors with line numbers (indentation/layout phase)
- Implement ValidationIssue + ValidationResult
- Implement core validation rules
- Implement rule engine + profile selection mechanism
- Add "statement_only" profile using the new mechanism
- Add comprehensive unit tests for the above
