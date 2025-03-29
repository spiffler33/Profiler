"""
Test suite for enhanced DebtRepaymentStrategy with optimization and constraint features.
"""

import unittest
import math
from unittest.mock import MagicMock, patch
from models.funding_strategies.debt_repayment_strategy import DebtRepaymentStrategy

class TestEnhancedDebtRepaymentStrategy(unittest.TestCase):
    """Test cases for enhanced debt repayment strategy with optimization features."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = DebtRepaymentStrategy()
        
        # Sample debt portfolio
        self.sample_debts = [
            {
                'name': 'Credit Card',
                'type': 'credit_card',
                'balance': 200000,
                'interest_rate': 0.36,
                'minimum_payment': 10000
            },
            {
                'name': 'Home Loan',
                'type': 'home_loan',
                'balance': 2000000,
                'interest_rate': 0.085,
                'minimum_payment': 20000
            },
            {
                'name': 'Personal Loan',
                'type': 'personal_loan',
                'balance': 500000,
                'interest_rate': 0.15,
                'minimum_payment': 15000
            }
        ]
        
        # Sample goal data
        self.goal_data = {
            'debts': self.sample_debts,
            'monthly_allocation': 60000,
            'preferred_method': 'hybrid',
            'psychological_profile': 'balanced',
            'monthly_income': 150000,
            'monthly_expenses': 80000,
            'credit_score': 750,
            'time_horizon': 5,
            'target_amount': sum(debt['balance'] for debt in self.sample_debts)
        }

    def test_calculate_emi(self):
        """Test EMI calculation method."""
        # Test normal case
        emi = self.strategy._calculate_emi(100000, 0.10, 5)
        self.assertAlmostEqual(emi, 2124.70, delta=1)
        
        # Test edge cases
        self.assertEqual(self.strategy._calculate_emi(0, 0.10, 5), 0)
        self.assertEqual(self.strategy._calculate_emi(100000, 0, 5), 1666.67, delta=1)
        self.assertEqual(self.strategy._calculate_emi(100000, 0.10, 0), 0)

    def test_estimate_total_interest(self):
        """Test estimation of total interest paid."""
        # Test avalanche method
        avalanche_interest = self.strategy._estimate_total_interest(
            self.sample_debts, 60000, "avalanche"
        )
        self.assertTrue(avalanche_interest > 0)
        
        # Test snowball method
        snowball_interest = self.strategy._estimate_total_interest(
            self.sample_debts, 60000, "snowball"
        )
        self.assertTrue(snowball_interest > 0)
        
        # Avalanche should result in less interest than snowball
        self.assertTrue(avalanche_interest < snowball_interest)
        
        # Test edge cases
        self.assertEqual(self.strategy._estimate_total_interest([], 60000, "avalanche"), 0)
        self.assertEqual(self.strategy._estimate_total_interest(self.sample_debts, 0, "avalanche"), 0)

    def test_estimate_first_payoff_time(self):
        """Test estimation of time to first debt payoff."""
        # Test avalanche method
        avalanche_time = self.strategy._estimate_first_payoff_time(
            self.sample_debts, 60000, "avalanche"
        )
        self.assertTrue(avalanche_time > 0)
        
        # Test snowball method
        snowball_time = self.strategy._estimate_first_payoff_time(
            self.sample_debts, 60000, "snowball"
        )
        self.assertTrue(snowball_time > 0)
        
        # Snowball should pay off first debt faster than avalanche in this case
        # Since the credit card has both highest interest and medium balance
        self.assertTrue(avalanche_time <= snowball_time)
        
        # Test insufficient allocation
        insufficient_allocation = sum(debt['minimum_payment'] for debt in self.sample_debts) - 1000
        self.assertEqual(
            self.strategy._estimate_first_payoff_time(self.sample_debts, insufficient_allocation, "avalanche"),
            float('inf')
        )
        
        # Test edge cases
        self.assertEqual(self.strategy._estimate_first_payoff_time([], 60000, "avalanche"), float('inf'))
        self.assertEqual(self.strategy._estimate_first_payoff_time(self.sample_debts, 0, "avalanche"), float('inf'))

    def test_assess_debt_repayment_capacity(self):
        """Test debt repayment capacity assessment."""
        capacity = self.strategy.assess_debt_repayment_capacity(self.goal_data)
        
        # Verify structure
        self.assertIn('debt_details', capacity)
        self.assertIn('income_details', capacity)
        self.assertIn('repayment_capacity', capacity)
        self.assertIn('recommendations', capacity)
        
        # Verify calculations
        self.assertEqual(capacity['debt_details']['total_debt'], sum(debt['balance'] for debt in self.sample_debts))
        self.assertEqual(capacity['income_details']['monthly_income'], self.goal_data['monthly_income'])
        self.assertEqual(capacity['income_details']['monthly_expenses'], self.goal_data['monthly_expenses'])
        
        # Verify capacity status based on DTI ratio
        dti_ratio = capacity['debt_details']['debt_to_income_ratio'] / 100  # Convert back to decimal
        if dti_ratio > 0.5:
            self.assertEqual(capacity['repayment_capacity']['capacity_status'], "Critical")
        elif dti_ratio > 0.4:
            self.assertEqual(capacity['repayment_capacity']['capacity_status'], "Severe")
        elif dti_ratio > 0.3:
            self.assertEqual(capacity['repayment_capacity']['capacity_status'], "Constrained")
        elif dti_ratio > 0.2:
            self.assertEqual(capacity['repayment_capacity']['capacity_status'], "Challenged")
        else:
            self.assertEqual(capacity['repayment_capacity']['capacity_status'], "Manageable")

    def test_validate_repayment_strategy_fit(self):
        """Test repayment strategy fit validation."""
        # Test balanced psychological profile
        self.goal_data['psychological_profile'] = 'balanced'
        fit1 = self.strategy.validate_repayment_strategy_fit(self.goal_data)
        self.assertIn('recommended_method', fit1)
        self.assertIn('strategy_alignment', fit1)
        self.assertIn('method_comparison', fit1)
        
        # Test analytical psychological profile
        self.goal_data['psychological_profile'] = 'analytical'
        fit2 = self.strategy.validate_repayment_strategy_fit(self.goal_data)
        self.assertEqual(fit2['psychological_optimal'], 'avalanche')
        
        # Test motivational psychological profile
        self.goal_data['psychological_profile'] = 'motivational'
        fit3 = self.strategy.validate_repayment_strategy_fit(self.goal_data)
        self.assertEqual(fit3['psychological_optimal'], 'snowball')
        
        # Test with no debts
        no_debts = self.goal_data.copy()
        no_debts['debts'] = []
        fit4 = self.strategy.validate_repayment_strategy_fit(no_debts)
        self.assertIn('message', fit4)
        self.assertEqual(fit4['recommended_method'], 'hybrid')

    def test_assess_debt_consolidation_feasibility(self):
        """Test debt consolidation feasibility assessment."""
        # Test normal case
        feasibility = self.strategy.assess_debt_consolidation_feasibility(self.goal_data)
        self.assertIn('consolidation_feasibility', feasibility)
        self.assertIn('consolidation_options', feasibility)
        
        # Verify high-interest detection (credit card and personal loan are high interest)
        high_interest_count = sum(1 for debt in self.sample_debts 
                             if debt['interest_rate'] > self.strategy.debt_optimization_params.get('consolidation_threshold', 0.12))
        self.assertEqual(high_interest_count, 2)  # Credit card and personal loan
        
        # Test with no high-interest debt
        low_interest_debts = [
            {
                'name': 'Home Loan 1',
                'type': 'home_loan',
                'balance': 2000000,
                'interest_rate': 0.085,
                'minimum_payment': 20000
            },
            {
                'name': 'Home Loan 2',
                'type': 'home_loan',
                'balance': 1000000,
                'interest_rate': 0.08,
                'minimum_payment': 10000
            }
        ]
        low_interest_goal = self.goal_data.copy()
        low_interest_goal['debts'] = low_interest_debts
        feasibility2 = self.strategy.assess_debt_consolidation_feasibility(low_interest_goal)
        self.assertIn('consolidation_feasibility', feasibility2)
        self.assertEqual(feasibility2['consolidation_feasibility'], "Not Recommended")

    def test_evaluate_debt_repayment_impact(self):
        """Test evaluation of debt repayment impact on other goals."""
        # Add other goals to test impact
        self.goal_data['other_goals'] = [
            {
                'type': 'retirement',
                'target_amount': 5000000,
                'timeline': 20,
                'priority': 'high',
                'monthly_allocation': 15000
            },
            {
                'type': 'education',
                'target_amount': 1000000,
                'timeline': 5,
                'priority': 'medium',
                'monthly_allocation': 10000
            }
        ]
        
        impact = self.strategy.evaluate_debt_repayment_impact(self.goal_data)
        
        # Verify structure
        self.assertIn('debt_metrics', impact)
        self.assertIn('financial_impact', impact)
        self.assertIn('other_goal_impacts', impact)
        self.assertIn('positive_impacts_of_debt_freedom', impact)
        
        # Verify impact calculations
        self.assertEqual(len(impact['other_goal_impacts']), len(self.goal_data['other_goals']))
        self.assertIn('monthly_debt_allocation', impact['financial_impact'])
        self.assertEqual(impact['financial_impact']['monthly_debt_allocation'], 
                     self.goal_data['monthly_allocation'])

    def test_optimize_debt_allocation(self):
        """Test optimization of debt allocation."""
        allocation = self.strategy.optimize_debt_allocation(self.goal_data)
        
        # Verify structure
        self.assertIn('optimized_allocation', allocation)
        self.assertIn('optimization_method', allocation)
        self.assertIn('mathematical_weight', allocation)
        self.assertIn('psychological_weight', allocation)
        
        # Verify allocation calculations
        total_min_payments = sum(debt['minimum_payment'] for debt in self.sample_debts)
        extra_payment = self.goal_data['monthly_allocation'] - total_min_payments
        self.assertEqual(allocation['minimum_payments_total'], total_min_payments)
        self.assertEqual(allocation['extra_payment_amount'], extra_payment)
        
        # Verify allocation priority assignment
        self.assertEqual(len(allocation['optimized_allocation']), len(self.sample_debts))
        for debt in allocation['optimized_allocation']:
            self.assertIn('allocation_priority', debt)
            self.assertIn('optimization_score', debt)
            
        # Verify highest priority debt gets extra payment
        highest_priority = min(allocation['optimized_allocation'], 
                             key=lambda x: x['allocation_priority'])
        self.assertEqual(highest_priority['extra_payment'], extra_payment)

    def test_optimize_repayment_order(self):
        """Test optimization of repayment order."""
        repayment_order = self.strategy.optimize_repayment_order(self.goal_data)
        
        # Verify structure
        self.assertIn('optimized_payoff_order', repayment_order)
        self.assertIn('optimization_method', repayment_order)
        self.assertIn('payoff_timeline', repayment_order)
        self.assertIn('additional_insights', repayment_order)
        
        # Verify enhanced payoff order
        self.assertEqual(len(repayment_order['optimized_payoff_order']), len(self.sample_debts))
        for debt in repayment_order['optimized_payoff_order']:
            self.assertIn('payoff_order', debt)
            self.assertIn('estimated_payoff_months', debt)
            self.assertIn('estimated_payoff_date', debt)
            self.assertIn('tax_considerations', debt)

    def test_optimize_consolidation_strategy(self):
        """Test optimization of consolidation strategy."""
        consolidation = self.strategy.optimize_consolidation_strategy(self.goal_data)
        
        # Verify structure
        self.assertIn('is_consolidation_recommended', consolidation)
        
        if consolidation.get('is_consolidation_recommended', False):
            self.assertIn('recommended_option', consolidation)
            self.assertIn('debts_to_consolidate', consolidation)
            self.assertIn('debts_to_keep_separate', consolidation)
            self.assertIn('financial_impact', consolidation)
            
            # Verify consolidation categorization
            high_interest_count = sum(1 for debt in self.sample_debts 
                                 if debt['interest_rate'] > self.strategy.debt_optimization_params.get('consolidation_threshold', 0.12))
            self.assertEqual(len(consolidation['debts_to_consolidate']), high_interest_count)
            
            # Verify financial impact calculations
            self.assertIn('total_to_consolidate', consolidation['financial_impact'])
            self.assertIn('monthly_savings', consolidation['financial_impact'])
            
            # If monthly savings exist, verify reallocation recommendation
            if consolidation['financial_impact']['monthly_savings'] > 0:
                self.assertIn('reallocation_recommendation', consolidation)
                self.assertEqual(
                    sum(alloc['allocation'] for alloc in consolidation['reallocation_recommendation']['recommended_uses']),
                    consolidation['financial_impact']['monthly_savings']
                )

    def test_generate_funding_strategy(self):
        """Test comprehensive funding strategy generation."""
        strategy = self.strategy.generate_funding_strategy(self.goal_data)
        
        # Verify structure
        self.assertEqual(strategy['goal_type'], 'debt_repayment')
        self.assertEqual(strategy['target_amount'], self.goal_data['target_amount'])
        self.assertEqual(strategy['monthly_allocation'], self.goal_data['monthly_allocation'])
        
        # Verify constraint assessments
        self.assertIn('constraint_assessments', strategy)
        self.assertIn('repayment_capacity', strategy['constraint_assessments'])
        self.assertIn('strategy_fit', strategy['constraint_assessments'])
        self.assertIn('consolidation_feasibility', strategy['constraint_assessments'])
        self.assertIn('financial_impact', strategy['constraint_assessments'])
        
        # Verify optimization strategies
        self.assertIn('optimization_strategies', strategy)
        self.assertIn('debt_allocation', strategy['optimization_strategies'])
        self.assertIn('repayment_order', strategy['optimization_strategies'])
        
        # Verify debt freedom plan
        self.assertIn('debt_freedom_plan', strategy)
        
        # Verify India-specific guidance
        self.assertIn('india_specific_guidance', strategy)
        self.assertIn('tax_optimization', strategy['india_specific_guidance'])
        self.assertIn('debt_types', strategy['india_specific_guidance'])
        self.assertIn('regional_considerations', strategy['india_specific_guidance'])

if __name__ == '__main__':
    unittest.main()