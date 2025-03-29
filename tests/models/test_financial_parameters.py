#!/usr/bin/env python3
"""
Test suite for the Financial Parameters module
"""

import unittest
import json
from datetime import datetime
from models.financial_parameters import (
    get_parameters, ParameterSource, ParameterMetadata, ParameterValue,
    FinancialParameters, ParameterCompatibilityAdapter, get_legacy_access_report,
    LEGACY_ACCESS_ENABLED, LOG_DEPRECATED_ACCESS
)

class TestFinancialParameters(unittest.TestCase):
    """Test cases for FinancialParameters class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Get a fresh parameters instance for each test
        self.params = get_parameters()
    
    def test_get_default_parameters(self):
        """Test that default parameters can be retrieved"""
        # Test that we can get a common parameter
        inflation = self.params.get("inflation.general")
        self.assertIsNotNone(inflation)
        self.assertGreater(inflation, 0)
        
        # Test that we can get a nested parameter
        equity_large_cap = self.params.get("asset_returns.equity.large_cap.value")
        self.assertIsNotNone(equity_large_cap)
        self.assertGreater(equity_large_cap, 0)
    
    def test_get_nonexistent_parameter(self):
        """Test behavior when getting a nonexistent parameter"""
        # Should return None for nonexistent parameter
        value = self.params.get("nonexistent.parameter")
        self.assertIsNone(value)
        
        # Should return default for nonexistent parameter with default
        value = self.params.get("nonexistent.parameter", 42)
        self.assertEqual(value, 42)
    
    def test_get_asset_return(self):
        """Test that asset returns can be retrieved"""
        # Test getting a simple asset return
        equity_return = self.params.get_asset_return("equity")
        self.assertIsNotNone(equity_return)
        self.assertGreater(equity_return, 0)
        
        # Test getting a specific sub-class return
        large_cap_return = self.params.get_asset_return("equity", "large_cap")
        self.assertIsNotNone(large_cap_return)
        self.assertGreater(large_cap_return, 0)
        
        # Test getting a return with risk profile
        conservative_equity = self.params.get_asset_return("equity", None, "conservative")
        self.assertIsNotNone(conservative_equity)
        self.assertGreater(conservative_equity, 0)
    
    def test_get_allocation_model(self):
        """Test that allocation models can be retrieved"""
        # Test getting a basic allocation model
        moderate_allocation = self.params.get_allocation_model("moderate")
        self.assertIsNotNone(moderate_allocation)
        self.assertIn("equity", moderate_allocation)
        self.assertIn("debt", moderate_allocation)
        self.assertIn("gold", moderate_allocation)
        
        # Test getting an allocation model without sub-allocations
        conservative = self.params.get_allocation_model("conservative", False)
        self.assertIsNotNone(conservative)
        self.assertIn("equity", conservative)
        self.assertNotIn("sub_allocation", conservative)

class TestParameterCompatibilityAdapter(unittest.TestCase):
    """Test cases for the compatibility adapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Ensure legacy access is enabled for tests
        self.original_legacy_access = LEGACY_ACCESS_ENABLED
        self.original_log_deprecated = LOG_DEPRECATED_ACCESS
        
        # Get parameters instance (should be the adapter if LEGACY_ACCESS_ENABLED is True)
        self.params = get_parameters()
        
        # Get a direct instance of FinancialParameters for comparison
        self.direct_params = FinancialParameters()
        
        # Get an adapter instance directly
        self.adapter = ParameterCompatibilityAdapter(self.direct_params)
    
    def tearDown(self):
        """Clean up after tests"""
        pass  # This ensures singleton status remains intact for other tests
    
    def test_compatibility_get_legacy_keys(self):
        """Test that legacy keys work through the adapter"""
        # Test common legacy keys
        inflation_legacy = self.adapter.get("inflation_rate")
        inflation_direct = self.direct_params.get("inflation.general")
        self.assertEqual(inflation_legacy, inflation_direct)
        
        equity_legacy = self.adapter.get("equity_return")
        equity_direct = self.direct_params.get("asset_returns.equity.moderate")
        self.assertEqual(equity_legacy, equity_direct)
    
    def test_compatibility_get_hierarchical_paths(self):
        """Test that hierarchical paths also work through the adapter"""
        # New paths should work directly
        inflation_path = self.adapter.get("inflation.general")
        inflation_direct = self.direct_params.get("inflation.general")
        self.assertEqual(inflation_path, inflation_direct)
    
    def test_compatibility_special_methods(self):
        """Test that special methods are delegated correctly"""
        # Test get_asset_return delegation
        adapter_equity = self.adapter.get_asset_return("equity", "large_cap")
        direct_equity = self.direct_params.get_asset_return("equity", "large_cap")
        self.assertEqual(adapter_equity, direct_equity)
        
        # Test get_allocation_model delegation
        adapter_allocation = self.adapter.get_allocation_model("moderate")
        direct_allocation = self.direct_params.get_allocation_model("moderate")
        self.assertEqual(adapter_allocation, direct_allocation)
    
    def test_access_logging(self):
        """Test that deprecated access is logged"""
        # Clear any existing log
        self.adapter._access_log = {}
        
        # Access a legacy key
        self.adapter.get("inflation_rate")
        
        # Check that it was logged
        log = self.adapter.get_access_log()
        self.assertIn("inflation_rate", log)
        self.assertEqual(log["inflation_rate"], 1)
        
        # Access it again
        self.adapter.get("inflation_rate")
        
        # Check that the count increased
        log = self.adapter.get_access_log()
        self.assertEqual(log["inflation_rate"], 2)
    
    def test_get_legacy_access_report(self):
        """Test the global function for getting the access report"""
        # Access a legacy key through the global function
        params = get_parameters()
        
        # Clear existing log by creating a new access log
        if hasattr(params, '_access_log'):
            params._access_log = {}
        
        # Use a legacy key
        params.get("equity_return")
        
        # Get the report
        report = get_legacy_access_report()
        
        # Check that the access was logged
        self.assertIn("equity_return", report)
        self.assertGreater(report["equity_return"], 0)

if __name__ == "__main__":
    unittest.main()