"""
Test suite for enhanced CharitableGivingStrategy with optimization and constraint features.
"""

import unittest
import math
from unittest.mock import MagicMock, patch
from models.funding_strategies.charitable_giving_strategy import CharitableGivingStrategy

class TestEnhancedCharitableGivingStrategy(unittest.TestCase):
    """Test cases for enhanced charitable giving strategy with optimization features."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = CharitableGivingStrategy()
        
        # Sample test data
        self.sample_goal_data = {
            'goal_type': 'charitable_giving',
            'age': 45,
            'total_assets': 25000000,
            'liquid_assets': 5000000,
            'annual_income': 3000000,
            'discretionary_income': 900000,
            'tax_bracket': 0.3,
            'family_status': 'married with children',
            'existing_commitments': {
                'home_loan': {'amount': 50000},
                'education': {'amount': 30000}
            },
            'current_charitable_giving': 150000,
            'retirement_status': 'pre_retirement',
            'target_amount': 1000000,
            'time_horizon': 5,
            'risk_profile': 'moderate',
            'causes_of_interest': [
                {'name': 'Education', 'priority': 'high'},
                {'name': 'Healthcare', 'priority': 'medium'},
                {'name': 'Environmental', 'priority': 'low'}
            ],
            'preferred_giving_structure': 'recurring',
            'religious_considerations': 'Hindu',
            'regional_preference': 'Local',
            'giving_motivations': ['tax_benefits', 'social_impact'],
            'donation_transparency': 'high',
            'donation_recognition': 'low',
            'giving_timeframe': 'both',
            'has_family_foundation': False,
            'nri_status': False
        }

    def test_initialize_methods(self):
        """Test the lazy initialization methods."""
        # Test optimizer initialization
        self.assertIsNone(self.strategy.optimizer)
        self.strategy._initialize_optimizer()
        self.assertIsNotNone(self.strategy.optimizer)
        
        # Test constraints initialization
        self.assertIsNone(self.strategy.constraints)
        self.strategy._initialize_constraints()
        self.assertIsNotNone(self.strategy.constraints)
        
        # Test compound strategy initialization
        self.assertIsNone(self.strategy.compound_strategy)
        self.strategy._initialize_compound_strategy()
        self.assertIsNotNone(self.strategy.compound_strategy)
        
    def test_load_charitable_parameters(self):
        """Test loading of charitable parameters."""
        # Create mock parameter service
        mock_param_service = MagicMock()
        mock_param_service.get_parameter.side_effect = lambda x: {
            'donation_options': {'educational': {'tax_benefit': 'Section 80G'}},
            'donation_structures': {'trust': {'description': 'Family trust'}},
            'indian_tax_benefits': {'religious_giving': {'limit': '5000'}}
        }.get(x, None)
        
        # Set the mock service
        self.strategy.param_service = mock_param_service
        
        # Reload parameters
        self.strategy._load_charitable_parameters()
        
        # Verify parameters were updated
        self.assertIn('educational', self.strategy.charitable_params['donation_options'])
        self.assertIn('trust', self.strategy.charitable_params['donation_structures'])
        self.assertIn('religious_giving', self.strategy.charitable_params['indian_tax_benefits'])
        
        # Verify error handling
        mock_param_service.get_parameter.side_effect = Exception("Test exception")
        self.strategy._load_charitable_parameters()  # Should not raise exception

    def test_assess_charitable_giving_capacity(self):
        """Test assessment of charitable giving capacity."""
        capacity = self.strategy.assess_charitable_giving_capacity(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('giving_capacity', capacity)
        self.assertIn('tax_efficiency', capacity)
        self.assertIn('goal_assessment', capacity)
        self.assertIn('recommendations', capacity)
        
        # Verify capacity calculations
        self.assertEqual(capacity['giving_capacity']['current_charitable_giving'], 150000)
        self.assertIn('sustainable_annual_giving', capacity['giving_capacity'])
        self.assertIn('one_time_capacity', capacity['giving_capacity'])
        self.assertIn('capacity_level', capacity['giving_capacity'])
        
        # Verify tax efficiency
        self.assertIn('current_tax_benefit', capacity['tax_efficiency'])
        self.assertIn('optimal_tax_benefit', capacity['tax_efficiency'])
        
        # Verify goal assessment
        self.assertIn('feasibility_percentage', capacity['goal_assessment'])
        self.assertIn('feasibility_status', capacity['goal_assessment'])
        
        # Verify recommendations
        self.assertTrue(len(capacity['recommendations']) > 0)
        
    def test_assess_tax_optimization_opportunities(self):
        """Test assessment of tax optimization opportunities."""
        opportunities = self.strategy.assess_tax_optimization_opportunities(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('tax_benefit_assessment', opportunities)
        self.assertIn('optimization_opportunities', opportunities)
        self.assertIn('india_specific_considerations', opportunities)
        self.assertIn('recommendations', opportunities)
        
        # Verify tax benefit assessment
        self.assertIn('applicable_section', opportunities['tax_benefit_assessment'])
        self.assertIn('deduction_percentage', opportunities['tax_benefit_assessment'])
        self.assertIn('current_tax_benefit', opportunities['tax_benefit_assessment'])
        
        # Verify optimization opportunities
        self.assertIn('bundling_opportunity', opportunities['optimization_opportunities'])
        self.assertIn('appreciated_assets_opportunity', opportunities['optimization_opportunities'])
        
    def test_evaluate_social_impact_potential(self):
        """Test evaluation of social impact potential."""
        impact = self.strategy.evaluate_social_impact_potential(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('impact_assessment', impact)
        self.assertIn('cause_evaluations', impact)
        self.assertIn('recommendations', impact)
        self.assertIn('india_specific_context', impact)
        
        # Verify impact assessment
        self.assertIn('overall_impact_score', impact['impact_assessment'])
        self.assertIn('impact_level', impact['impact_assessment'])
        
        # Verify cause evaluations (might be empty if no causes provided)
        if impact['cause_evaluations']:
            self.assertIn('cause', impact['cause_evaluations'][0])
            self.assertIn('impact_potential', impact['cause_evaluations'][0])
        
        # Verify recommendations
        self.assertTrue(len(impact['recommendations']) >= 0)
        
        # Verify India-specific considerations
        self.assertIn('sector_context', impact['india_specific_context'])
        self.assertIn('regional_disparities', impact['india_specific_context'])
        
    def test_assess_giving_structure_optimization(self):
        """Test assessment of giving structure optimization."""
        structure = self.strategy.assess_giving_structure_optimization(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('structure_optimization', structure)
        self.assertIn('vehicle_details', structure)
        self.assertIn('implementation_considerations', structure)
        self.assertIn('india_specific_context', structure)
        self.assertIn('recommendations', structure)
        
        # Verify structure optimization
        self.assertIn('optimal_vehicle', structure['structure_optimization'])
        self.assertIn('recommended_allocation', structure['structure_optimization'])
        
        # Verify vehicle details
        self.assertIn('direct_donation', structure['vehicle_details'])
        self.assertIn('corpus_donation', structure['vehicle_details'])
        
        # Verify implementation considerations
        self.assertIn('setup_requirements', structure['implementation_considerations'])
        
        # Verify India-specific considerations
        self.assertIn('regulatory_framework', structure['india_specific_context'])
        self.assertIn('registration_requirements', structure['india_specific_context'])
        
    def test_optimize_tax_efficiency(self):
        """Test optimization of tax efficiency."""
        optimized = self.strategy.optimize_tax_efficiency(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('current_tax_efficiency', optimized)
        self.assertIn('optimized_strategy', optimized)
        self.assertIn('india_specific_guidance', optimized)
        
        # Verify current tax efficiency
        self.assertIn('applicable_section', optimized['current_tax_efficiency'])
        self.assertIn('deduction_percentage', optimized['current_tax_efficiency'])
        self.assertIn('current_tax_benefit', optimized['current_tax_efficiency'])
        
        # Verify optimized strategy
        self.assertIn('total_potential_savings', optimized['optimized_strategy'])
        self.assertIn('recommended_strategies', optimized['optimized_strategy'])
        self.assertIn('implementation_plan', optimized['optimized_strategy'])
        
        # Verify implementation plan
        self.assertTrue(len(optimized['optimized_strategy']['implementation_plan']) > 0)
        
        # Verify India-specific guidance
        self.assertIn('section_80g_documentation', optimized['india_specific_guidance'])
        self.assertIn('donation_reporting', optimized['india_specific_guidance'])
        
    def test_optimize_impact_allocation(self):
        """Test optimization of impact allocation."""
        optimized = self.strategy.optimize_impact_allocation(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('optimized_allocation', optimized)
        self.assertIn('implementation_strategy', optimized)
        self.assertIn('india_specific_guidance', optimized)
        
        # Verify optimized allocation
        self.assertIn('cause_allocations', optimized['optimized_allocation'])
        self.assertIn('total_annual_giving', optimized['optimized_allocation'])
        self.assertIn('diversification_level', optimized['optimized_allocation'])
        
        # Verify implementation strategy
        self.assertIn('recommended_involvement', optimized['implementation_strategy'])
        self.assertIn('implementation_timeline', optimized['implementation_strategy'])
        
        # Verify implementation timeline
        self.assertTrue(len(optimized['implementation_strategy']['implementation_timeline']) > 0)
        
        # Verify India-specific guidance
        self.assertIn('regional_focus', optimized['india_specific_guidance'])
        self.assertIn('region_recommendations', optimized['india_specific_guidance'])
        
    def test_optimize_giving_structure(self):
        """Test optimization of giving structure."""
        optimized = self.strategy.optimize_giving_structure(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('optimized_structure', optimized)
        self.assertIn('implementation_timeline', optimized)
        self.assertIn('transition_planning', optimized)
        self.assertIn('india_specific_guidance', optimized)
        
        # Verify optimized structure
        self.assertIn('primary_vehicle', optimized['optimized_structure'])
        self.assertIn('allocation_strategy', optimized['optimized_structure'])
        self.assertIn('annual_giving_amount', optimized['optimized_structure'])
        self.assertIn('optimization_plan', optimized['optimized_structure'])
        
        # Verify implementation timeline
        self.assertTrue(len(optimized['implementation_timeline']) > 0)
        self.assertIn('phase', optimized['implementation_timeline'][0])
        self.assertIn('timeframe', optimized['implementation_timeline'][0])
        self.assertIn('actions', optimized['implementation_timeline'][0])
        
        # Verify optimization benefits
        self.assertIn('optimization_benefits', optimized)
        self.assertIn('tax_efficiency_improvement', optimized['optimization_benefits'])
        
        # Verify India-specific guidance
        self.assertIn('regulatory_considerations', optimized['india_specific_guidance'])
        self.assertIn('registration_requirements', optimized['india_specific_guidance'])
        
    def test_integrate_rebalancing_strategy(self):
        """Test rebalancing strategy integration."""
        rebalancing = self.strategy.integrate_rebalancing_strategy(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertEqual(rebalancing['goal_type'], 'charitable_giving')
        self.assertIn('rebalancing_schedule', rebalancing)
        self.assertIn('drift_thresholds', rebalancing)
        
        # Verify custom thresholds
        self.assertIn('asset_bands', rebalancing['drift_thresholds'])
        self.assertTrue(len(rebalancing['drift_thresholds']['asset_bands']) > 0)
        
        # Verify charitable considerations
        self.assertIn('charitable_giving_considerations', rebalancing)
        self.assertIn('tax_efficiency', rebalancing['charitable_giving_considerations'])
        
        # Verify India-specific factors
        self.assertIn('india_specific_considerations', rebalancing)
        self.assertIn('section_80g_optimization', rebalancing['india_specific_considerations'])
        
    def test_generate_funding_strategy(self):
        """Test comprehensive funding strategy generation."""
        strategy = self.strategy.generate_funding_strategy(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertEqual(strategy['goal_type'], 'charitable_giving')
        self.assertIn('donation_details', strategy)
        self.assertIn('constraint_assessments', strategy)
        self.assertIn('optimization_strategies', strategy)
        self.assertIn('india_specific_guidance', strategy)
        self.assertIn('implementation_plan', strategy)
        
        # Verify constraint assessments
        self.assertIn('giving_capacity', strategy['constraint_assessments'])
        self.assertIn('tax_optimization', strategy['constraint_assessments'])
        self.assertIn('impact_potential', strategy['constraint_assessments'])
        self.assertIn('structure_optimization', strategy['constraint_assessments'])
        
        # Verify optimization strategies
        self.assertIn('tax_efficiency', strategy['optimization_strategies'])
        self.assertIn('impact_allocation', strategy['optimization_strategies'])
        self.assertIn('giving_structure', strategy['optimization_strategies'])
        
        # Verify investment recommendations
        self.assertIn('investment_recommendations', strategy)
        
        # Verify India-specific guidance
        self.assertIn('tax_provisions', strategy['india_specific_guidance'])
        self.assertIn('regulatory_framework', strategy['india_specific_guidance'])
        self.assertIn('cultural_considerations', strategy['india_specific_guidance'])
        
        # Verify implementation plan
        self.assertIn('immediate_steps', strategy['implementation_plan'])
        self.assertIn('medium_term_steps', strategy['implementation_plan'])
        self.assertIn('annual_review_process', strategy['implementation_plan'])

if __name__ == '__main__':
    unittest.main()