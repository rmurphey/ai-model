# Model Versioning

## Overview

The analysis tool implements a comprehensive versioning system to ensure reproducibility across different versions of the model. As the model evolves, different versions may produce different results due to improvements, bug fixes, or algorithmic changes. The versioning system handles these differences transparently while maintaining backward compatibility.

## Version Format

Versions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes that may significantly affect results
- **MINOR**: New features or improvements with backward compatibility
- **PATCH**: Bug fixes and minor adjustments

Current version: **v2.0.0**

## Version Compatibility

The system automatically handles version compatibility when reproducing results:

**Full Compatibility**: Same version produces identical results
```bash
# Report v1.0.0 reproduced with v1.0.0 - exact match expected
python reproduce_results.py --tolerance 0.001 report_v1.0.0.md
```

**Major Compatibility**: Same major version with adjusted tolerance
```bash
# Report v1.0.0 reproduced with v1.1.0 - minor differences expected
python reproduce_results.py --tolerance 0.02 report_v1.0.0.md
```

**Cross-Major Reproduction**: Automatic adaptation with warnings
```bash
# Report v1.x reproduced with v2.x - adaptation applied
python reproduce_results.py --adapt report_v1.x.md
```

## Version Detection

The system automatically detects versions from report metadata:

```markdown
**Analysis Tool Version:** v1.0.0
**Analysis Engine:** AI Impact Model v1.0.0
```

Version information is extracted and used to:
- Select appropriate tolerance levels
- Apply version-specific adaptations
- Provide compatibility warnings
- Generate detailed difference explanations

## Tolerance Adjustment

Tolerance levels are automatically adjusted based on version compatibility:

| Version Relationship | Default Tolerance | Rationale |
|---------------------|------------------|-----------|
| Same version (1.0.0 → 1.0.0) | 0.001 | Exact reproduction expected |
| Minor update (1.0.0 → 1.1.0) | 0.02 | Small improvements may affect results |
| Major update (1.x → 2.x) | 0.05 | Significant changes, adaptation applied |

## Version Adaptation

When reproducing reports from older versions, the system applies automatic adaptations:

**Configuration Adaptation**: Updates deprecated parameters
```yaml
# v1.0 configuration
old_parameter: "legacy_value"

# Automatically adapted to v1.1
new_parameter: "updated_value"
```

**Parameter Mapping**: Translates changed parameter names
```python
# v1.0 → v1.1 adaptation
"feature_cycle_reduction" → "cycle_time_improvement"
"quality_factor" → "defect_reduction_rate"
```

**Value Adjustments**: Applies scaling factors for changed calculations
```python
# Example: v1.0 used different quality calculation
adapted_value = original_value * version_scaling_factor
```

## Creating New Versions

**Version Manager CLI**:
```bash
# Check current version
python version_manager.py current

# View version history
python version_manager.py history

# Get bump instructions
python version_manager.py bump patch    # Bug fixes
python version_manager.py bump minor    # New features, backward compatible
python version_manager.py bump major    # Breaking changes
```

**Manual Version Creation Process**:
1. **Get bump instructions**: Use the version manager to get specific instructions
2. **Update version.py**: Modify `CURRENT_VERSION`, `SUPPORTED_VERSIONS`, and `VERSION_HISTORY`
3. **Update adapters**: Add version adapters in `src/versioning/version_adapter.py` if needed
4. **Run tests**: Ensure all version tests pass
5. **Update documentation**: Update README.md version history

**Example: Creating v1.1.0**:
```python
# In src/config/version.py
CURRENT_VERSION = ModelVersion(1, 1, 0)

SUPPORTED_VERSIONS = [
    ModelVersion(1, 0, 0),
    ModelVersion(1, 1, 0)  # Add new version
]

VERSION_HISTORY["1.1.0"] = {
    "release_date": "2025-08-20",
    "description": "Enhanced analysis with new metrics",
    "breaking_changes": [],
    "new_features": ["New ROI calculation method", "Improved adoption modeling"]
}
```

## Working with Different Versions

**Checking Current Version**:
```python
from src.config.version import get_current_version_string
print(f"Current version: {get_current_version_string()}")
```

**Version-Aware Analysis**:
```python
from src.config.version import get_current_version, get_version_info
version = get_current_version()
info = get_version_info(version)
print(f"Compatibility: {info['compatibility']}")
```

**Custom Version Handling**:
```python
from src.versioning.version_adapter import adapt_scenario_config
adapted_config = adapt_scenario_config(
    config, from_version="1.0.0", to_version="1.1.0"
)
```

## Version History and Migration

**Version 2.0.0** (Current)
- **BREAKING**: Removed legacy single-file scenario loading support
- **NEW**: Added `/reports` command for comprehensive report generation
- **NEW**: Multi-format report export (Markdown, JSON, Text)
- Modular scenario loading is now the only supported method
- Enhanced report generation with Monte Carlo results integration

**Version 1.1.0**
- Added Monte Carlo simulation capabilities
- Probabilistic parameter definitions in scenarios
- NPV/ROI confidence intervals and risk assessment
- Sensitivity analysis for parameter importance

**Version 1.0.0**
- Initial stable release
- Baseline model with comprehensive business impact calculations
- Full reproduction system implementation

**Future Versions**
When new versions are released:
1. **Backward Compatibility**: Older reports remain reproducible
2. **Migration Guides**: Documentation for significant changes
3. **Adaptation Rules**: Automatic configuration updates
4. **Validation Tests**: Extensive testing of version transitions

## Best Practices

**For Report Generation**:
- Version information is automatically embedded in all reports
- No manual action required - versioning is transparent

**For Report Reproduction**:
- Use version-aware reproduction commands
- Review adaptation warnings for cross-version reproduction
- Validate critical analyses after version updates

**For Development**:
- Test version compatibility when making model changes
- Update adaptation rules for breaking changes
- Maintain comprehensive version test suites

**For Production Use**:
- Pin to specific versions for critical analyses
- Test reproduction of historical reports after updates
- Maintain version change logs for audit trails

## Troubleshooting Version Issues

**Reproduction Failures**:
```bash
# If reproduction fails, check version compatibility
python reproduce_results.py --version-info report.md

# Use adaptive mode for cross-version reproduction
python reproduce_results.py --adapt --tolerance 0.05 report.md
```

**Version Conflicts**:
```python
# Check version compatibility programmatically
from src.config.version import ModelVersion
v1 = ModelVersion.from_string("1.0.0")
v2 = ModelVersion.from_string("1.1.0")
print(f"Compatible: {v1.is_compatible_with(v2)}")
print(f"Compatibility level: {v1.compatibility_level(v2)}")
```

**Adaptation Issues**:
- Review adaptation warnings in reproduction output
- Check if manual configuration updates are needed
- Validate adapted results against original expectations