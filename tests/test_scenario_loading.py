"""
Tests for scenario loading and YAML configuration management
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from main import AIImpactModel
from src.utils.exceptions import ConfigurationError, ScenarioError


class TestScenarioLoading:
    """Test scenario loading from YAML files"""
    
    def test_load_valid_scenario_file(self):
        """Test loading a valid scenario configuration"""
        # This tests the actual scenarios.yaml file
        model = AIImpactModel()
        assert hasattr(model, 'scenarios')
        assert isinstance(model.scenarios, dict)
        assert len(model.scenarios) > 0
        
    def test_get_available_scenarios(self):
        """Test getting list of available scenarios"""
        model = AIImpactModel()
        scenarios = model.get_available_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        # Check for known scenarios
        assert 'moderate_enterprise' in scenarios
        
    def test_nonexistent_scenario_file(self):
        """Test error handling for non-existent scenario file"""
        with pytest.raises(ConfigurationError, match="not found"):
            AIImpactModel("nonexistent_file.yaml")
            
    def test_invalid_yaml_syntax(self):
        """Test error handling for invalid YAML syntax"""
        invalid_yaml = """
        invalid_yaml:
          - item1
          - item2
            missing_dash: value
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                with pytest.raises(ConfigurationError, match="Invalid YAML format"):
                    AIImpactModel(f.name)
            finally:
                os.unlink(f.name)
                
    def test_empty_scenario_file(self):
        """Test error handling for empty scenario file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            try:
                with pytest.raises(ConfigurationError, match="empty or contains no valid scenarios"):
                    AIImpactModel(f.name)
            finally:
                os.unlink(f.name)
                
    def test_yaml_with_only_comments(self):
        """Test error handling for YAML file with only comments"""
        comments_only = """
        # This is a comment
        # Another comment
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(comments_only)
            f.flush()
            
            try:
                with pytest.raises(ConfigurationError, match="empty or contains no valid scenarios"):
                    AIImpactModel(f.name)
            finally:
                os.unlink(f.name)


class TestLoadScenario:
    """Test loading individual scenarios"""
    
    def test_load_existing_scenario(self):
        """Test loading an existing scenario"""
        model = AIImpactModel()
        scenario = model.load_scenario('moderate_enterprise')
        assert isinstance(scenario, dict)
        assert 'baseline' in scenario
        assert 'adoption' in scenario
        assert 'impact' in scenario
        assert 'costs' in scenario
        assert 'timeframe_months' in scenario
        
    def test_load_nonexistent_scenario(self):
        """Test error when loading non-existent scenario"""
        model = AIImpactModel()
        with pytest.raises(ScenarioError, match="not found in configuration"):
            model.load_scenario('nonexistent_scenario')
            
    def test_scenario_error_includes_available_scenarios(self):
        """Test that ScenarioError includes list of available scenarios"""
        model = AIImpactModel()
        try:
            model.load_scenario('nonexistent_scenario')
            assert False, "Should have raised ScenarioError"
        except ScenarioError as e:
            assert hasattr(e, 'available_scenarios')
            assert len(e.available_scenarios) > 0
            assert 'moderate_enterprise' in e.available_scenarios
            
    def test_scenario_with_missing_required_fields(self):
        """Test error when scenario is missing required fields"""
        incomplete_scenario = {
            'test_incomplete': {
                'baseline': {'profile': 'enterprise'},
                'adoption': {'scenario': 'grassroots'},
                # Missing impact, costs, timeframe_months
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(incomplete_scenario, f)
            f.flush()
            
            try:
                model = AIImpactModel(f.name)
                with pytest.raises(ConfigurationError, match="missing required fields"):
                    model.load_scenario('test_incomplete')
            finally:
                os.unlink(f.name)


class TestScenarioValidation:
    """Test scenario validation logic"""
    
    def test_valid_scenario_structure(self):
        """Test validation of valid scenario structure"""
        valid_scenario = {
            'test_valid': {
                'baseline': {'profile': 'enterprise'},
                'adoption': {'scenario': 'grassroots'},
                'impact': {'scenario': 'moderate'},
                'costs': {'scenario': 'enterprise'},
                'timeframe_months': 36,
                'description': 'Test scenario',
                'name': 'Test Valid Scenario'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(valid_scenario, f)
            f.flush()
            
            try:
                model = AIImpactModel(f.name)
                scenario = model.load_scenario('test_valid')
                assert scenario['timeframe_months'] == 36
                assert scenario['baseline']['profile'] == 'enterprise'
            finally:
                os.unlink(f.name)
                
    def test_scenario_with_detailed_parameters(self):
        """Test scenario with detailed parameter definitions"""
        detailed_scenario = {
            'test_detailed': {
                'baseline': {
                    'team_size': 25,
                    'annual_salary': 80000,
                    'total_working_days': 250
                },
                'adoption': {
                    'initial_adopters': 0.05,
                    'early_adopters': 0.15,
                    'early_majority': 0.35,
                    'late_majority': 0.35,
                    'laggards': 0.10
                },
                'impact': {
                    'productivity_gain': 0.25,
                    'quality_improvement': 0.15,
                    'time_to_market_improvement': 0.20
                },
                'costs': {
                    'license_cost_monthly': 30,
                    'setup_cost_one_time': 2000
                },
                'timeframe_months': 24
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(detailed_scenario, f)
            f.flush()
            
            try:
                model = AIImpactModel(f.name)
                scenario = model.load_scenario('test_detailed')
                assert scenario['baseline']['team_size'] == 25
                assert scenario['costs']['license_cost_monthly'] == 30
            finally:
                os.unlink(f.name)


class TestErrorMessageQuality:
    """Test that error messages are helpful and actionable"""
    
    def test_file_not_found_error_message(self):
        """Test that file not found errors provide helpful guidance"""
        try:
            AIImpactModel("missing_scenarios.yaml")
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            error_msg = str(e)
            assert "🔧 Resolution Steps:" in error_msg
            assert "Check if the file path is correct" in error_msg
            assert "Ensure you're running from the project root directory" in error_msg
            
    def test_yaml_syntax_error_message(self):
        """Test that YAML syntax errors provide specific guidance"""
        invalid_yaml = """
        scenario1:
          field1: value1
          field2: [
            - item1
            - item2
          # Missing closing bracket
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                AIImpactModel(f.name)
                assert False, "Should have raised ConfigurationError"
            except ConfigurationError as e:
                error_msg = str(e)
                assert "🔧 Resolution Steps:" in error_msg
                assert "Check YAML syntax using an online YAML validator" in error_msg
                assert "Ensure proper indentation" in error_msg
            finally:
                os.unlink(f.name)
                
    def test_missing_scenario_error_message(self):
        """Test that missing scenario errors provide helpful suggestions"""
        model = AIImpactModel()
        try:
            model.load_scenario('moderate_enterpr1se')  # Typo in name
            assert False, "Should have raised ScenarioError"
        except ScenarioError as e:
            error_msg = str(e)
            assert "🔧 Resolution Steps:" in error_msg
            assert "Check spelling of scenario name" in error_msg
            assert "Use '--list' to see all available scenarios" in error_msg
            # Should suggest closest match
            assert "Did you mean 'moderate_enterprise'?" in error_msg


class TestScenarioFilePermissions:
    """Test handling of file permission issues"""
    
    @pytest.mark.skipif(os.name == 'nt', reason="Permission tests not reliable on Windows")
    def test_permission_denied_error(self):
        """Test error handling when scenario file has no read permissions"""
        valid_yaml = """
        test_scenario:
          baseline: {profile: enterprise}
          adoption: {scenario: grassroots}
          impact: {scenario: moderate}
          costs: {scenario: enterprise}
          timeframe_months: 36
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_yaml)
            f.flush()
            
            try:
                # Remove read permissions
                os.chmod(f.name, 0o000)
                
                with pytest.raises(ConfigurationError, match="Permission denied"):
                    AIImpactModel(f.name)
                    
            finally:
                # Restore permissions before cleanup
                os.chmod(f.name, 0o644)
                os.unlink(f.name)


class TestScenarioListMethods:
    """Test scenario listing and discovery methods"""
    
    def test_get_available_scenarios_returns_list(self):
        """Test that available scenarios are returned as a list"""
        model = AIImpactModel()
        scenarios = model.get_available_scenarios()
        assert isinstance(scenarios, list)
        assert all(isinstance(name, str) for name in scenarios)
        
    def test_available_scenarios_not_empty(self):
        """Test that there are actually scenarios available"""
        model = AIImpactModel()
        scenarios = model.get_available_scenarios()
        assert len(scenarios) > 0, "No scenarios found in configuration"
        
    def test_scenario_names_are_valid_identifiers(self):
        """Test that scenario names are valid Python identifiers (no spaces, special chars)"""
        model = AIImpactModel()
        scenarios = model.get_available_scenarios()
        
        for scenario_name in scenarios:
            # Check for reasonable naming conventions
            assert '_' in scenario_name or scenario_name.isalnum(), f"Scenario name '{scenario_name}' uses unexpected characters"
            assert not scenario_name.startswith('_'), f"Scenario name '{scenario_name}' starts with underscore"
            assert scenario_name.islower() or '_' in scenario_name, f"Scenario name '{scenario_name}' should be lowercase or use underscores"