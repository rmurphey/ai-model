"""
Modular scenario loader supporting both legacy single-file and new directory structure.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache
from ..utils.exceptions import ConfigurationError
from ..utils.cache import smart_cache, memoized_method


class ScenarioLoader:
    """Loads scenarios from modular directory structure."""
    
    def __init__(self, scenarios_path: str = "src/scenarios"):
        """
        Initialize scenario loader.
        
        Args:
            scenarios_path: Path to scenarios directory
        """
        self.scenarios_path = Path(scenarios_path)
        self._cache = {}
        self._profiles = {}
        self._strategies = {}
        self._distributions = {}
        
        # Only support modular directory structure
        if not self.scenarios_path.is_dir():
            raise ConfigurationError(
                f"Invalid scenarios path: {scenarios_path}",
                config_file=str(scenarios_path),
                resolution_steps=[
                    "Provide a valid directory path",
                    "Check that the directory exists",
                    "Ensure you're running from the project root"
                ]
            )
        
        self._load_components()
    
    @memoized_method(maxsize=32)
    def load_all_scenarios(self) -> Dict[str, Any]:
        """Load all available scenarios."""
        return self._load_modular_scenarios()
    
    def load_scenario(self, name: str) -> Dict[str, Any]:
        """Load a specific scenario by name."""
        if name in self._cache:
            return self._cache[name]
        
        scenario = self._load_modular_scenario(name)
        self._cache[name] = scenario
        return scenario
    
    
    def _load_components(self):
        """Load reusable components (profiles, strategies, distributions)."""
        # Load profiles
        profiles_dir = self.scenarios_path / "profiles"
        if profiles_dir.exists():
            for file in profiles_dir.glob("*.yaml"):
                try:
                    with open(file, 'r') as f:
                        profile = yaml.safe_load(f)
                        self._profiles[file.stem] = profile
                except yaml.YAMLError as e:
                    raise ConfigurationError(
                        f"Invalid YAML format in profile {file}",
                        config_file=str(file),
                        resolution_steps=[
                            "Check YAML syntax in the profile file",
                            f"Error: {str(e)}"
                        ]
                    )
        
        # Load strategies
        strategies_dir = self.scenarios_path / "strategies"
        if strategies_dir.exists():
            for file in strategies_dir.glob("*.yaml"):
                try:
                    with open(file, 'r') as f:
                        strategy = yaml.safe_load(f)
                        self._strategies[file.stem] = strategy
                except yaml.YAMLError as e:
                    raise ConfigurationError(
                        f"Invalid YAML format in strategy {file}",
                        config_file=str(file),
                        resolution_steps=[
                            "Check YAML syntax in the strategy file",
                            f"Error: {str(e)}"
                        ]
                    )
        
        # Load distributions
        distributions_dir = self.scenarios_path / "distributions"
        if distributions_dir.exists():
            for file in distributions_dir.glob("*.yaml"):
                try:
                    with open(file, 'r') as f:
                        dist = yaml.safe_load(f)
                        self._distributions[file.stem] = dist
                except yaml.YAMLError as e:
                    raise ConfigurationError(
                        f"Invalid YAML format in distribution {file}",
                        config_file=str(file),
                        resolution_steps=[
                            "Check YAML syntax in the distribution file",
                            f"Error: {str(e)}"
                        ]
                    )
    
    def _load_modular_scenarios(self) -> Dict[str, Any]:
        """Load all scenarios from modular directory structure."""
        scenarios = {}
        
        # Load deterministic scenarios
        det_dir = self.scenarios_path / "scenarios" / "deterministic"
        if det_dir.exists():
            for file in det_dir.glob("*.yaml"):
                scenario = self._load_scenario_file(file)
                scenarios[file.stem] = scenario
        
        # Load Monte Carlo scenarios
        mc_dir = self.scenarios_path / "scenarios" / "monte_carlo"
        if mc_dir.exists():
            for file in mc_dir.glob("*.yaml"):
                scenario = self._load_scenario_file(file)
                scenarios[f"{file.stem}_monte_carlo"] = scenario
        
        return scenarios
    
    def _load_modular_scenario(self, name: str) -> Dict[str, Any]:
        """Load a specific scenario from modular structure."""
        # Check various possible locations
        possible_files = [
            self.scenarios_path / "scenarios" / "deterministic" / f"{name}.yaml",
            self.scenarios_path / "scenarios" / "monte_carlo" / f"{name}.yaml",
            self.scenarios_path / "scenarios" / "monte_carlo" / f"{name.replace('_monte_carlo', '')}.yaml",
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                return self._load_scenario_file(file_path)
        
        raise ConfigurationError(
            f"Scenario '{name}' not found",
            config_file=str(self.scenarios_path),
            resolution_steps=[
                "Check scenario name spelling",
                f"Look in {self.scenarios_path / 'scenarios'}",
                "Use --list-scenarios to see available scenarios"
            ]
        )
    
    def _load_scenario_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and compose a scenario from a file."""
        try:
            with open(file_path, 'r') as f:
                scenario = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML format in {file_path}",
                config_file=str(file_path),
                resolution_steps=[
                    "Check YAML syntax using a validator",
                    "Ensure proper indentation (use spaces, not tabs)",
                    "Check for missing colons or dashes",
                    f"Error details: {str(e)}"
                ]
            )
        
        # Handle composition if 'extends' is specified
        if 'extends' in scenario:
            composed = {}
            for component_ref in scenario['extends']:
                component = self._load_component(component_ref)
                composed = self._deep_merge(composed, component)
            
            # Remove 'extends' from scenario and merge
            scenario_without_extends = {k: v for k, v in scenario.items() if k != 'extends'}
            composed = self._deep_merge(composed, scenario_without_extends)
            return composed
        
        return scenario
    
    def _load_component(self, component_ref: str) -> Dict[str, Any]:
        """Load a component (profile, strategy, or distribution)."""
        parts = component_ref.split('/')
        
        if len(parts) != 2:
            raise ConfigurationError(
                f"Invalid component reference: {component_ref}",
                config_file="scenario file",
                resolution_steps=[
                    "Use format: 'type/name' (e.g., 'profiles/startup')",
                    "Valid types: profiles, strategies, distributions"
                ]
            )
        
        component_type, component_name = parts
        
        if component_type == 'profiles':
            if component_name not in self._profiles:
                raise ConfigurationError(
                    f"Profile '{component_name}' not found",
                    config_file=f"profiles/{component_name}.yaml"
                )
            return self._profiles[component_name]
        elif component_type == 'strategies':
            if component_name not in self._strategies:
                raise ConfigurationError(
                    f"Strategy '{component_name}' not found",
                    config_file=f"strategies/{component_name}.yaml"
                )
            return self._strategies[component_name]
        elif component_type == 'distributions':
            if component_name not in self._distributions:
                raise ConfigurationError(
                    f"Distribution '{component_name}' not found",
                    config_file=f"distributions/{component_name}.yaml"
                )
            return self._distributions[component_name]
        else:
            raise ConfigurationError(
                f"Unknown component type: {component_type}",
                config_file=component_ref,
                resolution_steps=[
                    "Valid types: profiles, strategies, distributions"
                ]
            )
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def list_available_scenarios(self) -> List[str]:
        """List all available scenario names."""
        scenarios = self.load_all_scenarios()
        return sorted(scenarios.keys())
    
    def get_scenario_info(self, name: str) -> Dict[str, Any]:
        """Get metadata about a scenario without fully loading it."""
        scenario = self.load_scenario(name)
        return {
            'name': scenario.get('name', name),
            'description': scenario.get('description', 'No description'),
            'team_size': scenario.get('baseline', {}).get('team_size', 'Unknown'),
            'timeframe_months': scenario.get('timeframe_months', 24),
            'has_distributions': self._has_distributions(scenario)
        }
    
    def _has_distributions(self, scenario: Dict[str, Any]) -> bool:
        """Check if scenario has probability distributions defined."""
        def check_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    if 'distribution' in value:
                        return True
                    if check_dict(value):
                        return True
            return False
        
        return check_dict(scenario)