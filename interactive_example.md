# Interactive Mode Example Session

This shows what a real interactive session looks like with the fixed implementation:

```
$ python interactive.py

==================================================
  AI Impact Model Interactive Mode
==================================================

Choose your path:
  ❯ Quick Setup (5 questions)
    Detailed Setup (15 questions)
    Load existing scenario
    Use template
    View session history
    Quit

[User presses Enter to select Quick Setup]

==================================================
  Quick Setup
==================================================

[Question 1/5] Company Profile
What is your current team size? [1-10000] [50]: 75
✓ Team size: 75

[Question 2/5] Team Composition
Select your team composition:
  ❯ 30% junior, 50% mid, 20% senior
    50% junior, 35% mid, 15% senior
    20% junior, 40% mid, 40% senior
    Enter custom percentages

[User selects first option]

[Question 3/5] Adoption Strategy
Select your adoption strategy:
    Bottom-up, developer-driven adoption
  ❯ Top-down, management-driven rollout
    Mixed approach with pilot groups

[User selects second option]

[Question 4/5] Expected Impact
What level of impact do you expect?
    10-20% improvements
  ❯ 20-35% improvements
    35-50% improvements

[User selects second option]

[Question 5/5] Timeframe
Analysis timeframe in months [6-60] [24]: 36
✓ Timeframe: 36 months

Running analysis for: quick_setup_20250821_145632

============================================================
RUNNING SCENARIO: QUICK_SETUP_20250821_145632
============================================================

Creating baseline metrics...
✓ Team composition validated
✓ Capacity allocation validated
✓ Baseline metrics created

Modeling adoption curve...
✓ Adoption segments configured
✓ Learning curve parameters set

Calculating impacts...
✓ Time efficiency improvements: 30%
✓ Quality improvements: 25%
✓ Productivity gains: 35%

Financial Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% Complete

╔══════════════════════════════════════════════════════╗
║                  ANALYSIS RESULTS                      ║
╠══════════════════════════════════════════════════════╣
║ Financial Metrics:                                     ║
║   NPV: $2,847,392                                     ║
║   ROI: 287.4%                                         ║
║   Payback Period: 8.3 months                          ║
║                                                        ║
║ Productivity Impact:                                   ║
║   Time Saved: 12,450 hours/year                       ║
║   FTE Equivalent: 7.8 developers                      ║
║   Output Increase: 35%                                ║
║                                                        ║
║ Quality Improvements:                                  ║
║   Defect Reduction: 25%                               ║
║   Incident Reduction: 30%                             ║
║   Rework Reduction: 40%                               ║
╚══════════════════════════════════════════════════════╝

What would you like to do next?
  ❯ Explore detailed metrics
    Run sensitivity analysis
    Adjust parameters
    Compare with another scenario
    Export results
    Start new scenario
    Back to main menu

[Session continues with user exploring results...]
```

## Key Features Demonstrated

### 1. **Questionary UI Elements**
- **Select Lists**: Arrow keys to navigate, Enter to select
- **Text Input**: Shows defaults in brackets, validates input
- **Checkboxes**: Space to select multiple items
- **Confirmations**: Yes/No prompts for important actions

### 2. **Input Validation**
- Numeric ranges enforced (e.g., team size 1-10000)
- Percentages must be 0-1
- Ratios must sum to 1.0
- Invalid input shows helpful error messages

### 3. **Progressive Disclosure**
- Quick Setup: Only essential questions
- Detailed Setup: Full parameter control
- Smart defaults for all values

### 4. **Real-time Feedback**
- ✓ Checkmarks for completed steps
- Progress bars for long operations
- Clear error messages with recovery options

### 5. **Results Explorer**
After analysis, users can:
- Drill down into specific metrics
- Run "what-if" scenarios
- Perform sensitivity analysis
- Export in multiple formats
- Compare scenarios side-by-side

## Error Handling

The fixed version handles edge cases gracefully:

```
What is your current team size? [1-10000] [50]: -5
⚠ Value must be at least 1

What is your current team size? [1-10000] [50]: abc
⚠ Please enter a valid number

What is your current team size? [1-10000] [50]: 50000
⚠ Value must be at most 10000

What is your current team size? [1-10000] [50]: [User presses Ctrl+C]

Session terminated by user.
```

## Benefits of the Fix

1. **Robust Input Handling**: Questionary ensures input always waits for user
2. **Cross-platform**: Works on Windows, Mac, Linux, and SSH sessions
3. **Professional UX**: Consistent with modern CLI tools
4. **Parameter Validation**: All scenarios create valid BaselineMetrics
5. **Better Defaults**: Sensible defaults for all required parameters