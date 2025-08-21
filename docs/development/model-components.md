# Model Components

## 1. Baseline Metrics (`src/model/baseline.py`)

Establishes current state before AI adoption:
- Team composition and fully-loaded costs
- Current delivery metrics (cycle time, defect rates)
- Capacity allocation (features vs. maintenance)
- Quality baselines (incidents, rework)

### Key Classes
- `BaselineMetrics`: Core baseline configuration
- `TeamComposition`: Developer seniority distribution
- `DeliveryMetrics`: Current development speed
- `QualityMetrics`: Defect and incident rates

## 2. Adoption Dynamics (`src/model/adoption_dynamics.py`)

Models realistic adoption patterns:
- S-curve adoption with segment-specific rates
- Learning curves and efficiency gains
- Dropout and re-engagement patterns
- Network effects and peer influence

### Key Classes
- `AdoptionModel`: Main adoption simulation
- `AdoptionSegment`: Technology adoption categories
- `LearningCurve`: Efficiency improvement over time
- `NetworkEffects`: Peer influence dynamics

## 3. Impact Model (`src/model/impact_model.py`)

Calculates business value across dimensions:
- **Time Value**: Faster feature delivery, bug fixes, onboarding
- **Quality Value**: Fewer defects, incidents, less rework
- **Capacity Value**: More time on strategic work
- **Strategic Value**: Innovation, retention, competitive advantage

### Key Classes
- `ImpactFactors`: Configuration of improvements
- `ValueCalculator`: Computes financial value
- `TaskEffectiveness`: AI effectiveness by task type
- `DeveloperImpact`: Seniority-specific benefits

## 4. Cost Structure (`src/model/cost_structure.py`)

Comprehensive cost modeling:
- Per-seat licensing with enterprise discounts
- Token consumption with price evolution
- Training and change management
- Hidden costs (context switching, bad code cleanup)

### Key Classes
- `CostStructure`: Complete cost configuration
- `LicensingCosts`: Seat-based pricing
- `TokenCosts`: API usage expenses
- `TrainingCosts`: Education and onboarding
- `HiddenCosts`: Often overlooked expenses

## 5. Monte Carlo Engine (`src/model/monte_carlo.py`)

Probabilistic analysis capabilities:
- Parameter uncertainty modeling
- Distribution sampling
- Correlation handling
- Convergence testing

### Key Classes
- `MonteCarloEngine`: Main simulation engine
- `DistributionSampler`: Generates random samples
- `CorrelationMatrix`: Parameter relationships
- `ConvergenceMonitor`: Simulation stability

## 6. Visualizations (`src/model/visualizations.py`)

Console-friendly reporting utilities:
- Formatted summary tables
- ASCII charts and timelines  
- Currency and percentage formatting
- Executive summary generation
- Text-based cost and value breakdowns

### Key Functions
- `format_currency()`: Currency display
- `format_percentage()`: Percentage display
- `create_ascii_chart()`: Terminal charts
- `generate_summary_table()`: Formatted tables

## Component Interactions

```
BaselineMetrics
    ↓
AdoptionModel ←→ ImpactFactors
    ↓              ↓
CostStructure → ValueCalculator
    ↓              ↓
    └──→ Results ←─┘
           ↓
    Visualizations
```

## Data Flow

1. **Initialization**: Load baseline metrics and scenario configuration
2. **Adoption Simulation**: Model adoption curve over time
3. **Impact Calculation**: Apply improvements to baseline
4. **Cost Computation**: Calculate all associated costs
5. **Value Generation**: Compute time, quality, capacity value
6. **NPV/ROI Analysis**: Financial metrics calculation
7. **Visualization**: Format and display results

## Extension Points

### Adding New Metrics
1. Update `BaselineMetrics` with new parameters
2. Add corresponding impact factors in `ImpactFactors`
3. Implement value calculation in `ValueCalculator`
4. Update visualization methods

### Custom Adoption Models
1. Subclass `AdoptionModel`
2. Override `calculate_adoption_rate()`
3. Implement custom learning curves
4. Add new network effect models

### New Cost Categories
1. Extend `CostStructure` class
2. Add cost calculation methods
3. Update total cost aggregation
4. Include in NPV calculations

### Additional Value Streams
1. Define new value categories
2. Implement calculation logic
3. Add to value breakdown
4. Update summary displays

## Testing Components

Each component has corresponding tests:
- `tests/test_baseline.py`
- `tests/test_adoption_dynamics.py`
- `tests/test_impact_model.py`
- `tests/test_cost_structure.py`
- `tests/test_monte_carlo.py`

Run component-specific tests:
```bash
python -m unittest tests.test_baseline
python -m unittest tests.test_adoption_dynamics
```