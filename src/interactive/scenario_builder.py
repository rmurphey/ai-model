"""
Scenario builder for converting user inputs into model scenarios.
Provides templates and construction methods for different input types.
"""

from typing import Dict, Any, Optional


class ScenarioBuilder:
    """Builds scenario configurations from user inputs."""
    
    def __init__(self):
        """Initialize the scenario builder with default templates."""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined scenario templates."""
        return {
            "startup": {
                "name": "Fast-moving Startup",
                "baseline": {
                    "team_size": 20,
                    "junior_ratio": 0.5,
                    "mid_ratio": 0.35,
                    "senior_ratio": 0.15,
                    "junior_flc": 120000,  # 80k salary * 1.5 for benefits/overhead
                    "mid_flc": 180000,  # 120k salary * 1.5
                    "senior_flc": 240000,  # 160k salary * 1.5
                    "avg_feature_cycle_days": 21,
                    "avg_bug_fix_hours": 6,
                    "onboarding_days": 30,
                    "defect_escape_rate": 12.0,
                    "production_incidents_per_month": 3,
                    "avg_incident_cost": 5000,
                    "rework_percentage": 0.15,
                    "new_feature_percentage": 0.60,
                    "maintenance_percentage": 0.20,
                    "tech_debt_percentage": 0.05,
                    "meetings_percentage": 0.15,
                    "avg_pr_review_hours": 2,
                    "pr_rejection_rate": 0.20
                },
                "adoption": {
                    "scenario": "grassroots",
                    "early_adopter_rate": 0.25,
                    "early_majority_rate": 0.35,
                    "late_majority_rate": 0.25,
                    "laggard_rate": 0.15,
                    "dropout_rate_month": 0.03,
                    "plateau_efficiency": 0.85,
                    "learning_curve_months": 2
                },
                "impact": {
                    "feature_cycle_reduction": 0.35,
                    "bug_fix_reduction": 0.45,
                    "defect_reduction": 0.30,
                    "incident_reduction": 0.35,
                    "onboarding_time_reduction": 0.40,
                    "context_switch_reduction": 0.25,
                    "code_review_time_reduction": 0.30,
                    "documentation_improvement": 0.50
                },
                "costs": {
                    "cost_per_seat_month": 30,
                    "enterprise_discount_threshold": 50,
                    "enterprise_discount_rate": 0.2,
                    "token_price_per_million": 10,
                    "avg_tokens_million_per_user_month": 2,
                    "token_growth_rate_month": 0.1,
                    "token_plateau_month": 6,
                    "training_cost_per_user": 300,
                    "ongoing_training_ratio": 0.1,
                    "context_switch_cost_ratio": 0.15,
                    "bad_code_cleanup_ratio": 0.05
                },
                "timeframe_months": 24
            },
            "enterprise": {
                "name": "Enterprise Software Company",
                "baseline": {
                    "team_size": 200,
                    "junior_ratio": 0.3,
                    "mid_ratio": 0.5,
                    "senior_ratio": 0.2,
                    "junior_flc": 135000,  # 90k salary * 1.5
                    "mid_flc": 195000,  # 130k salary * 1.5
                    "senior_flc": 270000,  # 180k salary * 1.5
                    "avg_feature_cycle_days": 45,
                    "avg_bug_fix_hours": 12,
                    "onboarding_days": 60,
                    "defect_escape_rate": 18.0,
                    "production_incidents_per_month": 8,
                    "avg_incident_cost": 10000,
                    "rework_percentage": 0.20,
                    "new_feature_percentage": 0.45,
                    "maintenance_percentage": 0.35,
                    "tech_debt_percentage": 0.10,
                    "meetings_percentage": 0.10,
                    "avg_pr_review_hours": 4,
                    "pr_rejection_rate": 0.25
                },
                "adoption": {
                    "scenario": "mandated",
                    "early_adopter_rate": 0.15,
                    "early_majority_rate": 0.35,
                    "late_majority_rate": 0.35,
                    "laggard_rate": 0.15,
                    "dropout_rate_month": 0.02,
                    "plateau_efficiency": 0.75,
                    "learning_curve_months": 3
                },
                "impact": {
                    "feature_cycle_reduction": 0.25,
                    "bug_fix_reduction": 0.35,
                    "defect_reduction": 0.20,
                    "incident_reduction": 0.25,
                    "onboarding_time_reduction": 0.30,
                    "context_switch_reduction": 0.20,
                    "code_review_time_reduction": 0.25,
                    "documentation_improvement": 0.40
                },
                "costs": {
                    "cost_per_seat_month": 45,
                    "enterprise_discount_threshold": 100,
                    "enterprise_discount_rate": 0.3,
                    "token_price_per_million": 10,
                    "avg_tokens_million_per_user_month": 1.5,
                    "token_growth_rate_month": 0.05,
                    "token_plateau_month": 9,
                    "training_cost_per_user": 1000,
                    "ongoing_training_ratio": 0.15,
                    "context_switch_cost_ratio": 0.10,
                    "bad_code_cleanup_ratio": 0.03
                },
                "timeframe_months": 36
            },
            "fintech": {
                "name": "Financial Services Company",
                "baseline": {
                    "team_size": 100,
                    "junior_ratio": 0.2,
                    "mid_ratio": 0.5,
                    "senior_ratio": 0.3,
                    "junior_flc": 150000,  # 100k salary * 1.5
                    "mid_flc": 225000,  # 150k salary * 1.5
                    "senior_flc": 300000,  # 200k salary * 1.5
                    "avg_feature_cycle_days": 60,
                    "avg_bug_fix_hours": 16,
                    "onboarding_days": 90,
                    "defect_escape_rate": 8.0,
                    "production_incidents_per_month": 2,
                    "avg_incident_cost": 25000,
                    "rework_percentage": 0.12,
                    "new_feature_percentage": 0.35,
                    "maintenance_percentage": 0.40,
                    "tech_debt_percentage": 0.15,
                    "meetings_percentage": 0.10,
                    "avg_pr_review_hours": 6,
                    "pr_rejection_rate": 0.30
                },
                "adoption": {
                    "scenario": "organic",
                    "early_adopter_rate": 0.10,
                    "early_majority_rate": 0.25,
                    "late_majority_rate": 0.40,
                    "laggard_rate": 0.25,
                    "dropout_rate_month": 0.01,
                    "plateau_efficiency": 0.70,
                    "learning_curve_months": 4
                },
                "impact": {
                    "feature_cycle_reduction": 0.20,
                    "bug_fix_reduction": 0.30,
                    "defect_reduction": 0.25,
                    "incident_reduction": 0.30,
                    "onboarding_time_reduction": 0.25,
                    "context_switch_reduction": 0.15,
                    "code_review_time_reduction": 0.20,
                    "documentation_improvement": 0.35
                },
                "costs": {
                    "cost_per_seat_month": 50,
                    "enterprise_discount_threshold": 50,
                    "enterprise_discount_rate": 0.25,
                    "token_price_per_million": 10,
                    "avg_tokens_million_per_user_month": 1,
                    "token_growth_rate_month": 0.03,
                    "token_plateau_month": 12,
                    "training_cost_per_user": 1500,
                    "ongoing_training_ratio": 0.2,
                    "context_switch_cost_ratio": 0.08,
                    "bad_code_cleanup_ratio": 0.02
                },
                "timeframe_months": 36
            },
            "ecommerce": {
                "name": "E-commerce/SaaS Company",
                "baseline": {
                    "team_size": 75,
                    "junior_ratio": 0.4,
                    "mid_ratio": 0.4,
                    "senior_ratio": 0.2,
                    "junior_flc": 127500,  # 85k salary * 1.5
                    "mid_flc": 187500,  # 125k salary * 1.5
                    "senior_flc": 255000,  # 170k salary * 1.5
                    "avg_feature_cycle_days": 30,
                    "avg_bug_fix_hours": 8,
                    "onboarding_days": 45,
                    "defect_escape_rate": 15.0,
                    "production_incidents_per_month": 5,
                    "avg_incident_cost": 7500,
                    "rework_percentage": 0.18,
                    "new_feature_percentage": 0.50,
                    "maintenance_percentage": 0.30,
                    "tech_debt_percentage": 0.10,
                    "meetings_percentage": 0.10,
                    "avg_pr_review_hours": 3,
                    "pr_rejection_rate": 0.22
                },
                "adoption": {
                    "scenario": "organic",
                    "early_adopter_rate": 0.20,
                    "early_majority_rate": 0.35,
                    "late_majority_rate": 0.30,
                    "laggard_rate": 0.15,
                    "dropout_rate_month": 0.025,
                    "plateau_efficiency": 0.80,
                    "learning_curve_months": 2.5
                },
                "impact": {
                    "feature_cycle_reduction": 0.30,
                    "bug_fix_reduction": 0.40,
                    "defect_reduction": 0.25,
                    "incident_reduction": 0.30,
                    "onboarding_time_reduction": 0.35,
                    "context_switch_reduction": 0.20,
                    "code_review_time_reduction": 0.25,
                    "documentation_improvement": 0.45
                },
                "costs": {
                    "cost_per_seat_month": 35,
                    "enterprise_discount_threshold": 50,
                    "enterprise_discount_rate": 0.2,
                    "token_price_per_million": 10,
                    "avg_tokens_million_per_user_month": 1.8,
                    "token_growth_rate_month": 0.08,
                    "token_plateau_month": 6,
                    "training_cost_per_user": 500,
                    "ongoing_training_ratio": 0.12,
                    "context_switch_cost_ratio": 0.12,
                    "bad_code_cleanup_ratio": 0.04
                },
                "timeframe_months": 24
            }
        }
    
    def build_from_template(self, template_key: str) -> Dict[str, Any]:
        """Build a scenario from a predefined template."""
        if template_key not in self.templates:
            raise ValueError(f"Unknown template: {template_key}")
        
        return self.templates[template_key].copy()
    
    def build_quick_scenario(
        self,
        team_size: int,
        junior_ratio: float,
        mid_ratio: float,
        senior_ratio: float,
        adoption_strategy: str,
        impact_level: str,
        timeframe_months: int,
        custom_impact_value: Optional[float] = None,
        custom_impact_details: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Build a scenario from quick setup inputs."""
        
        # Handle custom impact details first
        if custom_impact_details is not None:
            # Use the specific values provided by the user
            impacts = {
                "feature_cycle_reduction": custom_impact_details.get("feature_cycle_reduction", 0.30),
                "bug_fix_reduction": custom_impact_details.get("bug_fix_reduction", 0.40),
                "defect_reduction": custom_impact_details.get("defect_reduction", 0.25),
                "incident_reduction": custom_impact_details.get("incident_reduction", 0.30),
                # Add related improvements with reasonable defaults based on primary metrics
                "onboarding_time_reduction": custom_impact_details.get("feature_cycle_reduction", 0.30) * 1.2,
                "context_switch_reduction": custom_impact_details.get("feature_cycle_reduction", 0.30) * 0.67,
                "code_review_time_reduction": custom_impact_details.get("bug_fix_reduction", 0.40) * 0.625,
                "documentation_improvement": custom_impact_details.get("defect_reduction", 0.25) * 1.8
            }
            # Cap all values at 0.7 (70% improvement max)
            impacts = {k: min(v, 0.7) for k, v in impacts.items()}
        elif custom_impact_value is not None:
            # Use custom value to calculate multiplier
            # custom_impact_value is already a decimal (e.g., 0.25 for 25%)
            # Map it to a multiplier (0.25 → ~0.8, 0.50 → ~1.6)
            multiplier = custom_impact_value * 3.2  # Scale to reasonable range
            
            # Base impact values (moderate)
            base_impacts = {
                "feature_cycle_reduction": 0.30,
                "bug_fix_reduction": 0.40,
                "defect_reduction": 0.25,
                "incident_reduction": 0.30,
                "onboarding_time_reduction": 0.35,
                "context_switch_reduction": 0.20,
                "code_review_time_reduction": 0.25,
                "documentation_improvement": 0.45
            }
            
            # Apply multiplier
            impacts = {k: min(v * multiplier, 0.7) for k, v in base_impacts.items()}
        else:
            # Use predefined impact levels
            impact_multipliers = {
                "conservative": 0.6,
                "moderate": 1.0,
                "aggressive": 1.4,
                "custom": 1.0  # Fallback if somehow custom wasn't handled
            }
            multiplier = impact_multipliers.get(impact_level, 1.0)
            
            # Base impact values (moderate)
            base_impacts = {
                "feature_cycle_reduction": 0.30,
                "bug_fix_reduction": 0.40,
                "defect_reduction": 0.25,
                "incident_reduction": 0.30,
                "onboarding_time_reduction": 0.35,
                "context_switch_reduction": 0.20,
                "code_review_time_reduction": 0.25,
                "documentation_improvement": 0.45
            }
            
            # Apply multiplier
            impacts = {k: min(v * multiplier, 0.7) for k, v in base_impacts.items()}
        
        # Map adoption strategy to parameters
        adoption_params = {
            "organic": {
                "early_adopter_rate": 0.15,
                "early_majority_rate": 0.35,
                "late_majority_rate": 0.35,
                "laggard_rate": 0.15,
                "dropout_rate_month": 0.02,
                "plateau_efficiency": 0.75,
                "learning_curve_months": 3
            },
            "mandated": {
                "early_adopter_rate": 0.10,
                "early_majority_rate": 0.30,
                "late_majority_rate": 0.40,
                "laggard_rate": 0.20,
                "dropout_rate_month": 0.025,
                "plateau_efficiency": 0.70,
                "learning_curve_months": 4
            },
            "hybrid": {
                "early_adopter_rate": 0.20,
                "early_majority_rate": 0.35,
                "late_majority_rate": 0.30,
                "laggard_rate": 0.15,
                "dropout_rate_month": 0.02,
                "plateau_efficiency": 0.78,
                "learning_curve_months": 2.5
            }
        }
        
        return {
            "name": f"Quick Setup - {adoption_strategy.title()} {impact_level.title()}",
            "baseline": {
                "team_size": team_size,
                "junior_ratio": junior_ratio,
                "mid_ratio": mid_ratio,
                "senior_ratio": senior_ratio,
                "junior_flc": 127500,  # 85k salary * 1.5 for benefits/overhead
                "mid_flc": 187500,  # 125k salary * 1.5
                "senior_flc": 255000,  # 170k salary * 1.5
                "avg_feature_cycle_days": 30,
                "avg_bug_fix_hours": 8,
                "onboarding_days": 45,
                "defect_escape_rate": 15.0,
                "production_incidents_per_month": 5,
                "avg_incident_cost": 7500,
                "rework_percentage": 0.18,
                "new_feature_percentage": 0.50,
                "maintenance_percentage": 0.30,
                "tech_debt_percentage": 0.10,
                "meetings_percentage": 0.10,
                "avg_pr_review_hours": 3,
                "pr_rejection_rate": 0.22
            },
            "adoption": {
                "scenario": adoption_strategy,
                **adoption_params.get(adoption_strategy, adoption_params["organic"])
            },
            "impact": impacts,
            "costs": {
                "cost_per_seat_month": 30,
                "enterprise_discount_threshold": 50,
                "enterprise_discount_rate": 0.2,
                "token_price_per_million": 10,
                "avg_tokens_million_per_user_month": 2,
                "token_growth_rate_month": 0.08,
                "token_plateau_month": 6,
                "training_cost_per_user": 500,
                "ongoing_training_ratio": 0.1,
                "context_switch_cost_ratio": 0.12,
                "bad_code_cleanup_ratio": 0.04
            },
            "timeframe_months": timeframe_months
        }
    
    def build_detailed_scenario(
        self,
        # Baseline parameters
        team_size: int,
        junior_ratio: float,
        mid_ratio: float,
        senior_ratio: float,
        avg_feature_cycle_days: float,
        avg_bug_fix_hours: float,
        monthly_incidents: float,
        defect_rate_per_kloc: float,
        
        # Adoption parameters
        adoption_strategy: str,
        plateau_adoption_rate: float,
        time_to_plateau_months: int,
        monthly_dropout_rate: float,
        
        # Impact parameters
        feature_cycle_reduction: float,
        bug_fix_reduction: float,
        defect_reduction: float,
        incident_reduction: float,
        
        # Cost parameters
        cost_per_seat_month: float,
        avg_tokens_million_per_user_month: float,
        training_cost_per_user: float,
        
        # Timeframe
        timeframe_months: int,
        
        # Optional parameters with defaults
        avg_junior_salary: float = 85000,
        avg_mid_salary: float = 125000,
        avg_senior_salary: float = 170000,
        flc_multiplier: float = 1.5,  # Fully-loaded cost multiplier
        onboarding_days: float = 45,
        avg_incident_cost: float = 7500,
        rework_percentage: float = 0.18,
        new_feature_percentage: float = 0.50,
        maintenance_percentage: float = 0.30,
        tech_debt_percentage: float = 0.10,
        meetings_percentage: float = 0.10,
        avg_pr_review_hours: float = 3,
        pr_rejection_rate: float = 0.22,
        onboarding_time_reduction: float = 0.35,
        context_switch_reduction: float = 0.20,
        code_review_time_reduction: float = 0.25,
        documentation_improvement: float = 0.45,
        enterprise_discount_threshold: int = 50,
        enterprise_discount_rate: float = 0.2,
        token_price_per_million: float = 10,
        token_growth_rate_month: float = 0.08,
        token_plateau_month: int = 6,
        ongoing_training_ratio: float = 0.1,
        context_switch_cost_ratio: float = 0.12,
        bad_code_cleanup_ratio: float = 0.04,
        learning_curve_months: float = 3,
        plateau_efficiency: float = 0.75
    ) -> Dict[str, Any]:
        """Build a detailed scenario from all parameters."""
        
        # Calculate adoption segment rates based on plateau
        total_adoption = plateau_adoption_rate
        early_adopter_rate = min(0.15, total_adoption * 0.2)
        early_majority_rate = min(0.35, total_adoption * 0.4)
        late_majority_rate = min(0.35, total_adoption * 0.3)
        laggard_rate = max(0, total_adoption - early_adopter_rate - early_majority_rate - late_majority_rate)
        
        return {
            "name": f"Detailed Setup - {adoption_strategy.title()}",
            "baseline": {
                "team_size": team_size,
                "junior_ratio": junior_ratio,
                "mid_ratio": mid_ratio,
                "senior_ratio": senior_ratio,
                "junior_flc": avg_junior_salary * flc_multiplier,  # Convert salary to FLC
                "mid_flc": avg_mid_salary * flc_multiplier,
                "senior_flc": avg_senior_salary * flc_multiplier,
                "avg_feature_cycle_days": avg_feature_cycle_days,
                "avg_bug_fix_hours": avg_bug_fix_hours,
                "onboarding_days": onboarding_days,
                "defect_escape_rate": defect_rate_per_kloc,
                "production_incidents_per_month": monthly_incidents,
                "avg_incident_cost": avg_incident_cost,
                "rework_percentage": rework_percentage,
                "new_feature_percentage": new_feature_percentage,
                "maintenance_percentage": maintenance_percentage,
                "tech_debt_percentage": tech_debt_percentage,
                "meetings_percentage": meetings_percentage,
                "avg_pr_review_hours": avg_pr_review_hours,
                "pr_rejection_rate": pr_rejection_rate
            },
            "adoption": {
                "scenario": adoption_strategy,
                "early_adopter_rate": early_adopter_rate,
                "early_majority_rate": early_majority_rate,
                "late_majority_rate": late_majority_rate,
                "laggard_rate": laggard_rate,
                "dropout_rate_month": monthly_dropout_rate,
                "plateau_efficiency": plateau_efficiency,
                "learning_curve_months": learning_curve_months,
                "time_to_plateau_months": time_to_plateau_months
            },
            "impact": {
                "feature_cycle_reduction": feature_cycle_reduction,
                "bug_fix_reduction": bug_fix_reduction,
                "defect_reduction": defect_reduction,
                "incident_reduction": incident_reduction,
                "onboarding_time_reduction": onboarding_time_reduction,
                "context_switch_reduction": context_switch_reduction,
                "code_review_time_reduction": code_review_time_reduction,
                "documentation_improvement": documentation_improvement
            },
            "costs": {
                "cost_per_seat_month": cost_per_seat_month,
                "enterprise_discount_threshold": enterprise_discount_threshold,
                "enterprise_discount_rate": enterprise_discount_rate,
                "token_price_per_million": token_price_per_million,
                "avg_tokens_million_per_user_month": avg_tokens_million_per_user_month,
                "token_growth_rate_month": token_growth_rate_month,
                "token_plateau_month": token_plateau_month,
                "training_cost_per_user": training_cost_per_user,
                "ongoing_training_ratio": ongoing_training_ratio,
                "context_switch_cost_ratio": context_switch_cost_ratio,
                "bad_code_cleanup_ratio": bad_code_cleanup_ratio
            },
            "timeframe_months": timeframe_months
        }
    
    def merge_with_defaults(self, partial_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a partial scenario with default values."""
        # Use enterprise template as base defaults
        defaults = self.templates["enterprise"].copy()
        
        # Deep merge the partial scenario
        def deep_merge(base: Dict, override: Dict) -> Dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(defaults, partial_scenario)