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

# Run default scenario
python main.py

# Run specific scenario
python main.py --scenario aggressive_scaleup

# Compare all scenarios
python main.py --scenario all --compare

# Generate visualizations
python main.py --scenario moderate_enterprise --visualize
```

## Model Components

### 1. Baseline Metrics (`baseline.py`)
Establishes current state before AI adoption:
- Team composition and fully-loaded costs
- Current delivery metrics (cycle time, defect rates)
- Capacity allocation (features vs. maintenance)
- Quality baselines (incidents, rework)

### 2. Adoption Dynamics (`adoption_dynamics.py`)
Models realistic adoption patterns:
- S-curve adoption with segment-specific rates
- Learning curves and efficiency gains
- Dropout and re-engagement patterns
- Network effects and peer influence

### 3. Impact Model (`impact_model.py`)
Calculates business value across dimensions:
- **Time Value**: Faster feature delivery, bug fixes, onboarding
- **Quality Value**: Fewer defects, incidents, less rework
- **Capacity Value**: More time on strategic work
- **Strategic Value**: Innovation, retention, competitive advantage

### 4. Cost Structure (`cost_structure.py`)
Comprehensive cost modeling:
- Per-seat licensing with enterprise discounts
- Token consumption with price evolution
- Training and change management
- Hidden costs (context switching, bad code cleanup)

### 5. Visualizations (`visualizations.py`)
Executive-ready reporting:
- Adoption and efficiency curves
- Cost breakdown over time
- ROI timeline with breakeven
- Sensitivity analysis
- Scenario comparisons

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

Edit `scenarios.yaml` to define your own scenarios:

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

## Advanced Usage

### Monte Carlo Simulation

```python
from adoption_dynamics import simulate_adoption_monte_carlo, create_adoption_scenario

params = create_adoption_scenario("organic")
results = simulate_adoption_monte_carlo(params, n_simulations=1000)

# results contains percentiles (P10, P50, P90) for risk analysis
```

### Task-Specific Analysis

```python
from impact_model import calculate_task_specific_impact

task_distribution = {
    "boilerplate": 0.15,
    "testing": 0.25,
    "documentation": 0.10,
    "debugging": 0.20,
    "feature_development": 0.30
}

impact = calculate_task_specific_impact(baseline, factors, task_distribution)
```

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

## Future Enhancements

- [ ] Integration with actual development metrics (JIRA, GitHub)
- [ ] Industry-specific benchmarks database
- [ ] Real-time token price updates
- [ ] Team growth modeling
- [ ] Multi-tool comparison (different AI vendors)

## Contributing

This model is designed to be extended. Key extension points:
- Add new baseline profiles in `create_industry_baseline()`
- Define new impact factors in `ImpactFactors`
- Create custom adoption curves in `AdoptionModel`
- Add new visualization types in `ModelVisualizer`

## License

MIT