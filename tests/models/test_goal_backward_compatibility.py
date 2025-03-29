#!/usr/bin/env python3
"""
Test script for Goal model backward compatibility features.

This script:
1. Tests property getters that map new field names to old ones
2. Tests that new fields have sensible defaults
3. Tests the to_dict() with legacy_mode
4. Tests from_legacy_dict() method with old data structures

Usage:
    python test_goal_backward_compatibility.py
"""

import os
import sys
import unittest
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from models.goal_models import Goal

class TestGoalBackwardCompatibility(unittest.TestCase):
    """Test suite for Goal model backward compatibility features"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a test goal with all fields
        self.test_goal = Goal(
            id="test-goal-123",
            user_profile_id="test-profile-456",
            category="education",
            title="Test Goal",
            target_amount=1000000.0,
            timeframe=(datetime.now() + timedelta(days=365)).isoformat(),
            current_amount=250000.0,
            importance="high",
            flexibility="somewhat_flexible",
            notes="This is a test goal",
            # New fields
            current_progress=25.0,
            priority_score=75.0,
            additional_funding_sources="Bonuses",
            goal_success_probability=80.0,
            adjustments_required=True,
            funding_strategy='{"strategy": "monthly", "amount": 15000}'
        )
        
        # Create a minimal test goal with just required fields
        self.minimal_goal = Goal(
            id="minimal-goal-789",
            category="home_purchase",
            title="Minimal Goal"
        )
        
        # Create a legacy dictionary
        self.legacy_dict = {
            "id": "legacy-goal-999",
            "profile_id": "legacy-profile-888",
            "category": "travel",
            "title": "Legacy Goal",
            "target_value": 200000.0,
            "time_horizon": 3,
            "current_value": 50000.0,
            "priority": "medium",
            "description": "This is a legacy goal"
        }
    
    def test_property_getters(self):
        """Test property getters that map new fields to old ones"""
        # Test all the property getters
        self.assertEqual(self.test_goal.priority, self.test_goal.importance)
        self.assertEqual(self.test_goal.target_value, self.test_goal.target_amount)
        self.assertEqual(self.test_goal.current_value, self.test_goal.current_amount)
        self.assertEqual(self.test_goal.progress, self.test_goal.current_progress)
        self.assertEqual(self.test_goal.description, self.test_goal.notes)
        self.assertEqual(self.test_goal.profile_id, self.test_goal.user_profile_id)
        
        # Test time_horizon calculation
        # We expect it to be approximately 1 year (365 days / 365 ≈ 1.0)
        self.assertAlmostEqual(self.test_goal.time_horizon, 1.0, delta=0.1)
    
    def test_sensible_defaults(self):
        """Test that new fields have sensible defaults"""
        # Test default values in minimal goal
        self.assertEqual(self.minimal_goal.target_amount, 0.0)
        self.assertEqual(self.minimal_goal.current_amount, 0.0)
        self.assertEqual(self.minimal_goal.importance, "medium")
        self.assertEqual(self.minimal_goal.flexibility, "somewhat_flexible")
        self.assertEqual(self.minimal_goal.notes, "")
        
        # Test default values for new fields
        self.assertEqual(self.minimal_goal.current_progress, 0.0)
        self.assertGreater(self.minimal_goal.priority_score, 0.0)  # Should be calculated
        self.assertEqual(self.minimal_goal.additional_funding_sources, "")
        self.assertEqual(self.minimal_goal.goal_success_probability, 0.0)
        self.assertEqual(self.minimal_goal.adjustments_required, False)
        self.assertEqual(self.minimal_goal.funding_strategy, "")
    
    def test_to_dict_legacy_mode(self):
        """Test the to_dict() method with legacy_mode"""
        # Get modern and legacy dictionaries
        modern_dict = self.test_goal.to_dict()
        legacy_dict = self.test_goal.to_dict(legacy_mode=True)
        
        # Modern dict should have new fields
        self.assertIn("current_progress", modern_dict)
        self.assertIn("priority_score", modern_dict)
        self.assertIn("additional_funding_sources", modern_dict)
        self.assertIn("goal_success_probability", modern_dict)
        self.assertIn("adjustments_required", modern_dict)
        self.assertIn("funding_strategy", modern_dict)
        
        # Legacy dict should not have new fields
        self.assertNotIn("current_progress", legacy_dict)
        self.assertNotIn("priority_score", legacy_dict)
        self.assertNotIn("additional_funding_sources", legacy_dict)
        self.assertNotIn("goal_success_probability", legacy_dict)
        self.assertNotIn("adjustments_required", legacy_dict)
        self.assertNotIn("funding_strategy", legacy_dict)
        
        # Legacy dict should have legacy fields
        self.assertIn("time_horizon", legacy_dict)
        self.assertIn("priority", legacy_dict)
        
        # Legacy fields should have mapped values
        self.assertEqual(legacy_dict["priority"], self.test_goal.importance)
        self.assertAlmostEqual(legacy_dict["time_horizon"], self.test_goal.time_horizon, delta=0.1)
    
    def test_from_legacy_dict(self):
        """Test from_legacy_dict() method with old data structures"""
        # Create a goal from the legacy dictionary
        goal = Goal.from_legacy_dict(self.legacy_dict)
        
        # Check that core fields are correctly mapped
        self.assertEqual(goal.id, self.legacy_dict["id"])
        self.assertEqual(goal.user_profile_id, self.legacy_dict["profile_id"])
        self.assertEqual(goal.category, self.legacy_dict["category"])
        self.assertEqual(goal.title, self.legacy_dict["title"])
        self.assertEqual(goal.target_amount, self.legacy_dict["target_value"])
        self.assertEqual(goal.current_amount, self.legacy_dict["current_value"])
        self.assertEqual(goal.importance, self.legacy_dict["priority"])
        self.assertEqual(goal.notes, self.legacy_dict["description"])
        
        # Check that timeframe was converted from time_horizon
        # We expect it to be approximately 3 years in the future
        target_date = datetime.fromisoformat(goal.timeframe)
        days_diff = (target_date - datetime.now()).days
        self.assertAlmostEqual(days_diff / 365.0, self.legacy_dict["time_horizon"], delta=0.1)
        
        # Check that new fields have sensible defaults
        self.assertEqual(goal.current_progress, 25.0)  # Calculated from target/current amounts
        self.assertGreater(goal.priority_score, 0.0)   # Should be calculated
        self.assertEqual(goal.additional_funding_sources, "")
        self.assertEqual(goal.goal_success_probability, 0.0)
        self.assertEqual(goal.adjustments_required, False)
        self.assertEqual(goal.funding_strategy, "")
    
    def test_mixed_old_new_fields(self):
        """Test handling of mixed old and new fields in dictionary"""
        # Create a mixed dictionary with both old and new field names
        mixed_dict = {
            "id": "mixed-goal-555",
            "profile_id": "mixed-profile-444",  # Old field
            "user_profile_id": "mixed-profile-333",  # New field (should take precedence)
            "category": "debt_repayment",
            "title": "Mixed Goal",
            "target_value": 100000.0,  # Old field
            "target_amount": 150000.0,  # New field (should take precedence)
            "time_horizon": 2,
            "priority": "low",  # Old field
            "importance": "high",  # New field (should take precedence)
            "description": "Old description",  # Old field
            "notes": "New notes",  # New field (should take precedence)
            "current_progress": 40.0,  # New field
            "additional_funding_sources": "Tax refund"  # New field
        }
        
        # Create a goal from the mixed dictionary
        goal = Goal.from_legacy_dict(mixed_dict)
        
        # Check that new fields take precedence
        self.assertEqual(goal.user_profile_id, mixed_dict["user_profile_id"])
        self.assertEqual(goal.target_amount, mixed_dict["target_amount"])
        self.assertEqual(goal.importance, mixed_dict["importance"])
        self.assertEqual(goal.notes, mixed_dict["notes"])
        
        # Check that new specific fields are populated
        self.assertEqual(goal.current_progress, mixed_dict["current_progress"])
        self.assertEqual(goal.additional_funding_sources, mixed_dict["additional_funding_sources"])
        
        # Also check through old field getters
        self.assertEqual(goal.profile_id, mixed_dict["user_profile_id"])
        self.assertEqual(goal.target_value, mixed_dict["target_amount"])
        self.assertEqual(goal.priority, mixed_dict["importance"])
        self.assertEqual(goal.description, mixed_dict["notes"])
        
if __name__ == "__main__":
    unittest.main()