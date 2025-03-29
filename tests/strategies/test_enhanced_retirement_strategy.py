import unittest
import json
from models.funding_strategies.retirement_strategy import RetirementFundingStrategy

class TestEnhancedRetirementStrategy(unittest.TestCase):
    """Test case for enhanced RetirementFundingStrategy with optimization features."""
    
    def setUp(self):
        """Set up test environment."""
        self.strategy = RetirementFundingStrategy()
        
        # Sample goal data for testing
        self.goal_data = {
            'current_age': 35,
            'retirement_age': 60,
            'monthly_expenses': 80000,
            'current_savings': 2000000,
            'monthly_contribution': 25000,
            'risk_profile': 'moderate',
            'annual_income': 1500000,
            'tax_bracket': 0.30,
            'profile_data': {
                'monthly_income': 125000,
                'risk_profile': 'moderate',
                'monthly_expenses': 70000
            }
        }
    
    def test_nps_allocation_with_tax_benefits(self):
        """Test NPS allocation optimization with tax benefits."""
        result = self.strategy.recommend_nps_allocation(
            self.goal_data['current_age'],
            self.goal_data['retirement_age'],
            self.goal_data['risk_profile'],
            self.goal_data['tax_bracket']
        )
        
        # Verify structure
        self.assertIn('allocation', result)
        self.assertIn('tax_benefits', result)
        
        # Verify allocation percentages
        allocation = result['allocation']
        self.assertIn('E', allocation)  # Equity
        self.assertIn('C', allocation)  # Corporate debt
        self.assertIn('G', allocation)  # Government securities
        
        # Verify total is 100%
        total_allocation = allocation['E'] + allocation['C'] + allocation['G']
        self.assertAlmostEqual(total_allocation, 1.0, places=2)
        
        # Verify tax benefits
        tax_benefits = result['tax_benefits']
        self.assertIn('section_80c', tax_benefits)
        self.assertIn('section_80ccd', tax_benefits)
        self.assertIn('total_annual_benefit', tax_benefits)
        
    def test_retirement_strategy_with_constraints(self):
        """Test complete retirement funding strategy with constraints."""
        result = self.strategy.generate_funding_strategy(self.goal_data)
        
        # Check structure
        self.assertEqual(result['goal_type'], 'retirement')
        self.assertIn('retirement_gap_analysis', result)
        self.assertIn('nps_allocation', result)
        self.assertIn('pension_options', result)
        
        # Check budget feasibility
        self.assertIn('budget_feasibility', result)
        feasibility = result['budget_feasibility']
        self.assertIn('contribution_assessment', feasibility)
        self.assertIn('corpus_assessment', feasibility)
        self.assertIn('age_assessment', feasibility)
        
        # Print for manual verification
        print("Generated retirement strategy with optimizations:")
        print(json.dumps(result, indent=2))
        
if __name__ == '__main__':
    unittest.main()