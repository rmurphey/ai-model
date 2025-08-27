"""
Tests for delivery pipeline model.
"""

import pytest
import numpy as np
from src.model.delivery_pipeline import (
    PipelineStage, StageMetrics, TestingStrategy, DeliveryPipeline,
    create_standard_pipeline
)
from src.utils.exceptions import ValidationError, CalculationError


class TestStageMetrics:
    """Test stage metrics calculations."""
    
    def test_stage_metrics_validation(self):
        """Test stage metrics validation."""
        # Valid metrics should not raise
        metrics = StageMetrics(
            stage=PipelineStage.CODING,
            base_throughput=3.0,
            base_cycle_time=2.0,
            base_quality=0.8,
            base_capacity=10.0
        )
        assert metrics.base_throughput == 3.0
        
        # Invalid throughput should raise
        with pytest.raises(CalculationError):
            StageMetrics(
                stage=PipelineStage.CODING,
                base_throughput=-1.0,  # Invalid
                base_cycle_time=2.0,
                base_quality=0.8,
                base_capacity=10.0
            )
    
    def test_effective_throughput(self):
        """Test effective throughput calculation with AI."""
        metrics = StageMetrics(
            stage=PipelineStage.CODING,
            base_throughput=3.0,
            base_cycle_time=2.0,
            base_quality=0.8,
            base_capacity=10.0,
            ai_throughput_multiplier=1.5  # 50% improvement
        )
        
        # No AI adoption
        assert metrics.get_effective_throughput(0.0) == 3.0
        
        # Full AI adoption
        assert metrics.get_effective_throughput(1.0) == 4.5
        
        # Partial AI adoption
        expected = 3.0 * (1 + 0.5 * 0.5)  # 3.75
        assert metrics.get_effective_throughput(0.5) == expected
    
    def test_effective_quality_caps_at_one(self):
        """Test that quality never exceeds 1.0."""
        metrics = StageMetrics(
            stage=PipelineStage.CODING,
            base_throughput=3.0,
            base_cycle_time=2.0,
            base_quality=0.9,
            base_capacity=10.0,
            ai_quality_multiplier=1.5  # Would exceed 1.0
        )
        
        # Should cap at 1.0
        assert metrics.get_effective_quality(1.0) == 1.0


class TestTestingStrategy:
    """Test testing strategy calculations."""
    
    def test_testing_strategy_validation(self):
        """Test testing strategy validation."""
        strategy = TestingStrategy(
            automation_coverage=0.7,
            test_execution_time_manual=4.0,
            test_execution_time_automated=0.5,
            ai_test_generation_quality=0.6,
            test_review_overhead=0.3
        )
        assert strategy.automation_coverage == 0.7
        
        # Invalid coverage should raise
        with pytest.raises(CalculationError):
            TestingStrategy(
                automation_coverage=1.5,  # > 1.0
                test_execution_time_manual=4.0,
                test_execution_time_automated=0.5,
                ai_test_generation_quality=0.6,
                test_review_overhead=0.3
            )
    
    def test_effective_test_time(self):
        """Test test time calculation with AI impact."""
        strategy = TestingStrategy(
            automation_coverage=0.5,  # 50% automated
            test_execution_time_manual=4.0,
            test_execution_time_automated=0.5,
            ai_test_generation_quality=0.6,
            test_review_overhead=0.3
        )
        
        # No AI should be baseline
        baseline_time = strategy.get_effective_test_time(0.0, 1.0)
        expected_baseline = 0.5 * 4.0 + 0.5 * 0.5  # 2.25
        assert baseline_time == expected_baseline
        
        # With AI should include overhead
        ai_time = strategy.get_effective_test_time(1.0, 1.0)
        assert ai_time > baseline_time  # Should be higher due to overhead
    
    def test_defect_escape_rate(self):
        """Test defect escape rate calculation."""
        strategy = TestingStrategy(
            automation_coverage=0.5,
            test_execution_time_manual=4.0,
            test_execution_time_automated=0.5,
            ai_test_generation_quality=0.6,
            test_review_overhead=0.3,
            defect_detection_rate_manual=0.8,
            defect_detection_rate_automated=0.7
        )
        
        # No AI should be based on detection rates
        no_ai_escape = strategy.get_defect_escape_rate(0.0)
        expected_detection = 0.5 * 0.7 + 0.5 * 0.8  # 0.75
        expected_escape = (1 - expected_detection) * 1.0  # No AI bug factor
        assert abs(no_ai_escape - expected_escape) < 0.01
        
        # With AI should be higher due to subtle bugs
        with_ai_escape = strategy.get_defect_escape_rate(1.0)
        assert with_ai_escape > no_ai_escape


class TestDeliveryPipeline:
    """Test delivery pipeline calculations."""
    
    def test_create_standard_pipeline(self):
        """Test standard pipeline creation."""
        pipeline = create_standard_pipeline(team_size=10)
        
        assert pipeline.team_size == 10
        assert len(pipeline.stages) == 7  # All pipeline stages
        assert PipelineStage.CODING in pipeline.stages
        assert PipelineStage.CODE_REVIEW in pipeline.stages
        assert PipelineStage.TESTING in pipeline.stages
    
    def test_throughput_calculation(self):
        """Test throughput calculation identifies bottleneck."""
        pipeline = create_standard_pipeline(team_size=10)
        
        # Calculate throughput with no AI
        throughput_no_ai = pipeline.calculate_throughput(0.0)
        assert 'throughput_per_day' in throughput_no_ai
        assert 'bottleneck_stage' in throughput_no_ai
        assert 'stage_throughputs' in throughput_no_ai
        
        # With AI
        throughput_with_ai = pipeline.calculate_throughput(1.0)
        assert throughput_with_ai['throughput_per_day'] != throughput_no_ai['throughput_per_day']
    
    def test_lead_time_calculation(self):
        """Test lead time calculation."""
        pipeline = create_standard_pipeline(team_size=10)
        
        lead_time_no_ai = pipeline.calculate_lead_time(0.0)
        assert 'total_lead_time_days' in lead_time_no_ai
        assert 'stage_times' in lead_time_no_ai
        assert 'coding_percentage' in lead_time_no_ai
        
        # Lead time should change with AI
        lead_time_with_ai = pipeline.calculate_lead_time(1.0)
        assert lead_time_with_ai['total_lead_time_days'] != lead_time_no_ai['total_lead_time_days']
    
    def test_quality_impact_calculation(self):
        """Test quality impact calculation."""
        pipeline = create_standard_pipeline(team_size=10)
        
        quality_no_ai = pipeline.calculate_quality_impact(0.0)
        assert 'defects_introduced_per_100' in quality_no_ai
        assert 'defects_escaped_per_100' in quality_no_ai
        assert 'quality_score' in quality_no_ai
        
        # Quality should change with AI
        quality_with_ai = pipeline.calculate_quality_impact(1.0)
        assert quality_with_ai['defects_introduced_per_100'] != quality_no_ai['defects_introduced_per_100']
    
    def test_value_delivery_calculation(self):
        """Test value delivery calculation."""
        pipeline = create_standard_pipeline(team_size=10)
        
        value_delivery = pipeline.calculate_value_delivery(0.5, feature_value=10000)
        
        assert 'features_deployed_per_day' in value_delivery
        assert 'net_value_per_day' in value_delivery
        assert 'incident_cost_per_day' in value_delivery
        assert 'value_after_incidents' in value_delivery
        
        # Should be positive value
        assert value_delivery['net_value_per_day'] > 0
        
        # Value after incidents should account for defect costs
        assert value_delivery['value_after_incidents'] <= value_delivery['net_value_per_day']
    
    def test_bottleneck_identification(self):
        """Test that bottleneck is correctly identified."""
        pipeline = create_standard_pipeline(team_size=10)
        
        # Test different adoption levels
        for adoption in [0.0, 0.5, 1.0]:
            throughput = pipeline.calculate_throughput(adoption)
            bottleneck = throughput['bottleneck_stage']
            stage_throughputs = throughput['stage_throughputs']
            
            # Bottleneck should be the minimum throughput stage
            min_throughput = min(stage_throughputs.values())
            assert stage_throughputs[bottleneck] == min_throughput
    
    def test_ai_makes_review_slower(self):
        """Test that AI makes code review slower."""
        pipeline = create_standard_pipeline(team_size=10)
        
        throughput_no_ai = pipeline.calculate_throughput(0.0)
        throughput_with_ai = pipeline.calculate_throughput(1.0)
        
        # Code review throughput should be lower with AI
        review_no_ai = throughput_no_ai['stage_throughputs']['code_review']
        review_with_ai = throughput_with_ai['stage_throughputs']['code_review']
        
        assert review_with_ai < review_no_ai
    
    def test_deployment_frequency_impact(self):
        """Test that deployment frequency affects value delivery."""
        daily_pipeline = create_standard_pipeline(
            team_size=10, 
            deployment_frequency="daily"
        )
        monthly_pipeline = create_standard_pipeline(
            team_size=10,
            deployment_frequency="monthly"
        )
        
        daily_value = daily_pipeline.calculate_value_delivery(0.5)
        monthly_value = monthly_pipeline.calculate_value_delivery(0.5)
        
        # Daily deployment should deliver more features
        assert daily_value['features_deployed_per_day'] > monthly_value['features_deployed_per_day']