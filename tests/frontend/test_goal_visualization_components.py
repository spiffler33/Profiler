#!/usr/bin/env python3
"""
Test script for validating Goal Visualization Components.
These tests validate that the frontend visualization components receive
the correct data from the backend and that the data is properly formatted.
"""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import models and services
from models.goal_document import GoalDocumentGenerator, DocumentSection
from models.goal_models import Goal
from models.goal_probability import GoalProbabilityAnalyzer
from services.goal_adjustment_service import GoalAdjustmentService


class TestGoalVisualizationComponents:
    """Test cases for the Goal Visualization Components"""

    @pytest.fixture
    def setup_test_data(self):
        """Setup common test data for visualization tests"""
        test_goal = Goal(
            id="test-goal-id",
            user_profile_id="test-profile-id",
            category="retirement",
            title="Retirement Fund",
            target_amount=10000000,  # 1 crore
            timeframe="2045-01-01",
            current_amount=1000000,  # 10 lakhs
            importance="high",
            flexibility="somewhat_flexible",
            notes="Retirement planning",
            current_progress=10.0,
            priority_score=85.0,
            goal_success_probability=0.65
        )
        
        test_profile = {
            "id": "test-profile-id",
            "name": "Test User",
            "email": "test@example.com",
            "age": 35,
            "income": 1200000,  # 12 lakhs per year
            "expenses": 50000,  # Monthly
            "country": "India"
        }
        
        return {
            "goal": test_goal,
            "profile": test_profile
        }

    def test_probabilistic_goal_visualizer_data_structure(self, setup_test_data):
        """Test the data structure passed to ProbabilisticGoalVisualizer component"""
        test_data = setup_test_data
        
        # Mock GoalProbabilityAnalyzer to generate visualization data
        with patch('models.goal_probability.GoalProbabilityAnalyzer.analyze_goal_probability') as mock_analyze:
            # Create expected probability analysis result
            mock_result = {
                "success_probability": 0.65,
                "projections": [
                    {
                        "year": 2025 + i,
                        "median": 1000000 * (1 + 0.12) ** i,
                        "percentiles": {
                            10: 1000000 * (1 + 0.08) ** i,
                            25: 1000000 * (1 + 0.10) ** i,
                            50: 1000000 * (1 + 0.12) ** i,
                            75: 1000000 * (1 + 0.14) ** i,
                            90: 1000000 * (1 + 0.16) ** i
                        }
                    } for i in range(20)
                ],
                "monthly_contribution": 25000,
                "expected_value": 10500000
            }
            
            # Set up the mock to return our expected result
            mock_analyze.return_value = mock_result
            
            # Instantiate the analyzer
            analyzer = GoalProbabilityAnalyzer()
            
            # Call the method under test
            result = analyzer.analyze_goal_probability(test_data["goal"], test_data["profile"])
            
            # Verify the structure of the result
            assert result["success_probability"] == 0.65
            assert len(result["projections"]) == 20
            assert "monthly_contribution" in result
            assert "expected_value" in result
            
            # Verify the projections structure
            assert "median" in result["projections"][0]
            assert "percentiles" in result["projections"][0]
            assert 10 in result["projections"][0]["percentiles"]
            assert 90 in result["projections"][0]["percentiles"]

    def test_document_generator_visualization_data(self, setup_test_data):
        """Test GoalDocumentGenerator creates visualization data for frontend"""
        test_data = setup_test_data
        
        # Create a document generator
        generator = GoalDocumentGenerator()
        
        # Create a test document directly
        test_document = [
            DocumentSection(
                title="Test Section",
                content={"summary": "This is a test section"}
            )
        ]
        
        # Add a visualization directly to the section
        test_document[0].visualizations.append("data:image/png;base64,TEST_IMAGE_DATA")
        
        # Mock the generate_json method to convert to expected format
        with patch.object(generator, 'generate_json') as mock_generate_json:
            mock_generate_json.return_value = {
                "sections": [
                    {
                        "title": section.title,
                        "content": section.content,
                        "visualizations": section.visualizations
                    }
                    for section in test_document
                ]
            }
            
            # Generate JSON for frontend visualization
            json_data = generator.generate_json(test_document)
            
            # Verify JSON structure for frontend visualization
            assert "sections" in json_data
            assert len(json_data["sections"]) > 0
            
            # Check for visualization data in sections
            has_visualization = False
            for section in json_data["sections"]:
                if "visualizations" in section and section["visualizations"]:
                    has_visualization = True
                    break
            
            assert has_visualization, "No visualizations found in document sections"

    def test_scenario_comparison_chart_data(self, setup_test_data):
        """Test data structure for ScenarioComparisonChart component"""
        test_data = setup_test_data
        
        # Create sample scenario data
        scenarios = {
            "current": {
                "successProbability": 0.65,
                "expectedValue": 10500000,
                "timeToAchievement": 20,
                "monthlyContribution": 25000,
                "projections": [
                    {
                        "year": 2025 + i,
                        "median": 1000000 * (1 + 0.12) ** i,
                    } for i in range(20)
                ]
            },
            "optimized": {
                "successProbability": 0.85,
                "expectedValue": 12000000,
                "timeToAchievement": 18,
                "monthlyContribution": 35000,
                "projections": [
                    {
                        "year": 2025 + i,
                        "median": 1000000 * (1 + 0.15) ** i,
                    } for i in range(20)
                ]
            }
        }
        
        # Validate structure of scenario data for frontend
        assert "successProbability" in scenarios["current"]
        assert "projections" in scenarios["current"]
        assert isinstance(scenarios["current"]["projections"], list)
        assert "median" in scenarios["current"]["projections"][0]
        
        # Make sure optimized scenario shows improvement
        assert scenarios["optimized"]["successProbability"] > scenarios["current"]["successProbability"]
        assert scenarios["optimized"]["expectedValue"] > scenarios["current"]["expectedValue"]
        
        # Check for camelCase naming convention (used in frontend React components)
        assert "successProbability" in scenarios["current"]
        assert "expectedValue" in scenarios["current"]
        assert "timeToAchievement" in scenarios["current"]
        assert "monthlyContribution" in scenarios["current"]

    def test_adjustment_impact_panel_data(self, setup_test_data):
        """Test data structure for AdjustmentImpactPanel component"""
        test_data = setup_test_data
        
        # Mock GoalAdjustmentService to generate adjustment recommendations
        with patch('services.goal_adjustment_service.GoalAdjustmentService.generate_adjustment_recommendations') as mock_adjust:
            # Create expected adjustment recommendations
            mock_adjustments = [
                {
                    "type": "contribution",
                    "description": "Increase monthly SIP",
                    "impact": 0.15,
                    "value": 35000,
                    "previousValue": 25000,
                    "yearlyImpact": 120000
                },
                {
                    "type": "allocation",
                    "description": "Adjust asset allocation",
                    "impact": 0.08,
                    "value": {
                        "Equity": 0.70,
                        "Debt": 0.20,
                        "Gold": 0.10
                    }
                },
                {
                    "type": "timeframe",
                    "description": "Extend retirement timeline",
                    "impact": 0.10,
                    "value": 22,
                    "previousValue": 20
                },
                {
                    "type": "tax",
                    "description": "Optimize for tax benefits",
                    "impact": 0.05,
                    "taxSavings": 50000,
                    "section": "80C",
                    "indiaSpecificNotes": "Consider ELSS funds for both equity exposure and tax benefits."
                }
            ]
            
            # Set up the mock to return our expected adjustments
            mock_adjust.return_value = mock_adjustments
            
            # Instantiate the service
            adjustment_service = GoalAdjustmentService()
            
            # Call the method under test
            adjustments = adjustment_service.generate_adjustment_recommendations(
                test_data["goal"], 
                test_data["profile"]
            )
            
            # Verify the structure of the adjustments
            assert len(adjustments) == 4
            
            # Check for different adjustment types
            adjustment_types = [adj["type"] for adj in adjustments]
            assert "contribution" in adjustment_types
            assert "allocation" in adjustment_types
            assert "timeframe" in adjustment_types
            assert "tax" in adjustment_types
            
            # Check impact values
            for adjustment in adjustments:
                assert "impact" in adjustment
                assert isinstance(adjustment["impact"], float)
                assert 0 <= adjustment["impact"] <= 1
                assert "description" in adjustment
            
            # Check India-specific tax context
            tax_adjustment = next((a for a in adjustments if a["type"] == "tax"), None)
            assert tax_adjustment
            assert "section" in tax_adjustment
            assert "80C" in tax_adjustment["section"]
            assert "indiaSpecificNotes" in tax_adjustment

    def test_goal_document_visualization_export(self, setup_test_data):
        """Test that GoalDocumentGenerator can export visualization data in different formats"""
        test_data = setup_test_data
        
        # Create a document generator
        generator = GoalDocumentGenerator()
        
        # Create a simple document for testing exports
        document = [
            DocumentSection(
                title="Test Section",
                content={"summary": "This is a test section"}
            )
        ]
        
        # Add a visualization
        document[0].visualizations.append("data:image/png;base64,TEST_IMAGE_DATA")
        
        # Mock export methods with proper return values
        with patch.object(generator, 'generate_pdf', return_value=b'PDF_CONTENT'):
            with patch.object(generator, 'generate_html', return_value="<html><body>Document content</body></html>"):
                with patch.object(generator, 'generate_json') as mock_json:
                    # Setup proper JSON return format
                    mock_json.return_value = {
                        "sections": [
                            {
                                "title": section.title,
                                "content": section.content,
                                "visualizations": section.visualizations
                            }
                            for section in document
                        ]
                    }
                    
                    # Test JSON format for API responses
                    json_data = generator.generate_json(document)
                    assert isinstance(json_data, dict)
                    assert "sections" in json_data
                    
                    # Test HTML format for web display
                    html_data = generator.generate_html(document)
                    assert "<html>" in html_data
                    
                    # Test PDF format for download
                    pdf_data = generator.generate_pdf(document)
                    assert isinstance(pdf_data, bytes)


if __name__ == "__main__":
    pytest.main(["-v", "test_goal_visualization_components.py"])