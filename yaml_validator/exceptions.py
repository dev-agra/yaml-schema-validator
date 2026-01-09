"""
Custom exceptions for the YAML schema validator.
"""


class YAMLValidatorError(Exception):
    """Base exception for all validator errors."""
    pass


class ParseError(YAMLValidatorError):
    """Raised when YAML parsing fails."""
    
    def __init__(self, message: str, line: int = None):
        self.message = message
        self.line = line
        super().__init__(message)


class LoadError(YAMLValidatorError):
    """Raised when loading into Pydantic models fails."""
    pass


class ProfileNotFoundError(YAMLValidatorError):
    """Raised when a requested profile doesn't exist."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        super().__init__(f"Profile not found: {profile_name}")


class ProfileConfigError(YAMLValidatorError):
    """Raised when a profile configuration is invalid."""
    pass