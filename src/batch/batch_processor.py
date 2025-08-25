"""
Batch processing engine for running multiple scenarios in parallel with progress tracking.
Supports configuration via YAML files and generates comparative analysis reports.
"""

import os
import yaml
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
from tqdm import tqdm
import pandas as pd
import json

from ..utils.exceptions import ConfigurationError, CalculationError
from ..utils.colors import *
from ..utils.cache import get_cache_statistics


@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    
    scenarios: List[str]
    parallel_workers: int = 4
    output_format: str = 'markdown'  # markdown, json, csv
    output_dir: str = 'outputs/batch'
    generate_comparison: bool = True
    include_monte_carlo: bool = False
    monte_carlo_iterations: int = 1000
    include_sensitivity: bool = False
    sensitivity_samples: int = 512
    save_individual_reports: bool = True
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'BatchConfig':
        """Load batch configuration from YAML file"""
        try:
            with open(yaml_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return cls(**config_data)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Batch configuration file not found: {yaml_path}",
                config_file=yaml_path,
                resolution_steps=[
                    "Check if the file path is correct",
                    "Create a batch configuration file",
                    "Use the example batch_config.yaml as template"
                ]
            )
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in batch configuration: {e}",
                config_file=yaml_path,
                resolution_steps=[
                    "Check YAML syntax",
                    "Ensure proper indentation",
                    "Validate against example configuration"
                ]
            )


@dataclass
class BatchResult:
    """Results from a single batch scenario run"""
    
    scenario_name: str
    success: bool
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    cache_hit: bool = False


class BatchProcessor:
    """
    Processes multiple scenarios in parallel with progress tracking.
    """
    
    def __init__(self, config: BatchConfig):
        """
        Initialize batch processor.
        
        Args:
            config: Batch processing configuration
        """
        self.config = config
        self.results: List[BatchResult] = []
        self.start_time = None
        self.end_time = None
        
        # Ensure output directory exists
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Determine optimal worker count
        if config.parallel_workers <= 0:
            self.worker_count = mp.cpu_count()
        else:
            self.worker_count = min(config.parallel_workers, mp.cpu_count())
    
    def run(self) -> Tuple[List[BatchResult], str]:
        """
        Execute batch processing for all configured scenarios.
        
        Returns:
            Tuple of (results list, summary report)
        """
        self.start_time = time.time()
        
        print(header("Batch Processing"))
        print(f"Scenarios to process: {len(self.config.scenarios)}")
        print(f"Parallel workers: {self.worker_count}")
        print(f"Output directory: {self.config.output_dir}")
        print()
        
        # Process scenarios in parallel
        if self.worker_count > 1:
            self._run_parallel()
        else:
            self._run_sequential()
        
        self.end_time = time.time()
        
        # Generate reports
        summary_report = self._generate_summary_report()
        
        if self.config.generate_comparison:
            comparison_report = self._generate_comparison_report()
            summary_report += "\n\n" + comparison_report
        
        # Save batch results
        self._save_batch_results(summary_report)
        
        return self.results, summary_report
    
    def _run_parallel(self):
        """Run scenarios in parallel using process pool"""
        from main import AIImpactModel
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit all scenarios
            future_to_scenario = {}
            
            for scenario in self.config.scenarios:
                future = executor.submit(self._process_scenario, scenario)
                future_to_scenario[future] = scenario
            
            # Process results with progress bar
            with tqdm(total=len(self.config.scenarios), desc="Processing scenarios") as pbar:
                for future in as_completed(future_to_scenario):
                    scenario = future_to_scenario[future]
                    
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout
                        self.results.append(result)
                        
                        if result.success:
                            pbar.set_postfix_str(f"✓ {scenario}")
                        else:
                            pbar.set_postfix_str(f"✗ {scenario}: {result.error_message}")
                    
                    except Exception as e:
                        self.results.append(BatchResult(
                            scenario_name=scenario,
                            success=False,
                            error_message=str(e),
                            execution_time=0
                        ))
                        pbar.set_postfix_str(f"✗ {scenario}: Timeout/Error")
                    
                    pbar.update(1)
    
    def _run_sequential(self):
        """Run scenarios sequentially with progress bar"""
        with tqdm(self.config.scenarios, desc="Processing scenarios") as pbar:
            for scenario in pbar:
                pbar.set_postfix_str(f"Running {scenario}")
                result = self._process_scenario(scenario)
                self.results.append(result)
                
                if result.success:
                    pbar.set_postfix_str(f"✓ {scenario}")
                else:
                    pbar.set_postfix_str(f"✗ {scenario}")
    
    def _process_scenario(self, scenario_name: str) -> BatchResult:
        """
        Process a single scenario.
        
        Args:
            scenario_name: Name of scenario to process
            
        Returns:
            BatchResult with processing outcome
        """
        from main import AIImpactModel
        
        start_time = time.time()
        cache_stats_before = get_cache_statistics().hits
        
        try:
            # Initialize model
            model = AIImpactModel()
            
            # Run scenario
            results = model._run_scenario_cached(scenario_name)
            
            # Check if this was a cache hit
            cache_stats_after = get_cache_statistics().hits
            cache_hit = cache_stats_after > cache_stats_before
            
            # Save individual report if requested
            if self.config.save_individual_reports:
                self._save_individual_report(scenario_name, results)
            
            # Run additional analyses if requested
            if self.config.include_monte_carlo:
                # Run Monte Carlo simulation
                monte_carlo_results = model.run_monte_carlo(
                    scenario_name,
                    iterations=self.config.monte_carlo_iterations
                )
                results['monte_carlo'] = {
                    'mean_npv': float(monte_carlo_results.npv_stats['mean']),
                    'std_npv': float(monte_carlo_results.npv_stats['std']),
                    'percentile_5': float(monte_carlo_results.npv_stats.get('p5', monte_carlo_results.npv_stats.get('p10', 0))),
                    'percentile_95': float(monte_carlo_results.npv_stats.get('p95', monte_carlo_results.npv_stats.get('p90', 0))),
                    'probability_positive': float(monte_carlo_results.probability_positive_npv),
                    'iterations': self.config.monte_carlo_iterations
                }
            
            if self.config.include_sensitivity:
                # Run sensitivity analysis
                from ..analysis.sensitivity_analysis import run_sensitivity_analysis
                
                sensitivity_results = run_sensitivity_analysis(
                    scenario_name,
                    n_samples=self.config.sensitivity_samples
                )
                
                # Extract top parameters by importance
                results['sensitivity'] = {
                    'top_parameters': sensitivity_results['ranked_parameters'][:5],
                    'total_variance_explained': sensitivity_results.get('variance_explained', 0),
                    'samples': self.config.sensitivity_samples
                }
            
            execution_time = time.time() - start_time
            
            return BatchResult(
                scenario_name=scenario_name,
                success=True,
                results=results,
                execution_time=execution_time,
                cache_hit=cache_hit
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return BatchResult(
                scenario_name=scenario_name,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _save_individual_report(self, scenario_name: str, results: Dict[str, Any]):
        """Save individual scenario report"""
        output_path = Path(self.config.output_dir) / f"{scenario_name}_report.json"
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for key, value in results.items():
            if hasattr(value, 'tolist'):  # numpy array
                serializable_results[key] = value.tolist()
            elif hasattr(value, '__dict__'):  # object with attributes
                serializable_results[key] = str(value)
            else:
                serializable_results[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
    
    def _generate_summary_report(self) -> str:
        """Generate summary report of batch processing"""
        total_time = self.end_time - self.start_time if self.end_time else 0
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        
        report = []
        report.append("# Batch Processing Summary\n")
        report.append(f"**Total scenarios processed**: {len(self.results)}")
        report.append(f"**Successful**: {successful}")
        report.append(f"**Failed**: {failed}")
        report.append(f"**Total time**: {total_time:.2f} seconds")
        report.append(f"**Average time per scenario**: {total_time/len(self.results):.2f} seconds")
        
        # Cache statistics
        cache_stats = get_cache_statistics()
        report.append(f"\n## Cache Performance")
        report.append(f"- Hit rate: {cache_stats.hit_rate:.1%}")
        report.append(f"- Time saved: {cache_stats.total_time_saved:.2f} seconds")
        
        # Performance metrics
        report.append(f"\n## Performance Metrics")
        report.append("| Scenario | Status | Time (s) | Cache Hit |")
        report.append("|----------|--------|----------|-----------|")
        
        for result in sorted(self.results, key=lambda x: x.execution_time, reverse=True):
            status = "✓ Success" if result.success else f"✗ Failed"
            cache_status = "Yes" if result.cache_hit else "No"
            report.append(f"| {result.scenario_name} | {status} | {result.execution_time:.2f} | {cache_status} |")
        
        # Error summary
        if failed > 0:
            report.append("\n## Errors")
            for result in self.results:
                if not result.success:
                    report.append(f"- **{result.scenario_name}**: {result.error_message}")
        
        return "\n".join(report)
    
    def _generate_comparison_report(self) -> str:
        """Generate comparison report for successful scenarios"""
        successful_results = [r for r in self.results if r.success and r.results]
        
        if len(successful_results) < 2:
            return "## Comparison Report\n\nInsufficient successful scenarios for comparison."
        
        report = []
        report.append("## Comparison Report\n")
        report.append("### Scenario Comparison\n")
        
        # Helper function to get value from nested or flat structure
        def get_val(data, key, default=0):
            # Try flat structure first
            if key in data:
                return data[key]
            # Try nested structure (e.g., financial.npv)
            if 'financial' in data and key in data['financial']:
                return data['financial'][key]
            if 'adoption' in data and key in data['adoption']:
                return data['adoption'][key]
            return default
        
        # Create comparison table
        comparison_data = []
        for result in successful_results:
            data = result.results
            # Get ROI value - handle both roi and roi_percent
            roi_value = get_val(data, 'roi', get_val(data, 'roi_percent', 0))
            if roi_value < 10:  # Likely a ratio, convert to percentage
                roi_value = roi_value * 100
            
            # Get peak adoption - handle both percentage and ratio
            peak_adopt = get_val(data, 'peak', get_val(data, 'peak_adoption', 0))
            if peak_adopt <= 1.0:  # Likely a ratio, convert to percentage
                peak_adopt = peak_adopt * 100
                
            comparison_data.append({
                'Scenario': result.scenario_name,
                'NPV': f"${get_val(data, 'npv', 0):,.0f}",
                'ROI': f"{roi_value:.1f}%",
                'Breakeven': f"{get_val(data, 'breakeven_month', 'N/A')} months",
                'Peak Adoption': f"{peak_adopt:.1f}%",
                'Total Cost': f"${get_val(data, 'total_cost_3y', 0):,.0f}",
                'Total Value': f"${get_val(data, 'total_value_3y', 0):,.0f}"
            })
        
        # Convert to markdown table
        df = pd.DataFrame(comparison_data)
        report.append(df.to_markdown(index=False))
        
        # Find best/worst scenarios
        report.append("\n### Key Insights")
        
        # Helper function to get value from nested or flat structure
        def get_value(data, key, default=0):
            # Try flat structure first
            if key in data:
                return data[key]
            # Try nested structure (e.g., financial.npv)
            if 'financial' in data and key in data['financial']:
                return data['financial'][key]
            if 'adoption' in data and key in data['adoption']:
                return data['adoption'][key]
            return default
        
        # Best NPV
        best_npv = max(successful_results, key=lambda x: get_value(x.results, 'npv'))
        npv_val = get_value(best_npv.results, 'npv')
        report.append(f"- **Highest NPV**: {best_npv.scenario_name} (${npv_val:,.0f})")
        
        # Best ROI
        best_roi = max(successful_results, key=lambda x: get_value(x.results, 'roi', get_value(x.results, 'roi_percent')))
        roi_val = get_value(best_roi.results, 'roi', get_value(best_roi.results, 'roi_percent'))
        # Convert ROI to percentage if needed
        if roi_val < 10:  # Likely a ratio, not percentage
            roi_val = roi_val * 100
        report.append(f"- **Highest ROI**: {best_roi.scenario_name} ({roi_val:.1f}%)")
        
        # Fastest breakeven
        scenarios_with_breakeven = [r for r in successful_results 
                                   if get_value(r.results, 'breakeven_month', None) is not None]
        if scenarios_with_breakeven:
            fastest_breakeven = min(scenarios_with_breakeven, 
                                  key=lambda x: get_value(x.results, 'breakeven_month', float('inf')))
            breakeven_val = get_value(fastest_breakeven.results, 'breakeven_month')
            report.append(f"- **Fastest Breakeven**: {fastest_breakeven.scenario_name} "
                         f"({breakeven_val} months)")
        
        # Add failed scenarios info if any
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            report.append("\n### Failed Scenarios")
            for result in failed_results:
                report.append(f"- **{result.scenario_name}**: Failed - {result.error_message}")
        
        return "\n".join(report)
    
    def _save_batch_results(self, report: str):
        """Save batch processing results and report"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Save markdown report
        report_path = Path(self.config.output_dir) / f"batch_report_{timestamp}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n{success('✓')} Batch report saved to: {info(str(report_path))}")
        
        # Save raw results as JSON
        results_path = Path(self.config.output_dir) / f"batch_results_{timestamp}.json"
        results_data = []
        
        for result in self.results:
            result_dict = {
                'scenario': result.scenario_name,
                'success': result.success,
                'execution_time': result.execution_time,
                'cache_hit': result.cache_hit,
                'error': result.error_message
            }
            
            if result.results:
                # Add key metrics
                result_dict['metrics'] = {
                    'npv': result.results.get('npv'),
                    'roi_percent': result.results.get('roi_percent'),
                    'breakeven_month': result.results.get('breakeven_month'),
                    'peak_adoption': result.results.get('peak_adoption')
                }
            
            results_data.append(result_dict)
        
        with open(results_path, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"{success('✓')} Raw results saved to: {info(str(results_path))}")


def run_batch_from_config(config_path: str) -> Tuple[List[BatchResult], str]:
    """
    Convenience function to run batch processing from a configuration file.
    
    Args:
        config_path: Path to batch configuration YAML
        
    Returns:
        Tuple of (results list, summary report)
    """
    config = BatchConfig.from_yaml(config_path)
    processor = BatchProcessor(config)
    return processor.run()