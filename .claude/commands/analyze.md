# AI Impact Analysis Command

Run AI development impact analysis scenarios and save results to timestamped text files.

## Usage

```bash
# Single scenario analysis
claude analyze moderate_enterprise

# Multiple scenarios
claude analyze startup enterprise scaleup

# Compare standard scenarios
claude analyze --compare

# Custom output filename
claude analyze --output my_report.txt moderate_enterprise

# List available scenarios
claude analyze --list
```

## Implementation

```bash
#!/bin/bash
cd "$(dirname "$0")" && cd ../..
source venv/bin/activate
python run_analysis.py "$@"
```

## Description

This command provides a streamlined interface to run AI impact analysis scenarios. It automatically:

- Executes scenario analysis with progress indicators
- Saves timestamped results to `outputs/reports/analysis_YYYYMMDD_HHMMSS.txt`
- Provides formatted executive summaries with key metrics
- Supports single scenario, multiple scenarios, or comparison modes
- Shows file preview after completion

Results include NPV, ROI, breakeven analysis, adoption curves, and detailed financial breakdowns perfect for executive reporting.

## Available Scenarios

- conservative_startup, moderate_startup, aggressive_startup
- conservative_enterprise, moderate_enterprise, aggressive_enterprise  
- conservative_scaleup, moderate_scaleup, aggressive_scaleup
- custom, task_distributions, sensitivity