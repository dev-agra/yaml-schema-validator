"""
Pytest configuration and fixtures for yaml-schema-validator tests.
"""

import pytest
from pathlib import Path


# =============================================================================
# Valid YAML Fixtures
# =============================================================================

@pytest.fixture
def valid_minimal_yaml():
    """Minimal valid YAML with all required fields."""
    return """
statement:
  fields:
    meters:
      prompt:
        identifiers:
          - "meter number"
        type: str
    charges:
      prompt:
        identifiers:
          - "total charges"
        type: str
"""


@pytest.fixture
def valid_full_yaml():
    """Full valid YAML with all optional fields."""
    return """
statement:
  prompt:
    instructions: "Extract utility statement data"
  fields:
    meters:
      prompt:
        identifiers:
          - "meter number"
          - "meter id"
        type: str
        description: "The meter identifier"
        format: "alphanumeric"
        instructions: "Look for meter number near usage"
    charges:
      prompt:
        identifiers:
          - "total charges"
          - "amount due"
        type: ["int", "float"]
        description: "Total amount owed"
"""


@pytest.fixture
def valid_no_group_prompt_yaml():
    """Valid YAML without group-level prompt (this is allowed)."""
    return """
statement:
  fields:
    amount:
      prompt:
        identifiers:
          - "amount"
        type: str
"""


# =============================================================================
# Invalid Indentation Fixtures
# =============================================================================

@pytest.fixture
def invalid_tab_yaml():
    """YAML with tab character."""
    return """
statement:
\tfields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
"""


@pytest.fixture
def invalid_indent_yaml():
    """YAML with bad indentation."""
    return """
statement:
  fields:
   amount:
      prompt:
        identifiers: ["amount"]
        type: str
"""


@pytest.fixture
def invalid_mapping_yaml():
    """YAML with mapping error."""
    return """
statement:
  fields:
    amount
      prompt:
        identifiers: ["amount"]
"""


# =============================================================================
# Invalid Schema Fixtures
# =============================================================================

@pytest.fixture
def missing_prompt_yaml():
    """YAML with field missing prompt."""
    return """
statement:
  fields:
    amount: {}
"""


@pytest.fixture
def missing_identifiers_yaml():
    """YAML with field missing identifiers."""
    return """
statement:
  fields:
    amount:
      prompt:
        type: str
"""


@pytest.fixture
def empty_identifiers_yaml():
    """YAML with empty identifiers list."""
    return """
statement:
  fields:
    amount:
      prompt:
        identifiers: []
        type: str
"""


@pytest.fixture
def missing_type_yaml():
    """YAML with field missing type."""
    return """
statement:
  fields:
    amount:
      prompt:
        identifiers:
          - "amount"
"""


@pytest.fixture
def group_prompt_no_instructions_yaml():
    """YAML with group prompt but missing instructions."""
    return """
statement:
  prompt:
    description: "This should be instructions"
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
"""


@pytest.fixture
def field_required_set_yaml():
    """YAML with field.prompt.required set (should warn)."""
    return """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
        required: true
"""


# =============================================================================
# Profile-Related Fixtures
# =============================================================================

@pytest.fixture
def invalid_top_level_key_yaml():
    """YAML with invalid top-level key for statement_only profile."""
    return """
invoice:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
"""


@pytest.fixture
def missing_required_fields_yaml():
    """YAML missing required fields for statement_only profile."""
    return """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["amount"]
        type: str
"""


@pytest.fixture
def valid_statement_only_yaml():
    """Valid YAML for statement_only profile."""
    return """
statement:
  fields:
    meters:
      prompt:
        identifiers: ["meter"]
        type: str
    charges:
      prompt:
        identifiers: ["charges"]
        type: str
"""


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_yaml_file(tmp_path):
    """Factory fixture to create temporary YAML files."""
    def _create_yaml(content: str, filename: str = "test.yaml") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path
    return _create_yaml


@pytest.fixture
def sample_line_map():
    """Sample line map for testing."""
    return {
        "statement": 1,
        "statement.fields": 2,
        "statement.fields.amount": 3,
        "statement.fields.amount.prompt": 4,
        "statement.fields.amount.prompt.identifiers": 5,
        "statement.fields.amount.prompt.type": 6,
    }