"""
Testing strategy models for software development.
Models different testing approaches and their interaction with AI tools.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio
from ..utils.exceptions import ValidationError


class TestingApproach(Enum):
    """Different testing methodologies."""
    MANUAL = "manual"
    AUTOMATED = "automated"
    TDD = "test_driven_development"
    BDD = "behavior_driven_development"
    PROPERTY_BASED = "property_based"
    EXPLORATORY = "exploratory"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestLevel(Enum):
    """Testing levels in the pyramid."""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    E2E = "end_to_end"
    ACCEPTANCE = "acceptance"


@dataclass
class TestPyramid:
    """Represents the distribution of tests across levels."""
    
    unit_percentage: float = 0.70  # 70% unit tests
    integration_percentage: float = 0.20  # 20% integration
    e2e_percentage: float = 0.10  # 10% E2E/system
    
    def __post_init__(self):
        """Validate test pyramid proportions."""
        total = self.unit_percentage + self.integration_percentage + self.e2e_percentage
        if abs(total - 1.0) > 0.01:
            raise ValidationError(
                field_name="test_pyramid",
                value=total,
                expected="sum to 1.0",
                suggestion="Adjust test level percentages to sum to 100%"
            )
    
    def get_ai_effectiveness(self, level: TestLevel) -> float:
        """AI is more effective at lower-level tests."""
        effectiveness = {
            TestLevel.UNIT: 0.8,  # AI good at unit tests
            TestLevel.INTEGRATION: 0.5,  # Moderate at integration
            TestLevel.SYSTEM: 0.3,  # Poor at system tests
            TestLevel.E2E: 0.2,  # Very poor at E2E
            TestLevel.ACCEPTANCE: 0.1  # Almost useless at acceptance
        }
        return effectiveness.get(level, 0.3)


@dataclass
class TestAutomation:
    """Configuration for test automation."""
    
    coverage_target: float  # Target test coverage percentage
    current_coverage: float  # Current coverage
    automation_percentage: float  # % of tests automated
    
    # Time metrics (hours)
    manual_test_time: float  # Time to run manually
    automated_test_time: float  # Time to run automated
    maintenance_overhead: float  # % time maintaining tests
    
    # AI impact
    ai_test_generation_speed: float = 2.0  # AI 2x faster at writing tests
    ai_test_quality_ratio: float = 0.7  # But 30% lower quality
    ai_maintenance_multiplier: float = 1.5  # AI tests need 50% more maintenance
    
    def __post_init__(self):
        """Validate automation parameters."""
        validate_ratio(self.coverage_target, "coverage_target")
        validate_ratio(self.current_coverage, "current_coverage")
        validate_ratio(self.automation_percentage, "automation_percentage")
        validate_positive(self.manual_test_time, "manual_test_time")
        validate_positive(self.automated_test_time, "automated_test_time")
        validate_ratio(self.maintenance_overhead, "maintenance_overhead", max_val=1.0)
    
    def calculate_testing_time(self, code_volume: float, ai_adoption: float) -> Dict[str, float]:
        """Calculate total testing time including AI impact."""
        # AI generates more code to test
        test_volume = code_volume * (1 + ai_adoption * 0.5)
        
        # Split between manual and automated
        manual_volume = test_volume * (1 - self.automation_percentage)
        automated_volume = test_volume * self.automation_percentage
        
        # Base times
        manual_time = manual_volume * self.manual_test_time
        automated_time = automated_volume * self.automated_test_time
        
        # AI speeds up test writing but increases maintenance
        if ai_adoption > 0:
            test_writing_speedup = 1 / (1 + (self.ai_test_generation_speed - 1) * ai_adoption)
            maintenance_increase = 1 + (self.ai_maintenance_multiplier - 1) * ai_adoption
            
            automated_time = automated_time * test_writing_speedup * maintenance_increase
        
        # Add maintenance overhead
        maintenance_time = (manual_time + automated_time) * self.maintenance_overhead
        
        return {
            'manual_time': manual_time,
            'automated_time': automated_time,
            'maintenance_time': maintenance_time,
            'total_time': manual_time + automated_time + maintenance_time,
            'automation_roi': safe_divide(manual_time - automated_time, automated_time, default=0)
        }
    
    def get_defect_detection_rate(self, ai_adoption: float) -> float:
        """Calculate defect detection effectiveness."""
        # Base detection rates
        manual_detection = 0.70 * (1 - self.automation_percentage)
        automated_detection = 0.60 * self.automation_percentage
        
        # AI-generated tests are less effective
        if ai_adoption > 0:
            ai_test_portion = self.automation_percentage * ai_adoption
            ai_detection = automated_detection * self.ai_test_quality_ratio
            automated_detection = automated_detection * (1 - ai_adoption) + ai_detection
        
        total_detection = manual_detection + automated_detection
        
        # Coverage impact
        coverage_factor = self.current_coverage / self.coverage_target
        
        return min(0.95, total_detection * coverage_factor)


@dataclass
class TDDStrategy:
    """Test-Driven Development configuration."""
    
    adoption_percentage: float  # % of team doing TDD
    cycle_time_overhead: float = 1.2  # TDD adds 20% to initial dev time
    defect_reduction: float = 0.4  # But reduces defects by 40%
    refactoring_benefit: float = 0.3  # And improves code structure by 30%
    
    # AI interaction
    ai_tdd_effectiveness: float = 0.3  # AI struggles with TDD
    ai_breaks_red_green_refactor: float = 0.7  # Often generates code and tests together
    
    def __post_init__(self):
        """Validate TDD parameters."""
        validate_ratio(self.adoption_percentage, "adoption_percentage")
        if not 0.8 <= self.cycle_time_overhead <= 2.0:
            raise ValidationError(
                field_name="cycle_time_overhead",
                value=self.cycle_time_overhead,
                expected="between 0.8 and 2.0",
                suggestion="TDD typically adds 10-50% initial overhead"
            )
    
    def calculate_impact(self, ai_adoption: float) -> Dict[str, float]:
        """Calculate TDD impact on development."""
        # TDD effectiveness decreases with AI
        effective_tdd = self.adoption_percentage * (1 - ai_adoption * self.ai_breaks_red_green_refactor)
        
        # Cycle time impact
        cycle_multiplier = 1 + (self.cycle_time_overhead - 1) * effective_tdd
        
        # Quality impact
        defect_multiplier = 1 - self.defect_reduction * effective_tdd
        
        # Refactoring benefit (helps with tech debt)
        refactor_benefit = self.refactoring_benefit * effective_tdd
        
        return {
            'effective_tdd_adoption': effective_tdd,
            'cycle_time_multiplier': cycle_multiplier,
            'defect_multiplier': defect_multiplier,
            'refactoring_benefit': refactor_benefit,
            'ai_tdd_conflict': ai_adoption * self.ai_breaks_red_green_refactor
        }


@dataclass
class TestingCulture:
    """Organization's testing culture and maturity."""
    
    testing_first_mindset: float  # 0-1, how much testing is prioritized
    peer_review_thoroughness: float  # 0-1, how careful are reviews
    regression_test_discipline: float  # 0-1, how well regression tests maintained
    test_documentation_quality: float  # 0-1, how well tests documented
    
    # Test automation maturity (replaces manual QA focus)
    test_automation_maturity: float = 0.7  # 0-1, level of test automation sophistication
    tdd_adoption: float = 0.3  # 0-1, extent of TDD practice adoption
    shift_left_maturity: float = 0.5  # 0-1, how early testing happens in pipeline
    
    # Legacy QA ratio for backward compatibility (DEPRECATED - will be removed)
    qa_developer_ratio: float = None  # Auto-calculated from automation maturity
    testing_in_definition_of_done: bool = True
    automated_testing_in_ci: bool = True
    
    # Quality responsibility distribution
    developer_testing_responsibility: float = None  # Auto-calculated based on maturity
    quality_gate_automation: float = None  # Auto-calculated
    
    def __post_init__(self):
        """Validate culture metrics."""
        validate_ratio(self.testing_first_mindset, "testing_first_mindset")
        validate_ratio(self.peer_review_thoroughness, "peer_review_thoroughness")
        validate_ratio(self.regression_test_discipline, "regression_test_discipline")
        validate_ratio(self.test_documentation_quality, "test_documentation_quality")
        validate_ratio(self.test_automation_maturity, "test_automation_maturity")
        validate_ratio(self.tdd_adoption, "tdd_adoption")
        validate_ratio(self.shift_left_maturity, "shift_left_maturity")
        
        # Calculate legacy QA ratio for backward compatibility
        if self.qa_developer_ratio is None:
            self.qa_developer_ratio = self._calculate_legacy_qa_ratio()
        
        # Calculate derived metrics based on automation maturity
        if self.developer_testing_responsibility is None:
            self.developer_testing_responsibility = self._calculate_developer_testing_responsibility()
        
        if self.quality_gate_automation is None:
            self.quality_gate_automation = self._calculate_quality_gate_automation()
        
        # Legacy compatibility properties
        self.developer_testing_load = self.developer_testing_responsibility
        self.quality_gate_strictness = self.quality_gate_automation
    
    def _calculate_legacy_qa_ratio(self) -> float:
        """Calculate legacy QA ratio for backward compatibility."""
        # Convert automation maturity to equivalent QA ratio for legacy support
        # Lower automation maturity implies higher reliance on manual QA
        return max(0.0, (1.0 - self.test_automation_maturity) * 0.3)
    
    def _calculate_developer_testing_responsibility(self) -> float:
        """Calculate developer testing responsibility based on automation maturity."""
        # Higher automation maturity means developers spend more focused time on testing
        # but testing becomes more efficient due to automation
        base_responsibility = 0.20  # 20% baseline for testing activities
        
        # TDD adoption increases developer testing time but improves quality
        tdd_factor = self.tdd_adoption * 0.15  # Up to 15% more time for TDD
        
        # Shift-left practices increase upfront testing time
        shift_left_factor = self.shift_left_maturity * 0.10  # Up to 10% more for early testing
        
        # Automation maturity reduces manual testing overhead
        automation_efficiency = self.test_automation_maturity * 0.05  # Up to 5% time savings
        
        total_responsibility = base_responsibility + tdd_factor + shift_left_factor - automation_efficiency
        return max(0.15, min(0.40, total_responsibility))  # Cap between 15-40%
    
    def _calculate_quality_gate_automation(self) -> float:
        """Calculate quality gate automation level."""
        # Quality gates should be automated, not manual
        base_automation = self.test_automation_maturity * 0.6  # Base from automation maturity
        
        # TDD practices improve automated quality gates
        tdd_boost = self.tdd_adoption * 0.2
        
        # Shift-left practices catch issues earlier
        shift_left_boost = self.shift_left_maturity * 0.15
        
        # Testing mindset affects consistency
        mindset_factor = self.testing_first_mindset * 0.05
        
        total_automation = base_automation + tdd_boost + shift_left_boost + mindset_factor
        return max(0.3, min(0.95, total_automation))  # Cap between 30-95%
    
    def get_quality_multiplier(self, ai_adoption: float) -> float:
        """Calculate overall quality impact from testing culture and automation."""
        # Base quality from culture and practices
        base_quality = (
            self.testing_first_mindset * 0.25 +
            self.peer_review_thoroughness * 0.25 +
            self.regression_test_discipline * 0.15 +
            self.test_documentation_quality * 0.10 +
            self.test_automation_maturity * 0.20 +  # Automation is key
            self.tdd_adoption * 0.05  # TDD provides quality foundation
        )
        
        # AI impact depends on automation maturity and practices, NOT manual QA
        automation_protection = self.test_automation_maturity * 0.3
        tdd_protection = self.tdd_adoption * 0.2  # TDD helps catch AI mistakes
        shift_left_protection = self.shift_left_maturity * 0.1  # Early detection
        
        # AI disruption is mitigated by good practices, not manual QA
        ai_disruption = ai_adoption * (0.3 - automation_protection - tdd_protection - shift_left_protection)
        ai_disruption = max(0.05, ai_disruption)  # Always some disruption
        
        # Developer responsibility factor - higher responsibility can mean better ownership
        responsibility_factor = 1 + (self.developer_testing_responsibility - 0.20) * 0.5
        
        quality_multiplier = base_quality * (1 - ai_disruption) * responsibility_factor
        
        return max(0.3, min(1.3, quality_multiplier))
    
    def get_ai_testing_value(self, ai_adoption: float) -> float:
        """Calculate the value AI provides for testing based on automation maturity."""
        # Base AI testing value depends on current automation gaps
        automation_gap = 1.0 - self.test_automation_maturity
        base_value = 0.4 + (automation_gap * 0.4)  # Higher value where automation is lacking
        
        # TDD teams get more value from AI test generation
        tdd_boost = self.tdd_adoption * 0.2
        
        # Testing-first mindset improves AI test utilization
        mindset_boost = self.testing_first_mindset * 0.1
        
        # Shift-left maturity affects how well AI tests are integrated
        integration_factor = self.shift_left_maturity * 0.1
        
        # Developer testing responsibility affects AI test value
        responsibility_factor = self.developer_testing_responsibility * 0.5
        
        total_value = base_value + tdd_boost + mindset_boost + integration_factor + responsibility_factor
        
        # Risk of over-reliance - higher for teams with lower automation maturity
        over_reliance_risk = ai_adoption * (0.2 + automation_gap * 0.2)
        
        ai_testing_value = total_value * (1 - over_reliance_risk)
        
        return max(0.2, min(1.0, ai_testing_value))


@dataclass
class CompleteTestStrategy:
    """Complete testing strategy combining all aspects."""
    
    pyramid: TestPyramid
    automation: TestAutomation
    tdd: Optional[TDDStrategy]
    culture: TestingCulture
    
    # Testing approaches used
    approaches: List[TestingApproach]
    
    # Flakiness and reliability
    test_flakiness_rate: float = 0.05  # 5% of tests are flaky
    flaky_test_impact: float = 0.2  # Flaky tests reduce confidence by 20%
    
    def calculate_comprehensive_impact(self, ai_adoption: float, 
                                      code_volume: float) -> Dict[str, float]:
        """Calculate comprehensive testing impact."""
        results = {}
        
        # Time impact
        time_metrics = self.automation.calculate_testing_time(code_volume, ai_adoption)
        results.update(time_metrics)
        
        # TDD impact if applicable
        if self.tdd:
            tdd_impact = self.tdd.calculate_impact(ai_adoption)
            results['tdd_impact'] = tdd_impact
            cycle_multiplier = tdd_impact['cycle_time_multiplier']
            defect_multiplier = tdd_impact['defect_multiplier']
        else:
            cycle_multiplier = 1.0
            defect_multiplier = 1.0
        
        # Detection effectiveness
        detection_rate = self.automation.get_defect_detection_rate(ai_adoption)
        
        # Culture impact
        culture_multiplier = self.culture.get_quality_multiplier(ai_adoption)
        
        # Flakiness impact (AI tests tend to be flakier)
        ai_flakiness = self.test_flakiness_rate * (1 + ai_adoption * 0.5)
        confidence_reduction = ai_flakiness * self.flaky_test_impact
        
        # Overall metrics
        results['total_cycle_time'] = time_metrics['total_time'] * cycle_multiplier
        results['defect_escape_rate'] = (1 - detection_rate) * defect_multiplier
        results['quality_score'] = culture_multiplier * (1 - confidence_reduction)
        results['testing_confidence'] = detection_rate * (1 - confidence_reduction)
        results['flakiness_rate'] = ai_flakiness
        
        # ROI calculation
        prevented_defects = detection_rate * 100  # Assume 100 defects per period
        defect_cost = 5000  # $5000 per escaped defect
        testing_cost = time_metrics['total_time'] * 150  # $150/hour
        
        results['testing_roi'] = safe_divide(
            prevented_defects * defect_cost - testing_cost,
            testing_cost,
            default=0
        )
        
        return results


def create_basic_test_strategy(team_type: str = "balanced") -> CompleteTestStrategy:
    """Create a basic test strategy based on team automation maturity and practices."""
    
    if team_type == "startup" or team_type == "startup_no_qa":
        # Early-stage teams: Low automation maturity, limited TDD adoption
        # Modern approach: Focus on automation rather than manual QA
        pyramid = TestPyramid(
            unit_percentage=0.60,
            integration_percentage=0.25,
            e2e_percentage=0.15
        )
        automation = TestAutomation(
            coverage_target=0.65,
            current_coverage=0.45,
            automation_percentage=0.40,  # Focus on building automation
            manual_test_time=2.5,
            automated_test_time=0.12,
            maintenance_overhead=0.18
        )
        tdd = TDDStrategy(adoption_percentage=0.10)  # Some TDD adoption
        culture = TestingCulture(
            testing_first_mindset=0.4,
            peer_review_thoroughness=0.6,  # Peer review is primary quality gate
            regression_test_discipline=0.4,
            test_documentation_quality=0.3,
            test_automation_maturity=0.3,  # Low automation maturity
            tdd_adoption=0.1,
            shift_left_maturity=0.2
        )
        approaches = [TestingApproach.AUTOMATED, TestingApproach.EXPLORATORY]
        
    elif team_type == "enterprise":
        # Enterprise: High automation maturity, comprehensive TDD adoption
        # Focus on mature practices rather than manual QA processes
        pyramid = TestPyramid(
            unit_percentage=0.70,
            integration_percentage=0.20,
            e2e_percentage=0.10
        )
        automation = TestAutomation(
            coverage_target=0.85,
            current_coverage=0.78,
            automation_percentage=0.85,  # High automation
            manual_test_time=3.0,  # Less manual testing
            automated_test_time=0.05,
            maintenance_overhead=0.20  # Better tooling reduces overhead
        )
        tdd = TDDStrategy(adoption_percentage=0.40)  # Higher TDD adoption
        culture = TestingCulture(
            testing_first_mindset=0.8,  # Strong testing culture
            peer_review_thoroughness=0.8,
            regression_test_discipline=0.8,
            test_documentation_quality=0.7,
            test_automation_maturity=0.8,  # High automation maturity
            tdd_adoption=0.4,
            shift_left_maturity=0.7  # Strong shift-left practices
        )
        approaches = [
            TestingApproach.AUTOMATED,
            TestingApproach.TDD,
            TestingApproach.PERFORMANCE,
            TestingApproach.SECURITY
        ]
        
    else:  # balanced
        # Balanced teams: Moderate automation maturity, growing TDD adoption
        pyramid = TestPyramid()  # Use defaults
        automation = TestAutomation(
            coverage_target=0.75,
            current_coverage=0.62,
            automation_percentage=0.60,  # Moderate automation
            manual_test_time=2.8,
            automated_test_time=0.08,
            maintenance_overhead=0.18
        )
        tdd = TDDStrategy(adoption_percentage=0.25)
        culture = TestingCulture(
            testing_first_mindset=0.6,
            peer_review_thoroughness=0.7,
            regression_test_discipline=0.6,
            test_documentation_quality=0.5,
            test_automation_maturity=0.6,  # Moderate automation maturity
            tdd_adoption=0.25,
            shift_left_maturity=0.4
        )
        approaches = [
            TestingApproach.AUTOMATED,
            TestingApproach.TDD
        ]  # Remove manual as primary approach
    
    return CompleteTestStrategy(
        pyramid=pyramid,
        automation=automation,
        tdd=tdd,
        culture=culture,
        approaches=approaches
    )