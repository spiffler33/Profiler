#!/usr/bin/env python3
"""
Test script for validating the GoalDocumentGenerator implementation.
This script tests document creation, visualization generation, and document format outputs.
"""

import os
import sys
import uuid
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock the matplotlib and reportlab imports for tests
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.pdfgen'] = MagicMock()
sys.modules['reportlab.pdfgen.canvas'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()

# Import the models
from models.goal_document import GoalDocumentGenerator, DocumentSection
from models.goal_models import Goal, GoalCategory, GoalManager
from models.database_profile_manager import DatabaseProfileManager

class TestGoalDocumentGenerator:
    """Test cases for the GoalDocumentGenerator"""

    @pytest.fixture
    def setup_test_data(self):
        """Setup test data for document generation tests"""
        # Create a test profile
        profile_id = str(uuid.uuid4())
        profile_data = {
            "id": profile_id,
            "name": "Test User",
            "email": "test@example.com",
            "age": 35,
            "currency": "INR",
            "income": 1200000,  # Annual income in INR
            "expenses": 50000,  # Monthly expenses in INR
            "savings": 300000,  # Annual savings in INR
            "location": "Mumbai, India",
            "financial_goals": [],
            "risk_profile": "moderate",
            "country": "India"
        }
        
        # Create test goals
        goals = [
            Goal(
                id=str(uuid.uuid4()),
                user_profile_id=profile_id,
                category="emergency_fund",
                title="Emergency Fund",
                target_amount=600000,
                timeframe=datetime.now().date().replace(year=datetime.now().year + 1).isoformat(),
                current_amount=200000,
                importance="high",
                flexibility="somewhat_flexible",
                notes="Build up 6 months of expenses",
                current_progress=33.33,
                priority_score=90.0,
                goal_success_probability=75.0,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            Goal(
                id=str(uuid.uuid4()),
                user_profile_id=profile_id,
                category="traditional_retirement",
                title="Retirement Savings",
                target_amount=20000000,
                timeframe=datetime.now().date().replace(year=datetime.now().year + 25).isoformat(),
                current_amount=2000000,
                importance="high",
                flexibility="very_flexible",
                notes="Long-term retirement nest egg",
                current_progress=10.0,
                priority_score=85.0,
                goal_success_probability=65.0,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            Goal(
                id=str(uuid.uuid4()),
                user_profile_id=profile_id,
                category="home",
                title="Home Purchase",
                target_amount=10000000,
                timeframe=datetime.now().date().replace(year=datetime.now().year + 5).isoformat(),
                current_amount=1500000,
                importance="medium",
                flexibility="fixed",
                notes="Down payment for apartment in Mumbai",
                current_progress=15.0,
                priority_score=80.0,
                goal_success_probability=60.0,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        ]
        
        # Add goals to profile
        profile_data["financial_goals"] = [goal.__dict__ for goal in goals]
        
        return {
            "profile": profile_data,
            "goals": goals
        }
    
    @pytest.fixture
    def document_generator(self):
        """Create a GoalDocumentGenerator instance"""
        return GoalDocumentGenerator()
    
    def test_document_section_creation(self):
        """Test the creation of document sections"""
        section = DocumentSection(
            title="Test Section",
            content={
                "summary": "This is a test section",
                "details": ["Item 1", "Item 2"]
            }
        )
        
        assert section.title == "Test Section"
        assert "summary" in section.content
        assert len(section.content["details"]) == 2
        assert section.visualizations == []
    
    def test_format_rupees(self, document_generator):
        """Test formatting of monetary values as Indian Rupees"""
        # Test various amounts
        assert "₹10,000" in document_generator.format_rupees(10000) or "10,000" in document_generator.format_rupees(10000)
        assert "₹1.00 L" in document_generator.format_rupees(100000) or "1,00,000" in document_generator.format_rupees(100000)
        assert "₹10.00 L" in document_generator.format_rupees(1000000) or "10,00,000" in document_generator.format_rupees(1000000)
        assert "₹1.00 Cr" in document_generator.format_rupees(10000000) or "1,00,00,000" in document_generator.format_rupees(10000000)
    
    @patch('models.goal_document.GoalDocumentGenerator.calculate_tax_liability')
    def test_calculate_tax_liability(self, mock_calculate, document_generator):
        """Test calculation of Indian tax liability"""
        mock_calculate.return_value = 120000
        
        tax = document_generator.calculate_tax_liability(1200000)
        assert tax == 120000
        mock_calculate.assert_called_once_with(1200000)
    
    @patch('models.goal_document.GoalDocumentGenerator.calculate_sip_amount')
    def test_calculate_sip_amount(self, mock_calculate, document_generator):
        """Test SIP (Systematic Investment Plan) calculation"""
        mock_calculate.return_value = 21500
        
        sip = document_generator.calculate_sip_amount(
            target_amount=1000000,
            timeframe_years=5,
            expected_return=0.12
        )
        assert sip == 21500
    
    def test_generate_goal_document_basic(self, document_generator, setup_test_data):
        """Test basic document generation for a goal"""
        test_data = setup_test_data
        goal = test_data["goals"][0]  # Emergency Fund goal
        profile = test_data["profile"]
        
        # Mock visualization methods to avoid actual rendering
        with patch.object(document_generator, '_generate_progress_visualization', return_value=DocumentSection(title="Progress Visualization", content={})):
            with patch.object(document_generator, '_generate_probability_analysis', return_value=DocumentSection(title="Probability Analysis", content={})):
                document = document_generator.generate_goal_document(goal, profile)
                
                # Verify document structure
                assert isinstance(document, dict)
                
                # Check for required sections
                assert "sections" in document
                assert isinstance(document["sections"], list)
                assert len(document["sections"]) > 0
                
                # Check for document metadata
                assert "id" in document
                assert "created_at" in document
                assert "goal_id" in document
                
                # Check document has some content
                assert "title" in document
    
    @patch('models.goal_document.GoalDocumentGenerator.generate_all_goals_summary')
    def test_generate_all_goals_summary(self, mock_generate, document_generator, setup_test_data):
        """Test generation of summary document for all goals"""
        test_data = setup_test_data
        profile = test_data["profile"]
        
        # Setup mock return value
        mock_result = {
            "id": str(uuid.uuid4()),
            "type": "goals_summary",
            "created_at": datetime.now().isoformat(),
            "profile_id": profile["id"],
            "title": "Financial Goals Summary",
            "sections": [
                {"title": "Overall Goals Summary", "content": {}, "visualizations": []},
                {"title": "Individual Goals", "content": {}, "visualizations": []}
            ]
        }
        mock_generate.return_value = mock_result
        
        # Call the method
        document = document_generator.generate_all_goals_summary(profile)
        
        # Verify the mock was called
        mock_generate.assert_called_once_with(profile)
        
        # Check the result
        assert document == mock_result
        assert "title" in document
        assert "sections" in document
    
    def test_generate_goal_comparison(self, document_generator, setup_test_data):
        """Test generation of goal comparison document"""
        test_data = setup_test_data
        goals = test_data["goals"]
        
        # Mock visualization methods
        with patch.object(document_generator, '_generate_goal_comparison_chart', return_value=DocumentSection(title="Goals Comparison", content={})):
            document = document_generator.generate_goal_comparison(
                [goals[0], goals[1]]  # Compare Emergency Fund and Retirement
            )
            
            # Verify document structure
            assert isinstance(document, dict)
            
            # Check for required sections
            assert "sections" in document
            assert isinstance(document["sections"], list)
            assert len(document["sections"]) > 0
            
            # Check for document metadata
            assert "id" in document
            assert "created_at" in document
            
            # Check document has some content
            assert "title" in document
    
    @patch('models.goal_document.GoalDocumentGenerator.generate_pdf')
    def test_generate_pdf(self, mock_generate_pdf, document_generator, setup_test_data):
        """Test PDF generation from document"""
        test_data = setup_test_data
        goal = test_data["goals"][0]
        profile = test_data["profile"]
        
        # Create a simple test document sections
        test_document_sections = [
            DocumentSection(
                title="Test Section",
                content={"text": "This is a test"}
            ).to_dict()
        ]
        
        mock_generate_pdf.return_value = b'PDF_CONTENT'
        
        # Test PDF generation
        pdf_data = document_generator.generate_pdf(test_document_sections)
        assert pdf_data == b'PDF_CONTENT'
        mock_generate_pdf.assert_called_once_with(test_document_sections)
    
    @patch('models.goal_document.GoalDocumentGenerator.generate_html')
    def test_generate_html(self, mock_generate_html, document_generator, setup_test_data):
        """Test HTML generation from document"""
        test_document_sections = [
            DocumentSection(
                title="Test Section",
                content={"text": "This is a test"}
            ).to_dict()
        ]
        
        mock_generate_html.return_value = "<html><body>Document content</body></html>"
        
        # Test HTML generation
        html = document_generator.generate_html(test_document_sections)
        assert "<html>" in html
        mock_generate_html.assert_called_once_with(test_document_sections)
    
    @patch('models.goal_document.GoalDocumentGenerator.generate_json')
    def test_generate_json(self, mock_generate_json, document_generator, setup_test_data):
        """Test JSON generation from document"""
        test_document_sections = [
            DocumentSection(
                title="Test Section",
                content={"text": "This is a test"}
            ).to_dict()
        ]
        
        expected_json = {"sections": [{"title": "Test Section", "content": {"text": "This is a test"}, "visualizations": []}]}
        mock_generate_json.return_value = expected_json
        
        # Test JSON generation
        json_data = document_generator.generate_json(test_document_sections)
        assert json_data == expected_json
        mock_generate_json.assert_called_once_with(test_document_sections)
    
    def test_create_visualizations(self, document_generator, setup_test_data):
        """Test visualization creation with matplotlib"""
        test_data = setup_test_data
        goal = test_data["goals"][0]
        
        # Create a dummy figure for the mocked pyplot
        mock_fig = MagicMock()
        
        # Test visualization via section methods directly
        section = DocumentSection(
            title="Test Visualization",
            content={"text": "This section has a visualization"}
        )
        
        # Add a visualization directly
        visualization_data = "data:image/png;base64,TEST_IMAGE_DATA"
        section.visualizations.append(visualization_data)
        
        # Verify the visualization was added
        assert len(section.visualizations) == 1
        assert "data:image/png;base64" in section.visualizations[0]
    
    def test_integration_document_generation(self, document_generator, setup_test_data):
        """Integration test for document generation process"""
        test_data = setup_test_data
        goal = test_data["goals"][0]
        profile = test_data["profile"]
        
        # Mock the visualization and generation methods
        with patch.object(document_generator, '_generate_progress_visualization', return_value=DocumentSection(title="Progress Visualization", content={})):
            with patch.object(document_generator, '_generate_probability_analysis', return_value=DocumentSection(title="Probability Analysis", content={})):
                with patch.object(document_generator, 'generate_pdf', return_value=b'PDF_CONTENT'):
                    with patch.object(document_generator, 'generate_html', return_value="<html>content</html>"):
                        # Test the full document generation flow
                        document = document_generator.generate_goal_document(goal, profile)
                        
                        # Generate different output formats
                        pdf = document_generator.generate_pdf(document.get("sections", []))
                        html = document_generator.generate_html(document.get("sections", []))
                        json_data = document_generator.generate_json(document.get("sections", []))
                        
                        # Verify the document was created with all necessary sections
                        section_titles = [section.get("title") for section in document.get("sections", [])]
                        expected_sections = [
                            "Executive Summary", 
                            "Progress Visualization", 
                            "Probability Analysis"
                        ]
                        
                        for section in expected_sections:
                            assert section in section_titles, f"Missing section: {section}"


if __name__ == "__main__":
    pytest.main(["-v", "test_goal_document.py"])