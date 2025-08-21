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
│   ├── startup.yaml           # 5-20 person startup configuration
│   ├── scaleup.yaml          # 20-100 person scaleup configuration
│   └── enterprise.yaml       # 101+ person enterprise configuration
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

## Complete Parameter Reference

This section documents all parameters available in scenario YAML files, their meanings, acceptable values, and business impact.

### Baseline Parameters

The baseline section defines the current state of your development organization before AI adoption.

#### Team Composition
```yaml
baseline:
  team_size: 50                    # Number of developers (integer, > 0)
                                   # Startup: 5-20, Scaleup: 20-100, Enterprise: 101+
  
  # Team seniority distribution (must sum to 1.0)
  junior_ratio: 0.3                # Percentage of junior developers (0-1)
  mid_ratio: 0.5                   # Percentage of mid-level developers (0-1)  
  senior_ratio: 0.2                # Percentage of senior developers (0-1)
  
  # Annual fully-loaded costs per developer level (USD)
  junior_flc: 130000               # Junior developer total cost
  mid_flc: 180000                  # Mid-level developer total cost
  senior_flc: 250000               # Senior developer total cost
```

#### Development Metrics
```yaml
baseline:
  # Time-to-delivery metrics
  avg_feature_cycle_days: 21       # Days from requirement to production (> 0)
  avg_bug_fix_hours: 6              # Hours from bug report to fix (> 0)
  onboarding_days: 30               # Days for new dev to be productive (> 0)
  avg_pr_review_hours: 4            # Hours spent per PR review (> 0)
```

#### Quality Metrics
```yaml
baseline:
  # Quality and incident metrics
  defect_escape_rate: 5.0           # Defects per 1000 lines of code (>= 0)
  production_incidents_per_month: 8  # Monthly production incidents (>= 0)
  avg_incident_cost: 10000          # Average cost per incident in USD (>= 0)
  rework_percentage: 0.15           # Percentage of work requiring rework (0-1)
  pr_rejection_rate: 0.2            # Percentage of PRs needing changes (0-1)
```

#### Capacity Allocation
```yaml
baseline:
  # How developers spend their time (should approximately sum to 1.0)
  effective_capacity_hours: 1600    # Annual productive hours per developer
  new_feature_percentage: 0.4       # Time on new features (0-1)
  maintenance_percentage: 0.4       # Time on maintenance (0-1)
  tech_debt_percentage: 0.15        # Time on technical debt (0-1)
  meetings_percentage: 0.05         # Time in meetings/admin (0-1)
  other_percentage: 0.0             # Other activities (0-1)
  
  # Delivery metrics
  feature_delivery_rate: 14         # Features per developer per year (> 0)
```

### Adoption Parameters

The adoption section models how developers adopt and learn AI tools over time.

#### Adoption Segments
Based on Rogers' Diffusion of Innovations, these should sum to 1.0:
```yaml
adoption:
  # Technology adoption curve segments
  initial_adopters: 0.05            # Innovators - adopt immediately (0-1)
  early_adopters: 0.15              # Early adopters - first 3 months (0-1)
  early_majority: 0.35              # Early majority - months 4-9 (0-1)
  late_majority: 0.30               # Late majority - months 10-18 (0-1)
  laggards: 0.15                    # Laggards - very late/never (0-1)
```

#### Adoption Dynamics
```yaml
adoption:
  # Factors influencing adoption speed
  training_effectiveness: 0.5       # How well training drives adoption (0-1)
  peer_influence: 0.7               # Network effect strength (0-1)
  management_mandate: 0.3           # Top-down push effectiveness (0-1)
  
  # Resistance and churn
  initial_resistance: 0.4           # Initial resistance percentage (0-1)
  dropout_rate_month: 0.02          # Monthly dropout/churn rate (0-1)
  re_engagement_rate: 0.03          # Rate dropouts return (0-1)
```

#### Learning Curve
```yaml
adoption:
  # How quickly developers become proficient
  initial_efficiency: 0.3           # Day 1 efficiency with AI (0-1)
  learning_rate: 0.3                # Speed of improvement (0-1, higher = faster)
  plateau_efficiency: 0.85          # Maximum efficiency achieved (0-1)
  
  # Segment-specific adoption rates
  junior_adoption_multiplier: 1.3   # Juniors adopt faster (> 0)
  mid_adoption_multiplier: 1.0      # Mid-level baseline (> 0)
  senior_adoption_multiplier: 0.7   # Seniors adopt slower (> 0)
```

### Impact Parameters

The impact section defines how AI tools improve various aspects of development.

#### Time Improvements
All values are reduction ratios (0 = no improvement, 1 = 100% faster):
```yaml
impact:
  # Development speed improvements
  feature_cycle_reduction: 0.25     # 25% faster feature delivery (0-1)
  bug_fix_reduction: 0.35           # 35% faster bug fixes (0-1)
  onboarding_reduction: 0.40         # 40% faster onboarding (0-1)
  pr_review_reduction: 0.50          # 50% faster PR reviews (0-1)
```

#### Quality Improvements
All values are reduction ratios for negative metrics:
```yaml
impact:
  # Quality enhancements
  defect_reduction: 0.30            # 30% fewer defects (0-1)
  incident_reduction: 0.25          # 25% fewer incidents (0-1)
  rework_reduction: 0.40            # 40% less rework (0-1)
```

#### Capacity Reallocation
Percentage point changes in how time is allocated:
```yaml
impact:
  # Capacity gains (percentage points)
  feature_capacity_gain: 0.10       # 10pp more time for features
  tech_debt_capacity_gain: 0.05     # 5pp more time for tech debt
```

#### Task Effectiveness
How well AI handles specific development tasks:
```yaml
impact:
  # AI effectiveness by task type (0 = useless, 1 = perfect)
  boilerplate_effectiveness: 0.85   # Repetitive code generation (0-1)
  test_generation_effectiveness: 0.70  # Unit test creation (0-1)
  documentation_effectiveness: 0.80  # Documentation writing (0-1)
  code_review_effectiveness: 0.60   # Code review assistance (0-1)
  debugging_effectiveness: 0.50     # Bug finding and fixing (0-1)
  
  # Developer-level impact multipliers
  junior_multiplier: 1.5            # Juniors benefit more (> 0)
  mid_multiplier: 1.3               # Mid-level moderate benefit (> 0)
  senior_multiplier: 1.2            # Seniors benefit less (> 0)
```

### Cost Parameters

The costs section captures all expenses related to AI tool adoption.

#### Licensing Costs
```yaml
costs:
  # Software licensing
  cost_per_seat_month: 50           # Monthly cost per developer (USD, >= 0)
  enterprise_discount: 0.3          # Enterprise discount rate (0-1)
```

#### Token/API Usage
```yaml
costs:
  # API and token consumption
  initial_tokens_per_dev_month: 500000  # Starting monthly token usage
  token_price_per_million: 8        # Cost per million tokens (USD)
  token_price_decline_annual: 0.25  # Annual price decline rate (0-1)
  token_growth_rate_monthly: 0.10   # Monthly usage growth (0-1)
  token_plateau_month: 12           # Month when usage stabilizes (> 0)
```

#### Training Costs
```yaml
costs:
  # Training and education
  initial_training_cost_per_dev: 2000   # Initial training cost (USD)
  ongoing_training_cost_annual: 500     # Annual training cost (USD)
  trainer_cost_per_day: 2000           # Daily trainer rate (USD)
  training_days_initial: 5              # Initial training days
  training_days_ongoing_annual: 2       # Annual training days
```

#### Infrastructure
```yaml
costs:
  # Infrastructure and support
  infrastructure_setup: 50000          # One-time setup cost (USD)
  infrastructure_monthly: 5000         # Monthly infrastructure (USD)
  admin_overhead_percentage: 0.05     # Admin overhead as % of FTE (0-1)
```

#### Hidden Costs
```yaml
costs:
  # Often overlooked costs
  context_switch_cost_month: 1000     # Monthly context switching (USD)
  bad_code_cleanup_percentage: 0.08   # Time cleaning AI mistakes (0-1)
  security_review_overhead: 4          # Extra security review hours
  
  # Experimentation budget
  pilot_budget: 100000                # Initial pilot investment (USD)
  ongoing_experimentation: 50000      # Annual R&D budget (USD)
```

### Global Parameters

Top-level parameters that control the overall scenario:

```yaml
# Scenario metadata
name: "Moderate Enterprise"          # Display name (string)
description: "50-person enterprise team with balanced AI adoption"
timeframe_months: 36                 # Analysis period (typically 24-36)

# Inheritance (for modular scenarios)
extends:                             # List of configurations to inherit
  - profiles/enterprise              # Base company profile
  - strategies/moderate              # Adoption strategy
  - distributions/medium_uncertainty  # For Monte Carlo

# Scenario references (for legacy format)
baseline:
  profile: enterprise                # Use predefined profile
adoption:
  scenario: grassroots              # Use predefined scenario
impact:
  scenario: moderate                # Use predefined scenario
costs:
  scenario: enterprise              # Use predefined scenario
```

## Parameter Validation Rules

### Required Constraints
1. **Ratios must sum to 1.0**:
   - `junior_ratio + mid_ratio + senior_ratio = 1.0`
   - `initial_adopters + early_adopters + early_majority + late_majority + laggards = 1.0`
   - Capacity percentages should approximately sum to 1.0

2. **Bounded Parameters (0-1)**:
   - All percentages and ratios
   - All reduction factors
   - All effectiveness measures
   - Learning curve parameters

3. **Positive Values Required**:
   - All costs (USD amounts)
   - Team size
   - Time metrics (days, hours)
   - Delivery rates

4. **Logical Constraints**:
   - `initial_efficiency < plateau_efficiency`
   - `token_plateau_month <= timeframe_months`
   - Multipliers typically > 0

### Common Parameter Patterns

#### Conservative Scenarios
- Lower reduction factors (0.1-0.3)
- Higher resistance (0.5-0.7)
- Lower effectiveness (0.3-0.6)
- Higher hidden costs
- Slower adoption curves

#### Moderate Scenarios
- Balanced reduction factors (0.2-0.4)
- Moderate resistance (0.3-0.5)
- Medium effectiveness (0.5-0.7)
- Realistic cost estimates
- Standard adoption curves

#### Aggressive Scenarios
- Higher reduction factors (0.3-0.6)
- Lower resistance (0.1-0.3)
- Higher effectiveness (0.7-0.9)
- Optimistic cost projections
- Faster adoption curves

#### Company Size Patterns

**Startups (5-20 people)**:
- Lower FLC costs
- Faster adoption
- Higher risk tolerance
- Less infrastructure cost
- More feature focus

**Scaleups (20-100 people)**:
- Moderate costs
- Balanced adoption
- Mixed experience levels
- Growing infrastructure
- Balance feature/maintenance

**Enterprises (101+ people)**:
- Higher FLC costs
- Slower adoption
- More process overhead
- Significant infrastructure
- Higher maintenance burden

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