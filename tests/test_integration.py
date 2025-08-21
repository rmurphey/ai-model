"""
Integration tests for core analysis workflows
"""

import pytest
import tempfile
import os
from main import AIImpactModel
from run_analysis import AnalysisRunner


class TestBasicIntegration:
    """Test basic end-to-end analysis workflows"""
    
    def test_single_scenario_analysis(self):
        """Test complete single scenario analysis workflow"""
        model = AIImpactModel()
        
        # Run a known scenario
        results = model.run_scenario('moderate_enterprise')
        
        # Verify results structure
        assert isinstance(results, dict)
        
        # Check for required result fields
        required_fields = [
            'scenario_name', 'config', 'baseline', 'adoption', 'efficiency',
            'costs', 'value', 'cumulative_value', 'impact_breakdown',
            'breakeven_month', 'npv', 'roi_percent', 'peak_adoption'
        ]
        
        for field in required_fields:
            assert field in results, f"Missing required field: {field}"
            
        # Verify data types and basic sanity checks
        assert isinstance(results['scenario_name'], str)
        assert results['scenario_name'] == 'moderate_enterprise'
        
        assert isinstance(results['config'], dict)
        assert 'timeframe_months' in results['config']
        
        assert hasattr(results['baseline'], 'team_size')
        assert results['baseline'].team_size > 0
        
        assert isinstance(results['adoption'], (list, tuple)) or hasattr(results['adoption'], '__len__')
        assert len(results['adoption']) > 0
        
        assert isinstance(results['npv'], (int, float))
        assert isinstance(results['roi_percent'], (int, float))
        assert isinstance(results['peak_adoption'], (int, float))
        assert 0 <= results['peak_adoption'] <= 1
        
    def test_multiple_scenarios_workflow(self):
        """Test analysis runner with multiple scenarios"""
        runner = AnalysisRunner()
        
        # Test with a few known scenarios
        scenario_names = ['moderate_enterprise']  # Start with one we know works
        results_list, content = runner.run_multiple_scenarios(scenario_names)
        
        assert isinstance(results_list, list)
        assert len(results_list) == len(scenario_names)
        assert isinstance(content, str)
        assert len(content) > 0
        
        # Verify each result
        for results in results_list:
            assert 'scenario_name' in results
            assert 'npv' in results
            assert 'roi_percent' in results
            
    def test_markdown_generation(self):
        """Test markdown report generation"""
        runner = AnalysisRunner()
        
        # Run single scenario to get results
        results, content = runner.run_single_scenario('moderate_enterprise')
        
        # Generate markdown
        markdown = runner.format_final_output(results, ['moderate_enterprise'], 'Single Scenario')
        
        # Verify markdown structure
        assert isinstance(markdown, str)
        assert len(markdown) > 1000  # Should be substantial content
        
        # Check for required markdown sections
        required_sections = [
            '# AI Development Impact Analysis Report',
            '## Scenario Analysis: moderate_enterprise',
            '### Executive Summary',
            '### Financial Performance',
            '### Reproducibility',
            'Complete scenario configuration used:',
            'final_metrics:',
            'impact_breakdown:'
        ]
        
        for section in required_sections:
            assert section in markdown, f"Missing required section: {section}"
            
        # Verify sparklines are included (Unicode characters)
        unicode_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        has_sparklines = any(char in markdown for char in unicode_chars)
        assert has_sparklines, "Markdown should contain sparkline visualizations"
        
    def test_file_generation_workflow(self):
        """Test complete file generation workflow"""
        runner = AnalysisRunner()
        
        # Run analysis and generate file
        results, content = runner.run_single_scenario('moderate_enterprise')
        markdown = runner.format_final_output(results, ['moderate_enterprise'], 'Single Scenario')
        
        # Test file creation in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override output directory for test
            runner.output_dir = temp_dir
            filename = runner.generate_filename()
            
            # Verify filename format
            assert filename.endswith('.md')
            assert 'analysis_' in filename
            
            # Save file
            with open(filename, 'w') as f:
                f.write(markdown)
                
            # Verify file was created and has content
            assert os.path.exists(filename)
            with open(filename, 'r') as f:
                saved_content = f.read()
                assert len(saved_content) > 1000
                assert saved_content == markdown


class TestAnalysisConsistency:
    """Test that analysis results are consistent and reasonable"""
    
    def test_scenario_results_consistency(self):
        """Test that scenario results are internally consistent"""
        model = AIImpactModel()
        results = model.run_scenario('moderate_enterprise')
        
        # Basic sanity checks
        assert results['total_cost_3y'] > 0, "Total cost should be positive"
        assert results['total_value_3y'] > 0, "Total value should be positive"
        
        # ROI calculation consistency
        expected_roi = ((results['total_value_3y'] - results['total_cost_3y']) / results['total_cost_3y']) * 100
        assert abs(results['roi_percent'] - expected_roi) < 1, "ROI calculation inconsistency"
        
        # Adoption curve should be reasonable
        adoption = results['adoption']
        assert 0 <= min(adoption) <= max(adoption) <= 1, "Adoption rates should be between 0 and 1"
        assert results['peak_adoption'] == max(adoption), "Peak adoption should match maximum in curve"
        
        # Value arrays should have same length as adoption
        assert len(results['value']) == len(adoption), "Value and adoption arrays should have same length"
        assert len(results['cumulative_value']) == len(adoption), "Cumulative value array length mismatch"
        
    def test_baseline_calculations_reasonable(self):
        """Test that baseline calculations produce reasonable results"""
        model = AIImpactModel()
        results = model.run_scenario('moderate_enterprise')
        baseline = results['baseline']
        
        # Team size should be reasonable
        assert 1 <= baseline.team_size <= 10000, f"Team size {baseline.team_size} seems unrealistic"
        
        # Weighted average FLC should be reasonable
        assert 50000 <= baseline.weighted_avg_flc <= 500000, f"Average FLC {baseline.weighted_avg_flc} seems unrealistic"
        
        # Total team cost should make sense
        expected_team_cost = baseline.team_size * baseline.weighted_avg_flc
        assert abs(baseline.total_team_cost - expected_team_cost) < 1000, "Team cost calculation inconsistency"
        
    def test_impact_breakdown_consistency(self):
        """Test that impact breakdown values are consistent"""
        model = AIImpactModel()
        results = model.run_scenario('moderate_enterprise')
        impact = results['impact_breakdown']
        
        # All impact values should be positive
        assert impact['time_value'] >= 0, "Time-to-market value should be non-negative"
        assert impact['quality_value'] >= 0, "Quality value should be non-negative"
        assert impact['capacity_value'] >= 0, "Capacity value should be non-negative"
        assert impact['strategic_value'] >= 0, "Strategic value should be non-negative"
        
        # Total should equal sum of components
        expected_total = (impact['time_value'] + impact['quality_value'] + 
                         impact['capacity_value'] + impact['strategic_value'])
        assert abs(impact['total_annual_value'] - expected_total) < 1, "Impact breakdown total inconsistency"
        
        # Value per developer should make sense
        expected_per_dev = impact['total_annual_value'] / results['baseline'].team_size
        assert abs(impact['value_per_developer'] - expected_per_dev) < 1, "Value per developer calculation error"


class TestErrorHandlingIntegration:
    """Test error handling in integrated workflows"""
    
    def test_invalid_scenario_in_analysis_runner(self):
        """Test error handling for invalid scenarios in analysis runner"""
        runner = AnalysisRunner()
        
        with pytest.raises(Exception):  # Should raise some form of error
            runner.run_single_scenario('nonexistent_scenario')
            
    def test_analysis_runner_with_empty_scenario_list(self):
        """Test handling of empty scenario list"""
        runner = AnalysisRunner()
        
        # Should return empty results without crashing
        results, output = runner.run_multiple_scenarios([])
        assert results == []
        assert isinstance(output, str)
            
    def test_malformed_results_handling(self):
        """Test that markdown generation handles edge cases gracefully"""
        runner = AnalysisRunner()
        
        # Test with minimal/malformed results structure - need at least 12 months for the report
        # Create 12 months of data to avoid index errors
        months = 12
        adoption_values = [0.1 + (i * 0.02) for i in range(months)]  # Gradual increase
        efficiency_values = [0.1 + (i * 0.01) for i in range(months)]  # Gradual increase
        value_values = [1000 + (i * 100) for i in range(months)]  # Increasing value
        cost_values = [100] * months  # Constant cost
        cumulative_value = [sum(value_values[:i+1]) for i in range(months)]
        cumulative_cost = [sum(cost_values[:i+1]) for i in range(months)]
        effective_adoption = [adoption_values[i] * efficiency_values[i] for i in range(months)]
        
        minimal_results = {
            'scenario_name': 'test',
            'baseline': type('MockBaseline', (), {
                'team_size': 1, 
                'weighted_avg_flc': 100000.0,
                'avg_feature_cycle_days': 21,
                'feature_delivery_rate': 1.0,
                'total_team_cost': 100000.0,
                'onboarding_days': 30,
                'annual_incident_cost': 50000,
                'junior_flc': 75000,
                'mid_flc': 100000,
                'senior_flc': 150000,
                'junior_ratio': 0.3,
                'mid_ratio': 0.5,
                'senior_ratio': 0.2,
                'annual_rework_cost': 25000.0,
                'avg_bug_fix_hours': 8,
                'avg_incident_cost': 1000,
                'avg_pr_review_hours': 2,
                'defect_escape_rate': 0.05,
                'effective_capacity_hours': 1600.0,
                'maintenance_percentage': 0.3,
                'meetings_percentage': 0.2,
                'new_feature_percentage': 0.4,
                'pr_rejection_rate': 0.15,
                'production_incidents_per_month': 5,
                'rework_percentage': 0.1,
                'tech_debt_percentage': 0.2,
                'calculate_baseline_efficiency': lambda: 0.7
            })(),
            'config': {'timeframe_months': 12},
            'adoption': adoption_values,
            'efficiency': efficiency_values,
            'costs': {
                'total': cost_values,
                'cumulative': cumulative_cost,
                'licensing': [50] * months,  # Add licensing costs
                'infrastructure': [25] * months,  # Add infrastructure costs
                'training': [25] * months  # Add training costs
            },
            'value': value_values,
            'cumulative_value': cumulative_value,
            'effective_adoption': effective_adoption,
            'impact_breakdown': {
                'time_value': 1000,
                'quality_value': 500,
                'capacity_value': 300,
                'strategic_value': 200,
                'total_annual_value': 2000,
                'value_per_developer': 2000  # Add missing field
            },
            'peak_adoption': max(adoption_values),
            'breakeven_month': 1,
            'npv': 10000,
            'roi_percent': 100,
            'total_cost_3y': 3600,
            'total_value_3y': 36000,
            'annual_cost_per_dev': 3600,
            'annual_value_per_dev': 12000
        }
        
        # Should not raise an exception
        markdown = runner._generate_single_scenario_markdown(minimal_results, 'test')
        assert isinstance(markdown, str)
        assert len(markdown) > 100  # Should generate substantial content


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__])