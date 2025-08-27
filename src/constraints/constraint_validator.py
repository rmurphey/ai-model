"""
Constraint validation utilities for AI impact model.
Validates scenarios and parameters against defined constraints.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from ..utils.exceptions import ValidationError, ConfigurationError
from ..scenarios.scenario_loader import ScenarioLoader


class ValidationStatus(Enum):
    """Status of constraint validation."""
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


@dataclass
class ValidationResult:
    """Result of constraint validation."""
    
    status: ValidationStatus
    scenario_name: str
    violations: List[str]
    warnings: List[str]
    suggestions: List[str]
    parameters_checked: Dict[str, Any]
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.status == ValidationStatus.VALID
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0
    
    def get_report(self) -> str:
        """Generate human-readable validation report."""
        lines = [
            f"Validation Report for: {self.scenario_name}",
            f"Status: {self.status.value.upper()}",
            ""
        ]
        
        if self.violations:
            lines.append("VIOLATIONS:")
            for violation in self.violations:
                lines.append(f"  ✗ {violation}")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
        
        if self.suggestions:
            lines.append("SUGGESTIONS:")
            for suggestion in self.suggestions:
                lines.append(f"  → {suggestion}")
            lines.append("")
        
        lines.append(f"Parameters checked: {len(self.parameters_checked)}")
        
        return "\n".join(lines)


class ConstraintValidator:
    """
    Validates scenarios and parameters against business constraints.
    """
    
    def __init__(self):
        """Initialize constraint validator."""
        self.constraint_rules = self._define_constraint_rules()
    
    def _define_constraint_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define validation rules for each parameter type."""
        return {
            'budget': {
                'max_monthly_per_developer': 500,
                'min_monthly_per_developer': 10,
                'warning_threshold': 200
            },
            'team_size': {
                'min': 1,
                'max': 10000,
                'warning_min': 3,
                'warning_max': 500
            },
            'adoption': {
                'initial_min': 0.01,
                'initial_max': 0.30,
                'plateau_min': 0.10,
                'plateau_max': 0.95,
                'dropout_min': 0.0,
                'dropout_max': 0.10
            },
            'impact': {
                'feature_cycle_max': 0.50,
                'bug_fix_max': 0.60,
                'defect_max': 0.40,
                'incident_max': 0.50,
                'onboarding_max': 0.70,
                'pr_review_max': 0.80,
                'rework_max': 0.60,
                'capacity_gain_max': 0.30,
                'capacity_gain_min': -0.20
            },
            'timeframe': {
                'min_months': 3,
                'max_months': 120,
                'warning_min': 6,
                'warning_max': 60
            }
        }
    
    def validate_scenario(self, scenario_data: Dict[str, Any], 
                         scenario_name: str = "unknown") -> ValidationResult:
        """
        Validate a complete scenario against all constraints.
        
        Args:
            scenario_data: Scenario configuration dictionary
            scenario_name: Name of the scenario
            
        Returns:
            ValidationResult with details
        """
        violations = []
        warnings = []
        suggestions = []
        parameters_checked = {}
        
        # Validate team size
        if 'baseline' in scenario_data:
            baseline = scenario_data['baseline']
            if isinstance(baseline, dict) and 'team_size' in baseline:
                team_size = self._extract_value(baseline['team_size'])
                parameters_checked['team_size'] = team_size
                
                rules = self.constraint_rules['team_size']
                if team_size < rules['min'] or team_size > rules['max']:
                    violations.append(
                        f"Team size {team_size} outside valid range [{rules['min']}, {rules['max']}]"
                    )
                elif team_size < rules['warning_min']:
                    warnings.append(
                        f"Team size {team_size} is very small, results may not be representative"
                    )
                elif team_size > rules['warning_max']:
                    warnings.append(
                        f"Team size {team_size} is very large, consider splitting analysis"
                    )
        
        # Validate costs
        if 'costs' in scenario_data:
            costs = scenario_data['costs']
            if isinstance(costs, dict) and 'cost_per_seat_month' in costs:
                cost = self._extract_value(costs['cost_per_seat_month'])
                parameters_checked['cost_per_seat_month'] = cost
                
                rules = self.constraint_rules['budget']
                if cost < rules['min_monthly_per_developer']:
                    violations.append(
                        f"Cost per seat ${cost} below minimum ${rules['min_monthly_per_developer']}"
                    )
                elif cost > rules['max_monthly_per_developer']:
                    violations.append(
                        f"Cost per seat ${cost} exceeds maximum ${rules['max_monthly_per_developer']}"
                    )
                elif cost > rules['warning_threshold']:
                    warnings.append(
                        f"Cost per seat ${cost} is high, verify pricing is correct"
                    )
        
        # Validate adoption parameters
        if 'adoption' in scenario_data:
            adoption = scenario_data['adoption']
            if isinstance(adoption, dict):
                rules = self.constraint_rules['adoption']
                
                # Check initial adopters
                if 'initial_adopters' in adoption:
                    initial = self._extract_value(adoption['initial_adopters'])
                    parameters_checked['initial_adopters'] = initial
                    
                    if initial < rules['initial_min'] or initial > rules['initial_max']:
                        violations.append(
                            f"Initial adoption {initial:.1%} outside range [{rules['initial_min']:.1%}, {rules['initial_max']:.1%}]"
                        )
                
                # Check plateau efficiency
                if 'plateau_efficiency' in adoption:
                    plateau = self._extract_value(adoption['plateau_efficiency'])
                    parameters_checked['plateau_efficiency'] = plateau
                    
                    if plateau < rules['plateau_min'] or plateau > rules['plateau_max']:
                        violations.append(
                            f"Plateau efficiency {plateau:.1%} outside range [{rules['plateau_min']:.1%}, {rules['plateau_max']:.1%}]"
                        )
                    
                    # Check plateau vs initial
                    if 'initial_adopters' in parameters_checked:
                        if plateau < parameters_checked['initial_adopters'] * 1.5:
                            warnings.append(
                                "Plateau efficiency should be significantly higher than initial adoption"
                            )
                
                # Check dropout rate
                if 'dropout_rate_month' in adoption:
                    dropout = self._extract_value(adoption['dropout_rate_month'])
                    parameters_checked['dropout_rate_month'] = dropout
                    
                    if dropout < rules['dropout_min'] or dropout > rules['dropout_max']:
                        violations.append(
                            f"Dropout rate {dropout:.1%} outside range [{rules['dropout_min']:.1%}, {rules['dropout_max']:.1%}]"
                        )
        
        # Validate impact parameters
        if 'impact' in scenario_data:
            impact = scenario_data['impact']
            if isinstance(impact, dict):
                rules = self.constraint_rules['impact']
                
                impact_checks = [
                    ('feature_cycle_reduction', 'feature_cycle_max'),
                    ('bug_fix_reduction', 'bug_fix_max'),
                    ('defect_reduction', 'defect_max'),
                    ('incident_reduction', 'incident_max'),
                    ('onboarding_reduction', 'onboarding_max'),
                    ('pr_review_reduction', 'pr_review_max'),
                    ('rework_reduction', 'rework_max')
                ]
                
                for param_name, rule_name in impact_checks:
                    if param_name in impact:
                        value = self._extract_value(impact[param_name])
                        parameters_checked[param_name] = value
                        
                        if value < 0:
                            violations.append(
                                f"{param_name} cannot be negative ({value:.1%})"
                            )
                        elif value > rules[rule_name]:
                            violations.append(
                                f"{param_name} {value:.1%} exceeds maximum {rules[rule_name]:.1%}"
                            )
                        elif value > rules[rule_name] * 0.8:
                            warnings.append(
                                f"{param_name} {value:.1%} is very optimistic"
                            )
                
                # Check capacity gains
                for capacity_param in ['feature_capacity_gain', 'tech_debt_capacity_gain']:
                    if capacity_param in impact:
                        value = self._extract_value(impact[capacity_param])
                        parameters_checked[capacity_param] = value
                        
                        if value < rules['capacity_gain_min'] or value > rules['capacity_gain_max']:
                            violations.append(
                                f"{capacity_param} {value:.1%} outside range [{rules['capacity_gain_min']:.1%}, {rules['capacity_gain_max']:.1%}]"
                            )
        
        # Validate timeframe
        if 'timeframe_months' in scenario_data:
            timeframe = self._extract_value(scenario_data['timeframe_months'])
            parameters_checked['timeframe_months'] = timeframe
            
            rules = self.constraint_rules['timeframe']
            if timeframe < rules['min_months'] or timeframe > rules['max_months']:
                violations.append(
                    f"Timeframe {timeframe} months outside range [{rules['min_months']}, {rules['max_months']}]"
                )
            elif timeframe < rules['warning_min']:
                warnings.append(
                    f"Timeframe {timeframe} months may be too short to see full adoption impact"
                )
            elif timeframe > rules['warning_max']:
                warnings.append(
                    f"Timeframe {timeframe} months has high uncertainty in predictions"
                )
        
        # Generate suggestions based on violations and warnings
        if violations:
            suggestions.append("Fix constraint violations before running analysis")
            suggestions.append("Review parameter limits in documentation")
        
        if warnings:
            suggestions.append("Consider adjusting parameters with warnings for more realistic results")
        
        if not violations and not warnings:
            suggestions.append("All parameters within recommended ranges")
        
        # Determine overall status
        if violations:
            status = ValidationStatus.INVALID
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALID
        
        return ValidationResult(
            status=status,
            scenario_name=scenario_name,
            violations=violations,
            warnings=warnings,
            suggestions=suggestions,
            parameters_checked=parameters_checked
        )
    
    def _extract_value(self, param: Any) -> float:
        """
        Extract numeric value from parameter (handles distributions).
        
        Args:
            param: Parameter value or distribution
            
        Returns:
            Numeric value
        """
        if isinstance(param, dict):
            # Handle distribution format
            if 'value' in param:
                return float(param['value'])
            elif 'mean' in param:
                return float(param['mean'])
            elif 'default' in param:
                return float(param['default'])
            else:
                # Try to get first numeric value
                for key, val in param.items():
                    if isinstance(val, (int, float)):
                        return float(val)
        elif isinstance(param, (int, float)):
            return float(param)
        
        raise ValidationError(
            field_name="parameter",
            value=param,
            expected="numeric value or distribution",
            suggestion="Provide a number or distribution with 'value' field"
        )
    
    def validate_all_scenarios(self, scenario_file: str = "src/scenarios") -> List[ValidationResult]:
        """
        Validate all scenarios in a file or directory.
        
        Args:
            scenario_file: Path to scenarios
            
        Returns:
            List of validation results
        """
        try:
            loader = ScenarioLoader(scenario_file)
            scenarios = loader.load_all_scenarios()
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load scenarios: {e}",
                config_file=scenario_file,
                resolution_steps=[
                    "Check scenario file path",
                    "Verify YAML syntax",
                    "Ensure file permissions are correct"
                ]
            )
        
        results = []
        for scenario_name, scenario_data in scenarios.items():
            result = self.validate_scenario(scenario_data, scenario_name)
            results.append(result)
        
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> str:
        """
        Generate summary of validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Summary string
        """
        total = len(results)
        valid = sum(1 for r in results if r.status == ValidationStatus.VALID)
        warnings = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        invalid = sum(1 for r in results if r.status == ValidationStatus.INVALID)
        
        lines = [
            "=" * 60,
            "CONSTRAINT VALIDATION SUMMARY",
            "=" * 60,
            f"Total scenarios checked: {total}",
            f"  ✓ Valid: {valid}",
            f"  ⚠ Warnings: {warnings}",
            f"  ✗ Invalid: {invalid}",
            ""
        ]
        
        if invalid > 0:
            lines.append("INVALID SCENARIOS:")
            for result in results:
                if result.status == ValidationStatus.INVALID:
                    lines.append(f"  - {result.scenario_name}:")
                    for violation in result.violations[:3]:  # Show first 3 violations
                        lines.append(f"    • {violation}")
            lines.append("")
        
        if warnings > 0:
            lines.append("SCENARIOS WITH WARNINGS:")
            for result in results:
                if result.status == ValidationStatus.WARNING:
                    lines.append(f"  - {result.scenario_name} ({len(result.warnings)} warnings)")
        
        return "\n".join(lines)