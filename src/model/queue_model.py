"""
Queue modeling for software delivery pipeline.
Implements Reinertsen's principles of product development flow and queueing theory.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio
from ..utils.exceptions import ValidationError, CalculationError


@dataclass
class QueueMetrics:
    """Metrics for a queue between pipeline stages."""
    
    # Queue characteristics
    arrival_rate: float  # Items arriving per day
    service_rate: float  # Items processed per day
    utilization: float   # Service utilization (0-1)
    
    # Queue performance (calculated from Little's Law)
    avg_queue_length: float      # Average items waiting
    avg_wait_time: float         # Average waiting time (days)
    avg_system_time: float       # Total time in system (wait + service)
    
    # Economic impact
    cost_of_delay_per_item: float = 1000.0  # $ per item per day
    queue_cost_per_day: float = 0.0         # Daily cost of this queue
    
    def __post_init__(self):
        """Calculate derived metrics using queueing theory."""
        validate_positive(self.arrival_rate, "arrival_rate")
        validate_positive(self.service_rate, "service_rate")
        
        # Basic M/M/1 queue calculations (Poisson arrivals, exponential service)
        if self.service_rate <= self.arrival_rate:
            # System is unstable - queue grows unbounded
            self.utilization = 1.0
            self.avg_queue_length = float('inf')
            self.avg_wait_time = float('inf') 
            self.avg_system_time = float('inf')
            self.queue_cost_per_day = float('inf')
        else:
            self.utilization = self.arrival_rate / self.service_rate
            
            # Little's Law applications
            self.avg_queue_length = (self.utilization ** 2) / (1 - self.utilization)
            self.avg_wait_time = self.avg_queue_length / self.arrival_rate
            self.avg_system_time = self.avg_wait_time + (1 / self.service_rate)
            
            # Economic impact of delays
            self.queue_cost_per_day = self.avg_queue_length * self.cost_of_delay_per_item


@dataclass
class WorkItem:
    """Represents work flowing through the pipeline."""
    
    id: str
    value: float  # Business value ($)
    urgency: float  # Cost of delay per day
    size: float  # Effort required (story points, hours, etc.)
    created_time: float = 0.0
    started_time: Optional[float] = None
    completed_time: Optional[float] = None
    
    def get_cost_of_delay(self, current_time: float) -> float:
        """Calculate accumulated cost of delay."""
        if self.completed_time:
            delay_time = self.completed_time - self.created_time
        else:
            delay_time = current_time - self.created_time
            
        return delay_time * self.urgency


@dataclass  
class PipelineQueue:
    """Models a queue between pipeline stages with WIP limits."""
    
    stage_name: str
    max_wip: Optional[int] = None  # Work In Progress limit
    batch_size: int = 1            # How many items processed together
    
    # Queue state
    waiting_items: List[WorkItem] = None
    in_progress_items: List[WorkItem] = None
    current_time: float = 0.0
    
    def __post_init__(self):
        """Initialize queue state."""
        if self.waiting_items is None:
            self.waiting_items = []
        if self.in_progress_items is None:
            self.in_progress_items = []
    
    def can_accept_work(self) -> bool:
        """Check if queue can accept more work (WIP limit)."""
        if self.max_wip is None:
            return True
        return len(self.waiting_items) + len(self.in_progress_items) < self.max_wip
    
    def add_work_item(self, item: WorkItem) -> bool:
        """Add work item to queue if WIP allows."""
        if not self.can_accept_work():
            return False  # Blocked by WIP limit
            
        self.waiting_items.append(item)
        return True
    
    def start_work(self, capacity: int) -> List[WorkItem]:
        """Start work on items up to capacity, considering batch size."""
        if not self.waiting_items:
            return []
        
        # Determine how many items to start
        available_capacity = capacity - len(self.in_progress_items)
        items_to_start = min(
            available_capacity,
            len(self.waiting_items),
            self.batch_size  # Batch processing constraint
        )
        
        if items_to_start <= 0:
            return []
        
        # Move items from waiting to in-progress
        started_items = []
        for _ in range(items_to_start):
            item = self.waiting_items.pop(0)  # FIFO
            item.started_time = self.current_time
            self.in_progress_items.append(item)
            started_items.append(item)
        
        return started_items
    
    def complete_work(self, completed_items: List[WorkItem]) -> None:
        """Mark work items as completed."""
        for item in completed_items:
            if item in self.in_progress_items:
                item.completed_time = self.current_time
                self.in_progress_items.remove(item)
    
    def get_queue_metrics(self) -> QueueMetrics:
        """Calculate current queue performance metrics."""
        total_items = len(self.waiting_items) + len(self.in_progress_items)
        
        if total_items == 0:
            return QueueMetrics(
                arrival_rate=0.0,
                service_rate=1.0,  # Avoid division by zero
                utilization=0.0,
                avg_queue_length=0.0,
                avg_wait_time=0.0,
                avg_system_time=0.0
            )
        
        # Calculate rates (simplified - would need historical data for accuracy)
        avg_item_value = sum(item.value for item in self.waiting_items + self.in_progress_items) / total_items
        avg_urgency = sum(item.urgency for item in self.waiting_items + self.in_progress_items) / total_items
        
        # Estimate arrival and service rates based on current state
        arrival_rate = total_items / max(1.0, self.current_time)  # Rough estimate
        service_rate = max(arrival_rate * 1.1, 1.0)  # Assume slightly above arrival rate
        
        return QueueMetrics(
            arrival_rate=arrival_rate,
            service_rate=service_rate,
            utilization=min(0.99, arrival_rate / service_rate),
            avg_queue_length=len(self.waiting_items),
            avg_wait_time=0.0,  # Would need historical data
            avg_system_time=0.0,  # Would need historical data
            cost_of_delay_per_item=avg_urgency
        )
    
    def get_total_cost_of_delay(self) -> float:
        """Calculate total accumulated cost of delay in this queue."""
        total_cost = 0.0
        for item in self.waiting_items + self.in_progress_items:
            total_cost += item.get_cost_of_delay(self.current_time)
        return total_cost


class BatchSizeOptimizer:
    """Optimize batch sizes according to Reinertsen's principles."""
    
    @staticmethod
    def calculate_optimal_batch_size(
        transaction_cost: float,  # Cost to process a batch
        holding_cost_per_item: float,  # Cost per item per time unit
        demand_rate: float,  # Items per time unit
        variability: float = 1.0  # Coefficient of variation
    ) -> int:
        """
        Calculate optimal batch size using economic batch size formula.
        
        Based on Reinertsen's economic batch size model that balances:
        - Transaction costs (favor large batches)
        - Holding costs (favor small batches)
        - Variability (favors smaller batches)
        """
        if holding_cost_per_item <= 0 or demand_rate <= 0:
            return 1
        
        # Economic batch size formula (simplified)
        economic_batch_size = np.sqrt(
            (2 * transaction_cost * demand_rate) / holding_cost_per_item
        )
        
        # Adjust for variability - higher variability favors smaller batches
        variability_adjustment = 1.0 / (1.0 + variability)
        optimal_size = economic_batch_size * variability_adjustment
        
        return max(1, int(optimal_size))
    
    @staticmethod
    def calculate_batch_delay_cost(
        batch_size: int,
        item_urgency: float,
        processing_time: float
    ) -> float:
        """
        Calculate the delay cost imposed by batching.
        
        Items must wait for the entire batch to complete before being released.
        """
        # Average delay for items in batch (first item waits longest)
        avg_delay = processing_time * (batch_size - 1) / 2
        return avg_delay * item_urgency * batch_size


def calculate_flow_efficiency(
    value_add_time: float,
    total_lead_time: float
) -> float:
    """
    Calculate flow efficiency: ratio of value-add time to total time.
    
    Per Reinertsen, most product development has flow efficiency < 25%.
    This identifies opportunity for queue reduction.
    """
    return safe_divide(value_add_time, total_lead_time, default=0.0)


def apply_littles_law(
    avg_wip: float,
    throughput: float
) -> float:
    """
    Apply Little's Law: Lead Time = WIP / Throughput
    
    Fundamental relationship for managing flow in product development.
    """
    return safe_divide(avg_wip, throughput, default=float('inf'))