#!/usr/bin/env python3
"""
Test script for validating the hierarchical goal category functionality.

This script tests:
1. Retrieving all predefined categories
2. Getting categories by hierarchy level
3. Getting subcategories for parent categories
4. Category initialization with duplicate handling

Usage:
    python test_goal_categories.py
"""

import os
import sys
import logging
import unittest
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from models.goal_models import GoalManager, GoalCategory

class GoalCategoriesTest(unittest.TestCase):
    """Test case for hierarchical goal categories functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment by initializing categories."""
        logger.info("Setting up test environment")
        cls.manager = GoalManager()
        
        # First, check if the new columns exist
        cls.has_hierarchy_columns = cls._check_hierarchy_columns(cls.manager)
        
        if not cls.has_hierarchy_columns:
            logger.warning("Hierarchy columns not found. Run migration script first:")
            logger.warning("python migrate_goal_categories.py")
            logger.warning("Tests will be skipped.")
        else:
            # Initialize categories if columns exist
            logger.info("Initializing predefined categories")
            cls.manager.initialize_predefined_categories()
            
    @staticmethod
    def _check_hierarchy_columns(manager):
        """Check if the hierarchy columns exist in the database."""
        try:
            # Use the manager's connection to check columns
            with manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(goal_categories)")
                columns = [column[1] for column in cursor.fetchall()]
                return 'hierarchy_level' in columns and 'parent_category_id' in columns
        except Exception as e:
            logger.error(f"Error checking hierarchy columns: {str(e)}")
            return False
            
    def setUp(self):
        """Skip tests if hierarchy columns don't exist."""
        if not self.has_hierarchy_columns:
            self.skipTest("Hierarchy columns not found in database")
    
    def test_main_categories(self):
        """Test retrieving all predefined categories."""
        logger.info("Testing get_all_categories()")
        
        # Get all categories
        categories = self.manager.get_all_categories()
        
        # Convert to list of names for easier testing
        category_names = [cat.name for cat in categories]
        
        # Check for the six main categories
        expected_categories = [
            "Security", "Essential", "Retirement", 
            "Lifestyle", "Legacy", "Custom"
        ]
        
        # Log found categories
        logger.info(f"Found {len(categories)} categories")
        for cat in categories:
            logger.info(f"  - {cat.name} (Level: {cat.hierarchy_level}, ID: {cat.id})")
        
        # Check if all expected categories exist
        for expected in expected_categories:
            with self.subTest(f"Check for {expected} category"):
                self.assertIn(expected, category_names, f"{expected} category not found")
                
        # Verify we have at least 6 categories (may have more if subcategories exist)
        self.assertGreaterEqual(len(categories), 6, "Should have at least 6 main categories")
        
    def test_hierarchy_levels(self):
        """Test getting categories by hierarchy level."""
        logger.info("Testing get_categories_by_hierarchy_level()")
        
        # Test each level
        levels = {
            self.manager.SECURITY_LEVEL: "Security",
            self.manager.ESSENTIAL_LEVEL: "Essential",
            self.manager.RETIREMENT_LEVEL: "Retirement",
            self.manager.LIFESTYLE_LEVEL: "Lifestyle",
            self.manager.LEGACY_LEVEL: "Legacy",
            self.manager.CUSTOM_LEVEL: "Custom"
        }
        
        for level, expected_name in levels.items():
            with self.subTest(f"Testing level {level} ({expected_name})"):
                logger.info(f"Getting categories for level {level} ({expected_name})")
                categories = self.manager.get_categories_by_hierarchy_level(level)
                
                # Log results
                logger.info(f"Found {len(categories)} categories at level {level}")
                for cat in categories:
                    logger.info(f"  - {cat.name} (ID: {cat.id})")
                
                # Check if we have at least one category at this level
                self.assertGreater(len(categories), 0, f"No categories found at level {level}")
                
                # Check if the expected category exists at this level
                category_names = [cat.name for cat in categories]
                self.assertIn(expected_name, category_names, 
                             f"{expected_name} category not found at level {level}")
    
    def test_subcategories(self):
        """Test getting subcategories for a parent category."""
        logger.info("Testing subcategory relationships")
        
        # Get all categories
        all_categories = self.manager.get_all_categories()
        
        # Create a dictionary mapping category names to their IDs
        category_ids = {cat.name: cat.id for cat in all_categories}
        
        # Create a dictionary of parent IDs for each category
        parent_ids = {cat.id: cat.parent_category_id for cat in all_categories}
        
        # Check if any subcategories exist (categories with non-null parent_category_id)
        subcategories = [cat for cat in all_categories if cat.parent_category_id is not None]
        
        if not subcategories:
            logger.warning("No subcategories found. This test will be partial.")
            self.skipTest("No subcategories found in database")
        
        # If we have subcategories, verify parent-child relationships
        for subcat in subcategories:
            parent_id = subcat.parent_category_id
            
            # Skip if parent_id is None
            if parent_id is None:
                continue
                
            # Find parent category in our list
            parent_category = next((cat for cat in all_categories if cat.id == parent_id), None)
            
            # Verify parent exists
            self.assertIsNotNone(parent_category, 
                                f"Parent category (ID: {parent_id}) not found for {subcat.name}")
            
            # Verify hierarchy level inheritance
            self.assertEqual(subcat.hierarchy_level, parent_category.hierarchy_level,
                           f"Subcategory {subcat.name} should inherit hierarchy level from parent {parent_category.name}")
            
            logger.info(f"Verified subcategory: {subcat.name} -> parent: {parent_category.name}")
    
    def test_initialize_duplicates(self):
        """Test that initialize_predefined_categories handles duplicates correctly."""
        logger.info("Testing duplicate handling in initialize_predefined_categories()")
        
        # Count categories before reinitializing
        before_count = len(self.manager.get_all_categories())
        logger.info(f"Categories before reinitialization: {before_count}")
        
        # Re-initialize categories without force_update
        success = self.manager.initialize_predefined_categories(force_update=False)
        self.assertTrue(success, "Category initialization should succeed")
        
        # Count categories after reinitializing
        after_count = len(self.manager.get_all_categories())
        logger.info(f"Categories after reinitialization: {after_count}")
        
        # Verify count didn't change (no duplicates created)
        self.assertEqual(before_count, after_count, 
                        "Category count should not change when reinitializing without force_update")
        
        # Get all categories to verify their properties
        categories = self.manager.get_all_categories()
        security_category = next((cat for cat in categories if cat.name == "Security"), None)
        
        # Security category should exist and be level 1
        self.assertIsNotNone(security_category, "Security category should exist")
        self.assertEqual(security_category.hierarchy_level, self.manager.SECURITY_LEVEL, 
                        "Security category should be level 1")
        
    def test_forced_update(self):
        """Test that forced update mode updates existing categories."""
        logger.info("Testing force_update mode")
        
        # Get current Security category and save its description
        categories = self.manager.get_all_categories()
        security_category = next((cat for cat in categories if cat.name == "Security"), None)
        original_description = security_category.description if security_category else "Unknown"
        
        try:
            # Temporarily modify the predefined description for the Security category
            original_predefined = self.manager.PREDEFINED_CATEGORIES[0]["description"]
            test_description = "TEMPORARY TEST DESCRIPTION - WILL BE REVERTED"
            self.manager.PREDEFINED_CATEGORIES[0]["description"] = test_description
            
            # Reinitialize with force_update=True
            success = self.manager.initialize_predefined_categories(force_update=True)
            self.assertTrue(success, "Forced update should succeed")
            
            # Verify that the description was updated
            categories = self.manager.get_all_categories()
            security_category = next((cat for cat in categories if cat.name == "Security"), None)
            self.assertIsNotNone(security_category, "Security category should exist")
            self.assertEqual(security_category.description, test_description,
                           "Description should be updated when force_update=True")
            
            logger.info("Forced update successfully modified existing category")
            
        finally:
            # Restore the original predefined description
            self.manager.PREDEFINED_CATEGORIES[0]["description"] = original_predefined
            
            # Put the database back to original state
            self.manager.initialize_predefined_categories(force_update=True)

def run_tests():
    """Run the test suite."""
    # Create test suite and run
    suite = unittest.TestLoader().loadTestsFromTestCase(GoalCategoriesTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Report results
    logger.info("Test Results:")
    logger.info(f"  Ran {result.testsRun} tests")
    logger.info(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"  Failures: {len(result.failures)}")
    logger.info(f"  Errors: {len(result.errors)}")
    
    # Return non-zero exit code if any tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    logger.info("Starting goal categories test suite")
    sys.exit(run_tests())