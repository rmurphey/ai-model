# CI/CD Testing Guide

## Overview

This repository uses GitHub Actions to automatically run comprehensive tests for all code changes, ensuring the integrity of financial modeling calculations and preventing regression in business-critical functionality.

## Test Coverage Summary

### 🎯 **Core Business Logic (109 Tests)**
- **Impact Model**: 26 tests covering value calculations (time, quality, capacity, strategic)
- **Cost Structure**: 30 tests covering financial modeling (licensing, tokens, training, hidden costs)
- **Adoption Dynamics**: 27 tests covering adoption curves (S-curve, Bass diffusion, efficiency learning)
- **Baseline Metrics**: 26 tests covering team composition and efficiency calculations

### 🛠️ **Utility & Integration Tests**
- **Math Helpers**: Safe division, validation, percentage calculations
- **Exception Handling**: User-friendly error messages with resolution steps
- **Validation Helpers**: Parameter validation and business logic checks
- **Integration Tests**: End-to-end workflow validation

## Workflows

### 1. **Main Test Workflow** (`.github/workflows/test.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch
- Manual workflow dispatch

**Features:**
- **Multi-version testing**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Dependency caching**: Faster builds with pip cache
- **Coverage reporting**: XML and HTML coverage reports
- **Test artifacts**: Downloadable test reports for each Python version
- **Codecov integration**: Coverage tracking and PR comments

**Test Execution:**
```bash
# Core business logic tests (critical path)
pytest tests/test_impact_model.py tests/test_cost_structure.py \
       tests/test_adoption_dynamics.py tests/test_baseline.py \
       --cov=src.model --cov-report=xml --cov-report=html

# Utility and integration tests
pytest tests/test_math_helpers.py tests/test_exceptions.py \
       tests/test_validation_helpers.py tests/test_scenario_loading.py \
       tests/test_integration.py --cov=src.utils --cov=src.analysis
```

### 2. **Pull Request Workflow** (`.github/workflows/test-pr.yml`)

**Optimized for Speed:**
- **Quick validation**: Python 3.11 only for faster feedback
- **Critical tests only**: Core business logic tests
- **Import integrity**: Verify module imports work correctly
- **Code quality**: Linting and formatting checks (non-blocking)

**Benefits:**
- **Fast feedback**: ~2-3 minutes vs ~8-10 minutes for full matrix
- **Early error detection**: Catches breaking changes immediately
- **PR summaries**: Automatic test result summaries in PR comments

## Quality Gates

### **Coverage Requirements**
- **Minimum**: 85% coverage for core business logic (`src.model`)
- **Target**: 90%+ coverage for financial calculations
- **Monitored**: All critical calculation paths must be tested

### **Test Categories**
- **🔴 Critical**: Must pass - business logic calculations
- **🟡 Important**: Should pass - utility functions and validation
- **🟢 Optional**: May skip - Monte Carlo simulations (marked with `@pytest.mark.skip`)

### **Success Criteria**
✅ All core business logic tests pass across Python versions  
✅ No breaking changes to financial calculations  
✅ Import integrity maintained  
✅ Coverage threshold met (85%+)  
✅ Code quality checks pass (warnings allowed)

## Local Testing

### **Run CI Tests Locally**
```bash
# Install CI dependencies
pip install pytest-cov pytest-html pytest-xdist

# Run core business logic tests (matches CI)
pytest tests/test_impact_model.py tests/test_cost_structure.py \
       tests/test_adoption_dynamics.py tests/test_baseline.py \
       --cov=src.model --cov-report=html --html=outputs/test-report.html

# Run quick PR validation
pytest tests/test_impact_model.py tests/test_cost_structure.py \
       tests/test_adoption_dynamics.py tests/test_baseline.py \
       --cov=src.model --cov-report=term-missing --cov-fail-under=85
```

### **Test Configuration**
The `pytest.ini` file configures:
- Test discovery patterns
- Coverage settings
- Warning filters
- Custom markers
- Output formatting

## Branch Protection

### **Required Status Checks**
- `test (3.9)` through `test (3.13)` - Full test matrix
- `quick-test` - PR validation
- `test-import-integrity` - Module import verification  
- `lint-and-format` - Code quality (warnings allowed)

### **Setup Instructions**
See `.github/BRANCH_PROTECTION.md` for detailed setup guide.

## Troubleshooting

### **Common Issues**

#### 1. **Tests Fail on One Python Version**
```bash
# Check compatibility issues
pytest tests/ -v --tb=long --python-version=3.x

# Common fixes:
- Update requirements.txt with compatible versions
- Check for f-string compatibility (3.6+)
- Verify dataclass usage (3.7+)
```

#### 2. **Coverage Below Threshold**
```bash
# Generate detailed coverage report
pytest --cov=src.model --cov-report=html --cov-report=term-missing

# Open htmlcov/index.html to see uncovered lines
# Add tests for missing coverage areas
```

#### 3. **Import Errors in CI**
```bash
# Test imports locally
python -c "from src.model.impact_model import BusinessImpact"

# Common fixes:
- Check __init__.py files exist
- Verify PYTHONPATH includes project root
- Update relative imports if needed
```

#### 4. **Flaky Monte Carlo Tests**
Monte Carlo tests are skipped by default (`@pytest.mark.skip`) due to random variations. To run them locally:
```bash
pytest tests/test_adoption_dynamics.py::TestSimulateAdoptionMonteCarlo -v
```

### **Performance Optimization**

#### **Parallel Testing**
```bash
# Run tests in parallel (local only)
pytest tests/ -n auto --dist=worksteal
```

#### **Test Selection**
```bash
# Run only critical tests
pytest tests/test_impact_model.py tests/test_cost_structure.py

# Run by marker
pytest -m "not slow" tests/

# Run specific test patterns
pytest -k "test_calculate_" tests/
```

## Monitoring & Alerts

### **GitHub Checks**
- All status checks must pass before merge
- Failed tests block PR merging
- Coverage reports attached to PRs

### **Notifications**
- PR authors notified of test failures
- Repository admins alerted to main branch failures
- Codecov provides coverage change notifications

## Maintenance

### **Regular Tasks**
- **Monthly**: Update Python versions in test matrix
- **Quarterly**: Review and update dependency versions
- **As needed**: Add tests for new functionality

### **Dependency Updates**
```bash
# Check for outdated packages
pip list --outdated

# Update testing dependencies
pip install --upgrade pytest pytest-cov pytest-html

# Test compatibility
pytest tests/ --tb=short
```

### **Adding New Tests**
1. Follow existing test patterns in `tests/test_*.py`
2. Use descriptive test names and docstrings
3. Test both happy path and edge cases
4. Include validation for mathematical accuracy
5. Add markers for slow tests: `@pytest.mark.slow`

## Security Considerations

- **No secrets in workflows**: All configuration is public
- **Dependency scanning**: Dependabot alerts for vulnerabilities
- **Code review required**: All changes must be reviewed
- **Branch protection**: Direct pushes to main blocked

## Performance Metrics

### **Typical Execution Times**
- **PR Quick Test**: ~2-3 minutes
- **Full Test Matrix**: ~8-10 minutes  
- **Core Business Logic**: ~30-45 seconds
- **All Tests**: ~60-90 seconds

### **Resource Usage**
- **Memory**: ~200-300MB per test worker
- **CPU**: Utilizes all available cores in parallel
- **Storage**: ~50MB for artifacts per build