# Programmatic Usage

## Basic Analysis

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

## Programmatic Reproduction

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

## Custom Scenario Creation

```python
from src.model.baseline import BaselineMetrics
from src.model.adoption_dynamics import AdoptionModel
from src.model.impact_model import ImpactFactors
from src.model.cost_structure import CostStructure

# Define custom baseline
baseline = BaselineMetrics(
    team_size=30,
    junior_ratio=0.3,
    mid_ratio=0.5,
    senior_ratio=0.2,
    avg_feature_cycle_days=21,
    defect_escape_rate=5.0
)

# Configure adoption
adoption = AdoptionModel(
    initial_adopters=0.1,
    early_adopters=0.2,
    learning_rate=0.3
)

# Set impact factors
impact = ImpactFactors(
    feature_cycle_reduction=0.25,
    defect_reduction=0.30,
    junior_multiplier=1.5
)

# Define costs
costs = CostStructure(
    cost_per_seat_month=50,
    token_price_per_million=8
)

# Run analysis
results = model.run_custom_scenario(
    baseline=baseline,
    adoption=adoption,
    impact=impact,
    costs=costs,
    timeframe_months=24
)
```

## Monte Carlo Analysis

```python
from src.model.monte_carlo import MonteCarloEngine
from src.model.distributions import TriangularDistribution, NormalDistribution

# Create Monte Carlo engine
mc_engine = MonteCarloEngine(iterations=1000, seed=42)

# Define distributions
distributions = {
    "baseline.avg_feature_cycle_days": TriangularDistribution(20, 25, 30),
    "impact.feature_cycle_reduction": NormalDistribution(0.3, 0.05),
    "costs.cost_per_seat_month": TriangularDistribution(40, 50, 60)
}

# Run simulation
mc_results = mc_engine.run_simulation(
    scenario_config=config,
    distributions=distributions
)

# Access results
print(f"NPV Mean: ${mc_results.npv_mean:,.0f}")
print(f"NPV 95% CI: [{mc_results.npv_ci_lower:,.0f}, {mc_results.npv_ci_upper:,.0f}]")
print(f"Probability NPV > 0: {mc_results.prob_positive_npv:.1%}")
```

## Batch Processing

```python
from src.batch.batch_processor import BatchProcessor

# Create batch processor
processor = BatchProcessor(parallel_workers=4)

# Define scenarios to process
scenarios = [
    "conservative_startup",
    "moderate_enterprise",
    "aggressive_scaleup"
]

# Run batch analysis
batch_results = processor.process_batch(
    scenarios=scenarios,
    output_dir="outputs/batch",
    generate_comparison=True
)

# Access aggregate results
for scenario, result in batch_results.items():
    print(f"{scenario}: NPV = ${result['npv']:,.0f}")
```

## Sensitivity Analysis

```python
from src.analysis.sensitivity_analysis import SensitivityAnalyzer

# Create analyzer
analyzer = SensitivityAnalyzer(samples=1024)

# Run sensitivity analysis
sensitivity_results = analyzer.analyze(
    scenario_config=config,
    parameters_to_vary=[
        "impact.feature_cycle_reduction",
        "adoption.plateau_efficiency",
        "costs.cost_per_seat_month"
    ]
)

# Get parameter importance
importance = sensitivity_results.get_parameter_importance()
for param, score in importance.items():
    print(f"{param}: {score:.3f}")
```

## Custom Analysis Scripts

The `src/analysis/` directory contains additional analysis tools:
- `terminal_visualizations.py` - Console-based charts and graphs
- `generate_scenario_matrix.py` - Batch scenario analysis
- `save_results.py` - Export utilities for different formats
- `scaleup_analysis.py` - Growth-focused analysis patterns

## Working with Results

```python
# Access detailed metrics
results = model.run_scenario("moderate_enterprise")

# Financial metrics
print(f"NPV: ${results.npv:,.0f}")
print(f"ROI: {results.roi:.1%}")
print(f"Breakeven: Month {results.breakeven_month}")

# Adoption metrics
print(f"Peak Adoption: {results.peak_adoption:.1%}")
print(f"Efficiency at Peak: {results.peak_efficiency:.1%}")

# Value breakdown
for component, value in results.value_breakdown.items():
    print(f"{component}: ${value:,.0f}")

# Time series data
for month in range(results.timeframe_months):
    print(f"Month {month}: {results.monthly_metrics[month]}")
```

## Integration Examples

### Flask API Endpoint

```python
from flask import Flask, jsonify, request
from main import AIImpactModel

app = Flask(__name__)
model = AIImpactModel()

@app.route('/analyze', methods=['POST'])
def analyze():
    scenario = request.json.get('scenario', 'moderate_enterprise')
    results = model.run_scenario(scenario)
    return jsonify({
        'npv': results.npv,
        'roi': results.roi,
        'breakeven_month': results.breakeven_month
    })
```

### Jupyter Notebook

```python
# In a Jupyter notebook
import pandas as pd
import matplotlib.pyplot as plt
from main import AIImpactModel

model = AIImpactModel()
results = model.run_scenario("moderate_enterprise")

# Create dataframe
df = pd.DataFrame(results.monthly_metrics)

# Plot adoption curve
df['adoption_rate'].plot(title='AI Tool Adoption Over Time')
plt.xlabel('Month')
plt.ylabel('Adoption Rate')
plt.show()
```