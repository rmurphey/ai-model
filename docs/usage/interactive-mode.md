# Interactive Mode

The tool includes an interactive terminal-based interface that guides you through scenario creation and analysis.

## Features

- **Quick Setup**: Answer 5 essential questions to get started
- **Detailed Setup**: Configure all parameters with guided prompts
- **Templates**: Start from pre-configured industry templates
- **What-If Analysis**: Explore variations of your scenario
- **Sensitivity Analysis**: Identify which parameters matter most
- **Parameter Refinement**: Iteratively improve your model
- **Results Explorer**: Navigate through detailed breakdowns
- **Scenario Comparison**: Compare multiple scenarios side-by-side
- **Robust Input Handling**: Uses questionary library for cross-platform terminal compatibility

## Usage

```bash
# Launch interactive mode
python main.py --interactive

# Or use the dedicated script
python interactive.py

# Note: Interactive mode requires a terminal environment
# If running through SSH or non-TTY environment, use:
python -u interactive.py
```

## Interactive Workflow

1. **Choose Setup Mode**: Quick (5 questions) or Detailed (15+ questions)
2. **Define Company Profile**: Team size, composition, current metrics
3. **Select Adoption Strategy**: Organic, mandated, or hybrid approach
4. **Set Expectations**: Expected improvements and timeframe
5. **Run Analysis**: Automatic execution with progress indicators
6. **Explore Results**: Interactive navigation through metrics
7. **Refine & Iterate**: Adjust parameters based on sensitivity
8. **Export**: Save results and configurations for sharing

## Quick Setup Questions

When choosing Quick Setup, you'll be asked:
1. Team size and composition
2. Industry/company type
3. Adoption approach (conservative/moderate/aggressive)
4. Expected impact level
5. Analysis timeframe

## Detailed Setup Options

The detailed setup allows configuration of:
- Full baseline metrics (cycle times, quality rates, costs)
- Granular adoption parameters (segments, learning curves)
- Specific impact factors by task type
- Complete cost structure
- Monte Carlo distributions

## Results Explorer

After analysis completes, navigate through:
- Executive summary with key metrics
- Financial breakdown by year
- Value drivers and components
- Adoption curves and efficiency gains
- Risk analysis (if Monte Carlo enabled)
- Sensitivity results

## Tips for Best Results

1. **Start with Quick Setup** to get familiar with the tool
2. **Use Templates** based on similar companies
3. **Run Sensitivity Analysis** to understand key drivers
4. **Iterate Parameters** based on sensitivity results
5. **Export Configurations** for reproducibility
6. **Compare Scenarios** to evaluate different strategies