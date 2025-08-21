"""
Model Version Configuration
Centralized version management for the AI Impact Analysis Model.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import re


@dataclass
class ModelVersion:
    """Represents a semantic version for the AI Impact Analysis Model"""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __repr__(self) -> str:
        return f"ModelVersion({self.major}, {self.minor}, {self.patch})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ModelVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, ModelVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other) -> bool:
        return self < other or self == other
    
    def __gt__(self, other) -> bool:
        return not self <= other
    
    def __ge__(self, other) -> bool:
        return not self < other
    
    def is_compatible_with(self, other: 'ModelVersion') -> bool:
        """
        Check if this version is compatible with another version.
        Same major version = compatible (following semantic versioning)
        """
        return self.major == other.major
    
    def compatibility_level(self, other: 'ModelVersion') -> str:
        """
        Return compatibility level with another version.
        
        Returns:
            'full': Same version, full compatibility
            'major': Same major version, high compatibility  
            'minor': Different major, limited compatibility
            'none': Significantly different, no compatibility
        """
        if self == other:
            return 'full'
        elif self.major == other.major:
            return 'major'
        elif abs(self.major - other.major) == 1:
            return 'minor'
        else:
            return 'none'
    
    @classmethod
    def from_string(cls, version_string: str) -> 'ModelVersion':
        """
        Parse a version string into a ModelVersion object.
        
        Args:
            version_string: Version in format "X.Y.Z" or "vX.Y.Z"
            
        Returns:
            ModelVersion object
            
        Raises:
            ValueError: If version string is invalid
        """
        # Remove 'v' prefix if present
        version_string = version_string.lstrip('v')
        
        # Match semantic version pattern
        pattern = r'^(\d+)\.(\d+)\.(\d+)$'
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        major, minor, patch = map(int, match.groups())
        return cls(major=major, minor=minor, patch=patch)


# Current model version
CURRENT_VERSION = ModelVersion(2, 0, 0)

# List of supported versions for reproduction
SUPPORTED_VERSIONS = [
    ModelVersion(1, 0, 0),
    ModelVersion(1, 1, 0),
    ModelVersion(2, 0, 0)
]

# Version history and breaking changes
VERSION_HISTORY = {
    "1.0.0": {
        "release_date": "2025-08-20",
        "description": "Initial stable release with comprehensive reproduction system",
        "breaking_changes": [],
        "new_features": [
            "Complete AI impact analysis model",
            "Reproduction engine with validation",
            "Multiple scenario support",
            "Comprehensive reporting"
        ]
    },
    "1.1.0": {
        "release_date": "2025-08-20",
        "description": "Add Monte Carlo simulation capabilities",
        "breaking_changes": [],
        "new_features": [
            "Monte Carlo simulation engine with multiple distribution types",
            "Probabilistic parameter definitions in scenarios",
            "NPV/ROI confidence intervals and risk assessment",
            "Sensitivity analysis for parameter importance",
            "CLI support for Monte Carlo analysis with customizable iterations",
            "Text-based visualization for distribution results",
            "Correlation support between parameters"
        ]
    }
}


def get_current_version() -> ModelVersion:
    """Get the current model version"""
    return CURRENT_VERSION


def get_current_version_string() -> str:
    """Get the current model version as a string"""
    return str(CURRENT_VERSION)


def is_version_supported(version: ModelVersion) -> bool:
    """Check if a version is supported for reproduction"""
    return version in SUPPORTED_VERSIONS


def get_supported_versions() -> List[ModelVersion]:
    """Get list of all supported versions"""
    return SUPPORTED_VERSIONS.copy()


def get_compatibility_info(from_version: ModelVersion, to_version: ModelVersion) -> dict:
    """
    Get detailed compatibility information between two versions.
    
    Args:
        from_version: Original version
        to_version: Target version
        
    Returns:
        Dictionary with compatibility details
    """
    compatibility = from_version.compatibility_level(to_version)
    
    info = {
        'from_version': str(from_version),
        'to_version': str(to_version),
        'compatibility_level': compatibility,
        'can_reproduce': compatibility in ['full', 'major'],
        'warnings': [],
        'recommendations': []
    }
    
    if compatibility == 'full':
        info['warnings'] = []
        info['recommendations'] = ["Perfect compatibility - results should be identical"]
    elif compatibility == 'major':
        info['warnings'] = ["Minor version differences may cause small numerical variations"]
        info['recommendations'] = ["Use relaxed tolerance for validation", "Review changelog for differences"]
    elif compatibility == 'minor':
        info['warnings'] = ["Major version difference - significant changes possible"]
        info['recommendations'] = ["Manual review required", "Consider upgrading to newer version"]
    else:
        info['warnings'] = ["Incompatible versions - reproduction not recommended"]
        info['recommendations'] = ["Upgrade to supported version", "Use migration tools if available"]
    
    return info


def validate_version_string(version_string: str) -> bool:
    """
    Validate if a version string is properly formatted.
    
    Args:
        version_string: Version string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ModelVersion.from_string(version_string)
        return True
    except ValueError:
        return False


def bump_version(bump_type: str = 'patch', description: str = "", breaking_changes: List[str] = None, new_features: List[str] = None) -> ModelVersion:
    """
    Bump the current version and update version history.
    
    Args:
        bump_type: 'major', 'minor', or 'patch'
        description: Description of the changes
        breaking_changes: List of breaking changes (for major/minor bumps)
        new_features: List of new features
        
    Returns:
        New ModelVersion object
        
    Raises:
        ValueError: If bump_type is invalid
    """
    global CURRENT_VERSION, SUPPORTED_VERSIONS, VERSION_HISTORY
    
    if bump_type not in ['major', 'minor', 'patch']:
        raise ValueError(f"Invalid bump_type: {bump_type}. Must be 'major', 'minor', or 'patch'")
    
    current = CURRENT_VERSION
    
    if bump_type == 'major':
        new_version = ModelVersion(current.major + 1, 0, 0)
    elif bump_type == 'minor':
        new_version = ModelVersion(current.major, current.minor + 1, 0)
    else:  # patch
        new_version = ModelVersion(current.major, current.minor, current.patch + 1)
    
    # Update globals (Note: This is for demonstration - in practice you'd update the file)
    CURRENT_VERSION = new_version
    SUPPORTED_VERSIONS.append(new_version)
    
    # Add to version history
    from datetime import datetime
    VERSION_HISTORY[str(new_version)] = {
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "description": description or f"{bump_type.capitalize()} version bump",
        "breaking_changes": breaking_changes or [],
        "new_features": new_features or []
    }
    
    return new_version


def get_version_bump_instructions(bump_type: str) -> str:
    """
    Get instructions for manually bumping version.
    
    Args:
        bump_type: 'major', 'minor', or 'patch'
        
    Returns:
        Instructions for version bump
    """
    current = CURRENT_VERSION
    
    if bump_type == 'major':
        new_version = ModelVersion(current.major + 1, 0, 0)
        impact = "Breaking changes that significantly affect results"
    elif bump_type == 'minor':
        new_version = ModelVersion(current.major, current.minor + 1, 0)
        impact = "New features or improvements with backward compatibility"
    elif bump_type == 'patch':
        new_version = ModelVersion(current.major, current.minor, current.patch + 1)
        impact = "Bug fixes that don't change results significantly"
    else:
        raise ValueError(f"Invalid bump_type: {bump_type}")
    
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    return f"""
To bump from v{current} to v{new_version} ({bump_type}):

1. Update CURRENT_VERSION in src/config/version.py:
   CURRENT_VERSION = ModelVersion({new_version.major}, {new_version.minor}, {new_version.patch})

2. Add {new_version} to SUPPORTED_VERSIONS list

3. Add entry to VERSION_HISTORY:
   "{new_version}": {{
       "release_date": "{today}",
       "description": "Your description here",
       "breaking_changes": [],  # List any breaking changes
       "new_features": []       # List new features
   }}

4. Update version adapters if needed (src/versioning/version_adapter.py)

5. Run tests:
   python -m unittest tests.test_version_management tests.test_version_reproduction

6. Update README.md version history section

Impact: {impact}
"""