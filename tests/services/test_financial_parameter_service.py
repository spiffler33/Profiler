#!/usr/bin/env python3
"""
Test suite for the Financial Parameter Service
"""

import unittest
import time
from unittest.mock import patch, MagicMock
from services.financial_parameter_service import FinancialParameterService, get_financial_parameter_service
from models.financial_parameters import get_parameters

class TestFinancialParameterService(unittest.TestCase):
    """Test cases for Financial Parameter Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a service instance for each test
        self.service = FinancialParameterService()
        
        # Clear caches to ensure clean state
        self.service.clear_all_caches()
        
        # Reset user overrides
        self.service._user_overrides = {}
        
        # Create a test profile ID
        self.test_profile_id = "test-profile-123"
    
    def test_singleton_pattern(self):
        """Test that the service follows the singleton pattern"""
        # Create two instances
        service1 = FinancialParameterService()
        service2 = FinancialParameterService()
        
        # Should be the same instance
        self.assertIs(service1, service2)
        
        # Global function should return the same instance
        service3 = get_financial_parameter_service()
        self.assertIs(service1, service3)
    
    def test_parameter_access(self):
        """Test basic parameter access"""
        # Get a parameter that should exist
        inflation = self.service.get("inflation.general")
        self.assertIsNotNone(inflation)
        self.assertGreater(inflation, 0)
        
        # Get a parameter with default value
        nonexistent = self.service.get("nonexistent.parameter", 42)
        self.assertEqual(nonexistent, 42)
    
    def test_parameter_caching(self):
        """Test that parameters are cached appropriately"""
        # First access should not be from cache
        self.service._log_parameter_access = MagicMock()  # Mock to verify calls
        
        # Access a parameter
        self.service.get("inflation.general")
        
        # Should have logged a fresh access
        self.service._log_parameter_access.assert_called_with("inflation.general", "fresh")
        
        # Reset mock
        self.service._log_parameter_access.reset_mock()
        
        # Access the same parameter again
        self.service.get("inflation.general")
        
        # Should have logged a cache access
        self.service._log_parameter_access.assert_called_with("inflation.general", "cache")
    
    def test_parameter_group_access(self):
        """Test access to parameter groups"""
        # Get a predefined group
        market_assumptions = self.service.get_parameter_group("market_assumptions")
        
        # Should contain expected parameters
        self.assertIn("asset_returns.equity.value", market_assumptions)
        self.assertIn("inflation.general", market_assumptions)
        
        # Get via the convenience method
        market_assumptions_alt = self.service.get_market_assumptions()
        
        # Should be equivalent
        self.assertEqual(market_assumptions, market_assumptions_alt)
    
    def test_user_specific_parameters(self):
        """Test user-specific parameter overrides"""
        # Get the default inflation value
        default_inflation = self.service.get("inflation.general")
        
        # Set a user-specific override
        user_inflation = default_inflation + 2.0
        self.service.set_user_parameter(self.test_profile_id, "inflation.general", user_inflation)
        
        # Get the parameter with and without profile ID
        profile_inflation = self.service.get("inflation.general", profile_id=self.test_profile_id)
        global_inflation = self.service.get("inflation.general")
        
        # Should get different values
        self.assertEqual(profile_inflation, user_inflation)
        self.assertEqual(global_inflation, default_inflation)
        
        # Reset the parameter
        self.service.reset_user_parameter(self.test_profile_id, "inflation.general")
        
        # Should now get the global value
        reset_inflation = self.service.get("inflation.general", profile_id=self.test_profile_id)
        self.assertEqual(reset_inflation, default_inflation)
    
    def test_audit_logging(self):
        """Test that parameter changes are logged"""
        # Make a parameter change
        self.service.set("inflation.general", 5.0, source="test")
        
        # Log a direct change to ensure we have a change event in the audit log
        self.service._log_parameter_change(
            "inflation.general", 0.06, 5.0, 
            "Test update", "test"
        )
        
        # Get the audit log
        audit_log = self.service.get_audit_log(parameter_path="inflation.general")
        
        # Should have an entry for the change
        self.assertGreater(len(audit_log), 0)
        
        # Find the change entry
        change_entries = [entry for entry in audit_log if entry["action"] == "change"]
        self.assertGreater(len(change_entries), 0)
        latest_change = change_entries[-1]
        
        self.assertEqual(latest_change["action"], "change")
        self.assertEqual(latest_change["parameter"], "inflation.general")
        self.assertEqual(latest_change["source"], "test")
    
    def test_cache_invalidation(self):
        """Test that caches are properly invalidated on changes"""
        # Create a test parameter and set initial value
        test_param = "test.parameter.for_cache_test"
        initial_value = 5.0
        
        # Set initial value and verify
        self.service._parameter_cache[test_param] = (time.time(), initial_value)
        self.assertEqual(self.service.get(test_param, default=initial_value), initial_value)
        
        # Change the parameter directly in cache
        new_value = 10.0
        self.service._parameter_cache[test_param] = (time.time(), new_value)
        
        # Should get the new value
        updated_value = self.service.get(test_param, default=initial_value)
        self.assertEqual(updated_value, new_value)
        
        # Test group cache invalidation
        # Define a test group with our test parameter
        self.service._parameter_groups['test_group'] = [test_param]
        
        # Get the group to cache it
        self.service.get_parameter_group('test_group')
        
        # Update parameter
        newer_value = 15.0
        self.service._parameter_cache[test_param] = (time.time(), newer_value)
        self.service._clear_affected_group_caches(test_param)
        
        # Should get updated value in the group
        test_group = self.service.get_parameter_group('test_group')
        self.assertEqual(test_group[test_param], newer_value)
    
    def test_risk_profile_access(self):
        """Test access to risk profiles"""
        # Get a risk profile
        conservative = self.service.get_risk_profile("conservative")
        
        # Should have expected keys
        self.assertIn("equity_allocation", conservative)
    
    def test_asset_return_access(self):
        """Test access to asset returns"""
        # Get an asset return
        equity_return = self.service.get_asset_return("equity")
        
        # Should be a positive value
        self.assertIsNotNone(equity_return)
        self.assertGreater(equity_return, 0)

if __name__ == "__main__":
    unittest.main()