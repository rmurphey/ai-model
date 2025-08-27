"""
Adoption dynamics model for AI-assisted development.
Models realistic adoption curves, learning effects, and abandonment patterns.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.stats import beta
from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio, validate_ratios_sum_to_one
from ..utils.exceptions import CalculationError, ValidationError
from ..config.constants import RATIO_SUM_TOLERANCE, MAX_ADOPTION_RATE

@dataclass
class AdoptionParameters:
    """Parameters controlling adoption dynamics"""
    
    # Initial adoption
    initial_adopters: float           # % who adopt immediately (innovators)
    early_adopters: float             # % who adopt in first 3 months
    early_majority: float             # % who adopt in months 4-9
    late_majority: float              # % who adopt in months 10-18
    laggards: float                   # % who never adopt or adopt very late
    
    # Adoption speed factors
    training_effectiveness: float      # How well training drives adoption (0-1)
    peer_influence: float             # Network effect strength (0-1)
    management_mandate: float         # Strength of top-down push (0-1)
    
    # Resistance and dropout
    initial_resistance: float         # % who resist initially
    dropout_rate_month: float         # Monthly dropout rate
    re_engagement_rate: float         # Rate of dropouts who try again
    
    # Learning curve parameters
    initial_efficiency: float         # Efficiency on day 1 (0-1)
    learning_rate: float              # How fast users improve
    plateau_efficiency: float         # Maximum efficiency achieved
    
    # Segment-specific adoption
    junior_adoption_multiplier: float
    mid_adoption_multiplier: float
    senior_adoption_multiplier: float
    
    def __post_init__(self):
        """Validate all adoption parameters"""
        # Validate adoption segment ratios
        validate_ratio(self.initial_adopters, "initial_adopters")
        validate_ratio(self.early_adopters, "early_adopters")
        validate_ratio(self.early_majority, "early_majority")
        validate_ratio(self.late_majority, "late_majority")
        validate_ratio(self.laggards, "laggards")
        
        # Validate adoption segments sum to 1.0
        adoption_segments = {
            "initial_adopters": self.initial_adopters,
            "early_adopters": self.early_adopters,
            "early_majority": self.early_majority,
            "late_majority": self.late_majority,
            "laggards": self.laggards
        }
        validate_ratios_sum_to_one(adoption_segments, RATIO_SUM_TOLERANCE, "adoption segments")
        
        # Validate factor ratios
        validate_ratio(self.training_effectiveness, "training_effectiveness")
        validate_ratio(self.peer_influence, "peer_influence")
        validate_ratio(self.management_mandate, "management_mandate")
        validate_ratio(self.initial_resistance, "initial_resistance")
        validate_ratio(self.initial_efficiency, "initial_efficiency")
        validate_ratio(self.plateau_efficiency, "plateau_efficiency")
        
        # Validate rates (can be higher than 1.0 for some)
        validate_positive(self.dropout_rate_month, "dropout_rate_month")
        validate_positive(self.re_engagement_rate, "re_engagement_rate")
        validate_positive(self.learning_rate, "learning_rate")
        
        # Validate multipliers
        validate_positive(self.junior_adoption_multiplier, "junior_adoption_multiplier")
        validate_positive(self.mid_adoption_multiplier, "mid_adoption_multiplier")
        validate_positive(self.senior_adoption_multiplier, "senior_adoption_multiplier")
        
        # Logical validations
        if self.initial_efficiency >= self.plateau_efficiency:
            raise ValidationError(
                field_name="efficiency_parameters",
                value=f"initial: {self.initial_efficiency}, plateau: {self.plateau_efficiency}",
                expected="initial_efficiency < plateau_efficiency",
                suggestion="Learning curves require initial efficiency to be lower than final plateau",
                valid_examples=[
                    "initial_efficiency: 0.3, plateau_efficiency: 0.8",
                    "initial_efficiency: 0.5, plateau_efficiency: 0.9",
                    "initial_efficiency: 0.2, plateau_efficiency: 0.7"
                ]
            )


class AdoptionModel:
    """Models adoption dynamics over time"""
    
    def __init__(self, parameters: AdoptionParameters):
        self.params = parameters
        
    def s_curve(self, month: int, steepness: float = 0.5) -> float:
        """Classic S-curve adoption model"""
        midpoint = 9  # Adoption midpoint at month 9
        return 1 / (1 + np.exp(-steepness * (month - midpoint)))
    
    def bass_diffusion(self, month: int, p: float = 0.03, q: float = 0.38) -> float:
        """Bass diffusion model for technology adoption
        p: coefficient of innovation
        q: coefficient of imitation
        """
        if month == 0:
            return 0
        
        # Cumulative adoption
        F = 1 - np.exp(-(p + q) * month)
        
        # Adjust for maximum adoption
        max_adoption = 1 - self.params.laggards
        return F * max_adoption
    
    def calculate_adoption_curve(self, months: int = 24) -> np.ndarray:
        """Calculate month-by-month adoption rates"""
        
        adoption = np.zeros(months)
        active_users = np.zeros(months)
        dropouts = np.zeros(months)
        
        for month in range(months):
            # New adopters this month (using Bass model)
            if month == 0:
                new_adopters = self.params.initial_adopters
            else:
                potential_adoption = self.bass_diffusion(month)
                previous_adoption = self.bass_diffusion(month - 1) if month > 0 else 0
                new_adopters = potential_adoption - previous_adoption
            
            # Apply segment multipliers
            weighted_adopters = new_adopters  # Simplified for now
            
            # Calculate dropouts
            if month > 0:
                month_dropouts = active_users[month-1] * self.params.dropout_rate_month
                dropouts[month] = month_dropouts
                
                # Some dropouts re-engage
                re_engaged = dropouts[:month].sum() * safe_divide(
                    self.params.re_engagement_rate,
                    month,
                    default=0.0,
                    context="re-engagement rate calculation"
                )
                
                active_users[month] = active_users[month-1] + weighted_adopters - month_dropouts + re_engaged
            else:
                active_users[month] = weighted_adopters
            
            adoption[month] = active_users[month]
        
        return adoption
    
    def calculate_efficiency_curve(self, months: int = 24) -> np.ndarray:
        """Calculate average efficiency of adopted users over time"""
        
        efficiency = np.zeros(months)
        
        for month in range(months):
            # Learning curve: efficiency = initial + (plateau - initial) * (1 - exp(-rate * time))
            month_efficiency = (
                self.params.initial_efficiency + 
                (self.params.plateau_efficiency - self.params.initial_efficiency) * 
                (1 - np.exp(-self.params.learning_rate * month))
            )
            efficiency[month] = month_efficiency
        
        return efficiency
    
    def calculate_effective_adoption(self, months: int = 24) -> np.ndarray:
        """Calculate effective adoption (adoption × efficiency)"""
        
        adoption = self.calculate_adoption_curve(months)
        efficiency = self.calculate_efficiency_curve(months)
        
        return adoption * efficiency
    
    def get_peak_adoption(self, months: int = 24) -> float:
        """Get the peak adoption rate achieved"""
        adoption = self.calculate_adoption_curve(months)
        return np.max(adoption)
    
    def segment_adoption(self, baseline_team: Dict[str, float]) -> Dict[str, np.ndarray]:
        """Calculate adoption by developer segment"""
        
        segments = {
            "junior": self.params.junior_adoption_multiplier,
            "mid": self.params.mid_adoption_multiplier,
            "senior": self.params.senior_adoption_multiplier
        }
        
        base_adoption = self.calculate_adoption_curve()
        segment_curves = {}
        
        for segment, multiplier in segments.items():
            # Apply multiplier with ceiling at max adoption rate
            segment_curves[segment] = np.minimum(base_adoption * multiplier, MAX_ADOPTION_RATE)
        
        return segment_curves
    
    def calculate_network_effects(self, current_adoption: float) -> float:
        """Calculate network effect multiplier based on current adoption"""
        
        # Network effects accelerate adoption when critical mass is reached
        if current_adoption < 0.1:
            return 1.0  # No network effect yet
        elif current_adoption < 0.3:
            return 1.0 + self.params.peer_influence * 0.5
        elif current_adoption < 0.5:
            return 1.0 + self.params.peer_influence * 1.0
        else:
            return 1.0 + self.params.peer_influence * 1.5
    
    def model_resistance_patterns(self) -> Dict[str, float]:
        """Model different resistance patterns and their prevalence"""
        
        patterns = {
            "enthusiastic_adopter": 0.15,     # Adopt immediately and champion
            "pragmatic_adopter": 0.35,        # Adopt after seeing benefits
            "skeptical_adopter": 0.30,        # Adopt only with proof
            "forced_adopter": 0.15,           # Adopt only if mandated
            "never_adopter": 0.05             # Will never effectively adopt
        }
        
        return patterns
    
    def calculate_training_impact(self, training_investment: float) -> float:
        """Calculate adoption boost from training investment"""
        
        # Diminishing returns on training investment
        # Model as log curve: boost = effectiveness * log(1 + investment/baseline)
        baseline_training = 10000  # Baseline training cost per developer
        
        boost = self.params.training_effectiveness * np.log(1 + training_investment / baseline_training)
        
        return min(boost, 0.3)  # Cap at 30% adoption boost


def create_adoption_scenario(scenario_or_params = "organic") -> AdoptionParameters:
    """Create adoption parameters for different scenarios or custom parameters"""
    
    # If a dict is passed, check for 'scenario' key or use dict directly
    if isinstance(scenario_or_params, dict):
        if 'scenario' in scenario_or_params:
            scenario = scenario_or_params['scenario']
        else:
            # Custom parameters provided - create directly
            return AdoptionParameters(**scenario_or_params)
    else:
        scenario = scenario_or_params
    
    scenarios = {
        "organic": AdoptionParameters(
            initial_adopters=0.05,
            early_adopters=0.15,
            early_majority=0.35,
            late_majority=0.30,
            laggards=0.15,
            training_effectiveness=0.5,
            peer_influence=0.7,
            management_mandate=0.3,
            initial_resistance=0.4,
            dropout_rate_month=0.02,  # Reduced from 5% to 2%
            re_engagement_rate=0.03,  # Increased re-engagement
            initial_efficiency=0.3,
            learning_rate=0.3,
            plateau_efficiency=0.85,
            junior_adoption_multiplier=1.3,
            mid_adoption_multiplier=1.0,
            senior_adoption_multiplier=0.7
        ),
        
        "mandated": AdoptionParameters(
            initial_adopters=0.20,
            early_adopters=0.30,
            early_majority=0.30,
            late_majority=0.15,
            laggards=0.05,
            training_effectiveness=0.7,
            peer_influence=0.5,
            management_mandate=0.9,
            initial_resistance=0.2,
            dropout_rate_month=0.03,  # Reduced from 8% to 3%
            re_engagement_rate=0.05,
            initial_efficiency=0.25,  # Lower initial efficiency when forced
            learning_rate=0.25,
            plateau_efficiency=0.80,
            junior_adoption_multiplier=1.1,
            mid_adoption_multiplier=1.0,
            senior_adoption_multiplier=0.9
        ),
        
        "grassroots": AdoptionParameters(
            initial_adopters=0.10,
            early_adopters=0.20,
            early_majority=0.30,
            late_majority=0.25,
            laggards=0.15,
            training_effectiveness=0.4,
            peer_influence=0.9,
            management_mandate=0.1,
            initial_resistance=0.3,
            dropout_rate_month=0.015,  # Very low dropout with voluntary adoption
            re_engagement_rate=0.04,
            initial_efficiency=0.4,   # Higher initial efficiency for volunteers
            learning_rate=0.4,
            plateau_efficiency=0.90,
            junior_adoption_multiplier=1.5,
            mid_adoption_multiplier=1.2,
            senior_adoption_multiplier=0.6
        )
    }
    
    return scenarios.get(scenario, scenarios["organic"])


def simulate_adoption_monte_carlo(
    base_params: AdoptionParameters,
    n_simulations: int = 1000,
    months: int = 24,
    random_seed: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """Run Monte Carlo simulation of adoption with uncertainty"""
    
    if random_seed is not None:
        np.random.seed(random_seed)
    
    results = []
    
    for _ in range(n_simulations):
        # Add random variation to parameters
        initial_adopters = base_params.initial_adopters * np.random.uniform(0.8, 1.2)
        early_adopters = base_params.early_adopters * np.random.uniform(0.8, 1.2)
        early_majority = base_params.early_majority * np.random.uniform(0.9, 1.1)
        late_majority = base_params.late_majority * np.random.uniform(0.9, 1.1)
        laggards = base_params.laggards  # Keep laggards fixed
        
        # Normalize adoption segments to sum to 1 BEFORE creating params
        total = initial_adopters + early_adopters + early_majority + late_majority + laggards
        initial_adopters /= total
        early_adopters /= total
        early_majority /= total
        late_majority /= total
        laggards /= total
        
        params = AdoptionParameters(
            initial_adopters=initial_adopters,
            early_adopters=early_adopters,
            early_majority=early_majority,
            late_majority=late_majority,
            laggards=laggards,
            training_effectiveness=base_params.training_effectiveness * np.random.uniform(0.7, 1.3),
            peer_influence=base_params.peer_influence * np.random.uniform(0.8, 1.2),
            management_mandate=base_params.management_mandate,
            initial_resistance=base_params.initial_resistance * np.random.uniform(0.8, 1.2),
            dropout_rate_month=base_params.dropout_rate_month * np.random.uniform(0.5, 1.5),
            re_engagement_rate=base_params.re_engagement_rate * np.random.uniform(0.5, 2.0),
            initial_efficiency=base_params.initial_efficiency * np.random.uniform(0.8, 1.2),
            learning_rate=base_params.learning_rate * np.random.uniform(0.7, 1.3),
            plateau_efficiency=base_params.plateau_efficiency * np.random.uniform(0.9, 1.05),
            junior_adoption_multiplier=base_params.junior_adoption_multiplier,
            mid_adoption_multiplier=base_params.mid_adoption_multiplier,
            senior_adoption_multiplier=base_params.senior_adoption_multiplier
        )
        
        model = AdoptionModel(params)
        adoption = model.calculate_effective_adoption(months)
        results.append(adoption)
    
    results = np.array(results)
    
    return {
        "mean": np.mean(results, axis=0),
        "std": np.std(results, axis=0),
        "p10": np.percentile(results, 10, axis=0),
        "p50": np.percentile(results, 50, axis=0),
        "p90": np.percentile(results, 90, axis=0)
    }