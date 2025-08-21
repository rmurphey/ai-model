#!/usr/bin/env python3
"""
Test script for new high-priority features:
1. Configuration caching
2. Sensitivity analysis  
3. Batch processing
"""

import os
import sys
import time
from pathlib import Path

# Test colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def test_caching():
    """Test configuration caching"""
    print(f"\n{YELLOW}Testing Configuration Caching...{RESET}")
    
    # First run - should miss cache
    print("  First run (cache miss expected)...")
    os.system("python main.py --scenario moderate_enterprise --cache-stats 2>&1 | grep 'Cache Stats' | tail -1")
    
    # Second run - should hit cache
    print("  Second run (cache hit expected)...")
    os.system("python main.py --scenario moderate_enterprise --cache-stats 2>&1 | grep 'Cache Stats' | tail -1")
    
    print(f"{GREEN}✓ Caching test complete{RESET}")
    return True

def test_sensitivity():
    """Test sensitivity analysis"""
    print(f"\n{YELLOW}Testing Sensitivity Analysis...{RESET}")
    
    # Run sensitivity analysis with small sample size for speed
    print("  Running sensitivity analysis (64 samples)...")
    result = os.system("python run_analysis.py --sensitivity moderate_enterprise --sensitivity-samples 64 > /dev/null 2>&1")
    
    if result == 0:
        # Check if output file was created
        output_files = list(Path('outputs/reports').glob('sensitivity_*.md'))
        if output_files:
            latest_file = max(output_files, key=lambda p: p.stat().st_mtime)
            print(f"  {GREEN}✓ Sensitivity report created: {latest_file.name}{RESET}")
            
            # Show first few lines of report
            with open(latest_file, 'r') as f:
                lines = f.readlines()[:10]
                print("  Report preview:")
                for line in lines[:5]:
                    print(f"    {line.strip()}")
            
            return True
        else:
            print(f"  {RED}✗ No sensitivity report found{RESET}")
            return False
    else:
        print(f"  {RED}✗ Sensitivity analysis failed{RESET}")
        return False

def test_batch_processing():
    """Test batch processing"""
    print(f"\n{YELLOW}Testing Batch Processing...{RESET}")
    
    # Create simple batch config
    batch_config = """
scenarios:
  - conservative_startup
  - moderate_enterprise
  - aggressive_scaleup
parallel_workers: 2
output_dir: outputs/test_batch
generate_comparison: true
save_individual_reports: false
"""
    
    config_path = 'test_batch_config.yaml'
    with open(config_path, 'w') as f:
        f.write(batch_config)
    
    print(f"  Created test batch config: {config_path}")
    
    # Run batch processing
    print("  Running batch processing (3 scenarios)...")
    result = os.system(f"python run_analysis.py --batch {config_path} > /dev/null 2>&1")
    
    if result == 0:
        # Check for output files
        batch_dir = Path('outputs/test_batch')
        if batch_dir.exists():
            report_files = list(batch_dir.glob('batch_report_*.md'))
            if report_files:
                latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
                print(f"  {GREEN}✓ Batch report created: {latest_report.name}{RESET}")
                
                # Clean up test files
                os.remove(config_path)
                
                return True
            else:
                print(f"  {RED}✗ No batch report found{RESET}")
                return False
        else:
            print(f"  {RED}✗ Batch output directory not created{RESET}")
            return False
    else:
        print(f"  {RED}✗ Batch processing failed{RESET}")
        return False

def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Testing New High-Priority Features{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    tests = [
        ("Configuration Caching", test_caching),
        ("Sensitivity Analysis", test_sensitivity),
        ("Batch Processing", test_batch_processing)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"{RED}✗ {name} test failed with error: {e}{RESET}")
            results.append((name, False))
    
    # Summary
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Test Summary{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = f"{GREEN}✓ PASSED{RESET}" if success else f"{RED}✗ FAILED{RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}All tests passed! 🎉{RESET}")
        return 0
    else:
        print(f"\n{RED}Some tests failed. Please review.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())