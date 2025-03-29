"""
Tests for the Goal Adjustment Module

This module contains tests for the GoalAdjustmentRecommender class which provides
recommendations for goal adjustments based on probability analysis and gap analysis.
"""

import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, Mock
import copy

from models.goal_adjustment import (
    GoalAdjustmentRecommender,
    AdjustmentRecommendation,
    AdjustmentOption,
    AdjustmentImpact
)

from models.gap_analysis import (
    GapResult,
    GapSeverity
)

# Test fixtures
@pytest.fixture
def sample_goal():
    """Fixture providing a sample financial goal for testing"""
    return Mock(
        id="goal-1",
        name="Test Retirement Goal",
        type="retirement",
        category="retirement",
        target_amount=1000000,
        current_amount=300000,
        target_date=date.today().replace(year=date.today().year + 20),
        monthly_contribution=1000,
        priority="high",
        asset_allocation={
            "equity": 0.7,
            "debt": 0.2,
            "gold": 0.05,
            "cash": 0.05
        }
    )

@pytest.fixture
def sample_goals():
    """Fixture providing multiple goals of different types for testing"""
    today = date.today()
    
    retirement_goal = Mock(
        id="goal-retirement",
        name="Retirement",
        type="retirement",
        category="retirement",
        target_amount=2000000,
        current_amount=500000,
        target_date=today.replace(year=today.year + 25),
        monthly_contribution=2000,
        priority="high",
        asset_allocation={
            "equity": 0.7,
            "debt": 0.2,
            "gold": 0.05,
            "cash": 0.05
        }
    )
    
    emergency_goal = Mock(
        id="goal-emergency",
        name="Emergency Fund",
        type="emergency_fund",
        category="emergency_fund",
        target_amount=50000,
        current_amount=20000,
        target_date=today.replace(year=today.year + 2),
        monthly_contribution=1000,
        priority="high",
        asset_allocation={
            "equity": 0.1,
            "debt": 0.3,
            "cash": 0.6
        }
    )
    
    education_goal = Mock(
        id="goal-education",
        name="Education Fund",
        type="education",
        category="education",
        target_amount=500000,
        current_amount=100000,
        target_date=today.replace(year=today.year + 10),
        monthly_contribution=3000,
        priority="medium",
        asset_allocation={
            "equity": 0.6,
            "debt": 0.3,
            "gold": 0.05,
            "cash": 0.05
        }
    )
    
    home_goal = Mock(
        id="goal-home",
        name="Home Purchase",
        type="home",
        category="home",
        target_amount=3000000,
        current_amount=500000,
        target_date=today.replace(year=today.year + 7),
        monthly_contribution=20000,
        priority="high",
        asset_allocation={
            "equity": 0.5,
            "debt": 0.4,
            "gold": 0.05,
            "cash": 0.05
        }
    )
    
    vacation_goal = Mock(
        id="goal-vacation",
        name="Vacation",
        type="discretionary",
        category="discretionary",
        target_amount=100000,
        current_amount=20000,
        target_date=today.replace(year=today.year + 1),
        monthly_contribution=5000,
        priority="low",
        asset_allocation={
            "equity": 0.3,
            "debt": 0.4,
            "gold": 0.0,
            "cash": 0.3
        }
    )
    
    return [retirement_goal, emergency_goal, education_goal, home_goal, vacation_goal]

@pytest.fixture
def sample_profile():
    """Fixture providing a sample user profile for testing"""
    return Mock(
        id="profile-1",
        name="Test User",
        age=35,
        retirement_age=65,
        annual_income=120000,
        monthly_expenses=4000,
        risk_tolerance="moderate",
        country="India"
    )

@pytest.fixture
def mock_parameter_service():
    """Fixture providing a mock parameter service with return assumptions"""
    service = Mock()
    
    # Set up mock return values
    service.get_inflation_assumption.return_value = 0.06  # 6% for India
    service.get_return_assumptions.return_value = {
        "equity": 0.12,  # 12% for equity in India
        "debt": 0.08,    # 8% for debt in India
        "gold": 0.07,    # 7% for gold
        "cash": 0.04     # 4% for cash
    }
    service.get_tax_rate.return_value = 0.30  # 30% tax rate
    service.get_section_80c_limit.return_value = 150000  # Rs. 1.5 lakh for 80C
    
    return service

@pytest.fixture
def mock_gap_analyzer():
    """Fixture providing a mock gap analyzer"""
    analyzer = Mock()
    
    # Create a mock analyze_goal_gap method
    def mock_analyze_goal(goal, profile):
        # Return different gaps based on goal type
        if goal.type == "retirement":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=500000,
                gap_percentage=25.0,
                severity=GapSeverity.SIGNIFICANT,
                timeframe_gap=5,
                capacity_gap=1000
            )
        elif goal.type == "emergency_fund":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=10000,
                gap_percentage=20.0,
                severity=GapSeverity.MODERATE,
                timeframe_gap=1,
                capacity_gap=500
            )
        elif goal.type == "education":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=150000,
                gap_percentage=30.0,
                severity=GapSeverity.SIGNIFICANT,
                timeframe_gap=3,
                capacity_gap=1500
            )
        elif goal.type == "home":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=1000000,
                gap_percentage=33.3,
                severity=GapSeverity.SEVERE,
                timeframe_gap=2,
                capacity_gap=10000
            )
        else:  # discretionary
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=20000,
                gap_percentage=20.0,
                severity=GapSeverity.MANAGEABLE,
                timeframe_gap=0,
                capacity_gap=1000
            )
    
    analyzer.analyze_goal_gap.side_effect = mock_analyze_goal
    
    return analyzer

@pytest.fixture
def mock_probability_analyzer():
    """Fixture providing a mock probability analyzer"""
    analyzer = Mock()
    
    # Create a mock analyze_goal_probability method
    def mock_analyze_probability(goal, profile):
        # Return different probabilities based on goal type
        if goal.type == "retirement":
            return Mock(
                goal_id=goal.id,
                success_probability=0.65,
                outcome_distribution=Mock(),
                timeline_assessment={
                    "expected_years": 25,
                    "expected_months": 6,
                    "probability_by_year": {
                        "20": 0.45,
                        "25": 0.65,
                        "30": 0.85
                    }
                },
                to_dict=lambda: {
                    "goal_id": goal.id,
                    "success_probability": 0.65,
                    "outcome_distribution": {},
                    "timeline_assessment": {
                        "expected_years": 25,
                        "expected_months": 6,
                        "probability_by_year": {
                            "20": 0.45,
                            "25": 0.65,
                            "30": 0.85
                        }
                    }
                }
            )
        elif goal.type == "emergency_fund":
            return Mock(
                goal_id=goal.id,
                success_probability=0.85,
                outcome_distribution=Mock(),
                timeline_assessment={
                    "expected_years": 1,
                    "expected_months": 10,
                    "probability_by_year": {
                        "1": 0.5,
                        "2": 0.85,
                        "3": 0.95
                    }
                },
                to_dict=lambda: {
                    "goal_id": goal.id,
                    "success_probability": 0.85,
                    "outcome_distribution": {},
                    "timeline_assessment": {
                        "expected_years": 1,
                        "expected_months": 10,
                        "probability_by_year": {
                            "1": 0.5,
                            "2": 0.85,
                            "3": 0.95
                        }
                    }
                }
            )
        elif goal.type == "education":
            return Mock(
                goal_id=goal.id,
                success_probability=0.75,
                outcome_distribution=Mock(),
                timeline_assessment={
                    "expected_years": 9,
                    "expected_months": 3,
                    "probability_by_year": {
                        "8": 0.6,
                        "10": 0.75,
                        "12": 0.9
                    }
                },
                to_dict=lambda: {
                    "goal_id": goal.id,
                    "success_probability": 0.75,
                    "outcome_distribution": {},
                    "timeline_assessment": {
                        "expected_years": 9,
                        "expected_months": 3,
                        "probability_by_year": {
                            "8": 0.6,
                            "10": 0.75,
                            "12": 0.9
                        }
                    }
                }
            )
        elif goal.type == "home":
            return Mock(
                goal_id=goal.id,
                success_probability=0.60,
                outcome_distribution=Mock(),
                timeline_assessment={
                    "expected_years": 7,
                    "expected_months": 8,
                    "probability_by_year": {
                        "6": 0.45,
                        "7": 0.60,
                        "9": 0.85
                    }
                },
                to_dict=lambda: {
                    "goal_id": goal.id,
                    "success_probability": 0.60,
                    "outcome_distribution": {},
                    "timeline_assessment": {
                        "expected_years": 7,
                        "expected_months": 8,
                        "probability_by_year": {
                            "6": 0.45,
                            "7": 0.60,
                            "9": 0.85
                        }
                    }
                }
            )
        else:  # discretionary
            return Mock(
                goal_id=goal.id,
                success_probability=0.90,
                outcome_distribution=Mock(),
                timeline_assessment={
                    "expected_years": 1,
                    "expected_months": 0,
                    "probability_by_year": {
                        "1": 0.90,
                        "2": 0.98
                    }
                },
                to_dict=lambda: {
                    "goal_id": goal.id,
                    "success_probability": 0.90,
                    "outcome_distribution": {},
                    "timeline_assessment": {
                        "expected_years": 1,
                        "expected_months": 0,
                        "probability_by_year": {
                            "1": 0.90,
                            "2": 0.98
                        }
                    }
                }
            )
    
    analyzer.analyze_goal_probability.side_effect = mock_analyze_probability
    
    return analyzer

# Tests for GoalAdjustmentRecommender
class TestGoalAdjustmentRecommender:
    """Tests for the GoalAdjustmentRecommender class"""
    
    def test_goal_adjustment_recommender_initialization(self, mock_parameter_service, mock_gap_analyzer, mock_probability_analyzer):
        """Test initialization of goal adjustment recommender"""
        # Initialize with required services
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Verify that services are set correctly
        assert recommender.parameter_service == mock_parameter_service
        assert recommender.gap_analyzer == mock_gap_analyzer
        assert recommender.probability_analyzer == mock_probability_analyzer
        
        # Verify that adjustment thresholds are initialized
        assert hasattr(recommender, 'target_probability')
        assert hasattr(recommender, 'min_acceptable_probability')
        
        # Test initialization with custom thresholds
        custom_recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer,
            target_probability=0.85,
            min_acceptable_probability=0.6
        )
        
        assert custom_recommender.target_probability == 0.85
        assert custom_recommender.min_acceptable_probability == 0.6
    
    def test_recommend_adjustments(self, sample_goals, sample_profile, mock_parameter_service, 
                                  mock_gap_analyzer, mock_probability_analyzer):
        """Test recommendation of adjustments for various goal types and gaps"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Test with each goal type
        for goal in sample_goals:
            # Get recommendations for this goal
            recommendations = recommender.recommend_adjustments(goal, sample_profile)
            
            # Verify recommendation structure
            assert isinstance(recommendations, AdjustmentRecommendation)
            assert recommendations.goal_id == goal.id
            assert hasattr(recommendations, 'current_probability')
            assert hasattr(recommendations, 'target_probability')
            assert hasattr(recommendations, 'adjustment_options')
            assert isinstance(recommendations.adjustment_options, list)
            
            # Verify that we have options for different adjustment types
            adjustment_types = {option.adjustment_type for option in recommendations.adjustment_options}
            
            # Skip allocation adjustment check for low-risk goals like emergency fund
            expected_types = {"target_amount", "timeframe", "contribution"}
            if goal.type != "emergency_fund":
                expected_types.add("allocation")
                
            # Verify we have the expected adjustment types
            assert adjustment_types.issuperset(expected_types)
            
            # Verify each option has impact assessment
            for option in recommendations.adjustment_options:
                assert hasattr(option, 'impact')
                assert hasattr(option.impact, 'probability_change')
                assert hasattr(option.impact, 'monthly_budget_impact')
    
    def test_adjust_target_amount(self, sample_goal, sample_profile, mock_parameter_service,
                                 mock_gap_analyzer, mock_probability_analyzer):
        """Test target amount adjustment with different reduction scenarios"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Mock the _simulate_probability_change method
        with patch.object(recommender, '_simulate_probability_change') as mock_simulate:
            # Define simulation results for different target reductions
            simulation_results = {
                0.95: 0.05,   # 5% reduction gives 0.05 probability increase
                0.9: 0.1,     # 10% reduction gives 0.1 probability increase
                0.85: 0.15,   # 15% reduction gives 0.15 probability increase
                0.8: 0.2      # 20% reduction gives 0.2 probability increase
            }
            
            def simulate_side_effect(goal, profile, adjustment_type, adjustment_value):
                if adjustment_type == "target_amount":
                    reduction_factor = adjustment_value / goal.target_amount
                    # Find the closest reduction factor in our simulation results
                    closest_factor = min(simulation_results.keys(), 
                                        key=lambda x: abs(x - reduction_factor))
                    return simulation_results[closest_factor]
                return 0.0
                
            mock_simulate.side_effect = simulate_side_effect
            
            # Get target amount adjustment options
            options = recommender._generate_target_amount_options(sample_goal, sample_profile, 0.65, 0.8)
            
            # Verify we have options
            assert len(options) > 0
            
            # Verify option structure
            for option in options:
                assert option.adjustment_type == "target_amount"
                assert hasattr(option, 'adjustment_value')
                assert hasattr(option, 'description')
                assert hasattr(option, 'impact')
                
                # Verify the adjustment is a reduction (lower than original target)
                assert option.adjustment_value < sample_goal.target_amount
                
                # Verify impact is positive (probability increase)
                assert option.impact.probability_change > 0
                
                # Verify budget impact is calculated
                assert hasattr(option.impact, 'monthly_budget_impact')
                assert option.impact.monthly_budget_impact <= 0  # Should be zero or negative (saving)
    
    def test_adjust_timeframe(self, sample_goal, sample_profile, mock_parameter_service,
                            mock_gap_analyzer, mock_probability_analyzer):
        """Test timeframe adjustment with various extension options"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Mock the _simulate_probability_change method
        with patch.object(recommender, '_simulate_probability_change') as mock_simulate:
            # Define simulation results for different timeframe extensions
            simulation_results = {
                1: 0.05,   # 1 year extension gives 0.05 probability increase
                2: 0.1,    # 2 year extension gives 0.1 probability increase
                3: 0.15,   # 3 year extension gives 0.15 probability increase
                5: 0.25    # 5 year extension gives 0.25 probability increase
            }
            
            def simulate_side_effect(goal, profile, adjustment_type, adjustment_value):
                if adjustment_type == "timeframe":
                    # adjustment_value should be the new target date
                    years_extended = adjustment_value.year - goal.target_date.year
                    if years_extended in simulation_results:
                        return simulation_results[years_extended]
                    # Interpolate for other values
                    keys = sorted(simulation_results.keys())
                    for i in range(len(keys) - 1):
                        if keys[i] <= years_extended <= keys[i+1]:
                            ratio = (years_extended - keys[i]) / (keys[i+1] - keys[i])
                            return simulation_results[keys[i]] + ratio * (simulation_results[keys[i+1]] - simulation_results[keys[i]])
                return 0.0
                
            mock_simulate.side_effect = simulate_side_effect
            
            # Get timeframe adjustment options
            options = recommender._generate_timeframe_options(sample_goal, sample_profile, 0.65, 0.8)
            
            # Verify we have options
            assert len(options) > 0
            
            # Verify option structure
            for option in options:
                assert option.adjustment_type == "timeframe"
                assert hasattr(option, 'adjustment_value')
                assert hasattr(option, 'description')
                assert hasattr(option, 'impact')
                
                # Verify the adjustment extends the timeframe
                assert option.adjustment_value > sample_goal.target_date
                
                # Verify impact is positive (probability increase)
                assert option.impact.probability_change > 0
                
                # Verify monthly budget impact is calculated
                assert hasattr(option.impact, 'monthly_budget_impact')
    
    def test_adjust_contribution(self, sample_goal, sample_profile, mock_parameter_service,
                               mock_gap_analyzer, mock_probability_analyzer):
        """Test contribution adjustment with different income profiles"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Mock the _simulate_probability_change method
        with patch.object(recommender, '_simulate_probability_change') as mock_simulate:
            # Define simulation results for different contribution increases
            simulation_results = {
                1.1: 0.05,   # 10% increase gives 0.05 probability increase
                1.2: 0.1,    # 20% increase gives 0.1 probability increase
                1.5: 0.2,    # 50% increase gives 0.2 probability increase
                2.0: 0.3     # 100% increase gives 0.3 probability increase
            }
            
            def simulate_side_effect(goal, profile, adjustment_type, adjustment_value):
                if adjustment_type == "contribution":
                    increase_factor = adjustment_value / goal.monthly_contribution
                    # Find the closest increase factor in our simulation results
                    closest_factor = min(simulation_results.keys(), 
                                        key=lambda x: abs(x - increase_factor))
                    return simulation_results[closest_factor]
                return 0.0
                
            mock_simulate.side_effect = simulate_side_effect
            
            # Get contribution adjustment options
            options = recommender._generate_contribution_options(sample_goal, sample_profile, 0.65, 0.8)
            
            # Verify we have options
            assert len(options) > 0
            
            # Verify option structure
            for option in options:
                assert option.adjustment_type == "contribution"
                assert hasattr(option, 'adjustment_value')
                assert hasattr(option, 'description')
                assert hasattr(option, 'impact')
                
                # Verify the adjustment increases contribution
                assert option.adjustment_value > sample_goal.monthly_contribution
                
                # Verify impact is positive (probability increase)
                assert option.impact.probability_change > 0
                
                # Verify monthly budget impact is calculated (should be positive - cost increase)
                assert hasattr(option.impact, 'monthly_budget_impact')
                assert option.impact.monthly_budget_impact > 0
                
                # Verify the budget impact matches the contribution increase
                contribution_increase = option.adjustment_value - sample_goal.monthly_contribution
                assert abs(option.impact.monthly_budget_impact - contribution_increase) < 0.01
    
    def test_adjust_allocation(self, sample_goal, sample_profile, mock_parameter_service,
                            mock_gap_analyzer, mock_probability_analyzer):
        """Test allocation adjustment with various risk profiles"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Mock the _simulate_probability_change method
        with patch.object(recommender, '_simulate_probability_change') as mock_simulate:
            # Define simulation results for different equity allocations
            simulation_results = {
                0.5: -0.1,   # 50% equity gives 0.1 probability decrease
                0.6: -0.05,  # 60% equity gives 0.05 probability decrease
                0.7: 0.0,    # 70% equity (current) gives no change
                0.8: 0.05,   # 80% equity gives 0.05 probability increase
                0.9: 0.1     # 90% equity gives 0.1 probability increase
            }
            
            def simulate_side_effect(goal, profile, adjustment_type, adjustment_value):
                if adjustment_type == "allocation":
                    # Extract equity allocation
                    equity_allocation = adjustment_value.get("equity", 0)
                    # Find the closest equity allocation in our simulation results
                    closest_allocation = min(simulation_results.keys(), 
                                           key=lambda x: abs(x - equity_allocation))
                    return simulation_results[closest_allocation]
                return 0.0
                
            mock_simulate.side_effect = simulate_side_effect
            
            # Get allocation adjustment options
            options = recommender._generate_allocation_options(sample_goal, sample_profile, 0.65, 0.8)
            
            # Verify we have options
            assert len(options) > 0
            
            # Verify option structure
            for option in options:
                assert option.adjustment_type == "allocation"
                assert hasattr(option, 'adjustment_value')
                assert hasattr(option, 'description')
                assert hasattr(option, 'impact')
                
                # Verify the adjustment is a valid allocation (sums to 1.0)
                allocation = option.adjustment_value
                assert abs(sum(allocation.values()) - 1.0) < 0.01
                
                # Verify all allocation values are non-negative
                assert all(v >= 0 for v in allocation.values())
    
    def test_goal_adjustment_data_structure(self, sample_goal, sample_profile, mock_parameter_service,
                                          mock_gap_analyzer, mock_probability_analyzer):
        """Test goal adjustment data structure consistency"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Get recommendations
        recommendations = recommender.recommend_adjustments(sample_goal, sample_profile)
        
        # Verify structure
        assert isinstance(recommendations, AdjustmentRecommendation)
        assert recommendations.goal_id == sample_goal.id
        assert isinstance(recommendations.current_probability, float)
        assert isinstance(recommendations.target_probability, float)
        assert isinstance(recommendations.adjustment_options, list)
        
        # Verify options
        for option in recommendations.adjustment_options:
            assert isinstance(option, AdjustmentOption)
            assert hasattr(option, 'adjustment_type')
            assert hasattr(option, 'adjustment_value')
            assert hasattr(option, 'description')
            assert hasattr(option, 'impact')
            
            # Verify impact
            assert isinstance(option.impact, AdjustmentImpact)
            assert hasattr(option.impact, 'probability_change')
            assert hasattr(option.impact, 'monthly_budget_impact')
            assert hasattr(option.impact, 'total_budget_impact')
            
        # Verify it can be converted to dictionary
        recommendations_dict = recommendations.to_dict()
        assert isinstance(recommendations_dict, dict)
        assert "goal_id" in recommendations_dict
        assert "current_probability" in recommendations_dict
        assert "target_probability" in recommendations_dict
        assert "adjustment_options" in recommendations_dict
    
    def test_indian_context_specific_adjustments(self, sample_goal, sample_profile, mock_parameter_service,
                                              mock_gap_analyzer, mock_probability_analyzer):
        """Test India-specific adjustments for tax and SIP recommendations"""
        # Set profile country to India
        sample_profile.country = "India"
        
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Mock the _simulate_probability_change method to return consistent values
        with patch.object(recommender, '_simulate_probability_change', return_value=0.1):
            # Set up retirement goal for testing 80C benefits
            retirement_goal = copy.deepcopy(sample_goal)
            retirement_goal.type = "retirement"
            retirement_goal.category = "retirement"
            
            # Get recommendations for retirement goal
            recommendations = recommender.recommend_adjustments(retirement_goal, sample_profile)
            
            # Look for India-specific recommendations
            has_tax_saving_option = False
            has_sip_option = False
            
            for option in recommendations.adjustment_options:
                if "80C" in option.description or "tax" in option.description.lower():
                    has_tax_saving_option = True
                
                if "SIP" in option.description or "systematic" in option.description.lower():
                    has_sip_option = True
            
            # Verify India-specific options are present
            assert has_tax_saving_option or has_sip_option, "No India-specific recommendations found"
    
    def test_adjustment_impact_calculations(self, sample_goal, sample_profile, mock_parameter_service,
                                          mock_gap_analyzer, mock_probability_analyzer):
        """Test accuracy of adjustment impact metrics"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Create sample adjustments
        adjustments = [
            {
                "type": "target_amount",
                "value": sample_goal.target_amount * 0.9,  # 10% reduction
                "probability_change": 0.1,  # 10% increase in probability
                "expected_monthly_impact": -sample_goal.monthly_contribution * 0.1  # 10% decrease in contribution
            },
            {
                "type": "contribution",
                "value": sample_goal.monthly_contribution * 1.2,  # 20% increase
                "probability_change": 0.15,  # 15% increase in probability
                "expected_monthly_impact": sample_goal.monthly_contribution * 0.2  # 20% increase in contribution
            },
            {
                "type": "timeframe",
                "value": sample_goal.target_date.replace(year=sample_goal.target_date.year + 2),  # 2 year extension
                "probability_change": 0.2,  # 20% increase in probability
                "expected_monthly_impact": -sample_goal.monthly_contribution * 0.15  # 15% decrease in contribution
            }
        ]
        
        # Test impact calculation for each adjustment
        for adj in adjustments:
            # Mock the _simulate_probability_change method
            with patch.object(recommender, '_simulate_probability_change', return_value=adj["probability_change"]):
                if adj["type"] == "target_amount":
                    # Calculate impact for target amount adjustment
                    impact = recommender._calculate_adjustment_impact(
                        sample_goal, sample_profile, adj["type"], adj["value"], 0.65
                    )
                elif adj["type"] == "contribution":
                    # Calculate impact for contribution adjustment
                    impact = recommender._calculate_adjustment_impact(
                        sample_goal, sample_profile, adj["type"], adj["value"], 0.65
                    )
                elif adj["type"] == "timeframe":
                    # Calculate impact for timeframe adjustment
                    impact = recommender._calculate_adjustment_impact(
                        sample_goal, sample_profile, adj["type"], adj["value"], 0.65
                    )
                
                # Verify impact structure
                assert isinstance(impact, AdjustmentImpact)
                assert hasattr(impact, 'probability_change')
                assert hasattr(impact, 'monthly_budget_impact')
                assert hasattr(impact, 'total_budget_impact')
                
                # Verify probability change matches expected
                assert abs(impact.probability_change - adj["probability_change"]) < 0.01
                
                # Verify monthly budget impact is reasonably close to expected
                # (may not be exact due to implementation details)
                assert abs(impact.monthly_budget_impact - adj["expected_monthly_impact"]) < adj["expected_monthly_impact"] * 0.2  # within 20%
                
                # Verify total budget impact is calculated
                assert impact.total_budget_impact is not None
                
                # Total impact should be monthly * months until goal
                months_until_goal = (sample_goal.target_date.year - date.today().year) * 12
                if adj["type"] != "timeframe":  # for original timeframe
                    assert abs(impact.total_budget_impact - (impact.monthly_budget_impact * months_until_goal)) < 100
                
    def test_prioritize_adjustment_options(self, sample_goal, sample_profile, mock_parameter_service,
                                         mock_gap_analyzer, mock_probability_analyzer):
        """Test that adjustment options are properly prioritized"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Create adjustment options with different impacts
        options = [
            AdjustmentOption(
                adjustment_type="target_amount",
                adjustment_value=sample_goal.target_amount * 0.9,
                description="Reduce target by 10%",
                impact=AdjustmentImpact(
                    probability_change=0.1,
                    monthly_budget_impact=-100,
                    total_budget_impact=-24000
                )
            ),
            AdjustmentOption(
                adjustment_type="contribution",
                adjustment_value=sample_goal.monthly_contribution * 1.2,
                description="Increase contribution by 20%",
                impact=AdjustmentImpact(
                    probability_change=0.15,
                    monthly_budget_impact=200,
                    total_budget_impact=48000
                )
            ),
            AdjustmentOption(
                adjustment_type="timeframe",
                adjustment_value=sample_goal.target_date.replace(year=sample_goal.target_date.year + 2),
                description="Extend timeline by 2 years",
                impact=AdjustmentImpact(
                    probability_change=0.2,
                    monthly_budget_impact=-150,
                    total_budget_impact=-43200
                )
            )
        ]
        
        # Mock the _generate methods to return our predefined options
        with patch.object(recommender, '_generate_target_amount_options', return_value=[options[0]]), \
             patch.object(recommender, '_generate_contribution_options', return_value=[options[1]]), \
             patch.object(recommender, '_generate_timeframe_options', return_value=[options[2]]), \
             patch.object(recommender, '_generate_allocation_options', return_value=[]):
            
            # Get recommendations
            recommendations = recommender.recommend_adjustments(sample_goal, sample_profile)
            
            # Verify options are included in the result
            assert len(recommendations.adjustment_options) == 3
            
            # Verify options are sorted by probability change (highest first)
            sorted_options = sorted(options, key=lambda x: x.impact.probability_change, reverse=True)
            for i, option in enumerate(recommendations.adjustment_options):
                assert option.adjustment_type == sorted_options[i].adjustment_type
                assert option.impact.probability_change == sorted_options[i].impact.probability_change
    
    def test_combined_adjustment_recommendations(self, sample_goal, sample_profile, mock_parameter_service,
                                              mock_gap_analyzer, mock_probability_analyzer):
        """Test combined adjustments are recommended when single adjustments are insufficient"""
        # Create recommender
        recommender = GoalAdjustmentRecommender(
            parameter_service=mock_parameter_service,
            gap_analyzer=mock_gap_analyzer,
            probability_analyzer=mock_probability_analyzer
        )
        
        # Set up a goal with very low probability
        sample_goal.target_amount = 2000000  # Very high target
        current_probability = 0.4  # Very low probability
        target_probability = 0.8  # Significant increase needed
        
        # Create options that individually don't meet the target
        target_option = AdjustmentOption(
            adjustment_type="target_amount",
            adjustment_value=sample_goal.target_amount * 0.85,
            description="Reduce target by 15%",
            impact=AdjustmentImpact(
                probability_change=0.15,
                monthly_budget_impact=-150,
                total_budget_impact=-36000
            )
        )
        
        contribution_option = AdjustmentOption(
            adjustment_type="contribution",
            adjustment_value=sample_goal.monthly_contribution * 1.3,
            description="Increase contribution by 30%",
            impact=AdjustmentImpact(
                probability_change=0.1,
                monthly_budget_impact=300,
                total_budget_impact=72000
            )
        )
        
        timeframe_option = AdjustmentOption(
            adjustment_type="timeframe",
            adjustment_value=sample_goal.target_date.replace(year=sample_goal.target_date.year + 3),
            description="Extend timeline by 3 years",
            impact=AdjustmentImpact(
                probability_change=0.2,
                monthly_budget_impact=-200,
                total_budget_impact=-48000
            )
        )
        
        # Mock the _generate methods to return our predefined options
        with patch.object(recommender, '_generate_target_amount_options', return_value=[target_option]), \
             patch.object(recommender, '_generate_contribution_options', return_value=[contribution_option]), \
             patch.object(recommender, '_generate_timeframe_options', return_value=[timeframe_option]), \
             patch.object(recommender, '_generate_allocation_options', return_value=[]), \
             patch.object(recommender, '_simulate_probability_change') as mock_simulate:
            
            # Make combined adjustments more effective
            def simulate_combined(goal, profile, adjustment_type, adjustment_value):
                if isinstance(adjustment_type, list):
                    # Combined adjustment - add individual effects and a synergy bonus
                    return sum(option.impact.probability_change for option in [target_option, timeframe_option]) + 0.05
                else:
                    # Individual adjustments - use predefined values
                    if adjustment_type == "target_amount":
                        return target_option.impact.probability_change
                    elif adjustment_type == "contribution":
                        return contribution_option.impact.probability_change
                    elif adjustment_type == "timeframe":
                        return timeframe_option.impact.probability_change
                    return 0.0
                    
            mock_simulate.side_effect = simulate_combined
            
            # Get recommendations with combined options enabled
            with patch.object(recommender, '_generate_combined_options', wraps=recommender._generate_combined_options):
                recommendations = recommender.recommend_adjustments(
                    sample_goal, sample_profile, current_probability, target_probability, include_combined=True
                )
                
                # Verify we have both individual and combined options
                individual_options = [opt for opt in recommendations.adjustment_options 
                                     if not isinstance(opt.adjustment_type, list)]
                combined_options = [opt for opt in recommendations.adjustment_options 
                                   if isinstance(opt.adjustment_type, list)]
                
                assert len(individual_options) > 0
                assert len(combined_options) > 0
                
                # Verify combined options have higher probability improvements
                max_individual_change = max(opt.impact.probability_change for opt in individual_options)
                for combined_opt in combined_options:
                    assert combined_opt.impact.probability_change > max_individual_change