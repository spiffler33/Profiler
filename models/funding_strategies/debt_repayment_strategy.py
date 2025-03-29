import logging
import math
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class DebtRepaymentStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for debt repayment goals with
    India-specific debt types and repayment considerations.
    
    Enhanced with optimization and constraint features to balance
    between debt avalanche and snowball approaches, optimize tax efficiency,
    and assess debt consolidation opportunities.
    """
    
    def __init__(self):
        """Initialize with debt repayment specific parameters"""
        super().__init__()
        
        # Optimizer, constraints, and compound strategy objects will be lazy initialized
        self.optimizer = None
        self.constraints = None
        self.compound_strategy = None
        
        # Additional debt repayment specific parameters
        self.debt_params = {
            "debt_types": {
                "credit_card": {
                    "typical_interest": 0.36,    # 36% typical interest
                    "priority_level": "very_high", # Priority level for repayment
                    "minimum_payment": 0.05      # 5% of outstanding balance
                },
                "personal_loan": {
                    "typical_interest": 0.15,    # 15% typical interest
                    "priority_level": "high",
                    "minimum_payment": 0.02      # 2% of outstanding balance
                },
                "home_loan": {
                    "typical_interest": 0.085,   # 8.5% typical interest
                    "priority_level": "low",
                    "minimum_payment": 0.01      # 1% of outstanding balance
                },
                "car_loan": {
                    "typical_interest": 0.10,    # 10% typical interest
                    "priority_level": "medium",
                    "minimum_payment": 0.02      # 2% of outstanding balance
                },
                "education_loan": {
                    "typical_interest": 0.09,    # 9% typical interest
                    "priority_level": "medium",
                    "minimum_payment": 0.015     # 1.5% of outstanding balance
                },
                "gold_loan": {
                    "typical_interest": 0.12,    # 12% typical interest
                    "priority_level": "high",
                    "minimum_payment": 0.03      # 3% of outstanding balance
                }
            },
            "repayment_methods": {
                "avalanche": {
                    "description": "Pay highest interest debt first",
                    "pros": ["Mathematically optimal", "Minimizes total interest", "Fastest debt-free path"],
                    "cons": ["Slower visible progress if high-interest debts are large", "Requires discipline"]
                },
                "snowball": {
                    "description": "Pay smallest balance debt first",
                    "pros": ["Quick psychological wins", "Builds momentum", "Simplifies finances faster"],
                    "cons": ["Mathematically suboptimal", "Potentially higher total interest"]
                },
                "hybrid": {
                    "description": "Modified approach considering both interest and balance",
                    "pros": ["Balances mathematical and psychological benefits", "Flexible", "Practical"],
                    "cons": ["Requires more analysis", "Not as straightforward"]
                }
            },
            "debt_consolidation": {
                "personal_loan": {
                    "typical_interest": 0.12,    # 12% for debt consolidation
                    "eligibility_criteria": "Good credit score, stable income",
                    "pros": ["Single payment", "Potentially lower interest", "Fixed timeline"],
                    "cons": ["Application process", "Potential fees", "Good credit required"]
                },
                "balance_transfer": {
                    "typical_interest": 0.0,     # 0% introductory rate
                    "typical_duration": 6,       # 6 months typical for 0% period
                    "typical_fee": 0.02,         # 2% balance transfer fee
                    "pros": ["Low/no interest period", "Simplified payments"],
                    "cons": ["Temporary solution", "Transfer fees", "Limited eligibility"]
                },
                "loan_against_property": {
                    "typical_interest": 0.09,    # 9% for loan against property
                    "eligibility_criteria": "Property ownership, good repayment capacity",
                    "pros": ["Low interest rate", "Large loan amount", "Longer tenure"],
                    "cons": ["Risk to property", "Processing time", "Fees and charges"]
                }
            },
            "tax_benefits": {
                "home_loan": {
                    "principal": {
                        "section": "80C",
                        "limit": 150000        # ₹1.5L limit
                    },
                    "interest": {
                        "section": "24",
                        "limit": 200000        # ₹2L limit for self-occupied
                    }
                },
                "education_loan": {
                    "interest": {
                        "section": "80E",
                        "limit": "No limit",   # No limit for interest deduction
                        "duration": "8 years"  # Available for 8 years
                    }
                }
            },
            "prepayment_penalties": {
                "home_loan": {
                    "floating_rate": 0.0,      # No penalty for floating rate
                    "fixed_rate": 0.02         # 2% typically for fixed rate
                },
                "personal_loan": 0.02,         # 2% typically
                "car_loan": 0.03,              # 3% typically
                "education_loan": 0.0          # No penalty typically
            }
        }
        
        # Load debt repayment specific parameters
        self._load_debt_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with debt-specific optimization parameters
            super()._initialize_optimizer()
            
            # Debt-specific optimization parameters
            self.debt_optimization_params = {
                'avalanche_weight': 0.6,       # Weight for mathematical optimization (interest rate focus)
                'snowball_weight': 0.4,        # Weight for psychological optimization (small balance focus)
                'consolidation_threshold': 0.12,  # Interest rate threshold for considering consolidation (12%)
                'payment_allocation_safety': 0.1,  # Keep 10% for emergency buffer
                'tax_optimization_priority': 0.3   # Weight for tax optimization considerations
            }
    
    def _initialize_constraints(self):
        """Initialize the funding constraints with lazy loading pattern"""
        if not hasattr(self, 'constraints') or self.constraints is None:
            # Initialize base constraints
            super()._initialize_constraints()
            
            # Debt-specific constraint parameters are defined in this class directly
            # No need to register them with the constraints object as it doesn't support that
    
    def _initialize_compound_strategy(self):
        """Initialize the compound strategy with lazy loading pattern"""
        if not hasattr(self, 'compound_strategy') or self.compound_strategy is None:
            # Initialize base compound strategy
            super()._initialize_compound_strategy()
            
            # Debt-specific strategies are defined in this class directly
            # They will be called explicitly in our optimization methods

    def _load_debt_parameters(self):
        """Load debt repayment specific parameters from service"""
        if self.param_service:
            try:
                # Load debt types
                debt_types = self.param_service.get_parameter('debt_types')
                if debt_types:
                    self.debt_params['debt_types'].update(debt_types)
                
                # Load repayment methods
                repayment_methods = self.param_service.get_parameter('debt_repayment_methods')
                if repayment_methods:
                    self.debt_params['repayment_methods'].update(repayment_methods)
                
                # Load debt consolidation
                debt_consolidation = self.param_service.get_parameter('debt_consolidation')
                if debt_consolidation:
                    self.debt_params['debt_consolidation'].update(debt_consolidation)
                
                # Load tax benefits
                tax_benefits = self.param_service.get_parameter('debt_tax_benefits')
                if tax_benefits:
                    self.debt_params['tax_benefits'].update(tax_benefits)
                
                # Load prepayment penalties
                prepayment_penalties = self.param_service.get_parameter('debt_prepayment_penalties')
                if prepayment_penalties:
                    self.debt_params['prepayment_penalties'].update(prepayment_penalties)
                
            except Exception as e:
                logger.error(f"Error loading debt parameters: {e}")
                # Continue with default parameters
    
    def analyze_debt_portfolio(self, debts):
        """
        Analyze debt portfolio with summary statistics and insights.
        
        Args:
            debts: List of debt dictionaries with details
            
        Returns:
            Dictionary with debt portfolio analysis
        """
        # Calculate summary statistics
        total_debt = sum(debt.get('balance', 0) for debt in debts)
        total_monthly_payment = sum(debt.get('monthly_payment', 0) for debt in debts)
        
        # Calculate weighted average interest rate
        weighted_interest = sum(debt.get('balance', 0) * debt.get('interest_rate', 0) for debt in debts)
        avg_interest_rate = weighted_interest / total_debt if total_debt > 0 else 0
        
        # Categorize debts by type and priority
        high_priority_debt = 0
        medium_priority_debt = 0
        low_priority_debt = 0
        
        debt_by_type = {}
        
        for debt in debts:
            debt_type = debt.get('type', 'other').lower()
            balance = debt.get('balance', 0)
            
            # Add to debt by type
            if debt_type not in debt_by_type:
                debt_by_type[debt_type] = 0
            debt_by_type[debt_type] += balance
            
            # Categorize by priority
            priority = self.debt_params['debt_types'].get(debt_type, {}).get('priority_level', 'medium')
            
            if priority == 'very_high' or priority == 'high':
                high_priority_debt += balance
            elif priority == 'medium':
                medium_priority_debt += balance
            else:
                low_priority_debt += balance
                
        # Analyze debt-to-income ratio (assuming monthly income is provided)
        monthly_income = sum(debt.get('monthly_income', 0) for debt in debts)
        if not monthly_income:
            # Default assumption if no income provided
            monthly_income = total_monthly_payment * 3  # Assume payments are ~1/3 of income
            
        debt_to_income_ratio = total_monthly_payment / monthly_income if monthly_income > 0 else 0
        
        # Determine debt health status
        if debt_to_income_ratio > 0.5:
            debt_health = "Critical"
            health_description = "Debt payments exceed 50% of income, immediate action required"
        elif debt_to_income_ratio > 0.4:
            debt_health = "Concerning"
            health_description = "Debt payments between 40-50% of income, serious attention needed"
        elif debt_to_income_ratio > 0.3:
            debt_health = "Caution"
            health_description = "Debt payments between 30-40% of income, careful management needed"
        elif debt_to_income_ratio > 0.2:
            debt_health = "Moderate"
            health_description = "Debt payments between 20-30% of income, monitor and manage"
        else:
            debt_health = "Healthy"
            health_description = "Debt payments below 20% of income, generally manageable"
            
        return {
            'total_debt': round(total_debt),
            'total_monthly_payment': round(total_monthly_payment),
            'weighted_avg_interest_rate': round(avg_interest_rate * 100, 2),
            'debt_breakdown_by_type': {k: round(v) for k, v in debt_by_type.items()},
            'debt_breakdown_by_priority': {
                'high_priority': round(high_priority_debt),
                'medium_priority': round(medium_priority_debt),
                'low_priority': round(low_priority_debt)
            },
            'debt_to_income_ratio': round(debt_to_income_ratio * 100, 1),
            'debt_health_status': debt_health,
            'health_description': health_description
        }
    
    def recommend_repayment_strategy(self, debts, monthly_allocation, prefer_method=None):
        """
        Recommend debt repayment strategy based on debts and preferences.
        
        Args:
            debts: List of debt dictionaries with details
            monthly_allocation: Monthly amount allocated for debt repayment
            prefer_method: Preferred repayment method (avalanche, snowball, hybrid)
            
        Returns:
            Dictionary with recommended repayment strategy
        """
        # Ensure we have minimum payments for each debt
        for debt in debts:
            debt_type = debt.get('type', 'other').lower()
            balance = debt.get('balance', 0)
            
            # If minimum payment not specified, estimate it
            if 'minimum_payment' not in debt or debt['minimum_payment'] <= 0:
                min_payment_rate = self.debt_params['debt_types'].get(debt_type, {}).get('minimum_payment', 0.02)
                debt['minimum_payment'] = balance * min_payment_rate
                
            # If interest rate not specified, use typical
            if 'interest_rate' not in debt or debt['interest_rate'] <= 0:
                typical_rate = self.debt_params['debt_types'].get(debt_type, {}).get('typical_interest', 0.10)
                debt['interest_rate'] = typical_rate
                
        # Calculate total minimum payment
        total_minimum_payment = sum(debt.get('minimum_payment', 0) for debt in debts)
        
        # Check if allocation is sufficient
        if monthly_allocation < total_minimum_payment:
            return {
                'error': 'Insufficient allocation',
                'message': 'Monthly allocation is less than total minimum payments',
                'required_minimum': round(total_minimum_payment),
                'allocation': round(monthly_allocation),
                'shortfall': round(total_minimum_payment - monthly_allocation)
            }
            
        # Determine available amount for extra payments
        extra_payment_amount = monthly_allocation - total_minimum_payment
        
        # Prepare repayment strategy
        strategy = {
            'monthly_allocation': round(monthly_allocation),
            'minimum_payments_total': round(total_minimum_payment),
            'extra_payment_amount': round(extra_payment_amount),
            'recommended_payoff_order': []
        }
        
        # Determine preferred method if not specified
        if not prefer_method:
            # Default to hybrid approach
            prefer_method = 'hybrid'
            
        # Sort debts based on selected method
        if prefer_method.lower() == 'avalanche':
            # Sort by interest rate (highest first)
            sorted_debts = sorted(debts, key=lambda x: x.get('interest_rate', 0), reverse=True)
            strategy['method'] = 'avalanche'
            strategy['method_description'] = self.debt_params['repayment_methods']['avalanche']['description']
            
        elif prefer_method.lower() == 'snowball':
            # Sort by balance (lowest first)
            sorted_debts = sorted(debts, key=lambda x: x.get('balance', 0))
            strategy['method'] = 'snowball'
            strategy['method_description'] = self.debt_params['repayment_methods']['snowball']['description']
            
        else:  # hybrid
            # Create a score based on both interest rate and balance
            for debt in debts:
                # Normalize interest rate (0-1 scale where 1 is highest)
                max_interest = max(d.get('interest_rate', 0) for d in debts)
                min_interest = min(d.get('interest_rate', 0) for d in debts)
                interest_range = max_interest - min_interest
                
                if interest_range > 0:
                    interest_score = (debt.get('interest_rate', 0) - min_interest) / interest_range
                else:
                    interest_score = 0.5  # All same interest rate
                    
                # Normalize balance inversely (0-1 scale where 1 is lowest)
                max_balance = max(d.get('balance', 0) for d in debts)
                min_balance = min(d.get('balance', 0) for d in debts)
                balance_range = max_balance - min_balance
                
                if balance_range > 0:
                    balance_score = 1 - ((debt.get('balance', 0) - min_balance) / balance_range)
                else:
                    balance_score = 0.5  # All same balance
                    
                # Calculate hybrid score (60% weight to interest, 40% to balance)
                debt['hybrid_score'] = (interest_score * 0.6) + (balance_score * 0.4)
                
            # Sort by hybrid score (highest first)
            sorted_debts = sorted(debts, key=lambda x: x.get('hybrid_score', 0), reverse=True)
            strategy['method'] = 'hybrid'
            strategy['method_description'] = self.debt_params['repayment_methods']['hybrid']['description']
                
        # Create payoff order with payment allocation
        for debt in sorted_debts:
            strategy['recommended_payoff_order'].append({
                'name': debt.get('name', f"{debt.get('type', 'Debt')} {debt.get('id', '')}"),
                'type': debt.get('type', 'other'),
                'balance': round(debt.get('balance', 0)),
                'interest_rate': round(debt.get('interest_rate', 0) * 100, 2),
                'minimum_payment': round(debt.get('minimum_payment', 0))
            })
            
        # Calculate and add focused payment for first debt
        if sorted_debts:
            first_debt = strategy['recommended_payoff_order'][0]
            first_debt['recommended_payment'] = round(first_debt['minimum_payment'] + extra_payment_amount)
            first_debt['extra_payment'] = round(extra_payment_amount)
            
        # Calculate estimated time to debt freedom
        strategy['payoff_timeline'] = self.calculate_debt_payoff_timeline(
            sorted_debts, monthly_allocation
        )
        
        # Add method-specific insights
        if prefer_method.lower() == 'avalanche':
            strategy['method_insights'] = [
                "Focus on highest interest debt first to minimize total interest",
                "Continue making minimum payments on all other debts",
                "When highest interest debt is paid, roll payment to next highest",
                "This method saves the most money overall"
            ]
        elif prefer_method.lower() == 'snowball':
            strategy['method_insights'] = [
                "Focus on smallest balance debt first for quick wins",
                "Continue making minimum payments on all other debts",
                "Each debt payoff creates momentum and simplifies finances",
                "This method provides psychological rewards through frequent successes"
            ]
        else:  # hybrid
            strategy['method_insights'] = [
                "Balances mathematical optimization with psychological factors",
                "Considers both interest rates and balances for prioritization",
                "Provides good flexibility for your specific situation",
                "Combine with debt consolidation for optimal results"
            ]
            
        return strategy
    
    def calculate_debt_payoff_timeline(self, debts, monthly_allocation):
        """
        Calculate detailed debt payoff timeline.
        
        Args:
            debts: List of debt dictionaries with details (sorted by payoff priority)
            monthly_allocation: Monthly amount allocated for debt repayment
            
        Returns:
            Dictionary with payoff timeline details
        """
        # Create a copy of debts to avoid modifying the original
        working_debts = [debt.copy() for debt in debts]
        
        # Initialize timeline
        months_to_freedom = 0
        total_interest_paid = 0
        milestone_months = []
        
        # Track monthly status until all debts are paid
        monthly_snapshots = []
        
        # Continue until all debts are paid off
        while working_debts and months_to_freedom < 360:  # Cap at 30 years
            months_to_freedom += 1
            month_allocation = monthly_allocation
            month_interest = 0
            month_principal = 0
            
            # Make minimum payments on all debts
            for debt in working_debts:
                # Calculate interest for this month
                monthly_interest = debt['balance'] * (debt['interest_rate'] / 12)
                month_interest += monthly_interest
                
                # Apply minimum payment or full balance if smaller
                payment = min(debt['minimum_payment'], debt['balance'] + monthly_interest)
                
                # Adjust balances
                principal_payment = payment - monthly_interest
                month_principal += principal_payment
                debt['balance'] -= principal_payment
                
                # Update total interest paid
                total_interest_paid += monthly_interest
                
                # Update allocation remaining
                month_allocation -= payment
                
            # Apply any extra payment to highest priority debt (first in list)
            if working_debts and month_allocation > 0:
                # Calculate interest already applied above
                highest_debt = working_debts[0]
                
                # Apply remaining allocation to principal
                principal_payment = min(month_allocation, highest_debt['balance'])
                highest_debt['balance'] -= principal_payment
                month_principal += principal_payment
                
            # Remove any fully paid debts
            working_debts = [debt for debt in working_debts if debt['balance'] > 1]  # Allow for tiny rounding errors
            
            # Track milestone when a debt is paid off
            if len(working_debts) < len(debts) - len(milestone_months):
                milestone_months.append({
                    'month': months_to_freedom,
                    'debt_paid': debts[len(milestone_months)].get('name', f"Debt {len(milestone_months) + 1}"),
                    'remaining_debts': len(working_debts),
                    'total_interest_so_far': round(total_interest_paid)
                })
                
            # Create snapshot every 3 months for the first year, then every 6 months
            if months_to_freedom <= 12 and months_to_freedom % 3 == 0:
                monthly_snapshots.append({
                    'month': months_to_freedom,
                    'remaining_balance': round(sum(debt['balance'] for debt in working_debts)),
                    'interest_paid_so_far': round(total_interest_paid),
                    'debts_remaining': len(working_debts)
                })
            elif months_to_freedom > 12 and months_to_freedom % 6 == 0:
                monthly_snapshots.append({
                    'month': months_to_freedom,
                    'remaining_balance': round(sum(debt['balance'] for debt in working_debts)),
                    'interest_paid_so_far': round(total_interest_paid),
                    'debts_remaining': len(working_debts)
                })
                
        return {
            'months_to_debt_freedom': months_to_freedom,
            'years_to_debt_freedom': round(months_to_freedom / 12, 1),
            'total_interest_paid': round(total_interest_paid),
            'debt_payoff_milestones': milestone_months,
            'progress_snapshots': monthly_snapshots
        }
    
    def evaluate_debt_consolidation(self, debts):
        """
        Evaluate debt consolidation options.
        
        Args:
            debts: List of debt dictionaries with details
            
        Returns:
            Dictionary with debt consolidation recommendations
        """
        # Filter for high-interest debts that make sense to consolidate
        high_interest_debts = [debt for debt in debts if debt.get('interest_rate', 0) > 0.12]  # Above 12%
        
        # Skip if no high-interest debts
        if not high_interest_debts:
            return {
                'recommendation': 'No consolidation needed',
                'reason': 'Existing debts do not have high enough interest rates to benefit from consolidation'
            }
            
        # Calculate total high-interest debt
        high_interest_total = sum(debt.get('balance', 0) for debt in high_interest_debts)
        weighted_interest = sum(debt.get('balance', 0) * debt.get('interest_rate', 0) for debt in high_interest_debts)
        avg_high_interest = weighted_interest / high_interest_total if high_interest_total > 0 else 0
        
        # Evaluate personal loan option
        personal_loan_rate = self.debt_params['debt_consolidation']['personal_loan']['typical_interest']
        personal_loan_savings = high_interest_total * (avg_high_interest - personal_loan_rate)
        
        # Evaluate balance transfer option
        # Assume 6 month 0% period followed by personal loan rate
        balance_transfer_fee = self.debt_params['debt_consolidation']['balance_transfer']['typical_fee']
        balance_transfer_period = self.debt_params['debt_consolidation']['balance_transfer']['typical_duration']
        
        # Calculate interest saved during 0% period
        balance_transfer_interest_saved = high_interest_total * avg_high_interest * (balance_transfer_period / 12)
        
        # Calculate fee
        balance_transfer_fee_amount = high_interest_total * balance_transfer_fee
        
        # Net savings
        balance_transfer_net_savings = balance_transfer_interest_saved - balance_transfer_fee_amount
        
        # Evaluate loan against property option (if any property debt exists)
        property_loan_option = None
        home_loans = [debt for debt in debts if debt.get('type', '').lower() == 'home_loan']
        
        if home_loans:
            # Check if there's sufficient property value to offer as collateral
            # This is a simplification - in reality would need property valuation
            property_value = sum(debt.get('original_amount', debt.get('balance', 0) * 1.5) for debt in home_loans)
            
            # Assume loan against property available up to 70% of value
            available_lap = property_value * 0.7 - sum(debt.get('balance', 0) for debt in home_loans)
            
            if available_lap >= high_interest_total:
                lap_rate = self.debt_params['debt_consolidation']['loan_against_property']['typical_interest']
                lap_savings = high_interest_total * (avg_high_interest - lap_rate)
                
                property_loan_option = {
                    'method': 'Loan Against Property',
                    'available_amount': round(available_lap),
                    'interest_rate': round(lap_rate * 100, 2),
                    'potential_savings': round(lap_savings),
                    'pros': self.debt_params['debt_consolidation']['loan_against_property']['pros'],
                    'cons': self.debt_params['debt_consolidation']['loan_against_property']['cons']
                }
                
        # Determine best option
        options = []
        
        # Personal loan option
        options.append({
            'method': 'Personal Loan Consolidation',
            'applicable_debt': round(high_interest_total),
            'current_avg_rate': round(avg_high_interest * 100, 2),
            'consolidation_rate': round(personal_loan_rate * 100, 2),
            'potential_savings': round(personal_savings),
            'pros': self.debt_params['debt_consolidation']['personal_loan']['pros'],
            'cons': self.debt_params['debt_consolidation']['personal_loan']['cons']
        })
        
        # Balance transfer option
        options.append({
            'method': 'Balance Transfer',
            'applicable_debt': round(high_interest_total),
            'introductory_rate': '0%',
            'introductory_period': f"{balance_transfer_period} months",
            'transfer_fee': round(balance_transfer_fee_amount),
            'net_savings': round(balance_transfer_net_savings),
            'pros': self.debt_params['debt_consolidation']['balance_transfer']['pros'],
            'cons': self.debt_params['debt_consolidation']['balance_transfer']['cons']
        })
        
        # Add property loan option if available
        if property_loan_option:
            options.append(property_loan_option)
            
        # Select best recommendation
        # Simple decision: highest potential savings
        best_option = max(options, key=lambda x: x.get('potential_savings', 0) if 'potential_savings' in x else x.get('net_savings', 0))
        
        return {
            'high_interest_debt_total': round(high_interest_total),
            'current_weighted_avg_rate': round(avg_high_interest * 100, 2),
            'recommended_option': best_option,
            'all_options': options,
            'implementation_steps': [
                "Compare actual rates from multiple lenders (market rates may differ from estimates)",
                "Check for hidden fees and charges",
                "Review terms and conditions carefully",
                "Apply only after creating a firm repayment plan",
                "Continue making payments on existing debts until consolidation is complete"
            ]
        }
    
    def analyze_tax_optimization(self, debts, tax_bracket=0.3):
        """
        Analyze tax optimization opportunities for debt.
        
        Args:
            debts: List of debt dictionaries with details
            tax_bracket: Income tax bracket (e.g., 0.3 for 30%)
            
        Returns:
            Dictionary with tax optimization recommendations
        """
        # Initialize tax benefits
        tax_benefits = []
        total_annual_benefit = 0
        
        # Look for tax-advantaged debts
        for debt in debts:
            debt_type = debt.get('type', '').lower()
            
            if debt_type == 'home_loan':
                balance = debt.get('balance', 0)
                annual_interest = balance * debt.get('interest_rate', 0)
                annual_principal = debt.get('annual_principal_payment', balance * 0.05)  # Estimate if not provided
                
                # Principal repayment deduction (80C)
                principal_limit = self.debt_params['tax_benefits']['home_loan']['principal']['limit']
                principal_benefit = min(annual_principal, principal_limit) * tax_bracket
                
                # Interest deduction (Section 24)
                interest_limit = self.debt_params['tax_benefits']['home_loan']['interest']['limit']
                interest_benefit = min(annual_interest, interest_limit) * tax_bracket
                
                if principal_benefit > 0 or interest_benefit > 0:
                    tax_benefits.append({
                        'debt_type': 'Home Loan',
                        'principal_deduction': {
                            'section': '80C',
                            'eligible_amount': round(min(annual_principal, principal_limit)),
                            'tax_benefit': round(principal_benefit)
                        },
                        'interest_deduction': {
                            'section': '24',
                            'eligible_amount': round(min(annual_interest, interest_limit)),
                            'tax_benefit': round(interest_benefit)
                        },
                        'total_benefit': round(principal_benefit + interest_benefit)
                    })
                    total_annual_benefit += principal_benefit + interest_benefit
                    
            elif debt_type == 'education_loan':
                annual_interest = debt.get('balance', 0) * debt.get('interest_rate', 0)
                
                # Interest deduction (80E)
                # No limit for education loan interest
                interest_benefit = annual_interest * tax_bracket
                
                if interest_benefit > 0:
                    tax_benefits.append({
                        'debt_type': 'Education Loan',
                        'interest_deduction': {
                            'section': '80E',
                            'eligible_amount': round(annual_interest),
                            'tax_benefit': round(interest_benefit),
                            'note': 'Available for 8 years from the year repayment begins'
                        },
                        'total_benefit': round(interest_benefit)
                    })
                    total_annual_benefit += interest_benefit
                    
        # Create optimization recommendations
        recommendations = []
        
        if any(debt.get('type', '').lower() == 'home_loan' for debt in debts):
            recommendations.append(
                "Claim both principal (80C) and interest (24) deductions for home loan"
            )
            recommendations.append(
                "If home loan interest exceeds ₹2 lakhs, consider renting out property to claim unlimited interest deduction"
            )
            
        if any(debt.get('type', '').lower() == 'education_loan' for debt in debts):
            recommendations.append(
                "Ensure education loan interest deduction is claimed under Section 80E (no upper limit)"
            )
            
        if any(debt.get('type', '').lower() not in ['home_loan', 'education_loan'] for debt in debts):
            recommendations.append(
                "Consider restructuring non-tax-advantaged debt into tax-advantaged forms if appropriate"
            )
            
        return {
            'annual_tax_benefits': round(total_annual_benefit),
            'tax_bracket_used': f"{tax_bracket * 100}%",
            'detailed_benefits': tax_benefits,
            'optimization_recommendations': recommendations
        }
    
    def create_debt_freedom_plan(self, debts, monthly_allocation, preferred_method=None):
        """
        Create a comprehensive debt freedom plan.
        
        Args:
            debts: List of debt dictionaries with details
            monthly_allocation: Monthly amount allocated for debt repayment
            preferred_method: Preferred repayment method
            
        Returns:
            Dictionary with comprehensive debt freedom plan
        """
        # Analyze debt portfolio
        portfolio_analysis = self.analyze_debt_portfolio(debts)
        
        # Get repayment strategy
        repayment_strategy = self.recommend_repayment_strategy(
            debts, monthly_allocation, preferred_method
        )
        
        # Check for sufficient allocation
        if 'error' in repayment_strategy:
            return {
                'error': 'Insufficient allocation',
                'portfolio_analysis': portfolio_analysis,
                'minimum_required': repayment_strategy['required_minimum'],
                'current_allocation': monthly_allocation,
                'shortfall': repayment_strategy['shortfall']
            }
            
        # Evaluate debt consolidation options
        consolidation_analysis = self.evaluate_debt_consolidation(debts)
        
        # Analyze tax optimization opportunities (assume 30% tax bracket if not specified)
        tax_bracket = 0.3
        # Try to extract from debts if available
        for debt in debts:
            if 'tax_bracket' in debt:
                tax_bracket = debt['tax_bracket']
                break
                
        tax_optimization = self.analyze_tax_optimization(debts, tax_bracket)
        
        # Create acceleration strategies
        acceleration_strategies = [
            {
                'strategy': 'One-time payment from savings',
                'potential_impact': 'Immediate reduction in principal and interest',
                'considerations': [
                    'Maintain emergency fund of 3-6 months',
                    'Apply to highest interest debt first',
                    'Consider prepayment penalties'
                ]
            },
            {
                'strategy': 'Income increase allocation',
                'potential_impact': 'Shorten payoff timeline as income grows',
                'implementation': 'Dedicate 50% of any raise or bonus to debt repayment'
            },
            {
                'strategy': 'Expense reduction',
                'potential_impact': 'Increase monthly allocation',
                'implementation': 'Review budget categories for potential savings'
            },
            {
                'strategy': 'Side income generation',
                'potential_impact': 'Additional cash flow for debt repayment',
                'implementation': 'Dedicate specific side gigs to debt freedom'
            },
            {
                'strategy': 'Refinancing/consolidation',
                'potential_impact': 'Lower rates and simplified payments',
                'considerations': consolidation_analysis['recommended_option']['method']
            }
        ]
        
        # Calculate how additional payments would affect timeline
        acceleration_scenarios = {}
        base_months = repayment_strategy['payoff_timeline']['months_to_debt_freedom']
        
        # Calculate impact of additional monthly payments
        additional_amounts = [5000, 10000, 20000]
        for amount in additional_amounts:
            # Skip if amount is too small relative to allocation
            if amount < monthly_allocation * 0.1:
                continue
                
            # Estimate impact using a simplification
            total_debt = portfolio_analysis['total_debt']
            avg_rate = portfolio_analysis['weighted_avg_interest_rate'] / 100
            
            # Calculate months with increased payment
            # This is an approximation - actual calculation would require debt-by-debt analysis
            new_payment = monthly_allocation + amount
            if new_payment > 0:
                # Estimate using remaining balance and increased payment
                # This is an approximation that works reasonably well
                estimated_months = -math.log(1 - (total_debt * avg_rate / 12) / new_payment) / math.log(1 + avg_rate / 12)
                month_reduction = max(0, base_months - estimated_months)
                
                acceleration_scenarios[f"additional_{amount}_monthly"] = {
                    'additional_amount': amount,
                    'new_monthly_payment': round(monthly_allocation + amount),
                    'estimated_months_saved': round(month_reduction),
                    'new_payoff_time_months': round(estimated_months)
                }
                
        # Combine all analyses into comprehensive plan
        plan = {
            'debt_portfolio_analysis': portfolio_analysis,
            'repayment_strategy': repayment_strategy,
            'consolidation_options': consolidation_analysis,
            'tax_optimization': tax_optimization,
            'acceleration_strategies': acceleration_strategies,
            'acceleration_scenarios': acceleration_scenarios,
            'post_debt_freedom': {
                'monthly_cash_flow_increase': round(monthly_allocation),
                'recommended_allocation': {
                    'emergency_fund': f"{round(monthly_allocation * 0.2)} (20%)",
                    'retirement': f"{round(monthly_allocation * 0.4)} (40%)",
                    'other_goals': f"{round(monthly_allocation * 0.3)} (30%)",
                    'lifestyle': f"{round(monthly_allocation * 0.1)} (10%)"
                },
                'wealth_building_transition': [
                    "Maintain debt-free lifestyle by avoiding new consumer debt",
                    "Redirect debt payments to wealth-building automatically",
                    "Gradually increase lifestyle only after financial goals are on track",
                    "Use newfound financial freedom to increase income and investments"
                ]
            }
        }
        
        return plan
    
    def assess_debt_repayment_capacity(self, goal_data):
        """
        Assess the capacity to repay debts based on income, expense, 
        and debt levels, focusing on sustainable repayment.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with debt repayment capacity assessment
        """
        # Extract necessary information
        debts = goal_data.get('debts', [])
        monthly_income = goal_data.get('monthly_income', 0)
        monthly_expenses = goal_data.get('monthly_expenses', 0)
        
        # Calculate total debt
        total_debt = sum(debt.get('balance', 0) for debt in debts) if debts else goal_data.get('target_amount', 0)
        
        # Calculate total minimum payments
        total_minimum_payment = 0
        for debt in debts:
            debt_type = debt.get('type', 'other').lower()
            balance = debt.get('balance', 0)
            
            # Use provided minimum payment or estimate it
            if 'minimum_payment' in debt and debt['minimum_payment'] > 0:
                total_minimum_payment += debt['minimum_payment']
            else:
                # Get minimum payment rate from parameters
                min_payment_rate = self.debt_params['debt_types'].get(debt_type, {}).get('minimum_payment', 0.02)
                total_minimum_payment += balance * min_payment_rate
        
        # Calculate available income for debt repayment
        disposable_income = monthly_income - monthly_expenses if monthly_income > 0 else 0
        
        # Calculate debt-to-income (DTI) ratio
        dti_ratio = total_minimum_payment / monthly_income if monthly_income > 0 else float('inf')
        
        # Calculate total debt to annual income ratio
        annual_income = monthly_income * 12 if monthly_income > 0 else 0
        debt_to_annual_income = total_debt / annual_income if annual_income > 0 else float('inf')
        
        # Determine repayment capacity status
        if dti_ratio > 0.5:
            capacity_status = "Critical"
            capacity_description = "Debt payments exceed 50% of income, immediate action required"
        elif dti_ratio > 0.4:
            capacity_status = "Severe"
            capacity_description = "Debt payments between 40-50% of income, serious intervention needed"
        elif dti_ratio > 0.3:
            capacity_status = "Constrained"
            capacity_description = "Debt payments between 30-40% of income, significant adjustments needed"
        elif dti_ratio > 0.2:
            capacity_status = "Challenged"
            capacity_description = "Debt payments between 20-30% of income, careful management required"
        else:
            capacity_status = "Manageable"
            capacity_description = "Debt payments below 20% of income, generally sustainable"
        
        # Calculate sustainable monthly allocation
        # Use 80% of disposable income as sustainable allocation
        sustainable_allocation = disposable_income * 0.8
        
        # Calculate minimum required allocation
        minimum_required = total_minimum_payment
        
        # Check if sustainable allocation meets minimum payments
        allocation_sufficiency = "Sufficient" if sustainable_allocation >= minimum_required else "Insufficient"
        
        # Calculate repayment timeline with sustainable allocation (simplified)
        # Assume average interest rate of 15%
        avg_interest_rate = 0.15
        if sustainable_allocation > 0 and sustainable_allocation > total_minimum_payment:
            # Simplified calculation - in reality would need detailed amortization
            excess_payment = sustainable_allocation - total_minimum_payment
            # Approximate months to repay using a simple formula
            # This is a rough estimate
            estimated_months = total_debt / excess_payment * (1 + avg_interest_rate/2)
            estimated_years = estimated_months / 12
        else:
            estimated_years = float('inf')  # Cannot repay with current allocation
        
        # Generate recommendations
        recommendations = []
        if allocation_sufficiency == "Insufficient":
            shortfall = minimum_required - sustainable_allocation
            recommendations.append(f"Increase monthly allocation by at least ₹{round(shortfall)} to meet minimum payments")
            recommendations.append("Consider debt restructuring or consolidation to reduce minimum payment requirements")
            recommendations.append("Explore emergency hardship programs offered by creditors")
        
        if capacity_status in ["Critical", "Severe"]:
            recommendations.append("Seek professional debt counseling immediately")
            recommendations.append("Consider debt settlement or restructuring for most pressing debts")
            recommendations.append("Look into income augmentation possibilities")
            
        if debt_to_annual_income > 1.0:
            recommendations.append("Develop a multi-year strategic debt reduction plan")
            recommendations.append("Consider liquidating non-essential assets to reduce debt burden")
        
        return {
            'debt_details': {
                'total_debt': round(total_debt),
                'total_minimum_monthly_payment': round(total_minimum_payment),
                'debt_to_income_ratio': round(dti_ratio * 100, 1),
                'debt_to_annual_income_ratio': round(debt_to_annual_income, 2)
            },
            'income_details': {
                'monthly_income': round(monthly_income),
                'monthly_expenses': round(monthly_expenses),
                'disposable_income': round(disposable_income)
            },
            'repayment_capacity': {
                'capacity_status': capacity_status,
                'capacity_description': capacity_description,
                'sustainable_monthly_allocation': round(sustainable_allocation),
                'minimum_required_allocation': round(minimum_required),
                'allocation_sufficiency': allocation_sufficiency,
                'estimated_years_to_debt_freedom': round(estimated_years, 1) if estimated_years != float('inf') else "Indefinite at current allocation"
            },
            'recommendations': recommendations
        }
    
    def _calculate_emi(self, principal, annual_interest_rate, years):
        """
        Calculate the equated monthly installment (EMI) for a loan.
        
        Args:
            principal: The loan principal amount
            annual_interest_rate: Annual interest rate (as a decimal, e.g., 0.09 for 9%)
            years: Loan tenure in years
            
        Returns:
            The monthly EMI amount
        """
        # Handle edge cases
        if principal <= 0 or years <= 0:
            return 0
            
        # Convert annual rate to monthly rate
        monthly_rate = annual_interest_rate / 12
        
        # Convert years to months
        months = years * 12
        
        # Handle edge case of zero interest rate
        if annual_interest_rate == 0:
            return principal / months
            
        # Calculate EMI using formula: P * r * (1+r)^n / ((1+r)^n - 1)
        # Where P = principal, r = monthly rate, n = number of months
        emi = principal * monthly_rate * math.pow(1 + monthly_rate, months) / (math.pow(1 + monthly_rate, months) - 1)
        
        return emi
    
    def _estimate_total_interest(self, debts, monthly_allocation, method="avalanche"):
        """
        Estimate the total interest paid over the repayment period
        for different repayment strategies.
        
        Args:
            debts: List of debt dictionaries with details
            monthly_allocation: Monthly amount allocated for debt repayment
            method: Repayment strategy method (avalanche, snowball, or hybrid)
            
        Returns:
            Total interest paid over the repayment period
        """
        # Create a copy of debts to avoid modifying the original
        if not debts or monthly_allocation <= 0:
            return 0
            
        working_debts = [debt.copy() for debt in debts]
        
        # Sort debts based on selected method
        if method.lower() == "avalanche":
            # Sort by interest rate (highest first)
            sorted_debts = sorted(working_debts, key=lambda x: x.get('interest_rate', 0), reverse=True)
        elif method.lower() == "snowball":
            # Sort by balance (lowest first)
            sorted_debts = sorted(working_debts, key=lambda x: x.get('balance', 0))
        else:  # hybrid
            # Create a score based on both interest rate and balance
            for debt in working_debts:
                # Normalize interest rate (0-1 scale where 1 is highest)
                max_interest = max(d.get('interest_rate', 0) for d in working_debts)
                min_interest = min(d.get('interest_rate', 0) for d in working_debts)
                interest_range = max_interest - min_interest
                
                if interest_range > 0:
                    interest_score = (debt.get('interest_rate', 0) - min_interest) / interest_range
                else:
                    interest_score = 0.5  # All same interest rate
                    
                # Normalize balance inversely (0-1 scale where 1 is lowest)
                max_balance = max(d.get('balance', 0) for d in working_debts)
                min_balance = min(d.get('balance', 0) for d in working_debts)
                balance_range = max_balance - min_balance
                
                if balance_range > 0:
                    balance_score = 1 - ((debt.get('balance', 0) - min_balance) / balance_range)
                else:
                    balance_score = 0.5  # All same balance
                    
                # Calculate hybrid score (60% weight to interest, 40% to balance)
                debt['hybrid_score'] = (interest_score * 0.6) + (balance_score * 0.4)
                
            # Sort by hybrid score (highest first)
            sorted_debts = sorted(working_debts, key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        # Calculate total minimum payment
        total_minimum_payment = 0
        for debt in sorted_debts:
            # Use provided minimum payment or estimate it
            if 'minimum_payment' in debt and debt['minimum_payment'] > 0:
                total_minimum_payment += debt['minimum_payment']
            else:
                # Estimate minimum payment
                debt_type = debt.get('type', 'other').lower()
                balance = debt.get('balance', 0)
                min_payment_rate = self.debt_params['debt_types'].get(debt_type, {}).get('minimum_payment', 0.02)
                min_payment = balance * min_payment_rate
                debt['minimum_payment'] = min_payment
                total_minimum_payment += min_payment
        
        # Calculate extra payment amount
        extra_payment = max(0, monthly_allocation - total_minimum_payment)
        
        # Initialize counters
        total_interest_paid = 0
        months = 0
        max_months = 360  # Cap at 30 years
        
        # Continue until all debts are paid off or max months reached
        while sorted_debts and months < max_months:
            months += 1
            month_allocation = monthly_allocation
            
            # Make minimum payments on all debts
            for debt in sorted_debts:
                # Calculate interest for this month
                monthly_interest = debt['balance'] * (debt['interest_rate'] / 12)
                total_interest_paid += monthly_interest
                
                # Apply minimum payment or full balance if smaller
                payment = min(debt['minimum_payment'], debt['balance'] + monthly_interest)
                
                # Adjust balances
                principal_payment = payment - monthly_interest
                debt['balance'] -= principal_payment
                
                # Update allocation remaining
                month_allocation -= payment
            
            # Apply any extra payment to highest priority debt (first in list)
            if sorted_debts and month_allocation > 0:
                highest_debt = sorted_debts[0]
                
                # Apply remaining allocation to principal
                principal_payment = min(month_allocation, highest_debt['balance'])
                highest_debt['balance'] -= principal_payment
            
            # Remove any fully paid debts
            sorted_debts = [debt for debt in sorted_debts if debt['balance'] > 1]  # Allow for tiny rounding errors
        
        return total_interest_paid
    
    def _estimate_first_payoff_time(self, debts, monthly_allocation, method="avalanche"):
        """
        Estimate the time (in months) until the first debt is paid off
        for different repayment strategies.
        
        Args:
            debts: List of debt dictionaries with details
            monthly_allocation: Monthly amount allocated for debt repayment
            method: Repayment strategy method (avalanche, snowball, or hybrid)
            
        Returns:
            Number of months until first debt payoff
        """
        # Create a copy of debts to avoid modifying the original
        if not debts or monthly_allocation <= 0:
            return float('inf')
            
        working_debts = [debt.copy() for debt in debts]
        
        # Sort debts based on selected method
        if method.lower() == "avalanche":
            # Sort by interest rate (highest first)
            sorted_debts = sorted(working_debts, key=lambda x: x.get('interest_rate', 0), reverse=True)
        elif method.lower() == "snowball":
            # Sort by balance (lowest first)
            sorted_debts = sorted(working_debts, key=lambda x: x.get('balance', 0))
        else:  # hybrid
            # Create a score based on both interest rate and balance
            for debt in working_debts:
                # Normalize interest rate (0-1 scale where 1 is highest)
                max_interest = max(d.get('interest_rate', 0) for d in working_debts)
                min_interest = min(d.get('interest_rate', 0) for d in working_debts)
                interest_range = max_interest - min_interest
                
                if interest_range > 0:
                    interest_score = (debt.get('interest_rate', 0) - min_interest) / interest_range
                else:
                    interest_score = 0.5  # All same interest rate
                    
                # Normalize balance inversely (0-1 scale where 1 is lowest)
                max_balance = max(d.get('balance', 0) for d in working_debts)
                min_balance = min(d.get('balance', 0) for d in working_debts)
                balance_range = max_balance - min_balance
                
                if balance_range > 0:
                    balance_score = 1 - ((debt.get('balance', 0) - min_balance) / balance_range)
                else:
                    balance_score = 0.5  # All same balance
                    
                # Calculate hybrid score (60% weight to interest, 40% to balance)
                debt['hybrid_score'] = (interest_score * 0.6) + (balance_score * 0.4)
                
            # Sort by hybrid score (highest first)
            sorted_debts = sorted(working_debts, key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        # Calculate total minimum payment
        total_minimum_payment = 0
        for debt in sorted_debts:
            # Use provided minimum payment or estimate it
            if 'minimum_payment' in debt and debt['minimum_payment'] > 0:
                total_minimum_payment += debt['minimum_payment']
            else:
                # Estimate minimum payment
                debt_type = debt.get('type', 'other').lower()
                balance = debt.get('balance', 0)
                min_payment_rate = self.debt_params['debt_types'].get(debt_type, {}).get('minimum_payment', 0.02)
                min_payment = balance * min_payment_rate
                debt['minimum_payment'] = min_payment
                total_minimum_payment += min_payment
        
        # Check if allocation is sufficient
        if monthly_allocation < total_minimum_payment:
            return float('inf')  # Cannot pay off any debt with insufficient allocation
        
        # Calculate extra payment amount
        extra_payment = max(0, monthly_allocation - total_minimum_payment)
        
        # Initialize counters
        months = 0
        max_months = 360  # Cap at 30 years
        initial_debt_count = len(sorted_debts)
        
        # Continue until a debt is paid off or max months reached
        while len(sorted_debts) == initial_debt_count and months < max_months:
            months += 1
            month_allocation = monthly_allocation
            
            # Make minimum payments on all debts
            for debt in sorted_debts:
                # Calculate interest for this month
                monthly_interest = debt['balance'] * (debt['interest_rate'] / 12)
                
                # Apply minimum payment or full balance if smaller
                payment = min(debt['minimum_payment'], debt['balance'] + monthly_interest)
                
                # Adjust balances
                principal_payment = payment - monthly_interest
                debt['balance'] -= principal_payment
                
                # Update allocation remaining
                month_allocation -= payment
            
            # Apply any extra payment to highest priority debt (first in list)
            if sorted_debts and month_allocation > 0:
                highest_debt = sorted_debts[0]
                
                # Apply remaining allocation to principal
                principal_payment = min(month_allocation, highest_debt['balance'])
                highest_debt['balance'] -= principal_payment
            
            # Remove any fully paid debts
            sorted_debts = [debt for debt in sorted_debts if debt['balance'] > 1]  # Allow for tiny rounding errors
        
        return months

    def validate_repayment_strategy_fit(self, goal_data):
        """
        Validate if the selected repayment strategy fits the user's financial
        situation and psychological profile.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with repayment strategy fit assessment
        """
        # Extract necessary information
        debts = goal_data.get('debts', [])
        preferred_method = goal_data.get('preferred_method', 'hybrid')
        psychological_profile = goal_data.get('psychological_profile', 'balanced')
        monthly_allocation = goal_data.get('monthly_allocation', 0)
        
        # If no debts provided, return generic assessment
        if not debts:
            return {
                'message': "Cannot validate strategy fit without debt details",
                'recommended_method': 'hybrid',
                'rationale': "Default recommendation without debt information"
            }
        
        # Analyze debt structure to determine mathematical optimal strategy
        # Calculate interest weighted by balance
        total_debt = sum(debt.get('balance', 0) for debt in debts)
        weighted_interest = sum(debt.get('balance', 0) * debt.get('interest_rate', 0) for debt in debts)
        avg_interest_rate = weighted_interest / total_debt if total_debt > 0 else 0
        
        # Calculate interest rate dispersion (max - min)
        interest_rates = [debt.get('interest_rate', 0) for debt in debts]
        interest_dispersion = max(interest_rates) - min(interest_rates) if interest_rates else 0
        
        # Calculate balance dispersion (max/min ratio)
        balances = [debt.get('balance', 0) for debt in debts if debt.get('balance', 0) > 0]
        balance_dispersion = max(balances) / min(balances) if balances and min(balances) > 0 else 1
        
        # Determine mathematically optimal method based on debt structure
        if interest_dispersion > 0.1:  # Significant interest rate difference
            mathematical_optimal = "avalanche"
            math_rationale = "Significant interest rate differences make avalanche method more efficient"
        elif balance_dispersion > 5:  # Significant balance differences
            mathematical_optimal = "snowball"
            math_rationale = "Wide balance dispersion makes snowball method provide quick wins"
        else:
            mathematical_optimal = "hybrid"
            math_rationale = "Similar interest rates and balances make hybrid approach appropriate"
        
        # Determine psychologically optimal method based on profile
        if psychological_profile == 'analytical':
            psychological_optimal = "avalanche"
            psych_rationale = "Analytical profile values mathematical optimization over quick wins"
        elif psychological_profile == 'motivational':
            psychological_optimal = "snowball"
            psych_rationale = "Motivational profile benefits from quick wins and momentum building"
        else:  # balanced or undefined
            psychological_optimal = "hybrid"
            psych_rationale = "Balanced profile benefits from both mathematical efficiency and psychological rewards"
        
        # Calculate expected outcomes for each method
        # This is a simplified calculation - real implementation would use more detailed amortization
        
        # Estimate avalanche method outcomes
        avalanche_interest = self._estimate_total_interest(debts, monthly_allocation, "avalanche")
        
        # Estimate snowball method outcomes
        snowball_interest = self._estimate_total_interest(debts, monthly_allocation, "snowball")
        
        # Estimate hybrid method outcomes (average of the two)
        hybrid_interest = (avalanche_interest + snowball_interest) / 2
        
        # Calculate time to first debt payoff for each method
        avalanche_first_payoff = self._estimate_first_payoff_time(debts, monthly_allocation, "avalanche")
        snowball_first_payoff = self._estimate_first_payoff_time(debts, monthly_allocation, "snowball")
        hybrid_first_payoff = self._estimate_first_payoff_time(debts, monthly_allocation, "hybrid")
        
        # Compare preferred method to optimal methods
        strategy_alignment = {
            'mathematical_optimal': mathematical_optimal,
            'mathematical_rationale': math_rationale,
            'psychological_optimal': psychological_optimal,
            'psychological_rationale': psych_rationale
        }
        
        # Determine overall recommendation based on weights
        math_weight = 0.6  # 60% weight to mathematical optimization
        psych_weight = 0.4  # 40% weight to psychological optimization
        
        method_scores = {
            'avalanche': (1.0 if mathematical_optimal == 'avalanche' else 0.0) * math_weight +
                         (1.0 if psychological_optimal == 'avalanche' else 0.0) * psych_weight,
            'snowball': (1.0 if mathematical_optimal == 'snowball' else 0.0) * math_weight +
                        (1.0 if psychological_optimal == 'snowball' else 0.0) * psych_weight,
            'hybrid': (1.0 if mathematical_optimal == 'hybrid' else 0.0) * math_weight +
                     (1.0 if psychological_optimal == 'hybrid' else 0.0) * psych_weight
        }
        
        # Add bonus to hybrid for being versatile
        method_scores['hybrid'] += 0.1
        
        # Determine recommended method
        recommended_method = max(method_scores, key=method_scores.get)
        
        # Determine alignment of preferred with recommended
        if preferred_method == recommended_method:
            alignment = "Optimal"
            alignment_message = f"Your preferred {preferred_method} method aligns well with your debt profile and psychological factors"
        else:
            alignment = "Suboptimal"
            alignment_message = f"Your preferred {preferred_method} method may not be optimal based on your debt profile and psychological factors"
        
        # Create method comparison
        method_comparison = {
            'avalanche': {
                'interest_savings': "Highest",
                'psychological_benefits': "Lowest",
                'time_to_debt_freedom': "Shortest",
                'time_to_first_payoff': f"{avalanche_first_payoff:.1f} months",
                'total_interest': round(avalanche_interest)
            },
            'snowball': {
                'interest_savings': "Lowest",
                'psychological_benefits': "Highest",
                'time_to_debt_freedom': "Longest",
                'time_to_first_payoff': f"{snowball_first_payoff:.1f} months",
                'total_interest': round(snowball_interest)
            },
            'hybrid': {
                'interest_savings': "Moderate",
                'psychological_benefits': "Moderate",
                'time_to_debt_freedom': "Moderate",
                'time_to_first_payoff': f"{hybrid_first_payoff:.1f} months",
                'total_interest': round(hybrid_interest)
            }
        }
        
        # Additional behavioral insights
        behavioral_insights = {
            'avalanche': [
                "Best for disciplined individuals who are motivated by efficiency",
                "Requires patience as early victories may take longer",
                "Most effective when interest rate differences are significant",
                "Minimizes interest costs over the repayment period"
            ],
            'snowball': [
                "Best for those who need psychological wins to stay motivated",
                "Provides quick victories by eliminating small debts first",
                "Creates momentum and simplifies finances faster",
                "May cost more in interest but increases likelihood of completion"
            ],
            'hybrid': [
                "Balances mathematical optimization with psychological factors",
                "Good for most people with mixed debt portfolios",
                "Adaptable to changing circumstances",
                "Provides some early wins while maintaining reasonable efficiency"
            ]
        }
        
        return {
            'preferred_method': preferred_method,
            'recommended_method': recommended_method,
            'strategy_alignment': alignment,
            'alignment_message': alignment_message,
            'strategy_fit_analysis': strategy_alignment,
            'method_comparison': method_comparison,
            'behavioral_insights': behavioral_insights[recommended_method],
            'potential_interest_difference': round(snowball_interest - avalanche_interest),
            'recommendation_rationale': f"Based on {math_weight*100}% weight to mathematical factors and {psych_weight*100}% to psychological factors"
        }
    
    def assess_debt_consolidation_feasibility(self, goal_data):
        """
        Assess the feasibility and benefits of debt consolidation
        for the given debt portfolio.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with debt consolidation feasibility assessment
        """
        # Extract necessary information
        debts = goal_data.get('debts', [])
        credit_score = goal_data.get('credit_score', 700)  # Default to average score
        monthly_income = goal_data.get('monthly_income', 0)
        monthly_expenses = goal_data.get('monthly_expenses', 0)
        
        # If no debts provided, return generic assessment
        if not debts:
            return {
                'message': "Cannot assess consolidation feasibility without debt details",
                'recommendation': "Provide detailed debt information for consolidation analysis"
            }
        
        # Filter for high-interest debts that make sense to consolidate
        # Use parameter for threshold or default to 12%
        consolidation_threshold = self.debt_optimization_params.get('consolidation_threshold', 0.12)
        high_interest_debts = [debt for debt in debts if debt.get('interest_rate', 0) > consolidation_threshold]
        
        # Skip detailed analysis if no high-interest debts
        if not high_interest_debts:
            return {
                'consolidation_feasibility': "Not Recommended",
                'rationale': f"No debts with interest rates above {consolidation_threshold*100}% threshold",
                'high_interest_debt_total': 0,
                'recommendation': "Continue with current repayment strategy"
            }
        
        # Calculate total high-interest debt
        high_interest_total = sum(debt.get('balance', 0) for debt in high_interest_debts)
        weighted_interest = sum(debt.get('balance', 0) * debt.get('interest_rate', 0) for debt in high_interest_debts)
        avg_high_interest = weighted_interest / high_interest_total if high_interest_total > 0 else 0
        
        # Check eligibility for different consolidation options
        # Personal loan eligibility
        personal_loan_eligible = credit_score >= 700
        personal_loan_rate = self.debt_params['debt_consolidation']['personal_loan']['typical_interest']
        personal_loan_rate_adjusted = personal_loan_rate
        
        # Adjust rate based on credit score
        if credit_score < 650:
            personal_loan_rate_adjusted += 0.03  # Add 3% for poor credit
        elif credit_score < 700:
            personal_loan_rate_adjusted += 0.015  # Add 1.5% for fair credit
        elif credit_score > 750:
            personal_loan_rate_adjusted -= 0.01  # Subtract 1% for excellent credit
        
        # Calculate personal loan savings
        personal_loan_savings = high_interest_total * (avg_high_interest - personal_loan_rate_adjusted)
        personal_loan_monthly = self._calculate_emi(high_interest_total, personal_loan_rate_adjusted, 3)  # 3 year term
        
        # Balance transfer eligibility
        balance_transfer_eligible = credit_score >= 720 and high_interest_total <= 500000
        balance_transfer_fee = self.debt_params['debt_consolidation']['balance_transfer']['typical_fee']
        balance_transfer_period = self.debt_params['debt_consolidation']['balance_transfer']['typical_duration']
        
        # Calculate balance transfer savings
        interest_saved_during_intro = high_interest_total * avg_high_interest * (balance_transfer_period / 12)
        balance_transfer_fee_amount = high_interest_total * balance_transfer_fee
        balance_transfer_savings = interest_saved_during_intro - balance_transfer_fee_amount
        
        # Loan against property eligibility
        property_value = goal_data.get('property_value', 0)
        existing_home_loan = sum(debt.get('balance', 0) for debt in debts if debt.get('type', '').lower() == 'home_loan')
        available_lap = max(0, property_value * 0.7 - existing_home_loan) if property_value > 0 else 0
        lap_eligible = available_lap >= high_interest_total and property_value > 0
        
        # Calculate LAP savings if eligible
        lap_rate = self.debt_params['debt_consolidation']['loan_against_property']['typical_interest']
        lap_savings = high_interest_total * (avg_high_interest - lap_rate) if lap_eligible else 0
        lap_monthly = self._calculate_emi(high_interest_total, lap_rate, 10) if lap_eligible else 0  # 10 year term
        
        # Calculate total current monthly payment for high-interest debts
        current_monthly_payment = 0
        for debt in high_interest_debts:
            if 'monthly_payment' in debt:
                current_monthly_payment += debt['monthly_payment']
            else:
                # Estimate monthly payment
                debt_type = debt.get('type', 'other').lower()
                balance = debt.get('balance', 0)
                rate = debt.get('interest_rate', 0)
                term = debt.get('remaining_term', 3) * 12  # Default to 3 years if not specified
                
                current_monthly_payment += self._calculate_emi(balance, rate, term/12)
        
        # Calculate disposable income
        disposable_income = monthly_income - monthly_expenses if monthly_income > 0 else 0
        
        # Determine best consolidation option
        consolidation_options = []
        
        if personal_loan_eligible:
            consolidation_options.append({
                'option': 'Personal Loan',
                'eligible': "Yes",
                'total_savings': round(personal_loan_savings),
                'monthly_payment': round(personal_loan_monthly),
                'monthly_savings': round(current_monthly_payment - personal_loan_monthly),
                'interest_rate': f"{personal_loan_rate_adjusted*100:.2f}%",
                'typical_term': "3-5 years",
                'pros': self.debt_params['debt_consolidation']['personal_loan']['pros'],
                'cons': self.debt_params['debt_consolidation']['personal_loan']['cons']
            })
        else:
            consolidation_options.append({
                'option': 'Personal Loan',
                'eligible': "No",
                'reason': "Credit score below 700 or insufficient income"
            })
            
        if balance_transfer_eligible:
            consolidation_options.append({
                'option': 'Balance Transfer',
                'eligible': "Yes",
                'total_savings': round(balance_transfer_savings),
                'upfront_fee': round(balance_transfer_fee_amount),
                'introductory_rate': "0%",
                'introductory_period': f"{balance_transfer_period} months",
                'note': "Requires excellent credit and usually applicable to credit card debt",
                'pros': self.debt_params['debt_consolidation']['balance_transfer']['pros'],
                'cons': self.debt_params['debt_consolidation']['balance_transfer']['cons']
            })
        else:
            consolidation_options.append({
                'option': 'Balance Transfer',
                'eligible': "No",
                'reason': "Credit score below 720 or debt amount too high"
            })
            
        if lap_eligible:
            consolidation_options.append({
                'option': 'Loan Against Property',
                'eligible': "Yes",
                'total_savings': round(lap_savings),
                'monthly_payment': round(lap_monthly),
                'monthly_savings': round(current_monthly_payment - lap_monthly),
                'interest_rate': f"{lap_rate*100:.2f}%",
                'typical_term': "10-15 years",
                'available_equity': round(available_lap),
                'pros': self.debt_params['debt_consolidation']['loan_against_property']['pros'],
                'cons': self.debt_params['debt_consolidation']['loan_against_property']['cons']
            })
        else:
            consolidation_options.append({
                'option': 'Loan Against Property',
                'eligible': "No",
                'reason': "Insufficient property equity or no property owned"
            })
        
        # Determine overall consolidation feasibility
        eligible_options = [opt for opt in consolidation_options if opt.get('eligible') == "Yes"]
        
        if not eligible_options:
            feasibility = "Not Feasible"
            rationale = "No eligible consolidation options based on credit profile and assets"
            recommendation = "Focus on improving credit score and traditional debt repayment methods"
        else:
            # Find best option based on total savings
            best_option = max(eligible_options, key=lambda x: x.get('total_savings', 0))
            
            # Check if savings are significant
            if best_option.get('total_savings', 0) < high_interest_total * 0.05:  # Less than 5% savings
                feasibility = "Marginally Beneficial"
                rationale = f"Savings from consolidation are minimal relative to debt amount ({round(best_option.get('total_savings', 0)/high_interest_total*100,1)}%)"
                recommendation = "Consolidation possible but benefits are limited, consider traditional repayment strategies"
            else:
                feasibility = "Beneficial"
                rationale = f"Consolidation can save ₹{round(best_option.get('total_savings', 0))} over the repayment period"
                
                if 'monthly_savings' in best_option and best_option['monthly_savings'] > 0:
                    recommendation = f"Consider {best_option['option']} consolidation to save ₹{round(best_option['monthly_savings'])} monthly and ₹{round(best_option['total_savings'])} overall"
                else:
                    recommendation = f"Consider {best_option['option']} consolidation to save ₹{round(best_option['total_savings'])} over the repayment period"
        
        # Check if monthly payment for best option is affordable
        if eligible_options and 'monthly_payment' in eligible_options[0]:
            best_monthly = eligible_options[0]['monthly_payment']
            if best_monthly > disposable_income * 0.8:
                affordability = "Not Affordable"
                affordability_note = f"Consolidation payment (₹{round(best_monthly)}) exceeds 80% of disposable income (₹{round(disposable_income)})"
            else:
                affordability = "Affordable"
                affordability_note = f"Consolidation payment (₹{round(best_monthly)}) is {round(best_monthly/disposable_income*100,1)}% of disposable income"
        else:
            affordability = "Unknown"
            affordability_note = "Cannot determine affordability without income details or eligible options"
        
        return {
            'consolidation_feasibility': feasibility,
            'rationale': rationale,
            'recommendation': recommendation,
            'affordability': {
                'status': affordability,
                'note': affordability_note,
                'disposable_income': round(disposable_income)
            },
            'high_interest_debt': {
                'total': round(high_interest_total),
                'average_interest_rate': f"{avg_high_interest*100:.2f}%",
                'current_monthly_payment': round(current_monthly_payment)
            },
            'consolidation_options': consolidation_options,
            'implementation_steps': [
                "Verify actual interest rates available to you with multiple lenders",
                "Read all terms and conditions carefully, paying attention to fees and penalties",
                "Create a repayment plan before consolidating to avoid re-accumulating debt",
                "Continue making payments on existing debts until consolidation is complete",
                "Consider partial consolidation of only the highest-interest debts if full consolidation isn't feasible"
            ]
        }
    
    def evaluate_debt_repayment_impact(self, goal_data):
        """
        Evaluate the impact of debt repayment on overall financial health
        and progress towards other financial goals.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with impact assessment
        """
        # Extract necessary information
        debts = goal_data.get('debts', [])
        monthly_allocation = goal_data.get('monthly_allocation', 0)
        monthly_income = goal_data.get('monthly_income', 0)
        other_goals = goal_data.get('other_goals', [])
        
        # Calculate key metrics
        total_debt = sum(debt.get('balance', 0) for debt in debts) if debts else goal_data.get('target_amount', 0)
        
        # Calculate total minimum payments
        total_minimum_payment = 0
        for debt in debts:
            if 'minimum_payment' in debt:
                total_minimum_payment += debt['minimum_payment']
            else:
                # Estimate minimum payment
                debt_type = debt.get('type', 'other').lower()
                balance = debt.get('balance', 0)
                min_payment_rate = self.debt_params['debt_types'].get(debt_type, {}).get('minimum_payment', 0.02)
                total_minimum_payment += balance * min_payment_rate
        
        # Calculate debt-to-income ratio
        dti_ratio = total_minimum_payment / monthly_income if monthly_income > 0 else float('inf')
        
        # Calculate allocation to minimum payment ratio
        payment_coverage_ratio = monthly_allocation / total_minimum_payment if total_minimum_payment > 0 else float('inf')
        
        # Calculate time to debt freedom (simplified)
        # This is a very simplified calculation - in reality would use debt-by-debt amortization
        avg_interest_rate = 0.15  # Assume 15% average interest
        if payment_coverage_ratio > 1 and monthly_allocation > 0:
            # Calculate excess payment
            excess_payment = monthly_allocation - total_minimum_payment
            # Approximate months to repay using a simple formula
            estimated_months = total_debt / excess_payment * (1 + avg_interest_rate/2)
            time_to_freedom = estimated_months / 12
        else:
            time_to_freedom = float('inf')  # Cannot repay with current allocation
        
        # Calculate opportunity cost of debt allocation
        # Assuming 8% potential investment return
        investment_return_rate = 0.08
        opportunity_cost = monthly_allocation * 12 * time_to_freedom * investment_return_rate / 2
        
        # Evaluate impact on other financial goals
        goal_impacts = []
        remaining_allocation = monthly_income - monthly_allocation if monthly_income > 0 else 0
        
        for goal in other_goals:
            goal_type = goal.get('type', 'other')
            goal_amount = goal.get('target_amount', 0)
            goal_timeline = goal.get('timeline', 5)  # Years
            goal_priority = goal.get('priority', 'medium')
            goal_allocation = goal.get('monthly_allocation', 0)
            
            # Calculate if goal allocation is still feasible
            if remaining_allocation < goal_allocation:
                impact_status = "Severe"
                impact_description = "Debt repayment significantly reduces funds available for this goal"
                delay_years = 2  # Significant delay
            elif remaining_allocation < goal_allocation * 1.2:
                impact_status = "Moderate"
                impact_description = "Debt repayment somewhat constrains funds available for this goal"
                delay_years = 1  # Moderate delay
            else:
                impact_status = "Minimal"
                impact_description = "Sufficient funds remain available for this goal"
                delay_years = 0  # No delay
            
            # Calculate adjusted timeline
            adjusted_timeline = goal_timeline + delay_years
            
            goal_impacts.append({
                'goal_type': goal_type,
                'original_timeline': goal_timeline,
                'adjusted_timeline': adjusted_timeline,
                'impact_status': impact_status,
                'impact_description': impact_description
            })
        
        # Evaluate positive impacts of becoming debt-free
        positive_impacts = [
            {
                'aspect': "Monthly Cash Flow",
                'impact': f"₹{round(monthly_allocation)} freed up monthly after debt repayment",
                'timeline': f"In approximately {round(time_to_freedom, 1)} years"
            },
            {
                'aspect': "Financial Flexibility",
                'impact': "Increased ability to respond to opportunities and emergencies",
                'timeline': "Gradually increasing as debts are eliminated"
            },
            {
                'aspect': "Investment Capacity",
                'impact': f"Ability to redirect ₹{round(monthly_allocation)} monthly to investments",
                'timeline': f"After debt freedom in {round(time_to_freedom, 1)} years"
            },
            {
                'aspect': "Credit Score",
                'impact': "Potential improvement from reducing credit utilization and building payment history",
                'timeline': "Progressive improvement over the repayment period"
            },
            {
                'aspect': "Financial Stress",
                'impact': "Reduced anxiety and improved financial wellbeing",
                'timeline': "Immediate improvement as repayment plan is implemented"
            }
        ]
        
        # Determine suggested allocation adjustments
        suggested_adjustments = []
        
        if payment_coverage_ratio < 1.2:
            suggested_adjustments.append({
                'adjustment': "Increase debt allocation",
                'amount': round(total_minimum_payment * 0.2),  # 20% above minimum
                'rationale': "Current allocation barely covers minimum payments, offering minimal progress"
            })
        
        if dti_ratio > 0.4 and other_goals:
            suggested_adjustments.append({
                'adjustment': "Temporarily reduce other goal allocations",
                'amount': round(monthly_allocation * 0.2),  # 20% of current allocation
                'rationale': "High debt burden requires prioritizing debt reduction before other goals"
            })
        
        if time_to_freedom > 5 and payment_coverage_ratio < 2:
            suggested_adjustments.append({
                'adjustment': "Consider debt consolidation or restructuring",
                'impact': "Could reduce total interest and accelerate payoff timeline",
                'rationale': "Long repayment timeline indicates need for strategy adjustment"
            })
        
        return {
            'debt_metrics': {
                'total_debt': round(total_debt),
                'monthly_minimum_payment': round(total_minimum_payment),
                'debt_to_income_ratio': round(dti_ratio * 100, 1),
                'payment_coverage_ratio': round(payment_coverage_ratio, 2),
                'estimated_years_to_debt_freedom': round(time_to_freedom, 1) if time_to_freedom != float('inf') else "Indefinite at current allocation"
            },
            'financial_impact': {
                'monthly_debt_allocation': round(monthly_allocation),
                'remaining_monthly_allocation': round(remaining_allocation),
                'opportunity_cost': round(opportunity_cost),
                'opportunity_cost_note': f"Potential investment growth foregone over {round(time_to_freedom, 1)} years of debt repayment"
            },
            'other_goal_impacts': goal_impacts,
            'positive_impacts_of_debt_freedom': positive_impacts,
            'suggested_allocation_adjustments': suggested_adjustments,
            'balance_recommendation': f"{'Prioritize debt repayment over other goals' if dti_ratio > 0.3 else 'Balance debt repayment with other important financial goals'}"
        }
        
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy for debt repayment goals with focus on
        maintaining liquidity for debt payments while optimizing any invested assets.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            profile_data: Optional dictionary with profile details
            
        Returns:
            Dictionary with rebalancing strategy tailored for debt repayment
        """
        # Create rebalancing strategy instance
        rebalancing = RebalancingStrategy()
        
        # Extract debt repayment specific information
        debts = goal_data.get('debts', [])
        monthly_allocation = goal_data.get('monthly_allocation')
        time_horizon = goal_data.get('time_horizon', 3)  # Default 3 years if not specified
        target_amount = goal_data.get('target_amount')
        
        # Calculate total debt if target amount not provided
        if not target_amount and debts:
            target_amount = sum(debt.get('balance', 0) for debt in debts)
        
        # Create minimal profile if not provided
        if not profile_data:
            profile_data = {
                'risk_profile': 'conservative',  # Debt repayment is inherently conservative
                'portfolio_value': target_amount * 0.1,  # Assumption: small portfolio while repaying debt
                'liquidity_needs': {
                    'near_term': monthly_allocation * 6 if monthly_allocation else target_amount * 0.1,
                    'timeline_months': 6
                }
            }
        
        # Get default allocation for debt repayment
        # For debt repayment, focus on liquid assets and very conservative allocation
        # Only for any invested assets not directly allocated for immediate debt payments
        default_allocation = {
            'cash': 0.60,      # 60% cash for liquidity to make debt payments
            'debt': 0.35,      # 35% short-term debt instruments
            'equity': 0.05     # Minimal equity exposure
        }
        
        # Extract any existing allocation from goal data
        allocation = goal_data.get('investment_allocation', default_allocation)
        
        # Create rebalancing goal with debt repayment focus
        rebalancing_goal = {
            'goal_type': 'debt_repayment',
            'time_horizon': time_horizon,
            'target_allocation': allocation,
            'target_amount': target_amount,
            'profile_data': profile_data
        }
        
        # Design rebalancing schedule specific to debt repayment
        # For debt repayment, we prioritize liquidity and payment schedules
        debt_schedule = self.analyze_debt_portfolio(debts) if debts else None
        
        # Calculate threshold factors based on debt type and payment schedule
        threshold_factors = {}
        
        if debts:
            # Sort debts by priority for threshold calculations
            high_priority_debt = 0
            for debt in debts:
                debt_type = debt.get('type', 'other').lower()
                balance = debt.get('balance', 0)
                priority = self.debt_params['debt_types'].get(debt_type, {}).get('priority_level', 'medium')
                if priority in ['very_high', 'high']:
                    high_priority_debt += balance
            
            # Calculate high priority debt percentage
            total_debt = sum(debt.get('balance', 0) for debt in debts)
            high_priority_percentage = high_priority_debt / total_debt if total_debt > 0 else 0
            
            # Tighter thresholds when high priority debt is significant
            if high_priority_percentage > 0.7:  # More than 70% high priority
                threshold_factors = {
                    'cash': 0.5,    # Very tight threshold for cash (0.5x standard)
                    'debt': 0.7,    # Tight threshold for debt instruments
                    'equity': 0.8   # Slightly looser for minimal equity
                }
            elif high_priority_percentage > 0.3:  # More than 30% high priority
                threshold_factors = {
                    'cash': 0.7,    # Tight threshold for cash
                    'debt': 0.8,    # Somewhat tight for debt
                    'equity': 0.9   # Near normal for minimal equity
                }
            else:  # Low priority debt dominates
                threshold_factors = {
                    'cash': 0.8,    # Somewhat tight for cash
                    'debt': 0.9,    # Near normal for debt
                    'equity': 1.0   # Normal for equity
                }
        else:
            # Default factors if no detailed debt information
            threshold_factors = {
                'cash': 0.7,    # Relatively tight for cash
                'debt': 0.8,    # Somewhat tight for debt
                'equity': 0.9   # Near normal for equity
            }
        
        # Design rebalancing schedule
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(rebalancing_goal, profile_data)
        
        # Adjust schedule based on debt repayment timeline
        # For debt repayment, align with payment schedules
        
        # Calculate base drift thresholds
        base_thresholds = rebalancing.calculate_drift_thresholds(allocation)
        
        # Apply custom threshold factors for debt repayment
        custom_thresholds = {
            'threshold_rationale': "Debt repayment-specific thresholds focused on payment liquidity",
            'asset_bands': {}
        }
        
        for asset, band in base_thresholds['asset_bands'].items():
            factor = threshold_factors.get(asset, 1.0)
            custom_thresholds['asset_bands'][asset] = {
                'target': band['target'],
                'threshold': band['threshold'] * factor,
                'upper_band': band['target'] + (band['threshold'] * factor),
                'lower_band': max(0, band['target'] - (band['threshold'] * factor)),
                'rebalance_when': f"< {max(0, band['target'] - (band['threshold'] * factor)):.2f} or > {band['target'] + (band['threshold'] * factor):.2f}"
            }
        
        # Create comprehensive debt repayment rebalancing strategy
        debt_rebalancing_strategy = {
            'goal_type': 'debt_repayment',
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': custom_thresholds,
            'debt_specific_considerations': {
                'payment_schedule_alignment': "Maintain higher cash allocation before major payment dates",
                'liquidity_management': "Ensure sufficient liquid assets to cover at least 3 months of debt payments",
                'reinvestment_strategy': "As debts are paid off, gradually shift freed-up cash to growth assets"
            },
            'implementation_priorities': [
                "Cash flow maintenance for debt payments is the highest priority",
                "Rebalance only after ensuring all scheduled debt payments are covered",
                "Invest any temporary cash surplus in short-term liquid instruments",
                "As high-interest debts are eliminated, gradually normalize allocation"
            ]
        }
        
        # Add debt-specific rebalancing advice
        debt_rebalancing_strategy['debt_rebalancing_advice'] = {
            'payment_milestone_approach': [
                "Rebalance after each significant debt is paid off",
                "Gradually reduce cash allocation as total debt decreases",
                "Increase growth assets as high-interest debts are eliminated"
            ],
            'interest_rate_considerations': [
                "Maintain higher cash allocation when interest rates are rising",
                "Consider prepaying variable-rate debt during rising rate environment",
                "During falling rates, lock in fixed-rate instruments for non-payment funds"
            ],
            'tax_efficient_debt_rebalancing': [
                "Time rebalancing to optimize tax benefits from home loan interest payments",
                "Coordinate education loan interest deductions with portfolio adjustments",
                "Consider fiscal year timing for tax-advantaged debt instruments"
            ]
        }
        
        return debt_rebalancing_strategy
    
    def optimize_debt_allocation(self, goal_data):
        """
        Optimize the allocation of funds across different debts based on various factors
        including interest rates, balances, and psychological factors.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with optimized debt allocation strategy
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        debts = goal_data.get('debts', [])
        monthly_allocation = goal_data.get('monthly_allocation', 0)
        preferred_method = goal_data.get('preferred_method', 'hybrid')
        psychological_profile = goal_data.get('psychological_profile', 'balanced')
        
        # If no debts provided, return generic optimization
        if not debts or monthly_allocation <= 0:
            return {
                'message': "Cannot optimize debt allocation without sufficient details",
                'recommendation': "Provide detailed debt information and monthly allocation"
            }
        
        # Calculate total minimum payment
        total_minimum_payment = 0
        for debt in debts:
            # Use provided minimum payment or estimate it
            if 'minimum_payment' in debt and debt['minimum_payment'] > 0:
                total_minimum_payment += debt['minimum_payment']
            else:
                # Estimate minimum payment
                debt_type = debt.get('type', 'other').lower()
                balance = debt.get('balance', 0)
                min_payment_rate = self.debt_params['debt_types'].get(debt_type, {}).get('minimum_payment', 0.02)
                min_payment = balance * min_payment_rate
                total_minimum_payment += min_payment
        
        # Check if allocation is sufficient
        if monthly_allocation < total_minimum_payment:
            return {
                'error': 'Insufficient allocation',
                'message': 'Monthly allocation is less than total minimum payments',
                'required_minimum': round(total_minimum_payment),
                'allocation': round(monthly_allocation),
                'shortfall': round(total_minimum_payment - monthly_allocation)
            }
        
        # Get the recommended repayment strategy based on debt profile and psychological factors
        strategy_fit = self.validate_repayment_strategy_fit(goal_data)
        recommended_method = strategy_fit['recommended_method']
        
        # Calculate weight balance between mathematical and psychological factors
        # Default weights from debt optimization parameters
        math_weight = self.debt_optimization_params.get('avalanche_weight', 0.6)
        psych_weight = self.debt_optimization_params.get('snowball_weight', 0.4)
        
        # Adjust weights based on psychological profile
        if psychological_profile == 'analytical':
            math_weight = 0.8
            psych_weight = 0.2
        elif psychological_profile == 'motivational':
            math_weight = 0.3
            psych_weight = 0.7
        
        # Create working copy of debts for optimization
        working_debts = [debt.copy() for debt in debts]
        
        # Calculate normalized scores for each debt (interest rate and balance)
        # Normalize interest rates (higher is better for targeting)
        interest_rates = [debt.get('interest_rate', 0) for debt in working_debts]
        max_interest = max(interest_rates) if interest_rates else 0
        min_interest = min(interest_rates) if interest_rates else 0
        interest_range = max_interest - min_interest
        
        # Normalize balances (lower is better for quick wins)
        balances = [debt.get('balance', 0) for debt in working_debts]
        max_balance = max(balances) if balances else 0
        min_balance = min(balances) if balances else 0
        balance_range = max_balance - min_balance
        
        # Calculate hybrid optimization score for each debt
        optimized_allocation = []
        for debt in working_debts:
            # Interest rate score (normalized)
            interest_score = 0.5  # Default if all same
            if interest_range > 0:
                interest_score = (debt.get('interest_rate', 0) - min_interest) / interest_range
            
            # Balance score (inverse normalized - lower balance gets higher score)
            balance_score = 0.5  # Default if all same
            if balance_range > 0:
                balance_score = 1 - ((debt.get('balance', 0) - min_balance) / balance_range)
            
            # Tax benefit score (1 for tax-advantaged debt, 0 for others)
            debt_type = debt.get('type', '').lower()
            tax_benefit = 1 if debt_type in ['home_loan', 'education_loan'] else 0
            
            # Consider prepayment penalties
            has_penalty = False
            if debt_type in self.debt_params['prepayment_penalties']:
                penalty_rate = self.debt_params['prepayment_penalties'][debt_type]
                if isinstance(penalty_rate, dict):  # For home loans with different fixed/floating rates
                    penalty_rate = penalty_rate.get('fixed_rate', 0)  # Default to fixed rate penalty
                has_penalty = penalty_rate > 0
            
            # Calculate composite score
            # Higher score = higher priority for extra payment allocation
            if recommended_method == 'avalanche':
                composite_score = (interest_score * 0.8) + (balance_score * 0.1) + (tax_benefit * 0.1)
                if has_penalty:
                    composite_score *= 0.9  # Reduce score if prepayment penalty exists
            elif recommended_method == 'snowball':
                composite_score = (balance_score * 0.8) + (interest_score * 0.1) + (tax_benefit * 0.1)
                if has_penalty:
                    composite_score *= 0.9  # Reduce score if prepayment penalty exists
            else:  # hybrid
                # Custom weighted formula for hybrid approach
                composite_score = (interest_score * math_weight) + (balance_score * psych_weight) + (tax_benefit * 0.1)
                if has_penalty:
                    composite_score *= 0.9  # Reduce score if prepayment penalty exists
            
            # Add to optimized allocation
            optimized_allocation.append({
                'name': debt.get('name', f"{debt.get('type', 'Debt')} {debt.get('id', '')}"),
                'type': debt.get('type', 'other'),
                'balance': round(debt.get('balance', 0)),
                'interest_rate': round(debt.get('interest_rate', 0) * 100, 2),
                'optimization_score': round(composite_score, 2),
                'allocation_priority': len(optimized_allocation) + 1,  # Will be updated after sort
                'minimum_payment': round(debt.get('minimum_payment', 0)) if 'minimum_payment' in debt else None
            })
        
        # Sort by optimization score (highest first)
        optimized_allocation.sort(key=lambda x: x['optimization_score'], reverse=True)
        
        # Update allocation priorities after sorting
        for i, allocation in enumerate(optimized_allocation):
            allocation['allocation_priority'] = i + 1
        
        # Calculate allocation distribution
        extra_payment = monthly_allocation - total_minimum_payment
        
        # Allocate extra payment to highest priority debt
        if optimized_allocation:
            optimized_allocation[0]['recommended_payment'] = round(optimized_allocation[0].get('minimum_payment', 0) + extra_payment)
            optimized_allocation[0]['extra_payment'] = round(extra_payment)
        
        return {
            'optimized_allocation': optimized_allocation,
            'optimization_method': recommended_method,
            'mathematical_weight': math_weight,
            'psychological_weight': psych_weight,
            'monthly_allocation': round(monthly_allocation),
            'minimum_payments_total': round(total_minimum_payment),
            'extra_payment_amount': round(extra_payment),
            'optimization_rationale': f"Balancing {math_weight*100}% mathematical efficiency with {psych_weight*100}% psychological factors"
        }
    
    def optimize_repayment_order(self, goal_data):
        """
        Optimize the order in which debts are paid off based on various factors
        like interest rates, balances, and debt types.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with optimized repayment order strategy
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        debts = goal_data.get('debts', [])
        monthly_allocation = goal_data.get('monthly_allocation', 0)
        preferred_method = goal_data.get('preferred_method', 'hybrid')
        
        # If no debts provided, return generic optimization
        if not debts or monthly_allocation <= 0:
            return {
                'message': "Cannot optimize repayment order without sufficient details",
                'recommendation': "Provide detailed debt information and monthly allocation"
            }
        
        # Get the recommended repayment strategy fit
        strategy_fit = self.validate_repayment_strategy_fit(goal_data)
        recommended_method = strategy_fit['recommended_method']
        
        # Create working copy of debts for optimization
        working_debts = [debt.copy() for debt in debts]
        
        # Get debt repayment parameters with various optimizations
        debt_freedom_plan = self.create_debt_freedom_plan(
            working_debts, monthly_allocation, recommended_method
        )
        
        # Extract repayment strategy from the plan
        repayment_strategy = debt_freedom_plan.get('repayment_strategy', {})
        
        # Get payoff order from the strategy
        payoff_order = repayment_strategy.get('recommended_payoff_order', [])
        
        # Enhance payoff order with additional optimization insights
        enhanced_payoff_order = []
        for i, debt in enumerate(payoff_order):
            # Calculate estimated payoff date
            # This is a simplification - would use more detailed calculation in production
            estimated_months = 0
            if i == 0:
                # For first debt, use recommended payment
                balance = debt.get('balance', 0)
                monthly_payment = debt.get('recommended_payment', 0)
                interest_rate = debt.get('interest_rate', 0) / 100
                
                if monthly_payment > 0:
                    # Simple approximation for payoff time
                    # This is a rough estimate assuming constant payment
                    estimated_months = -math.log(1 - (balance * interest_rate / 12) / monthly_payment) / math.log(1 + interest_rate / 12)
                    estimated_months = max(1, round(estimated_months))
            else:
                # For subsequent debts, use milestone months from the payoff timeline
                if i < len(debt_freedom_plan['repayment_strategy']['payoff_timeline'].get('debt_payoff_milestones', [])):
                    milestone = debt_freedom_plan['repayment_strategy']['payoff_timeline']['debt_payoff_milestones'][i-1]
                    estimated_months = milestone.get('month', 0)
                else:
                    # Fallback if milestone not available
                    estimated_months = (i + 1) * 6  # Very rough estimate
            
            # Calculate projected date
            current_date = datetime.now()
            estimated_date = current_date.replace(day=1) + pd.DateOffset(months=estimated_months)
            
            # Enhance with tax considerations and optimization notes
            debt_type = debt.get('type', '').lower()
            tax_notes = []
            
            if debt_type == 'home_loan':
                tax_notes.append("Eligible for tax benefits under Section 80C (principal) and Section 24 (interest)")
            elif debt_type == 'education_loan':
                tax_notes.append("Eligible for tax benefits under Section 80E (interest)")
            
            # Add strategy-specific notes
            strategy_notes = []
            if i == 0:
                # Notes for highest priority debt
                if recommended_method == 'avalanche':
                    strategy_notes.append("Highest interest rate makes this mathematically optimal")
                elif recommended_method == 'snowball':
                    strategy_notes.append("Smallest balance provides quick psychological win")
                else:  # hybrid
                    strategy_notes.append("Balance of high interest and achievable payoff")
            
            # Add to enhanced order
            enhanced_debt = debt.copy()
            enhanced_debt.update({
                'payoff_order': i + 1,
                'estimated_payoff_months': estimated_months,
                'estimated_payoff_date': estimated_date.strftime('%b %Y'),
                'tax_considerations': tax_notes if tax_notes else ["No specific tax benefits"],
                'strategy_notes': strategy_notes
            })
            enhanced_payoff_order.append(enhanced_debt)
        
        return {
            'optimized_payoff_order': enhanced_payoff_order,
            'optimization_method': recommended_method,
            'optimization_rationale': strategy_fit['recommendation_rationale'],
            'payoff_timeline': debt_freedom_plan['repayment_strategy']['payoff_timeline'],
            'additional_insights': [
                "Focus all extra payments on one debt at a time for maximum impact",
                "Maintain minimum payments on all other debts while focusing on target debt",
                "When target debt is paid off, roll entire payment to next debt in sequence",
                "Review and adjust strategy quarterly as interest rates and circumstances change"
            ]
        }
    
    def optimize_consolidation_strategy(self, goal_data):
        """
        Optimize debt consolidation strategy by analyzing which debts should be
        consolidated and through which method.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with optimized consolidation strategy
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        debts = goal_data.get('debts', [])
        monthly_allocation = goal_data.get('monthly_allocation', 0)
        credit_score = goal_data.get('credit_score', 700)  # Default to average score
        
        # If no debts provided, return generic optimization
        if not debts or monthly_allocation <= 0:
            return {
                'message': "Cannot optimize consolidation strategy without sufficient details",
                'recommendation': "Provide detailed debt information and monthly allocation"
            }
        
        # Assess consolidation feasibility
        consolidation_assessment = self.assess_debt_consolidation_feasibility(goal_data)
        
        # If consolidation is not feasible, return assessment
        if consolidation_assessment.get('consolidation_feasibility') == "Not Feasible":
            return {
                'is_consolidation_recommended': False,
                'reason': consolidation_assessment.get('rationale'),
                'consolidation_assessment': consolidation_assessment
            }
        
        # Get all eligible consolidation options
        consolidation_options = consolidation_assessment.get('consolidation_options', [])
        eligible_options = [option for option in consolidation_options if option.get('eligible') == "Yes"]
        
        # If no eligible options, return assessment
        if not eligible_options:
            return {
                'is_consolidation_recommended': False,
                'reason': "No eligible consolidation options available",
                'consolidation_assessment': consolidation_assessment
            }
        
        # Find best option based on total savings
        best_option = max(eligible_options, key=lambda x: x.get('total_savings', 0) if 'total_savings' in x else 0)
        
        # Categorize debts into consolidation groups
        consolidation_threshold = self.debt_optimization_params.get('consolidation_threshold', 0.12)
        
        # Group 1: High-interest debts suitable for consolidation
        high_interest_debts = [debt for debt in debts if debt.get('interest_rate', 0) > consolidation_threshold]
        high_interest_total = sum(debt.get('balance', 0) for debt in high_interest_debts)
        
        # Group 2: Tax-advantaged debts to keep separate
        tax_advantaged_debts = [debt for debt in debts if 
                               debt.get('type', '').lower() in ['home_loan', 'education_loan'] and 
                               debt.get('interest_rate', 0) <= consolidation_threshold]
        
        # Group 3: Low-interest debts to keep separate
        low_interest_debts = [debt for debt in debts if 
                             debt.get('interest_rate', 0) <= consolidation_threshold and
                             debt.get('type', '').lower() not in ['home_loan', 'education_loan']]
        
        # Calculate optimized monthly payments after consolidation
        # Calculate old monthly total
        old_monthly_total = 0
        for debt in high_interest_debts:
            if 'monthly_payment' in debt:
                old_monthly_total += debt['monthly_payment']
            else:
                # Estimate monthly payment
                balance = debt.get('balance', 0)
                rate = debt.get('interest_rate', 0)
                term = debt.get('remaining_term', 3) * 12  # Default to 3 years if not specified
                old_monthly_total += self._calculate_emi(balance, rate, term/12)
        
        # Calculate new monthly payment
        new_monthly_payment = 0
        if best_option.get('option') == "Personal Loan":
            new_monthly_payment = self._calculate_emi(high_interest_total, 
                                                    float(best_option.get('interest_rate', '0%').strip('%')) / 100, 
                                                    3)  # Assume 3-year term
        elif best_option.get('option') == "Loan Against Property":
            new_monthly_payment = self._calculate_emi(high_interest_total, 
                                                    float(best_option.get('interest_rate', '0%').strip('%')) / 100, 
                                                    10)  # Assume 10-year term
        else:  # Balance transfer
            # For balance transfer, estimate payment to pay off during intro period
            intro_period = int(best_option.get('introductory_period', '6 months').split()[0])
            new_monthly_payment = high_interest_total / intro_period
        
        # Calculate monthly savings
        monthly_savings = old_monthly_total - new_monthly_payment
        
        # Create optimized consolidation strategy
        optimized_strategy = {
            'is_consolidation_recommended': True,
            'recommended_option': best_option.get('option'),
            'consolidation_details': best_option,
            'debts_to_consolidate': [
                {
                    'name': debt.get('name', f"{debt.get('type', 'Debt')} {debt.get('id', '')}"),
                    'type': debt.get('type', 'other'),
                    'balance': round(debt.get('balance', 0)),
                    'interest_rate': round(debt.get('interest_rate', 0) * 100, 2)
                }
                for debt in high_interest_debts
            ],
            'debts_to_keep_separate': [
                {
                    'name': debt.get('name', f"{debt.get('type', 'Debt')} {debt.get('id', '')}"),
                    'type': debt.get('type', 'other'),
                    'balance': round(debt.get('balance', 0)),
                    'interest_rate': round(debt.get('interest_rate', 0) * 100, 2),
                    'reason': "Tax-advantaged debt" if debt.get('type', '').lower() in ['home_loan', 'education_loan'] else "Low interest rate"
                }
                for debt in tax_advantaged_debts + low_interest_debts
            ],
            'financial_impact': {
                'total_to_consolidate': round(high_interest_total),
                'old_monthly_payment': round(old_monthly_total),
                'new_monthly_payment': round(new_monthly_payment),
                'monthly_savings': round(monthly_savings),
                'total_savings': round(best_option.get('total_savings', 0))
            },
            'implementation_steps': [
                "Compare actual rates from multiple lenders to ensure you get the best available rate",
                "Read all terms and conditions carefully before applying",
                "Calculate exact payoff amounts for all debts to be consolidated",
                "Prepare all required documentation (income proof, identity, address proof, etc.)",
                "After approval, ensure all consolidated debts are fully paid off",
                "Set up automatic payments for new consolidation loan",
                "Create plan for utilizing freed-up cash flow"
            ]
        }
        
        if monthly_savings > 0:
            optimized_strategy['reallocation_recommendation'] = {
                'monthly_amount': round(monthly_savings),
                'recommended_uses': [
                    {"allocation": round(monthly_savings * 0.5), "purpose": "Additional debt payment to next highest priority debt"},
                    {"allocation": round(monthly_savings * 0.3), "purpose": "Emergency fund building"},
                    {"allocation": round(monthly_savings * 0.2), "purpose": "Long-term investment"}
                ]
            }
        
        return optimized_strategy
        
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive debt repayment funding strategy with optimization features.
        
        Args:
            goal_data: Dictionary with debt repayment goal details
            
        Returns:
            Dictionary with comprehensive debt repayment strategy
        """
        # Initialize utility classes
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # Extract debt repayment specific information
        debts = goal_data.get('debts', [])
        monthly_allocation = goal_data.get('monthly_allocation')
        preferred_method = goal_data.get('preferred_method')
        time_horizon = goal_data.get('time_horizon')
        
        # Calculate total debt if target amount not provided
        target_amount = goal_data.get('target_amount')
        if not target_amount and debts:
            target_amount = sum(debt.get('balance', 0) for debt in debts)
            
        # Get monthly allocation if not provided
        if not monthly_allocation and time_horizon:
            # Simple calculation assuming linear payoff
            monthly_allocation = target_amount / (time_horizon * 12)
            
        # Create debt repayment specific goal data
        repayment_goal = {
            'goal_type': 'debt_repayment',
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'risk_profile': 'conservative',  # Debt repayment is inherently conservative
            'current_savings': 0,  # Not applicable for debt repayment
            'monthly_contribution': monthly_allocation
        }
        
        # Get base funding strategy if no detailed debts provided
        if not debts:
            return super().generate_funding_strategy(repayment_goal)
        
        # Enhanced with constraint assessments
        # 1. Assess debt repayment capacity
        capacity_assessment = self.assess_debt_repayment_capacity(goal_data)
        
        # 2. Validate repayment strategy fit
        strategy_fit = self.validate_repayment_strategy_fit(goal_data)
        
        # 3. Assess debt consolidation feasibility
        consolidation_assessment = self.assess_debt_consolidation_feasibility(goal_data)
        
        # 4. Evaluate debt repayment impact on other goals
        impact_assessment = self.evaluate_debt_repayment_impact(goal_data)
        
        # Apply optimization strategies
        # 1. Optimize debt allocation
        debt_allocation = self.optimize_debt_allocation(goal_data)
        
        # 2. Optimize repayment order
        repayment_order = self.optimize_repayment_order(goal_data)
        
        # 3. Optimize consolidation strategy if beneficial
        consolidation_strategy = self.optimize_consolidation_strategy(goal_data)
        
        # Create comprehensive debt freedom plan with base and optimized elements
        debt_freedom_plan = self.create_debt_freedom_plan(
            debts, monthly_allocation, strategy_fit['recommended_method']
        )
        
        # Create strategy with base elements and constraint/optimization elements
        strategy = {
            'goal_type': 'debt_repayment',
            'target_amount': target_amount,
            'monthly_allocation': monthly_allocation,
            'constraint_assessments': {
                'repayment_capacity': capacity_assessment,
                'strategy_fit': strategy_fit,
                'consolidation_feasibility': consolidation_assessment,
                'financial_impact': impact_assessment
            },
            'optimization_strategies': {
                'debt_allocation': debt_allocation,
                'repayment_order': repayment_order,
                'consolidation_strategy': consolidation_strategy if consolidation_strategy.get('is_consolidation_recommended', False) else None
            },
            'debt_freedom_plan': debt_freedom_plan
        }
        
        # Add debt repayment specific advice
        strategy['specific_advice'] = {
            'mindset_shift': [
                "Commit to no new debt while paying off existing debt",
                "Track progress visually for motivation",
                "Create specific celebration milestones for each debt paid"
            ],
            'behavioral_strategies': [
                "Automate minimum payments to avoid missed payments",
                "Automate extra payments to highest priority debt",
                "Increase income through side hustles specifically for debt payoff",
                "Implement cash-only policy for discretionary spending"
            ],
            'financial_tactics': [
                "Build emergency fund first to avoid new debt emergencies",
                "Review interest rates quarterly and look for reduction opportunities",
                "Optimize tax benefits from eligible debts",
                "Consider debt consolidation if it offers significant savings"
            ]
        }
        
        # Add India-specific guidance
        strategy['india_specific_guidance'] = {
            'tax_optimization': [
                "Utilize Section 80C benefits for home loan principal repayment (up to ₹1.5L)",
                "Claim Section 24 deduction for home loan interest (up to ₹2L for self-occupied property)",
                "Claim Section 80E deduction for education loan interest (no upper limit, available for 8 years)",
                "Maintain proper documentation for tax-deductible loan payments"
            ],
            'debt_types': [
                "Prioritize unsecured high-interest debts (personal loans, credit cards) for faster repayment",
                "Consider converting high-interest personal loans to secured loans for lower rates",
                "Evaluate gold loan as short-term alternative to high-interest personal loans",
                "Restructure home loans to take advantage of current interest rate environment"
            ],
            'regional_considerations': [
                "Urban centers: Target aggressive repayment to offset high cost of living",
                "Tier 2/3 cities: Balance between debt repayment and property investment may be optimal",
                "Rural areas: Focus on productive agricultural or business loans over consumer debt"
            ]
        }
        
        # Integrate rebalancing strategy if profile data is available
        if 'profile_data' in goal_data:
            rebalancing_strategy = self.integrate_rebalancing_strategy(goal_data, goal_data['profile_data'])
            strategy['rebalancing_strategy'] = rebalancing_strategy
        
        return strategy