# Contributing

This model is designed to be extended. Here are the key extension points and guidelines.

## Key Extension Points

- Add new baseline profiles in `create_industry_baseline()`
- Define new impact factors in `ImpactFactors`
- Create custom adoption curves in `AdoptionModel`
- Add new text-based analysis utilities in `ModelVisualizer`
- Extend export functionality in `run_analysis.py`
- Create new Claude commands in `.claude/commands/`
- Enhance reproduction validation in `src/reproducibility/validators.py`
- Add new reproduction test cases in `tests/test_reproduction_engine.py`
- Extend version management in `src/config/version.py`
- Add version adapters in `src/versioning/version_adapter.py`

## Reproduction System Guidelines

When contributing to the reproduction system:
1. **Maintain backward compatibility** - existing reports should remain reproducible
2. **Add version information** - include version metadata in new features  
3. **Test thoroughly** - add test cases for new validation rules
4. **Document changes** - update reproduction guidelines for breaking changes
5. **Validate existing reports** - run reproduction tests before committing changes

## Versioning Guidelines

When making changes that affect model results:

### Version Bumps
Follow semantic versioning principles:
- **PATCH**: Bug fixes that don't change results significantly
- **MINOR**: New features or improvements with backward compatibility
- **MAJOR**: Breaking changes that significantly affect results

### Version Adapters
Create adapters for cross-version compatibility:
- Add new adapter classes in `src/versioning/version_adapter.py`
- Register adapters in the version registry
- Test adaptation logic thoroughly

### Testing Requirements
- Run full test suite: `python -m unittest tests.test_version_management tests.test_version_reproduction`
- Validate historical reports: `python reproduce_results.py --validate outputs/reports/`
- Test version transitions between old and new versions

### Documentation Updates
- Update version history in README.md
- Document breaking changes and migration paths
- Add examples for new version-specific features

## Code Style Guidelines

### Python Code
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Add docstrings for all public functions
- Keep functions focused and single-purpose

### YAML Configurations
- Use clear, descriptive parameter names
- Add comments for complex configurations
- Maintain consistent indentation (2 spaces)
- Validate YAML syntax before committing

### Documentation
- Use clear, concise language
- Include code examples where helpful
- Keep README focused on users
- Put technical details in docs/

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m unittest tests.test_reproduction_engine
python -m unittest tests.test_version_management

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

### Adding Tests
- Write tests for new features
- Test edge cases and error conditions
- Ensure tests are reproducible
- Mock external dependencies

## Pull Request Process

1. **Fork and Clone**: Fork the repository and clone locally
2. **Create Branch**: Use descriptive branch names (e.g., `feature/add-new-distribution`)
3. **Make Changes**: Implement your feature or fix
4. **Add Tests**: Include tests for new functionality
5. **Update Docs**: Update relevant documentation
6. **Run Tests**: Ensure all tests pass
7. **Commit**: Use clear, atomic commits
8. **Push**: Push to your fork
9. **PR**: Open a pull request with clear description

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

Examples:
- `Add Beta distribution support for Monte Carlo`
- `Fix NPV calculation in edge cases`
- `Update documentation for version 2.0.0`
- `Refactor adoption model for better performance`

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-impact-model.git
cd ai-impact-model

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8

# Run tests to verify setup
python -m pytest
```

## Areas for Contribution

### High Priority
- Additional probability distributions
- More industry-specific baselines
- Enhanced visualization options
- API endpoints for integration
- Dashboard web interface

### Medium Priority
- Additional export formats
- More sophisticated adoption models
- Industry benchmark data
- Automated parameter tuning
- Cloud deployment options

### Low Priority
- Internationalization support
- Historical data import
- Alternative calculation methods
- Performance optimizations
- Additional test coverage

## Getting Help

- Open an issue for bugs or feature requests
- Use discussions for questions
- Check existing issues before creating new ones
- Provide minimal reproducible examples for bugs