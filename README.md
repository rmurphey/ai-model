# AI-Assisted Development Business Impact Model

A comprehensive model for understanding the business impact of AI-assisted software development tools on organizational outcomes.

## Overview

This model provides a data-driven framework for evaluating the ROI of AI development tools by considering:
- Realistic adoption curves with dropout and learning effects
- Multi-dimensional value creation (time, quality, capacity, strategic)
- Complete cost structure (licensing, tokens, training, hidden costs)
- Risk scenarios and sensitivity analysis
- Team composition and seniority effects

## Quick Start

```bash
# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Using the Claude command (recommended)
claude analyze moderate_enterprise
claude analyze --compare
claude analyze --list

# Or using Python directly
python main.py --scenario moderate_enterprise
python main.py --compare

# Using the analysis script with export options
python run_analysis.py moderate_enterprise
python run_analysis.py --output my_report.txt moderate_enterprise
python run_analysis.py --compare all

# NEW: Performance-Enhanced Features
# Configuration caching for faster repeated runs
python main.py --scenario moderate_enterprise --cache-stats
python main.py --scenario moderate_enterprise --no-cache  # Disable caching

# Sensitivity analysis to understand parameter importance
python run_analysis.py --sensitivity moderate_enterprise
python run_analysis.py --sensitivity moderate_enterprise --sensitivity-samples 1024

# Batch processing for multiple scenarios in parallel
python run_analysis.py --batch src/batch/batch_config.yaml
python run_analysis.py --batch my_batch.yaml --batch-workers 8

# Reproducing results from existing reports
python reproduce_results.py outputs/reports/analysis_20250820_185901.md
python reproduce_results.py --validate reports/*.md
python reproduce_results.py --tolerance 0.01 reports/
```

## Project Structure

```
├── main.py                     # Main entry point
├── run_analysis.py             # Analysis script with export functionality
├── reproduce_results.py        # Result reproduction and validation tool
├── version_manager.py          # Version management CLI tool
├── requirements.txt            # Dependencies (includes colorama for colors)
├── .claude/
│   └── commands/
│       ├── analyze             # Claude command executable
│       └── analyze.md          # Command documentation
├── src/
│   ├── model/                 # Core model components
│   │   ├── baseline.py        # Baseline metrics
│   │   ├── adoption_dynamics.py # Adoption patterns
│   │   ├── impact_model.py    # Value calculations
│   │   ├── cost_structure.py  # Cost modeling
│   │   ├── monte_carlo.py     # Monte Carlo simulation engine
│   │   ├── monte_carlo_viz.py # Monte Carlo visualizations
│   │   └── visualizations.py  # Text-based utilities
│   ├── config/                # Configuration and versioning
│   │   ├── constants.py       # System constants
│   │   └── version.py         # Version management and compatibility
│   ├── versioning/            # Version adaptation system
│   │   └── version_adapter.py # Cross-version compatibility adapters
│   ├── utils/                 # Utility modules
│   │   ├── colors.py          # Console color formatting
│   │   └── cache.py           # Caching utilities for performance
│   ├── scenarios/             # Modular scenario configurations
│   │   ├── scenarios.yaml     # Legacy scenario definitions
│   │   ├── scenario_loader.py # Modular scenario loading system
│   │   ├── profiles/          # Company profile definitions
│   │   ├── strategies/        # Adoption strategy definitions
│   │   └── README.md          # Scenario system documentation
│   ├── batch/                 # Batch processing system
│   │   ├── batch_processor.py # Parallel batch execution engine
│   │   └── batch_config.yaml  # Example batch configuration
│   ├── reproducibility/       # Result reproduction system
│   │   ├── reproduction_engine.py  # Core reproduction logic
│   │   └── validators.py      # Validation framework
│   └── analysis/              # Additional analysis tools
│       ├── terminal_visualizations.py
│       ├── sensitivity_analysis.py  # Sobol indices and sensitivity
│       ├── generate_scenario_matrix.py
│       └── save_results.py
├── outputs/
│   ├── charts/               # PNG visualizations (legacy)
│   ├── reports/              # Text analysis reports
│   └── data/                 # CSV data exports
└── venv/                     # Virtual environment
```

## Model Components

### 1. Baseline Metrics (`src/model/baseline.py`)
Establishes current state before AI adoption:
- Team composition and fully-loaded costs
- Current delivery metrics (cycle time, defect rates)
- Capacity allocation (features vs. maintenance)
- Quality baselines (incidents, rework)

### 2. Adoption Dynamics (`src/model/adoption_dynamics.py`)
Models realistic adoption patterns:
- S-curve adoption with segment-specific rates
- Learning curves and efficiency gains
- Dropout and re-engagement patterns
- Network effects and peer influence

### 3. Impact Model (`src/model/impact_model.py`)
Calculates business value across dimensions:
- **Time Value**: Faster feature delivery, bug fixes, onboarding
- **Quality Value**: Fewer defects, incidents, less rework
- **Capacity Value**: More time on strategic work
- **Strategic Value**: Innovation, retention, competitive advantage

### 4. Cost Structure (`src/model/cost_structure.py`)
Comprehensive cost modeling:
- Per-seat licensing with enterprise discounts
- Token consumption with price evolution
- Training and change management
- Hidden costs (context switching, bad code cleanup)

### 5. Text-Based Utilities (`src/model/visualizations.py`)
Console-friendly reporting utilities:
- Formatted summary tables
- ASCII charts and timelines  
- Currency and percentage formatting
- Executive summary generation
- Text-based cost and value breakdowns

## Key Insights

### Value Creation Vectors
Instead of abstract "productivity gains," the model measures:
- **Cycle Time Reduction**: Days from requirement to production
- **Quality Improvements**: Defect and incident reduction
- **Capacity Reallocation**: Strategic vs. maintenance work
- **Knowledge Democratization**: Junior developers becoming more effective

### Adoption Realism
- Not everyone adopts immediately or successfully
- Learning curves affect initial efficiency
- Different tasks benefit differently from AI assistance
- Seniority affects both adoption rate and value gained

### Cost Evolution
- Token prices decline over time (20-30% annually)
- Usage patterns evolve (growth then plateau)
- Training costs front-loaded
- Hidden costs in early months

## Scenarios

### Pre-configured Scenarios

1. **Conservative Startup**: Small team, organic adoption, modest gains
2. **Moderate Enterprise**: Large team, mandated adoption, balanced impact
3. **Aggressive Scale-up**: Fast-growing team, grassroots adoption, high impact
4. **Custom**: Fully configurable parameters

### Customizing Scenarios

Edit `src/scenarios/scenarios.yaml` to define your own scenarios:

```yaml
my_scenario:
  name: "My Custom Scenario"
  baseline:
    team_size: 40
    junior_ratio: 0.3
    mid_ratio: 0.5
    senior_ratio: 0.2
    # ... more parameters
  adoption:
    scenario: "organic"  # or specify custom parameters
  impact:
    feature_cycle_reduction: 0.25
    # ... more parameters
  costs:
    cost_per_seat_month: 45
    # ... more parameters
  timeframe_months: 24
```

## Claude Command and Export Functionality

### Claude Command Usage

The repository includes a native Claude command for streamlined analysis:

```bash
# Single scenario analysis
claude analyze moderate_enterprise

# Compare standard scenarios (conservative_startup, moderate_enterprise, aggressive_scaleup)
claude analyze --compare

# List all available scenarios
claude analyze --list

# Multiple scenario analysis
claude analyze startup enterprise scaleup

# Custom output filename
claude analyze --output my_report.txt moderate_enterprise
```

### Export and Output Options

#### Automatic Report Generation
All analyses automatically generate timestamped reports in `outputs/reports/`:
- **Filename format**: `analysis_YYYYMMDD_HHMMSS.txt`
- **Custom names**: Use `--output filename.txt` for custom naming
- **Content**: Executive summaries, financial metrics, value breakdowns

#### Report Contents and Formatting
Each exported report includes:
- **Executive Summary**: Key metrics, NPV, ROI, breakeven analysis
- **Financial Breakdown**: 3-year investment vs value, per-developer costs
- **Value Analysis**: Time, quality, capacity, and strategic value components
- **Adoption Metrics**: Peak adoption rates, efficiency curves
- **Opportunity Cost Analysis**: Current inefficiency vs AI tool value capture

**Output Formats:**
- **Saved Files**: Clean markdown format with headers, lists, and formatting
- **Console Output**: Colorful plaintext with ANSI colors for readability
  - 🟢 Green for positive metrics (NPV, value, gains)
  - 🔴 Red for costs and negative values
  - 🔵 Blue for headers and section titles
  - 🟡 Yellow for percentages and warnings
  - 🔷 Cyan for file paths and highlights

#### Direct Script Usage
For more control, use the analysis script directly:

```bash
# Basic analysis with auto-generated filename
python run_analysis.py moderate_enterprise

# Custom output file
python run_analysis.py --output quarterly_analysis.txt moderate_enterprise

# Multiple scenarios in one report
python run_analysis.py startup enterprise scaleup

# Comparison mode
python run_analysis.py --compare all

# List available scenarios
python run_analysis.py --list
```

## Interpreting Results

### Key Metrics

- **NPV**: Net present value of the investment
- **Breakeven Month**: When cumulative value exceeds costs
- **Peak Adoption**: Maximum adoption rate achieved
- **Value per Developer**: Annual value created per adopted developer

### Risk Considerations

The model accounts for:
- Adoption failure (laggards who never adopt)
- Dropout rates (users who stop using tools)
- Bad AI code requiring cleanup
- Context switching during adoption

## New Performance Features (v1.1.0+)

### Configuration Caching
Improves performance by caching scenario configurations and results:
- **40% faster** repeated runs with automatic result caching
- Cache statistics tracking (hits, misses, time saved)
- Configurable TTL (time-to-live) for cache entries
- Environment variable control: `AI_IMPACT_CACHE_ENABLED=false` to disable

```bash
# View cache performance
python main.py --scenario moderate_enterprise --cache-stats

# Disable caching for fresh calculations
python main.py --scenario moderate_enterprise --no-cache
```

### Sensitivity Analysis
Understand which parameters most influence your results:
- **Sobol indices** for global sensitivity analysis
- First-order effects (main effects) and total effects (including interactions)
- Partial dependence plots for parameter relationships
- Convergence metrics to ensure reliable results

```bash
# Run sensitivity analysis with default 512 samples
python run_analysis.py --sensitivity moderate_enterprise

# High-precision analysis with 2048 samples
python run_analysis.py --sensitivity moderate_enterprise --sensitivity-samples 2048
```

Output includes:
- Ranked parameter importance
- Variance explained by each parameter
- Interaction effects between parameters
- Tornado charts for visualization

### Batch Processing
Process multiple scenarios in parallel for comprehensive analysis:
- **Parallel execution** with configurable worker count
- Progress tracking with real-time updates
- Automatic comparison report generation
- Individual and aggregate result saving

```bash
# Use example batch configuration
python run_analysis.py --batch src/batch/batch_config.yaml

# Custom batch with specific worker count
python run_analysis.py --batch my_scenarios.yaml --batch-workers 8
```

Batch configuration example:
```yaml
scenarios:
  - conservative_startup
  - moderate_enterprise
  - aggressive_scaleup
parallel_workers: 4
output_dir: outputs/batch
generate_comparison: true
save_individual_reports: true
```

## Result Reproduction and Validation

### Overview

Every analysis report generated by this tool includes comprehensive metadata that enables exact reproduction of results. This ensures research integrity, enables collaboration, and provides an audit trail for business-critical analyses.

### Reproducing Results from Reports

All generated markdown reports embed complete reproduction information. Use the dedicated reproduction tool to validate and reproduce results:

```bash
# Reproduce results from a single report
python reproduce_results.py outputs/reports/analysis_20250820_185901.md

# Validate multiple reports with detailed output
python reproduce_results.py --validate --detailed reports/*.md

# Batch validation with custom tolerance
python reproduce_results.py --tolerance 0.02 outputs/reports/

# Summary mode for large report sets
python reproduce_results.py --summary outputs/reports/
```

### Reproduction Features

**Automatic Metadata Extraction**
- Extracts scenario configurations from embedded YAML
- Recovers all resolved parameter values
- Validates checksums and version compatibility

**Intelligent Validation**
- Configurable tolerance levels for numerical comparisons
- Handles floating-point precision differences
- Scenario-specific validation rules
- Confidence scoring and detailed difference reporting

**Comprehensive Reporting**
- Side-by-side comparison of original vs reproduced results
- Root cause analysis for significant differences
- Confidence scores and reproduction quality metrics
- Recommendations for improving reproducibility

### Validation Configuration

Customize validation behavior for specific use cases:

```python
from src.reproducibility.validators import create_validation_config

# Strict validation for critical analyses
strict_config = create_validation_config(tolerance=0.005, strict=True)

# Custom rules for specific metrics
custom_rules = {
    "npv": {"tolerance": 0.02, "type": "percentage"},
    "breakeven_month": {"tolerance": 0, "type": "exact"}
}
config = create_validation_config(custom_rules=custom_rules)
```

### Understanding Results

**Success Indicators:**
- ✅ **High Confidence (95%+)**: All critical metrics match within tolerance
- ⚠️ **Moderate Confidence (80-95%)**: Minor differences, likely due to precision
- ❌ **Low Confidence (<80%)**: Significant differences requiring investigation

**Common Difference Causes:**
- Floating-point precision variations
- Random seed differences (if applicable)
- Dependency version changes
- Model improvements or bug fixes

### Integration with CI/CD

Validate historical reports in automated pipelines:

```bash
# In your CI pipeline
python reproduce_results.py --validate --quiet reports/ || exit 1
```

## Monte Carlo Simulation

### Overview

The model supports **Monte Carlo simulation** for probabilistic business impact analysis. Instead of single point estimates, Monte Carlo runs thousands of simulations with parameter uncertainty to provide confidence intervals and risk assessment.

### Key Features

- **Probability distributions** for all model parameters
- **Confidence intervals** for NPV, ROI, and breakeven analysis  
- **Risk metrics** including probability of positive NPV
- **Sensitivity analysis** to identify high-impact parameters
- **Correlation support** between related parameters

### Running Monte Carlo Analysis

```bash
# Basic Monte Carlo simulation (1000 iterations)
python main.py --monte-carlo --scenario moderate_enterprise

# Custom iterations and confidence level
python main.py --monte-carlo --scenario startup --iterations 5000 --confidence 0.99

# With reproducible random seed
python main.py --monte-carlo --scenario enterprise --seed 42

# Using Monte Carlo scenario definitions
python main.py --monte-carlo --scenario-file src/scenarios/scenarios_monte_carlo.yaml
```

### Defining Uncertainty in Scenarios

Parameters can have probability distributions instead of fixed values:

```yaml
# Example: Triangular distribution for cycle time
avg_feature_cycle_days:
  value: 30  # Used in deterministic mode
  distribution:
    type: triangular
    min: 25
    mode: 30
    max: 40

# Example: Normal distribution for reduction factor
feature_cycle_reduction:
  value: 0.3
  distribution:
    type: normal
    mean: 0.3
    std: 0.05
    min: 0.1  # Optional bounds
    max: 0.5

# Example: Beta distribution for rates
adoption_rate:
  value: 0.7
  distribution:
    type: beta
    alpha: 7
    beta: 3
```

### Available Distributions

- **Normal**: For symmetric uncertainty (`mean`, `std`)
- **Triangular**: When min/likely/max are known (`min`, `mode`, `max`)
- **Beta**: For rates and percentages (`alpha`, `beta`)
- **Uniform**: Equal probability in range (`min`, `max`)
- **LogNormal**: For costs and durations (`mean_log`, `std_log`)
- **Deterministic**: Fixed value (no distribution)

### Parameter Correlations

Define relationships between parameters:

```yaml
correlations:
  - param1: impact.feature_cycle_reduction
    param2: impact.bug_fix_reduction
    correlation: 0.7  # Positive correlation
    
  - param1: costs.cost_per_seat_month
    param2: costs.training_cost_per_user
    correlation: 0.3
```

### Monte Carlo Output

The simulation provides:

**Distribution Statistics:**
- Mean, median, standard deviation
- Percentiles (P5, P10, P25, P50, P75, P90, P95)
- Confidence intervals (default 95%)

**Risk Metrics:**
- Probability of positive NPV
- Probability of breakeven within target timeframe
- Probability of achieving ROI target
- Value at Risk (VaR) analysis

**Sensitivity Analysis:**
- Parameter correlations with outcomes
- Ranked parameter importance
- Identifies key risk drivers

### Example Output

```
MONTE CARLO RESULTS
Iterations: 1000
Convergence: ✓ Achieved
Runtime: 12.3 seconds

NPV DISTRIBUTION
Mean                 $2,456,789
Median (P50)         $2,398,234
Std Deviation        $523,456
P10                  $1,789,012
P90                  $3,234,567
95% CI               [$1,567,890, $3,456,789]

RISK ANALYSIS
Prob(NPV > 0)                    95.3%
Prob(Breakeven < 24 months)      87.2%
Prob(ROI > 100%)                 78.9%

TOP 5 SENSITIVITY DRIVERS
1. impact.feature_cycle_reduction        ↑ 0.823
2. adoption.plateau_efficiency           ↑ 0.756
3. costs.cost_per_seat_month            ↓ 0.612
4. impact.defect_reduction              ↑ 0.589
5. adoption.dropout_rate_month          ↓ 0.412
```

## Model Versioning

### Overview

The analysis tool implements a comprehensive versioning system to ensure reproducibility across different versions of the model. As the model evolves, different versions may produce different results due to improvements, bug fixes, or algorithmic changes. The versioning system handles these differences transparently while maintaining backward compatibility.

### Version Format

Versions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes that may significantly affect results
- **MINOR**: New features or improvements with backward compatibility
- **PATCH**: Bug fixes and minor adjustments

Current version: **v1.0.0**

### Version Compatibility

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

### Version Detection

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

### Tolerance Adjustment

Tolerance levels are automatically adjusted based on version compatibility:

| Version Relationship | Default Tolerance | Rationale |
|---------------------|------------------|-----------|
| Same version (1.0.0 → 1.0.0) | 0.001 | Exact reproduction expected |
| Minor update (1.0.0 → 1.1.0) | 0.02 | Small improvements may affect results |
| Major update (1.x → 2.x) | 0.05 | Significant changes, adaptation applied |

### Version Adaptation

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

### Creating New Versions

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

### Working with Different Versions

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

### Version History and Migration

**Version 1.0.0** (Current)
- Initial stable release
- Baseline model with comprehensive business impact calculations
- Full reproduction system implementation

**Future Versions**
When new versions are released:
1. **Backward Compatibility**: Older reports remain reproducible
2. **Migration Guides**: Documentation for significant changes
3. **Adaptation Rules**: Automatic configuration updates
4. **Validation Tests**: Extensive testing of version transitions

### Best Practices

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

### Troubleshooting Version Issues

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

## Advanced Usage

### Programmatic Analysis

```python
from main import AIImpactModel

# Initialize model
model = AIImpactModel()

# Run specific scenario
results = model.run_scenario("moderate_enterprise")
model.print_summary(results)

# Compare multiple scenarios
for scenario in ["conservative_startup", "moderate_enterprise", "aggressive_scaleup"]:
    model.run_scenario(scenario)
model.compare_scenarios()
```

### Programmatic Reproduction

```python
from src.reproducibility.reproduction_engine import ReproductionEngine

# Initialize reproduction engine
engine = ReproductionEngine()

# Reproduce results from report
result = engine.reproduce_from_report("path/to/report.md", tolerance=0.01)

if result.success:
    print(f"Reproduction successful! Confidence: {result.confidence_score:.1%}")
else:
    print("Reproduction failed:")
    for scenario, differences in result.differences.items():
        print(f"  {scenario}: {differences}")
```

### Custom Analysis Scripts

The `src/analysis/` directory contains additional analysis tools:
- `terminal_visualizations.py` - Console-based charts and graphs
- `generate_scenario_matrix.py` - Batch scenario analysis
- `save_results.py` - Export utilities for different formats
- `scaleup_analysis.py` - Growth-focused analysis patterns

The `src/reproducibility/` directory contains reproduction tools:
- `reproduction_engine.py` - Core reproduction and validation logic
- `validators.py` - Configurable validation framework

## Model Assumptions

1. **Fully-loaded costs** include salary, benefits, and overhead
2. **Feature value** approximated by cost to develop
3. **Learning curves** follow exponential improvement
4. **Token prices** decline predictably over time
5. **Network effects** accelerate adoption at critical mass

## Limitations

- Does not model competitive dynamics explicitly
- Assumes stable team size (can be modified)
- Quality improvements are estimates, not guarantees
- Strategic value is hardest to quantify precisely

## Contributing

This model is designed to be extended. Key extension points:
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

### Reproduction System Guidelines

When contributing to the reproduction system:
1. **Maintain backward compatibility** - existing reports should remain reproducible
2. **Add version information** - include version metadata in new features  
3. **Test thoroughly** - add test cases for new validation rules
4. **Document changes** - update reproduction guidelines for breaking changes
5. **Validate existing reports** - run reproduction tests before committing changes

### Versioning Guidelines

When making changes that affect model results:
1. **Version Bumps**: Follow semantic versioning principles
   - **PATCH**: Bug fixes that don't change results significantly
   - **MINOR**: New features or improvements with backward compatibility
   - **MAJOR**: Breaking changes that significantly affect results

2. **Version Adapters**: Create adapters for cross-version compatibility
   - Add new adapter classes in `src/versioning/version_adapter.py`
   - Register adapters in the version registry
   - Test adaptation logic thoroughly

3. **Testing Requirements**:
   - Run full test suite: `python -m unittest tests.test_version_management tests.test_version_reproduction`
   - Validate historical reports: `python reproduce_results.py --validate outputs/reports/`
   - Test version transitions between old and new versions

4. **Documentation Updates**:
   - Update version history in README.md
   - Document breaking changes and migration paths
   - Add examples for new version-specific features

## License

MIT