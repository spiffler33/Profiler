import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class EmergencyFundStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for emergency funds with
    India-specific liquidity and safety considerations.
    """
    
    def __init__(self):
        """Initialize with emergency fund specific parameters"""
        super().__init__()
        
        # Additional emergency fund specific parameters
        self.emergency_params = {
            "recommended_months": {
                "default": 6,
                "single_income": 9,
                "freelancer": 12,
                "dual_income": 4
            },
            "expense_categories": {
                "essential": ["housing", "utilities", "food", "healthcare", "transportation", "insurance", "debt_payments"],
                "discretionary": ["entertainment", "dining", "shopping", "travel", "subscriptions"]
            },
            "liquid_options": {
                "savings_account": {
                    "expected_return": 0.035,
                    "liquidity": "immediate",
                    "min_balance": 10000
                },
                "liquid_funds": {
                    "expected_return": 0.055,
                    "liquidity": "T+1 day",
                    "exit_load": "None for most funds"
                },
                "sweep_fd": {
                    "expected_return": 0.06,
                    "liquidity": "immediate up to savings balance",
                    "min_balance": 25000
                }
            },
            "inflation_protection": {
                "review_frequency": "every 6 months",
                "increase_percentage": 0.05  # 5% increase every review
            },
            "liquidity_optimization": {
                "tier1_minimum_percentage": 0.30,  # Minimum 30% in immediate access
                "tier1_maximum_percentage": 0.40,  # Maximum 40% in immediate access
                "tier2_target_percentage": 0.40,   # Target 40% in quick access (1-2 days)
                "tier3_maximum_percentage": 0.30,  # Maximum 30% in slightly delayed access
                "rebalancing_threshold": 0.05      # 5% deviation triggers rebalancing
            },
            "yield_optimization": {
                "sweep_account_minimum": 100000,   # Minimum for sweep account setup
                "liquid_fund_minimum": 50000,      # Minimum for liquid fund setup
                "high_yield_savings_options": ["HDFC", "ICICI", "Kotak", "Axis"],
                "top_liquid_funds": ["Aditya Birla Sun Life Liquid Fund", "HDFC Liquid Fund", "Kotak Liquid Fund"],
                "expected_return_premium": 0.012   # 1.2% additional from optimization
            }
        }
        
        # Load emergency fund specific parameters
        self._load_emergency_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the StrategyOptimizer instance if not already initialized"""
        super()._initialize_optimizer()
        
    def _initialize_constraints(self):
        """Initialize the FundingConstraints instance if not already initialized"""
        super()._initialize_constraints()
        
    def _initialize_compound_strategy(self):
        """Initialize the CompoundStrategy instance if not already initialized"""
        super()._initialize_compound_strategy()
        
    def _load_emergency_parameters(self):
        """Load emergency fund specific parameters from service"""
        if self.param_service:
            try:
                # Load recommended months
                rec_months = self.param_service.get_parameter('emergency_recommended_months')
                if rec_months:
                    self.emergency_params['recommended_months'].update(rec_months)
                
                # Load expense categories
                expense_cats = self.param_service.get_parameter('emergency_expense_categories')
                if expense_cats:
                    self.emergency_params['expense_categories'].update(expense_cats)
                
                # Load liquid options
                liquid_opts = self.param_service.get_parameter('emergency_liquid_options')
                if liquid_opts:
                    self.emergency_params['liquid_options'].update(liquid_opts)
                
                # Load inflation protection
                inflation_protection = self.param_service.get_parameter('emergency_inflation_protection')
                if inflation_protection:
                    self.emergency_params['inflation_protection'].update(inflation_protection)
                
            except Exception as e:
                logger.error(f"Error loading emergency fund parameters: {e}")
                # Continue with default parameters
    
    def calculate_required_emergency_fund(self, monthly_expenses, income_type='default', include_discretionary=False):
        """
        Calculate required emergency fund amount based on expenses and income type.
        
        Args:
            monthly_expenses: Dictionary with expense categories and amounts
            income_type: 'default', 'single_income', 'freelancer', or 'dual_income'
            include_discretionary: Whether to include discretionary expenses
            
        Returns:
            Required emergency fund amount
        """
        # Get recommended months based on income type
        recommended_months = self.emergency_params['recommended_months'].get(income_type, 
                                                               self.emergency_params['recommended_months']['default'])
        
        # Calculate total monthly essential expenses
        total_monthly = 0
        
        # If monthly_expenses is a dictionary with categories
        if isinstance(monthly_expenses, dict):
            essential_categories = self.emergency_params['expense_categories']['essential']
            discretionary_categories = self.emergency_params['expense_categories']['discretionary']
            
            # Sum up essential expenses
            for category in essential_categories:
                if category in monthly_expenses:
                    total_monthly += monthly_expenses[category]
            
            # Add discretionary if requested
            if include_discretionary:
                for category in discretionary_categories:
                    if category in monthly_expenses:
                        total_monthly += monthly_expenses[category]
        else:
            # If it's just a single number
            total_monthly = monthly_expenses
        
        # Calculate required fund
        required_fund = total_monthly * recommended_months
        
        return required_fund
    
    def recommend_emergency_allocation(self):
        """
        Recommend asset allocation specifically for emergency funds.
        
        Returns:
            Dictionary with recommended asset allocation
        """
        # Emergency funds should be highly liquid and safe
        allocation = {
            'cash': 0.4,  # 40% in savings/checking accounts
            'liquid_funds': 0.4,  # 40% in liquid funds
            'short_term_fd': 0.2,  # 20% in short-term fixed deposits
            'equity': 0,
            'debt': 0,
            'gold': 0,
            'alternatives': 0
        }
        
        return allocation
    
    def analyze_emergency_preparedness(self, monthly_expenses, current_emergency_fund, 
                                     income_type='default', include_discretionary=False):
        """
        Analyze emergency preparedness based on current fund and expenses.
        
        Args:
            monthly_expenses: Dictionary with expense categories and amounts
            current_emergency_fund: Current emergency fund amount
            income_type: 'default', 'single_income', 'freelancer', or 'dual_income'
            include_discretionary: Whether to include discretionary expenses
            
        Returns:
            Dictionary with emergency preparedness analysis
        """
        # Calculate required emergency fund
        required_fund = self.calculate_required_emergency_fund(
            monthly_expenses, income_type, include_discretionary
        )
        
        # Calculate current coverage in months
        total_monthly = 0
        if isinstance(monthly_expenses, dict):
            essential_categories = self.emergency_params['expense_categories']['essential']
            discretionary_categories = self.emergency_params['expense_categories']['discretionary']
            
            # Sum up essential expenses
            for category in essential_categories:
                if category in monthly_expenses:
                    total_monthly += monthly_expenses[category]
            
            # Add discretionary if requested
            if include_discretionary:
                for category in discretionary_categories:
                    if category in monthly_expenses:
                        total_monthly += monthly_expenses[category]
        else:
            # If it's just a single number
            total_monthly = monthly_expenses
        
        # Avoid division by zero
        current_months_covered = 0
        if total_monthly > 0:
            current_months_covered = current_emergency_fund / total_monthly
        
        # Calculate gap
        gap = max(0, required_fund - current_emergency_fund)
        
        # Calculate percentage funded
        percent_funded = (current_emergency_fund / required_fund * 100) if required_fund > 0 else 0
        
        # Determine preparedness level
        if percent_funded >= 100:
            preparedness_level = "Fully Prepared"
        elif percent_funded >= 75:
            preparedness_level = "Well Prepared"
        elif percent_funded >= 50:
            preparedness_level = "Moderately Prepared"
        elif percent_funded >= 25:
            preparedness_level = "Somewhat Prepared"
        else:
            preparedness_level = "Underprepared"
        
        # Recommended monthly contribution to fill gap
        # Aim to build emergency fund within 12 months
        recommended_monthly = gap / 12
        
        return {
            'required_fund': round(required_fund),
            'current_fund': current_emergency_fund,
            'gap': round(gap),
            'percent_funded': round(percent_funded, 1),
            'current_months_covered': round(current_months_covered, 1),
            'recommended_months': self.emergency_params['recommended_months'].get(
                income_type, self.emergency_params['recommended_months']['default']
            ),
            'preparedness_level': preparedness_level,
            'recommended_monthly_contribution': round(recommended_monthly)
        }
    
    def recommend_emergency_instruments(self, emergency_fund_amount):
        """
        Recommend specific investment instruments for emergency fund.
        
        Args:
            emergency_fund_amount: Total emergency fund amount
            
        Returns:
            Dictionary with specific investment recommendations
        """
        # Get allocation for emergency fund
        allocation = self.recommend_emergency_allocation()
        
        # Calculate amount for each component
        cash_amount = emergency_fund_amount * allocation['cash']
        liquid_funds_amount = emergency_fund_amount * allocation['liquid_funds']
        short_term_fd_amount = emergency_fund_amount * allocation['short_term_fd']
        
        # Determine specific instruments
        recommendations = {
            'immediate_access': {
                'savings_account': cash_amount,
                'expected_return': self.emergency_params['liquid_options']['savings_account']['expected_return'] * 100,
                'access_time': 'Immediate',
                'features': 'Lowest returns but instant accessibility'
            },
            'quick_access': {
                'liquid_funds': liquid_funds_amount,
                'expected_return': self.emergency_params['liquid_options']['liquid_funds']['expected_return'] * 100,
                'access_time': '1-2 business days',
                'features': 'Better returns than savings, minimal exit loads'
            },
            'backup_tier': {
                'short_term_fd': short_term_fd_amount,
                'expected_return': self.emergency_params['liquid_options']['sweep_fd']['expected_return'] * 100,
                'access_time': '1-7 days (with some penalty for premature withdrawal)',
                'features': 'Higher returns, slight delay in accessibility'
            }
        }
        
        # Add weighted average expected return
        weighted_return = (
            allocation['cash'] * self.emergency_params['liquid_options']['savings_account']['expected_return'] +
            allocation['liquid_funds'] * self.emergency_params['liquid_options']['liquid_funds']['expected_return'] +
            allocation['short_term_fd'] * self.emergency_params['liquid_options']['sweep_fd']['expected_return']
        )
        
        recommendations['weighted_average_return'] = round(weighted_return * 100, 2)
        
        return recommendations
    
    def create_emergency_fund_plan(self, goal_data):
        """
        Create detailed emergency fund plan.
        
        Args:
            goal_data: Dictionary with emergency fund details
            
        Returns:
            Dictionary with comprehensive emergency fund plan
        """
        # Extract emergency fund specific information
        monthly_expenses = goal_data.get('monthly_expenses', {})
        current_fund = goal_data.get('current_emergency_fund', 0)
        income_type = goal_data.get('income_type', 'default')
        include_discretionary = goal_data.get('include_discretionary', False)
        
        # Analyze emergency preparedness
        preparedness = self.analyze_emergency_preparedness(
            monthly_expenses, current_fund, income_type, include_discretionary
        )
        
        # Recommend instruments for the emergency fund
        instrument_recommendations = self.recommend_emergency_instruments(
            preparedness['required_fund']
        )
        
        # Calculate timeframe to fully fund
        months_to_fund = 0
        if preparedness['gap'] > 0 and preparedness['recommended_monthly_contribution'] > 0:
            months_to_fund = preparedness['gap'] / preparedness['recommended_monthly_contribution']
        
        # Inflation protection plan
        inflation_protection = {
            'review_frequency': self.emergency_params['inflation_protection']['review_frequency'],
            'recommended_increase': self.emergency_params['inflation_protection']['increase_percentage'] * 100,
            'next_review_date': (datetime.now().replace(day=1) + 
                              pd.DateOffset(months=6)).strftime('%Y-%m-%d')
        }
        
        # Compile emergency fund plan
        emergency_plan = {
            'emergency_fund_analysis': preparedness,
            'recommended_allocation': instrument_recommendations,
            'funding_timeline': {
                'months_to_full_funding': round(months_to_fund),
                'recommended_monthly_contribution': preparedness['recommended_monthly_contribution'],
                'priority_level': 'High' if preparedness['percent_funded'] < 50 else 'Medium'
            },
            'inflation_protection': inflation_protection,
            'maintenance_strategy': {
                'replenishment_priority': 'Highest - replenish before other financial goals if used',
                'periodic_review': 'Every 6 months to account for expense changes',
                'rebalancing_frequency': 'Annual'
            }
        }
        
        return emergency_plan
    
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy tailored for emergency funds.
        
        Emergency funds require minimal rebalancing with a focus on liquidity
        and safety rather than maximizing returns. The rebalancing approach
        is conservative and designed to maintain constant accessibility.
        
        Args:
            goal_data: Dictionary with emergency fund details
            profile_data: Dictionary with user profile information
            
        Returns:
            Dictionary with emergency fund rebalancing strategy
        """
        # Create rebalancing instance
        rebalancing = RebalancingStrategy()
        
        # Extract goal information
        target_amount = goal_data.get('target_amount', 0)
        current_fund = goal_data.get('current_emergency_fund', 0)
        
        # Default asset allocation for emergency funds
        allocation = self.recommend_emergency_allocation()
        
        # If profile data not provided, create minimal profile
        if not profile_data:
            profile_data = {
                'risk_profile': 'conservative',
                'portfolio_value': current_fund,
                'liquidity_needs': {
                    'near_term': current_fund,  # All emergency funds are near-term by nature
                    'timeline_months': 1  # Assume immediate need possible
                }
            }
        
        # Create goal data specifically for rebalancing
        rebalancing_goal = {
            'goal_type': 'emergency_fund',
            'time_horizon': 1,  # Emergency funds always have immediate horizon
            'target_allocation': allocation,
            'current_allocation': goal_data.get('current_allocation', allocation),
            'priority_level': 'high'  # Emergency funds are high priority
        }
        
        # Design rebalancing schedule - use annual or semi-annual with trigger-based approach
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(
            rebalancing_goal, profile_data
        )
        
        # Customize drift thresholds for emergency funds
        custom_thresholds = {
            'cash': 0.01,  # Tighter threshold for cash (1%)
            'liquid_funds': 0.02,  # Slightly wider for liquid funds (2%)
            'short_term_fd': 0.03  # Wider for FDs (3%)
        }
        
        drift_thresholds = rebalancing.calculate_drift_thresholds(custom_thresholds)
        
        # Create emergency fund specific rebalancing strategy
        emergency_rebalancing = {
            'goal_type': 'emergency_fund',
            'approach': 'conservative_minimal',
            'rationale': 'Emergency funds require minimal rebalancing with focus on liquidity maintenance',
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': drift_thresholds,
            'priority': 'Maintaining liquidity over optimization',
            'emergency_specific_considerations': {
                'liquidity_focus': 'Maintain high levels of liquidity at all times',
                'accessibility': 'Ensure immediate access to at least 30% of funds',
                'safety_priority': 'Prioritize capital preservation over growth'
            },
            'implementation_priorities': [
                'Rebalance primarily through new contributions',
                'Avoid transactions that reduce immediate accessibility',
                'Maintain at least 40% in highly liquid instruments regardless of allocation',
                'Rebalancing should never compromise the immediate availability of funds'
            ]
        }
        
        return emergency_rebalancing
    
    def optimize_liquidity_allocation(self, emergency_fund_amount):
        """
        Optimize allocation between liquidity tiers to maximize returns while ensuring immediate access.
        
        Args:
            emergency_fund_amount: Total emergency fund amount
            
        Returns:
            Optimized allocation across liquidity tiers
        """
        # Initialize optimizer if needed
        self._initialize_optimizer()
        
        # Get liquidity optimization parameters
        tier1_min = self.emergency_params['liquidity_optimization']['tier1_minimum_percentage']
        tier1_max = self.emergency_params['liquidity_optimization']['tier1_maximum_percentage']
        tier2_target = self.emergency_params['liquidity_optimization']['tier2_target_percentage']
        tier3_max = self.emergency_params['liquidity_optimization']['tier3_maximum_percentage']
        
        # Calculate minimum amounts for various instruments
        sweep_min = self.emergency_params['yield_optimization']['sweep_account_minimum']
        liquid_min = self.emergency_params['yield_optimization']['liquid_fund_minimum']
        
        # Default allocation
        allocation = {
            'tier1_immediate': tier1_min,
            'tier2_quick': tier2_target,
            'tier3_short_term': 1.0 - tier1_min - tier2_target
        }
        
        # Optimize based on fund size
        if emergency_fund_amount < 100000:
            # For small funds, keep everything in immediate access
            allocation = {
                'tier1_immediate': 1.0,
                'tier2_quick': 0.0,
                'tier3_short_term': 0.0
            }
        elif emergency_fund_amount < 200000:
            # For medium funds, focus on first two tiers
            allocation = {
                'tier1_immediate': 0.6,
                'tier2_quick': 0.4,
                'tier3_short_term': 0.0
            }
        else:
            # For larger funds, optimize across all tiers
            tier1_immediate = max(tier1_min, min(tier1_max, 50000 / emergency_fund_amount))
            
            # Check if we can meet minimum for sweep and liquid
            if emergency_fund_amount * (1.0 - tier1_immediate) >= sweep_min + liquid_min:
                tier2_quick = tier2_target
                tier3_short_term = 1.0 - tier1_immediate - tier2_quick
            else:
                # Adjust tier2 to ensure we meet minimum for at least liquid funds
                tier2_quick = max(tier2_target, liquid_min / emergency_fund_amount)
                tier3_short_term = max(0.0, 1.0 - tier1_immediate - tier2_quick)
            
            allocation = {
                'tier1_immediate': tier1_immediate,
                'tier2_quick': tier2_quick,
                'tier3_short_term': tier3_short_term
            }
        
        # Calculate amounts for each tier
        amounts = {
            'tier1_immediate': round(emergency_fund_amount * allocation['tier1_immediate']),
            'tier2_quick': round(emergency_fund_amount * allocation['tier2_quick']),
            'tier3_short_term': round(emergency_fund_amount * allocation['tier3_short_term'])
        }
        
        # Calculate expected returns
        savings_return = self.emergency_params['liquid_options']['savings_account']['expected_return']
        liquid_return = self.emergency_params['liquid_options']['liquid_funds']['expected_return']
        sweep_return = self.emergency_params['liquid_options']['sweep_fd']['expected_return']
        
        weighted_return = (
            allocation['tier1_immediate'] * savings_return +
            allocation['tier2_quick'] * liquid_return +
            allocation['tier3_short_term'] * sweep_return
        )
        
        return {
            'allocation_percentages': {
                'tier1_immediate': round(allocation['tier1_immediate'] * 100, 1),
                'tier2_quick': round(allocation['tier2_quick'] * 100, 1),
                'tier3_short_term': round(allocation['tier3_short_term'] * 100, 1)
            },
            'allocation_amounts': amounts,
            'expected_return': round(weighted_return * 100, 2),
            'access_analysis': {
                'immediate_access_percentage': round(allocation['tier1_immediate'] * 100, 1),
                'within_2_days_percentage': round((allocation['tier1_immediate'] + allocation['tier2_quick']) * 100, 1),
                'within_7_days_percentage': 100.0
            }
        }
    
    def optimize_yield(self, optimized_allocation, emergency_fund_amount):
        """
        Optimize yield within each liquidity tier while maintaining required accessibility.
        
        Args:
            optimized_allocation: Optimized allocation across liquidity tiers
            emergency_fund_amount: Total emergency fund amount
            
        Returns:
            Yield-optimized instrument recommendations
        """
        # Initialize optimizer if needed
        self._initialize_optimizer()
        
        # Get tier amounts
        tier1_amount = optimized_allocation['allocation_amounts']['tier1_immediate']
        tier2_amount = optimized_allocation['allocation_amounts']['tier2_quick']
        tier3_amount = optimized_allocation['allocation_amounts']['tier3_short_term']
        
        # Get recommended options for each tier
        high_yield_savings = self.emergency_params['yield_optimization']['high_yield_savings_options']
        top_liquid_funds = self.emergency_params['yield_optimization']['top_liquid_funds']
        
        # Base returns
        savings_return = self.emergency_params['liquid_options']['savings_account']['expected_return']
        liquid_return = self.emergency_params['liquid_options']['liquid_funds']['expected_return']
        sweep_return = self.emergency_params['liquid_options']['sweep_fd']['expected_return']
        
        # Potential return premium from optimization
        return_premium = self.emergency_params['yield_optimization']['expected_return_premium']
        
        # Tier 1 optimization (immediate access)
        tier1_instruments = {}
        if tier1_amount > 0:
            # For larger amounts, split between high-yield savings and regular savings
            if tier1_amount >= 100000:
                high_yield_amount = round(tier1_amount * 0.7)
                regular_savings_amount = tier1_amount - high_yield_amount
                
                tier1_instruments = {
                    'high_yield_savings': {
                        'amount': high_yield_amount,
                        'expected_return': round((savings_return + return_premium * 0.5) * 100, 2),
                        'recommended_options': high_yield_savings[:2]
                    },
                    'regular_savings': {
                        'amount': regular_savings_amount,
                        'expected_return': round(savings_return * 100, 2)
                    }
                }
            else:
                tier1_instruments = {
                    'regular_savings': {
                        'amount': tier1_amount,
                        'expected_return': round(savings_return * 100, 2)
                    }
                }
        
        # Tier 2 optimization (quick access)
        tier2_instruments = {}
        if tier2_amount > 0:
            # For larger amounts, use a mix of liquid funds
            if tier2_amount >= 100000:
                overnight_fund_amount = round(tier2_amount * 0.4)
                liquid_fund_amount = tier2_amount - overnight_fund_amount
                
                tier2_instruments = {
                    'overnight_funds': {
                        'amount': overnight_fund_amount,
                        'expected_return': round((liquid_return - 0.005) * 100, 2),
                        'access_time': 'T+1 day'
                    },
                    'liquid_funds': {
                        'amount': liquid_fund_amount,
                        'expected_return': round((liquid_return + return_premium * 0.7) * 100, 2),
                        'recommended_options': top_liquid_funds,
                        'access_time': 'T+1 to T+2 days'
                    }
                }
            else:
                tier2_instruments = {
                    'liquid_funds': {
                        'amount': tier2_amount,
                        'expected_return': round((liquid_return + return_premium * 0.5) * 100, 2),
                        'recommended_options': [top_liquid_funds[0]],
                        'access_time': 'T+1 to T+2 days'
                    }
                }
        
        # Tier 3 optimization (short-term)
        tier3_instruments = {}
        if tier3_amount > 0:
            if tier3_amount >= 200000:
                sweep_fd_amount = round(tier3_amount * 0.6)
                arbitrage_fund_amount = tier3_amount - sweep_fd_amount
                
                tier3_instruments = {
                    'sweep_fd': {
                        'amount': sweep_fd_amount,
                        'expected_return': round(sweep_return * 100, 2),
                        'access_time': '1-3 days'
                    },
                    'arbitrage_funds': {
                        'amount': arbitrage_fund_amount,
                        'expected_return': round((sweep_return + return_premium) * 100, 2),
                        'access_time': '3-7 days',
                        'tax_efficiency': 'Better than FDs for amounts held > 1 year'
                    }
                }
            else:
                tier3_instruments = {
                    'sweep_fd': {
                        'amount': tier3_amount,
                        'expected_return': round(sweep_return * 100, 2),
                        'access_time': '1-3 days'
                    }
                }
        
        # Calculate overall optimized return
        base_return = (
            (tier1_amount * savings_return) +
            (tier2_amount * liquid_return) +
            (tier3_amount * sweep_return)
        ) / emergency_fund_amount if emergency_fund_amount > 0 else 0
        
        # Calculate instrument-specific returns
        instruments_return = 0
        total_accounted = 0
        
        # Tier 1
        for instrument, details in tier1_instruments.items():
            instruments_return += details['amount'] * (details['expected_return'] / 100)
            total_accounted += details['amount']
            
        # Tier 2
        for instrument, details in tier2_instruments.items():
            instruments_return += details['amount'] * (details['expected_return'] / 100)
            total_accounted += details['amount']
            
        # Tier 3
        for instrument, details in tier3_instruments.items():
            instruments_return += details['amount'] * (details['expected_return'] / 100)
            total_accounted += details['amount']
            
        optimized_return = instruments_return / total_accounted if total_accounted > 0 else base_return
        improvement = optimized_return - base_return
        
        return {
            'optimized_instruments': {
                'tier1_immediate': tier1_instruments,
                'tier2_quick': tier2_instruments,
                'tier3_short_term': tier3_instruments
            },
            'return_optimization': {
                'base_return': round(base_return * 100, 2),
                'optimized_return': round(optimized_return * 100, 2),
                'improvement': round(improvement * 100, 2),
                'annual_additional_income': round(improvement * emergency_fund_amount)
            }
        }
    
    def assess_emergency_fund_feasibility(self, strategy, profile_data):
        """
        Assess the feasibility of the emergency fund strategy given income and expenses.
        
        Args:
            strategy: Emergency fund strategy to assess
            profile_data: User profile with income and expense information
            
        Returns:
            Dictionary with emergency fund feasibility assessment
        """
        # Initialize constraints if needed
        self._initialize_constraints()
        
        if not strategy or not profile_data:
            return None
            
        # Extract relevant profile information
        monthly_income = profile_data.get('monthly_income', 0)
        monthly_expenses = profile_data.get('monthly_expenses', 0)
        if not monthly_income or not monthly_expenses:
            logger.warning("Missing income or expense data, cannot assess emergency fund feasibility")
            return None
            
        # Extract emergency fund parameters
        target_amount = strategy.get('target_amount', 0)
        current_amount = strategy.get('current_status', {}).get('current_savings', 0)
        monthly_contribution = strategy.get('recommendation', {}).get('total_monthly_investment', 0)
        
        # Calculate months to build emergency fund
        months_to_build = 0
        if monthly_contribution > 0:
            remaining_amount = target_amount - current_amount
            months_to_build = remaining_amount / monthly_contribution if remaining_amount > 0 else 0
        
        # Calculate contribution as percentage of income
        contribution_percent = monthly_contribution / monthly_income if monthly_income > 0 else 0
        
        # Check if emergency fund target is appropriate
        months_coverage = target_amount / monthly_expenses if monthly_expenses > 0 else 0
        income_stability = profile_data.get('income_stability', 'stable')
        
        # Determine appropriate months of coverage based on income stability
        if income_stability == 'unstable' or income_stability == 'freelancer':
            recommended_months = 9
        elif income_stability == 'very_unstable':
            recommended_months = 12
        elif income_stability == 'dual_income':
            recommended_months = 4
        else:
            recommended_months = 6
        
        # Initialize feasibility assessment
        feasibility = {
            'is_feasible': True,
            'target_assessment': {
                'target_amount': round(target_amount),
                'current_amount': round(current_amount),
                'months_coverage': round(months_coverage, 1),
                'recommended_months': recommended_months,
                'status': 'appropriate' if abs(months_coverage - recommended_months) <= 2 else 
                         ('excessive' if months_coverage > recommended_months + 2 else 'insufficient')
            },
            'timeline_assessment': {
                'monthly_contribution': round(monthly_contribution),
                'months_to_build': round(months_to_build),
                'percent_of_income': round(contribution_percent * 100, 1),
                'status': 'reasonable' if months_to_build <= 12 else 
                         ('extended' if months_to_build <= 24 else 'too_long')
            },
            'recommendations': []
        }
        
        # Generate recommendations based on assessment
        if feasibility['target_assessment']['status'] == 'insufficient':
            feasibility['recommendations'].append(
                f"Current target ({round(months_coverage, 1)} months) provides insufficient coverage for your situation. Aim for {recommended_months} months of expenses."
            )
        elif feasibility['target_assessment']['status'] == 'excessive':
            feasibility['recommendations'].append(
                f"Current target ({round(months_coverage, 1)} months) exceeds recommended coverage ({recommended_months} months). Consider reallocating excess to other financial goals."
            )
        
        if feasibility['timeline_assessment']['status'] == 'too_long':
            feasibility['is_feasible'] = False
            feasibility['recommendations'].append(
                f"Building emergency fund will take {round(months_to_build)} months, which is too long. Increase monthly contribution or consider temporary reallocation from other goals."
            )
        elif feasibility['timeline_assessment']['status'] == 'extended':
            feasibility['recommendations'].append(
                f"Building emergency fund will take {round(months_to_build)} months. Consider moderately increasing contribution to accelerate timeline."
            )
        
        if contribution_percent > 0.3:
            feasibility['is_feasible'] = False
            feasibility['recommendations'].append(
                f"Monthly contribution ({round(contribution_percent * 100)}% of income) is unsustainably high. Extend timeline or adjust target."
            )
        elif contribution_percent > 0.2:
            feasibility['recommendations'].append(
                f"Monthly contribution ({round(contribution_percent * 100)}% of income) is high but may be acceptable for short period."
            )
        
        return feasibility
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive emergency fund strategy with optimizations.
        
        Args:
            goal_data: Dictionary with emergency fund details
            
        Returns:
            Dictionary with comprehensive emergency fund strategy
        """
        # Initialize utility classes
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # Extract emergency fund specific information
        monthly_expenses = goal_data.get('monthly_expenses', {})
        current_fund = goal_data.get('current_emergency_fund', 0)
        income_type = goal_data.get('income_type', 'default')
        include_discretionary = goal_data.get('include_discretionary', False)
        
        # Calculate required fund if target amount not provided
        target_amount = goal_data.get('target_amount')
        if not target_amount:
            target_amount = self.calculate_required_emergency_fund(
                monthly_expenses, income_type, include_discretionary
            )
        
        # Create emergency fund specific goal data
        emergency_goal = {
            'goal_type': 'emergency fund',
            'target_amount': target_amount,
            'time_horizon': goal_data.get('time_horizon', 1),  # Default 1 year for emergency fund
            'risk_profile': 'conservative',  # Always conservative for emergency funds
            'current_savings': current_fund,
            'monthly_contribution': goal_data.get('monthly_contribution', 0),
            
            # Emergency fund specific fields
            'monthly_expenses': monthly_expenses,
            'current_emergency_fund': current_fund,
            'income_type': income_type,
            'include_discretionary': include_discretionary
        }
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(emergency_goal)
        
        # Enhanced with emergency fund specific plan
        emergency_plan = self.create_emergency_fund_plan(emergency_goal)
        
        # Profile data for constraints and optimizations
        profile_data = goal_data.get('profile_data', {})
        
        # Add rebalancing strategy
        if profile_data:
            emergency_goal['rebalancing_strategy'] = self.integrate_rebalancing_strategy(
                emergency_goal, profile_data
            )
            
            # Apply liquidity optimization
            optimized_liquidity = self.optimize_liquidity_allocation(target_amount)
            
            # Apply yield optimization within liquidity constraints
            optimized_yield = self.optimize_yield(optimized_liquidity, target_amount)
            
            # Add optimized solutions to emergency plan
            emergency_plan['optimized_strategy'] = {
                'liquidity_tiers': optimized_liquidity,
                'yield_optimization': optimized_yield,
                'implementation_steps': [
                    f"Setup high-yield savings account with {optimized_yield['optimized_instruments']['tier1_immediate'].get('high_yield_savings', {}).get('recommended_options', ['a major bank'])[0]} for immediate access funds",
                    f"Invest in liquid funds like {', '.join(optimized_yield['optimized_instruments']['tier2_quick'].get('liquid_funds', {}).get('recommended_options', ['liquid fund'])[:1])} for quick access tier",
                    f"Setup sweep FD for remainder to maximize returns while maintaining access"
                ]
            }
            
            # Apply constraints assessment
            emergency_feasibility = self.assess_emergency_fund_feasibility(
                base_strategy, profile_data
            )
            
            if emergency_feasibility:
                base_strategy['emergency_feasibility'] = emergency_feasibility
        
        # Combine into comprehensive strategy
        strategy = {
            **base_strategy,
            'emergency_fund_plan': emergency_plan
        }
        
        # Add rebalancing strategy if available
        if 'rebalancing_strategy' in emergency_goal:
            strategy['rebalancing_strategy'] = emergency_goal['rebalancing_strategy']
        
        # Add emergency fund specific advice
        strategy['specific_advice'] = {
            'accessibility_tiers': [
                'Tier 1: Immediate access (savings account)',
                'Tier 2: Quick access (liquid funds)',
                'Tier 3: Short-term FDs or sweep accounts'
            ],
            'contingency_planning': [
                'Identify essential vs discretionary expenses',
                'Consider health insurance to reduce emergency medical expenses',
                'Set up auto-transfers to build emergency fund consistently'
            ],
            'maintenance_guidelines': [
                'Replenish immediately after use',
                'Review and increase amount as expenses grow',
                'Keep emergency fund separate from other investments'
            ]
        }
        
        # If compound strategy is available, run scenario analysis
        if hasattr(self, 'compound_strategy'):
            try:
                scenario_analysis = self.compound_strategy.analyze_emergency_scenarios(
                    strategy, profile_data
                )
                if scenario_analysis:
                    strategy['scenario_analysis'] = scenario_analysis
            except Exception as e:
                logger.error(f"Error in emergency fund scenario analysis: {e}")
        
        return strategy