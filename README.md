# AI-Assisted Development Business Impact Model

A data-driven framework for evaluating the ROI of AI development tools in your organization.

## Features

✨ **Interactive Mode** - Guided scenario creation with 5-question quick setup  
📊 **Monte Carlo Simulation** - Probabilistic analysis with confidence intervals  
🔄 **Result Reproduction** - Validate and reproduce any historical analysis  
⚡ **Performance Optimized** - Caching, parallel processing, batch analysis  
📈 **Sensitivity Analysis** - Identify which parameters matter most  
🎯 **Industry Templates** - Pre-configured scenarios for different company types  
📝 **Comprehensive Reports** - Export to Markdown, JSON, or plain text  
🔍 **Version Management** - Track model evolution and ensure reproducibility  
🔧 **Constraint Solver** - Optimize parameters with business constraints (NEW)

## Quick Start

```bash
# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Interactive mode (recommended for first-time users)
python interactive.py

# Run a pre-configured scenario
python main.py --scenario moderate_enterprise

# Compare scenarios
python main.py --compare

# Monte Carlo simulation
python main.py --monte-carlo --scenario moderate_enterprise
```

## Basic Usage

### Using Claude Commands

```bash
# Analyze a single scenario
claude analyze moderate_enterprise

# Compare multiple scenarios
claude analyze --compare

# Generate comprehensive reports
claude reports enterprise --monte-carlo --format markdown
```

### Using Python Scripts

```bash
# Run analysis with automatic report generation
python run_analysis.py moderate_enterprise

# Custom output location
python run_analysis.py --output quarterly_report.md moderate_enterprise

# Sensitivity analysis
python run_analysis.py --sensitivity moderate_enterprise

# Batch processing
python run_analysis.py --batch src/batch/batch_config.yaml

# Parameter overrides (NEW)
python run_analysis.py aggressive_startup --team-size 50
python run_analysis.py moderate_enterprise --adoption grassroots
python run_analysis.py conservative_startup --impact aggressive --costs enterprise

# Combined overrides
python run_analysis.py aggressive_startup --team-size 50 --adoption mandated --impact aggressive
```

### Parameter Override Options

You can customize any scenario without creating new YAML files using command-line overrides:

- **`--team-size N`**: Override team size (e.g., 10, 50, 100, 200)
- **`--adoption`**: Override adoption scenario
  - `organic`: Natural, peer-driven adoption (5% initial, 15% early adopters)
  - `mandated`: Management-driven adoption (20% initial, 30% early adopters)
  - `grassroots`: Bottom-up developer-led (10% initial, 20% early adopters)
- **`--impact`**: Override impact scenario
  - `conservative`: Cautious estimates (10-20% improvements)
  - `moderate`: Balanced projections (25-35% improvements)
  - `aggressive`: Optimistic targets (40-50% improvements)
- **`--costs`**: Override costs scenario
  - `startup`: Low budget ($30/seat, 200K tokens/month)
  - `enterprise`: Higher investment ($50/seat, 500K tokens/month)
  - `aggressive`: Premium tier ($100/seat, 1M tokens/month)

## Pre-configured Scenarios

- **Conservative Startup**: Small team (5-20), organic adoption, modest gains
- **Moderate Enterprise**: Large team (50-100), mandated adoption, balanced impact
- **Aggressive Scale-up**: Fast-growing team (20-50), grassroots adoption, high impact
- **Custom**: Fully configurable parameters via interactive mode or YAML

## Constraint-Based Optimization (NEW)

### Parameter Optimization
Find optimal parameters given business constraints:

```bash
# Maximize NPV with budget constraint
python optimize.py --objective max_npv --budget 10000

# Maximize ROI with team size constraints
python optimize.py --objective max_roi --min-team 10 --max-team 50

# Balanced optimization with multiple constraints
python optimize.py --objective balanced --budget 20000 --min-roi 2.0

# Minimize cost while maintaining minimum ROI
python optimize.py --objective min_cost --min-roi 1.5
```

### Constraint Validation
Validate scenarios against business constraints:

```bash
# Validate a specific scenario
python validate_constraints.py moderate_enterprise

# Validate all scenarios
python validate_constraints.py --all

# Detailed validation with warnings
python validate_constraints.py --all --verbose

# Strict mode (treat warnings as errors)
python validate_constraints.py --all --strict
```

### Available Constraints
- **Budget**: Maximum monthly/total cost limits
- **Team Size**: Minimum/maximum team size bounds
- **Team Composition**: Valid role distribution ratios
- **Adoption**: Realistic adoption rates and plateaus
- **Impact**: Maximum feasible improvement percentages
- **ROI**: Minimum acceptable return thresholds
- **Timeframe**: Analysis period constraints

### Optimization Objectives
- `max_npv`: Maximize Net Present Value
- `max_roi`: Maximize Return on Investment
- `min_cost`: Minimize total costs
- `max_adoption`: Maximize adoption success
- `balanced`: Multi-objective balanced optimization

## Project Structure

```
├── main.py                 # Main entry point
├── interactive.py          # Interactive mode
├── run_analysis.py         # CLI analysis tool
├── reproduce_results.py    # Result reproduction
├── optimize.py             # Constraint optimization CLI
├── validate_constraints.py # Constraint validation CLI
├── docs/                   # Documentation
│   ├── technical/         # Technical docs
│   ├── usage/            # Usage guides
│   └── development/      # Developer docs
├── src/
│   ├── model/            # Core model
│   ├── scenarios/        # Configurations
│   ├── interactive/      # Interactive UI
│   ├── analysis/         # Analysis tools
│   └── constraints/      # Constraint solver framework
│       ├── constraint_solver.py      # OR-Tools solver interface
│       ├── business_constraints.py   # Business rules
│       ├── optimization_objectives.py # Optimization goals
│       └── constraint_validator.py   # Validation utilities
└── outputs/              # Generated reports
```

## Documentation

### 📚 Usage Guides
- [Interactive Mode](docs/usage/interactive-mode.md) - Step-by-step interactive analysis
- [Export Options](docs/usage/export-options.md) - Report generation and formats
- [Programmatic Usage](docs/usage/programmatic-usage.md) - API and integration examples

### 🔧 Technical Documentation  
- [Monte Carlo Simulation](docs/technical/monte-carlo.md) - Probabilistic analysis
- [Performance Features](docs/technical/performance.md) - Optimization and caching
- [Reproduction System](docs/technical/reproduction.md) - Result validation
- [Version Management](docs/technical/versioning.md) - Model versioning

### 👩‍💻 Development
- [Model Components](docs/development/model-components.md) - Architecture overview
- [Contributing](docs/development/contributing.md) - How to contribute
- [Assumptions & Limitations](docs/development/assumptions-limitations.md) - Model boundaries
- [Scenario Configuration](src/scenarios/README.md) - Complete parameter reference

## Key Metrics

The model calculates:
- **NPV**: Net present value of the AI investment
- **ROI**: Return on investment percentage
- **Breakeven**: Month when value exceeds costs
- **Adoption Rate**: Peak and average adoption levels
- **Value Breakdown**: Time, quality, capacity, and strategic value
- **Risk Metrics**: Probability of positive NPV (Monte Carlo)

## Example Output

```
=== EXECUTIVE SUMMARY ===
Scenario: Moderate Enterprise (50 developers)

KEY METRICS
NPV (3 years):           $2,456,789
ROI:                     187.3%
Breakeven Month:         14
Peak Adoption:           78.5%

VALUE BREAKDOWN
Time Savings:            $1,234,567 (35%)
Quality Improvements:    $987,654 (28%)
Capacity Gains:          $765,432 (22%)
Strategic Value:         $543,210 (15%)
```





## Testing

The project includes comprehensive test coverage with unit and integration tests. Test scenarios are available for development and testing:

### Test Scenarios

Located in `src/scenarios/`:
- **test_scenario.yaml** - Basic test scenario with full parameter set
- **mc_scenario.yaml** - Monte Carlo test scenario with probability distributions
- **sens_scenario.yaml** - Sensitivity analysis test scenario
- **bad_scenario.yaml** - Invalid scenario for error handling tests
- **scenario1.yaml**, **scenario2.yaml** - Simple scenarios for parallel processing tests

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test modules
python -m pytest tests/test_batch_processor_advanced.py
python -m pytest tests/test_sensitivity_analysis_advanced.py

# Run integration tests (previously skipped, now fixed)
python -m pytest -k "integration"
```

## Contributing

See [Contributing Guide](docs/development/contributing.md) for details on:
- Extension points and architecture
- Development setup
- Testing requirements  
- Pull request process
- Code style guidelines

## License

MIT