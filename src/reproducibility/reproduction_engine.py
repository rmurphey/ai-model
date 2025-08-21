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
from src.config.version import ModelVersion, get_current_version, get_compatibility_info
from src.versioning.version_adapter import adapt_scenario_config


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
    model_version: Optional[ModelVersion] = None
    tool_version: Optional[str] = None


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
    version_compatibility: Optional[Dict[str, Any]] = None


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
        
        # Extract version information
        model_version, tool_version = self._extract_version_info(content)
        
        return ReproductionMetadata(
            command_used=command_used,
            analysis_type=analysis_type,
            scenario_names=scenario_names,
            generation_date=generation_date,
            scenario_configs=scenario_configs,
            resolved_parameters=resolved_parameters,
            original_results=original_results,
            report_checksum=report_checksum,
            model_version=model_version,
            tool_version=tool_version
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
    
    def _extract_version_info(self, content: str) -> Tuple[Optional[ModelVersion], Optional[str]]:
        """Extract model version and tool version from the report"""
        model_version = None
        tool_version = None
        
        # Extract Analysis Tool Version from header
        tool_match = re.search(r'\*\*Analysis Tool Version:\*\* v?([^\s]+)', content)
        if tool_match:
            tool_version = tool_match.group(1)
            try:
                model_version = ModelVersion.from_string(tool_version)
            except ValueError:
                # If tool version doesn't parse as semantic version, try analysis engine version
                pass
        
        # Fallback: Extract from Analysis engine line in footer
        if model_version is None:
            engine_match = re.search(r'Analysis engine: AI Impact Model v?([\d.]+)', content)
            if engine_match:
                try:
                    model_version = ModelVersion.from_string(engine_match.group(1))
                except ValueError:
                    pass
        
        return model_version, tool_version


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
            
            # Adapt scenario configuration if needed
            adapted_configs = metadata.scenario_configs
            current_version = get_current_version()
            
            if metadata.model_version and metadata.model_version != current_version:
                # Adapt configurations for version compatibility
                adaptation_warnings = []
                for scenario_name, config in metadata.scenario_configs.items():
                    adaptation_result = adapt_scenario_config(
                        config, metadata.model_version, current_version
                    )
                    if adaptation_result.success:
                        adapted_configs[scenario_name] = adaptation_result.adapted_config
                        adaptation_warnings.extend(adaptation_result.warnings)
                    else:
                        raise ValidationError(
                            "scenario_adaptation",
                            f"'{scenario_name}' from {metadata.model_version} to {current_version}",
                            "Compatible version transition",
                            suggestion=f"Check version adapter compatibility. Errors: {', '.join(adaptation_result.errors)}"
                        )
            
            # Create temporary scenario file with adapted configs
            adapted_metadata = metadata
            adapted_metadata.scenario_configs = adapted_configs
            temp_scenario_file = self.builder.create_temporary_scenario_file(adapted_metadata)
            
            # Run reproduction
            reproduced_results = self._run_reproduction(adapted_metadata, temp_scenario_file)
            
            # Check version compatibility
            version_compatibility = None
            if metadata.model_version:
                version_compatibility = get_compatibility_info(metadata.model_version, current_version)
                
                # Adjust tolerance based on version compatibility
                if version_compatibility['compatibility_level'] == 'major':
                    tolerance = max(tolerance, 0.02)  # Relax tolerance for minor version differences
                elif version_compatibility['compatibility_level'] == 'minor':
                    tolerance = max(tolerance, 0.05)  # Further relax for major version differences
            
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
                reproduction_metadata=metadata,
                version_compatibility=version_compatibility
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
                reproduction_metadata=metadata if 'metadata' in locals() else None,
                version_compatibility=None
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