#!/usr/bin/env python3
"""
Test script for the goal probability fields migration.

This script verifies:
1. The migration adds the correct fields to existing goals
2. The probability calculation works as expected
3. The generated data structures are valid JSON
4. The Indian financial context is properly handled
"""

import os
import sys
import json
import unittest
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from models.goal_models import Goal, GoalManager
from utils.goal_data_migrator import (
    calculate_goal_success_probability,
    generate_simulation_data,
    generate_scenarios,
    generate_adjustments,
    format_indian_currency
)

class TestGoalProbabilityMigration(unittest.TestCase):
    """Test cases for goal probability migration"""
    
    def setUp(self):
        """Set up test data"""
        self.test_goals = []
        
        # Create test goals with different characteristics
        # 1. Retirement goal - long term, high amount
        retirement_goal = Goal(
            id="test-retirement-goal",
            user_profile_id="test-user",
            category="retirement",
            title="Retirement Fund",
            target_amount=10000000,  # 1 Crore
            timeframe=(datetime.now() + timedelta(days=365*20)).isoformat(),  # 20 years
            current_amount=1000000,  # 10 Lakh
            importance="high",
            flexibility="somewhat_flexible",
            notes="Retirement planning"
        )
        self.test_goals.append(retirement_goal)
        
        # 2. Education goal - medium term, medium amount
        education_goal = Goal(
            id="test-education-goal",
            user_profile_id="test-user",
            category="education",
            title="Child's College",
            target_amount=1500000,  # 15 Lakh
            timeframe=(datetime.now() + timedelta(days=365*10)).isoformat(),  # 10 years
            current_amount=300000,  # 3 Lakh
            importance="high",
            flexibility="fixed",
            notes="Education fund for child"
        )
        self.test_goals.append(education_goal)
        
        # 3. Emergency fund - short term, lower amount
        emergency_goal = Goal(
            id="test-emergency-goal",
            user_profile_id="test-user",
            category="emergency_fund",
            title="Emergency Fund",
            target_amount=300000,  # 3 Lakh
            timeframe=(datetime.now() + timedelta(days=365*1)).isoformat(),  # 1 year
            current_amount=150000,  # 1.5 Lakh
            importance="high",
            flexibility="fixed",
            notes="6 months of expenses"
        )
        self.test_goals.append(emergency_goal)
        
        # 4. Home purchase - medium term, high amount
        home_goal = Goal(
            id="test-home-goal",
            user_profile_id="test-user",
            category="home_purchase",
            title="Home Down Payment",
            target_amount=3000000,  # 30 Lakh
            timeframe=(datetime.now() + timedelta(days=365*5)).isoformat(),  # 5 years
            current_amount=500000,  # 5 Lakh
            importance="medium",
            flexibility="somewhat_flexible",
            notes="Down payment for house"
        )
        self.test_goals.append(home_goal)
        
        # 5. Wedding goal - short term, medium amount
        wedding_goal = Goal(
            id="test-wedding-goal",
            user_profile_id="test-user",
            category="wedding",
            title="Wedding Fund",
            target_amount=800000,  # 8 Lakh
            timeframe=(datetime.now() + timedelta(days=365*2)).isoformat(),  # 2 years
            current_amount=100000,  # 1 Lakh
            importance="medium",
            flexibility="somewhat_flexible",
            notes="Wedding expenses"
        )
        self.test_goals.append(wedding_goal)
    
    def test_format_indian_currency(self):
        """Test Indian currency formatting"""
        self.assertEqual(format_indian_currency(1500), "₹1500.00")
        self.assertEqual(format_indian_currency(150000), "₹1.50 L")
        self.assertEqual(format_indian_currency(20000000), "₹2.00 Cr")
    
    def test_calculate_goal_success_probability(self):
        """Test success probability calculation"""
        for goal in self.test_goals:
            probability = calculate_goal_success_probability(goal)
            
            # Verify probability range
            self.assertGreaterEqual(probability, 1.0)
            self.assertLessEqual(probability, 99.0)
            
            # Check that emergency fund has high probability
            if goal.category == "emergency_fund":
                self.assertGreaterEqual(probability, 50.0)
            
            # Check that wedding with short timeline has lower probability
            if goal.category == "wedding":
                self.assertLessEqual(probability, 75.0)
                
    def test_generate_simulation_data(self):
        """Test simulation data generation"""
        for goal in self.test_goals:
            # Calculate probability first
            goal.goal_success_probability = calculate_goal_success_probability(goal)
            
            # Generate simulation data
            simulation_data = generate_simulation_data(goal, goal.category)
            
            # Verify structure
            self.assertIn("monte_carlo", simulation_data)
            self.assertIn("investment_options", simulation_data)
            self.assertIn("target", simulation_data)
            
            # Verify SIP data
            self.assertIn("sip", simulation_data["investment_options"])
            self.assertIn("monthly_amount", simulation_data["investment_options"]["sip"])
            self.assertGreater(simulation_data["investment_options"]["sip"]["monthly_amount"], 0)
            
            # Verify tax benefits for retirement
            if goal.category == "retirement":
                self.assertTrue(simulation_data["investment_options"]["sip"]["tax_benefits"]["section_80c"])
                
            # Verify confidence interval
            self.assertEqual(len(simulation_data["monte_carlo"]["confidence_interval"]), 2)
            self.assertLessEqual(simulation_data["monte_carlo"]["confidence_interval"][0], 
                               simulation_data["monte_carlo"]["confidence_interval"][1])
                               
            # Verify target formatting for Indian context
            target_formatted = simulation_data["target"]["formatted"]
            if goal.target_amount >= 10000000:  # 1 Crore
                self.assertIn("Cr", target_formatted)
            elif goal.target_amount >= 100000:  # 1 Lakh
                self.assertIn("L", target_formatted)
            
            # Test if JSON serialization works
            json_str = json.dumps(simulation_data)
            parsed = json.loads(json_str)
            self.assertEqual(parsed["monte_carlo"]["success_rate"], simulation_data["monte_carlo"]["success_rate"])
    
    def test_generate_scenarios(self):
        """Test scenarios generation"""
        for goal in self.test_goals:
            # Calculate probability first
            goal.goal_success_probability = calculate_goal_success_probability(goal)
            
            # Generate simulation data
            simulation_data = generate_simulation_data(goal, goal.category)
            
            # Generate scenarios
            scenarios = generate_scenarios(goal, simulation_data)
            
            # Verify structure
            self.assertIn("conservative", scenarios)
            self.assertIn("moderate", scenarios)
            self.assertIn("aggressive", scenarios)
            
            # Verify data relationships
            self.assertGreater(scenarios["conservative"]["sip_amount"], 
                             scenarios["moderate"]["sip_amount"])
            self.assertLess(scenarios["aggressive"]["sip_amount"], 
                          scenarios["moderate"]["sip_amount"])
            
            self.assertLess(scenarios["conservative"]["success_probability"], 
                          scenarios["moderate"]["success_probability"])
            self.assertGreater(scenarios["aggressive"]["success_probability"], 
                             scenarios["moderate"]["success_probability"])
            
            # Test if JSON serialization works
            json_str = json.dumps(scenarios)
            parsed = json.loads(json_str)
            self.assertEqual(parsed["moderate"]["return_rate"], scenarios["moderate"]["return_rate"])
    
    def test_generate_adjustments(self):
        """Test adjustments generation"""
        for goal in self.test_goals:
            # Set adjustments required to true to force generation
            goal.adjustments_required = True
            goal.goal_success_probability = calculate_goal_success_probability(goal)
            
            # Generate simulation data
            simulation_data = generate_simulation_data(goal, goal.category)
            
            # Generate adjustments
            adjustments = generate_adjustments(goal, simulation_data)
            
            # Verify structure
            self.assertIsNotNone(adjustments)
            self.assertIn("recommended", adjustments)
            self.assertIn("applied", adjustments)
            self.assertIn("history", adjustments)
            
            # Verify there are recommendations
            self.assertGreater(len(adjustments["recommended"]), 0)
            
            # Verify each recommendation has expected fields
            for recommendation in adjustments["recommended"]:
                self.assertIn("type", recommendation)
                self.assertIn("amount", recommendation)
                self.assertIn("impact", recommendation)
                self.assertIn("description", recommendation)
                
                # Verify impact is positive
                self.assertGreater(recommendation["impact"], 0)
                
                # Verify description includes formatted amount
                if recommendation["type"] in ["increase_sip", "lumpsum_investment", "reduce_target"]:
                    self.assertIn("₹", recommendation["description"])
            
            # Test if JSON serialization works
            json_str = json.dumps(adjustments)
            parsed = json.loads(json_str)
            self.assertEqual(len(parsed["recommended"]), len(adjustments["recommended"]))
    
    def test_goal_helper_methods(self):
        """Test the Goal class helper methods for the new fields"""
        goal = self.test_goals[0]  # Use retirement goal
        
        # Generate data
        simulation_data = generate_simulation_data(goal, goal.category)
        scenarios = generate_scenarios(goal, simulation_data)
        adjustments = generate_adjustments(goal, simulation_data)
        
        # Test setters
        goal.set_simulation_data(simulation_data)
        goal.set_scenarios(scenarios)
        goal.set_adjustments(adjustments)
        
        # Test getters
        retrieved_simulation = goal.get_simulation_data()
        self.assertEqual(retrieved_simulation["monte_carlo"]["trials"], 
                       simulation_data["monte_carlo"]["trials"])
        
        retrieved_scenarios = goal.get_scenarios()
        self.assertEqual(retrieved_scenarios["moderate"]["return_rate"],
                       scenarios["moderate"]["return_rate"])
        
        retrieved_adjustments = goal.get_adjustments()
        self.assertEqual(len(retrieved_adjustments["recommended"]),
                       len(adjustments["recommended"]))
        
        # Test SIP helper
        sip_details = goal.get_sip_details()
        self.assertEqual(sip_details["monthly_amount"],
                       simulation_data["investment_options"]["sip"]["monthly_amount"])
        
        # Test JSON serialization via to_dict
        goal_dict = goal.to_dict()
        self.assertIn("simulation_data", goal_dict)
        self.assertIn("scenarios", goal_dict)
        self.assertIn("adjustments", goal_dict)

if __name__ == "__main__":
    unittest.main()