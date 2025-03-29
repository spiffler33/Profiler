#!/usr/bin/env python3
"""
Test suite for the parameter usage analyzer utility.

This module tests the functionality of the analyze_parameter_usage.py script,
verifying that it correctly identifies and reports parameter usage patterns.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from io import StringIO

# Import modules to test
from utils.analyze_parameter_usage import (
    generate_usage_report,
    create_html_report,
    run_application_scenario,
    run_all_tests
)

from models.financial_parameters import (
    get_parameters, ParameterCompatibilityAdapter
)


class TestParameterUsageAnalyzer(unittest.TestCase):
    """Tests for the parameter usage analyzer utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample access report for testing
        self.sample_access_report = {
            "inflation_rate": 10,
            "equity_return": 8,
            "debt_return": 6,
            "gold_return": 4,
            "life_expectancy": 2
        }
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_report_path = os.path.join(self.temp_dir, "test_report.html")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if os.path.exists(self.test_report_path):
            os.remove(self.test_report_path)
        os.rmdir(self.temp_dir)
    
    def test_generate_usage_report(self):
        """Test that generate_usage_report produces correct structure."""
        # Generate report from sample data
        report = generate_usage_report(self.sample_access_report)
        
        # Check report structure
        self.assertIn("timestamp", report)
        self.assertIn("total_legacy_keys_used", report)
        self.assertIn("total_access_count", report)
        self.assertIn("most_used_keys", report)
        self.assertIn("key_details", report)
        self.assertIn("recommendations", report)
        
        # Check report values
        self.assertEqual(report["total_legacy_keys_used"], 5)
        self.assertEqual(report["total_access_count"], 30)  # Sum of all access counts
        
        # Check most used keys
        self.assertEqual(len(report["most_used_keys"]), 5)
        # Keys should be sorted by usage count
        self.assertEqual(report["most_used_keys"][0]["key"], "inflation_rate")
        self.assertEqual(report["most_used_keys"][0]["count"], 10)
        
        # Check key details
        self.assertEqual(len(report["key_details"]), 5)
        
        # Check recommendations
        self.assertTrue(len(report["recommendations"]) > 0)
        
        # Check for specific recommendation about frequently used keys
        found_recommended_key = False
        for recommendation in report["recommendations"]:
            if "most frequently used key" in recommendation:
                found_recommended_key = True
                break
        self.assertTrue(found_recommended_key, "No recommendation about most frequently used key")
    
    def test_create_html_report(self):
        """Test that create_html_report generates valid HTML file."""
        # Generate a report
        report = generate_usage_report(self.sample_access_report)
        
        # Create HTML report
        create_html_report(report, self.test_report_path)
        
        # Check that file was created
        self.assertTrue(os.path.exists(self.test_report_path))
        
        # Read file content
        with open(self.test_report_path, 'r') as f:
            content = f.read()
        
        # Check for key elements in HTML
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("<title>Parameter Usage Report</title>", content)
        self.assertIn("Legacy Keys Used:", content)
        self.assertIn("inflation_rate", content)
        self.assertIn("10</td>", content)  # Count for inflation_rate
        self.assertIn("Recommendations", content)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_application_scenario(self, mock_stdout):
        """Test that run_application_scenario executes without errors."""
        # Skip this test without detailed mocking
        self.skipTest("This function accesses Flask app - requiring more complex mocking")
        
        # This function would normally patch app.test_client and other elements
        # that are referenced in run_application_scenario, but we'll skip for now
    
    @patch('sys.stdout', new_callable=StringIO)
    @patch('subprocess.run')
    def test_run_all_tests_success(self, mock_run, mock_stdout):
        """Test run_all_tests when tests succeed."""
        # Mock successful test run
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Run the function
        run_all_tests()
        
        # Check output contains success message
        self.assertIn("✓ All tests passed", mock_stdout.getvalue())
        
    @patch('sys.stdout', new_callable=StringIO)
    @patch('subprocess.run')
    def test_run_all_tests_failure(self, mock_run, mock_stdout):
        """Test run_all_tests when tests fail."""
        # Mock failed test run
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Test failures"
        mock_run.return_value = mock_process
        
        # Run the function
        run_all_tests()
        
        # Check output contains failure message
        self.assertIn("× Some tests failed", mock_stdout.getvalue())
    
    def test_report_with_no_legacy_keys(self):
        """Test report generation with no legacy keys."""
        # Empty access report
        empty_report = {}
        
        # Generate report
        report = generate_usage_report(empty_report)
        
        # Check report values
        self.assertEqual(report["total_legacy_keys_used"], 0)
        self.assertEqual(report["total_access_count"], 0)
        self.assertEqual(len(report["most_used_keys"]), 0)
        self.assertEqual(len(report["key_details"]), 0)
        
        # Check recommendations
        self.assertEqual(len(report["recommendations"]), 1)
        self.assertIn("No legacy keys detected", report["recommendations"][0])


class TestParameterUsageIntegration(unittest.TestCase):
    """Integration tests for parameter usage analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Get parameters instance
        self.params = get_parameters()
        
        # Clear access log if adapter is being used
        if isinstance(self.params, ParameterCompatibilityAdapter) and hasattr(self.params, '_access_log'):
            self.params._access_log = {}
    
    def test_usage_tracking(self):
        """Test that parameter usage is tracked correctly."""
        # Only run this test if we're using the compatibility adapter
        if not isinstance(self.params, ParameterCompatibilityAdapter):
            self.skipTest("This test requires ParameterCompatibilityAdapter")
        
        # Access some legacy keys
        self.params.get("inflation_rate")
        self.params.get("equity_return")
        self.params.get("inflation_rate")  # Access twice
        
        # Get the access log
        access_log = self.params.get_access_log()
        
        # Verify the log contents
        self.assertIn("inflation_rate", access_log)
        self.assertIn("equity_return", access_log)
        self.assertEqual(access_log["inflation_rate"], 2)
        self.assertEqual(access_log["equity_return"], 1)
    
    def test_generate_report_from_real_usage(self):
        """Test generating a report from real parameter usage."""
        # Only run this test if we're using the compatibility adapter
        if not isinstance(self.params, ParameterCompatibilityAdapter):
            self.skipTest("This test requires ParameterCompatibilityAdapter")
            
        # Access some parameters to populate the log
        self.params.get("inflation_rate")
        self.params.get("equity_return")
        self.params.get("debt_return")
        
        # Get actual access log
        from models.financial_parameters import get_legacy_access_report
        access_log = get_legacy_access_report()
        
        # Generate report from actual usage
        report = generate_usage_report(access_log)
        
        # Basic validation of the report
        self.assertGreaterEqual(report["total_legacy_keys_used"], 3)
        self.assertGreaterEqual(report["total_access_count"], 3)
        
        # Keys we accessed should be in the report
        keys_in_report = [item["key"] for item in report["key_details"]]
        self.assertIn("inflation_rate", keys_in_report)
        self.assertIn("equity_return", keys_in_report)
        self.assertIn("debt_return", keys_in_report)


if __name__ == "__main__":
    unittest.main()