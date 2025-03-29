"""
Tests for the Goal Probability Module

This module contains tests for the GoalProbabilityAnalyzer class which performs
Monte Carlo simulations and probability analysis on financial goals.
"""

import pytest
import json
import numpy as np
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, Mock
import copy

from models.goal_probability import (
    GoalProbabilityAnalyzer,
    ProbabilityResult,
    GoalOutcomeDistribution
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
    
    return service

@pytest.fixture
def mock_monte_carlo_simulation():
    """Fixture providing a mock Monte Carlo simulation"""
    simulation = Mock()
    
    # Mock the run_simulation method to return predefined results
    simulation.run_simulation.return_value = {
        "goal_amount": 1000000,
        "goal_timeline_years": 20,
        "simulation_results": np.random.normal(1200000, 300000, 1000),  # Random normally distributed results
        "success_probability": 0.75,
        "percentiles": {
            "10": 800000,
            "25": 950000,
            "50": 1150000,
            "75": 1350000,
            "90": 1500000
        },
        "goal_achievement_timeline": {
            "years": 18,
            "months": 4
        }
    }
    
    return simulation

# Tests for GoalProbabilityAnalyzer
class TestGoalProbabilityAnalyzer:
    """Tests for the GoalProbabilityAnalyzer class"""
    
    def test_goal_probability_analyzer_initialization(self, mock_parameter_service):
        """Test initialization of the goal probability analyzer"""
        # Initialize with parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Verify that parameter service is set correctly
        assert analyzer.parameter_service == mock_parameter_service
        
        # Verify that default simulation parameters are set
        assert hasattr(analyzer, 'simulation_count')
        assert hasattr(analyzer, 'time_horizon_years')
        
        # Test initialization with custom parameters
        custom_analyzer = GoalProbabilityAnalyzer(
            parameter_service=mock_parameter_service,
            simulation_count=2000,
            time_horizon_years=40
        )
        
        assert custom_analyzer.simulation_count == 2000
        assert custom_analyzer.time_horizon_years == 40
    
    def test_analyze_goal_probability(self, sample_goal, sample_profile, mock_parameter_service):
        """Test analysis of goal probability with different goal types"""
        # Create analyzer with mocked parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Mock the MonteCarloSimulation to avoid actual simulation
        with patch('models.goal_probability.MonteCarloSimulation') as MockSimulation:
            mock_simulation_instance = Mock()
            MockSimulation.return_value = mock_simulation_instance
            
            # Set up the mock simulation to return predefined results
            mock_simulation_instance.run_simulation.return_value = {
                "goal_amount": sample_goal.target_amount,
                "goal_timeline_years": 20,
                "simulation_results": np.random.normal(1200000, 300000, 1000),
                "success_probability": 0.75,
                "percentiles": {
                    "10": 800000,
                    "25": 950000,
                    "50": 1150000,
                    "75": 1350000,
                    "90": 1500000
                },
                "goal_achievement_timeline": {
                    "years": 18,
                    "months": 4
                }
            }
            
            # Analyze goal probability
            result = analyzer.analyze_goal_probability(sample_goal, sample_profile)
            
            # Verify that the result structure is correct
            assert isinstance(result, GoalProbabilityResult)
            assert hasattr(result, 'goal_id')
            assert hasattr(result, 'success_probability')
            assert hasattr(result, 'outcome_distribution')
            assert hasattr(result, 'timeline_assessment')
            
            # Verify that the goal id matches
            assert result.goal_id == sample_goal.id
            
            # Verify that the success probability is set
            assert result.success_probability == 0.75
            
            # Verify that the simulation was called with the correct parameters
            MockSimulation.assert_called_once()
            assert mock_simulation_instance.run_simulation.called
    
    def test_goal_outcome_distribution(self, sample_goal, sample_profile, mock_parameter_service):
        """Test goal outcome distribution with various statistical metrics"""
        # Create analyzer with mocked parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Generate mock simulation results
        simulation_results = np.random.normal(1200000, 300000, 1000)
        
        # Create a mock OutcomeDistribution object
        with patch('models.goal_probability.OutcomeDistribution') as MockDistribution:
            mock_distribution = Mock()
            MockDistribution.return_value = mock_distribution
            
            # Set up the distribution methods
            mock_distribution.calculate_percentiles.return_value = {
                "10": 800000,
                "25": 950000,
                "50": 1150000,
                "75": 1350000,
                "90": 1500000
            }
            mock_distribution.calculate_mean.return_value = 1200000
            mock_distribution.calculate_median.return_value = 1150000
            mock_distribution.calculate_std_dev.return_value = 300000
            
            # Create a probability result with the mock distribution
            result = GoalProbabilityResult(
                goal_id=sample_goal.id,
                success_probability=0.75,
                outcome_distribution=mock_distribution,
                timeline_assessment={
                    "expected_years": 18,
                    "expected_months": 4,
                    "probability_by_year": {
                        "15": 0.3,
                        "18": 0.6,
                        "20": 0.75,
                        "22": 0.85
                    }
                }
            )
            
            # Verify distribution methods are called and return expected values
            assert result.outcome_distribution.calculate_percentiles() == {
                "10": 800000,
                "25": 950000,
                "50": 1150000,
                "75": 1350000,
                "90": 1500000
            }
            assert result.outcome_distribution.calculate_mean() == 1200000
            assert result.outcome_distribution.calculate_median() == 1150000
            assert result.outcome_distribution.calculate_std_dev() == 300000
    
    def test_time_based_probability_assessment(self, sample_goal, sample_profile, mock_parameter_service):
        """Test probability evolution over time"""
        # Create analyzer with mocked parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Mock the MonteCarloSimulation
        with patch('models.goal_probability.MonteCarloSimulation') as MockSimulation:
            mock_simulation_instance = Mock()
            MockSimulation.return_value = mock_simulation_instance
            
            # Set up the mock simulation with time-based probabilities
            mock_simulation_instance.run_simulation.return_value = {
                "goal_amount": sample_goal.target_amount,
                "goal_timeline_years": 20,
                "simulation_results": np.random.normal(1200000, 300000, 1000),
                "success_probability": 0.75,
                "percentiles": {
                    "10": 800000,
                    "25": 950000,
                    "50": 1150000,
                    "75": 1350000,
                    "90": 1500000
                },
                "goal_achievement_timeline": {
                    "years": 18,
                    "months": 4
                },
                "probability_by_year": {
                    "15": 0.3,
                    "18": 0.6,
                    "20": 0.75,
                    "22": 0.85,
                    "25": 0.92
                }
            }
            
            # Analyze goal probability
            result = analyzer.analyze_goal_probability(sample_goal, sample_profile)
            
            # Verify timeline assessment is included
            assert hasattr(result, 'timeline_assessment')
            assert "probability_by_year" in result.timeline_assessment
            
            # Verify probability increases over time
            prob_by_year = result.timeline_assessment["probability_by_year"]
            assert prob_by_year["15"] < prob_by_year["18"] < prob_by_year["20"] < prob_by_year["22"]
    
    def test_goal_specific_probability_analysis(self, sample_goals, sample_profile, mock_parameter_service):
        """Test probability analysis for each major goal type"""
        # Create analyzer with mocked parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Mock the MonteCarloSimulation to avoid actual simulation
        with patch('models.goal_probability.MonteCarloSimulation') as MockSimulation:
            mock_simulation_instance = Mock()
            MockSimulation.return_value = mock_simulation_instance
            
            # Analyze each goal type
            for goal in sample_goals:
                # Set up different simulation results based on goal type
                if goal.type == "retirement":
                    success_prob = 0.65
                elif goal.type == "emergency_fund":
                    success_prob = 0.95
                elif goal.type == "education":
                    success_prob = 0.80
                elif goal.type == "home":
                    success_prob = 0.70
                else:  # discretionary
                    success_prob = 0.90
                
                # Configure the mock simulation for this goal type
                mock_simulation_instance.run_simulation.return_value = {
                    "goal_amount": goal.target_amount,
                    "goal_timeline_years": (goal.target_date.year - date.today().year),
                    "simulation_results": np.random.normal(goal.target_amount * 1.2, goal.target_amount * 0.3, 1000),
                    "success_probability": success_prob,
                    "percentiles": {
                        "10": goal.target_amount * 0.8,
                        "25": goal.target_amount * 0.95,
                        "50": goal.target_amount * 1.15,
                        "75": goal.target_amount * 1.35,
                        "90": goal.target_amount * 1.5
                    },
                    "goal_achievement_timeline": {
                        "years": (goal.target_date.year - date.today().year) - 2,
                        "months": 5
                    }
                }
                
                # Analyze this goal
                result = analyzer.analyze_goal_probability(goal, sample_profile)
                
                # Verify the result
                assert result.goal_id == goal.id
                assert result.success_probability == success_prob
                assert hasattr(result, 'outcome_distribution')
                assert hasattr(result, 'timeline_assessment')
    
    def test_probability_result_structure(self, sample_goal, sample_profile, mock_parameter_service):
        """Test result structure consistency"""
        # Create analyzer with mocked parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Mock the MonteCarloSimulation to avoid actual simulation
        with patch('models.goal_probability.MonteCarloSimulation') as MockSimulation:
            mock_simulation_instance = Mock()
            MockSimulation.return_value = mock_simulation_instance
            
            # Set up the mock simulation
            mock_simulation_instance.run_simulation.return_value = {
                "goal_amount": sample_goal.target_amount,
                "goal_timeline_years": 20,
                "simulation_results": np.random.normal(1200000, 300000, 1000),
                "success_probability": 0.75,
                "percentiles": {
                    "10": 800000,
                    "25": 950000,
                    "50": 1150000,
                    "75": 1350000,
                    "90": 1500000
                },
                "goal_achievement_timeline": {
                    "years": 18,
                    "months": 4
                },
                "probability_by_year": {
                    "15": 0.3,
                    "18": 0.6,
                    "20": 0.75,
                    "22": 0.85
                }
            }
            
            # Analyze goal probability
            result = analyzer.analyze_goal_probability(sample_goal, sample_profile)
            
            # Verify the result structure
            assert result.goal_id == sample_goal.id
            assert isinstance(result.success_probability, float)
            assert isinstance(result.timeline_assessment, dict)
            assert "expected_years" in result.timeline_assessment
            assert "expected_months" in result.timeline_assessment
            assert "probability_by_year" in result.timeline_assessment
            
            # Verify result can be converted to dictionary
            result_dict = result.to_dict()
            assert isinstance(result_dict, dict)
            assert "goal_id" in result_dict
            assert "success_probability" in result_dict
            assert "outcome_distribution" in result_dict
            assert "timeline_assessment" in result_dict
            
            # Verify dictionary has the correct values
            assert result_dict["goal_id"] == sample_goal.id
            assert result_dict["success_probability"] == 0.75
    
    def test_with_various_market_conditions(self, sample_goal, sample_profile, mock_parameter_service):
        """Test probability analysis with different market conditions"""
        # Create analyzer with mocked parameter service
        analyzer = GoalProbabilityAnalyzer(parameter_service=mock_parameter_service)
        
        # Mock the MonteCarloSimulation
        with patch('models.goal_probability.MonteCarloSimulation') as MockSimulation:
            mock_simulation_instance = Mock()
            MockSimulation.return_value = mock_simulation_instance
            
            # Define different market conditions
            market_conditions = [
                {
                    "name": "Bullish Market",
                    "returns": {
                        "equity": 0.15,
                        "debt": 0.09,
                        "gold": 0.08,
                        "cash": 0.045
                    },
                    "expected_probability": 0.85
                },
                {
                    "name": "Bearish Market",
                    "returns": {
                        "equity": 0.07,
                        "debt": 0.06,
                        "gold": 0.09,
                        "cash": 0.04
                    },
                    "expected_probability": 0.55
                },
                {
                    "name": "Sideways Market",
                    "returns": {
                        "equity": 0.10,
                        "debt": 0.07,
                        "gold": 0.07,
                        "cash": 0.04
                    },
                    "expected_probability": 0.70
                }
            ]
            
            # Test with each market condition
            for condition in market_conditions:
                # Update the mock parameter service
                mock_parameter_service.get_return_assumptions.return_value = condition["returns"]
                
                # Configure the mock simulation for this market condition
                mock_simulation_instance.run_simulation.return_value = {
                    "goal_amount": sample_goal.target_amount,
                    "goal_timeline_years": 20,
                    "simulation_results": np.random.normal(1200000, 300000, 1000),
                    "success_probability": condition["expected_probability"],
                    "percentiles": {
                        "10": 800000,
                        "25": 950000,
                        "50": 1150000,
                        "75": 1350000,
                        "90": 1500000
                    },
                    "goal_achievement_timeline": {
                        "years": 18,
                        "months": 4
                    }
                }
                
                # Analyze goal probability with this market condition
                result = analyzer.analyze_goal_probability(sample_goal, sample_profile)
                
                # Verify the result
                assert result.success_probability == condition["expected_probability"]


# Tests for MonteCarloSimulation
class TestMonteCarloSimulation:
    """Tests for the MonteCarloSimulation class"""
    
    def test_monte_carlo_simulation_initialization(self, sample_goal, mock_parameter_service):
        """Test initialization of Monte Carlo simulation"""
        # Create simulation with default parameters
        simulation = MonteCarloSimulation(
            goal=sample_goal,
            return_assumptions=mock_parameter_service.get_return_assumptions(),
            inflation_rate=mock_parameter_service.get_inflation_assumption(),
            simulation_count=1000
        )
        
        # Verify parameters are set correctly
        assert simulation.goal == sample_goal
        assert simulation.return_assumptions == mock_parameter_service.get_return_assumptions()
        assert simulation.inflation_rate == mock_parameter_service.get_inflation_assumption()
        assert simulation.simulation_count == 1000
    
    def test_run_simulation(self, sample_goal, mock_parameter_service):
        """Test running Monte Carlo simulation"""
        # Create simulation
        simulation = MonteCarloSimulation(
            goal=sample_goal,
            return_assumptions=mock_parameter_service.get_return_assumptions(),
            inflation_rate=mock_parameter_service.get_inflation_assumption(),
            simulation_count=1000
        )
        
        # Mock the numpy random functions to avoid randomness in tests
        with patch('numpy.random.normal') as mock_normal, \
             patch('numpy.random.lognormal') as mock_lognormal:
            
            # Set up mock returns
            mock_normal.return_value = np.ones(simulation.simulation_count) * 0.1  # 10% annual returns
            mock_lognormal.return_value = np.ones((20, simulation.simulation_count)) * 1.1  # 10% annual returns
            
            # Run simulation
            result = simulation.run_simulation()
            
            # Verify result structure
            assert "goal_amount" in result
            assert "goal_timeline_years" in result
            assert "simulation_results" in result
            assert "success_probability" in result
            assert "percentiles" in result
            assert "goal_achievement_timeline" in result
            
            # Verify goal amount matches
            assert result["goal_amount"] == sample_goal.target_amount
            
            # Verify timeline is calculated correctly
            goal_years = (sample_goal.target_date.year - date.today().year)
            assert result["goal_timeline_years"] == goal_years
            
            # Verify simulation results are populated
            assert len(result["simulation_results"]) == simulation.simulation_count
    
    def test_calculate_success_probability(self, sample_goal, mock_parameter_service):
        """Test calculation of success probability"""
        # Create simulation
        simulation = MonteCarloSimulation(
            goal=sample_goal,
            return_assumptions=mock_parameter_service.get_return_assumptions(),
            inflation_rate=mock_parameter_service.get_inflation_assumption(),
            simulation_count=1000
        )
        
        # Create simulated results where 75% exceed the target
        simulated_results = np.zeros(1000)
        simulated_results[:750] = sample_goal.target_amount * 1.2  # 75% exceed target
        simulated_results[750:] = sample_goal.target_amount * 0.8  # 25% fall short
        
        # Calculate success probability
        success_prob = simulation._calculate_success_probability(
            simulated_results, sample_goal.target_amount
        )
        
        # Verify the result (should be close to 0.75)
        assert abs(success_prob - 0.75) < 0.01
    
    def test_calculate_percentiles(self, sample_goal, mock_parameter_service):
        """Test calculation of percentiles from simulation results"""
        # Create simulation
        simulation = MonteCarloSimulation(
            goal=sample_goal,
            return_assumptions=mock_parameter_service.get_return_assumptions(),
            inflation_rate=mock_parameter_service.get_inflation_assumption(),
            simulation_count=1000
        )
        
        # Create simulated results with known distribution
        simulated_results = np.linspace(500000, 1500000, 1000)  # Linear from 500k to 1.5M
        
        # Calculate percentiles
        percentiles = simulation._calculate_percentiles(simulated_results)
        
        # Verify the percentiles
        assert "10" in percentiles
        assert "25" in percentiles
        assert "50" in percentiles
        assert "75" in percentiles
        assert "90" in percentiles
        
        # Verify percentiles increase
        assert percentiles["10"] < percentiles["25"] < percentiles["50"] < percentiles["75"] < percentiles["90"]
        
        # Verify specific values (given the linear distribution)
        assert abs(percentiles["10"] - 600000) < 5000
        assert abs(percentiles["50"] - 1000000) < 5000
        assert abs(percentiles["90"] - 1400000) < 5000
    
    def test_goal_achievement_timeline(self, sample_goal, mock_parameter_service):
        """Test calculation of goal achievement timeline"""
        # Create simulation
        simulation = MonteCarloSimulation(
            goal=sample_goal,
            return_assumptions=mock_parameter_service.get_return_assumptions(),
            inflation_rate=mock_parameter_service.get_inflation_assumption(),
            simulation_count=1000
        )
        
        # Mock the simulation projection method
        with patch.object(simulation, '_project_goal_trajectory') as mock_project:
            # Set up the trajectory to reach the goal in year 18
            years = 25
            trajectory = np.zeros((years, 1000))
            for i in range(years):
                if i < 18:
                    trajectory[i] = sample_goal.target_amount * (i / 18)
                else:
                    trajectory[i] = sample_goal.target_amount * (1 + (i - 18) * 0.05)
            
            mock_project.return_value = trajectory
            
            # Calculate achievement timeline
            timeline = simulation._calculate_achievement_timeline(
                sample_goal.target_amount, years
            )
            
            # Verify timeline structure
            assert "years" in timeline
            assert "months" in timeline
            
            # Verify calculated timeline (should be close to 18 years)
            assert timeline["years"] == 18
            assert 0 <= timeline["months"] < 12