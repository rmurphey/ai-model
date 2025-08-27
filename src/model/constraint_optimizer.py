"""
Theory of Constraints optimizer implementing Goldratt's Five Focusing Steps.
Replaces global AI adoption optimization with constraint-focused approach.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np

from .delivery_pipeline import DeliveryPipeline, PipelineStage
from .queue_model import QueueMetrics, PipelineQueue
from ..utils.math_helpers import safe_divide, validate_positive
from ..utils.exceptions import ValidationError


class ConstraintType(Enum):
    """Types of constraints in the delivery pipeline."""
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    CODING = "coding"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    MONITORING = "monitoring"


@dataclass
class ConstraintAnalysis:
    """Results of constraint identification and analysis."""
    
    constraint_type: ConstraintType
    constraint_stage: str
    current_throughput: float
    constraint_utilization: float
    improvement_potential: float
    
    # Constraint-specific metrics
    stage_throughputs: Dict[str, float]
    queue_buildup: Dict[str, float]  # Items waiting at each stage
    cost_of_constraint: float  # Economic impact per day
    
    # Exploitation recommendations
    exploitation_strategies: List[str]
    exploitation_impact: float  # Expected throughput increase
    
    # Elevation strategies (if exploitation isn't enough)
    elevation_strategies: List[str]
    elevation_cost: float
    elevation_impact: float


@dataclass
class SubordinationRule:
    """Rule for subordinating non-constraint resources to the constraint."""
    
    stage: PipelineStage
    constraint_stage: PipelineStage
    rule_type: str  # "buffer", "pace", "priority"
    rule_description: str
    impact_factor: float  # How much this helps the constraint


class ConstraintOptimizer:
    """
    Implements Goldratt's Five Focusing Steps for software delivery optimization.
    
    Steps:
    1. Identify the constraint
    2. Exploit (optimize) the constraint
    3. Subordinate everything to the constraint
    4. Elevate the constraint
    5. Return to step 1 (avoid inertia)
    """
    
    def __init__(self, pipeline: DeliveryPipeline):
        self.pipeline = pipeline
        self.constraint_history: List[ConstraintAnalysis] = []
        self.subordination_rules: List[SubordinationRule] = []
    
    def identify_constraint(self, 
                          ai_adoption: float,
                          team_composition: Dict[str, int]) -> ConstraintAnalysis:
        """
        Step 1: Identify the system constraint (bottleneck).
        
        In software delivery, this is typically:
        - Code review (senior developer capacity)
        - Testing (automation maturity)
        - Deployment (frequency/process)
        """
        # Calculate throughput for each stage
        throughput_data = self.pipeline.calculate_throughput(ai_adoption)
        stage_throughputs = throughput_data['stage_throughputs']
        bottleneck_stage = throughput_data['bottleneck_stage']
        constraint_throughput = throughput_data['throughput_per_day']
        
        # Identify constraint type
        constraint_type = ConstraintType(bottleneck_stage)
        
        # Calculate utilization and queue buildup
        utilization = throughput_data['utilization']
        constraint_utilization = utilization[bottleneck_stage]
        
        # Calculate queue buildup (simplified model)
        queue_buildup = {}
        for stage, throughput in stage_throughputs.items():
            if stage == bottleneck_stage:
                queue_buildup[stage] = 0.0  # Constraint has no upstream queue
            else:
                # Queue builds up when upstream is faster than constraint
                upstream_excess = max(0, throughput - constraint_throughput)
                queue_buildup[stage] = upstream_excess
        
        # Calculate economic impact
        feature_value = 10000  # $10k per feature (from pipeline model)
        cost_of_constraint = (
            sum(queue_buildup.values()) * feature_value * 0.01  # 1% value loss per day
        )
        
        # Generate exploitation strategies
        exploitation_strategies = self._generate_exploitation_strategies(
            constraint_type, ai_adoption, team_composition, constraint_utilization
        )
        
        # Generate elevation strategies
        elevation_strategies = self._generate_elevation_strategies(
            constraint_type, team_composition
        )
        
        analysis = ConstraintAnalysis(
            constraint_type=constraint_type,
            constraint_stage=bottleneck_stage,
            current_throughput=constraint_throughput,
            constraint_utilization=constraint_utilization,
            improvement_potential=self._calculate_improvement_potential(
                constraint_type, constraint_utilization
            ),
            stage_throughputs=stage_throughputs,
            queue_buildup=queue_buildup,
            cost_of_constraint=cost_of_constraint,
            exploitation_strategies=exploitation_strategies,
            exploitation_impact=self._estimate_exploitation_impact(constraint_type),
            elevation_strategies=elevation_strategies,
            elevation_cost=self._estimate_elevation_cost(constraint_type, team_composition),
            elevation_impact=self._estimate_elevation_impact(constraint_type)
        )
        
        self.constraint_history.append(analysis)
        return analysis
    
    def exploit_constraint(self, 
                          constraint_analysis: ConstraintAnalysis,
                          ai_adoption: float) -> Dict[str, Any]:
        """
        Step 2: Exploit (optimize) the constraint without adding capacity.
        
        Extract maximum performance from existing constraint resources.
        """
        constraint_type = constraint_analysis.constraint_type
        current_throughput = constraint_analysis.current_throughput
        
        # Apply exploitation strategies
        improvements = {}
        
        if constraint_type == ConstraintType.CODE_REVIEW:
            # Optimize code review process - REALISTIC improvements
            improvements.update({
                'review_tooling_improvement': 0.05,  # 5% faster with better tools
                'review_focus_improvement': 0.08,   # 8% faster with focused reviews
                'ai_review_assistance': 0.04,       # 4% faster with AI assistance
                'batched_reviews': 0.03             # 3% faster with batching
            })
            
        elif constraint_type == ConstraintType.TESTING:
            # Optimize testing process - REALISTIC improvements
            improvements.update({
                'test_parallelization': 0.10,      # 10% faster with parallel execution
                'test_selection': 0.06,            # 6% faster with smart test selection
                'flaky_test_elimination': 0.05,    # 5% faster removing flaky tests
                'test_environment_optimization': 0.04  # 4% faster with better environments
            })
            
        elif constraint_type == ConstraintType.DEPLOYMENT:
            # Optimize deployment process - REALISTIC improvements
            improvements.update({
                'deployment_automation': 0.12,     # 12% faster with full automation
                'deployment_batching': 0.06,       # 6% faster with optimal batching
                'rollback_optimization': 0.04,     # 4% faster with better rollback
                'monitoring_integration': 0.03     # 3% faster with integrated monitoring
            })
        
        # Calculate total exploitation impact with MORE diminishing returns
        total_improvement = sum(improvements.values())
        # Apply stronger diminishing returns for realism
        # Cap at 30% total improvement even in best case
        effective_improvement = min(0.30, total_improvement * 0.7)  # 70% effectiveness, 30% max
        
        exploited_throughput = current_throughput * (1 + effective_improvement)
        
        return {
            'original_throughput': current_throughput,
            'exploited_throughput': exploited_throughput,
            'improvement_percent': effective_improvement * 100,
            'improvements_applied': improvements,
            'cost': 0,  # Exploitation should be zero-cost
            'timeline_days': 30  # Exploitation can be done quickly
        }
    
    def subordinate_to_constraint(self, 
                                 constraint_analysis: ConstraintAnalysis) -> List[SubordinationRule]:
        """
        Step 3: Subordinate everything else to the constraint.
        
        All non-constraint resources should support the constraint's needs.
        """
        constraint_stage = PipelineStage(constraint_analysis.constraint_stage)
        subordination_rules = []
        
        for stage in PipelineStage:
            if stage == constraint_stage:
                continue  # Don't subordinate constraint to itself
            
            if constraint_analysis.constraint_type == ConstraintType.CODE_REVIEW:
                if stage == PipelineStage.CODING:
                    # Coding should produce reviewable chunks
                    subordination_rules.append(SubordinationRule(
                        stage=stage,
                        constraint_stage=constraint_stage,
                        rule_type="batch_size",
                        rule_description="Create smaller, reviewable PRs to optimize review throughput",
                        impact_factor=0.15
                    ))
                elif stage == PipelineStage.TESTING:
                    # Testing should not wait for perfect code
                    subordination_rules.append(SubordinationRule(
                        stage=stage,
                        constraint_stage=constraint_stage,
                        rule_type="buffer",
                        rule_description="Start testing early, don't wait for perfect reviews",
                        impact_factor=0.10
                    ))
                    
            elif constraint_analysis.constraint_type == ConstraintType.TESTING:
                if stage == PipelineStage.CODING:
                    # Coding should produce testable code
                    subordination_rules.append(SubordinationRule(
                        stage=stage,
                        constraint_stage=constraint_stage,
                        rule_type="quality",
                        rule_description="Focus on testable, well-structured code",
                        impact_factor=0.12
                    ))
                elif stage == PipelineStage.CODE_REVIEW:
                    # Reviews should prioritize testability
                    subordination_rules.append(SubordinationRule(
                        stage=stage,
                        constraint_stage=constraint_stage,
                        rule_type="priority",
                        rule_description="Prioritize review of testable, test-enhanced code",
                        impact_factor=0.08
                    ))
        
        self.subordination_rules = subordination_rules
        return subordination_rules
    
    def elevate_constraint(self, 
                          constraint_analysis: ConstraintAnalysis,
                          team_composition: Dict[str, int]) -> Dict[str, Any]:
        """
        Step 4: Elevate the constraint by adding capacity.
        
        Only after exploitation and subordination should we add resources.
        """
        constraint_type = constraint_analysis.constraint_type
        
        elevation_options = []
        
        if constraint_type == ConstraintType.CODE_REVIEW:
            # Add senior developers or promote mid-level
            senior_count = team_composition.get('senior', 0)
            mid_count = team_composition.get('mid', 0)
            
            elevation_options.extend([
                {
                    'strategy': 'hire_senior_developer',
                    'cost': 180000,  # Annual salary + overhead
                    'timeline_days': 90,
                    'throughput_increase': 40,  # 40 more PRs/month reviewed
                    'description': 'Hire additional senior developer'
                },
                {
                    'strategy': 'promote_mid_to_senior',
                    'cost': 25000,  # Promotion cost + training
                    'timeline_days': 60,
                    'throughput_increase': 30,  # Promoted mid can review more
                    'description': f'Promote mid-level developer to senior (have {mid_count} available)'
                },
                {
                    'strategy': 'review_tooling',
                    'cost': 50000,  # Advanced review tools + setup
                    'timeline_days': 30,
                    'throughput_increase': senior_count * 5,  # 5 more PRs per senior
                    'description': 'Implement advanced code review tooling'
                }
            ])
            
        elif constraint_type == ConstraintType.TESTING:
            elevation_options.extend([
                {
                    'strategy': 'increase_test_automation',
                    'cost': 75000,  # Automation tools + setup time
                    'timeline_days': 45,
                    'throughput_increase': 50,  # Automated tests handle more
                    'description': 'Increase test automation coverage to 80%+'
                },
                {
                    'strategy': 'parallel_test_infrastructure',
                    'cost': 30000,  # Cloud infrastructure + setup
                    'timeline_days': 20,
                    'throughput_increase': 80,  # Parallel execution
                    'description': 'Add parallel test execution infrastructure'
                }
            ])
        
        # Select best elevation strategy (highest ROI)
        best_strategy = max(
            elevation_options,
            key=lambda x: x['throughput_increase'] / (x['cost'] / 12)  # Monthly ROI
        ) if elevation_options else None
        
        return {
            'recommended_strategy': best_strategy,
            'all_options': elevation_options,
            'constraint_type': constraint_type.value
        }
    
    def optimize_for_constraint(self, 
                               team_composition: Dict[str, int],
                               cost_per_seat: float,
                               feature_value: float = 4000,
                               avg_salary: int = 120000) -> Dict[str, Any]:
        """
        Complete Five Focusing Steps optimization.
        
        Returns optimal configuration focused on constraint throughput,
        not global AI adoption.
        """
        # Try different AI adoption levels, but focus on constraint throughput
        best_result = None
        best_value_per_day = -float('inf')
        
        for adoption_pct in range(10, 100, 10):
            ai_adoption = adoption_pct / 100
            
            # Step 1: Identify constraint
            constraint_analysis = self.identify_constraint(ai_adoption, team_composition)
            
            # Step 2: Exploit constraint
            exploitation_result = self.exploit_constraint(constraint_analysis, ai_adoption)
            
            # Step 3: Subordinate (rules applied automatically)
            subordination_rules = self.subordinate_to_constraint(constraint_analysis)
            subordination_benefit = sum(rule.impact_factor for rule in subordination_rules)
            
            # Calculate total throughput after exploitation and subordination
            exploited_throughput = exploitation_result['exploited_throughput']
            subordinated_throughput = exploited_throughput * (1 + subordination_benefit)
            
            # Calculate INCREMENTAL value (what we gain vs baseline)
            team_size = sum(team_composition.values())
            # Get actual baseline from pipeline with 0% AI
            baseline_analysis = self.identify_constraint(0.0, team_composition)
            baseline_throughput = baseline_analysis.current_throughput
            incremental_throughput = subordinated_throughput - baseline_throughput
            realistic_throughput = subordinated_throughput  # Use actual calculated throughput
            
            # Financial calculations with proper cost accounting
            monthly_salary_cost = (avg_salary / 12) * team_size
            monthly_ai_cost = cost_per_seat * team_size * ai_adoption
            implementation_cost_monthly = (team_size * 500) / 12  # Implementation cost amortized
            
            # Incremental value and cost
            monthly_incremental_value = incremental_throughput * feature_value * 30
            monthly_incremental_cost = monthly_ai_cost + implementation_cost_monthly
            
            # Net value per day
            net_value_per_day = (monthly_incremental_value - monthly_incremental_cost) / 30
            
            if net_value_per_day > best_value_per_day:
                best_value_per_day = net_value_per_day
                best_result = {
                    'optimal_ai_adoption': ai_adoption * 100,
                    'constraint_analysis': constraint_analysis,
                    'exploitation_result': exploitation_result,
                    'subordination_rules': subordination_rules,
                    'final_throughput': realistic_throughput,
                    'baseline_throughput': baseline_throughput,
                    'incremental_throughput': incremental_throughput,
                    'monthly_salary_cost': monthly_salary_cost,
                    'monthly_ai_cost': monthly_ai_cost,
                    'monthly_cost': monthly_salary_cost + monthly_ai_cost,
                    'monthly_incremental_value': monthly_incremental_value,
                    'monthly_incremental_cost': monthly_incremental_cost,
                    'net_value_per_day': net_value_per_day,
                    'realistic_roi': (monthly_incremental_value - monthly_incremental_cost) / monthly_incremental_cost * 100 if monthly_incremental_cost > 0 else 0,
                    'constraint_focused': True  # Flag indicating ToC approach
                }
        
        return best_result
    
    def _generate_exploitation_strategies(self, 
                                        constraint_type: ConstraintType,
                                        ai_adoption: float,
                                        team_composition: Dict[str, int],
                                        utilization: float) -> List[str]:
        """Generate specific strategies to exploit the constraint."""
        strategies = []
        
        if constraint_type == ConstraintType.CODE_REVIEW:
            strategies.extend([
                "Implement review checklists and templates",
                "Use AI-assisted code review tools",
                "Batch similar reviews together",
                "Focus senior reviews on architecture, juniors on syntax",
                f"Current utilization: {utilization:.1%} - optimize review scheduling"
            ])
            
        elif constraint_type == ConstraintType.TESTING:
            strategies.extend([
                "Increase test parallelization",
                "Implement smart test selection",
                "Eliminate flaky tests",
                "Optimize test environments",
                "Use risk-based testing prioritization"
            ])
            
        return strategies
    
    def _generate_elevation_strategies(self, 
                                     constraint_type: ConstraintType,
                                     team_composition: Dict[str, int]) -> List[str]:
        """Generate strategies to elevate (add capacity to) the constraint."""
        strategies = []
        
        if constraint_type == ConstraintType.CODE_REVIEW:
            senior_count = team_composition.get('senior', 0)
            mid_count = team_composition.get('mid', 0)
            
            strategies.extend([
                f"Hire additional senior developers (currently {senior_count})",
                f"Promote {min(mid_count, 2)} mid-level developers to senior",
                "Implement advanced review tooling",
                "Add code review specialists"
            ])
            
        elif constraint_type == ConstraintType.TESTING:
            strategies.extend([
                "Invest in test automation infrastructure",
                "Add dedicated test engineers",
                "Implement parallel testing infrastructure",
                "Add performance testing capacity"
            ])
            
        return strategies
    
    def _calculate_improvement_potential(self, 
                                       constraint_type: ConstraintType,
                                       utilization: float) -> float:
        """Calculate the potential improvement from optimizing this constraint."""
        # Higher utilization = more potential benefit from optimization
        base_potential = min(0.5, utilization * 0.6)  # Max 50% improvement
        
        # Constraint-specific multipliers
        if constraint_type == ConstraintType.CODE_REVIEW:
            return base_potential * 1.2  # Review optimization has high impact
        elif constraint_type == ConstraintType.TESTING:
            return base_potential * 1.1  # Testing optimization has good impact
        else:
            return base_potential
    
    def _estimate_exploitation_impact(self, constraint_type: ConstraintType) -> float:
        """Estimate REALISTIC throughput increase from exploitation strategies."""
        if constraint_type == ConstraintType.CODE_REVIEW:
            return 0.15  # 15% improvement realistic from review optimization
        elif constraint_type == ConstraintType.TESTING:
            return 0.20  # 20% improvement realistic from test optimization
        else:
            return 0.10  # 10% default improvement
    
    def _estimate_elevation_cost(self, 
                               constraint_type: ConstraintType,
                               team_composition: Dict[str, int]) -> float:
        """Estimate cost to elevate the constraint."""
        if constraint_type == ConstraintType.CODE_REVIEW:
            # Cost to hire senior developer or promote mid-level
            return 150000  # Annual cost
        elif constraint_type == ConstraintType.TESTING:
            # Cost for automation infrastructure
            return 75000
        else:
            return 50000  # Default elevation cost
    
    def _estimate_elevation_impact(self, constraint_type: ConstraintType) -> float:
        """Estimate throughput increase from elevation strategies."""
        if constraint_type == ConstraintType.CODE_REVIEW:
            return 0.40  # 40% improvement from adding senior capacity
        elif constraint_type == ConstraintType.TESTING:
            return 0.50  # 50% improvement from automation
        else:
            return 0.25  # 25% default improvement