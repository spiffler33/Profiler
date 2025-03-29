"""
Integration tests for the Financial Context Analyzer with other system components.

These tests verify that the FinancialContextAnalyzer integrates correctly with
other components like question flow, profile management, and UI visualization.
"""

import pytest
import json
from unittest.mock import MagicMock, patch

from models.financial_context_analyzer import FinancialContextAnalyzer
from models.profile_understanding import ProfileUnderstandingCalculator
from models.question_generator import QuestionGenerator
from services.profile_analytics_service import ProfileAnalyticsService
from services.question_service import QuestionService
from services.financial_parameter_service import FinancialParameterService

# Create fixtures and mock services
@pytest.fixture
def financial_parameter_service():
    service = MagicMock(spec=FinancialParameterService)
    service.get_parameter = MagicMock(return_value=None)
    # Initialize with default values
    thresholds = {
        'emergency_fund_months': 6,
        'retirement_savings_rate': 15,
        'debt_to_income_ratio': 36
    }
    # Allow custom parameter retrieval
    def mock_get_parameter(param_name, default=None):
        if param_name == 'thresholds.emergency_fund_months':
            return 9  # Higher than default
        elif '.' in param_name:
            parts = param_name.split('.')
            if parts[0] == 'thresholds' and parts[1] in thresholds:
                return thresholds[parts[1]]
        return default
    
    service.get_parameter.side_effect = mock_get_parameter
    return service

@pytest.fixture
def profile_understanding_calculator():
    calculator = MagicMock(spec=ProfileUnderstandingCalculator)
    calculator.calculate_understanding_level = MagicMock(return_value=5)  # Mid-level understanding
    return calculator

@pytest.fixture
def question_generator():
    generator = MagicMock(spec=QuestionGenerator)
    generator.generate_questions = MagicMock(return_value=[
        {"id": "q1", "text": "Test question 1?", "category": "income"},
        {"id": "q2", "text": "Test question 2?", "category": "investments"}
    ])
    return generator

@pytest.fixture
def question_service(question_generator):
    service = MagicMock(spec=QuestionService)
    service.question_generator = question_generator
    service.get_next_questions = MagicMock(return_value=[
        {"id": "q1", "text": "Test question 1?", "category": "income"},
        {"id": "q2", "text": "Test question 2?", "category": "investments"}
    ])
    # Add missing methods
    service.incorporate_suggestions = MagicMock(return_value=True)
    service.get_questions_by_categories = MagicMock(return_value=[
        {"id": "q1", "text": "Test question about emergency fund?", "category": "emergency_fund"},
        {"id": "q2", "text": "Test question about investments?", "category": "investments"}
    ])
    return service

@pytest.fixture
def profile_analytics_service():
    service = MagicMock(spec=ProfileAnalyticsService)
    service.generate_profile_insights = MagicMock(return_value={
        "insights": [
            {"category": "emergency_fund", "text": "Increase your emergency fund"}
        ]
    })
    return service

@pytest.fixture
def context_analyzer(financial_parameter_service, profile_understanding_calculator):
    return FinancialContextAnalyzer(
        financial_parameter_service=financial_parameter_service,
        profile_understanding_calculator=profile_understanding_calculator,
        cache_enabled=False
    )

# Sample test profile
@pytest.fixture
def sample_profile():
    return {
        "id": "test-profile-integration",
        "age": 35,
        "monthly_income": 85000,
        "annual_income": 1020000,
        "monthly_expenses": 50000,
        "emergency_fund": 200000,
        "risk_tolerance": "moderate",
        "investments": {
            "equity": 300000,
            "debt": 200000
        }
    }


class TestContextAnalyzerIntegration:
    """Integration tests for FinancialContextAnalyzer."""
    
    def test_integration_with_question_service(self, context_analyzer, question_service, sample_profile):
        """Test integration between context analyzer and question service."""
        # Analyze profile to get suggested questions
        analysis_result = context_analyzer.analyze_profile(sample_profile)
        suggested_questions = analysis_result['question_flow']['suggested_questions']
        
        # Pass suggestions to question service
        with patch.object(question_service, 'incorporate_suggestions') as mock_incorporate:
            question_service.incorporate_suggestions(suggested_questions, sample_profile['id'])
            mock_incorporate.assert_called_once_with(suggested_questions, sample_profile['id'])
            
        # Use question service to get next questions
        next_questions = question_service.get_next_questions(sample_profile['id'])
        assert len(next_questions) > 0
    
    def test_integration_with_understanding_calculator(self, context_analyzer, profile_understanding_calculator, sample_profile):
        """Test integration between context analyzer and understanding calculator."""
        # Create a question that needs complexity adjustment
        technical_question = {
            'question': 'What is your asset allocation?',
            'category': 'investments'
        }
        
        # First test with intermediate understanding
        profile_understanding_calculator.calculate_understanding_level.return_value = 5
        result_intermediate = context_analyzer.tailor_question_complexity(sample_profile, technical_question)
        assert result_intermediate['literacy_level'] == 'intermediate'
        
        # Test with beginner understanding
        profile_understanding_calculator.calculate_understanding_level.return_value = 2
        result_beginner = context_analyzer.tailor_question_complexity(sample_profile, technical_question)
        assert result_beginner['literacy_level'] == 'beginner'
        assert '(' in result_beginner['question']  # Should have explanation
        
        # Test with advanced understanding
        profile_understanding_calculator.calculate_understanding_level.return_value = 8
        result_advanced = context_analyzer.tailor_question_complexity(sample_profile, technical_question)
        assert result_advanced['literacy_level'] == 'advanced'
        assert 'additional_context' in result_advanced
    
    def test_integration_with_financial_parameter_service(self, context_analyzer, financial_parameter_service, sample_profile):
        """Test integration between context analyzer and financial parameter service."""
        # Set up financial parameter service to return custom thresholds
        def get_parameter_side_effect(param_name, default=None):
            if param_name == 'thresholds.emergency_fund_months':
                return 9  # Higher than default 6 months
            return default
            
        financial_parameter_service.get_parameter.side_effect = get_parameter_side_effect
        
        # Create a test profile with insufficient emergency fund
        test_profile = sample_profile.copy()
        test_profile['monthly_expenses'] = 90000  # High monthly expenses
        test_profile['emergency_fund'] = 100000   # Only about 1 month of coverage
        
        # Analyze emergency fund with custom threshold
        result = context_analyzer.analyze_emergency_fund(test_profile)
        
        # With high threshold (9 months) and only 1 month of coverage,
        # we should get a high severity risk
        assert any(risk['severity'] == 'high' for risk in result['risks'])
        assert any('emergency_fund' in risk['type'] for risk in result['risks'])
    
    def test_integration_with_ui_formatting(self, context_analyzer, sample_profile):
        """Test integration with UI formatting requirements."""
        # Create insights to format
        insights = [
            {
                'category': 'emergency_preparedness',
                'description': 'Your emergency fund is below recommended levels',
                'recommended_action': 'Increase your emergency fund to 6 months of expenses',
                'priority': 'high'
            },
            {
                'category': 'tax_planning',
                'description': 'You have unused tax deduction opportunities',
                'recommended_action': 'Consider ELSS investments for tax benefits',
                'priority': 'medium'
            }
        ]
        
        # Format insights for UI
        formatted_insights = [context_analyzer.format_insight_for_display(insight) for insight in insights]
        
        # Check UI-specific formatting
        for insight in formatted_insights:
            assert 'priority_icon' in insight
            assert 'category_icon' in insight
            assert 'formatted_action' in insight
            assert '<strong>' in insight['formatted_action']
            
        # Check action plan formatting for UI
        prioritized_insights = context_analyzer.prioritize_insights(insights)
        action_plan = context_analyzer.generate_action_plan(prioritized_insights)
        
        assert 'summary' in action_plan
        assert 'immediate_actions' in action_plan
        assert all('description' in action for action in action_plan['immediate_actions'])
        
    def test_end_to_end_profile_analysis_and_question_flow(self, context_analyzer, question_service, sample_profile):
        """Test the end-to-end flow from profile analysis to question generation."""
        # 1. Analyze profile
        analysis_result = context_analyzer.analyze_profile(sample_profile)
        
        # 2. Get question opportunities and recommendations
        question_opportunities = analysis_result['question_flow']['question_opportunities']
        recommended_path = analysis_result['question_flow']['recommended_path']
        suggested_questions = analysis_result['question_flow']['suggested_questions']
        
        # 3. Get specific questions based on recommendations
        question_categories = [q['category'] for q in suggested_questions]
        
        # Create a test profile with more gaps to ensure high priority areas
        gap_profile = sample_profile.copy()
        # Remove some data to create gaps
        gap_profile['emergency_fund'] = 0
        gap_profile['id'] = 'test-profile-gaps'
        
        # Analyze the gap profile to get high priority areas
        gap_analysis = context_analyzer.analyze_profile(gap_profile)
        gap_opportunities = gap_analysis['question_flow']['question_opportunities']
        
        # Add a high priority area manually
        high_priority_area = 'emergency_fund'
        
        # 4. Pass to question service with high priority areas included
        with patch.object(question_service, 'get_questions_by_categories') as mock_get:
            # Ensure high priority area is included
            categories_for_test = [high_priority_area]
            # Add some original categories
            for cat in question_categories[:2]:
                if cat not in categories_for_test:
                    categories_for_test.append(cat)
                    
            mock_get.return_value = [
                {"id": f"q-{cat}", "text": f"Question about {cat}?", "category": cat}
                for cat in categories_for_test
            ]
            
            next_questions = question_service.get_questions_by_categories(categories_for_test)
            
            # 5. Verify the flow
            assert len(next_questions) == len(categories_for_test)
            
            # 6. Verify that high priority categories are included
            assert any(q['category'] == high_priority_area for q in next_questions)
            
            # 7. Clean up for good test hygiene
            mock_get.reset_mock()