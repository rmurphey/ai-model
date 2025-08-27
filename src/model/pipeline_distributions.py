"""
Distributions for delivery pipeline and testing parameters in Monte Carlo.
"""

from typing import Dict, Optional
from .distributions import EnhancedParameterDistributions
from .distributions_old import Normal, Triangular, Beta, Uniform, LogNormal


def add_pipeline_distributions(distributions: EnhancedParameterDistributions,
                              scenario_type: str = "moderate") -> None:
    """
    Add delivery pipeline stage distributions to parameter distributions.
    
    Args:
        distributions: ParameterDistributions object to add to
        scenario_type: "conservative", "moderate", or "aggressive"
    """
    
    if scenario_type == "conservative":
        # Conservative: More uncertainty, lower improvements
        
        # Code review takes longer for AI code (20-50% slower)
        distributions.add_distribution(
            "ai_code_review_multiplier",
            Triangular(min_val=1.2, mode=1.3, max_val=1.5)
        )
        
        # Testing effectiveness varies
        distributions.add_distribution(
            "test_automation_coverage",
            Beta(alpha=2, beta=5, min_val=0.1, max_val=0.5)  # 10-50% automation
        )
        
        # Manual testing time (hours per test suite)
        distributions.add_distribution(
            "test_execution_time_manual",
            Triangular(min_val=3.0, mode=4.0, max_val=6.0)
        )
        
        # AI test quality is poor
        distributions.add_distribution(
            "ai_test_generation_quality",
            Beta(alpha=2, beta=8, min_val=0.3, max_val=0.6)  # 30-60% quality
        )
        
        # Deployment frequency impact
        distributions.add_distribution(
            "deployment_delay_factor",
            Uniform(min_val=0.7, max_val=1.0)  # 0-30% delay
        )
        
        # Defect escape rate with AI
        distributions.add_distribution(
            "ai_defect_escape_multiplier",
            Triangular(min_val=1.0, mode=1.2, max_val=1.4)  # More defects escape
        )
        
    elif scenario_type == "aggressive":
        # Aggressive: Optimistic assumptions
        
        # Code review slightly slower for AI
        distributions.add_distribution(
            "ai_code_review_multiplier",
            Triangular(min_val=1.0, mode=1.1, max_val=1.2)
        )
        
        # High test automation
        distributions.add_distribution(
            "test_automation_coverage",
            Beta(alpha=8, beta=2, min_val=0.7, max_val=0.95)  # 70-95% automation
        )
        
        # Fast automated testing
        distributions.add_distribution(
            "test_execution_time_manual",
            Triangular(min_val=2.0, mode=3.0, max_val=4.0)
        )
        
        # AI tests are decent
        distributions.add_distribution(
            "ai_test_generation_quality",
            Beta(alpha=6, beta=4, min_val=0.6, max_val=0.8)  # 60-80% quality
        )
        
        # Frequent deployments
        distributions.add_distribution(
            "deployment_delay_factor",
            Uniform(min_val=0.9, max_val=1.1)  # -10% to +10% variation
        )
        
        # Slightly more defects but caught
        distributions.add_distribution(
            "ai_defect_escape_multiplier",
            Triangular(min_val=0.9, mode=1.0, max_val=1.1)
        )
        
    else:  # moderate
        # Moderate: Balanced uncertainty
        
        # Code review moderately slower
        distributions.add_distribution(
            "ai_code_review_multiplier",
            Triangular(min_val=1.1, mode=1.2, max_val=1.3)
        )
        
        # Mixed test automation
        distributions.add_distribution(
            "test_automation_coverage",
            Beta(alpha=4, beta=4, min_val=0.3, max_val=0.7)  # 30-70% automation
        )
        
        # Variable testing time
        distributions.add_distribution(
            "test_execution_time_manual",
            Normal(mean=3.5, std=0.8, min_val=2.0, max_val=5.0)
        )
        
        # AI test quality varies
        distributions.add_distribution(
            "ai_test_generation_quality",
            Beta(alpha=3, beta=5, min_val=0.4, max_val=0.7)  # 40-70% quality
        )
        
        # Some deployment variability
        distributions.add_distribution(
            "deployment_delay_factor",
            Normal(mean=0.85, std=0.1, min_val=0.6, max_val=1.0)
        )
        
        # Moderate defect impact
        distributions.add_distribution(
            "ai_defect_escape_multiplier",
            Normal(mean=1.15, std=0.15, min_val=0.9, max_val=1.4)
        )
    
    # Add correlations
    # Review time correlates with test quality
    distributions.add_correlation("ai_code_review_multiplier", "ai_test_generation_quality", -0.3)
    
    # Test automation correlates with deployment frequency
    distributions.add_correlation("test_automation_coverage", "deployment_delay_factor", 0.4)
    
    # Test quality affects defect escape
    distributions.add_correlation("ai_test_generation_quality", "ai_defect_escape_multiplier", -0.5)


def add_testing_strategy_distributions(distributions: EnhancedParameterDistributions,
                                      team_type: str = "balanced") -> None:
    """
    Add testing strategy distributions based on team type.
    
    Args:
        distributions: ParameterDistributions object to add to
        team_type: "startup", "enterprise", or "balanced"
    """
    
    if team_type == "startup":
        # Startups: High variability, less mature testing
        
        # TDD adoption varies widely
        distributions.add_distribution(
            "tdd_adoption_percentage",
            Beta(alpha=2, beta=8, min_val=0.0, max_val=0.3)  # 0-30% TDD
        )
        
        # Test pyramid is often inverted
        distributions.add_distribution(
            "unit_test_percentage",
            Beta(alpha=3, beta=5, min_val=0.3, max_val=0.6)  # 30-60% unit tests
        )
        
        # Test flakiness is high
        distributions.add_distribution(
            "test_flakiness_rate",
            Beta(alpha=3, beta=7, min_val=0.05, max_val=0.2)  # 5-20% flaky
        )
        
        # Low QA ratio
        distributions.add_distribution(
            "qa_developer_ratio",
            Beta(alpha=2, beta=18, min_val=0.0, max_val=0.15)  # 0-15% QA
        )
        
    elif team_type == "enterprise":
        # Enterprise: More stable, mature testing
        
        # Some TDD adoption
        distributions.add_distribution(
            "tdd_adoption_percentage",
            Beta(alpha=4, beta=6, min_val=0.2, max_val=0.5)  # 20-50% TDD
        )
        
        # Good test pyramid
        distributions.add_distribution(
            "unit_test_percentage",
            Beta(alpha=7, beta=3, min_val=0.6, max_val=0.8)  # 60-80% unit tests
        )
        
        # Lower flakiness
        distributions.add_distribution(
            "test_flakiness_rate",
            Beta(alpha=2, beta=18, min_val=0.02, max_val=0.08)  # 2-8% flaky
        )
        
        # Higher QA ratio
        distributions.add_distribution(
            "qa_developer_ratio",
            Beta(alpha=5, beta=15, min_val=0.15, max_val=0.35)  # 15-35% QA
        )
        
    else:  # balanced
        # Balanced: Moderate variability
        
        # Moderate TDD
        distributions.add_distribution(
            "tdd_adoption_percentage",
            Beta(alpha=3, beta=7, min_val=0.1, max_val=0.4)  # 10-40% TDD
        )
        
        # Decent test pyramid
        distributions.add_distribution(
            "unit_test_percentage",
            Beta(alpha=5, beta=3, min_val=0.5, max_val=0.75)  # 50-75% unit tests
        )
        
        # Moderate flakiness
        distributions.add_distribution(
            "test_flakiness_rate",
            Beta(alpha=2, beta=13, min_val=0.03, max_val=0.12)  # 3-12% flaky
        )
        
        # Moderate QA
        distributions.add_distribution(
            "qa_developer_ratio",
            Beta(alpha=3, beta=12, min_val=0.1, max_val=0.25)  # 10-25% QA
        )
    
    # Add testing culture distributions
    distributions.add_distribution(
        "testing_first_mindset",
        Beta(alpha=4, beta=6, min_val=0.3, max_val=0.8)  # How much testing prioritized
    )
    
    distributions.add_distribution(
        "peer_review_thoroughness",
        Beta(alpha=5, beta=5, min_val=0.4, max_val=0.9)  # Review quality
    )
    
    # Correlations
    # TDD correlates with unit test percentage
    distributions.add_correlation("tdd_adoption_percentage", "unit_test_percentage", 0.6)
    
    # QA ratio affects flakiness
    distributions.add_correlation("qa_developer_ratio", "test_flakiness_rate", -0.4)
    
    # Testing mindset affects review thoroughness
    distributions.add_correlation("testing_first_mindset", "peer_review_thoroughness", 0.5)


def add_capacity_constraint_distributions(distributions: EnhancedParameterDistributions) -> None:
    """
    Add distributions for capacity constraints and bottlenecks.
    """
    
    # WIP (Work In Progress) limits
    distributions.add_distribution(
        "wip_limit_multiplier",
        Triangular(min_val=1.5, mode=2.0, max_val=3.0)  # WIP = team_size * multiplier
    )
    
    # Context switching overhead
    distributions.add_distribution(
        "context_switch_overhead",
        Beta(alpha=3, beta=12, min_val=0.1, max_val=0.3)  # 10-30% overhead
    )
    
    # Review bottleneck severity
    distributions.add_distribution(
        "review_bottleneck_factor",
        Beta(alpha=4, beta=6, min_val=0.2, max_val=0.5)  # How much review blocks flow
    )
    
    # Testing bottleneck severity
    distributions.add_distribution(
        "testing_bottleneck_factor",
        Beta(alpha=5, beta=5, min_val=0.15, max_val=0.4)
    )
    
    # Deployment window constraints
    distributions.add_distribution(
        "deployment_window_availability",
        Beta(alpha=6, beta=4, min_val=0.5, max_val=1.0)  # % of time can deploy
    )
    
    # Correlations
    # WIP limits affect context switching
    distributions.add_correlation("wip_limit_multiplier", "context_switch_overhead", -0.5)
    
    # Review bottleneck correlates with testing bottleneck
    distributions.add_correlation("review_bottleneck_factor", "testing_bottleneck_factor", 0.4)