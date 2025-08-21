# Reports Command

Generate comprehensive reports from AI impact analysis results.

## Usage

```bash
/reports <scenario> [options]
```

## Arguments

- `scenario` - Name of the scenario to analyze (required)

## Options

- `--format <type>` - Output format: markdown, json, text, or all (default: markdown)
- `--output <path>` - Custom output file path (default: reports/<scenario>_<timestamp>.<ext>)
- `--monte-carlo` - Include Monte Carlo simulation in analysis
- `--iterations <n>` - Number of Monte Carlo iterations (default: 10000)
- `--scenarios-path <path>` - Path to scenarios directory (default: src/scenarios)

## Examples

### Generate a markdown report for the startup scenario
```bash
/reports startup
```

### Generate reports in all formats with Monte Carlo analysis
```bash
/reports enterprise --format all --monte-carlo
```

### Generate a JSON report with custom output path
```bash
/reports ai_assistant --format json --output my_report.json
```

### Run Monte Carlo with 50000 iterations
```bash
/reports startup --monte-carlo --iterations 50000
```

## Output Formats

### Markdown (.md)
Human-readable report with sections for:
- Executive Summary (NPV, ROI, Payback Period)
- Time Efficiency Analysis
- Cost Analysis
- Productivity Metrics
- Monte Carlo Results (if enabled)

### JSON (.json)
Machine-readable format containing:
- Metadata (scenario, timestamp, version)
- Complete results dictionary
- All calculated metrics

### Text (.txt)
Plain text format suitable for:
- Terminal output
- Email reports
- Legacy systems

## Report Contents

All reports include:
- Financial metrics (NPV, ROI, payback period)
- Time efficiency metrics
- Cost breakdown
- Productivity improvements
- Monte Carlo simulation results (when enabled)
- Sensitivity analysis (when Monte Carlo is used)

## Output Location

By default, reports are saved to the `reports/` directory with filenames like:
- `startup_20250121_143022.md`
- `enterprise_20250121_143022.json`

Use the `--output` option to specify a custom location.