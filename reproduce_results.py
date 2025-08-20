#!/usr/bin/env python3
"""
Result Reproduction CLI Tool
Reproduces analysis results from markdown reports for validation and verification.

Usage:
    python reproduce_results.py path/to/report.md
    python reproduce_results.py --validate reports/*.md
    python reproduce_results.py --tolerance 0.01 reports/
    python reproduce_results.py --summary reports/
"""

import os
import sys
import argparse
import glob
from typing import List, Dict, Optional
from datetime import datetime
import json

from src.reproducibility.reproduction_engine import ReproductionEngine, ReproductionResult
from src.utils.colors import *
from src.utils.exceptions import ConfigurationError, ValidationError


class ReproductionReporter:
    """Generates detailed reports for reproduction results"""
    
    def __init__(self):
        self.total_reports = 0
        self.successful_reproductions = 0
        self.failed_reproductions = 0
        self.results = []
    
    def add_result(self, result: ReproductionResult, report_path: str):
        """Add a reproduction result to the summary"""
        self.total_reports += 1
        
        if result.success:
            self.successful_reproductions += 1
        else:
            self.failed_reproductions += 1
        
        self.results.append({
            'report_path': report_path,
            'result': result
        })
    
    def print_detailed_result(self, result: ReproductionResult, report_path: str):
        """Print detailed reproduction result"""
        
        print(subsection_divider(f"REPRODUCTION RESULT: {os.path.basename(report_path)}"))
        
        # Overall status
        status_color = success if result.success else error
        status_text = "✅ SUCCESS" if result.success else "❌ FAILED"
        print(f"{metric('Status'):<25} {status_color(status_text)}")
        print(f"{metric('Confidence Score'):<25} {percentage(f'{result.confidence_score:.1%}')}")
        
        if result.reproduction_metadata:
            metadata = result.reproduction_metadata
            print(f"{metric('Analysis Type'):<25} {info(metadata.analysis_type)}")
            print(f"{metric('Scenarios'):<25} {info(', '.join(metadata.scenario_names))}")
            print(f"{metric('Original Date'):<25} {info(metadata.generation_date)}")
            print(f"{metric('Command Used'):<25} {dim_text(metadata.command_used)}")
        
        print()
        
        # Detailed differences if any
        if result.differences and result.success:
            print(header("MINOR DIFFERENCES (within tolerance)"))
            self._print_differences(result.differences, warning)
            print()
        elif result.differences and not result.success:
            print(header("SIGNIFICANT DIFFERENCES"))
            self._print_differences(result.differences, error)
            print()
        
        # Validation details
        if result.validation_details:
            print(header("VALIDATION DETAILS"))
            for scenario, detail in result.validation_details.items():
                detail_color = success if "match" in detail.lower() else warning
                print(f"{metric(scenario):<25} {detail_color(detail)}")
            print()
    
    def _print_differences(self, differences: Dict, color_func):
        """Print formatted differences"""
        for scenario, diffs in differences.items():
            if isinstance(diffs, dict):
                print(f"  {info(scenario)}:")
                for metric, diff in diffs.items():
                    print(f"    {color_func('•')} {metric}: {diff}")
            else:
                print(f"  {info(scenario)}: {color_func(diffs)}")
    
    def print_summary(self):
        """Print overall summary of all reproductions"""
        
        print(section_divider("REPRODUCTION SUMMARY", 80))
        
        # Overall statistics
        success_rate = self.successful_reproductions / self.total_reports if self.total_reports > 0 else 0
        print(f"{metric('Total Reports Processed'):<30} {info(str(self.total_reports))}")
        print(f"{metric('Successful Reproductions'):<30} {success(str(self.successful_reproductions))}")
        print(f"{metric('Failed Reproductions'):<30} {error(str(self.failed_reproductions))}")
        print(f"{metric('Success Rate'):<30} {percentage(f'{success_rate:.1%}')}")
        print()
        
        # Average confidence score
        if self.results:
            avg_confidence = sum(r['result'].confidence_score for r in self.results) / len(self.results)
            print(f"{metric('Average Confidence Score'):<30} {percentage(f'{avg_confidence:.1%}')}")
            print()
        
        # Failed reports details
        failed_results = [r for r in self.results if not r['result'].success]
        if failed_results:
            print(header("FAILED REPRODUCTIONS"))
            for result_info in failed_results:
                report_name = os.path.basename(result_info['report_path'])
                confidence = result_info['result'].confidence_score
                print(f"  {error('•')} {report_name} - Confidence: {percentage(f'{confidence:.1%}')}")
            print()
        
        # Recommendations
        self._print_recommendations(success_rate, failed_results)
    
    def _print_recommendations(self, success_rate: float, failed_results: List):
        """Print recommendations based on reproduction results"""
        
        print(header("RECOMMENDATIONS"))
        
        if success_rate >= 0.95:
            print(f"  {success('✅')} Excellent reproduction rate - analysis pipeline is highly reliable")
        elif success_rate >= 0.80:
            print(f"  {warning('⚠️')} Good reproduction rate - investigate failed cases for improvements")
        else:
            print(f"  {error('🚨')} Low reproduction rate - significant investigation needed")
        
        if failed_results:
            print(f"  {info('💡')} Review failed reproductions for:")
            print(f"    • Changes in scenario definitions")
            print(f"    • Dependency version differences") 
            print(f"    • Random seed or numerical precision issues")
            print(f"    • Missing or incomplete metadata")
        
        print(f"  {info('📋')} Consider:")
        print(f"    • Increasing tolerance for minor numerical differences")
        print(f"    • Updating old reports if model improvements are validated")
        print(f"    • Adding version control integration for better provenance")


class ReproductionCLI:
    """Command-line interface for result reproduction"""
    
    def __init__(self):
        self.engine = ReproductionEngine()
        self.reporter = ReproductionReporter()
    
    def reproduce_single_report(self, report_path: str, tolerance: float = 0.01, 
                              verbose: bool = True) -> ReproductionResult:
        """Reproduce results from a single report"""
        
        if verbose:
            print(info(f"🔄 Reproducing results from: {os.path.basename(report_path)}"))
        
        if not os.path.exists(report_path):
            raise FileNotFoundError(f"Report file not found: {report_path}")
        
        result = self.engine.reproduce_from_report(report_path, tolerance)
        
        if verbose:
            status_text = "✅ Success" if result.success else "❌ Failed"
            print(f"  {status_text} - Confidence: {result.confidence_score:.1%}")
        
        return result
    
    def reproduce_multiple_reports(self, report_paths: List[str], tolerance: float = 0.01,
                                 verbose: bool = True, detailed: bool = False) -> List[ReproductionResult]:
        """Reproduce results from multiple reports"""
        
        print(info(f"🔄 Processing {len(report_paths)} reports..."))
        
        results = []
        
        for i, report_path in enumerate(report_paths, 1):
            if verbose:
                print(f"  {dim_text(f'[{i}/{len(report_paths)}]')} {os.path.basename(report_path)}")
            
            try:
                result = self.reproduce_single_report(report_path, tolerance, verbose=False)
                results.append(result)
                self.reporter.add_result(result, report_path)
                
                if detailed:
                    self.reporter.print_detailed_result(result, report_path)
                
                if verbose:
                    status_text = "✅" if result.success else "❌"
                    confidence_text = f"{result.confidence_score:.1%}"
                    print(f"    {status_text} Confidence: {confidence_text}")
                
            except Exception as e:
                print(f"    {error('❌')} Error: {str(e)}")
                # Create failed result
                failed_result = ReproductionResult(
                    success=False,
                    confidence_score=0.0,
                    original_results={},
                    reproduced_results={},
                    differences={'error': str(e)},
                    validation_details={'error': f"Processing failed: {str(e)}"},
                    reproduction_metadata=None
                )
                results.append(failed_result)
                self.reporter.add_result(failed_result, report_path)
        
        return results
    
    def validate_reports(self, report_paths: List[str], tolerance: float = 0.01) -> bool:
        """Validate multiple reports and return overall success"""
        
        results = self.reproduce_multiple_reports(report_paths, tolerance, verbose=True)
        
        print()
        self.reporter.print_summary()
        
        # Return True if all reports passed validation
        return all(result.success for result in results)


def find_report_files(paths: List[str]) -> List[str]:
    """Find all markdown report files from given paths"""
    
    report_files = []
    
    for path in paths:
        if os.path.isfile(path):
            if path.endswith('.md'):
                report_files.append(path)
        elif os.path.isdir(path):
            # Find all .md files in directory
            pattern = os.path.join(path, "*.md")
            report_files.extend(glob.glob(pattern))
    
    return sorted(report_files)


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Reproduce AI impact analysis results from markdown reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python reproduce_results.py report.md
    python reproduce_results.py --tolerance 0.05 reports/
    python reproduce_results.py --validate --detailed reports/
    python reproduce_results.py --summary outputs/reports/
        """
    )
    
    parser.add_argument('paths', nargs='+',
                       help='Report file(s) or directory containing reports')
    parser.add_argument('--tolerance', '-t', type=float, default=0.01,
                       help='Tolerance for numerical differences (default: 0.01 = 1%%)')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validation mode - return exit code based on success')
    parser.add_argument('--detailed', '-d', action='store_true',
                       help='Show detailed differences for each report')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Show only summary statistics')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimize output (only errors and final results)')
    
    args = parser.parse_args()
    
    try:
        # Find all report files
        report_files = find_report_files(args.paths)
        
        if not report_files:
            print(error("❌ No markdown report files found in specified paths"))
            print(info("💡 Make sure you're pointing to .md files or directories containing them"))
            return 1
        
        if not args.quiet:
            print(header(f"AI Impact Analysis - Result Reproduction"))
            print(info(f"Found {len(report_files)} report file(s)"))
            print()
        
        # Initialize CLI
        cli = ReproductionCLI()
        
        # Process based on mode
        if len(report_files) == 1 and not args.summary:
            # Single report - show detailed results
            result = cli.reproduce_single_report(
                report_files[0], 
                tolerance=args.tolerance,
                verbose=not args.quiet
            )
            
            if not args.quiet:
                cli.reporter.add_result(result, report_files[0])
                cli.reporter.print_detailed_result(result, report_files[0])
            
            # Return appropriate exit code
            return 0 if result.success else 1
            
        else:
            # Multiple reports or summary mode
            if args.validate:
                success = cli.validate_reports(report_files, args.tolerance)
                return 0 if success else 1
            else:
                cli.reproduce_multiple_reports(
                    report_files, 
                    tolerance=args.tolerance,
                    verbose=not args.quiet,
                    detailed=args.detailed
                )
                
                if not args.quiet:
                    cli.reporter.print_summary()
                
                return 0
        
    except KeyboardInterrupt:
        print(warning("\n⏹️  Reproduction interrupted by user"))
        return 130
        
    except FileNotFoundError as e:
        print(error(f"❌ File not found: {e}"))
        print(warning("🔧 Check file paths and ensure reports exist"))
        return 2
        
    except PermissionError as e:
        print(error(f"❌ Permission denied: {e}"))
        print(warning("🔧 Check file permissions and access rights"))
        return 13
        
    except (ConfigurationError, ValidationError) as e:
        print(error(f"❌ {e}"))
        return 1
        
    except Exception as e:
        print(error(f"❌ Unexpected error: {e}"))
        print(warning("🔧 This may be a bug - please report with full error details"))
        return 1


if __name__ == "__main__":
    sys.exit(main())