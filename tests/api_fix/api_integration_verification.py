#!/usr/bin/env python3
"""
API Integration Verification Test Suite

This script performs a comprehensive verification of the API consolidation work, including:
1. Testing the utils module functions directly
2. Testing the API endpoints that use the consolidated utils
3. Verifying error handling and edge cases

Run this after major changes to ensure the full API stack works correctly.
"""

import os
import sys
import logging
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List

# Add the project directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import test modules
from tests.api_fix.utils_consolidation_test import APIUtilsTest
from tests.api.test_goal_probability_api import GoalProbabilityAPITest
from tests.api.test_visualization_integration import VisualizationDataAPITest
from tests.api.test_goal_api_v2 import GoalAPIV2Test

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_imports():
    """Verify that all required modules can be imported."""
    logger.info("Testing imports...")
    try:
        # Import utils module
        from api.v2.utils import (
            monitor_performance, check_cache, cache_response,
            rate_limit_middleware, check_admin_access, create_error_response
        )
        logger.info("✅ Utils module imported successfully")
        
        # Import API modules
        import api.v2.goal_probability_api
        logger.info("✅ Goal probability API imported successfully")
        
        import api.v2.visualization_data
        logger.info("✅ Visualization data API imported successfully")
        
        # Import Monte Carlo modules
        from models.monte_carlo.simulation import (
            validate_simulation_parameters, 
            prepare_simulation_data,
            safely_get_simulation_data
        )
        logger.info("✅ Monte Carlo simulation module imported successfully")
        
        from models.monte_carlo.cache import (
            _cache, 
            get_cache_stats, 
            invalidate_cache
        )
        logger.info("✅ Monte Carlo cache module imported successfully")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during imports: {e}")
        return False

def check_reference_integrity():
    """Verify that the utils module is properly referenced by API modules."""
    logger.info("Testing reference integrity...")
    try:
        # Check if goal_probability_api uses utils
        with open(os.path.join(os.getcwd(), 'api/v2/goal_probability_api.py'), 'r') as f:
            goal_api_content = f.read()
            
        # Check if visualization_data uses utils
        with open(os.path.join(os.getcwd(), 'api/v2/visualization_data.py'), 'r') as f:
            viz_api_content = f.read()
            
        # Check for import statement
        if 'from api.v2.utils import' in goal_api_content:
            logger.info("✅ Goal probability API imports from utils")
        else:
            logger.warning("❌ Goal probability API does not import from utils")
            return False
            
        if 'from api.v2.utils import' in viz_api_content:
            logger.info("✅ Visualization data API imports from utils")
        else:
            logger.warning("❌ Visualization data API does not import from utils")
            return False
            
        # Check for function usage
        for func_name in ['monitor_performance', 'check_cache', 'cache_response', 'check_admin_access']:
            if func_name in goal_api_content:
                logger.info(f"✅ Goal probability API uses {func_name}")
            else:
                logger.warning(f"❌ Goal probability API does not use {func_name}")
                
            if func_name in viz_api_content:
                logger.info(f"✅ Visualization data API uses {func_name}")
            else:
                logger.warning(f"❌ Visualization data API does not use {func_name}")
                
        return True
    except Exception as e:
        logger.error(f"❌ Error checking reference integrity: {e}")
        return False

def run_utils_tests():
    """Run only the utils module tests."""
    logger.info("Running utils module tests...")
    import unittest
    
    # Create test suite with just utils tests
    suite = unittest.TestSuite()
    for test_name in [
        'test_01_rate_limiting',
        'test_02_caching',
        'test_03_performance_monitoring',
        'test_04_error_handling',
        'test_05_admin_access',
        'test_06_rate_limit_cleanup'
    ]:
        suite.addTest(APIUtilsTest(test_name))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()

def run_integration_tests():
    """Run key integration tests to verify API functionality."""
    logger.info("Running integration tests...")
    import unittest
    
    # Create test suite with key API tests
    suite = unittest.TestSuite()
    
    # Goal probability API tests
    suite.addTest(GoalProbabilityAPITest('test_01_get_goal_probability'))
    suite.addTest(GoalProbabilityAPITest('test_03_get_goal_adjustments'))
    
    # Visualization API tests
    suite.addTest(VisualizationDataAPITest('test_01_visualization_data_structure'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()

def generate_verification_report(results: Dict[str, bool]) -> str:
    """Generate a comprehensive verification report."""
    report = [
        "# API Consolidation Verification Report",
        f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Summary",
        "\n| Test | Status |",
        "| ---- | ------ |",
    ]
    
    # Add test results to report
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        report.append(f"| {test_name} | {status} |")
    
    # Add overall result
    all_passed = all(results.values())
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    report.append(f"\n## Overall Result: {overall_status}")
    
    # Add recommendations section
    report.append("\n## Recommendations")
    if all_passed:
        report.append("\nThe API consolidation appears to be complete and working correctly. The consolidated utils module is properly integrated with all API endpoints and functions as expected.")
        report.append("\nNext steps:")
        report.append("1. Deploy the consolidated code to production")
        report.append("2. Monitor performance and error rates")
        report.append("3. Apply the same pattern to other API modules")
    else:
        report.append("\nThe API consolidation is incomplete or has issues. Please address the following:")
        if not results.get('imports', True):
            report.append("- Fix import errors in the modules")
        if not results.get('references', True):
            report.append("- Ensure all API modules properly reference the utils module")
        if not results.get('utils_tests', True):
            report.append("- Fix issues with the utils module functions")
        if not results.get('integration_tests', True):
            report.append("- Fix issues with the API endpoints that use the utils module")
    
    return "\n".join(report)

def main():
    """Run the verification tests and generate a report."""
    logger.info("Starting API integration verification...")
    
    # Run all verification tests
    results = {}
    
    # Check imports
    results['imports'] = check_imports()
    
    # Check reference integrity
    results['references'] = check_reference_integrity()
    
    # Run utils tests
    results['utils_tests'] = run_utils_tests()
    
    # Run integration tests
    results['integration_tests'] = run_integration_tests()
    
    # Generate report
    report = generate_verification_report(results)
    
    # Save report to file
    report_path = os.path.join(os.getcwd(), 'reports', 'api_consolidation_verification.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Verification report saved to: {report_path}")
    
    # Print summary
    print("\n" + report)
    
    # Return success or failure
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())