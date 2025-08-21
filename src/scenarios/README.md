# Scenario Configuration Guide

This directory contains all scenario configurations for the AI Impact Model. Scenarios can be organized in two ways:

1. **Legacy Format**: Single YAML files containing all scenarios
2. **Modular Format**: Organized directory structure with reusable components

## Directory Structure

```
scenarios/
├── README.md                    # This file
├── scenarios.yaml              # Legacy deterministic scenarios (backward compatibility)
├── scenarios_monte_carlo.yaml  # Legacy Monte Carlo scenarios (backward compatibility)
├── profiles/                   # Company profiles (reusable base configurations)
│   ├── startup.yaml           # 10-person startup configuration
│   ├── scaleup.yaml          # 25-person scaleup configuration
│   └── enterprise.yaml       # 50-person enterprise configuration
├── strategies/                 # Adoption and impact strategies
│   ├── conservative.yaml     # Risk-averse approach
│   ├── moderate.yaml         # Balanced approach
│   └── aggressive.yaml       # Optimistic approach
├── distributions/             # Uncertainty distributions for Monte Carlo
│   ├── low_uncertainty.yaml  # Narrow uncertainty ranges
│   ├── medium_uncertainty.yaml # Moderate uncertainty
│   └── high_uncertainty.yaml # Wide uncertainty ranges
└── scenarios/                 # Complete scenario definitions
    ├── deterministic/        # Point-estimate scenarios
    │   └── *.yaml
    └── monte_carlo/         # Probabilistic scenarios
        └── *.yaml
```

## Using Modular Scenarios

### Simple Composition

Scenarios can extend from profiles and strategies:

```yaml
# scenarios/deterministic/moderate_enterprise.yaml
name: Moderate Enterprise
description: Enterprise team with balanced AI adoption

extends:
  - profiles/enterprise      # Base company profile
  - strategies/moderate      # Adoption strategy

# Override specific values
adoption:
  scenario: organic

timeframe_months: 36
```

### With Distributions (Monte Carlo)

Add uncertainty distributions for Monte Carlo analysis:

```yaml
# scenarios/monte_carlo/moderate_enterprise.yaml
name: Moderate Enterprise with Uncertainty
description: Enterprise with probabilistic modeling

extends:
  - profiles/enterprise
  - strategies/moderate
  - distributions/medium_uncertainty

# Override with specific distributions
baseline:
  avg_feature_cycle_days:
    value: 21
    distribution:
      type: triangular
      min: 18
      mode: 21
      max: 28
```

## Component Types

### Profiles (`profiles/*.yaml`)

Define company-specific baseline metrics:
- Team size and composition
- Compensation levels
- Development metrics (cycle times, quality)
- Capacity allocation
- Delivery rates

### Strategies (`strategies/*.yaml`)

Define adoption approach and expected impacts:
- Adoption curve parameters
- Learning dynamics
- Impact factors (time/quality improvements)
- Cost parameters
- Task effectiveness multipliers

### Distributions (`distributions/*.yaml`)

Define uncertainty ranges for parameters:
- Distribution types (normal, triangular, beta, etc.)
- Confidence bounds
- Parameter correlations

## Creating New Scenarios

### Option 1: Extend Existing Components

1. Create a new file in `scenarios/deterministic/` or `scenarios/monte_carlo/`
2. Use `extends` to compose from existing profiles and strategies
3. Override specific values as needed

```yaml
name: My Custom Scenario
extends:
  - profiles/startup
  - strategies/aggressive
  
# Custom overrides
baseline:
  team_size: 15  # Override default startup size
```

### Option 2: Standalone Scenario

Create a complete scenario without extending:

```yaml
name: Standalone Scenario
description: Complete configuration

baseline:
  team_size: 30
  # ... all baseline metrics

adoption:
  # ... all adoption parameters

impact:
  # ... all impact factors

costs:
  # ... all cost parameters

timeframe_months: 24
```

## Distribution Types for Monte Carlo

### Triangular
Best for parameters with clear min/likely/max values:
```yaml
parameter:
  value: 30  # Deterministic value
  distribution:
    type: triangular
    min: 20
    mode: 30
    max: 40
```

### Normal
For symmetric uncertainty:
```yaml
parameter:
  value: 100
  distribution:
    type: normal
    mean: 100
    std: 15
    min: 70   # Optional truncation
    max: 130  # Optional truncation
```

### Beta
For rates and percentages (0-1 bounded):
```yaml
parameter:
  value: 0.7
  distribution:
    type: beta
    alpha: 7
    beta: 3
```

### Uniform
Equal probability across range:
```yaml
parameter:
  value: 1000
  distribution:
    type: uniform
    min: 800
    max: 1200
```

### LogNormal
For costs and durations (positive, right-skewed):
```yaml
parameter:
  value: 1000
  distribution:
    type: lognormal
    mean_log: 6.9  # ln(1000)
    std_log: 0.3
```

## Running Scenarios

### Using Legacy Files
```bash
python main.py --scenario moderate_enterprise
python main.py --monte-carlo --scenario moderate_enterprise_monte_carlo
```

### Using Modular Structure
```bash
python main.py --scenario-dir src/scenarios --scenario moderate_enterprise
python main.py --monte-carlo --scenario-dir src/scenarios --scenario moderate_enterprise
```

## Best Practices

1. **Keep profiles generic**: Focus on company characteristics, not strategy
2. **Keep strategies reusable**: Define approaches that work across company types
3. **Use meaningful names**: `aggressive_enterprise` is clearer than `scenario_3`
4. **Document overrides**: Explain why you're overriding default values
5. **Test compositions**: Ensure extended scenarios produce expected results
6. **Version control**: Track changes to scenarios for reproducibility

## Migration from Legacy

The system supports both formats simultaneously:
- Legacy files (`scenarios.yaml`, `scenarios_monte_carlo.yaml`) continue to work
- New modular scenarios can be added alongside
- Gradual migration is possible - no breaking changes

## Troubleshooting

### Scenario Not Found
- Check file exists in correct directory
- Verify naming convention (deterministic vs monte_carlo)
- Use `--list-scenarios` to see available scenarios

### Composition Errors
- Ensure referenced profiles/strategies exist
- Check YAML syntax in all extended files
- Verify no circular dependencies

### Distribution Issues
- Ensure distribution parameters are valid
- Check min < mode < max for triangular
- Verify alpha, beta > 0 for beta distribution