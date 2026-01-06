"""
Profile configuration loader.

This module loads profile configurations from YAML files and
creates the corresponding rule instances.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Optional, Any

import yaml

from ..core.exceptions import ProfileNotFoundError, ProfileConfigError
from ..rules.base import Rule, RuleRegistry
from ..rules.profile_rules.statement_only import (
    TopLevelKeysRule,
    RequiredFieldsRule,
    FieldsDictTypeRule,
)


# Default profiles directory
PROFILES_DIR = Path(__file__).parent / "configs"


class ProfileConfig:
    """
    Parsed profile configuration.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        rules: Dict[str, Any] = None
    ):
        self.name = name
        self.description = description
        self.version = version
        self.rules = rules or {}
    
    @property
    def required_top_level_keys(self) -> Set[str]:
        """Get required top-level keys."""
        top_level = self.rules.get("top_level", {})
        return set(top_level.get("required", []))
    
    @property
    def allowed_top_level_keys(self) -> Set[str]:
        """Get allowed top-level keys."""
        top_level = self.rules.get("top_level", {})
        return set(top_level.get("allowed", []))
    
    def get_group_config(self, group_name: str) -> Dict[str, Any]:
        """Get configuration for a specific group."""
        groups = self.rules.get("groups", {})
        return groups.get(group_name, {})
    
    def get_required_fields(self, group_name: str) -> Set[str]:
        """Get required fields for a group."""
        group_config = self.get_group_config(group_name)
        fields_config = group_config.get("fields", {})
        return set(fields_config.get("required", []))


def load_profile_config(profile_name: str) -> ProfileConfig:
    """
    Load a profile configuration from YAML file.
    
    Args:
        profile_name: Name of the profile (e.g., "statement_only")
    
    Returns:
        ProfileConfig instance
    
    Raises:
        ProfileNotFoundError: If profile doesn't exist
        ProfileConfigError: If profile config is invalid
    """
    config_path = PROFILES_DIR / f"{profile_name}.yaml"
    
    if not config_path.exists():
        raise ProfileNotFoundError(profile_name)
    
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ProfileConfigError(f"Profile config must be a dictionary")
        
        return ProfileConfig(
            name=data.get("name", profile_name),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            rules=data.get("rules", {})
        )
    
    except yaml.YAMLError as e:
        raise ProfileConfigError(f"Invalid YAML in profile config: {e}")


def create_rules_from_config(config: ProfileConfig) -> List[Rule]:
    """
    Create rule instances from a profile configuration.
    
    Args:
        config: ProfileConfig instance
    
    Returns:
        List of Rule instances
    """
    rules = []
    
    # Top-level key rules
    if config.required_top_level_keys or config.allowed_top_level_keys:
        rules.append(TopLevelKeysRule(
            required_keys=config.required_top_level_keys,
            allowed_keys=config.allowed_top_level_keys or config.required_top_level_keys
        ))
    
    # Group-specific rules
    for group_name in config.rules.get("groups", {}).keys():
        group_config = config.get_group_config(group_name)
        fields_config = group_config.get("fields", {})
        
        # Required fields rule
        required_fields = config.get_required_fields(group_name)
        if required_fields:
            rules.append(RequiredFieldsRule(
                group_name=group_name,
                required_fields=required_fields
            ))
        
        # Fields type rule
        if fields_config.get("type") == "dict":
            rules.append(FieldsDictTypeRule(group_name=group_name))
    
    return rules


def register_profile(
    registry: RuleRegistry,
    profile_name: str,
    config: ProfileConfig = None
) -> None:
    """
    Register a profile's rules with the registry.
    
    Args:
        registry: RuleRegistry to register with
        profile_name: Name of the profile
        config: Optional ProfileConfig (loads from file if not provided)
    """
    if config is None:
        config = load_profile_config(profile_name)
    
    rules = create_rules_from_config(config)
    
    for rule in rules:
        registry.register_profile(profile_name, rule)


def get_available_profiles() -> List[str]:
    """
    Get list of available profile names.
    
    Returns:
        List of profile names
    """
    profiles = []
    
    if PROFILES_DIR.exists():
        for config_file in PROFILES_DIR.glob("*.yaml"):
            profiles.append(config_file.stem)
    
    return sorted(profiles)


def profile_exists(profile_name: str) -> bool:
    """
    Check if a profile exists.
    
    Args:
        profile_name: Name of the profile
    
    Returns:
        True if profile exists
    """
    config_path = PROFILES_DIR / f"{profile_name}.yaml"
    return config_path.exists()