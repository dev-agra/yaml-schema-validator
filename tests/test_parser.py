"""
Tests for YAML parser.
"""

import pytest

from src.parser import parse_yaml, get_line_for_path
from src.core.models import ErrorCodes


class TestParseYAML:
    """Tests for the parse_yaml function."""
    
    def test_valid_yaml_parses_successfully(self, valid_minimal_yaml):
        """Valid YAML should parse without errors."""
        result = parse_yaml(valid_minimal_yaml)
        
        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert "statement" in result.data
    
    def test_valid_yaml_returns_dict(self, valid_minimal_yaml):
        """Parsed data should be a plain dict, not CommentedMap."""
        result = parse_yaml(valid_minimal_yaml)
        
        assert isinstance(result.data, dict)
        assert isinstance(result.data["statement"], dict)
    
    def test_tab_character_returns_error(self, invalid_tab_yaml):
        """Tab characters should cause an error with line number."""
        result = parse_yaml(invalid_tab_yaml)
        
        assert result.success is False
        assert result.error is not None
        assert result.error.code == ErrorCodes.YAML_TAB_ERROR
        assert result.error.line is not None
        assert "tab" in result.error.message.lower()
    
    def test_empty_yaml_returns_error(self):
        """Empty YAML should return an error."""
        result = parse_yaml("")
        
        assert result.success is False
        assert result.error is not None
        assert "empty" in result.error.message.lower()
    
    def test_comment_only_yaml_returns_error(self):
        """YAML with only comments should return an error."""
        result = parse_yaml("# Just a comment\n# Another comment")
        
        assert result.success is False
        assert result.error is not None
    
    def test_invalid_yaml_syntax_returns_error(self):
        """Invalid YAML syntax should return an error."""
        invalid_yaml = """
statement:
  fields:
    - this: is
    wrong: syntax
"""
        result = parse_yaml(invalid_yaml)
        
        assert result.success is False
        assert result.error is not None
        assert result.error.line is not None


class TestLineMap:
    """Tests for line number mapping."""
    
    def test_line_map_contains_top_level_keys(self, valid_minimal_yaml):
        """Line map should contain top-level keys."""
        result = parse_yaml(valid_minimal_yaml)
        
        assert result.success
        assert "statement" in result.line_map
    
    def test_line_map_contains_nested_keys(self, valid_minimal_yaml):
        """Line map should contain nested keys."""
        result = parse_yaml(valid_minimal_yaml)
        
        assert result.success
        assert "statement.fields" in result.line_map
        assert "statement.fields.meters" in result.line_map
    
    def test_line_numbers_are_positive(self, valid_minimal_yaml):
        """All line numbers should be positive integers."""
        result = parse_yaml(valid_minimal_yaml)
        
        assert result.success
        for path, line in result.line_map.items():
            assert isinstance(line, int)
            assert line > 0


class TestGetLineForPath:
    """Tests for the get_line_for_path helper."""
    
    def test_exact_path_match(self, sample_line_map):
        """Should return line number for exact path match."""
        line = get_line_for_path(sample_line_map, ["statement", "fields"])
        
        assert line == 2
    
    def test_parent_path_fallback(self, sample_line_map):
        """Should fall back to parent path if exact not found."""
        line = get_line_for_path(
            sample_line_map,
            ["statement", "fields", "amount", "prompt", "nonexistent"]
        )
        
        assert line is not None
    
    def test_no_match_returns_none(self, sample_line_map):
        """Should return None if no path matches."""
        line = get_line_for_path(sample_line_map, ["nonexistent", "path"])
        
        assert line is None


class TestInlineArraySyntax:
    """Tests for inline array YAML syntax."""
    
    def test_inline_array_parses_correctly(self):
        """Inline array syntax should parse correctly."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers: ["id1", "id2", "id3"]
        type: str
"""
        result = parse_yaml(yaml_text)
        
        assert result.success
        identifiers = result.data["statement"]["fields"]["amount"]["prompt"]["identifiers"]
        assert identifiers == ["id1", "id2", "id3"]
    
    def test_block_array_parses_correctly(self):
        """Block array syntax should parse correctly."""
        yaml_text = """
statement:
  fields:
    amount:
      prompt:
        identifiers:
          - id1
          - id2
          - id3
        type: str
"""
        result = parse_yaml(yaml_text)
        
        assert result.success
        identifiers = result.data["statement"]["fields"]["amount"]["prompt"]["identifiers"]
        assert identifiers == ["id1", "id2", "id3"]