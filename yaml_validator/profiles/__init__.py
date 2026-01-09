"""
Profile configuration system.

Profiles define domain-specific validation rules loaded from YAML configs.
"""

from yaml_validator.profiles.profile_loader import (
    load_profile_config,
    get_available_profiles,
    ProfileConfig,
)

__all__ = ["load_profile_config", "get_available_profiles", "ProfileConfig"]
