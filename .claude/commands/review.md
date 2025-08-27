# Review Command

Comprehensive code review using Python review agents. Analyzes code quality, testing coverage, and generates actionable recommendations.

## Usage

```bash
# Run full review with report display
claude review

# Run review without displaying report
claude review --no-show

# Run with verbose output
claude review -v
claude review --verbose

# Explicitly show the report
claude review --show

# Review a different directory
claude review --path /path/to/repo
```

## Implementation

```bash
#!/bin/bash
cd "$(dirname "$0")" && cd ../..
source venv/bin/activate 2>/dev/null || true
python -m src.commands.review_command "$@"
```

## Description

The `/review` command orchestrates multiple specialized code review agents to provide comprehensive analysis of your Python codebase:

### Review Agents

1. **Python Reviewer Agent**
   - Analyzes code structure and quality
   - Identifies performance opportunities
   - Checks architectural patterns
   - Evaluates maintainability
   - Provides overall code score (0-10)

2. **Python Testing Expert Agent**
   - Analyzes test coverage and quality
   - Identifies coverage gaps
   - Reviews test patterns
   - Measures test performance
   - Provides test health score (0-10)

### Report Generation

Reports are saved to `outputs/review_reports/` with timestamps:
- `review_summary_YYYYMMDD_HHMMSS.md` - Combined markdown report
- `python_reviewer_YYYYMMDD_HHMMSS.json` - Detailed reviewer findings
- `testing_expert_YYYYMMDD_HHMMSS.json` - Detailed testing analysis
- `latest_review.md` - Symlink to most recent summary

### Report Contents

The summary report includes:
- **Executive Summary**: Overall scores and key metrics
- **Combined Quality Score**: Average of code and test scores
- **Key Findings**: Prioritized issues and recommendations
- **Strengths**: Positive patterns identified
- **Metrics Summary**: Coverage, complexity, maintainability
- **Top Recommendations**: Actionable next steps
- **Recent Improvements**: Progress since last review

### Quality Scoring

Combined scores determine repository status:
- **8.0-10.0**: ✅ Production Ready
- **6.0-7.9**: ⚠️ Needs Improvement
- **0.0-5.9**: ❌ Significant Issues

### Exit Codes

- `0`: Review passed (score ≥ 6.0)
- `1`: Review failed (score < 6.0)

## Examples

### Quick Review
```bash
$ claude review
🚀 Starting Code Review Process
==================================================
🔍 Running Python code reviewer agent...
🧪 Running Python testing expert agent...
📝 Generating summary report...

✅ Review complete in 2.3 seconds

📁 Reports saved to: outputs/review_reports
  • Summary: review_summary_20250821_100000.md
  • Reviewer: python_reviewer_20250821_100000.json
  • Testing: testing_expert_20250821_100000.json

📊 Combined Quality Score: 8.2/10
```

### Verbose Review
```bash
$ claude review -v
# Shows detailed progress including:
# - Files analyzed count
# - Test discovery details
# - Issue counts by priority
# - Real-time scoring updates
```

### CI/CD Integration
```bash
# Use in CI pipeline
if claude review --no-show; then
  echo "Code review passed"
else
  echo "Code review failed - check reports"
  cat outputs/review_reports/latest_review.md
  exit 1
fi
```

### Review Different Project
```bash
$ claude review --path ../other-project
# Reviews the specified directory
```

## Report Storage

Reports are automatically organized:
```
outputs/review_reports/
├── .gitignore                           # Excludes reports from git
├── latest_review.md                     # Symlink to most recent
├── review_summary_20250821_100000.md    # Human-readable summary
├── python_reviewer_20250821_100000.json # Detailed code analysis
└── testing_expert_20250821_100000.json  # Detailed test analysis
```

## Integration with Other Commands

Works well with other Claude commands:
```bash
# Check what needs work
claude next

# Run review
claude review

# Fix issues based on review
claude analyze --sensitivity moderate_enterprise

# Verify improvements
claude review --show
```

## Notes

- Reviews are timestamp-based to track progress over time
- JSON reports enable programmatic processing
- Reports directory is gitignored by default
- Latest review is always accessible via symlink
- Exit codes enable CI/CD integration
- Combines multiple agent perspectives for comprehensive analysis