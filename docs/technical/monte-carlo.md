# Monte Carlo Simulation

## Overview

The model supports **Monte Carlo simulation** for probabilistic business impact analysis. Instead of single point estimates, Monte Carlo runs thousands of simulations with parameter uncertainty to provide confidence intervals and risk assessment.

## Key Features

- **Probability distributions** for all model parameters
- **Confidence intervals** for NPV, ROI, and breakeven analysis  
- **Risk metrics** including probability of positive NPV
- **Sensitivity analysis** to identify high-impact parameters
- **Correlation support** between related parameters

## Running Monte Carlo Analysis

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

## Defining Uncertainty in Scenarios

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

## Available Distributions

- **Normal**: For symmetric uncertainty (`mean`, `std`)
- **Triangular**: When min/likely/max are known (`min`, `mode`, `max`)
- **Beta**: For rates and percentages (`alpha`, `beta`)
- **Uniform**: Equal probability in range (`min`, `max`)
- **LogNormal**: For costs and durations (`mean_log`, `std_log`)
- **Deterministic**: Fixed value (no distribution)

## Parameter Correlations

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

## Monte Carlo Output

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

## Example Output

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