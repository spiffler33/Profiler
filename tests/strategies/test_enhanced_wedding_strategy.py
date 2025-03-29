import unittest
from models.funding_strategies.wedding_strategy import WeddingFundingStrategy

class TestEnhancedWeddingStrategy(unittest.TestCase):
    """Test case for the enhanced WeddingFundingStrategy class with optimization features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.strategy = WeddingFundingStrategy()
        
        # Sample goal data for testing
        self.moderate_wedding_goal = {
            'goal_type': 'wedding',
            'target_amount': 1500000,  # 15 lakh
            'time_horizon': 1.5,       # 18 months
            'risk_profile': 'conservative',
            'current_savings': 300000,
            'monthly_contribution': 50000,
            'region': 'north_india',
            'tier': 'tier_1',
            'category': 'moderate',
            'guest_count': 'large',    # 300-500 guests
            'family_contribution_percent': 50,
            'priorities': ['venue', 'catering', 'sangeet'],
            'annual_income': 1200000   # 12 lakh annual income
        }
        
        self.budget_wedding_goal = {
            'goal_type': 'wedding',
            'target_amount': 600000,   # 6 lakh
            'time_horizon': 1.0,       # 12 months
            'risk_profile': 'conservative',
            'current_savings': 200000,
            'monthly_contribution': 30000,
            'region': 'south_india',
            'tier': 'tier_1',
            'category': 'budget',
            'guest_count': 'small',    # Under 150 guests
            'family_contribution_percent': 40,
            'priorities': ['venue', 'rituals'],
            'annual_income': 800000    # 8 lakh annual income
        }
        
        self.premium_wedding_goal = {
            'goal_type': 'wedding',
            'target_amount': 3000000,  # 30 lakh
            'time_horizon': 2.0,       # 24 months
            'risk_profile': 'moderate',
            'current_savings': 500000,
            'monthly_contribution': 80000,
            'region': 'west_india',
            'tier': 'metro',
            'category': 'premium',
            'guest_count': 'very_large', # Over 500 guests
            'family_contribution_percent': 60,
            'priorities': ['venue', 'catering', 'decor', 'entertainment'],
            'annual_income': 2000000   # 20 lakh annual income
        }
    
    def test_initialization(self):
        """Test the initialization of the strategy class and lazy loading pattern"""
        self.assertIsNotNone(self.strategy)
        self.assertIsNone(self.strategy.optimizer)
        self.assertIsNone(self.strategy.constraints)
        self.assertIsNone(self.strategy.compound_strategy)
    
    def test_lazy_initialization(self):
        """Test the lazy initialization of optimizer, constraints, and compound strategy"""
        # Initialize optimizer
        self.strategy._initialize_optimizer()
        self.assertIsNotNone(self.strategy.optimizer)
        
        # Initialize constraints
        self.strategy._initialize_constraints()
        self.assertIsNotNone(self.strategy.constraints)
        
        # Initialize compound strategy
        self.strategy._initialize_compound_strategy()
        self.assertIsNotNone(self.strategy.compound_strategy)
    
    def test_assess_wedding_budget_feasibility(self):
        """Test budget feasibility assessment"""
        # Test with moderate wedding
        result = self.strategy.assess_wedding_budget_feasibility(self.moderate_wedding_goal)
        self.assertIn('overall_feasibility', result)
        self.assertIn('wedding_cost', result)
        self.assertIn('annual_income', result)
        self.assertIn('cost_to_income_ratio', result)
        self.assertIn('self_contribution', result)
        self.assertIn('projected_savings', result)
        self.assertIn('recommendations', result)
        
        # Test with challenging scenario where wedding cost exceeds annual income
        challenging_goal = self.moderate_wedding_goal.copy()
        challenging_goal['target_amount'] = 2000000  # 20 lakh
        challenging_goal['annual_income'] = 1000000  # 10 lakh
        result_challenging = self.strategy.assess_wedding_budget_feasibility(challenging_goal)
        self.assertIn('limiting_factors', result_challenging)
        self.assertTrue(len(result_challenging['limiting_factors']) > 0)
        self.assertIn('recommendations', result_challenging)
        self.assertTrue(len(result_challenging['recommendations']) > 0)
    
    def test_validate_wedding_timing(self):
        """Test wedding timing validation"""
        # Test with sufficient timeline
        result = self.strategy.validate_wedding_timing(self.premium_wedding_goal)
        self.assertIn('wedding_timeline', result)
        self.assertIn('time_needed_for_saving', result)
        self.assertIn('time_needed_for_planning', result)
        self.assertIn('total_time_recommended', result)
        self.assertIn('timeline_feasibility', result)
        
        # Test with rushed timeline
        rushed_goal = self.premium_wedding_goal.copy()
        rushed_goal['time_horizon'] = 0.5  # 6 months
        result_rushed = self.strategy.validate_wedding_timing(rushed_goal)
        self.assertIn('timeline_feasibility', result_rushed)
        self.assertNotEqual(result_rushed['timeline_feasibility'], 'Adequate')
        self.assertIn('recommendations', result_rushed)
        self.assertTrue(len(result_rushed['recommendations']) > 0)
    
    def test_assess_cultural_expectations(self):
        """Test cultural expectations assessment"""
        # Test North Indian wedding
        result_north = self.strategy.assess_cultural_expectations(self.moderate_wedding_goal)
        self.assertIn('region', result_north)
        self.assertIn('regional_cultural_expectations', result_north)
        self.assertIn('category_expectations', result_north)
        self.assertIn('budget_cultural_alignment', result_north)
        
        # Test South Indian wedding
        result_south = self.strategy.assess_cultural_expectations(self.budget_wedding_goal)
        self.assertIn('regional_cultural_expectations', result_south)
        self.assertNotEqual(result_north['regional_cultural_expectations'], 
                           result_south['regional_cultural_expectations'])
    
    def test_validate_family_contribution_balance(self):
        """Test family contribution balance validation"""
        # Test with standard contribution split
        result = self.strategy.validate_family_contribution_balance(self.moderate_wedding_goal)
        self.assertIn('current_family_contribution', result)
        self.assertIn('affordability_assessment', result)
        self.assertIn('cultural_alignment', result)
        self.assertIn('alternative_scenarios', result)
        
        # Test with challenging self-contribution
        challenging_goal = self.moderate_wedding_goal.copy()
        challenging_goal['family_contribution_percent'] = 20
        challenging_goal['annual_income'] = 800000  # 8 lakh
        result_challenging = self.strategy.validate_family_contribution_balance(challenging_goal)
        self.assertIn('recommendations', result_challenging)
        self.assertTrue(len(result_challenging['recommendations']) > 0)
    
    def test_optimize_wedding_budget(self):
        """Test wedding budget optimization"""
        result = self.strategy.optimize_wedding_budget(self.moderate_wedding_goal)
        self.assertIn('original_budget', result)
        self.assertIn('optimized_budget', result)
        self.assertIn('budget_adjustment_rationale', result)
        self.assertIn('standard_expense_breakdown', result)
        self.assertIn('optimized_expense_breakdown', result)
        self.assertIn('ceremony_budget_allocation', result)
        self.assertIn('total_potential_savings', result)
        self.assertIn('recommendations', result)
    
    def test_optimize_family_contribution(self):
        """Test family contribution optimization"""
        result = self.strategy.optimize_family_contribution(self.moderate_wedding_goal)
        self.assertIn('current_contribution_split', result)
        self.assertIn('financial_capacity_assessment', result)
        self.assertIn('cultural_considerations', result)
        self.assertIn('optimized_contribution', result)
        self.assertIn('scenarios', result)
        self.assertIn('decision_points', result)
        self.assertIn('recommendations', result)
    
    def test_optimize_wedding_timing(self):
        """Test wedding timing optimization"""
        result = self.strategy.optimize_wedding_timing(self.moderate_wedding_goal)
        self.assertIn('timing_assessment', result)
        self.assertIn('seasonal_considerations', result)
        self.assertIn('optimal_timing_options', result)
        self.assertIn('earliest_possible_date', result)
        self.assertIn('recommended_date_range', result)
        self.assertIn('recommendations', result)
    
    def test_optimize_guest_list(self):
        """Test guest list optimization"""
        result = self.strategy.optimize_guest_list(self.premium_wedding_goal)
        self.assertIn('guest_list_assessment', result)
        self.assertIn('optimization_scenarios', result)
        self.assertIn('optimized_guest_list', result)
        self.assertIn('guest_list_tiering_strategy', result)
        self.assertIn('recommendations', result)
    
    def test_generate_funding_strategy(self):
        """Test the complete funding strategy generation with optimizations"""
        result = self.strategy.generate_funding_strategy(self.moderate_wedding_goal)
        
        # Base strategy components
        self.assertIn('wedding_details', result)
        self.assertIn('expense_breakdown', result)
        self.assertIn('wedding_specific_allocation', result)
        
        # Enhanced optimization components
        self.assertIn('optimizations', result)
        self.assertIn('constraint_assessments', result)
        self.assertIn('key_optimization_recommendations', result)
        
        # Check optimization components
        self.assertIn('budget_optimization', result['optimizations'])
        self.assertIn('family_contribution_optimization', result['optimizations'])
        self.assertIn('timing_optimization', result['optimizations'])
        self.assertIn('guest_list_optimization', result['optimizations'])
        
        # Check constraint components
        self.assertIn('budget_feasibility', result['constraint_assessments'])
        self.assertIn('wedding_timing', result['constraint_assessments'])
        self.assertIn('cultural_expectations', result['constraint_assessments'])
        self.assertIn('family_contribution_assessment', result['constraint_assessments'])

if __name__ == '__main__':
    unittest.main()