"""
Test suite for enhanced LegacyPlanningStrategy with optimization and constraint features.
"""

import unittest
import math
from unittest.mock import MagicMock, patch
from models.funding_strategies.legacy_planning_strategy import LegacyPlanningStrategy

class TestEnhancedLegacyPlanningStrategy(unittest.TestCase):
    """Test cases for enhanced legacy planning strategy with optimization features."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = LegacyPlanningStrategy()
        
        # Sample test data
        self.sample_goal_data = {
            'goal_type': 'estate_planning',
            'age': 55,
            'total_assets': 30000000,
            'annual_income': 2500000,
            'family_status': 'married with children',
            'estate_complexity': 'moderate',
            'beneficiaries': [
                {
                    'relationship': 'spouse',
                    'age': 52,
                    'financial_maturity': 'high',
                    'financial_need': 'low'
                },
                {
                    'relationship': 'child',
                    'age': 25,
                    'financial_maturity': 'moderate',
                    'financial_need': 'moderate'
                },
                {
                    'relationship': 'child',
                    'age': 18,
                    'financial_maturity': 'low',
                    'financial_need': 'high'
                }
            ],
            'estate_components': {
                'liquid_assets': 6000000,
                'property': 15000000,
                'investments': 7000000,
                'business': 2000000
            },
            'existing_documents': [
                {'type': 'will', 'year': 2018},
                {'type': 'financial_poa', 'year': 2018}
            ],
            'monthly_contribution': 50000,
            'current_savings': 5000000,
            'time_horizon': 10,
            'risk_profile': 'conservative',
            'retirement_status': 'pre_retirement',
            'tax_bracket': 0.3,
            'charitable_interests': [
                {'name': 'Education', 'priority': 'high'},
                {'name': 'Healthcare', 'priority': 'medium'}
            ],
            'current_giving': 300000,
            'giving_timeframe': 'both',
            'has_asset_inventory': True,
            'health_status': 'good',
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

    def test_estimate_estate_planning_cost(self):
        """Test the estate planning cost estimation method."""
        # Test simple case
        cost1 = self.strategy.estimate_estate_planning_cost(5000000, 'simple', 'simple')
        self.assertTrue(cost1 > 0)
        
        # Test complex case
        cost2 = self.strategy.estimate_estate_planning_cost(50000000, 'complex', 'complex')
        self.assertTrue(cost2 > cost1)
        
        # Test family complexity factor
        cost3 = self.strategy.estimate_estate_planning_cost(5000000, 'simple', 'complex')
        self.assertTrue(cost3 > cost1)
        
        # Test estate value factor
        cost4 = self.strategy.estimate_estate_planning_cost(20000000, 'simple', 'simple')
        self.assertTrue(cost4 > cost1)

    def test_analyze_charitable_giving_options(self):
        """Test the charitable giving options analysis."""
        analysis = self.strategy.analyze_charitable_giving_options(
            2500000, 1000000, 5, 0.3
        )
        
        # Verify structure and values
        self.assertEqual(analysis['charitable_goal'], 1000000)
        self.assertEqual(analysis['time_horizon'], 5)
        self.assertEqual(analysis['annual_giving_target'], 200000)
        
        # Verify tax analysis
        self.assertIn('tax_analysis', analysis)
        self.assertEqual(analysis['tax_analysis']['tax_bracket'], "30.0%")
        self.assertEqual(analysis['tax_analysis']['max_annual_deduction'], 250000)
        
        # Verify implementation steps
        self.assertIn('implementation_steps', analysis)
        self.assertTrue(len(analysis['implementation_steps']) > 0)

    def test_create_inheritance_planning_framework(self):
        """Test the inheritance planning framework creation."""
        framework = self.strategy.create_inheritance_planning_framework(
            30000000, 
            self.sample_goal_data['beneficiaries'],
            self.sample_goal_data['estate_components']
        )
        
        # Verify structure
        self.assertEqual(framework['estate_value'], 30000000)
        self.assertTrue(framework['beneficiary_composition']['spouse_exists'])
        self.assertEqual(framework['beneficiary_composition']['child_count'], 2)
        
        # Verify estate composition
        self.assertEqual(framework['estate_composition']['liquid_assets'], 6000000)
        self.assertEqual(framework['estate_composition']['property_assets'], 15000000)
        
        # Verify required instruments
        self.assertIn('Will', framework['required_legal_instruments'])
        
        # Verify distribution recommendations
        self.assertTrue(any(item['beneficiary_type'] == 'Spouse' for item in framework['distribution_recommendations']))
        self.assertTrue(any(item['beneficiary_type'] == 'Multiple Children' for item in framework['distribution_recommendations']))
        
        # Verify implementation timeline
        self.assertTrue(len(framework['implementation_timeline']) > 0)

    def test_analyze_legacy_planning_allocations(self):
        """Test legacy planning allocations analysis."""
        analysis = self.strategy.analyze_legacy_planning_allocations(
            30000000, 55, 'married with children'
        )
        
        # Verify structure
        self.assertEqual(analysis['total_assets'], 30000000)
        self.assertEqual(analysis['age'], 55)
        self.assertEqual(analysis['life_stage'], 'mid')
        self.assertEqual(analysis['family_status'], 'married with children')
        
        # Verify allocations
        self.assertIn('allocation_percentages', analysis)
        self.assertIn('allocation_amounts', analysis)
        self.assertEqual(sum(analysis['allocation_percentages'].values()), 100.0)
        
        # Verify recommendations
        self.assertIn('recommendations', analysis)
        self.assertIn('estate_planning', analysis['recommendations'])
        self.assertIn('charitable_giving', analysis['recommendations'])
        self.assertIn('wealth_transfer', analysis['recommendations'])

    def test_integrate_rebalancing_strategy(self):
        """Test rebalancing strategy integration."""
        rebalancing = self.strategy.integrate_rebalancing_strategy(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertEqual(rebalancing['goal_type'], 'estate_planning')
        self.assertIn('rebalancing_schedule', rebalancing)
        self.assertIn('drift_thresholds', rebalancing)
        
        # Verify custom thresholds
        self.assertIn('asset_bands', rebalancing['drift_thresholds'])
        self.assertTrue(len(rebalancing['drift_thresholds']['asset_bands']) > 0)
        
        # Verify India-specific factors
        self.assertIn('india_specific_legacy_factors', rebalancing)
        self.assertIn('gold_allocation', rebalancing['india_specific_legacy_factors'])
        
        # Verify tax optimization
        self.assertIn('tax_optimization', rebalancing)
        self.assertIn('fiscal_year_timing', rebalancing['tax_optimization'])

    def test_assess_estate_planning_readiness(self):
        """Test estate planning readiness assessment."""
        readiness = self.strategy.assess_estate_planning_readiness(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('readiness_assessment', readiness)
        self.assertIn('document_status', readiness)
        self.assertIn('recommendations', readiness)
        
        # Verify document status
        self.assertIn('essential_documents', readiness['document_status'])
        self.assertTrue(readiness['document_status']['essential_documents']['will']['exists'])
        self.assertTrue(readiness['document_status']['essential_documents']['financial_poa']['exists'])
        self.assertFalse(readiness['document_status']['essential_documents']['healthcare_poa']['exists'])
        
        # Verify readiness score calculation
        self.assertIn('document_score', readiness['readiness_assessment'])
        self.assertTrue(0 <= readiness['readiness_assessment']['document_score'] <= 100)
        
        # Verify recommendations - should include missing healthcare POA
        healthcare_rec = next((rec for rec in readiness['recommendations'] 
                               if 'healthcare' in rec['action'].lower()), None)
        self.assertIsNotNone(healthcare_rec)

    def test_assess_charitable_giving_capability(self):
        """Test charitable giving capability assessment."""
        capability = self.strategy.assess_charitable_giving_capability(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('giving_capacity', capability)
        self.assertIn('tax_efficiency', capability)
        self.assertIn('giving_vehicles', capability)
        self.assertIn('recommendations', capability)
        
        # Verify capacity calculations
        self.assertEqual(capability['giving_capacity']['current_annual_giving'], 300000)
        self.assertIn('sustainable_annual_giving', capability['giving_capacity'])
        self.assertIn('max_tax_advantaged_giving', capability['giving_capacity'])
        
        # Verify tax efficiency
        self.assertEqual(capability['tax_efficiency']['tax_bracket'], "30%")
        self.assertIn('potential_tax_savings', capability['tax_efficiency'])
        
        # Verify giving vehicles
        self.assertEqual(capability['giving_vehicles'][0]['vehicle'], 'Direct Donations')
        
        # Verify capacity level determination
        self.assertIn('capacity_level', capability['giving_capacity'])

    def test_evaluate_wealth_transfer_impact(self):
        """Test wealth transfer impact evaluation."""
        impact = self.strategy.evaluate_wealth_transfer_impact(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('donor_financial_security', impact)
        self.assertIn('wealth_transfer_assessment', impact)
        self.assertIn('recipient_assessments', impact)
        self.assertIn('recommendations', impact)
        
        # Verify donor security assessment
        self.assertIn('status', impact['donor_financial_security'])
        self.assertIn('retirement_funding_ratio', impact['donor_financial_security'])
        
        # Verify wealth transfer assessment
        self.assertIn('asset_liquidity_challenge', impact['wealth_transfer_assessment'])
        self.assertIn('tax_efficiency', impact['wealth_transfer_assessment'])
        
        # Verify recipient assessments
        self.assertEqual(len(impact['recipient_assessments']), 3)  # Three beneficiaries
        self.assertIn('readiness', impact['recipient_assessments'][0])
        self.assertIn('impact', impact['recipient_assessments'][0])
        self.assertIn('recommended_structure', impact['recipient_assessments'][0])
        
        # Verify implementation priorities
        self.assertIn('implementation_priorities', impact)
        self.assertTrue(len(impact['implementation_priorities']) > 0)

    def test_assess_legacy_planning_integration(self):
        """Test legacy planning integration assessment."""
        integration = self.strategy.assess_legacy_planning_integration(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('overall_integration', integration)
        self.assertIn('component_integration', integration)
        self.assertIn('recommendations', integration)
        
        # Verify overall integration score
        self.assertIn('score', integration['overall_integration'])
        self.assertTrue(0 <= integration['overall_integration']['score'] <= 100)
        
        # Verify component integration
        self.assertIn('retirement_planning', integration['component_integration'])
        self.assertIn('tax_planning', integration['component_integration'])
        self.assertIn('risk_management', integration['component_integration'])
        
        # Verify integration framework
        self.assertIn('integration_framework', integration)
        self.assertTrue(len(integration['integration_framework']) > 0)

    def test_optimize_estate_planning_structure(self):
        """Test estate planning structure optimization."""
        optimized = self.strategy.optimize_estate_planning_structure(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('optimized_structure', optimized)
        self.assertIn('implementation_roadmap', optimized)
        self.assertIn('india_specific_considerations', optimized)
        
        # Verify complexity assessment
        self.assertIn('complexity_assessment', optimized['optimized_structure'])
        self.assertTrue(0 <= optimized['optimized_structure']['complexity_assessment']['overall_score'] <= 100)
        
        # Verify structural components
        self.assertIn('structural_components', optimized['optimized_structure'])
        self.assertTrue(len(optimized['optimized_structure']['structural_components']) > 0)
        self.assertTrue(any(comp['component'] == 'Will' for comp in optimized['optimized_structure']['structural_components']))
        
        # Verify implementation roadmap
        self.assertTrue(len(optimized['implementation_roadmap']) > 0)
        
        # Verify India-specific considerations
        self.assertIn('hindu_succession', optimized['india_specific_considerations'])

    def test_optimize_charitable_giving_strategy(self):
        """Test charitable giving strategy optimization."""
        optimized = self.strategy.optimize_charitable_giving_strategy(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('optimized_giving_strategy', optimized)
        self.assertIn('implementation_timeline', optimized)
        self.assertIn('india_specific_considerations', optimized)
        
        # Verify optimized giving strategy
        self.assertIn('primary_vehicle', optimized['optimized_giving_strategy'])
        self.assertIn('secondary_vehicle', optimized['optimized_giving_strategy'])
        self.assertIn('cause_allocation', optimized['optimized_giving_strategy'])
        self.assertIn('optimized_annual_giving', optimized['optimized_giving_strategy'])
        
        # Verify implementation timeline
        self.assertTrue(len(optimized['implementation_timeline']) > 0)
        
        # Verify India-specific considerations
        self.assertIn('section_80g_verification', optimized['india_specific_considerations'])

    def test_optimize_wealth_transfer_plan(self):
        """Test wealth transfer plan optimization."""
        optimized = self.strategy.optimize_wealth_transfer_plan(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertIn('optimized_wealth_transfer', optimized)
        self.assertIn('implementation_timeline', optimized)
        self.assertIn('india_specific_considerations', optimized)
        
        # Verify optimized wealth transfer
        self.assertIn('optimal_transfer_timing', optimized['optimized_wealth_transfer'])
        self.assertIn('optimal_transfer_amount', optimized['optimized_wealth_transfer'])
        self.assertIn('transfer_percentage', optimized['optimized_wealth_transfer'])
        self.assertIn('transfer_vehicles', optimized['optimized_wealth_transfer'])
        self.assertIn('beneficiary_strategies', optimized['optimized_wealth_transfer'])
        
        # Verify transfer vehicles
        self.assertTrue(len(optimized['optimized_wealth_transfer']['transfer_vehicles']) > 0)
        
        # Verify beneficiary strategies
        self.assertEqual(len(optimized['optimized_wealth_transfer']['beneficiary_strategies']), 3)  # Three beneficiaries
        
        # Verify implementation timeline
        self.assertTrue(len(optimized['implementation_timeline']) > 0)
        
        # Verify India-specific considerations
        self.assertIn('gift_documentation', optimized['india_specific_considerations'])

    def test_generate_funding_strategy(self):
        """Test comprehensive funding strategy generation."""
        strategy = self.strategy.generate_funding_strategy(
            self.sample_goal_data
        )
        
        # Verify structure
        self.assertEqual(strategy['goal_type'], 'estate_planning')
        self.assertIn('legacy_details', strategy)
        self.assertIn('constraint_assessments', strategy)
        self.assertIn('optimization_strategies', strategy)
        self.assertIn('legacy_planning_strategies', strategy)
        self.assertIn('india_specific_guidance', strategy)
        self.assertIn('specific_advice', strategy)
        
        # Verify constraint assessments
        self.assertIn('estate_planning_readiness', strategy['constraint_assessments'])
        self.assertIn('charitable_giving_capability', strategy['constraint_assessments'])
        self.assertIn('wealth_transfer_impact', strategy['constraint_assessments'])
        self.assertIn('legacy_planning_integration', strategy['constraint_assessments'])
        
        # Verify optimization strategies
        self.assertIn('estate_planning_structure', strategy['optimization_strategies'])
        self.assertIn('charitable_giving_strategy', strategy['optimization_strategies'])
        self.assertIn('wealth_transfer_plan', strategy['optimization_strategies'])
        
        # Verify legacy planning strategies
        self.assertIn('legacy_allocation', strategy['legacy_planning_strategies'])
        
        # Verify India-specific guidance
        self.assertIn('succession_laws', strategy['india_specific_guidance'])
        self.assertIn('tax_planning', strategy['india_specific_guidance'])
        self.assertIn('cultural_considerations', strategy['india_specific_guidance'])
        
        # Verify specific advice
        self.assertIn('prioritization', strategy['specific_advice'])
        self.assertIn('implementation', strategy['specific_advice'])
        self.assertIn('investment_approach', strategy['specific_advice'])

if __name__ == '__main__':
    unittest.main()