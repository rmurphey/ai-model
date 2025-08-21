# Export and Output Options

## Claude Command Usage

The repository includes a native Claude command for streamlined analysis:

```bash
# Single scenario analysis
claude analyze moderate_enterprise

# Compare standard scenarios (conservative_startup, moderate_enterprise, aggressive_scaleup)
claude analyze --compare

# List all available scenarios
claude analyze --list

# Multiple scenario analysis
claude analyze startup enterprise scaleup

# Custom output filename
claude analyze --output my_report.txt moderate_enterprise
```

## Report Generation

### Comprehensive Reports Command

```bash
# Generate comprehensive reports
claude reports startup --format markdown
claude reports enterprise --monte-carlo --format all
claude reports ai_assistant --output custom_report.json
```

### Automatic Report Generation

All analyses automatically generate timestamped reports in `outputs/reports/`:
- **Filename format**: `analysis_YYYYMMDD_HHMMSS.txt`
- **Custom names**: Use `--output filename.txt` for custom naming
- **Content**: Executive summaries, financial metrics, value breakdowns

## Report Contents

Each exported report includes:
- **Executive Summary**: Key metrics, NPV, ROI, breakeven analysis
- **Financial Breakdown**: 3-year investment vs value, per-developer costs
- **Value Analysis**: Time, quality, capacity, and strategic value components
- **Adoption Metrics**: Peak adoption rates, efficiency curves
- **Opportunity Cost Analysis**: Current inefficiency vs AI tool value capture

## Output Formats

**Saved Files**: Clean markdown format with headers, lists, and formatting

**Console Output**: Colorful plaintext with ANSI colors for readability
- 🟢 Green for positive metrics (NPV, value, gains)
- 🔴 Red for costs and negative values
- 🔵 Blue for headers and section titles
- 🟡 Yellow for percentages and warnings
- 🔷 Cyan for file paths and highlights

## Direct Script Usage

For more control, use the analysis script directly:

```bash
# Basic analysis with auto-generated filename
python run_analysis.py moderate_enterprise

# Custom output file
python run_analysis.py --output quarterly_analysis.txt moderate_enterprise

# Multiple scenarios in one report
python run_analysis.py startup enterprise scaleup

# Comparison mode
python run_analysis.py --compare all

# List available scenarios
python run_analysis.py --list
```

## Export Locations

- **Reports**: `outputs/reports/` - Text and markdown analysis reports
- **Data**: `outputs/data/` - CSV data exports
- **Batch Results**: `outputs/batch/` - Batch processing results
- **Charts**: `outputs/charts/` - PNG visualizations (legacy)

## Format Options

### Markdown Format
- Human-readable with formatting
- Includes tables and lists
- Embeds reproduction metadata
- Best for documentation and sharing

### JSON Format
- Machine-readable structure
- Complete parameter data
- Suitable for further processing
- API integration ready

### Text Format
- Plain text with minimal formatting
- Console-friendly output
- Easy to parse with scripts
- Suitable for logs and monitoring

## Batch Export

When using batch processing, exports include:
- Individual scenario reports
- Comparison matrix
- Aggregate statistics
- JSON data for all scenarios

```yaml
# batch_config.yaml
output_dir: outputs/batch
generate_comparison: true
save_individual_reports: true
format: markdown  # or json, text
```

## Metadata Inclusion

All exports include:
- **Version Information**: Tool version for reproducibility
- **Timestamp**: Analysis date and time
- **Configuration**: Complete scenario parameters
- **Random Seed**: For Monte Carlo reproducibility
- **Checksum**: Data integrity verification