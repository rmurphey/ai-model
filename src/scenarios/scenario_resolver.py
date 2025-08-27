"""
Scenario resolution system for clean configuration handling.
Resolves scenario references and extracts distributions for dual-mode analysis.
"""

from typing import Dict, Any, Optional
import copy
from ..model.distributions import (
    ParameterDistributions, 
    create_distribution_from_config,
    Deterministic, Triangular, Beta, Uniform, Normal, LogNormal
)
from ..model.adoption_dynamics import create_adoption_scenario
from ..model.impact_model import create_impact_scenario
from ..model.cost_structure import create_cost_scenario
from ..model.baseline import create_industry_baseline


def resolve_scenario(scenario_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fully resolve a scenario into a clean config with only deterministic values.
    
    This function:
    1. Resolves all 'scenario' references (adoption: mandated, impact: aggressive, etc.)
    2. Extracts 'value' from any dict with {value: x, distribution: y}
    3. Returns a flat, clean config ready for deterministic analysis
    
    Args:
        scenario_config: Raw scenario configuration from YAML
        
    Returns:
        Clean configuration with only simple values (no nested dicts)
    """
    config = copy.deepcopy(scenario_config)
    
    # Resolve baseline
    if 'baseline' in config:
        config['baseline'] = _resolve_baseline(config['baseline'])
    
    # Resolve adoption
    if 'adoption' in config:
        config['adoption'] = _resolve_adoption(config['adoption'])
    
    # Resolve impact
    if 'impact' in config:
        config['impact'] = _resolve_impact(config['impact'])
    
    # Resolve costs
    if 'costs' in config:
        config['costs'] = _resolve_costs(config['costs'])
    
    # Clean any remaining nested values
    config = _extract_values(config)
    
    return config


def _resolve_baseline(baseline_config: Any) -> Dict[str, Any]:
    """Resolve baseline configuration."""
    if isinstance(baseline_config, str):
        # Just a profile string like "enterprise"
        baseline = create_industry_baseline(baseline_config)
        return baseline.__dict__ if hasattr(baseline, '__dict__') else {'profile': baseline_config}
    
    elif isinstance(baseline_config, dict):
        if 'profile' in baseline_config:
            # Has a profile reference, resolve it first
            baseline = create_industry_baseline(baseline_config['profile'])
            result = baseline.__dict__ if hasattr(baseline, '__dict__') else {}
            
            # Override with any specific values
            for key, value in baseline_config.items():
                if key != 'profile':
                    result[key] = _extract_value(value)
            return result
        else:
            # No profile, just extract values
            return _extract_values(baseline_config)
    
    return {}


def _resolve_adoption(adoption_config: Any) -> Dict[str, Any]:
    """Resolve adoption configuration."""
    if isinstance(adoption_config, str):
        # Just a scenario string like "mandated"
        params = create_adoption_scenario(adoption_config)
        return params.__dict__
    
    elif isinstance(adoption_config, dict):
        if 'scenario' in adoption_config:
            # Has a scenario reference, resolve it first
            params = create_adoption_scenario(adoption_config['scenario'])
            result = params.__dict__
            
            # Override with any specific values
            for key, value in adoption_config.items():
                if key != 'scenario':
                    result[key] = _extract_value(value)
            return result
        else:
            # No scenario, just extract values
            return _extract_values(adoption_config)
    
    return {}


def _resolve_impact(impact_config: Any) -> Dict[str, Any]:
    """Resolve impact configuration."""
    if isinstance(impact_config, str):
        # Just a scenario string like "aggressive"
        factors = create_impact_scenario(impact_config)
        return factors.__dict__
    
    elif isinstance(impact_config, dict):
        if 'scenario' in impact_config:
            # Has a scenario reference, resolve it first
            factors = create_impact_scenario(impact_config['scenario'])
            result = factors.__dict__
            
            # Override with any specific values
            for key, value in impact_config.items():
                if key != 'scenario':
                    result[key] = _extract_value(value)
            return result
        else:
            # No scenario, just extract values
            return _extract_values(impact_config)
    
    return {}


def _resolve_costs(costs_config: Any) -> Dict[str, Any]:
    """Resolve costs configuration."""
    if isinstance(costs_config, str):
        # Just a scenario string like "enterprise"
        costs = create_cost_scenario(costs_config)
        return costs.__dict__
    
    elif isinstance(costs_config, dict):
        if 'scenario' in costs_config:
            # Has a scenario reference, resolve it first
            costs = create_cost_scenario(costs_config['scenario'])
            result = costs.__dict__
            
            # Override with any specific values
            for key, value in costs_config.items():
                if key != 'scenario':
                    result[key] = _extract_value(value)
            return result
        else:
            # No scenario, just extract values
            return _extract_values(costs_config)
    
    return {}


def _extract_value(item: Any) -> Any:
    """Extract the deterministic value from a parameter."""
    if isinstance(item, dict):
        if 'value' in item:
            # Has explicit value field
            return item['value']
        elif 'distribution' in item and 'type' not in item:
            # Just a distribution config, extract a representative value
            dist_config = item['distribution']
            return _get_distribution_center(dist_config)
        else:
            # Regular dict, recurse
            return _extract_values(item)
    return item


def _extract_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively extract values from nested configuration."""
    result = {}
    for key, value in config.items():
        result[key] = _extract_value(value)
    return result


def _get_distribution_center(dist_config: Dict[str, Any]) -> float:
    """Get the central/expected value from a distribution config."""
    dist_type = dist_config.get('type', 'deterministic')
    
    if dist_type == 'triangular':
        return dist_config.get('mode', (dist_config.get('min', 0) + dist_config.get('max', 1)) / 2)
    elif dist_type == 'uniform':
        return (dist_config.get('min', 0) + dist_config.get('max', 1)) / 2
    elif dist_type == 'beta':
        # Use the mode of beta distribution
        alpha = dist_config.get('alpha', 2)
        beta = dist_config.get('beta', 2)
        if alpha > 1 and beta > 1:
            mode = (alpha - 1) / (alpha + beta - 2)
        else:
            mode = 0.5
        min_val = dist_config.get('min', 0)
        max_val = dist_config.get('max', 1)
        return min_val + mode * (max_val - min_val)
    elif dist_type == 'normal':
        return dist_config.get('mean', 0)
    elif dist_type == 'lognormal':
        import numpy as np
        mean_log = dist_config.get('mean_log', 0)
        return np.exp(mean_log)
    else:
        # Default or deterministic
        return dist_config.get('value', 0)


def extract_distributions(scenario_config: Dict[str, Any], 
                        auto_generate: bool = True) -> ParameterDistributions:
    """
    Extract distribution definitions from scenario configuration.
    
    Args:
        scenario_config: Raw scenario configuration
        auto_generate: If True, auto-generate distributions for parameters without them
        
    Returns:
        ParameterDistributions object for Monte Carlo simulation
    """
    distributions = ParameterDistributions()
    
    # First resolve the scenario to get base values
    base_config = resolve_scenario(scenario_config)
    
    # Process each section
    for section_name in ['baseline', 'adoption', 'impact', 'costs']:
        if section_name not in scenario_config:
            continue
            
        section_config = scenario_config[section_name]
        
        # Skip if it's just a string reference
        if isinstance(section_config, str):
            # Use auto-generation for scenario references if enabled
            if auto_generate and section_name in base_config:
                _add_auto_distributions(distributions, base_config[section_name], section_name)
            continue
        
        # Process each parameter in the section
        _process_section_distributions(
            distributions, 
            section_config, 
            section_name,
            base_config.get(section_name, {}),
            auto_generate
        )
    
    # Special handling for adoption segments - don't create distributions for them
    # They need to be sampled together to ensure they sum to 1.0
    adoption_segments = ['initial_adopters', 'early_adopters', 'early_majority', 'late_majority', 'laggards']
    for segment in adoption_segments:
        key = f'adoption.{segment}'
        if key in distributions.distributions:
            # Keep them deterministic for now
            value = base_config.get('adoption', {}).get(segment, 0.2)
            distributions.distributions[key] = Deterministic(value=value)
    
    return distributions


def _process_section_distributions(distributions: ParameterDistributions,
                                  section_config: Dict[str, Any],
                                  section_name: str,
                                  base_values: Dict[str, Any],
                                  auto_generate: bool):
    """Process distributions for a configuration section."""
    for param_name, param_config in section_config.items():
        if param_name == 'scenario':
            # Skip scenario references
            continue
            
        full_param_name = f"{section_name}.{param_name}"
        
        if isinstance(param_config, dict) and 'distribution' in param_config:
            # Has explicit distribution
            dist = create_distribution_from_config(param_config['distribution'])
            distributions.add_distribution(full_param_name, dist)
            
        elif auto_generate and param_name in base_values:
            # Auto-generate distribution based on parameter type
            value = base_values[param_name]
            if isinstance(value, (int, float)):
                dist = _auto_generate_distribution(param_name, float(value), section_name)
                distributions.add_distribution(full_param_name, dist)


def _add_auto_distributions(distributions: ParameterDistributions,
                           base_values: Dict[str, Any],
                           section_name: str):
    """Add auto-generated distributions for all numeric parameters."""
    for param_name, value in base_values.items():
        if isinstance(value, (int, float)):
            full_param_name = f"{section_name}.{param_name}"
            dist = _auto_generate_distribution(param_name, float(value), section_name)
            distributions.add_distribution(full_param_name, dist)


def _auto_generate_distribution(param_name: str, value: float, section: str):
    """Auto-generate appropriate distribution based on parameter semantics."""
    param_lower = param_name.lower()
    
    # Rates and percentages (0-1 bounded)
    if any(term in param_lower for term in ['rate', 'percentage', 'ratio', 'efficiency', 'multiplier']):
        if 0 <= value <= 1:
            # Use beta distribution for bounded percentages
            if value <= 0.1:
                alpha, beta = 2, 18
            elif value >= 0.9:
                alpha, beta = 18, 2
            else:
                alpha, beta = 4, 4
            
            min_val = max(0, value - 0.2)
            max_val = min(1, value + 0.2)
            return Beta(alpha=alpha, beta=beta, min_val=min_val, max_val=max_val)
        else:
            # Multiplier > 1
            return Triangular(min_val=value * 0.8, mode=value, max_val=value * 1.3)
    
    # Time-based parameters
    elif any(term in param_lower for term in ['days', 'hours', 'time', 'cycle', 'month']):
        return Triangular(min_val=value * 0.75, mode=value, max_val=value * 1.5)
    
    # Counts and sizes
    elif any(term in param_lower for term in ['size', 'count', 'number']) or param_name == 'team_size':
        if value >= 20:
            return Uniform(min_val=value * 0.7, max_val=value * 1.3)
        else:
            return Triangular(min_val=max(1, value * 0.5), mode=value, max_val=value * 1.5)
    
    # Costs
    elif any(term in param_lower for term in ['cost', 'price', 'spend']) or section == 'costs':
        import numpy as np
        std_log = 0.2
        mean_log = np.log(value) if value > 0 else 0
        return LogNormal(mean_log=mean_log, std_log=std_log, 
                        min_val=value * 0.5, max_val=value * 2.0)
    
    # Default
    else:
        return Triangular(min_val=value * 0.8, mode=value, max_val=value * 1.2)


def apply_overrides(config: Dict[str, Any], overrides: Dict[str, Any]):
    """
    Apply command-line overrides to resolved configuration.
    
    Args:
        config: Resolved configuration (modified in place)
        overrides: Override values from command line
    """
    if 'team_size' in overrides:
        if 'baseline' not in config:
            config['baseline'] = {}
        config['baseline']['team_size'] = overrides['team_size']
    
    # Note: adoption, impact, and costs overrides are scenario references
    # They should be resolved before getting here
    # This function only handles simple value overrides