"""
Pydantic models for YAML schema validation.

These models represent the structure of GroundX prompt/config YAML files:
- Top level: Dict[str, Group]
- Group contains optional prompt and fields
- Fields are Dict[str, ExtractedField]
- ExtractedField contains a prompt with identifiers, type, etc.
"""

from __future__ import annotations

from typing import Optional, List, Union, Dict, Any

from pydantic import BaseModel, ConfigDict, field_validator


class Prompt(BaseModel):
    """
    Prompt configuration for Groups or ExtractedFields.
    
    For Groups:
        - instructions is required (if prompt is present)
        - other fields are ignored (but we warn if present)
    
    For ExtractedFields:
        - identifiers is required (at least 1 item)
        - type is required
        - instructions, description, format are optional
    """
    model_config = ConfigDict(extra="forbid")
    
    # Core fields for ExtractedFields
    identifiers: Optional[List[str]] = None
    type: Optional[Union[str, List[str]]] = None  # Can be "str" or ["int", "float"]
    instructions: Optional[str] = None
    
    # Optional metadata fields
    description: Optional[str] = None
    format: Optional[str] = None
    
    # Fields that are ignored on Group prompts (warn if present)
    attr_name: Optional[str] = None
    default: Optional[Any] = None
    
    # Field that is ignored on ExtractedField prompts (warn if present)
    required: Optional[bool] = None
    
    @field_validator('identifiers')
    @classmethod
    def validate_identifiers(cls, v):
        """Validate identifiers is not an empty list."""
        if v is not None and len(v) == 0:
            raise ValueError('identifiers cannot be an empty list')
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate type values are reasonable."""
        if v is None:
            return v
        
        types_to_check = [v] if isinstance(v, str) else v
        
        for t in types_to_check:
            if not isinstance(t, str):
                raise ValueError(f'type must be string or list of strings, got {type(t)}')
        
        return v
    
    def has_ignored_group_attrs(self) -> List[str]:
        """
        Check if any attributes that are ignored for Group prompts are set.
        
        Returns list of attribute names that are set but would be ignored.
        """
        ignored = []
        if self.identifiers is not None:
            ignored.append("identifiers")
        if self.type is not None:
            ignored.append("type")
        if self.attr_name is not None:
            ignored.append("attr_name")
        if self.default is not None:
            ignored.append("default")
        if self.description is not None:
            ignored.append("description")
        if self.format is not None:
            ignored.append("format")
        if self.required is not None:
            ignored.append("required")
        return ignored


class ExtractedField(BaseModel):
    """
    A field to be extracted from documents.
    
    Must have a prompt with identifiers and type.
    """
    model_config = ConfigDict(extra="forbid")
    
    prompt: Optional[Prompt] = None


class Group(BaseModel):
    """
    A group of fields to extract.
    
    May optionally have a prompt with instructions.
    Must have fields (Dict[str, ExtractedField]).
    """
    model_config = ConfigDict(extra="forbid")
    
    prompt: Optional[Prompt] = None
    fields: Optional[Dict[str, ExtractedField]] = None


# Type alias for the top-level structure
YAMLSchema = Dict[str, Group]


def create_schema_from_dict(data: Dict[str, Any]) -> Dict[str, Group]:
    """
    Create a YAMLSchema (Dict[str, Group]) from a plain dictionary.
    
    Args:
        data: Parsed YAML as a plain dictionary
    
    Returns:
        Dictionary mapping group names to Group instances
    
    Raises:
        ValueError: If the data structure is invalid
    """
    result = {}
    
    for group_name, group_data in data.items():
        if not isinstance(group_data, dict):
            raise ValueError(
                f"Group '{group_name}' must be a dictionary, got {type(group_data).__name__}"
            )
        
        result[group_name] = Group(**group_data)
    
    return result