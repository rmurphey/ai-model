#!/usr/bin/env python3
"""
Result Reproduction Engine
Extracts metadata from markdown reports and reproduces analysis results for validation.
"""

import re
import yaml
import os
import tempfile
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import numpy as np

from main import AIImpactModel
from src.utils.exceptions import ConfigurationError, ScenarioError, ValidationError


@dataclass
class ReproductionMetadata:
    """Container for reproduction metadata extracted from reports"""
    command_used: str
    analysis_type: str
    scenario_names: List[str]
    generation_date: str
    scenario_configs: Dict[str, Any]
    resolved_parameters: Dict[str, Any]
    original_results: Dict[str, Any]
    report_checksum: str


@dataclass  
class ReproductionResult:
    """Container for reproduction validation results"""
    success: bool
    confidence_score: float
    original_results: Dict[str, Any]
    reproduced_results: Dict[str, Any]
    differences: Dict[str, Any]
    validation_details: Dict[str, str]
    reproduction_metadata: ReproductionMetadata


class MetadataExtractor:
    """Extracts reproduction metadata from markdown reports"""
    
    def __init__(self):
        self.yaml_pattern = r'```yaml\n(.*?)\n```'
        self.command_pattern = r'```bash\n(.*?)\n```'
        
    def extract_from_report(self, report_path: str) -> ReproductionMetadata:
        """Extract all reproduction metadata from a markdown report"""
        
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate checksum for validation
        report_checksum = hashlib.md5(content.encode()).hexdigest()
        
        # Extract basic metadata
        analysis_type = self._extract_analysis_type(content)
        scenario_names = self._extract_scenario_names(content)
        generation_date = self._extract_generation_date(content)
        command_used = self._extract_command_used(content)
        
        # Extract YAML configurations
        scenario_configs = self._extract_scenario_configs(content)
        resolved_parameters = self._extract_resolved_parameters(content)
        
        # Extract original results for validation
        original_results = self._extract_original_results(content)
        
        return ReproductionMetadata(
            command_used=command_used,
            analysis_type=analysis_type,
            scenario_names=scenario_names,
            generation_date=generation_date,
            scenario_configs=scenario_configs,
            resolved_parameters=resolved_parameters,
            original_results=original_results,
            report_checksum=report_checksum
        )
    
    def _extract_analysis_type(self, content: str) -> str:
        """Extract analysis type from report header"""
        match = re.search(r'\*\*Analysis Type:\*\* (.*?)(?:\n|\s\s)', content)
        return match.group(1).strip() if match else "Unknown"
    
    def _extract_scenario_names(self, content: str) -> List[str]:
        """Extract scenario names from report header"""
        match = re.search(r'\*\*Scenarios:\*\* (.*?)(?:\n|\s\s)', content)
        if match:
            scenarios_text = match.group(1).strip()
            return [s.strip() for s in scenarios_text.split(',')]
        return []
    
    def _extract_generation_date(self, content: str) -> str:
        """Extract generation date from report"""
        match = re.search(r'\*\*Generated:\*\* (.*?)(?:\n|\s\s)', content)
        return match.group(1).strip() if match else ""
    
    def _extract_command_used(self, content: str) -> str:
        """Extract the command used to generate the report"""
        # Look for command in reproducibility section
        repro_section = re.search(r'### Reproducibility(.*?)(?=###|\Z)', content, re.DOTALL)
        if repro_section:
            command_match = re.search(self.command_pattern, repro_section.group(1), re.DOTALL)
            if command_match:
                return command_match.group(1).strip()
        return ""
    
    def _extract_scenario_configs(self, content: str) -> Dict[str, Any]:
        """Extract scenario configurations from the report"""
        configs = {}
        
        # Find the scenario configuration section
        config_section = re.search(r'Complete scenario configuration used:(.*?)(?=\*\*Resolved parameter|\Z)', 
                                 content, re.DOTALL)
        
        if config_section:
            # Look for scenario name patterns like **scenario_name:**
            scenario_pattern = r'\*\*(.*?):\*\*\s*```yaml\n(.*?)\n```'
            scenario_matches = re.findall(scenario_pattern, config_section.group(1), re.DOTALL)
            
            for scenario_name, yaml_content in scenario_matches:
                # Clean up scenario name - remove markdown formatting and whitespace
                clean_name = scenario_name.strip().lstrip('*').strip()
                try:
                    parsed_yaml = yaml.safe_load(yaml_content)
                    if isinstance(parsed_yaml, dict):
                        configs[clean_name] = parsed_yaml
                except yaml.YAMLError:
                    continue
            
            # Fallback: try to parse all YAML blocks and infer structure
            if not configs:
                yaml_blocks = re.findall(self.yaml_pattern, config_section.group(1), re.DOTALL)
                for yaml_block in yaml_blocks:
                    try:
                        parsed_yaml = yaml.safe_load(yaml_block)
                        if isinstance(parsed_yaml, dict):
                            # If this looks like a scenario config (has baseline, adoption, etc.)
                            if any(key in parsed_yaml for key in ['baseline', 'adoption', 'impact', 'costs']):
                                # Try to infer scenario name from context or use default
                                scenario_name = parsed_yaml.get('name', 'reproduced_scenario').lower().replace(' ', '_')
                                configs[scenario_name] = parsed_yaml
                    except yaml.YAMLError:
                        continue
        
        return configs
    
    def _extract_resolved_parameters(self, content: str) -> Dict[str, Any]:
        """Extract resolved parameter values from the report"""
        # Find the resolved parameters section
        params_section = re.search(r'Resolved parameter values used in calculations:(.*?)(?=\*\*Note:|\Z)', 
                                 content, re.DOTALL)
        
        if params_section:
            yaml_blocks = re.findall(self.yaml_pattern, params_section.group(1), re.DOTALL)
            
            for yaml_block in yaml_blocks:
                try:
                    return yaml.safe_load(yaml_block)
                except yaml.YAMLError:
                    continue
        
        return {}
    
    def _extract_original_results(self, content: str) -> Dict[str, Any]:
        """Extract key results from the report for validation"""
        results = {}
        
        # Extract financial metrics
        npv_match = re.search(r'\*\*Net Present Value \(NPV\)\*\* \| \$([0-9,]+)', content)
        if npv_match:
            results['npv'] = float(npv_match.group(1).replace(',', ''))
        
        roi_match = re.search(r'\*\*Return on Investment \(ROI\)\*\* \| ([0-9.]+)%', content)
        if roi_match:
            results['roi_percent'] = float(roi_match.group(1))
        
        breakeven_match = re.search(r'\*\*Breakeven Point\*\* \| Month ([0-9]+)', content)
        if breakeven_match:
            results['breakeven_month'] = int(breakeven_match.group(1))
        
        adoption_match = re.search(r'\*\*Peak Adoption Rate\*\* \| ([0-9.]+)%', content)
        if adoption_match:
            results['peak_adoption'] = float(adoption_match.group(1)) / 100
        
        # Extract cost and value totals
        total_cost_match = re.search(r'\*\*Total Investment \(3 years\)\*\* \| \$([0-9,]+)', content)
        if total_cost_match:
            results['total_cost_3y'] = float(total_cost_match.group(1).replace(',', ''))
        
        total_value_match = re.search(r'\*\*Total Value Created \(3 years\)\*\* \| \$([0-9,]+)', content)
        if total_value_match:
            results['total_value_3y'] = float(total_value_match.group(1).replace(',', ''))
        
        return results


class ScenarioBuilder:
    """Builds temporary scenario files from extracted metadata"""
    
    def __init__(self):
        self.temp_dir = None
        self.temp_files = []
    
    def create_temporary_scenario_file(self, metadata: ReproductionMetadata) -> str:
        """Create a temporary scenario file from extracted metadata"""
        
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix='ai_impact_reproduction_')
        
        # Create temporary scenario file
        temp_scenario_file = os.path.join(self.temp_dir, 'reproduction_scenarios.yaml')
        
        # Write scenario configurations
        with open(temp_scenario_file, 'w') as f:
            yaml.dump(metadata.scenario_configs, f, default_flow_style=False, indent=2)
        
        self.temp_files.append(temp_scenario_file)
        return temp_scenario_file
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
        
        self.temp_files = []
        self.temp_dir = None


class ReproductionEngine:
    """Main engine for reproducing analysis results"""
    
    def __init__(self):
        self.extractor = MetadataExtractor()
        self.builder = ScenarioBuilder()
        
    def reproduce_from_report(self, report_path: str, 
                            tolerance: float = 0.01) -> ReproductionResult:
        """Reproduce analysis results from a markdown report"""
        
        try:
            # Extract metadata
            metadata = self.extractor.extract_from_report(report_path)
            
            # Validate we have required information
            if not metadata.scenario_names:
                raise ValidationError(
                    f"No scenario names found in report: {report_path}",
                    "reproduction_validation",
                    context="Report must contain scenario information for reproduction"
                )
            
            # Create temporary scenario file
            temp_scenario_file = self.builder.create_temporary_scenario_file(metadata)
            
            # Run reproduction
            reproduced_results = self._run_reproduction(metadata, temp_scenario_file)
            
            # Validate results
            validation_result = self._validate_results(
                metadata.original_results, 
                reproduced_results, 
                tolerance
            )
            
            return ReproductionResult(
                success=validation_result['success'],
                confidence_score=validation_result['confidence_score'],
                original_results=metadata.original_results,
                reproduced_results=reproduced_results,
                differences=validation_result['differences'],
                validation_details=validation_result['details'],
                reproduction_metadata=metadata
            )
            
        except Exception as e:
            # Return failed result with error information
            return ReproductionResult(
                success=False,
                confidence_score=0.0,
                original_results={},
                reproduced_results={},
                differences={'error': str(e)},
                validation_details={'error': f"Reproduction failed: {str(e)}"},
                reproduction_metadata=metadata if 'metadata' in locals() else None
            )
        
        finally:
            # Always cleanup temporary files
            self.builder.cleanup()
    
    def _run_reproduction(self, metadata: ReproductionMetadata, 
                         scenario_file: str) -> Dict[str, Any]:
        """Run the reproduction analysis"""
        
        # Initialize model with temporary scenario file
        model = AIImpactModel(scenario_file)
        
        # Run scenarios based on analysis type
        results = {}
        
        if metadata.analysis_type == "Single Scenario":
            scenario_name = metadata.scenario_names[0]
            result = model.run_scenario(scenario_name)
            results = self._extract_key_metrics(result)
            
        elif metadata.analysis_type == "Multiple Scenarios":
            for scenario_name in metadata.scenario_names:
                result = model.run_scenario(scenario_name)
                results[scenario_name] = self._extract_key_metrics(result)
                
        elif metadata.analysis_type == "Scenario Comparison":
            for scenario_name in metadata.scenario_names:
                result = model.run_scenario(scenario_name)
                results[scenario_name] = self._extract_key_metrics(result)
        
        return results
    
    def _extract_key_metrics(self, scenario_results: Dict) -> Dict[str, Any]:
        """Extract key metrics from scenario results for comparison"""
        
        # Convert numpy values to Python types for comparison
        def convert_numpy(value):
            if hasattr(value, 'item'):
                return value.item()
            return value
        
        return {
            'npv': convert_numpy(scenario_results.get('npv', 0)),
            'roi_percent': convert_numpy(scenario_results.get('roi_percent', 0)),
            'breakeven_month': scenario_results.get('breakeven_month'),
            'peak_adoption': convert_numpy(scenario_results.get('peak_adoption', 0)),
            'total_cost_3y': convert_numpy(scenario_results.get('total_cost_3y', 0)),
            'total_value_3y': convert_numpy(scenario_results.get('total_value_3y', 0)),
            'annual_cost_per_dev': convert_numpy(scenario_results.get('annual_cost_per_dev', 0)),
            'annual_value_per_dev': convert_numpy(scenario_results.get('annual_value_per_dev', 0))
        }
    
    def _validate_results(self, original: Dict[str, Any], reproduced: Dict[str, Any], 
                         tolerance: float) -> Dict[str, Any]:
        """Validate reproduced results against originals"""
        
        validation_details = {}
        differences = {}
        total_metrics = 0
        matching_metrics = 0
        
        # For single scenario results
        if not any(isinstance(v, dict) for v in original.values()):
            original = {'single_scenario': original}
            reproduced = {'single_scenario': reproduced}
        
        for scenario_name in original.keys():
            if scenario_name not in reproduced:
                differences[scenario_name] = f"Missing in reproduced results"
                validation_details[scenario_name] = "Scenario not reproduced"
                continue
            
            orig_scenario = original[scenario_name]
            repro_scenario = reproduced[scenario_name]
            scenario_diffs = {}
            
            for metric, orig_value in orig_scenario.items():
                total_metrics += 1
                
                if metric not in repro_scenario:
                    scenario_diffs[metric] = f"Missing in reproduction"
                    continue
                
                repro_value = repro_scenario[metric]
                
                # Handle None values
                if orig_value is None and repro_value is None:
                    matching_metrics += 1
                    continue
                elif orig_value is None or repro_value is None:
                    scenario_diffs[metric] = f"Original: {orig_value}, Reproduced: {repro_value}"
                    continue
                
                # Numerical comparison with tolerance
                if isinstance(orig_value, (int, float)) and isinstance(repro_value, (int, float)):
                    if orig_value == 0:
                        # Handle zero values
                        if abs(repro_value) <= tolerance:
                            matching_metrics += 1
                        else:
                            scenario_diffs[metric] = f"Original: {orig_value}, Reproduced: {repro_value}"
                    else:
                        # Percentage difference
                        pct_diff = abs((repro_value - orig_value) / orig_value)
                        if pct_diff <= tolerance:
                            matching_metrics += 1
                        else:
                            scenario_diffs[metric] = f"Original: {orig_value}, Reproduced: {repro_value} ({pct_diff:.3%} diff)"
                else:
                    # Exact comparison for non-numerical values
                    if orig_value == repro_value:
                        matching_metrics += 1
                    else:
                        scenario_diffs[metric] = f"Original: {orig_value}, Reproduced: {repro_value}"
            
            if scenario_diffs:
                differences[scenario_name] = scenario_diffs
                validation_details[scenario_name] = f"{len(scenario_diffs)} metrics differ"
            else:
                validation_details[scenario_name] = "All metrics match"
        
        # Calculate confidence score
        confidence_score = matching_metrics / total_metrics if total_metrics > 0 else 0.0
        success = confidence_score >= 0.95  # 95% of metrics must match
        
        return {
            'success': success,
            'confidence_score': confidence_score,
            'differences': differences,
            'details': validation_details,
            'total_metrics': total_metrics,
            'matching_metrics': matching_metrics
        }