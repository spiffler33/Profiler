"""
Test suite for Financial Context Analyzer Module

This module provides comprehensive tests for the FinancialContextAnalyzer class,
which analyzes user financial profiles and generates insights.
"""

import pytest
import json
import time
import re
from unittest.mock import MagicMock, patch
from datetime import datetime
from collections import defaultdict

# Import the class to test
from models.financial_context_analyzer import FinancialContextAnalyzer

# Test data
SAMPLE_PROFILE = {
    "id": "test-profile-123",
    "age": 35,
    "monthly_income": 85000,
    "annual_income": 1020000,
    "monthly_expenses": 50000,
    "emergency_fund": 200000,
    "job_stability": "medium",
    "dependents": 1,
    "tax_bracket": 0.3,
    "residence": {
        "monthly_rent": 22000,
        "city_tier": 1,
        "city_type": "metro"
    },
    "income_details": {
        "basic_salary": 50000,
        "hra": 20000
    },
    "investments": {
        "equity": 300000,
        "debt": 200000,
        "gold": 50000,
        "real_estate": 0,
        "tax_efficient": 150000
    },
    "asset_allocation": {
        "equity": 0.55,
        "debt": 0.35,
        "gold": 0.10,
        "real_estate": 0
    },
    "retirement_investments": {
        "nps_tier1_annual": 50000,
        "ppf_annual": 100000
    },
    "insurance": {
        "health": {
            "coverage": 300000,
            "family_covered": True,
            "critical_illness_rider": False
        },
        "life": {
            "coverage": 5000000
        },
        "property": {
            "coverage": 0
        }
    },
    "debts": {
        "home_loan": {
            "balance": 2000000,
            "interest_rate": 8.5,
            "monthly_payment": 20000
        },
        "personal_loan": {
            "balance": 100000,
            "interest_rate": 14,
            "monthly_payment": 5000
        }
    },
    "assets": {
        "liquid": 250000,
        "investments": 550000,
        "real_estate": 0,
        "vehicles": 500000
    },
    "goals": [
        {
            "id": "goal-1",
            "name": "Retirement",
            "type": "retirement",
            "target_amount": 30000000,
            "target_year": 2050,
            "monthly_funding": 15000,
            "priority": 5
        },
        {
            "id": "goal-2",
            "name": "Home Purchase",
            "type": "home",
            "target_amount": 8000000,
            "target_year": 2030,
            "monthly_funding": 20000,
            "priority": 4
        }
    ],
    "tax_deductions": {
        "section_80c": {
            "elss": 50000,
            "ppf": 100000,
            "tax_saving_fd": 0,
            "others": 0
        }
    },
    "monthly_savings_capacity": 30000,
    "risk_tolerance": "moderate"
}

# Configure mocks with appropriate return values
MOCK_FINANCIAL_PARAMETER_SERVICE = MagicMock()
MOCK_FINANCIAL_PARAMETER_SERVICE.get_parameter = MagicMock(return_value=None)

# Setup mock to return actual values when needed
def mock_get_parameter(param_name, default=None):
    if param_name == 'thresholds.emergency_fund_months':
        return 6  # Default emergency fund months
    elif param_name == 'thresholds.debt_burden_ratio':
        return 0.36  # Default debt burden ratio
    elif param_name == 'thresholds.retirement_savings_rate':
        return 0.15  # Default retirement savings rate
    return default

MOCK_FINANCIAL_PARAMETER_SERVICE.get_parameter.side_effect = mock_get_parameter
MOCK_PROFILE_MANAGER = MagicMock()
MOCK_PROFILE_UNDERSTANDING_CALCULATOR = MagicMock()

@pytest.fixture
def financial_context_analyzer():
    """Create a FinancialContextAnalyzer instance for testing."""
    return FinancialContextAnalyzer(
        financial_parameter_service=MOCK_FINANCIAL_PARAMETER_SERVICE,
        profile_manager=MOCK_PROFILE_MANAGER,
        profile_understanding_calculator=MOCK_PROFILE_UNDERSTANDING_CALCULATOR,
        cache_enabled=False
    )

class TestFinancialContextAnalyzer:
    """Tests for FinancialContextAnalyzer."""

    def test_initialization(self, financial_context_analyzer):
        """Test that the analyzer initializes correctly with dependencies."""
        assert financial_context_analyzer.financial_parameter_service == MOCK_FINANCIAL_PARAMETER_SERVICE
        assert financial_context_analyzer.profile_manager == MOCK_PROFILE_MANAGER
        assert financial_context_analyzer.profile_understanding_calculator == MOCK_PROFILE_UNDERSTANDING_CALCULATOR
        assert financial_context_analyzer.cache_enabled is False
        assert isinstance(financial_context_analyzer.thresholds, dict)
        assert isinstance(financial_context_analyzer.wellness_category_weights, dict)

    def test_analyze_profile_basic(self, financial_context_analyzer):
        """Test the high-level analyze_profile method returns expected structure."""
        result = financial_context_analyzer.analyze_profile(SAMPLE_PROFILE)
        
        # Check overall structure
        assert 'profile_id' in result
        assert 'analyses' in result
        assert 'opportunities' in result
        assert 'risks' in result
        assert 'insights' in result
        assert isinstance(result['insights'], dict)
        assert 'action_plan' in result
        assert 'question_flow' in result
        assert 'financial_wellness_score' in result
        assert 'analysis_version' in result
        assert 'processing_time_seconds' in result
        assert 'timestamp' in result
        
        # Check profile ID
        assert result['profile_id'] == SAMPLE_PROFILE['id']
        
        # Check analyses contain all expected modules
        assert 'tax_efficiency' in result['analyses']
        assert 'emergency_fund' in result['analyses']
        assert 'debt_burden' in result['analyses']
        assert 'investment_allocation' in result['analyses']
        assert 'insurance_coverage' in result['analyses']
        assert 'goal_conflicts' in result['analyses']
        assert 'hra_optimization' in result['analyses']
        assert 'retirement_tax_benefits' in result['analyses']
        assert 'section_80c_optimization' in result['analyses']
        assert 'health_insurance_adequacy' in result['analyses']
        
        # Check action plan structure
        assert 'immediate_actions' in result['action_plan']
        assert 'short_term_actions' in result['action_plan']
        assert 'long_term_actions' in result['action_plan']
        assert 'summary' in result['action_plan']
        
        # Check question flow structure
        assert 'suggested_questions' in result['question_flow']
        assert 'question_opportunities' in result['question_flow']
        assert 'recommended_path' in result['question_flow']
        
        # Check wellness score structure
        assert 'overall_score' in result['financial_wellness_score']
        assert 'category_scores' in result['financial_wellness_score']
        assert 'interpretation' in result['financial_wellness_score']

    def test_analyze_emergency_fund(self, financial_context_analyzer):
        """Test the emergency fund analysis module."""
        result = financial_context_analyzer.analyze_emergency_fund(SAMPLE_PROFILE)
        
        assert 'score' in result
        assert 'opportunities' in result
        assert 'risks' in result
        assert 'insights' in result
        assert 'suggested_questions' in result
        
        # Based on our sample data (emergency fund of 200,000 and monthly expenses of 50,000)
        # Emergency fund covers 4 months, which is below the 6-month threshold
        assert result['score'] < 100  # Score should reflect inadequate emergency fund
        assert any('insufficient_emergency_fund' in risk['type'] for risk in result['risks'])
        assert any('build_emergency_fund' in opportunity['type'] for opportunity in result['opportunities'])

    def test_analyze_debt_burden(self, financial_context_analyzer):
        """Test the debt burden analysis module."""
        result = financial_context_analyzer.analyze_debt_burden(SAMPLE_PROFILE)
        
        assert 'score' in result
        assert 'opportunities' in result
        assert 'risks' in result
        
        # Sample profile has high-interest personal loan (14%)
        assert any('high_interest_debt' in opportunity['type'] for opportunity in result['opportunities'])
        
        # Check debt-to-income ratio analysis
        # Monthly debt payments = 25000, monthly income = 85000
        # Ratio = 0.29, which is below the 0.40 threshold
        debt_to_income = sum(debt.get('monthly_payment', 0) for debt in SAMPLE_PROFILE['debts'].values()) / SAMPLE_PROFILE['monthly_income']
        assert debt_to_income < financial_context_analyzer.thresholds['debt_burden_ratio']
        
        # Verify high-interest debt detection
        high_interest_debts = [debt for name, debt in SAMPLE_PROFILE['debts'].items() 
                              if debt.get('interest_rate', 0) > 12]
        assert len(high_interest_debts) > 0  # Sample has one high-interest debt

    def test_analyze_investment_allocation(self, financial_context_analyzer):
        """Test the investment allocation analysis module."""
        result = financial_context_analyzer.analyze_investment_allocation(SAMPLE_PROFILE)
        
        assert 'score' in result
        
        # Check age-appropriate equity allocation
        # Using 100-age rule with risk adjustments
        age = SAMPLE_PROFILE['age']
        risk_tolerance = SAMPLE_PROFILE['risk_tolerance']
        
        # Calculate expected target equity percentage
        base_target = 100 - age  # 100 - 35 = 65
        risk_adjustments = {'conservative': -15, 'moderate': 0, 'aggressive': 15}
        expected_target = base_target + risk_adjustments.get(risk_tolerance, 0)
        expected_target = max(20, min(90, expected_target))  # Constrain between 20-90%
        
        # Current equity allocation is 55%
        current_equity = SAMPLE_PROFILE['asset_allocation']['equity'] * 100
        
        # Check if analysis correctly identifies the gap
        equity_diff = abs(current_equity - expected_target)
        if equity_diff > 15:
            assert any('inappropriate_equity_allocation' in risk['type'] for risk in result['risks'])

    def test_analyze_tax_efficiency(self, financial_context_analyzer):
        """Test the tax efficiency analysis module."""
        result = financial_context_analyzer.analyze_tax_efficiency(SAMPLE_PROFILE)
        
        assert 'score' in result
        assert 'opportunities' in result
        
        # Tax-efficient investments = 150,000, Total investments = 550,000
        # Efficiency ratio = 27.3%
        tax_efficient = SAMPLE_PROFILE['investments'].get('tax_efficient', 0)
        total_investments = sum(SAMPLE_PROFILE['investments'].values())
        expected_score = int((tax_efficient / total_investments) * 100) if total_investments > 0 else 0
        
        # Allow for small differences due to rounding or calculation methods
        assert abs(result['score'] - expected_score) <= 5

    def test_categorize_insights(self, financial_context_analyzer):
        """Test the insight categorization functionality."""
        # Create test insights
        insights = [
            {'category': 'emergency_preparedness', 'description': 'Test insight 1'},
            {'category': 'tax_planning', 'description': 'Test insight 2'},
            {'category': 'tax_planning', 'description': 'Test insight 3'},
            {'category': 'retirement_planning', 'description': 'Test insight 4'},
            {'category': 'debt_management', 'description': 'Test insight 5'},
            {'description': 'Test insight with no category'}  # Missing category
        ]
        
        categorized = financial_context_analyzer.categorize_insights(insights)
        
        # Check structure
        assert isinstance(categorized, dict)
        assert 'tax_planning' in categorized
        assert 'emergency_preparedness' in categorized
        assert 'retirement_planning' in categorized
        assert 'debt_management' in categorized
        assert 'general' in categorized  # Default category
        
        # Check counts
        assert len(categorized['tax_planning']) == 2
        assert len(categorized['emergency_preparedness']) == 1
        assert len(categorized['retirement_planning']) == 1
        assert len(categorized['debt_management']) == 1
        assert len(categorized['general']) == 1  # For the insight without category

    def test_prioritize_insights(self, financial_context_analyzer):
        """Test the insight prioritization functionality."""
        # Create test insights with different priorities
        insights = [
            {'category': 'emergency_preparedness', 'description': 'Critical insight', 'priority': 'high'},
            {'category': 'tax_planning', 'description': 'Important insight', 'priority': 'medium'},
            {'category': 'tax_planning', 'description': 'Optional insight', 'priority': 'low'},
            {'category': 'retirement_planning', 'description': 'Default priority insight'}  # No priority specified
        ]
        
        prioritized = financial_context_analyzer.prioritize_insights(insights)
        
        # Check structure
        assert isinstance(prioritized, list)
        assert len(prioritized) == len(insights)
        
        # Check that all insights have priority scores
        for insight in prioritized:
            assert 'priority_score' in insight
            
        # Check sorting order (highest priority first)
        for i in range(len(prioritized) - 1):
            assert prioritized[i]['priority_score'] >= prioritized[i+1]['priority_score']
            
        # Check high priority item is first
        assert prioritized[0]['priority'] == 'high'
        assert prioritized[0]['category'] == 'emergency_preparedness'

    def test_format_insight_for_display(self, financial_context_analyzer):
        """Test the formatting of insights for display."""
        # Create a test insight
        insight = {
            'category': 'emergency_preparedness',
            'description': 'You need a larger emergency fund',
            'recommended_action': 'Increase your emergency fund to cover 6 months of expenses',
            'priority': 'high'
        }
        
        formatted = financial_context_analyzer.format_insight_for_display(insight)
        
        # Check that formatting was applied
        assert 'priority_icon' in formatted
        assert 'category_icon' in formatted
        assert 'formatted_description' in formatted
        assert 'formatted_action' in formatted
        
        # Check that HTML formatting was applied to action
        assert '<strong>' in formatted['formatted_action']
        assert '</strong>' in formatted['formatted_action']
        
        # Check that appropriate icons were selected
        assert formatted['priority_icon'] == '🔴'  # High priority red icon
        assert formatted['category_icon'] == '🚨'  # Emergency preparedness icon

    def test_generate_action_plan(self, financial_context_analyzer):
        """Test the action plan generation functionality."""
        # Create prioritized insights
        insights = [
            {'recommended_action': 'Action 1', 'category': 'emergency_preparedness', 'priority': 'high', 'priority_score': 90},
            {'recommended_action': 'Action 2', 'category': 'tax_planning', 'priority': 'medium', 'priority_score': 70},
            {'recommended_action': 'Action 3', 'category': 'retirement_planning', 'priority': 'low', 'priority_score': 40},
            {'recommended_action': 'Action 4', 'category': 'debt_management', 'priority': 'high', 'priority_score': 85}
        ]
        
        # Set thresholds for testing
        financial_context_analyzer.thresholds['high_priority_score_threshold'] = 80
        financial_context_analyzer.thresholds['medium_priority_score_threshold'] = 60
        
        action_plan = financial_context_analyzer.generate_action_plan(insights)
        
        # Check structure
        assert 'immediate_actions' in action_plan
        assert 'short_term_actions' in action_plan
        assert 'long_term_actions' in action_plan
        assert 'summary' in action_plan
        assert 'top_priorities' in action_plan
        assert 'generated_at' in action_plan
        
        # Check action categorization
        assert len(action_plan['immediate_actions']) == 2  # Score >= 80
        assert len(action_plan['short_term_actions']) == 1  # 60 <= Score < 80
        assert len(action_plan['long_term_actions']) == 1  # Score < 60
        
        # Check top priorities (first 3 from insights)
        assert len(action_plan['top_priorities']) == 3
        assert 'Action 1' in action_plan['top_priorities']
        
        # Check summary format
        assert str(len(action_plan['immediate_actions'])) in action_plan['summary']
        assert str(len(action_plan['short_term_actions'])) in action_plan['summary']
        assert str(len(action_plan['long_term_actions'])) in action_plan['summary']

    def test_identify_question_opportunities(self, financial_context_analyzer):
        """Test the identification of missing information opportunities."""
        # Create a profile with missing data
        incomplete_profile = {
            "id": "incomplete-profile",
            "age": 35,
            "monthly_income": 85000,  # Has income
            # Missing: emergency_fund, investments, insurance, etc.
        }
        
        opportunities = financial_context_analyzer.identify_question_opportunities(incomplete_profile)
        
        # Check structure
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        
        # Check that each opportunity has required fields
        for opportunity in opportunities:
            assert 'area' in opportunity
            assert 'missing_fields' in opportunity
            assert 'completeness' in opportunity
            assert 'importance' in opportunity
            
        # Check specific areas are identified as missing
        areas = [opp['area'] for opp in opportunities]
        assert 'emergency_fund' in areas
        assert 'insurance' in areas
        assert 'investments' in areas
        
        # Check emergency fund is high importance
        emergency_opp = next((opp for opp in opportunities if opp['area'] == 'emergency_fund'), None)
        assert emergency_opp is not None
        assert emergency_opp['importance'] == 'high'
        assert emergency_opp['completeness'] == 0  # Completely missing

    def test_generate_question_suggestions(self, financial_context_analyzer):
        """Test generating question suggestions based on profile gaps."""
        # Create a profile with specific gaps
        profile_with_gaps = {
            "id": "profile-with-gaps",
            "age": 35,
            "monthly_income": 85000,  # Has income
            # Missing: emergency_fund, investments, insurance, etc.
        }
        
        suggestions = financial_context_analyzer.generate_question_suggestions(profile_with_gaps)
        
        # Check structure
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert len(suggestions) <= 10  # Should limit to 10 questions
        
        # Check that each suggestion has required fields
        for suggestion in suggestions:
            assert 'question' in suggestion
            assert 'importance' in suggestion
            assert 'category' in suggestion
            assert 'reason' in suggestion
            
        # Check for expected questions about missing information
        questions = [q['question'] for q in suggestions]
        categories = [q['category'] for q in suggestions]
        
        # Should ask about emergency fund
        assert any('emergency' in q.lower() for q in questions)
        assert 'emergency_fund' in categories
        
        # Should ask about insurance
        assert any('insurance' in q.lower() for q in questions)
        assert 'insurance' in categories

    def test_calculate_financial_wellness_score(self, financial_context_analyzer):
        """Test calculation of financial wellness score."""
        # Create mock analysis results
        analyses = {
            'emergency_fund': {'score': 40},  # Below threshold (poor)
            'debt_burden': {'score': 70},     # Moderate
            'tax_efficiency': {'score': 80},  # Good
            'insurance_coverage': {'score': 60},  # Moderate
            'investment_allocation': {'score': 75},  # Good
            'retirement_tax_benefits': {'score': 90}  # Excellent
        }
        
        wellness = financial_context_analyzer.calculate_financial_wellness_score(SAMPLE_PROFILE, analyses)
        
        # Check structure
        assert 'overall_score' in wellness
        assert 'category_scores' in wellness
        assert 'interpretation' in wellness
        assert 'strengths' in wellness
        assert 'improvement_areas' in wellness
        
        # Check calculations
        assert wellness['overall_score'] > 0
        assert wellness['overall_score'] <= 100
        
        # Check interpretation (depends on thresholds)
        assert wellness['interpretation'] in ["Excellent financial health", "Good financial health", 
                                            "Fair financial health", "Needs attention"]
        
        # Check correct identification of strengths (high scores)
        assert 'retirement_tax_benefits' in wellness['strengths']
        
        # Check correct identification of improvement areas (low scores with significant weight)
        assert 'emergency_fund' in wellness['improvement_areas']

    def test_suggest_question_path(self, financial_context_analyzer):
        """Test the question path recommendation functionality."""
        # Create a profile with specific gaps in foundation areas
        profile_with_foundation_gaps = {
            "id": "profile-with-gaps",
            "age": 35,
            "monthly_income": 85000,  # Has income
            # Missing: emergency_fund, debts, expenses, etc.
        }
        
        # Create predefined opportunities for testing
        opportunities = [
            {
                'area': 'emergency_fund',
                'missing_fields': ['emergency_fund', 'liquid_assets'],
                'completeness': 0.0,
                'importance': 'high',
                'has_some_data': False
            },
            {
                'area': 'investments',
                'missing_fields': ['investments', 'asset_allocation'],
                'completeness': 0.0,
                'importance': 'medium',
                'has_some_data': False
            },
            {
                'area': 'debt',
                'missing_fields': ['debts', 'debt_interest_rates', 'debt_monthly_payments'],
                'completeness': 0.0,
                'importance': 'high',
                'has_some_data': False
            }
        ]
        
        recommendation = financial_context_analyzer.suggest_question_path(
            profile_with_foundation_gaps, 
            question_opportunities=opportunities
        )
        
        # Check structure
        assert 'paths' in recommendation
        assert 'recommended_path' in recommendation
        assert 'recommended_questions' in recommendation
        assert 'next_steps' in recommendation
        
        # Check paths are identified correctly
        assert 'foundation' in recommendation['paths']
        assert 'foundation' == recommendation['recommended_path']  # Should prioritize foundation
        
        # Check foundation path includes correct areas
        foundation_path = recommendation['paths']['foundation']
        assert 'missing_areas' in foundation_path
        assert 'emergency_fund' in foundation_path['missing_areas']
        assert 'debt' in foundation_path['missing_areas']
        
        # Check next steps guidance
        assert "foundation" in recommendation['next_steps'].lower()

    def test_tailor_question_complexity(self, financial_context_analyzer):
        """Test the question complexity tailoring functionality."""
        # Test for beginner user
        financial_context_analyzer.profile_understanding_calculator.calculate_understanding_level = MagicMock(return_value=2)
        
        # Create a question with technical terms
        technical_question = {
            'question': 'What is your asset allocation for retirement?',
            'category': 'investments',
            'importance': 'medium'
        }
        
        beginner_result = financial_context_analyzer.tailor_question_complexity(SAMPLE_PROFILE, technical_question)
        
        # Should add explanations for beginners
        assert 'literacy_level' in beginner_result
        assert beginner_result['literacy_level'] == 'beginner'
        assert 'asset allocation' in beginner_result['question']
        assert '(' in beginner_result['question']  # Should have explanation in parentheses
        
        # Test for advanced user
        financial_context_analyzer.profile_understanding_calculator.calculate_understanding_level = MagicMock(return_value=8)
        
        advanced_result = financial_context_analyzer.tailor_question_complexity(SAMPLE_PROFILE, technical_question)
        
        # Should add context for advanced users
        assert 'literacy_level' in advanced_result
        assert advanced_result['literacy_level'] == 'advanced'
        assert 'additional_context' in advanced_result  # Should provide additional context
        
    def test_caching(self):
        """Test that caching works correctly."""
        # Create analyzer with caching enabled
        analyzer = FinancialContextAnalyzer(
            financial_parameter_service=MOCK_FINANCIAL_PARAMETER_SERVICE,
            profile_manager=MOCK_PROFILE_MANAGER,
            cache_enabled=True
        )
        
        # Manually call the methods that would be called by analyze_emergency_fund
        profile_id = SAMPLE_PROFILE['id']
        analysis_type = 'emergency_fund'
        
        # Test getting from cache (not found)
        result = analyzer._get_from_cache(profile_id, analysis_type)
        assert result is None
        
        # Test storing in cache
        test_data = {'score': 85, 'test': True}
        analyzer._store_in_cache(profile_id, analysis_type, test_data)
        
        # Check cache key
        cache_key = analyzer._get_cache_key(profile_id, analysis_type)
        assert cache_key in analyzer._cache
        
        # Test getting cached data
        result = analyzer._get_from_cache(profile_id, analysis_type)
        assert result == test_data
                
        # Test cache clearing
        analyzer._cache = {'test-profile-123:emergency_fund': {'data': {}, 'timestamp': time.time()}}
        analyzer.clear_cache('test-profile-123')
        assert 'test-profile-123:emergency_fund' not in analyzer._cache
        
    def test_error_handling(self, financial_context_analyzer):
        """Test error handling in the analyze_profile method."""
        # Create a MagicMock that raises an exception
        with patch.object(financial_context_analyzer, 'analyze_tax_efficiency', 
                         side_effect=Exception("Test exception")):
            result = financial_context_analyzer.analyze_profile(SAMPLE_PROFILE)
            
            # Check error structure
            assert 'error' in result
            assert 'status' in result
            assert result['status'] == 'error'
            assert 'Test exception' in result['error']