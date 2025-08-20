"""
Configuration constants for AI Impact Analysis Model.
Centralizes all magic numbers and business parameters for easy maintenance.
"""

# Time-based constants
WORKING_DAYS_PER_YEAR = 260
WORKING_HOURS_PER_YEAR = 2080
WORKING_HOURS_PER_MONTH = 173
MONTHS_PER_YEAR = 12

# Financial constants
DEFAULT_DISCOUNT_RATE_ANNUAL = 0.10
DEFAULT_TURNOVER_RATE = 0.20  # 20% annual turnover assumption

# Development productivity constants
TECH_DEBT_MULTIPLIER = 1.5  # Tech debt work has 1.5x future value multiplier
CONTEXT_SWITCHING_PRODUCTIVITY_LOSS = 0.10  # 10% productivity loss estimate
INNOVATION_CAPACITY_PERCENTAGE = 0.10  # 10% of capacity for innovation
COMPETITIVE_VALUE_MULTIPLIER = 0.10  # 10% of feature acceleration value

# Quality and efficiency constants
BUGS_PER_INCIDENT = 3  # Assume 3 bugs per production incident
HOURS_PER_DEFECT_FIX = 10  # Hours to fix one defect
KLOC_PER_TEAM_PER_YEAR = 100  # Assume team produces 100 KLOC per year

# Training and adoption constants
TRAINING_GROUP_SIZE = 10  # 1 trainer per 10 developers
QUARTERLY_TRAINING_FREQUENCY = 3  # Every 3 months
MAX_TRAINING_BOOST = 0.30  # Cap training adoption boost at 30%
BASELINE_TRAINING_COST = 10000  # Baseline training cost per developer

# Network effect thresholds
NETWORK_EFFECT_THRESHOLD_LOW = 0.10  # 10% adoption for initial network effects
NETWORK_EFFECT_THRESHOLD_MID = 0.30  # 30% adoption for moderate effects
NETWORK_EFFECT_THRESHOLD_HIGH = 0.50  # 50% adoption for strong effects

# Visualization constants
DEFAULT_CHART_WIDTH = 60
DEFAULT_TIMELINE_BAR_LENGTH = 30

# Business impact multipliers
JUNIOR_EFFECTIVENESS_BOOST = 0.20  # 20% effectiveness boost for juniors
MAX_ADOPTION_RATE = 0.95  # 95% ceiling for segment adoption
RETENTION_VALUE_IMPROVEMENT = 0.01  # 1% reduction in turnover per adoption point
RETENTION_MULTIPLIER = 0.01  # 1% retention improvement value multiplier

# Cost model defaults
ENTERPRISE_TEAM_SIZE_THRESHOLD = 50  # Teams >= 50 get enterprise discounts
TOKEN_USAGE_PLATEAU_MONTHS = 6  # Default months to token usage plateau
DEV_HOURS_PER_MONTH = 173  # Average working hours per month
BUG_FIX_DENOMINATOR = 80  # Denominator factor for bug fix calculations

# Scenario validation bounds
MIN_RATIO = 0.0
MAX_RATIO = 1.0
MIN_PERCENTAGE = 0.0
MAX_PERCENTAGE = 100.0
RATIO_SUM_TOLERANCE = 0.01  # Tolerance for ratio sums to equal 1.0

# File and directory constants
DEFAULT_SCENARIOS_FILE = "src/scenarios/scenarios.yaml"
DEFAULT_OUTPUT_DIR = "outputs/reports"
DEFAULT_CHART_DIR = "outputs/charts"

# Error handling constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30