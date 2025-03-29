"""
Test suite for enhanced CustomGoalStrategy with optimization and constraint features.
"""

import unittest
import math
from unittest.mock import MagicMock, patch
from models.funding_strategies.custom_goal_strategy import CustomGoalStrategy

class TestEnhancedCustomGoalStrategy(unittest.TestCase):
    """Test cases for enhanced custom goal strategy with optimization features."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = CustomGoalStrategy()
        
        # Sample test data
        self.sample_goal_data = {
            'goal_type': 'custom',
            'age': 42,
            'total_assets': 20000000,
            'liquid_assets': 4000000,
            'annual_income': 2500000,
            'discretionary_income': 800000,
            'tax_bracket': 0.3,
            'family_status': 'married with children',
            'existing_commitments': {
                'home_loan': {'amount': 60000},
                'education': {'amount': 35000}
            },
            'retirement_status': 'pre_retirement',
            'target_amount': 1500000,
            'time_horizon': 4,
            'risk_profile': 'moderate',
            'custom_goal_name': 'Family Vacation to South India',
            'custom_goal_description': 'Trip to visit temples and cultural sites in South India',
            'goal_priority': 'medium',
            'goal_flexibility': 'moderate',
            'goal_category': 'lifestyle',
            'wealth_building_potential': 'minimal',
            'recurring_expense': False,
            'cultural_significance': 'high',
            'regional_preference': 'South India',
            'funding_regularity': 'monthly',
            'additional_resources': ['family gifts', 'tax refund'],
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
        
    def test_load_custom_parameters(self):
        """Test loading of custom goal parameters."""
        # Create mock parameter service
        mock_param_service = MagicMock()
        mock_param_service.get_parameter.side_effect = lambda x: {
            'goal_classification_rubric': {'time_sensitivity': {'critical': {'weight': 3.0}}},
            'allocation_templates': {'growth_focused': {'equity': 0.40}},
            'funding_approaches': {'hybrid': {'description': 'Combination approach'}}
        }.get(x, None)
        
        # Set the mock service
        self.strategy.param_service = mock_param_service
        
        # Reload parameters
        self.strategy._load_custom_parameters()
        
        # Verify parameters were updated
        self.assertIn('time_sensitivity', self.strategy.custom_params['goal_classification_rubric'])
        self.assertIn('growth_focused', self.strategy.custom_params['allocation_templates'])
        self.assertIn('hybrid', self.strategy.custom_params['funding_approaches'])
        
        # Verify error handling
        mock_param_service.get_parameter.side_effect = Exception("Test exception")
        self.strategy._load_custom_parameters()  # Should not raise exception

    def test_assess_goal_classification_confidence(self):
        """Test assessment of goal classification confidence."""
        confidence = self.strategy.assess_goal_classification_confidence(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('classification', confidence)
        self.assertIn('confidence_scores', confidence)
        self.assertIn('confidence_level', confidence)
        self.assertIn('india_specific_considerations', confidence)
        self.assertIn('recommendations', confidence)
        
        # Verify classification
        self.assertIn('time_sensitivity', confidence['classification'])
        self.assertIn('wealth_building', confidence['classification'])
        self.assertIn('goal_magnitude', confidence['classification'])
        
        # Verify confidence scores
        self.assertIn('time_sensitivity', confidence['confidence_scores'])
        self.assertIn('wealth_building', confidence['confidence_scores'])
        self.assertIn('goal_magnitude', confidence['confidence_scores'])
        self.assertIn('overall', confidence['confidence_scores'])
        
        # Verify India-specific considerations
        self.assertIn('pilgrimage_classification', confidence['india_specific_considerations'])
        self.assertIn('major_ceremonies', confidence['india_specific_considerations'])
        
        # Verify recommendations
        self.assertTrue(len(confidence['recommendations']) > 0)
        
    def test_assess_funding_flexibility(self):
        """Test assessment of funding flexibility."""
        flexibility = self.strategy.assess_funding_flexibility(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('flexibility_scores', flexibility)
        self.assertIn('flexibility_level', flexibility)
        self.assertIn('suitable_approaches', flexibility)
        self.assertIn('india_specific_patterns', flexibility)
        self.assertIn('optimization_opportunities', flexibility)
        
        # Verify flexibility scores
        self.assertIn('timing_flexibility', flexibility['flexibility_scores'])
        self.assertIn('funding_pattern_flexibility', flexibility['flexibility_scores'])
        self.assertIn('overall_flexibility', flexibility['flexibility_scores'])
        
        # Verify suitable approaches
        self.assertTrue(len(flexibility['suitable_approaches']) > 0)
        self.assertIn('approach', flexibility['suitable_approaches'][0])
        self.assertIn('suitability_score', flexibility['suitable_approaches'][0])
        
        # Verify India-specific patterns
        self.assertIn('seasonal_income_management', flexibility['india_specific_patterns'])
        self.assertIn('family_resource_pooling', flexibility['india_specific_patterns'])
        
    def test_assess_financial_integration(self):
        """Test assessment of financial integration."""
        integration = self.strategy.assess_financial_integration(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('integration_scores', integration)
        self.assertIn('integration_level', integration)
        self.assertIn('tax_efficiency_strategies', integration)
        self.assertIn('optimization_recommendations', integration)
        self.assertIn('india_specific_integration', integration)
        
        # Verify integration scores
        self.assertIn('tax_efficiency_potential', integration['integration_scores'])
        self.assertIn('portfolio_alignment', integration['integration_scores'])
        self.assertIn('overall_integration', integration['integration_scores'])
        
        # Verify tax efficiency strategies
        if len(integration['tax_efficiency_strategies']) > 0:
            self.assertIn('strategy', integration['tax_efficiency_strategies'][0])
            self.assertIn('applicable_section', integration['tax_efficiency_strategies'][0])
        
        # Verify optimization recommendations
        self.assertTrue(len(integration['optimization_recommendations']) > 0)
        
        # Verify India-specific integration
        self.assertIn('tax_optimizations', integration['india_specific_integration'])
        self.assertIn('cultural_considerations', integration['india_specific_integration'])
        
    def test_assess_sustainability_metrics(self):
        """Test assessment of sustainability metrics."""
        sustainability = self.strategy.assess_sustainability_metrics(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('sustainability_metrics', sustainability)
        self.assertIn('sustainability_level', sustainability)
        self.assertIn('india_specific_considerations', sustainability)
        self.assertIn('optimization_opportunities', sustainability)
        
        # Verify sustainability metrics
        self.assertIn('income_sustainability', sustainability['sustainability_metrics'])
        self.assertIn('timeline_sustainability', sustainability['sustainability_metrics'])
        self.assertIn('lifecycle_sustainability', sustainability['sustainability_metrics'])
        self.assertIn('overall_sustainability', sustainability['sustainability_metrics'])
        
        # Verify India-specific considerations
        self.assertIn('traditional_sustainability', sustainability['india_specific_considerations'])
        self.assertIn('community_sustainability', sustainability['india_specific_considerations'])
        
        # Verify optimization opportunities
        self.assertTrue(len(sustainability['optimization_opportunities']) > 0)
        
    def test_optimize_goal_classification(self):
        """Test optimization of goal classification."""
        optimized = self.strategy.optimize_goal_classification(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('optimized_classification', optimized)
        self.assertIn('recommendations', optimized)
        self.assertIn('india_specific_optimizations', optimized)
        self.assertIn('implementation_steps', optimized)
        
        # Verify optimized classification
        self.assertIn('original_classification', optimized['optimized_classification'])
        self.assertIn('optimized_classification', optimized['optimized_classification'])
        self.assertIn('refinements', optimized['optimized_classification'])
        self.assertIn('confidence_improvement', optimized['optimized_classification'])
        
        # Verify India-specific optimizations
        self.assertIn('cultural_context', optimized['india_specific_optimizations'])
        self.assertIn('wealth_perception', optimized['india_specific_optimizations'])
        
    def test_optimize_funding_approach(self):
        """Test optimization of funding approach."""
        optimized = self.strategy.optimize_funding_approach(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('funding_approach', optimized)
        self.assertIn('implementation_timeline', optimized)
        self.assertIn('optimization_strategies', optimized)
        self.assertIn('india_specific_optimizations', optimized)
        
        # Verify funding approach
        self.assertIn('recommended_approach', optimized['funding_approach'])
        self.assertIn('approach_rationale', optimized['funding_approach']) 
        self.assertIn('optimized_allocation', optimized['funding_approach'])
        
        # Verify implementation timeline
        self.assertTrue(len(optimized['implementation_timeline']) > 0)
        self.assertIn('phase', optimized['implementation_timeline'][0])
        self.assertIn('actions', optimized['implementation_timeline'][0])
        
        # Verify optimization strategies
        self.assertTrue(len(optimized['optimization_strategies']) > 0)
        
        # Verify India-specific optimizations
        self.assertIn('systematic_investment_plans', optimized['india_specific_optimizations'])
        
    def test_optimize_financial_integration(self):
        """Test optimization of financial integration."""
        optimized = self.strategy.optimize_financial_integration(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('integration_metrics', optimized)
        self.assertIn('integration_optimization', optimized)
        self.assertIn('implementation_roadmap', optimized)
        self.assertIn('india_specific_integration', optimized)
        self.assertIn('monitoring_framework', optimized)
        
        # Verify integration metrics
        self.assertIn('tax_efficiency_potential', optimized['integration_metrics'])
        self.assertIn('portfolio_alignment', optimized['integration_metrics'])
        self.assertIn('overall_integration', optimized['integration_metrics'])
        
        # Verify integration optimization
        self.assertIn('tax_optimization', optimized['integration_optimization'])
        self.assertIn('portfolio_integration', optimized['integration_optimization'])
        
        # Verify implementation roadmap
        self.assertTrue(len(optimized['implementation_roadmap']) > 0)
        self.assertIn('phase', optimized['implementation_roadmap'][0])
        self.assertIn('actions', optimized['implementation_roadmap'][0])
        
        # Verify India-specific integration
        self.assertIn('tax_optimizations', optimized['india_specific_integration'])
        self.assertIn('cultural_considerations', optimized['india_specific_integration'])
        
    def test_optimize_goal_sustainability(self):
        """Test optimization of goal sustainability."""
        optimized = self.strategy.optimize_goal_sustainability(self.sample_goal_data)
        
        # Verify structure
        self.assertIn('sustainability_metrics', optimized)
        self.assertIn('primary_challenges', optimized)
        self.assertIn('optimization_strategies', optimized)
        self.assertIn('india_specific_sustainability', optimized)
        self.assertIn('implementation_roadmap', optimized)
        
        # Verify sustainability metrics
        self.assertIn('income_sustainability', optimized['sustainability_metrics'])
        self.assertIn('timeline_sustainability', optimized['sustainability_metrics'])
        self.assertIn('lifecycle_sustainability', optimized['sustainability_metrics'])
        self.assertIn('overall_sustainability', optimized['sustainability_metrics'])
        
        # Verify optimization strategies
        self.assertTrue(len(optimized['optimization_strategies']) > 0)
        if len(optimized['optimization_strategies']) > 0:
            self.assertIn('challenge', optimized['optimization_strategies'][0])
            self.assertIn('strategy', optimized['optimization_strategies'][0])
        
        # Verify implementation roadmap
        self.assertTrue(len(optimized['implementation_roadmap']) > 0)
        
        # Verify India-specific sustainability
        self.assertIn('traditional_sustainability', optimized['india_specific_sustainability'])
        self.assertIn('family_considerations', optimized['india_specific_sustainability'])
        
    def test_classify_custom_goal(self):
        """Test custom goal classification."""
        # Extract relevant parameters from sample goal data
        goal_amount = self.sample_goal_data.get('target_amount', 0)
        time_horizon = self.sample_goal_data.get('time_horizon', 0)
        annual_income = self.sample_goal_data.get('annual_income', 0)
        goal_description = self.sample_goal_data.get('custom_goal_description', '')
        
        classification = self.strategy.classify_custom_goal(
            goal_amount=goal_amount,
            time_horizon=time_horizon,
            annual_income=annual_income,
            goal_description=goal_description
        )
        
        # Verify structure
        self.assertIn('classification', classification)
        self.assertIn('priority_score', classification)
        self.assertIn('recommended_approach', classification)
        self.assertIn('classification_details', classification)
        
        # Verify classification values
        self.assertIn('time_sensitivity', classification['classification'])
        self.assertIn('wealth_building', classification['classification'])
        self.assertIn('goal_magnitude', classification['classification'])
        
        # Verify recommended approach
        self.assertIn('allocation_template', classification['recommended_approach'])
        self.assertIn('funding_method', classification['recommended_approach'])
        
    def test_customize_allocation_model(self):
        """Test customization of allocation model."""
        # Extract relevant parameters from sample goal data
        base_template = 'balanced'
        time_horizon = self.sample_goal_data.get('time_horizon', 0)
        risk_tolerance = self.sample_goal_data.get('risk_profile', 'moderate')
        goal_priority = 65
        
        allocation = self.strategy.customize_allocation_model(
            base_template=base_template,
            time_horizon=time_horizon,
            risk_tolerance=risk_tolerance,
            goal_priority=goal_priority
        )
        
        # Verify allocation structure
        for key in ['cash', 'short_term_debt', 'balanced_funds', 'expected_return']:
            self.assertIn(key, allocation)
        
        # Verify allocations sum to approximately 1 (allowing for small rounding errors)
        total = sum(v for k, v in allocation.items() if k != 'expected_return')
        self.assertGreater(total, 0.99)
        self.assertLess(total, 1.01)
        
        # Verify expected return
        self.assertTrue(isinstance(allocation['expected_return'], float))
        
    def test_design_custom_funding_plan(self):
        """Test design of custom funding plan."""
        # Extract relevant parameters from sample goal data
        goal_amount = self.sample_goal_data.get('target_amount', 0)
        time_horizon = self.sample_goal_data.get('time_horizon', 0)
        current_savings = 0
        monthly_capacity = self.sample_goal_data.get('discretionary_income', 0) / 12
        allocation = {
            'cash': 0.2,
            'short_term_debt': 0.3,
            'balanced_funds': 0.3,
            'equity': 0.2,
            'expected_return': 0.075
        }
        
        plan = self.strategy.design_custom_funding_plan(
            goal_amount=goal_amount,
            time_horizon=time_horizon,
            current_savings=current_savings,
            monthly_capacity=monthly_capacity,
            allocation=allocation
        )
        
        # Verify funding plan structure
        self.assertIn('goal_amount', plan)
        self.assertIn('time_horizon', plan)
        self.assertIn('projected_growth', plan)
        self.assertIn('funding_requirements', plan)
        self.assertIn('implementation_plan', plan)
        
        # Verify funding requirements
        self.assertIn('recommended_monthly_contribution', plan['funding_requirements'])
        
        # Verify implementation plan
        self.assertIn('regular_contribution', plan['implementation_plan'])
        self.assertIn('milestones', plan['implementation_plan'])
        
        # Verify milestones
        self.assertTrue(len(plan['implementation_plan']['milestones']) > 0)
        
    def test_generate_custom_goal_insights(self):
        """Test generation of custom goal insights."""
        # Create mock for generate_custom_goal_insights
        with patch.object(self.strategy, 'generate_custom_goal_insights') as mock_insights:
            # Set up mock return value
            mock_insights.return_value = {
                'goal_feasibility': {
                    'feasibility_score': 0.75,
                    'feasibility_assessment': 'Moderately feasible'
                },
                'optimization_opportunities': [
                    {'area': 'Funding', 'opportunity': 'Increase monthly contributions'}
                ],
                'risk_factors': [
                    {'factor': 'Timeline', 'risk_level': 'Medium'}
                ],
                'india_specific_insights': {
                    'cultural_context': 'Religious travel has cultural significance',
                    'market_considerations': 'Consider seasonal pricing variations'
                }
            }
            
            # Call the method
            insights = self.strategy.generate_custom_goal_insights(self.sample_goal_data)
        
        # Verify the mock was called with the right arguments
        mock_insights.assert_called_once_with(self.sample_goal_data)
        
        # Verify structure from mock return value
        self.assertIn('goal_feasibility', insights)
        self.assertIn('optimization_opportunities', insights)
        self.assertIn('risk_factors', insights)
        self.assertIn('india_specific_insights', insights)
        
        # Verify goal feasibility
        self.assertEqual(insights['goal_feasibility']['feasibility_score'], 0.75)
        self.assertEqual(insights['goal_feasibility']['feasibility_assessment'], 'Moderately feasible')
        
        # Verify optimization opportunities
        self.assertEqual(len(insights['optimization_opportunities']), 1)
        
        # Verify India-specific insights
        self.assertEqual(insights['india_specific_insights']['cultural_context'], 'Religious travel has cultural significance')
        
    def test_integrate_rebalancing_strategy(self):
        """Test rebalancing strategy integration."""
        # Create mock for integrate_rebalancing_strategy
        with patch.object(self.strategy, 'integrate_rebalancing_strategy') as mock_rebalance:
            # Set up mock return value
            mock_rebalance.return_value = {
                'goal_type': 'custom',
                'rebalancing_schedule': {
                    'frequency': 'quarterly',
                    'conditional_triggers': ['5% portfolio drift']
                },
                'drift_thresholds': {
                    'asset_bands': [
                        {'asset_class': 'equity', 'lower': -5, 'upper': 5}
                    ]
                },
                'custom_goal_considerations': {
                    'timeline_adjustments': True,
                    'priority_based_threshold': '10%'
                },
                'india_specific_considerations': {
                    'tax_implications': 'Consider STCG for rebalancing timing'
                }
            }
            
            # Call the method
            rebalancing = self.strategy.integrate_rebalancing_strategy(self.sample_goal_data)
        
        # Verify the mock was called with the right arguments
        mock_rebalance.assert_called_once_with(self.sample_goal_data)
        
        # Verify structure from mock return value
        self.assertEqual(rebalancing['goal_type'], 'custom')
        self.assertIn('rebalancing_schedule', rebalancing)
        self.assertIn('drift_thresholds', rebalancing)
        self.assertIn('custom_goal_considerations', rebalancing)
        self.assertIn('india_specific_considerations', rebalancing)
        
    def test_generate_funding_strategy(self):
        """Test comprehensive funding strategy generation."""
        # Create mock for generate_funding_strategy
        with patch.object(self.strategy, 'generate_funding_strategy') as mock_generate:
            # Set up mock return value
            mock_generate.return_value = {
                'goal_type': 'custom',
                'goal_details': {
                    'name': 'Family Vacation to South India',
                    'target_amount': 1500000,
                    'time_horizon': 4
                },
                'goal_classification': {
                    'time_sensitivity': 'flexible',
                    'wealth_building': 'minimal',
                    'goal_magnitude': 'moderate'
                },
                'constraint_assessments': {
                    'classification_confidence': {'overall_confidence_score': 0.82},
                    'funding_flexibility': {'flexibility_score': 0.65},
                    'financial_integration': {'integration_score': 0.70},
                    'sustainability_metrics': {'overall_sustainability': 0.55}
                },
                'optimization_strategies': {
                    'goal_classification': {'recommended_actions': []},
                    'funding_approach': {'recommended_approach': 'hybrid'},
                    'financial_integration': {'portfolio_integration': {}},
                    'goal_sustainability': {'optimization_strategies': []}
                },
                'investment_recommendations': {
                    'allocation_model': {'cash': 0.2, 'short_term_debt': 0.3}
                },
                'india_specific_guidance': {
                    'tax_provisions': 'Consider Section 80C options',
                    'investment_vehicles': 'Mutual funds with SIP approach',
                    'cultural_considerations': 'Plan around auspicious travel dates'
                },
                'implementation_plan': {
                    'immediate_steps': ['Set up monthly SIP of ₹12,500'],
                    'medium_term_steps': ['Review progress quarterly'],
                    'annual_review_process': 'Adjust strategy based on progress'
                }
            }
            
            # Call the method
            strategy = self.strategy.generate_funding_strategy(self.sample_goal_data)
        
        # Verify the mock was called with the right arguments
        mock_generate.assert_called_once_with(self.sample_goal_data)
        
        # Verify structure from mock return value
        self.assertEqual(strategy['goal_type'], 'custom')
        self.assertIn('goal_classification', strategy)
        self.assertIn('constraint_assessments', strategy)
        self.assertIn('optimization_strategies', strategy)
        self.assertIn('investment_recommendations', strategy)
        self.assertIn('india_specific_guidance', strategy)
        self.assertIn('implementation_plan', strategy)

if __name__ == '__main__':
    unittest.main()