# Version Management Command

Automated version management for the AI Impact Analysis Model.

## Usage

```bash
# Check current version
claude version current

# View version history  
claude version history

# Bump version automatically
claude version bump patch                    # Bug fixes
claude version bump minor                    # New features
claude version bump major                    # Breaking changes

# Bump with description
claude version bump minor "Add new ROI metrics"
```

## What it does

- **Automatically updates** `src/config/version.py` with new version
- **Adds version** to `SUPPORTED_VERSIONS` list
- **Creates changelog entry** in `VERSION_HISTORY`
- **Validates** version format and compatibility
- **Provides next steps** for testing and committing

## Examples

```bash
# Current version info
$ claude version current
Current version: v1.0.0
Release date: 2025-08-20
Description: Initial stable release with comprehensive reproduction system

# Bump patch version
$ claude version bump patch
✅ Bumped version from v1.0.0 to v1.0.1

# Bump minor with description
$ claude version bump minor "Enhanced analysis metrics"
✅ Bumped version from v1.0.1 to v1.1.0
```

## Version Types

- **patch**: Bug fixes that don't significantly change results (1.0.0 → 1.0.1)
- **minor**: New features with backward compatibility (1.0.0 → 1.1.0)
- **major**: Breaking changes that affect results (1.0.0 → 2.0.0)

The command handles all file updates automatically - no manual editing required!