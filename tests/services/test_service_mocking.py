#!/usr/bin/env python3
"""
Service Layer Mocking Infrastructure

This module provides a robust mocking infrastructure for testing service layer
components with consistent mock objects and data.
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceMockFactory:
    """Factory for creating consistent service mocks."""
    
    def __init__(self):
        """Initialize the mock factory with test data."""
        # Create test profile ID
        self.test_profile_id = str(uuid.uuid4())
        
        # Create test goals
        self.retirement_goal_id = str(uuid.uuid4())
        self.education_goal_id = str(uuid.uuid4())
        self.home_goal_id = str(uuid.uuid4())
        
        # Create test goals and default profile data
        self.create_test_goals()
        self.create_default_profile_data()
        
    def create_test_goals(self):
        """Create consistent test goal objects."""
        # Retirement goal
        self.retirement_goal = MagicMock()
        self.retirement_goal.id = self.retirement_goal_id
        self.retirement_goal.user_profile_id = self.test_profile_id
        self.retirement_goal.category = "traditional_retirement"
        self.retirement_goal.title = "Retirement"
        self.retirement_goal.target_amount = 5000000
        self.retirement_goal.timeframe = (datetime.now() + timedelta(days=365*25)).isoformat()
        self.retirement_goal.current_amount = 1000000
        self.retirement_goal.importance = "high"
        self.retirement_goal.flexibility = "somewhat_flexible"
        self.retirement_goal.notes = "Test retirement goal"
        self.retirement_goal.current_progress = 20.0
        self.retirement_goal.goal_success_probability = 75.0
        self.retirement_goal.funding_strategy = json.dumps({
            "retirement_age": 65,
            "withdrawal_rate": 0.04
        })
        
        # Education goal
        self.education_goal = MagicMock()
        self.education_goal.id = self.education_goal_id
        self.education_goal.user_profile_id = self.test_profile_id
        self.education_goal.category = "education"
        self.education_goal.title = "College Fund"
        self.education_goal.target_amount = 1000000
        self.education_goal.timeframe = (datetime.now() + timedelta(days=365*10)).isoformat()
        self.education_goal.current_amount = 200000
        self.education_goal.importance = "high"
        self.education_goal.flexibility = "low"
        self.education_goal.notes = "Test education goal"
        self.education_goal.current_progress = 20.0
        self.education_goal.goal_success_probability = 65.0
        self.education_goal.funding_strategy = json.dumps({
            "education_type": "college",
            "years": 4
        })
        
        # Home purchase goal
        self.home_goal = MagicMock()
        self.home_goal.id = self.home_goal_id
        self.home_goal.user_profile_id = self.test_profile_id
        self.home_goal.category = "home_purchase"
        self.home_goal.title = "Home Down Payment"
        self.home_goal.target_amount = 2000000
        self.home_goal.timeframe = (datetime.now() + timedelta(days=365*5)).isoformat()
        self.home_goal.current_amount = 500000
        self.home_goal.importance = "high"
        self.home_goal.flexibility = "medium"
        self.home_goal.notes = "Test home purchase goal"
        self.home_goal.current_progress = 25.0
        self.home_goal.goal_success_probability = 70.0
        self.home_goal.funding_strategy = json.dumps({
            "down_payment_percent": 0.20,
            "home_value": 10000000
        })
        
        # Add to_dict methods to return consistent dictionary representations
        for goal in [self.retirement_goal, self.education_goal, self.home_goal]:
            goal.to_dict = self._create_to_dict_method(goal)
        
        # Store all test goals in a list
        self.test_goals = [self.retirement_goal, self.education_goal, self.home_goal]
    
    def create_default_profile_data(self):
        """Create default profile data for testing."""
        self.default_profile_data = {
            "id": self.test_profile_id,
            "name": "Test User",
            "email": "test@example.com",
            "annual_income": 1500000,
            "monthly_income": 125000,
            "monthly_expenses": 75000,
            "risk_profile": "moderate",
            "answers": [
                {"question_id": "annual_income", "answer": 1500000},
                {"question_id": "monthly_income", "answer": 125000},
                {"question_id": "monthly_expenses", "answer": 75000},
                {"question_id": "risk_profile", "answer": "moderate"}
            ]
        }
    
    def _create_to_dict_method(self, goal):
        """Create a to_dict method for a goal mock."""
        def to_dict_method(legacy_mode=False):
            if legacy_mode:
                # Return legacy format
                return {
                    "id": goal.id,
                    "profile_id": goal.user_profile_id,
                    "category": goal.category,
                    "title": goal.title,
                    "target_value": goal.target_amount,
                    "current_value": goal.current_amount,
                    "priority": goal.importance,
                    "description": goal.notes,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            else:
                # Return modern format with all fields
                return {
                    "id": goal.id,
                    "user_profile_id": goal.user_profile_id,
                    "category": goal.category,
                    "title": goal.title,
                    "target_amount": goal.target_amount,
                    "timeframe": goal.timeframe,
                    "current_amount": goal.current_amount,
                    "importance": goal.importance,
                    "flexibility": goal.flexibility,
                    "notes": goal.notes,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "current_progress": goal.current_progress,
                    "goal_success_probability": goal.goal_success_probability,
                    "funding_strategy": goal.funding_strategy
                }
        
        return MagicMock(side_effect=to_dict_method)
    
    def create_goal_manager_mock(self):
        """Create a consistent GoalManager mock."""
        mock_goal_manager = MagicMock()
        
        # Set up get_goal to return the appropriate goal
        mock_goal_manager.get_goal.side_effect = lambda goal_id: next(
            (g for g in self.test_goals if g.id == goal_id), None
        )
        
        # Set up get_profile_goals to return all goals
        mock_goal_manager.get_profile_goals.return_value = self.test_goals
        
        # Set up get_goals_by_priority to return goals in a specific order
        mock_goal_manager.get_goals_by_priority.return_value = [
            self.home_goal,
            self.education_goal,
            self.retirement_goal
        ]
        
        # Set up create_goal to return the created goal
        mock_goal_manager.create_goal.side_effect = lambda goal: goal
        
        # Set up update_goal to return the updated goal
        mock_goal_manager.update_goal.side_effect = lambda goal: goal
        
        # Set up delete_goal to return success
        mock_goal_manager.delete_goal.return_value = True
        
        return mock_goal_manager
    
    def create_probability_analyzer_mock(self):
        """Create a consistent GoalProbabilityAnalyzer mock."""
        mock_analyzer = MagicMock()
        
        # Create a mock ProbabilityResult
        result = MagicMock()
        result.success_metrics = {
            "success_probability": 0.75,
            "partial_success_probability": 0.85,
            "median_outcome": 5000000,
            "confidence_intervals": {
                "lower_bound": 0.65,
                "upper_bound": 0.85
            }
        }
        result.time_based_metrics = {
            "estimated_completion_time": 25,
            "current_progress": 20.0
        }
        result.risk_metrics = {
            "shortfall_risk": 0.25,
            "volatility": 0.15
        }
        
        # Add get_safe_success_probability method
        result.get_safe_success_probability = MagicMock(return_value=0.75)
        
        # Add to_dict method
        result.to_dict = MagicMock(return_value={
            "success_metrics": result.success_metrics,
            "time_based_metrics": result.time_based_metrics,
            "risk_metrics": result.risk_metrics
        })
        
        # Set up analyze_goal to return the probability result
        mock_analyzer.analyze_goal.return_value = result
        
        # Set up analyze_goal_probability to return the same result
        mock_analyzer.analyze_goal_probability.return_value = result
        
        return mock_analyzer
    
    def create_gap_analyzer_mock(self):
        """Create a consistent GapAnalyzer mock."""
        mock_gap_analyzer = MagicMock()
        
        # Create a mock gap result
        gap_result = MagicMock()
        gap_result.goal_id = self.retirement_goal.id
        gap_result.gap_amount = 1000000
        gap_result.gap_percentage = 0.2
        gap_result.severity = "MODERATE"
        
        # Create mock remediation options
        remediation_option1 = MagicMock()
        remediation_option1.description = "Increase monthly contribution"
        remediation_option1.adjustment_type = "contribution"
        remediation_option1.adjustment_value = 15000
        remediation_option1.impact_metrics = {"probability_change": 0.15}
        
        remediation_option2 = MagicMock()
        remediation_option2.description = "Extend timeframe by 2 years"
        remediation_option2.adjustment_type = "timeframe"
        remediation_option2.adjustment_value = (datetime.now() + timedelta(days=365*27)).isoformat()
        remediation_option2.impact_metrics = {"probability_change": 0.1}
        
        gap_result.remediation_options = [remediation_option1, remediation_option2]
        
        # Set up analyze_goal_gap to return the gap result
        mock_gap_analyzer.analyze_goal_gap.return_value = gap_result
        
        return mock_gap_analyzer
    
    def create_adjustment_recommender_mock(self):
        """Create a consistent GoalAdjustmentRecommender mock."""
        mock_recommender = MagicMock()
        
        # Create a mock adjustment result
        adjustment_result = MagicMock()
        adjustment_result.goal_id = self.retirement_goal.id
        
        # Reuse the remediation options from gap analyzer
        gap_analyzer = self.create_gap_analyzer_mock()
        gap_result = gap_analyzer.analyze_goal_gap.return_value
        adjustment_result.adjustment_options = gap_result.remediation_options
        
        adjustment_result.target_probability = 0.85
        adjustment_result.confidence_score = 0.8
        
        # Set up recommend_adjustments to return the adjustment result
        mock_recommender.recommend_adjustments.return_value = adjustment_result
        
        return mock_recommender
    
    def create_parameter_service_mock(self):
        """Create a consistent FinancialParameterService mock."""
        mock_param_service = MagicMock()
        
        # Set up extract_parameters to return a normalized parameter dict
        mock_param_service.extract_parameters.side_effect = lambda profile_data: {
            "annual_income": profile_data.get("annual_income", 100000),
            "monthly_income": profile_data.get("monthly_income", 
                                            profile_data.get("annual_income", 100000) / 12),
            "monthly_expenses": profile_data.get("monthly_expenses", 50000),
            "risk_profile": profile_data.get("risk_profile", "moderate")
        }
        
        # Set up get_parameters to return default values
        mock_param_service.get_parameters.return_value = {
            "inflation_rate": 0.06,
            "equity_return": 0.10,
            "debt_return": 0.06,
            "gold_return": 0.08,
            "cash_return": 0.04
        }
        
        return mock_param_service
    
    def apply_service_patches(self, test_case):
        """Apply all service patches to a test case."""
        # Create all mocks
        mock_goal_manager = self.create_goal_manager_mock()
        mock_probability_analyzer = self.create_probability_analyzer_mock()
        mock_gap_analyzer = self.create_gap_analyzer_mock()
        mock_adjustment_recommender = self.create_adjustment_recommender_mock()
        mock_param_service = self.create_parameter_service_mock()
        
        # Create patches
        goal_manager_patcher = patch('services.goal_service.GoalManager', 
                                   return_value=mock_goal_manager)
        probability_analyzer_patcher = patch('models.goal_probability.GoalProbabilityAnalyzer', 
                                           return_value=mock_probability_analyzer)
        gap_analyzer_patcher = patch('models.gap_analysis.analyzer.GapAnalysis', 
                                   return_value=mock_gap_analyzer)
        adjustment_recommender_patcher = patch('models.goal_adjustment.GoalAdjustmentRecommender', 
                                             return_value=mock_adjustment_recommender)
        param_service_patcher = patch('services.financial_parameter_service.FinancialParameterService', 
                                    return_value=mock_param_service)
        
        # Start all patches
        mock_goal_manager_instance = goal_manager_patcher.start()
        mock_probability_analyzer_instance = probability_analyzer_patcher.start()
        mock_gap_analyzer_instance = gap_analyzer_patcher.start()
        mock_adjustment_recommender_instance = adjustment_recommender_patcher.start()
        mock_param_service_instance = param_service_patcher.start()
        
        # Add to test case for cleanup
        test_case.addCleanup(goal_manager_patcher.stop)
        test_case.addCleanup(probability_analyzer_patcher.stop)
        test_case.addCleanup(gap_analyzer_patcher.stop)
        test_case.addCleanup(adjustment_recommender_patcher.stop)
        test_case.addCleanup(param_service_patcher.stop)
        
        # Return all mock instances
        return {
            "goal_manager": mock_goal_manager_instance,
            "probability_analyzer": mock_probability_analyzer_instance,
            "gap_analyzer": mock_gap_analyzer_instance,
            "adjustment_recommender": mock_adjustment_recommender_instance,
            "param_service": mock_param_service_instance
        }

# Create a single instance for import and reuse
service_mock_factory = ServiceMockFactory()