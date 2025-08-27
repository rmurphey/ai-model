"""
Software delivery pipeline model.
Models the full cycle from idea to production value delivery.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from .queue_model import PipelineQueue, QueueMetrics, apply_littles_law
from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio
from ..utils.exceptions import ValidationError, CalculationError


class PipelineStage(Enum):
    """Stages in the delivery pipeline."""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    CODING = "coding"
    TESTING = "testing"
    CODE_REVIEW = "code_review"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


@dataclass
class StageMetrics:
    """Metrics for a pipeline stage."""
    
    stage: PipelineStage
    base_throughput: float  # Items per day
    base_cycle_time: float  # Days per item
    base_quality: float  # Quality score 0-1
    base_capacity: float  # Max items in parallel
    
    # AI impact factors
    ai_throughput_multiplier: float = 1.0  # >1 helps, <1 hurts
    ai_cycle_time_multiplier: float = 1.0  # <1 faster, >1 slower
    ai_quality_multiplier: float = 1.0  # >1 better, <1 worse
    ai_capacity_impact: float = 1.0  # Capacity change with AI
    
    def __post_init__(self):
        """Validate stage metrics."""
        validate_positive(self.base_throughput, "base_throughput")
        validate_positive(self.base_cycle_time, "base_cycle_time")
        validate_ratio(self.base_quality, "base_quality")
        validate_positive(self.base_capacity, "base_capacity")
        
        # Multipliers should be reasonable
        if not 0.1 <= self.ai_throughput_multiplier <= 10:
            raise ValidationError(
                field_name="ai_throughput_multiplier",
                value=self.ai_throughput_multiplier,
                expected="between 0.1 and 10",
                suggestion="Use realistic AI impact multipliers"
            )
    
    def get_effective_throughput(self, ai_adoption: float) -> float:
        """Calculate effective throughput with AI adoption."""
        ai_impact = 1 + (self.ai_throughput_multiplier - 1) * ai_adoption
        return self.base_throughput * ai_impact
    
    def get_effective_cycle_time(self, ai_adoption: float) -> float:
        """Calculate effective cycle time with AI adoption."""
        ai_impact = 1 + (self.ai_cycle_time_multiplier - 1) * ai_adoption
        return self.base_cycle_time * ai_impact
    
    def get_effective_quality(self, ai_adoption: float) -> float:
        """Calculate effective quality with AI adoption."""
        ai_impact = 1 + (self.ai_quality_multiplier - 1) * ai_adoption
        return min(1.0, self.base_quality * ai_impact)


@dataclass
class TestingStrategy:
    """Testing strategy configuration."""
    
    automation_coverage: float  # 0-1, percentage of tests automated
    test_execution_time_manual: float  # Hours per test suite
    test_execution_time_automated: float  # Hours per test suite
    ai_test_generation_quality: float  # 0-1, quality of AI-generated tests
    test_review_overhead: float  # Extra time to review AI tests
    
    # Test effectiveness
    defect_detection_rate_manual: float = 0.7  # Manual testing catches 70%
    defect_detection_rate_automated: float = 0.6  # Automated catches 60%
    
    def __post_init__(self):
        """Validate testing parameters."""
        validate_ratio(self.automation_coverage, "automation_coverage")
        validate_positive(self.test_execution_time_manual, "test_execution_time_manual")
        validate_positive(self.test_execution_time_automated, "test_execution_time_automated")
        validate_ratio(self.ai_test_generation_quality, "ai_test_generation_quality")
        validate_ratio(self.test_review_overhead, "test_review_overhead", min_val=0, max_val=2)
        validate_ratio(self.defect_detection_rate_manual, "defect_detection_rate_manual")
        validate_ratio(self.defect_detection_rate_automated, "defect_detection_rate_automated")
    
    def get_effective_test_time(self, ai_adoption: float, code_volume: float) -> float:
        """Calculate total test time including AI impact."""
        # More AI code = more to test
        test_volume = code_volume * (1 + ai_adoption * 0.5)  # AI generates 50% more code
        
        # Split between manual and automated
        manual_portion = (1 - self.automation_coverage) * test_volume
        automated_portion = self.automation_coverage * test_volume
        
        # Calculate times
        manual_time = manual_portion * self.test_execution_time_manual
        automated_time = automated_portion * self.test_execution_time_automated
        
        # Add overhead for reviewing AI-generated tests
        ai_test_overhead = ai_adoption * self.test_review_overhead * test_volume
        
        return manual_time + automated_time + ai_test_overhead
    
    def get_defect_escape_rate(self, ai_adoption: float) -> float:
        """Calculate defects that escape to production."""
        # Weighted average of detection rates
        avg_detection = (
            self.automation_coverage * self.defect_detection_rate_automated +
            (1 - self.automation_coverage) * self.defect_detection_rate_manual
        )
        
        # AI may introduce subtle bugs harder to catch
        ai_bug_factor = 1 + ai_adoption * 0.2  # 20% more subtle bugs with AI
        
        escape_rate = (1 - avg_detection) * ai_bug_factor
        return min(1.0, escape_rate)


@dataclass 
class DeliveryPipeline:
    """Models the complete software delivery pipeline with queue modeling."""
    
    stages: Dict[PipelineStage, StageMetrics]
    testing_strategy: TestingStrategy
    team_size: int
    
    # Review dynamics
    ai_code_review_multiplier: float = 1.2  # AI code takes 20% longer to review
    review_thoroughness: float = 0.8  # How careful are reviewers (0-1)
    
    # Deployment parameters
    deployment_frequency: str = "weekly"  # daily, weekly, biweekly, monthly
    rollback_rate: float = 0.02  # Percentage of deployments rolled back
    
    # Queue modeling and WIP limits
    stage_queues: Dict[PipelineStage, PipelineQueue] = None
    wip_limits: Dict[PipelineStage, int] = None
    batch_sizes: Dict[PipelineStage, int] = None
    
    # Subordination settings (Theory of Constraints)
    constraint_stage: Optional[PipelineStage] = None
    subordination_active: bool = False
    
    def __post_init__(self):
        """Validate pipeline configuration and initialize queue modeling."""
        validate_positive(self.team_size, "team_size")
        validate_ratio(self.review_thoroughness, "review_thoroughness")
        validate_ratio(self.rollback_rate, "rollback_rate")
        
        if not 0.8 <= self.ai_code_review_multiplier <= 2.0:
            raise ValidationError(
                field_name="ai_code_review_multiplier",
                value=self.ai_code_review_multiplier,
                expected="between 0.8 and 2.0",
                suggestion="AI code typically takes longer to review"
            )
        
        # Initialize queue modeling if not provided
        if self.stage_queues is None:
            self._initialize_queues()
        if self.wip_limits is None:
            self._initialize_wip_limits()
        if self.batch_sizes is None:
            self._initialize_batch_sizes()
    
    def _initialize_queues(self):
        """Initialize pipeline queues for each stage."""
        self.stage_queues = {}
        for stage in PipelineStage:
            self.stage_queues[stage] = PipelineQueue(
                stage_name=stage.value,
                max_wip=None,  # Will be set by WIP limits
                batch_size=1   # Will be set by batch sizes
            )
    
    def _initialize_wip_limits(self):
        """Initialize reasonable WIP limits based on team size."""
        base_wip = max(2, self.team_size // 3)  # Base WIP limit
        
        self.wip_limits = {
            PipelineStage.REQUIREMENTS: base_wip * 2,  # Requirements can queue up
            PipelineStage.DESIGN: base_wip,
            PipelineStage.CODING: self.team_size,      # One per developer
            PipelineStage.CODE_REVIEW: base_wip,       # Limited by senior capacity
            PipelineStage.TESTING: base_wip,
            PipelineStage.DEPLOYMENT: base_wip // 2,   # Keep deployment queue small
            PipelineStage.MONITORING: base_wip * 3     # Monitoring can handle more
        }
        
        # Apply WIP limits to queues
        for stage, limit in self.wip_limits.items():
            if stage in self.stage_queues:
                self.stage_queues[stage].max_wip = limit
    
    def _initialize_batch_sizes(self):
        """Initialize optimal batch sizes based on Reinertsen's principles."""
        self.batch_sizes = {
            PipelineStage.REQUIREMENTS: 3,     # Batch requirements for efficiency
            PipelineStage.DESIGN: 2,          # Small design batches
            PipelineStage.CODING: 1,          # Individual features
            PipelineStage.CODE_REVIEW: 2,     # Review 2 PRs together for efficiency
            PipelineStage.TESTING: 3,         # Batch tests for automation
            PipelineStage.DEPLOYMENT: 5,      # Deploy multiple features together
            PipelineStage.MONITORING: 1       # Monitor individual deployments
        }
        
        # Apply batch sizes to queues
        for stage, batch_size in self.batch_sizes.items():
            if stage in self.stage_queues:
                self.stage_queues[stage].batch_size = batch_size
    
    def calculate_throughput_with_queues(self, ai_adoption: float) -> Dict[str, float]:
        """
        Calculate pipeline throughput with queue-aware modeling.
        Includes queue delays and WIP constraints in throughput calculation.
        """
        stage_throughputs = {}
        queue_delays = {}
        
        for stage, metrics in self.stages.items():
            # Calculate base throughput
            if stage == PipelineStage.CODE_REVIEW:
                review_impact = 1 + (self.ai_code_review_multiplier - 1) * ai_adoption
                base_throughput = metrics.get_effective_throughput(ai_adoption) / review_impact
            elif stage == PipelineStage.TESTING:
                base_throughput = metrics.get_effective_throughput(ai_adoption)
                test_time = self.testing_strategy.get_effective_test_time(ai_adoption, 1.0)
                base_throughput = safe_divide(base_throughput, 1 + test_time/8, default=0.1)
            else:
                base_throughput = metrics.get_effective_throughput(ai_adoption)
            
            # Apply WIP constraints
            wip_limit = self.wip_limits.get(stage, float('inf'))
            wip_constrained_throughput = min(base_throughput, wip_limit * 0.8)  # 80% utilization
            
            # Calculate queue delay impact
            queue = self.stage_queues.get(stage)
            if queue and len(queue.waiting_items) > 0:
                queue_metrics = queue.get_queue_metrics()
                queue_delay_factor = 1.0 / (1.0 + queue_metrics.avg_wait_time * 0.1)  # Delay reduces effective throughput
                effective_throughput = wip_constrained_throughput * queue_delay_factor
                queue_delays[stage.value] = queue_metrics.avg_wait_time
            else:
                effective_throughput = wip_constrained_throughput
                queue_delays[stage.value] = 0.0
            
            stage_throughputs[stage.value] = effective_throughput
        
        # Overall throughput is the minimum (bottleneck)
        bottleneck_stage = min(stage_throughputs, key=stage_throughputs.get)
        bottleneck_throughput = stage_throughputs[bottleneck_stage]
        
        return {
            'throughput_per_day': bottleneck_throughput,
            'bottleneck_stage': bottleneck_stage,
            'stage_throughputs': stage_throughputs,
            'queue_delays': queue_delays,
            'utilization': {stage: stage_throughputs[stage]/bottleneck_throughput 
                          for stage in stage_throughputs},
            'wip_utilization': {stage.value: len(self.stage_queues[stage].waiting_items + 
                                                self.stage_queues[stage].in_progress_items) / 
                                              self.wip_limits[stage]
                              for stage in self.stages.keys()}
        }
    
    def calculate_throughput(self, ai_adoption: float) -> Dict[str, float]:
        """
        Calculate pipeline throughput using Theory of Constraints.
        The bottleneck determines overall throughput.
        """
        stage_throughputs = {}
        
        for stage, metrics in self.stages.items():
            if stage == PipelineStage.CODE_REVIEW:
                # Review is slower for AI code
                review_impact = 1 + (self.ai_code_review_multiplier - 1) * ai_adoption
                throughput = metrics.get_effective_throughput(ai_adoption) / review_impact
            elif stage == PipelineStage.TESTING:
                # Testing bottleneck depends on strategy
                base_throughput = metrics.get_effective_throughput(ai_adoption)
                test_time = self.testing_strategy.get_effective_test_time(ai_adoption, 1.0)
                throughput = safe_divide(base_throughput, 1 + test_time/8, default=0.1)
            else:
                throughput = metrics.get_effective_throughput(ai_adoption)
            
            stage_throughputs[stage.value] = throughput
        
        # Overall throughput is the minimum (bottleneck)
        bottleneck_stage = min(stage_throughputs, key=stage_throughputs.get)
        bottleneck_throughput = stage_throughputs[bottleneck_stage]
        
        return {
            'throughput_per_day': bottleneck_throughput,
            'bottleneck_stage': bottleneck_stage,
            'stage_throughputs': stage_throughputs,
            'utilization': {stage: stage_throughputs[stage]/bottleneck_throughput 
                          for stage in stage_throughputs}
        }
    
    def apply_subordination(self, constraint_stage: PipelineStage):
        """
        Apply Theory of Constraints subordination to optimize for the constraint.
        All stages subordinate their local optimization to support the constraint.
        """
        self.constraint_stage = constraint_stage
        self.subordination_active = True
        
        # Adjust WIP limits to support constraint
        if constraint_stage == PipelineStage.CODE_REVIEW:
            # Reduce coding WIP to prevent overwhelming review
            self.wip_limits[PipelineStage.CODING] = min(
                self.wip_limits[PipelineStage.CODING],
                self.wip_limits[PipelineStage.CODE_REVIEW] * 2
            )
            # Increase buffer before review
            self.wip_limits[PipelineStage.CODE_REVIEW] = int(
                self.wip_limits[PipelineStage.CODE_REVIEW] * 1.2
            )
            
        elif constraint_stage == PipelineStage.TESTING:
            # Optimize for testability
            self.batch_sizes[PipelineStage.CODING] = 1  # Smaller, more testable chunks
            self.wip_limits[PipelineStage.TESTING] = int(
                self.wip_limits[PipelineStage.TESTING] * 1.3
            )
        
        # Update queues with new limits and batch sizes
        for stage in self.stages.keys():
            if stage in self.stage_queues:
                self.stage_queues[stage].max_wip = self.wip_limits[stage]
                self.stage_queues[stage].batch_size = self.batch_sizes[stage]
    
    def calculate_queue_costs(self) -> Dict[str, float]:
        """
        Calculate economic cost of queues (invisible cost in most organizations).
        Based on Reinertsen's emphasis on queue cost visibility.
        """
        queue_costs = {}
        total_queue_cost = 0.0
        
        for stage, queue in self.stage_queues.items():
            queue_cost = queue.get_total_cost_of_delay()
            queue_costs[stage.value] = queue_cost
            total_queue_cost += queue_cost
        
        return {
            'queue_costs_by_stage': queue_costs,
            'total_daily_queue_cost': total_queue_cost,
            'monthly_queue_cost': total_queue_cost * 30,
            'queue_cost_per_feature': safe_divide(total_queue_cost, 
                                                 self.calculate_throughput(0.5)['throughput_per_day'])
        }
    
    def calculate_lead_time(self, ai_adoption: float) -> Dict[str, float]:
        """Calculate total lead time from idea to production."""
        total_cycle_time = 0
        stage_times = {}
        
        for stage, metrics in self.stages.items():
            if stage == PipelineStage.CODE_REVIEW:
                # Review is slower for AI code
                review_impact = 1 + (self.ai_code_review_multiplier - 1) * ai_adoption
                cycle_time = metrics.get_effective_cycle_time(ai_adoption) * review_impact
            elif stage == PipelineStage.TESTING:
                # Testing time depends on automation
                base_cycle = metrics.get_effective_cycle_time(ai_adoption)
                test_overhead = self.testing_strategy.get_effective_test_time(ai_adoption, 1.0) / 8
                cycle_time = base_cycle + test_overhead
            else:
                cycle_time = metrics.get_effective_cycle_time(ai_adoption)
            
            stage_times[stage.value] = cycle_time
            total_cycle_time += cycle_time
        
        return {
            'total_lead_time_days': total_cycle_time,
            'stage_times': stage_times,
            'coding_percentage': stage_times.get('coding', 0) / total_cycle_time * 100
        }
    
    def calculate_quality_impact(self, ai_adoption: float) -> Dict[str, float]:
        """Calculate quality metrics including defect rates."""
        # Base defect introduction rate
        coding_quality = self.stages[PipelineStage.CODING].get_effective_quality(ai_adoption)
        
        # AI might introduce different types of bugs
        syntax_error_reduction = 0.3 * ai_adoption  # AI reduces syntax errors
        logic_error_increase = 0.2 * ai_adoption  # But increases logic errors
        
        base_defect_rate = (1 - coding_quality) * 100  # Defects per 100 features
        
        # Adjust for AI impact
        ai_defect_multiplier = 1 - syntax_error_reduction + logic_error_increase
        introduced_defects = base_defect_rate * ai_defect_multiplier
        
        # How many escape to production
        escape_rate = self.testing_strategy.get_defect_escape_rate(ai_adoption)
        escaped_defects = introduced_defects * escape_rate
        
        # Impact of code review
        review_quality = self.stages[PipelineStage.CODE_REVIEW].get_effective_quality(ai_adoption)
        review_catch_rate = review_quality * self.review_thoroughness
        
        final_defect_rate = escaped_defects * (1 - review_catch_rate)
        
        return {
            'defects_introduced_per_100': introduced_defects,
            'defects_escaped_per_100': escaped_defects,
            'defects_in_production_per_100': final_defect_rate,
            'defect_escape_rate': escape_rate,
            'quality_score': 1 - final_defect_rate/100
        }
    
    def calculate_flow_efficiency(self) -> float:
        """
        Calculate flow efficiency: ratio of value-add time to total lead time.
        Per Reinertsen, most product development has flow efficiency < 25%.
        """
        lead_time_data = self.calculate_lead_time(0.5)  # Use moderate AI adoption
        total_lead_time = lead_time_data['total_lead_time_days']
        
        # Value-add stages (actual work, not waiting)
        value_add_stages = [PipelineStage.DESIGN, PipelineStage.CODING, PipelineStage.TESTING]
        value_add_time = sum(
            lead_time_data['stage_times'].get(stage.value, 0)
            for stage in value_add_stages
        )
        
        return safe_divide(value_add_time, total_lead_time, default=0.0)
    
    def calculate_value_delivery(self, ai_adoption: float, 
                                feature_value: float = 10000) -> Dict[str, float]:
        """
        Calculate actual value delivered to customers.
        
        Args:
            ai_adoption: AI adoption rate (0-1)
            feature_value: Average value per feature ($)
        """
        # Get throughput
        throughput_metrics = self.calculate_throughput(ai_adoption)
        features_per_day = throughput_metrics['throughput_per_day']
        
        # Get quality
        quality_metrics = self.calculate_quality_impact(ai_adoption)
        defect_rate = quality_metrics['defects_in_production_per_100'] / 100
        
        # Calculate deployment frequency impact
        deploy_frequencies = {
            'daily': 1.0,
            'weekly': 0.2,
            'biweekly': 0.1,
            'monthly': 0.033
        }
        deploy_factor = deploy_frequencies.get(self.deployment_frequency, 0.1)
        
        # Features that actually make it to production
        deployed_features_per_day = features_per_day * deploy_factor * (1 - self.rollback_rate)
        
        # Value delivered (accounting for defects reducing value)
        value_reduction_from_defects = defect_rate * 0.5  # Each defect reduces value by 50%
        net_value_per_feature = feature_value * (1 - value_reduction_from_defects)
        
        daily_value = deployed_features_per_day * net_value_per_feature
        
        # Cost of incidents
        incidents_per_day = deployed_features_per_day * defect_rate * 0.1  # 10% of defects cause incidents
        incident_cost = incidents_per_day * 5000  # $5000 per incident average
        
        # Include queue costs in value calculation
        queue_costs = self.calculate_queue_costs()
        daily_queue_cost = queue_costs['total_daily_queue_cost']
        
        return {
            'features_deployed_per_day': deployed_features_per_day,
            'gross_value_per_day': deployed_features_per_day * feature_value,
            'net_value_per_day': daily_value,
            'incident_cost_per_day': incident_cost,
            'queue_cost_per_day': daily_queue_cost,
            'value_after_incidents': daily_value - incident_cost,
            'value_after_all_costs': daily_value - incident_cost - daily_queue_cost,
            'flow_efficiency': self.calculate_flow_efficiency(),
            'value_efficiency': safe_divide(daily_value - incident_cost - daily_queue_cost, 
                                          deployed_features_per_day * feature_value,
                                          default=0)
        }


def create_standard_pipeline(team_size: int, 
                            test_automation: float = 0.3,
                            deployment_frequency: str = "weekly") -> DeliveryPipeline:
    """Create a standard delivery pipeline configuration."""
    
    stages = {
        PipelineStage.REQUIREMENTS: StageMetrics(
            stage=PipelineStage.REQUIREMENTS,
            base_throughput=5.0,  # 5 requirements per day
            base_cycle_time=2.0,  # 2 days per requirement
            base_quality=0.8,
            base_capacity=10.0,
            ai_throughput_multiplier=1.1,  # AI helps a bit with requirements
            ai_cycle_time_multiplier=0.9,
            ai_quality_multiplier=1.0
        ),
        PipelineStage.DESIGN: StageMetrics(
            stage=PipelineStage.DESIGN,
            base_throughput=4.0,
            base_cycle_time=1.0,
            base_quality=0.85,
            base_capacity=8.0,
            ai_throughput_multiplier=1.2,  # AI helps with design exploration
            ai_cycle_time_multiplier=0.8,
            ai_quality_multiplier=0.95  # May miss edge cases
        ),
        PipelineStage.CODING: StageMetrics(
            stage=PipelineStage.CODING,
            base_throughput=3.0,
            base_cycle_time=2.0,
            base_quality=0.75,
            base_capacity=team_size,
            ai_throughput_multiplier=1.5,  # AI significantly helps coding speed
            ai_cycle_time_multiplier=0.6,  # 40% faster
            ai_quality_multiplier=0.9  # But quality may suffer
        ),
        PipelineStage.TESTING: StageMetrics(
            stage=PipelineStage.TESTING,
            base_throughput=2.5,
            base_cycle_time=1.5,
            base_quality=0.9,
            base_capacity=team_size * 0.5,
            ai_throughput_multiplier=1.1,  # AI helps a little
            ai_cycle_time_multiplier=1.2,  # But more code to test
            ai_quality_multiplier=0.85  # AI-generated tests less effective
        ),
        PipelineStage.CODE_REVIEW: StageMetrics(
            stage=PipelineStage.CODE_REVIEW,
            base_throughput=4.0,
            base_cycle_time=0.5,
            base_quality=0.85,
            base_capacity=team_size * 0.3,
            ai_throughput_multiplier=0.8,  # AI code harder to review
            ai_cycle_time_multiplier=1.3,  # Takes longer
            ai_quality_multiplier=0.9  # May miss AI-specific issues
        ),
        PipelineStage.DEPLOYMENT: StageMetrics(
            stage=PipelineStage.DEPLOYMENT,
            base_throughput=10.0,
            base_cycle_time=0.2,
            base_quality=0.95,
            base_capacity=20.0,
            ai_throughput_multiplier=1.0,  # No impact
            ai_cycle_time_multiplier=1.0,
            ai_quality_multiplier=1.0
        ),
        PipelineStage.MONITORING: StageMetrics(
            stage=PipelineStage.MONITORING,
            base_throughput=20.0,
            base_cycle_time=0.1,
            base_quality=0.9,
            base_capacity=50.0,
            ai_throughput_multiplier=1.0,
            ai_cycle_time_multiplier=1.1,  # Slightly more to monitor
            ai_quality_multiplier=0.95  # AI behavior less predictable
        )
    }
    
    testing_strategy = TestingStrategy(
        automation_coverage=test_automation,
        test_execution_time_manual=4.0,  # 4 hours manual
        test_execution_time_automated=0.5,  # 30 minutes automated
        ai_test_generation_quality=0.6,  # AI tests are mediocre
        test_review_overhead=0.3  # 30% overhead to review AI tests
    )
    
    return DeliveryPipeline(
        stages=stages,
        testing_strategy=testing_strategy,
        team_size=team_size,
        deployment_frequency=deployment_frequency
    )