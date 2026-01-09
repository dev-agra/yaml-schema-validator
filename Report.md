# YAML-Schema-Validator

To approach the YAML Schema Validator problem statement, we are implementing a multi-phased pipeline designed to bridge the gap between raw data and strict GroundX Pydantic models.

## Problem Statement & Approach

The core challenge is validating complex YAML configurations that must eventually load into groundx.extract.classes.group.Group and ExtractedField models. To solve this, our approach follows a four-pass validation logic:

**Phase 1: Syntax & Layout Pass:** Before any semantic checks, we use ruamel.yaml to enforce strict indentation and layout rules. This catches basic YAML errors (like tab usage or misalignments) that would otherwise crash a standard parser without a clear line number.

**Phase 2: Model Loading Pass:** We attempt to "inflate" the YAML into actual Python objects. By catching pydantic.ValidationError, we map cryptic machine-readable errors into a human-friendly "path" format (e.g., statement.fields.meters.prompt.type).

**Phase 3: Core Semantic Pass:** Post-loading, we enforce domain-specific rules. For example, we verify that every Group contains non-empty instructions and that ExtractedField prompts contain at least one identifier.

**Phase 4: Custom Profile Pass:** We use a pluggable registry to apply customer-specific rules, such as the statement_only profile, which restricts top-level keys and mandates the presence of specific fields like meters and charges.

## Approach Considerations

We designed a multi-phase validation pipeline (parse → load → core rules → profile rules) so errors surface in a logical order. We evaluated fail-fast everywhere, collect-all everywhere, and a hybrid approach. Fail-fast alone felt frustrating, while collect-all wasted effort on broken input, so we chose a hybrid that stops early for invalid YAML and then reports all meaningful semantic issues together.

For the YAML parser with line numbers, accurate error locations were a priority. We compared PyYAML, ruamel.yaml, and strictyaml. PyYAML dropped line positions after parsing, and strictyaml felt too restrictive for real-world files, so ruamel.yaml gave us the right balance of flexibility and precise error reporting.

In the Pydantic schema loader, our goal was strict structure with clear feedback. We considered manual validation, JSON Schema, Pydantic, and marshmallow. Manual checks became tedious, JSON Schema didn't integrate well with our flow, and Pydantic gave us strong typing, strictness (extra="forbid"), and readable errors in one place.

The extensible rule engine was built around an abstract Rule class and a registry. We evaluated hardcoded if/else logic, function-based rules, and class-based rules. Hardcoded logic didn't scale, and functions lacked structure, so class-based rules gave us isolation, testability, and easier growth over time.

The profile system uses YAML-based configuration for domain-specific rules. We compared hardcoded profile classes, Python-based configs, and YAML configs. Code-based options tied changes to developers, while YAML made profiles easy to add, review, and evolve without touching application logic.

With the CLI, Python API, and test suite, the focus was usability and confidence. The CLI supports human and CI use cases, the API enables integration, and the test suite helped clarify edge cases early and ensured the system stays stable as it evolves.

## Going Beyond

**Auto-Fix** `--fix`
Automatically repairs deterministic issues like tabs→spaces, normalizes inconsistent indentation, and removes ignored attributes (required, group prompt attrs). Outputs a .fixed.yaml file with all changes applied while listing remaining issues that require manual intervention.

**Rich Output** `--format rich` (default)
Colorized terminal output using the Rich library with red panels for errors, yellow for warnings, and 2-3 lines of surrounding code context with the problem line highlighted. Includes visual icons, structured formatting, and dimmed suggestions for a professional developer experience.

**Interactive Wizard** `--wizard`
Step-by-step CLI prompts that guide users through creating a valid YAML schema from scratch. Asks for group names, whether to add instructions, then iterates through fields collecting names, identifiers, types, and optional metadata. Generates complete valid YAML and optionally saves to file.

**Report Generation** `--report <file.html>`
Generates professional HTML reports with executive summary (pass/fail status, error/warning counts), expandable issue details, syntax-highlighted code snippets showing error context, and fix suggestions. Suitable for documentation, audits, or sharing with non-technical stakeholders.

**Tab Auto-Fix** `--fix-tabs`
Single-purpose command that finds and replaces all tab characters with spaces in-place. Fixes the most common YAML error instantly without touching other formatting. Also available: --fix-indent for normalizing inconsistent spacing.

**Rule Listing** `--list-rules`
Displays all available validation rules in a formatted table showing error codes, severity levels (error/warning), and descriptions. Helps users understand exactly what checks are performed and allows referencing specific rules in documentation or discussions.

**Verbose Mode** `--verbose`
Shows detailed execution information including timing metrics for each phase (parse, load, rules), which rules were checked, and their pass/fail status. Useful for debugging slow validations or understanding why certain errors are triggered.

## Future Improvements

**AI-Assisted Suggestions**
Use LLMs to suggest appropriate identifiers based on field names and document context, recommend related fields to add, and provide intelligent auto-fixes for complex semantic errors that simple string manipulation cannot handle.

**Schema Registry**
Centralized repository for publishing, versioning, and sharing validated schemas across teams. Support for pushing schemas with version tags, pulling approved configurations, access control, and integration with CI/CD pipelines.

**Watch Mode** `--watch`
Monitor YAML files and automatically re-validate on save using filesystem watchers. Provides instant feedback loop during development without manually re-running commands.

**JSON Schema Generation** `--generate-json-schema`
Export validation rules as JSON Schema for IDE integration. Enables autocomplete, hover documentation, and inline validation in VS Code/IntelliJ without running the validator.

**Schema from Documents**
Analyze sample PDFs/images using OCR and NLP to automatically generate extraction schemas by identifying fields, values, and text patterns.

**Web Interface**
Browser-based validation UI with Monaco editor, real-time validation, click-to-navigate errors, and shareable result URLs.

## Learnings/Notes

We learned that putting a clear structure in place early (parser → loader → rules → profiles) reduced cognitive load later and made the system easier to extend without revisiting earlier decisions.

High-quality errors turned out to be as important as validation itself; preserving line numbers and giving precise, actionable feedback significantly improves developer confidence and reduces iteration time.

Combining fail-fast behavior for syntax and structural issues with collect-all behavior for semantic rules struck a good balance between safety and usability, avoiding noisy outputs while still surfacing all meaningful problems.

Choosing explicit, class-based rules over more abstract or declarative approaches kept the system understandable, testable, and approachable, especially as the number of rules increased.

Using configuration (YAML profiles) instead of code for domain-specific constraints enabled flexibility and faster iteration without increasing operational or deployment complexity.

Deliberately avoiding advanced features early (AI fixes, plugins, web UI) helped keep focus on reliability and correctness, creating a strong foundation on which more ambitious capabilities can be added later.
