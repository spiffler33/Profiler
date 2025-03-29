import json
import logging
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union, Callable, TypeVar, Generic

logger = logging.getLogger(__name__)

# Strategy type for type hinting
Strategy = TypeVar('Strategy')

def get_financial_parameter_service():
    """
    Get the financial parameter service instance.
    
    This is separated out to avoid circular imports and to make testing easier.
    """
    try:
        from services.financial_parameter_service import FinancialParameterService
        return FinancialParameterService()
    except ImportError:
        logger.warning("Financial Parameter Service not available, using default parameters")
        return None


class FundingStrategyGenerator:
    """
    Generator for creating customized funding strategies for financial goals,
    with India-specific investment approach and tax considerations.
    """
    
    def __init__(self):
        """Initialize the generator with parameters from FinancialParameterService"""
        # Get financial parameter service
        self.param_service = get_financial_parameter_service()
        
        # Initialize utility classes for constraints and optimization
        self.constraints = None  # Will be initialized on first use
        self.optimizer = None    # Will be initialized on first use
        self.compound_strategy = None  # Will be initialized on first use
        
        # Initialize params dictionary with default values
        self.params = {
            "inflation_rate": 0.06,  # Default: 6% annual inflation
            "equity_allocation": {
                "conservative": 0.40,  # 40% for conservative equity allocation
                "moderate": 0.60,     # 60% for moderate equity allocation 
                "aggressive": 0.80    # 80% for aggressive equity allocation
            },
            "expected_returns": {
                "equity": 0.12,      # 12% annual for equity
                "debt": 0.07,        # 7% annual for debt
                "cash": 0.035,       # 3.5% annual for cash/liquid funds
                "gold": 0.08,        # 8% annual for gold
                "real_estate": 0.09  # 9% annual for real estate
            },
            "tax_rates": {
                "income_tax": {
                    "default": 0.30,         # Default highest bracket
                    "brackets": [
                        {"limit": 250000, "rate": 0.0},
                        {"limit": 500000, "rate": 0.05},
                        {"limit": 750000, "rate": 0.10},
                        {"limit": 1000000, "rate": 0.15},
                        {"limit": 1250000, "rate": 0.20},
                        {"limit": 1500000, "rate": 0.30}
                    ]
                },
                "ltcg": {
                    "equity": 0.10,         # 10% LTCG on equity (>1yr)
                    "debt": 0.20,           # 20% LTCG on debt/other (>3yrs)
                    "real_estate": 0.20     # 20% LTCG on real estate with indexation
                },
                "stcg": {
                    "equity": 0.15,         # 15% STCG on equity (<1yr)
                    "debt": 0.30,           # As per income tax slab for debt (<3yrs)
                    "real_estate": 0.30     # As per income tax slab for real estate (<2yrs)
                }
            },
            "recurring_investment_options": {
                "sip": {
                    "min_amount": 500,      # Min SIP amount usually 500 INR
                    "frequency_options": ["monthly", "quarterly", "annually"]
                },
                "rds": {
                    "min_amount": 1000,
                    "rate": 0.055           # 5.5% typical for RD (recurring deposit)
                }
            },
            "lumpsum_investment_options": {
                "fd": {
                    "min_amount": 10000,
                    "rates": {
                        "1_year": 0.055,    # 5.5% for 1 year FD
                        "3_year": 0.065,    # 6.5% for 3 year FD
                        "5_year": 0.07      # 7.0% for 5 year FD
                    }
                },
                "tax_saving": {
                    "elss": {
                        "lock_in": 3,       # 3 year lock-in for ELSS
                        "expected_return": 0.12  # 12% expected return
                    },
                    "ppf": {
                        "lock_in": 15,      # 15 year lock-in for PPF
                        "rate": 0.071       # 7.1% current PPF rate
                    }
                }
            },
            # Parameters for portfolio-level optimization
            "portfolio_optimization": {
                "priority_weights": {
                    "emergency_fund": 0.9,
                    "debt_repayment": 0.8,
                    "education": 0.7,
                    "retirement": 0.7,
                    "home_purchase": 0.6,
                    "other": 0.5,
                    "discretionary": 0.3
                },
                "budget_allocation": {
                    "max_total_contribution_percent": 0.5,  # Maximum 50% of income for all goals
                    "essential_minimum_allocation": 0.6,    # At least 60% of budget to essential goals
                    "discretionary_maximum_allocation": 0.2 # At most 20% of budget to discretionary goals
                },
                "candidate_combination_criteria": {
                    "time_horizon_similar_threshold": 3,     # Goals within 3 years of each other
                    "goal_type_combinations": [
                        ["education", "wedding"],           # Common Indian combination for children
                        ["home_purchase", "home_improvement"],
                        ["retirement", "legacy_planning"],
                        ["education", "education"]          # Multiple children education
                    ]
                }
            }
        }
        
        # Override default params with values from parameter service
        self._load_parameters()
        
    def _load_parameters(self):
        """Load parameters from the financial parameter service if available"""
        if self.param_service:
            try:
                # Load general parameters
                inflation = self.param_service.get_parameter('inflation_rate')
                if inflation:
                    self.params['inflation_rate'] = inflation
                
                # Load asset allocation parameters
                allocations = self.param_service.get_parameter('equity_allocation')
                if allocations:
                    self.params['equity_allocation'].update(allocations)
                
                # Load expected returns
                returns = self.param_service.get_parameter('expected_returns')
                if returns:
                    self.params['expected_returns'].update(returns)
                
                # Load tax rates
                tax_rates = self.param_service.get_parameter('tax_rates')
                if tax_rates:
                    self.params['tax_rates'].update(tax_rates)
                
                # Load investment options
                recurring = self.param_service.get_parameter('recurring_investment_options')
                if recurring:
                    self.params['recurring_investment_options'].update(recurring)
                
                lumpsum = self.param_service.get_parameter('lumpsum_investment_options')
                if lumpsum:
                    self.params['lumpsum_investment_options'].update(lumpsum)
                
                # Load portfolio optimization parameters
                portfolio_opt = self.param_service.get_parameter('portfolio_optimization')
                if portfolio_opt:
                    self.params['portfolio_optimization'].update(portfolio_opt)
                
            except Exception as e:
                logger.error(f"Error loading financial parameters: {e}")
                # Continue with default parameters
                
    def _initialize_constraints(self):
        """Initialize the FundingConstraints instance if not already initialized"""
        if self.constraints is None:
            from .base_strategy import FundingConstraints
            self.constraints = FundingConstraints()
            logger.debug("FundingConstraints initialized")
            
    def _initialize_optimizer(self):
        """Initialize the StrategyOptimizer instance if not already initialized"""
        if self.optimizer is None:
            from .base_strategy import StrategyOptimizer
            self.optimizer = StrategyOptimizer() 
            logger.debug("StrategyOptimizer initialized")
            
    def _initialize_compound_strategy(self):
        """Initialize the CompoundStrategy instance if not already initialized"""
        if self.compound_strategy is None:
            from .base_strategy import CompoundStrategy
            self.compound_strategy = CompoundStrategy()
            logger.debug("CompoundStrategy initialized")
    
    def get_strategy_for_goal(self, goal_data):
        """
        Factory method to return the appropriate funding strategy for a goal type.
        
        Args:
            goal_data: Dictionary containing goal details including type
            
        Returns:
            An instance of the appropriate funding strategy class
        """
        goal_type = goal_data.get('goal_type', '').lower()
        
        if goal_type == 'retirement':
            return RetirementFundingStrategy()
        elif goal_type in ('education', 'higher education'):
            return EducationFundingStrategy()
        elif goal_type == 'emergency fund':
            return EmergencyFundStrategy()
        elif goal_type in ('home', 'home purchase', 'down payment'):
            return HomeDownPaymentStrategy()
        elif goal_type in ('vacation', 'travel', 'vehicle', 'car', 'general savings'):
            return DiscretionaryGoalStrategy()
        elif goal_type in ('wedding', 'marriage'):
            return WeddingFundingStrategy()
        elif goal_type in ('debt', 'debt repayment', 'debt consolidation'):
            return DebtRepaymentStrategy()
        elif goal_type in ('estate_planning', 'legacy_planning', 'inheritance'):
            return LegacyPlanningStrategy()
        elif goal_type in ('charitable_giving', 'charity', 'donation'):
            return CharitableGivingStrategy()
        elif goal_type in ('custom', 'other'):
            return CustomGoalStrategy()
        else:
            # Default to base class if no specialized strategy exists
            logger.warning(f"No specialized funding strategy for goal type: {goal_type}")
            return FundingStrategyGenerator()
    
    def recommend_allocation(self, time_horizon, risk_profile='moderate'):
        """
        Recommend asset allocation based on time horizon and risk profile.
        
        Args:
            time_horizon: Time to goal in years
            risk_profile: One of 'conservative', 'moderate', or 'aggressive'
            
        Returns:
            Dictionary with recommended asset allocation percentages
        """
        # Default allocation
        allocation = {'equity': 0, 'debt': 0, 'cash': 0, 'gold': 0, 'alternatives': 0}
        
        # Get equity allocation for risk profile
        equity_percent = self.params['equity_allocation'].get(risk_profile, 0.60)
        
        # Adjust for time horizon
        if time_horizon < 1:
            # Less than 1 year: Mostly liquid investments
            allocation['cash'] = 0.90
            allocation['debt'] = 0.10
        elif time_horizon < 3:
            # 1-3 years: Conservative allocation
            allocation['equity'] = min(0.30, equity_percent * 0.5)
            allocation['debt'] = 0.50
            allocation['cash'] = 0.20
        elif time_horizon < 5:
            # 3-5 years: Moderate allocation
            allocation['equity'] = min(0.50, equity_percent * 0.7)
            allocation['debt'] = 0.40
            allocation['cash'] = 0.05
            allocation['gold'] = 0.05
        elif time_horizon < 10:
            # 5-10 years: Full risk profile allocation
            allocation['equity'] = equity_percent
            allocation['debt'] = 0.90 - equity_percent
            allocation['gold'] = 0.05
            allocation['alternatives'] = 0.05
        else:
            # 10+ years: Aggressive allocation based on risk profile
            allocation['equity'] = min(0.75, equity_percent * 1.1)
            allocation['debt'] = 0.15
            allocation['gold'] = 0.05
            allocation['alternatives'] = 0.05
            
        return allocation
    
    def calculate_monthly_investment(self, goal_amount, years, expected_return):
        """
        Calculate required monthly investment to reach goal amount.
        
        Args:
            goal_amount: Target amount in currency units
            years: Number of years to goal
            expected_return: Annual expected return as decimal (e.g., 0.08 for 8%)
            
        Returns:
            Monthly investment amount required
        """
        # Convert annual rate to monthly
        monthly_rate = expected_return / 12
        # Number of months
        months = years * 12
        
        # Handle special case for immediate goals
        if months <= 1:
            return goal_amount
            
        # Formula: PMT = FV / ((1 + r)^n - 1) * (1 + r)
        denominator = ((1 + monthly_rate) ** months - 1) * (1 + monthly_rate)
        if denominator <= 0:
            return goal_amount / months  # Fallback to simple division
            
        monthly_investment = goal_amount / denominator
        return monthly_investment
    
    def calculate_lump_sum_investment(self, goal_amount, years, expected_return):
        """
        Calculate required lump sum investment to reach goal amount.
        
        Args:
            goal_amount: Target amount in currency units
            years: Number of years to goal
            expected_return: Annual expected return as decimal
            
        Returns:
            Lump sum amount required today
        """
        # For immediate goals
        if years <= 0:
            return goal_amount
            
        # Formula: PV = FV / (1 + r)^n
        lump_sum = goal_amount / ((1 + expected_return) ** years)
        return lump_sum
    
    def get_expected_return(self, allocation):
        """
        Calculate expected return based on asset allocation.
        
        Args:
            allocation: Dictionary with asset allocation percentages
            
        Returns:
            Expected annual return as decimal
        """
        expected_return = 0
        for asset, percent in allocation.items():
            if asset in self.params['expected_returns']:
                expected_return += percent * self.params['expected_returns'][asset]
                
        return expected_return
    
    def adjust_for_inflation(self, current_amount, years, inflation_rate=None):
        """
        Adjust a current amount for inflation to get future value.
        
        Args:
            current_amount: Amount in today's currency units
            years: Number of years in the future
            inflation_rate: Annual inflation rate as decimal (default: from params)
            
        Returns:
            Inflation-adjusted amount
        """
        if inflation_rate is None:
            inflation_rate = self.params['inflation_rate']
            
        # Formula: FV = PV * (1 + inflation_rate) ^ years
        future_value = current_amount * ((1 + inflation_rate) ** years)
        return future_value

    def estimate_tax_benefit(self, annual_investment, tax_bracket=None):
        """
        Estimate tax benefit from tax-saving investments.
        
        Args:
            annual_investment: Annual investment amount
            tax_bracket: Income tax bracket (decimal). If None, highest bracket used.
            
        Returns:
            Estimated annual tax benefit
        """
        if tax_bracket is None:
            tax_bracket = self.params['tax_rates']['income_tax']['default']
            
        # Cap at 1.5 lakhs for 80C investments
        eligible_amount = min(annual_investment, 150000)
        tax_benefit = eligible_amount * tax_bracket
        
        return tax_benefit
    
    def recommend_investment_instruments(self, allocation, monthly_amount, lump_sum=0,
                                         time_horizon=0, goal_type='general'):
        """
        Recommend specific investment instruments based on allocation.
        
        Args:
            allocation: Dictionary with asset allocation percentages
            monthly_amount: Monthly investment capacity
            lump_sum: Available lump sum amount
            time_horizon: Years to goal
            goal_type: Type of financial goal
            
        Returns:
            Dictionary with specific investment recommendations
        """
        recommendations = {
            'monthly': {},
            'lump_sum': {},
            'rationale': {}
        }
        
        # Handle monthly investments
        if monthly_amount > 0:
            # Divide based on allocation
            for asset, percent in allocation.items():
                if percent > 0:
                    asset_monthly = monthly_amount * percent
                    
                    if asset == 'equity':
                        if asset_monthly >= 500:  # Minimum SIP amount
                            if time_horizon > 10:
                                recommendations['monthly']['index_funds'] = asset_monthly * 0.7
                                recommendations['monthly']['mid_cap_funds'] = asset_monthly * 0.3
                                recommendations['rationale']['equity'] = "Long-term horizon suits index funds with some mid-cap exposure"
                            elif time_horizon > 5:
                                recommendations['monthly']['large_cap_funds'] = asset_monthly * 0.5
                                recommendations['monthly']['balanced_funds'] = asset_monthly * 0.5
                                recommendations['rationale']['equity'] = "Medium-term horizon with a mix of large-cap and balanced funds"
                            else:
                                recommendations['monthly']['balanced_funds'] = asset_monthly
                                recommendations['rationale']['equity'] = "Short horizon suggests conservative balanced funds"
                                
                    elif asset == 'debt':
                        if time_horizon > 5:
                            recommendations['monthly']['debt_funds'] = asset_monthly
                            recommendations['rationale']['debt'] = "Long-term debt allocation through debt funds"
                        else:
                            recommendations['monthly']['short_term_debt'] = asset_monthly * 0.7
                            recommendations['monthly']['rds'] = asset_monthly * 0.3
                            recommendations['rationale']['debt'] = "Short-term horizon with focus on liquidity"
                            
                    elif asset == 'cash':
                        recommendations['monthly']['liquid_funds'] = asset_monthly
                        recommendations['rationale']['cash'] = "Cash allocation for liquidity through liquid funds"
                        
                    elif asset == 'gold':
                        recommendations['monthly']['gold_etf'] = asset_monthly
                        recommendations['rationale']['gold'] = "Gold allocation via ETFs for diversification"
                        
                    elif asset == 'alternatives':
                        if time_horizon > 7:
                            recommendations['monthly']['alternative_funds'] = asset_monthly
                            recommendations['rationale']['alternatives'] = "Long-term allocation to alternatives for diversification"
        
        # Handle lump sum investments
        if lump_sum > 0:
            # Divide based on allocation
            for asset, percent in allocation.items():
                if percent > 0:
                    asset_lump = lump_sum * percent
                    
                    if asset == 'equity':
                        if time_horizon < 1:
                            # Avoid equity for very short term
                            recommendations['lump_sum']['arbitrage_funds'] = asset_lump
                            recommendations['rationale']['lump_equity'] = "Using arbitrage funds for very short-term equity exposure"
                        elif time_horizon < 3:
                            recommendations['lump_sum']['balanced_funds'] = asset_lump
                            recommendations['rationale']['lump_equity'] = "Conservative equity allocation for short term"
                        else:
                            # Consider STP for larger amounts
                            if asset_lump > 100000 and time_horizon > 5:
                                recommendations['lump_sum']['stp_from_liquid'] = asset_lump
                                recommendations['rationale']['lump_equity'] = "STP recommended for large amount to average market entry"
                            else:
                                recommendations['lump_sum']['index_funds'] = asset_lump * 0.5
                                recommendations['lump_sum']['large_cap_funds'] = asset_lump * 0.5
                                recommendations['rationale']['lump_equity'] = "Mix of index and large-cap for balanced approach"
                    
                    elif asset == 'debt':
                        if time_horizon < 1:
                            recommendations['lump_sum']['ultra_short_debt'] = asset_lump
                            recommendations['rationale']['lump_debt'] = "Ultra short-term debt for capital preservation"
                        elif time_horizon < 3:
                            recommendations['lump_sum']['short_term_debt'] = asset_lump
                            recommendations['rationale']['lump_debt'] = "Short-term debt funds for this horizon"
                        else:
                            # Tax efficiency for longer term
                            recommendations['lump_sum']['income_funds'] = asset_lump
                            recommendations['rationale']['lump_debt'] = "Income funds for tax-efficient debt exposure"
                    
                    elif asset == 'cash':
                        if time_horizon < 1:
                            recommendations['lump_sum']['sweep_fd'] = asset_lump
                            recommendations['rationale']['lump_cash'] = "Sweep FD for immediate liquidity with some returns"
                        else:
                            recommendations['lump_sum']['liquid_funds'] = asset_lump
                            recommendations['rationale']['lump_cash'] = "Liquid funds for cash allocation"
                    
                    elif asset == 'gold':
                        recommendations['lump_sum']['gold_etf'] = asset_lump
                        recommendations['rationale']['lump_gold'] = "Gold ETFs for gold allocation"
                    
                    elif asset == 'alternatives':
                        if time_horizon > 5:
                            recommendations['lump_sum']['alternative_funds'] = asset_lump
                            recommendations['rationale']['lump_alternatives'] = "Alternative funds for diversification"
        
        # Additional tax-saving recommendations if relevant
        if goal_type in ['retirement', 'education']:
            tax_saving = {}
            if monthly_amount * 12 > 50000:  # Meaningful tax-saving amount
                tax_saving['monthly'] = {
                    'nps': min(monthly_amount * 0.2, 4000),  # 20% or max 4000/month
                    'elss': min(monthly_amount * 0.1, 2000)  # 10% or max 2000/month
                }
                tax_saving['rationale'] = "Additional allocation to NPS for retirement tax benefits, and ELSS for tax-saving with liquidity after 3 years"
            
            if lump_sum > 100000:
                tax_saving['lump_sum'] = {
                    'ppf': min(lump_sum * 0.15, 150000),  # 15% or max 1.5 lakh
                    'elss': min(lump_sum * 0.1, 50000)  # 10% or max 50,000
                }
            
            recommendations['tax_saving'] = tax_saving
        
        return recommendations
    
    def generate_funding_strategy(self, goal_data, profile_data=None, apply_optimizations=True):
        """
        Generate a comprehensive funding strategy for a financial goal with optional
        optimization and constraint application.
        
        Args:
            goal_data: Dictionary with goal details including:
                - goal_type: Type of goal (e.g., retirement, education)
                - target_amount: Goal amount in currency units
                - time_horizon: Years to goal
                - risk_profile: Risk tolerance (conservative/moderate/aggressive)
                - current_savings: Amount already saved for this goal
                - monthly_contribution: Current monthly contribution
            profile_data: Optional user profile data for constraint application
            apply_optimizations: Whether to apply optimizations (default: True)
                
        Returns:
            Dictionary with comprehensive funding strategy details
        """
        # Extract goal information
        goal_type = goal_data.get('goal_type', 'general')
        target_amount = goal_data.get('target_amount', 0)
        time_horizon = goal_data.get('time_horizon', 0)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        
        # Handle case where goal is immediate
        if time_horizon <= 0:
            return {
                'goal_type': goal_type,
                'current_status': {
                    'target_amount': target_amount,
                    'current_savings': current_savings,
                    'gap': target_amount - current_savings,
                    'percent_funded': (current_savings / target_amount * 100) if target_amount > 0 else 0
                },
                'recommendation': {
                    'message': "This goal is immediate and should be funded from your current savings or emergency fund.",
                    'required_amount': target_amount,
                    'allocation': {'cash': 1.0},
                    'instruments': {'immediate': {'savings_account': target_amount}}
                }
            }
        
        # Adjust target for inflation if needed
        inflation_adjusted_target = self.adjust_for_inflation(
            target_amount, time_horizon
        )
        
        # Recommended asset allocation
        allocation = self.recommend_allocation(time_horizon, risk_profile)
        
        # Expected return based on allocation
        expected_return = self.get_expected_return(allocation)
        
        # Calculate how current savings will grow
        future_value_of_current = current_savings * ((1 + expected_return) ** time_horizon)
        
        # Calculate how regular contributions will add up
        future_value_of_monthly = 0
        if monthly_contribution > 0:
            # Use compound interest formula for periodic payments
            monthly_rate = expected_return / 12
            months = time_horizon * 12
            future_value_of_monthly = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        
        # Calculate gap
        total_projected = future_value_of_current + future_value_of_monthly
        gap = inflation_adjusted_target - total_projected
        
        # Calculate required additional monthly investment
        required_monthly = 0
        if gap > 0:
            required_monthly = self.calculate_monthly_investment(
                gap, time_horizon, expected_return
            )
        
        # Calculate lump sum alternative
        required_lump_sum = 0
        if gap > 0:
            required_lump_sum = self.calculate_lump_sum_investment(
                gap, time_horizon, expected_return
            )
        
        # Generate investment recommendations
        total_monthly = monthly_contribution + required_monthly
        investment_recs = self.recommend_investment_instruments(
            allocation, total_monthly, required_lump_sum, time_horizon, goal_type
        )
        
        # Estimate tax benefits if applicable
        annual_investment = total_monthly * 12
        tax_benefit = self.estimate_tax_benefit(annual_investment)
        
        # Compile the complete strategy
        strategy = {
            'goal_type': goal_type,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'inflation_adjusted_target': round(inflation_adjusted_target),
            'current_status': {
                'target_amount': target_amount,
                'inflation_adjusted_target': round(inflation_adjusted_target),
                'current_savings': current_savings,
                'monthly_contribution': monthly_contribution,
                'projected_future_value': round(total_projected),
                'gap': round(gap) if gap > 0 else 0,
                'percent_funded': round((total_projected / inflation_adjusted_target * 100), 1) if inflation_adjusted_target > 0 else 0
            },
            'recommendation': {
                'asset_allocation': allocation,
                'expected_annual_return': round(expected_return * 100, 2),
                'additional_monthly_required': round(required_monthly) if required_monthly > 0 else 0,
                'total_monthly_investment': round(total_monthly),
                'lump_sum_alternative': round(required_lump_sum) if required_lump_sum > 0 else 0,
                'investment_instruments': investment_recs,
                'estimated_annual_tax_benefit': round(tax_benefit) if tax_benefit > 0 else 0
            }
        }
        
        # Add specific advice based on goal type
        if goal_type == 'retirement':
            strategy['specific_advice'] = {
                'nps_allocation': min(annual_investment * 0.2, 50000),
                'tax_saving_opportunities': ['NPS (additional tax benefit under 80CCD(1B))'],
                'considerations': [
                    'Increase equity allocation in early years',
                    'Consider annuity options for regular income post-retirement',
                    'Review and increase contributions with income growth'
                ]
            }
            
        elif goal_type in ('education', 'higher education'):
            strategy['specific_advice'] = {
                'sukanya_samriddhi': 'Consider if for girl child education' if time_horizon > 10 else None,
                'considerations': [
                    'Research scholarship opportunities',
                    'Consider education loans as supplementary option',
                    'Factor in additional costs beyond tuition'
                ]
            }
            
        elif goal_type in ('home', 'home purchase', 'down payment'):
            strategy['specific_advice'] = {
                'recommended_down_payment': round(inflation_adjusted_target * 0.2),
                'tax_benefits': 'Interest deduction up to ₹2L and principal repayment under 80C',
                'considerations': [
                    'Check eligibility for schemes like PMAY',
                    'Compare rent vs. buy scenarios',
                    'Factor in additional costs (registration, stamp duty, etc.)'
                ]
            }
        
        # Apply optimizations if requested and profile data is available
        if apply_optimizations and profile_data:
            strategy = self.optimize_strategy(strategy, profile_data)
            
            # Apply feasibility assessment and constraints
            strategy = self.apply_constraints_to_strategy(strategy, profile_data)
            
        return strategy
        
    def optimize_strategy(self, strategy, profile_data):
        """
        Apply tax and timing optimizations to a single strategy
        
        Args:
            strategy: The funding strategy to optimize
            profile_data: User profile data for context
            
        Returns:
            Optimized strategy
        """
        # Initialize optimizer if needed
        self._initialize_optimizer()
        
        # Apply tax efficiency optimizations
        optimized_strategy, tax_summary = self.optimizer.optimize_tax_efficiency([strategy], profile_data)
        
        # If optimizer returned a list with one strategy, extract it
        if isinstance(optimized_strategy, list) and len(optimized_strategy) == 1:
            optimized_strategy = optimized_strategy[0]
        
        # Apply contribution timing optimizations if there's a monthly investment
        if optimized_strategy.get('recommendation', {}).get('total_monthly_investment', 0) > 0:
            optimized_strategy = self.optimizer.optimize_contribution_timing(optimized_strategy, profile_data)
            
        # Add tax efficiency summary to strategy
        if 'recommendation' in optimized_strategy and tax_summary:
            optimized_strategy['recommendation']['tax_efficiency_summary'] = tax_summary
            
        return optimized_strategy
        
    def apply_constraints_to_strategy(self, strategy, profile_data):
        """
        Apply feasibility assessment and constraints to a single strategy
        
        Args:
            strategy: The funding strategy to assess
            profile_data: User profile data for constraint application
            
        Returns:
            Strategy with feasibility assessment
        """
        # Initialize constraints if needed
        self._initialize_constraints()
        
        # Assess feasibility
        assessed_strategies = self.constraints.detect_unrealistic_targets([strategy], profile_data)
        
        # If returned as a list with one strategy, extract it
        if isinstance(assessed_strategies, list) and len(assessed_strategies) == 1:
            assessed_strategy = assessed_strategies[0]
        else:
            assessed_strategy = strategy
            
        return assessed_strategy
        
    def optimize_portfolio(self, strategies: List[Dict[str, Any]], profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Optimize a portfolio of strategies holistically, considering cross-goal impacts
        
        Args:
            strategies: List of funding strategies for different goals
            profile_data: User profile data for constraint application
            
        Returns:
            List of optimized strategies with budget constraints applied
        """
        if not strategies or not profile_data:
            return strategies
            
        # Initialize utility classes if needed
        self._initialize_constraints()
        self._initialize_optimizer()
        self._initialize_compound_strategy()
        
        # Step 1: Apply budget constraints across all strategies
        constrained_strategies = self.apply_constraints(strategies, profile_data)
        
        # Step 2: Find and create compound strategies where applicable
        candidate_compounds = self.generate_compound_strategies(constrained_strategies)
        
        # Step 3: Apply tax optimizations across the portfolio
        optimized_strategies, tax_summary = self.optimizer.optimize_tax_efficiency(constrained_strategies, profile_data)
        
        # Step 4: Balance short and long-term allocations
        balanced_strategies = self.optimizer.balance_short_long_term(optimized_strategies)
        
        # Step 5: Add portfolio-level recommendations
        portfolio_recommendations = self._generate_portfolio_recommendations(
            balanced_strategies, 
            profile_data,
            tax_summary,
            candidate_compounds
        )
        
        # Add portfolio recommendations to each strategy
        for strategy in balanced_strategies:
            if 'recommendation' in strategy:
                strategy['recommendation']['portfolio_context'] = {
                    'total_goals': len(balanced_strategies),
                    'portfolio_recommendations': portfolio_recommendations,
                }
        
        return balanced_strategies
    
    def apply_constraints(self, strategies: List[Dict[str, Any]], profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply budget constraints across all goals in the portfolio
        
        Args:
            strategies: List of funding strategies for different goals
            profile_data: User profile data for constraint application
            
        Returns:
            List of strategies with budget constraints applied
        """
        # Initialize constraints if needed
        self._initialize_constraints()
        
        # Apply budget constraints
        constrained_strategies = self.constraints.apply_budget_constraints(strategies, profile_data)
        
        # Detect unrealistic targets
        assessed_strategies = self.constraints.detect_unrealistic_targets(constrained_strategies, profile_data)
        
        return assessed_strategies
    
    def generate_compound_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify and create compound strategies for compatible goals
        
        Args:
            strategies: List of funding strategies to analyze
            
        Returns:
            List of compound strategies
        """
        if not strategies or len(strategies) < 2:
            return []
            
        # Initialize compound strategy generator if needed
        self._initialize_compound_strategy()
        
        # Get combination criteria
        time_threshold = self.params['portfolio_optimization']['candidate_combination_criteria']['time_horizon_similar_threshold']
        candidate_combinations = self.params['portfolio_optimization']['candidate_combination_criteria']['goal_type_combinations']
        
        compound_strategies = []
        processed_indices = set()
        
        # Look for compatible goals to combine
        for i in range(len(strategies)):
            if i in processed_indices:
                continue
                
            strategy1 = strategies[i]
            goal_type1 = strategy1.get('goal_type', '').lower()
            time_horizon1 = strategy1.get('time_horizon', 0)
            
            for j in range(i+1, len(strategies)):
                if j in processed_indices:
                    continue
                    
                strategy2 = strategies[j]
                goal_type2 = strategy2.get('goal_type', '').lower()
                time_horizon2 = strategy2.get('time_horizon', 0)
                
                # Check if goals are candidates for combination
                is_time_compatible = abs(time_horizon1 - time_horizon2) <= time_threshold
                is_type_compatible = any([goal_type1 in combo and goal_type2 in combo for combo in candidate_combinations])
                
                if is_time_compatible or is_type_compatible:
                    # Combine these strategies
                    compound = self.compound_strategy.combine_strategies([strategy1, strategy2])
                    compound_strategies.append(compound)
                    
                    # Mark these as processed
                    processed_indices.add(i)
                    processed_indices.add(j)
                    
                    # Log the combination
                    logger.info(f"Created compound strategy for {goal_type1} and {goal_type2} goals")
                    break
        
        return compound_strategies
    
    def analyze_portfolio_scenarios(self, strategies: List[Dict[str, Any]], profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run scenario analysis across the entire portfolio
        
        Args:
            strategies: List of funding strategies to analyze
            profile_data: User profile data for analysis context
            
        Returns:
            Dictionary with portfolio scenario analysis results
        """
        if not strategies:
            return {"error": "No strategies provided for analysis"}
            
        # Initialize compound strategy for scenario analysis
        self._initialize_compound_strategy()
        
        # Define common scenarios to test across the portfolio
        common_scenarios = [
            {"name": "Baseline", "market_condition": "baseline", "contribution_pattern": "steady"},
            {"name": "Optimistic Market", "market_condition": "optimistic", "contribution_pattern": "steady"},
            {"name": "Pessimistic Market", "market_condition": "pessimistic", "contribution_pattern": "steady"},
            {"name": "Income Growth", "market_condition": "baseline", "contribution_pattern": "increasing", 
             "monthly_increase_factor": 0.08},  # 8% annual income growth
            {"name": "Extended Timeline", "market_condition": "baseline", "contribution_pattern": "steady", 
             "time_horizon_extension": 2}
        ]
        
        # Analyze each strategy
        analyzed_strategies = []
        for strategy in strategies:
            analyzed = self.compound_strategy.analyze_scenarios(strategy, common_scenarios)
            analyzed_strategies.append(analyzed)
            
        # Compile portfolio-level analysis
        goal_achievement_rates = []
        success_rates = []
        
        for strategy in analyzed_strategies:
            scenarios = strategy.get('scenario_analysis', {}).get('scenarios', [])
            if scenarios:
                # Calculate success rate for this goal
                success_count = sum(1 for s in scenarios if s.get('calculations', {}).get('goal_achieved', False))
                success_rate = success_count / len(scenarios) if scenarios else 0
                success_rates.append(success_rate)
                
                # Get baseline achievement rate
                baseline_scenario = next((s for s in scenarios if s.get('name') == 'Baseline'), None)
                if baseline_scenario:
                    achievement_rate = baseline_scenario.get('calculations', {}).get('goal_achievement_ratio', 0)
                    goal_achievement_rates.append(achievement_rate)
        
        # Calculate portfolio-wide metrics
        portfolio_analysis = {
            "overall_success_rate": sum(success_rates) / len(success_rates) if success_rates else 0,
            "average_goal_achievement": sum(goal_achievement_rates) / len(goal_achievement_rates) if goal_achievement_rates else 0,
            "most_sensitive_scenario": self._identify_most_sensitive_scenario(analyzed_strategies),
            "portfolio_recommendations": self._generate_scenario_recommendations(analyzed_strategies, profile_data)
        }
        
        return portfolio_analysis
    
    def _identify_most_sensitive_scenario(self, analyzed_strategies):
        """Identify the scenario that has the biggest impact across goals"""
        scenario_impacts = {}
        
        for strategy in analyzed_strategies:
            scenarios = strategy.get('scenario_analysis', {}).get('scenarios', [])
            baseline = next((s for s in scenarios if s['name'] == 'Baseline'), None)
            
            if not baseline:
                continue
                
            baseline_achievement = baseline.get('calculations', {}).get('goal_achievement_ratio', 0)
            
            for scenario in scenarios:
                if scenario['name'] == 'Baseline':
                    continue
                    
                # Calculate impact relative to baseline
                achievement = scenario.get('calculations', {}).get('goal_achievement_ratio', 0)
                impact = achievement - baseline_achievement
                
                # Track impact by scenario name
                scenario_name = scenario['name']
                if scenario_name not in scenario_impacts:
                    scenario_impacts[scenario_name] = []
                    
                scenario_impacts[scenario_name].append(impact)
        
        # Calculate average impact for each scenario
        avg_impacts = {}
        for scenario, impacts in scenario_impacts.items():
            if impacts:
                avg_impacts[scenario] = sum(impacts) / len(impacts)
        
        # Find the scenario with the largest absolute impact
        if avg_impacts:
            most_sensitive = max(avg_impacts.items(), key=lambda x: abs(x[1]))
            return {
                "scenario": most_sensitive[0],
                "average_impact": round(most_sensitive[1] * 100, 2),  # Convert to percentage
                "direction": "positive" if most_sensitive[1] > 0 else "negative"
            }
        
        return None
    
    def _generate_scenario_recommendations(self, analyzed_strategies, profile_data):
        """Generate portfolio-level recommendations based on scenario analysis"""
        recommendations = []
        
        # Calculate overall metrics
        success_rates = []
        for strategy in analyzed_strategies:
            comparison = strategy.get('scenario_analysis', {}).get('comparison', {})
            success_percent = comparison.get('percentage_of_successful_scenarios', 0)
            success_rates.append(success_percent)
        
        overall_success = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Generate overall recommendations
        if overall_success < 50:
            recommendations.append(
                "Your overall portfolio has a low probability of success. Consider extending timelines, increasing contributions, or adjusting goal targets."
            )
        elif overall_success < 75:
            recommendations.append(
                "Your portfolio has a moderate chance of success. Focus on the highest priority goals and consider more aggressive investment strategies for long-term goals."
            )
        else:
            recommendations.append(
                "Your portfolio has a strong probability of success. Continue regular reviews and rebalancing to stay on track."
            )
            
        # Check for specific improvement opportunities
        optimistic_improvements = []
        income_growth_improvements = []
        extension_improvements = []
        
        for strategy in analyzed_strategies:
            scenarios = strategy.get('scenario_analysis', {}).get('scenarios', [])
            baseline = next((s for s in scenarios if s['name'] == 'Baseline'), None)
            
            if not baseline or not baseline.get('calculations', {}).get('goal_achieved', False):
                # Goal is not achieved in baseline scenario, look for improvements
                optimistic = next((s for s in scenarios if s['name'] == 'Optimistic Market'), None)
                income_growth = next((s for s in scenarios if s['name'] == 'Income Growth'), None)
                extended = next((s for s in scenarios if s['name'] == 'Extended Timeline'), None)
                
                goal_type = strategy.get('goal_type', 'unknown')
                
                if optimistic and optimistic.get('calculations', {}).get('goal_achieved', False):
                    optimistic_improvements.append(goal_type)
                    
                if income_growth and income_growth.get('calculations', {}).get('goal_achieved', False):
                    income_growth_improvements.append(goal_type)
                    
                if extended and extended.get('calculations', {}).get('goal_achieved', False):
                    extension_improvements.append(goal_type)
        
        # Add specific recommendations based on patterns
        if income_growth_improvements:
            recommendations.append(
                f"Increasing your contributions over time significantly improves outcomes for your {', '.join(income_growth_improvements)} goals."
            )
            
        if extension_improvements:
            recommendations.append(
                f"Extending your timeline by 2+ years dramatically improves feasibility for your {', '.join(extension_improvements)} goals."
            )
            
        if optimistic_improvements and not income_growth_improvements and not extension_improvements:
            recommendations.append(
                f"Your {', '.join(optimistic_improvements)} goals are highly dependent on market performance. Consider adding a buffer to your savings targets."
            )
        
        return recommendations
                
    def _generate_portfolio_recommendations(self, strategies, profile_data, tax_summary, compound_strategies):
        """Generate portfolio-level recommendations based on optimized strategies"""
        recommendations = []
        
        # Add tax efficiency recommendations
        if tax_summary:
            remaining_80c = tax_summary.get('remaining_80c', 0)
            if remaining_80c > 0:
                recommendations.append(
                    f"You have ₹{remaining_80c:,} of unused Section 80C deduction limit. Consider additional tax-saving investments."
                )
                
            remaining_80ccd = tax_summary.get('remaining_80ccd', 0)
            if remaining_80ccd > 0:
                recommendations.append(
                    f"You have ₹{remaining_80ccd:,} of unused NPS tax benefit under Section 80CCD(1B). Consider increasing your NPS contributions."
                )
        
        # Add compound strategy recommendations
        if compound_strategies:
            recommendations.append(
                f"Consider combining your {len(compound_strategies)} identified goal pairs with similar timeframes to simplify portfolio management."
            )
        
        # Check for common patterns that need attention
        high_pressure_goals = []
        infeasible_goals = []
        
        for strategy in strategies:
            feasibility = strategy.get('feasibility_assessment', {})
            if feasibility.get('pressure_level') == 'high':
                high_pressure_goals.append(strategy.get('goal_type', 'unknown'))
            elif not feasibility.get('is_feasible', True):
                infeasible_goals.append(strategy.get('goal_type', 'unknown'))
        
        # Add recommendations based on patterns
        if infeasible_goals:
            recommendations.append(
                f"Your {', '.join(infeasible_goals)} goals appear to be infeasible with current income. Consider adjusting timelines or target amounts."
            )
            
        if high_pressure_goals:
            recommendations.append(
                f"Your {', '.join(high_pressure_goals)} goals are putting significant pressure on your budget. Consider prioritizing or extending timelines."
            )
            
        # Return compiled recommendations
        return recommendations


class FundingConstraints:
    """
    Class for applying realistic constraints to funding strategies based on Indian budgeting patterns.
    Handles budget limitations, goal prioritization, and target feasibility assessment.
    """
    
    def __init__(self):
        """Initialize with financial parameter service for configuration retrieval"""
        self.param_service = get_financial_parameter_service()
        
        # Default parameters
        self.params = {
            "budget_limits": {
                "max_income_percent": 0.5,  # Maximum 50% of income for all SIPs
                "emergency_fund_priority": 0.8,  # Priority factor for emergency fund
                "debt_repayment_priority": 0.7,  # Priority factor for debt repayment
                "minimum_sip_amount": 500,  # Minimum SIP amount for most mutual funds
                "discretionary_cap": 0.2,   # Cap on discretionary goals as % of income
                "retirement_min_percent": 0.10,  # Minimum 10% of income toward retirement
                "retirement_ideal_percent": 0.15  # Ideal 15% of income toward retirement
            },
            "feasibility_thresholds": {
                "income_to_goal_ratio_min": 0.02,  # Goal requires at least 2% of monthly income
                "max_contribution_percent": 0.3,   # Max 30% of income to any single goal
                "high_pressure_threshold": 0.6,    # Ratio of required vs available is high pressure
                "critical_pressure_threshold": 0.8,  # Ratio of required vs available is critical
                "retirement_corpus_income_ratio": 25  # Retirement corpus should be 25x annual expenses
            },
            "category_inflation_rates": {
                "education": 0.1,           # 10% for education expenses
                "healthcare": 0.08,         # 8% for healthcare
                "housing": 0.07,            # 7% for housing
                "general": 0.06,            # 6% general inflation
                "discretionary": 0.04,      # 4% for discretionary expenses
                "retirement_healthcare": 0.10  # 10% healthcare inflation for retirement planning
            },
            "life_expectancy": {
                "base": 80,                 # Base life expectancy
                "adjustment_factors": {
                    "family_history": 2,    # Add 2 years for good family history
                    "health_conditions": -3,  # Subtract 3 years for health conditions
                    "lifestyle": {
                        "active": 2,        # Add 2 years for active lifestyle
                        "sedentary": -2     # Subtract 2 years for sedentary lifestyle
                    }
                }
            }
        }
        
        # Override defaults with service parameters
        self._load_constraint_parameters()
    
    def _load_constraint_parameters(self):
        """Load constraint parameters from financial parameter service if available"""
        if self.param_service:
            try:
                # Load budget limit parameters
                budget_limits = self.param_service.get_parameter('budget_limits')
                if budget_limits:
                    self.params['budget_limits'].update(budget_limits)
                
                # Load feasibility threshold parameters
                feasibility = self.param_service.get_parameter('feasibility_thresholds')
                if feasibility:
                    self.params['feasibility_thresholds'].update(feasibility)
                
                # Load category inflation rates
                inflation_rates = self.param_service.get_parameter('category_inflation_rates')
                if inflation_rates:
                    self.params['category_inflation_rates'].update(inflation_rates)
                    
            except Exception as e:
                logger.error(f"Error loading constraint parameters: {e}")
                # Continue with default parameters
    
    def apply_budget_constraints(self, strategies: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply budget constraints to ensure total SIPs don't exceed financial capacity.
        
        Args:
            strategies: List of funding strategies for different goals
            profile: User profile with income and expense information
            
        Returns:
            List of modified strategies with realistic contribution amounts
        """
        if not strategies or not profile:
            logger.warning("Cannot apply budget constraints: Missing strategies or profile data")
            return strategies
        
        # Extract relevant profile information
        monthly_income = profile.get('monthly_income', 0)
        if not monthly_income:
            logger.warning("Missing monthly income data, cannot apply constraints")
            return strategies
        
        # Calculate monthly expenses and obligations
        monthly_expenses = profile.get('monthly_expenses', 0)
        loan_emis = profile.get('loan_emis', 0)
        fixed_obligations = profile.get('fixed_obligations', 0)
        
        # Calculate disposable income
        total_obligations = monthly_expenses + loan_emis + fixed_obligations
        disposable_income = max(0, monthly_income - total_obligations)
        
        # Maximum percentage of disposable income for investments
        max_investment_percent = self.params['budget_limits']['max_income_percent']
        
        # Calculate available budget for SIPs
        available_budget = disposable_income * max_investment_percent
        
        # Calculate current total monthly requirement across all strategies
        total_required = sum(
            strategy.get('recommendation', {}).get('total_monthly_investment', 0)
            for strategy in strategies
        )
        
        # If required amount exceeds available budget, allocate by priority
        if total_required > available_budget:
            logger.info(f"Required investment ({total_required}) exceeds available budget ({available_budget}). Adjusting allocations.")
            adjusted_strategies = self.allocate_by_priority(strategies, available_budget)
            
            # Log adjustment results
            total_adjusted = sum(
                strategy.get('recommendation', {}).get('total_monthly_investment', 0)
                for strategy in adjusted_strategies
            )
            logger.info(f"Adjusted total investment: {total_adjusted} (Budget: {available_budget})")
            
            return adjusted_strategies
        
        # If within budget, no adjustment needed
        logger.info(f"Total investment ({total_required}) is within budget ({available_budget})")
        return strategies
    
    def allocate_by_priority(self, strategies: List[Dict[str, Any]], available_budget: float) -> List[Dict[str, Any]]:
        """
        Distribute limited funds according to goal priorities.
        
        Args:
            strategies: List of funding strategies for different goals
            available_budget: Maximum available monthly budget for all SIPs
            
        Returns:
            List of strategies with adjusted contribution amounts
        """
        if not strategies or available_budget <= 0:
            return strategies
        
        # Make a copy of strategies to avoid modifying the original
        adjusted_strategies = [dict(strategy) for strategy in strategies]
        
        # Calculate priority scores for each strategy
        prioritized_strategies = []
        min_sip = self.params['budget_limits']['minimum_sip_amount']
        
        # Assign priority scores based on goal type and timeline
        for idx, strategy in enumerate(adjusted_strategies):
            goal_type = strategy.get('goal_type', '').lower()
            time_horizon = strategy.get('time_horizon', 10)
            current_monthly = strategy.get('recommendation', {}).get('total_monthly_investment', 0)
            
            # Skip goals with no required investment
            if current_monthly <= 0:
                continue
                
            # Base priority score
            priority = 0.5
            
            # Adjust priority based on goal type
            if goal_type == 'emergency fund':
                priority = self.params['budget_limits']['emergency_fund_priority']
            elif goal_type in ('debt', 'debt repayment'):
                priority = self.params['budget_limits']['debt_repayment_priority']
            elif goal_type == 'retirement':
                priority = 0.6
            elif goal_type in ('education', 'higher education'):
                priority = 0.6 if time_horizon < 5 else 0.5
            elif goal_type in ('home', 'home purchase'):
                priority = 0.5
            elif goal_type in ('vacation', 'travel', 'vehicle'):
                priority = 0.3
                
            # Adjust priority based on time horizon
            if time_horizon < 2:
                priority += 0.2  # Increase priority for short-term goals
            elif time_horizon > 15:
                priority -= 0.1  # Decrease priority for very long-term goals
                
            prioritized_strategies.append({
                'index': idx,
                'priority': priority,
                'current_amount': current_monthly,
                'minimum_amount': min(current_monthly, min_sip) if current_monthly > 0 else 0
            })
        
        # Sort strategies by priority (highest first)
        prioritized_strategies.sort(key=lambda x: x['priority'], reverse=True)
        
        # First, allocate minimum SIP amounts for all goals to maintain them
        remaining_budget = available_budget
        for strategy in prioritized_strategies:
            min_amount = strategy['minimum_amount']
            if min_amount > 0 and remaining_budget >= min_amount:
                remaining_budget -= min_amount
            else:
                # If we can't even meet minimum SIPs, focus only on highest priority goals
                break
                
        # Then, allocate remaining budget proportionally based on priority
        if remaining_budget > 0 and prioritized_strategies:
            # Calculate total priority weight
            total_priority = sum(s['priority'] for s in prioritized_strategies)
            
            # Allocate remaining budget proportionally
            for strategy in prioritized_strategies:
                idx = strategy['index']
                min_amount = strategy['minimum_amount']
                priority_share = strategy['priority'] / total_priority if total_priority > 0 else 0
                
                # Calculate proportional allocation of remaining budget
                proportional_amount = remaining_budget * priority_share
                
                # Total allocation is minimum amount plus proportional share
                total_allocation = min_amount + proportional_amount
                
                # Cap at original requested amount
                original_amount = strategy['current_amount']
                final_amount = min(total_allocation, original_amount)
                
                # Update the strategy with adjusted amount
                if 'recommendation' in adjusted_strategies[idx]:
                    adjusted_strategies[idx]['recommendation']['total_monthly_investment'] = round(final_amount)
                    
                    # Also update additional monthly required if present
                    if 'additional_monthly_required' in adjusted_strategies[idx]['recommendation']:
                        current_contribution = adjusted_strategies[idx].get('current_status', {}).get('monthly_contribution', 0)
                        adjusted_strategies[idx]['recommendation']['additional_monthly_required'] = round(max(0, final_amount - current_contribution))
        
        # Add adjustment message
        for strategy in adjusted_strategies:
            if 'recommendation' in strategy:
                if 'notes' not in strategy['recommendation']:
                    strategy['recommendation']['notes'] = []
                strategy['recommendation']['notes'].append("Monthly investment amount adjusted to fit within available budget.")
        
        return adjusted_strategies
    
    def detect_unrealistic_targets(self, strategies: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify goals with unrealistic targets based on income and timeline.
        
        Args:
            strategies: List of funding strategies for different goals
            profile: User profile with income information
            
        Returns:
            List of strategies with added feasibility assessment
        """
        if not strategies or not profile:
            return strategies
        
        # Extract relevant profile information
        monthly_income = profile.get('monthly_income', 0)
        if not monthly_income:
            logger.warning("Missing monthly income data, cannot assess target feasibility")
            return strategies
        
        # Make a copy of strategies to avoid modifying the original
        assessed_strategies = [dict(strategy) for strategy in strategies]
        
        # Thresholds from parameters
        income_to_goal_ratio_min = self.params['feasibility_thresholds']['income_to_goal_ratio_min']
        max_contribution_percent = self.params['feasibility_thresholds']['max_contribution_percent']
        high_pressure = self.params['feasibility_thresholds']['high_pressure_threshold']
        critical_pressure = self.params['feasibility_thresholds']['critical_pressure_threshold']
        
        # Assess each strategy
        for strategy in assessed_strategies:
            # Skip if no recommendation
            if 'recommendation' not in strategy:
                continue
                
            goal_type = strategy.get('goal_type', '').lower()
            time_horizon = strategy.get('time_horizon', 10)
            total_monthly = strategy['recommendation'].get('total_monthly_investment', 0)
            
            # Skip if no investment required
            if total_monthly <= 0:
                continue
                
            # Calculate contribution as percentage of income
            contribution_percent = total_monthly / monthly_income if monthly_income > 0 else 1
            
            # Initialize feasibility assessment
            feasibility = {
                'is_feasible': True,
                'pressure_level': 'normal',
                'recommendations': []
            }
            
            # Check contribution against maximum threshold
            if contribution_percent > max_contribution_percent:
                feasibility['is_feasible'] = False
                feasibility['pressure_level'] = 'critical'
                feasibility['recommendations'].append(
                    f"Goal requires {round(contribution_percent * 100)}% of income, which exceeds recommended maximum of {round(max_contribution_percent * 100)}%."
                )
                
                # Add specific recommendations
                if time_horizon < 5:
                    feasibility['recommendations'].append("Consider extending the timeline to reduce monthly contribution.")
                else:
                    feasibility['recommendations'].append("Consider reducing the target amount or exploring alternative funding sources.")
            
            # Check if contribution is very small relative to income
            elif contribution_percent < income_to_goal_ratio_min:
                feasibility['pressure_level'] = 'low'
                feasibility['recommendations'].append(
                    f"Goal requires only {round(contribution_percent * 100)}% of income, which is very manageable."
                )
            
            # Check moderate pressure levels
            elif contribution_percent > high_pressure:
                feasibility['pressure_level'] = 'high'
                feasibility['recommendations'].append(
                    f"Goal requires {round(contribution_percent * 100)}% of income, which may be challenging to sustain."
                )
                
                # Specific recommendations based on goal type
                if goal_type in ('vacation', 'travel', 'vehicle'):
                    feasibility['recommendations'].append("Consider extending the timeline for this discretionary goal.")
                elif goal_type in ('home', 'home purchase'):
                    feasibility['recommendations'].append("Consider a smaller down payment or a more affordable property.")
            
            # Add appropriate inflation consideration
            category_inflation = self.params['category_inflation_rates'].get(
                goal_type if goal_type in self.params['category_inflation_rates'] else 'general'
            )
            
            # Add inflation note for long-term goals
            if time_horizon > 5 and category_inflation > self.params['category_inflation_rates']['general']:
                feasibility['recommendations'].append(
                    f"Note that {goal_type} expenses typically grow at {round(category_inflation * 100)}% annually, which is higher than general inflation."
                )
            
            # Add feasibility assessment to strategy
            strategy['feasibility_assessment'] = feasibility
        
        return assessed_strategies
        
    def assess_retirement_budget_feasibility(self, strategy: Dict[str, Any], profile: Dict[str, Any], 
                                           current_age: int, retirement_age: int) -> Dict[str, Any]:
        """
        Assess feasibility of retirement strategy with Indian-specific considerations.
        
        Args:
            strategy: Retirement funding strategy to assess
            profile: User profile with income and expense information
            current_age: Current age of the investor
            retirement_age: Expected retirement age
            
        Returns:
            Dictionary with retirement-specific feasibility assessment
        """
        if not strategy or not profile or strategy.get('goal_type', '').lower() != 'retirement':
            return None
            
        # Extract relevant profile information
        monthly_income = profile.get('monthly_income', 0)
        annual_income = monthly_income * 12 if monthly_income else profile.get('annual_income', 0)
        if not monthly_income and not annual_income:
            logger.warning("Missing income data, cannot assess retirement feasibility")
            return None
            
        if not monthly_income:
            monthly_income = annual_income / 12
            
        # Extract retirement-specific information
        monthly_expenses = strategy.get('monthly_expenses', profile.get('monthly_expenses', monthly_income * 0.7))
        annual_expenses = monthly_expenses * 12
        
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # Extract strategy recommendations
        recommendation = strategy.get('recommendation', {})
        total_monthly_contribution = recommendation.get('total_monthly_investment', 0)
        
        # Calculate as percentage of income
        contribution_percent = total_monthly_contribution / monthly_income if monthly_income > 0 else 0
        
        # Get retirement-specific thresholds
        retirement_min_percent = self.params['budget_limits'].get('retirement_min_percent', 0.10)
        retirement_ideal_percent = self.params['budget_limits'].get('retirement_ideal_percent', 0.15)
        corpus_income_ratio = self.params['feasibility_thresholds'].get('retirement_corpus_income_ratio', 25)
        
        # Initialize feasibility assessment
        feasibility = {
            'is_feasible': True,
            'contribution_assessment': {
                'current_percent_of_income': round(contribution_percent * 100, 1),
                'min_recommended_percent': round(retirement_min_percent * 100),
                'ideal_percent': round(retirement_ideal_percent * 100),
                'status': 'below_min' if contribution_percent < retirement_min_percent else 
                         ('optimal' if retirement_min_percent <= contribution_percent <= retirement_ideal_percent * 1.2 else 'above_ideal')
            },
            'corpus_assessment': {},
            'age_assessment': {},
            'recommendations': []
        }
        
        # Assess contribution adequacy
        if contribution_percent < retirement_min_percent:
            feasibility['recommendations'].append(
                f"Current contribution ({round(contribution_percent * 100, 1)}% of income) is below the minimum recommended level of {round(retirement_min_percent * 100)}%. Consider increasing your retirement savings."
            )
        elif contribution_percent > retirement_ideal_percent * 1.5:
            # If contributing significantly more than ideal
            feasibility['recommendations'].append(
                f"Current contribution ({round(contribution_percent * 100, 1)}% of income) is significantly above the ideal level of {round(retirement_ideal_percent * 100)}%. This may impact short-term financial goals."
            )
        
        # Assess target corpus adequacy
        target_corpus = strategy.get('inflation_adjusted_target', 0)
        corpus_years_coverage = target_corpus / annual_expenses if annual_expenses > 0 else 0
        
        feasibility['corpus_assessment'] = {
            'target_corpus': round(target_corpus),
            'annual_expenses': round(annual_expenses),
            'years_coverage': round(corpus_years_coverage, 1),
            'recommended_years': corpus_income_ratio,
            'status': 'insufficient' if corpus_years_coverage < corpus_income_ratio * 0.8 else 
                     ('optimal' if corpus_income_ratio * 0.8 <= corpus_years_coverage <= corpus_income_ratio * 1.2 else 'more_than_needed')
        }
        
        # Add corpus recommendations
        if corpus_years_coverage < corpus_income_ratio * 0.8:
            shortfall_percent = (1 - (corpus_years_coverage / corpus_income_ratio)) * 100
            feasibility['recommendations'].append(
                f"Target corpus provides only {round(corpus_years_coverage, 1)} years of expenses, which is {round(shortfall_percent)}% short of the recommended {corpus_income_ratio} years."
            )
            
            # Add specific remedial advice
            if years_to_retirement > 10:
                feasibility['recommendations'].append(
                    "Consider increasing monthly contributions or adopting a more growth-oriented investment strategy to bridge this gap."
                )
            elif years_to_retirement > 5:
                feasibility['recommendations'].append(
                    "With limited time remaining, consider a combination of increased contributions, postponing retirement, and reducing post-retirement expenses."
                )
            else:
                feasibility['recommendations'].append(
                    "With very limited time remaining, consider postponing retirement, exploring partial retirement options, or planning for additional income sources post-retirement."
                )
                
        elif corpus_years_coverage > corpus_income_ratio * 1.5:
            # If significantly more corpus than needed
            feasibility['recommendations'].append(
                f"Target corpus provides {round(corpus_years_coverage, 1)} years of expenses, which is significantly more than the recommended {corpus_income_ratio} years. Consider balancing with other financial goals."
            )
        
        # Assess retirement age appropriateness
        early_retirement = retirement_age < 58
        late_retirement = retirement_age > 65
        retirement_duration = 85 - retirement_age  # Assuming life expectancy of 85
        
        feasibility['age_assessment'] = {
            'current_age': current_age,
            'retirement_age': retirement_age,
            'years_to_retirement': years_to_retirement,
            'estimated_retirement_duration': retirement_duration,
            'status': 'early' if early_retirement else ('late' if late_retirement else 'normal')
        }
        
        # Add age-related recommendations
        if early_retirement:
            feasibility['recommendations'].append(
                f"Planning to retire at {retirement_age} is earlier than the typical retirement age. This requires a larger corpus to cover a longer retirement period of {retirement_duration} years."
            )
            
            if contribution_percent < retirement_ideal_percent * 1.2:
                feasibility['recommendations'].append(
                    "For early retirement, consider significantly increasing your savings rate to at least 20-25% of income."
                )
        
        elif late_retirement:
            feasibility['recommendations'].append(
                f"Planning to retire at {retirement_age} is later than typical. This provides more time to build corpus but results in a shorter retirement duration of {retirement_duration} years."
            )
            
            if corpus_years_coverage > corpus_income_ratio:
                feasibility['recommendations'].append(
                    "With a later retirement age and adequate corpus, you may have flexibility to retire earlier if desired."
                )
        
        # Overall feasibility assessment
        insufficient_contribution = contribution_percent < retirement_min_percent * 0.8
        insufficient_corpus = corpus_years_coverage < corpus_income_ratio * 0.7
        
        if insufficient_contribution and insufficient_corpus:
            feasibility['is_feasible'] = False
            feasibility['overall_status'] = 'critically_underfunded'
            feasibility['recommendations'].insert(0, 
                "Your retirement plan is critically underfunded. Significant adjustments are needed to make retirement financially viable."
            )
        elif insufficient_contribution or insufficient_corpus:
            feasibility['is_feasible'] = True
            feasibility['overall_status'] = 'underfunded'
            feasibility['recommendations'].insert(0, 
                "Your retirement plan is underfunded. Adjustments are recommended to improve financial security in retirement."
            )
        elif contribution_percent >= retirement_min_percent and corpus_years_coverage >= corpus_income_ratio:
            feasibility['overall_status'] = 'adequately_funded'
            feasibility['recommendations'].insert(0, 
                "Your retirement plan appears adequately funded. Continue regular reviews to stay on track."
            )
        else:
            feasibility['overall_status'] = 'review_needed'
            
        return feasibility


class StrategyOptimizer:
    """
    Class for optimizing funding strategies with Indian tax efficiency focus.
    Implements optimization methods for tax efficiency, time horizon balancing,
    and contribution timing that's aligned with Indian market conditions.
    """
    
    def __init__(self):
        """Initialize with financial parameter service for optimization parameters"""
        self.param_service = get_financial_parameter_service()
        
        # Default optimization parameters
        self.params = {
            "tax_optimization": {
                "section_80c_limit": 150000,  # ₹1.5 lakh Section 80C limit
                "section_80ccd_limit": 50000,  # ₹50,000 additional NPS deduction under 80CCD(1B)
                "section_80d_limit": {
                    "self": 25000,           # ₹25,000 for self health insurance
                    "parents": 50000,        # ₹50,000 for parents (senior citizens)
                    "self_senior": 50000     # ₹50,000 if self is senior citizen
                },
                "capital_gains": {
                    "equity_lt_threshold_months": 12,  # 12 months for LTCG on equity
                    "debt_lt_threshold_months": 36,    # 36 months for LTCG on debt funds
                    "ltcg_equity_exemption": 100000,   # ₹1 lakh annual exemption for equity LTCG
                    "stcg_equity_rate": 0.15,          # 15% STCG on equity
                    "ltcg_equity_rate": 0.10,          # 10% LTCG on equity above ₹1L
                    "ltcg_debt_rate": 0.20,            # 20% LTCG with indexation benefit
                    "stcg_debt_rate": "slab"           # Taxed as per income slab
                }
            },
            "time_horizon_balance": {
                "near_term_threshold": 2,      # Goals within 2 years
                "mid_term_threshold": 7,       # Goals within 2-7 years
                "long_term_threshold": 7,      # Goals beyond 7 years
                "emergency_allocation": 0.30,  # 30% of portfolio for emergency/near-term needs
                "market_condition_factor": {
                    "bull": 1.2,               # More aggressive in bull markets
                    "bear": 0.8,               # More conservative in bear markets
                    "normal": 1.0              # Normal conditions
                }
            },
            "contribution_timing": {
                "sip_preference_threshold": 50000,  # Above ₹50k monthly, consider staggered deployment
                "lumpsum_threshold": 500000,        # ₹5 lakh or above for staggered deployment consideration
                "tax_year_end_months": [1, 2, 3],   # Jan, Feb, Mar (before tax year end)
                "bonus_season_months": [3, 4, 5],   # Mar, Apr, May (typical Indian bonus season)
                "staggered_deployment_period": {
                    "small": 3,                    # 3 months for ₹5L-₹10L
                    "medium": 6,                   # 6 months for ₹10L-₹25L
                    "large": 12                    # 12 months for ₹25L+
                }
            }
        }
        
        # Override defaults with service parameters
        self._load_optimization_parameters()
    
    def _load_optimization_parameters(self):
        """Load optimization parameters from financial parameter service if available"""
        if self.param_service:
            try:
                # Load tax optimization parameters
                tax_params = self.param_service.get_parameter('tax_optimization')
                if tax_params:
                    self.params['tax_optimization'].update(tax_params)
                
                # Load time horizon balance parameters
                horizon_params = self.param_service.get_parameter('time_horizon_balance')
                if horizon_params:
                    self.params['time_horizon_balance'].update(horizon_params)
                
                # Load contribution timing parameters
                timing_params = self.param_service.get_parameter('contribution_timing')
                if timing_params:
                    self.params['contribution_timing'].update(timing_params)
                    
            except Exception as e:
                logger.error(f"Error loading optimization parameters: {e}")
                # Continue with default parameters
    
    def optimize_tax_efficiency(self, strategies: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Maximize tax efficiency across funding strategies with focus on Indian tax laws.
        
        Args:
            strategies: List of funding strategies for different goals
            profile: User profile with income and tax information
            
        Returns:
            List of strategies optimized for tax efficiency
        """
        if not strategies or not profile:
            logger.warning("Cannot optimize tax efficiency: Missing strategies or profile data")
            return strategies
        
        # Make a copy of strategies to avoid modifying the original
        optimized_strategies = [dict(strategy) for strategy in strategies]
        
        # Extract relevant profile information
        tax_bracket = profile.get('tax_bracket', 0.3)  # Default to highest bracket if not specified
        age = profile.get('age', 35)
        parents_senior_citizens = profile.get('parents_senior_citizens', False)
        has_health_insurance = profile.get('has_health_insurance', False)
        
        # Section 80C parameters
        section_80c_limit = self.params['tax_optimization']['section_80c_limit']
        section_80ccd_limit = self.params['tax_optimization']['section_80ccd_limit']
        
        # Track total 80C investments already allocated
        allocated_80c = 0
        allocated_80ccd = 0
        
        # First pass: Identify eligible goals for tax-advantaged investments
        eligible_goals = []
        for idx, strategy in enumerate(optimized_strategies):
            goal_type = strategy.get('goal_type', '').lower()
            time_horizon = strategy.get('time_horizon', 0)
            
            # Eligibility score (higher = more suitable for tax advantage)
            eligibility = 0
            
            # Long-term goals are better for tax-advantaged investments
            if time_horizon > 5:
                eligibility += 3
            elif time_horizon > 3:
                eligibility += 2
            elif time_horizon > 1:
                eligibility += 1
            
            # Prioritize essential goals
            if goal_type in ('retirement', 'pension'):
                eligibility += 5  # Highest priority for retirement
            elif goal_type in ('education', 'higher education'):
                eligibility += 4  # High priority for education
            elif goal_type in ('home', 'home purchase'):
                eligibility += 3  # Good priority for home purchase
            elif goal_type == 'emergency fund':
                eligibility += 0  # Emergency funds need liquidity, not tax advantage
            
            if eligibility > 0:
                eligible_goals.append({
                    'index': idx,
                    'goal_type': goal_type,
                    'time_horizon': time_horizon,
                    'eligibility': eligibility,
                    'monthly_investment': strategy.get('recommendation', {}).get('total_monthly_investment', 0)
                })
        
        # Sort goals by eligibility score (highest first)
        eligible_goals.sort(key=lambda x: x['eligibility'], reverse=True)
        
        # Second pass: Allocate Section 80C investments (ELSS, PPF, etc.)
        for goal in eligible_goals:
            idx = goal['index']
            goal_type = goal['goal_type']
            monthly_investment = goal['monthly_investment']
            annual_investment = monthly_investment * 12
            
            # Skip if no investment recommended
            if monthly_investment <= 0:
                continue
            
            # Maximum that can still be allocated to 80C
            available_80c = max(0, section_80c_limit - allocated_80c)
            
            if available_80c > 0:
                tax_saving_instruments = {}
                tax_saving_notes = []
                
                if goal_type == 'retirement':
                    # Retirement: PPF and ELSS for 80C, plus NPS for 80CCD(1B)
                    if annual_investment >= 50000:
                        # Allocate to 80C instruments
                        ppf_amount = min(available_80c * 0.6, 70000)  # 60% to PPF, max 70k
                        elss_amount = min(available_80c - ppf_amount, available_80c * 0.4)  # Rest to ELSS
                        
                        # Allocate to NPS under 80CCD(1B)
                        available_80ccd = max(0, section_80ccd_limit - allocated_80ccd)
                        nps_amount = min(available_80ccd, 50000, annual_investment - ppf_amount - elss_amount)
                        
                        tax_saving_instruments['ppf'] = round(ppf_amount)
                        tax_saving_instruments['elss'] = round(elss_amount)
                        
                        if nps_amount > 0:
                            tax_saving_instruments['nps'] = round(nps_amount)
                            allocated_80ccd += nps_amount
                        
                        # Update allocated amounts
                        allocated_80c += (ppf_amount + elss_amount)
                        
                        tax_saving_notes.append(
                            f"Allocated ₹{round(ppf_amount):,} to PPF and ₹{round(elss_amount):,} to ELSS for Section 80C benefits."
                        )
                        if nps_amount > 0:
                            tax_saving_notes.append(
                                f"Additional ₹{round(nps_amount):,} to NPS for Section 80CCD(1B) benefits."
                            )
                    
                elif goal_type in ('education', 'higher education'):
                    # Education: Sukanya Samriddhi (for girl child) or ELSS
                    has_girl_child = profile.get('has_girl_child', False)
                    
                    if has_girl_child and goal['time_horizon'] > 5:
                        ssy_amount = min(available_80c * 0.7, 150000)  # Up to 70% to SSY, max 1.5L
                        elss_amount = min(available_80c - ssy_amount, available_80c * 0.3)  # Rest to ELSS
                        
                        tax_saving_instruments['sukanya_samriddhi'] = round(ssy_amount)
                        if elss_amount > 0:
                            tax_saving_instruments['elss'] = round(elss_amount)
                        
                        allocated_80c += (ssy_amount + elss_amount)
                        
                        tax_saving_notes.append(
                            f"Allocated ₹{round(ssy_amount):,} to Sukanya Samriddhi Yojana for girl child education."
                        )
                        if elss_amount > 0:
                            tax_saving_notes.append(
                                f"Additional ₹{round(elss_amount):,} to ELSS for Section 80C benefits."
                            )
                    else:
                        # No girl child or short time horizon, use ELSS
                        elss_amount = min(available_80c, 150000)
                        tax_saving_instruments['elss'] = round(elss_amount)
                        allocated_80c += elss_amount
                        
                        tax_saving_notes.append(
                            f"Allocated ₹{round(elss_amount):,} to ELSS for Section 80C benefits."
                        )
                
                elif goal_type in ('home', 'home purchase'):
                    # Home purchase: Tax benefits on home loan principal (80C) and interest (24)
                    # Here we focus on principal component for 80C
                    if goal['time_horizon'] < 3:
                        home_loan_principal = min(available_80c, 150000)
                        tax_saving_instruments['home_loan_principal'] = round(home_loan_principal)
                        allocated_80c += home_loan_principal
                        
                        tax_saving_notes.append(
                            f"Allocated ₹{round(home_loan_principal):,} to home loan principal repayment for Section 80C benefits."
                        )
                        tax_saving_notes.append(
                            "Additional tax benefits available on home loan interest under Section 24 (up to ₹2,00,000)."
                        )
                
                # Update strategy with tax optimization recommendations
                if tax_saving_instruments and 'recommendation' in optimized_strategies[idx]:
                    if 'tax_optimization' not in optimized_strategies[idx]['recommendation']:
                        optimized_strategies[idx]['recommendation']['tax_optimization'] = {}
                    
                    optimized_strategies[idx]['recommendation']['tax_optimization']['instruments'] = tax_saving_instruments
                    optimized_strategies[idx]['recommendation']['tax_optimization']['notes'] = tax_saving_notes
                    optimized_strategies[idx]['recommendation']['tax_optimization']['potential_tax_benefit'] = round(
                        sum(tax_saving_instruments.values()) * tax_bracket
                    )
        
        # Third pass: Handle Section 80D (health insurance) if applicable
        if has_health_insurance:
            health_insurance_limit = self.params['tax_optimization']['section_80d_limit']['self']
            if age >= 60:
                health_insurance_limit = self.params['tax_optimization']['section_80d_limit']['self_senior']
            
            parents_limit = 0
            if parents_senior_citizens:
                parents_limit = self.params['tax_optimization']['section_80d_limit']['parents']
            
            total_80d_limit = health_insurance_limit + parents_limit
            
            # Find health-related goals
            for idx, strategy in enumerate(optimized_strategies):
                if strategy.get('goal_type', '').lower() in ('health', 'medical', 'healthcare'):
                    if 'recommendation' in strategy:
                        if 'tax_optimization' not in strategy['recommendation']:
                            strategy['recommendation']['tax_optimization'] = {}
                        
                        strategy['recommendation']['tax_optimization']['section_80d'] = {
                            'eligible_amount': total_80d_limit,
                            'potential_tax_benefit': round(total_80d_limit * tax_bracket),
                            'notes': [
                                f"Health insurance premiums eligible for deduction under Section 80D (up to ₹{health_insurance_limit:,} for self"
                                + (f" and ₹{parents_limit:,} for senior citizen parents" if parents_limit > 0 else "") + ")."
                            ]
                        }
        
        # Fourth pass: Optimize based on capital gains tax considerations
        for idx, strategy in enumerate(optimized_strategies):
            time_horizon = strategy.get('time_horizon', 0)
            if 'recommendation' in strategy and 'asset_allocation' in strategy['recommendation']:
                allocation = strategy['recommendation']['asset_allocation']
                tax_notes = []
                
                # For short time horizons, prioritize debt that avoids short-term capital gains
                if time_horizon < 1:
                    tax_notes.append("For very short-term goals, focus on liquid funds and arbitrage funds to minimize tax impact.")
                
                # For medium time horizons (1-3 years), balance STCG on equity vs LTCG on debt
                elif time_horizon < 3:
                    if allocation.get('equity', 0) > 0.3:
                        tax_notes.append(
                            "Consider reducing equity allocation to minimize 15% STCG tax impact since time horizon is less than 3 years."
                        )
                    tax_notes.append(
                        "Debt investments held for over 3 years qualify for 20% LTCG with indexation benefit, which can be more tax-efficient."
                    )
                
                # For horizons over 1 year but under LTCG threshold for debt
                elif time_horizon >= 1 and time_horizon < 3:
                    tax_notes.append(
                        "Equity investments held over 1 year qualify for 10% LTCG tax (with ₹1 lakh exemption), more efficient than debt STCG."
                    )
                
                # For long time horizons (>3 years), both equity and debt can qualify for LTCG
                elif time_horizon >= 3:
                    tax_notes.append(
                        "Both equity (>1 year) and debt (>3 years) investments qualify for LTCG tax treatment, optimizing tax efficiency."
                    )
                    if allocation.get('equity', 0) > 0.7:
                        tax_notes.append(
                            "High equity allocation benefits from ₹1 lakh annual LTCG exemption on equity investments."
                        )
                
                # Add capital gains notes if there are any
                if tax_notes and 'recommendation' in optimized_strategies[idx]:
                    if 'tax_optimization' not in optimized_strategies[idx]['recommendation']:
                        optimized_strategies[idx]['recommendation']['tax_optimization'] = {}
                    
                    if 'capital_gains_notes' not in optimized_strategies[idx]['recommendation']['tax_optimization']:
                        optimized_strategies[idx]['recommendation']['tax_optimization']['capital_gains_notes'] = []
                    
                    optimized_strategies[idx]['recommendation']['tax_optimization']['capital_gains_notes'].extend(tax_notes)
        
        # Add overall tax optimization summary
        tax_efficiency_summary = {
            'total_80c_allocated': allocated_80c,
            'remaining_80c': max(0, section_80c_limit - allocated_80c),
            'total_80ccd_allocated': allocated_80ccd,
            'remaining_80ccd': max(0, section_80ccd_limit - allocated_80ccd),
            'potential_tax_savings': round((allocated_80c + allocated_80ccd) * tax_bracket),
            'tax_year_end_guidance': "Consider completing tax-saving investments before March 31st to claim deductions in the current financial year."
        }
        
        # Return optimized strategies
        return optimized_strategies, tax_efficiency_summary
    
    def balance_short_long_term(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize allocation between immediate and future goals based on
        Indian market conditions and risk-return profiles.
        
        Args:
            strategies: List of funding strategies for different goals
            
        Returns:
            List of strategies with balanced allocation across time horizons
        """
        if not strategies:
            return strategies
        
        # Make a copy to avoid modifying the original
        balanced_strategies = [dict(strategy) for strategy in strategies]
        
        # Group strategies by time horizon
        near_term_goals = []
        mid_term_goals = []
        long_term_goals = []
        
        near_term_threshold = self.params['time_horizon_balance']['near_term_threshold']
        mid_term_threshold = self.params['time_horizon_balance']['mid_term_threshold']
        
        # Categorize goals by time horizon
        for idx, strategy in enumerate(balanced_strategies):
            time_horizon = strategy.get('time_horizon', 0)
            monthly_investment = strategy.get('recommendation', {}).get('total_monthly_investment', 0)
            
            if monthly_investment <= 0:
                continue
                
            goal_data = {
                'index': idx,
                'goal_type': strategy.get('goal_type', 'general'),
                'time_horizon': time_horizon,
                'monthly_investment': monthly_investment,
                'priority': 0.5  # Default priority
            }
            
            # Adjust priority based on goal type
            if goal_data['goal_type'] == 'emergency fund':
                goal_data['priority'] = 0.9
            elif goal_data['goal_type'] in ('retirement', 'pension'):
                goal_data['priority'] = 0.8
            elif goal_data['goal_type'] in ('education', 'higher education'):
                goal_data['priority'] = 0.7
            elif goal_data['goal_type'] in ('home', 'home purchase'):
                goal_data['priority'] = 0.6
            elif goal_data['goal_type'] in ('vacation', 'travel', 'vehicle'):
                goal_data['priority'] = 0.3
                
            # Categorize by time horizon
            if time_horizon <= near_term_threshold:
                near_term_goals.append(goal_data)
            elif time_horizon <= mid_term_threshold:
                mid_term_goals.append(goal_data)
            else:
                long_term_goals.append(goal_data)
        
        # Calculate total monthly investment across all goals
        total_monthly = sum(
            s.get('recommendation', {}).get('total_monthly_investment', 0) 
            for s in balanced_strategies
        )
        
        if total_monthly <= 0:
            return balanced_strategies
            
        # Calculate current allocation by time horizon
        near_term_allocation = sum(g['monthly_investment'] for g in near_term_goals) / total_monthly
        mid_term_allocation = sum(g['monthly_investment'] for g in mid_term_goals) / total_monthly
        long_term_allocation = sum(g['monthly_investment'] for g in long_term_goals) / total_monthly
        
        # Ideal allocation ratios (can be adjusted based on market conditions)
        # Balance between liquidity, growth, and long-term wealth creation
        emergency_allocation = self.params['time_horizon_balance']['emergency_allocation']
        ideal_near_term = emergency_allocation  # ~30% for near-term/emergency needs
        ideal_mid_term = 0.30  # ~30% for mid-term goals
        ideal_long_term = 0.40  # ~40% for long-term growth
        
        # Adjust based on market conditions (optional)
        market_condition = "normal"  # Could be dynamically determined
        market_factor = self.params['time_horizon_balance']['market_condition_factor'].get(market_condition, 1.0)
        
        ideal_near_term = max(0.2, ideal_near_term / market_factor)
        ideal_long_term = min(0.7, ideal_long_term * market_factor)
        ideal_mid_term = 1.0 - ideal_near_term - ideal_long_term
        
        # Initialize balance adjustments
        balance_notes = []
        adjusted_strategies = []
        
        # Check if significant rebalancing is needed
        significant_adjustment = (
            abs(near_term_allocation - ideal_near_term) > 0.1 or
            abs(mid_term_allocation - ideal_mid_term) > 0.1 or
            abs(long_term_allocation - ideal_long_term) > 0.1
        )
        
        if significant_adjustment:
            # If significant adjustment needed, prepare balance notes
            if near_term_allocation < ideal_near_term:
                balance_notes.append(
                    f"Near-term allocation ({near_term_allocation:.0%}) is below target ({ideal_near_term:.0%}). "
                    f"Consider increasing allocation to liquid investments for short-term needs."
                )
            elif near_term_allocation > ideal_near_term + 0.1:
                balance_notes.append(
                    f"Near-term allocation ({near_term_allocation:.0%}) is higher than target ({ideal_near_term:.0%}). "
                    f"Consider shifting some funds to mid or long-term investments for better growth potential."
                )
                
            if long_term_allocation < ideal_long_term:
                balance_notes.append(
                    f"Long-term allocation ({long_term_allocation:.0%}) is below target ({ideal_long_term:.0%}). "
                    f"Consider increasing allocation to equity-oriented investments for long-term growth."
                )
            
            # Provide goal-specific adjustments for better balance
            for goal in near_term_goals + mid_term_goals + long_term_goals:
                idx = goal['index']
                if 'recommendation' in balanced_strategies[idx]:
                    if 'time_horizon_balance' not in balanced_strategies[idx]['recommendation']:
                        balanced_strategies[idx]['recommendation']['time_horizon_balance'] = {}
                    
                    # Get original allocation if available
                    original_allocation = balanced_strategies[idx]['recommendation'].get('asset_allocation', {})
                    adjusted_allocation = dict(original_allocation)
                    
                    # Adjust allocation based on time horizon category
                    if goal['time_horizon'] <= near_term_threshold:
                        if near_term_allocation < ideal_near_term:
                            # Suggest more conservative allocation for near-term goals
                            adjusted_allocation['cash'] = min(0.4, original_allocation.get('cash', 0) + 0.1)
                            adjusted_allocation['debt'] = min(0.5, original_allocation.get('debt', 0) + 0.05)
                            adjusted_allocation['equity'] = max(0.1, original_allocation.get('equity', 0) - 0.15)
                            
                            balanced_strategies[idx]['recommendation']['time_horizon_balance']['adjusted_allocation'] = adjusted_allocation
                            balanced_strategies[idx]['recommendation']['time_horizon_balance']['notes'] = [
                                "Adjusted to more conservative allocation to match near-term liquidity needs.",
                                "Increased cash and debt components for better capital preservation."
                            ]
                    
                    elif goal['time_horizon'] <= mid_term_threshold:
                        # Mid-term balance should have moderate allocation
                        if mid_term_allocation < ideal_mid_term:
                            adjusted_allocation['equity'] = min(0.6, original_allocation.get('equity', 0) + 0.05)
                            adjusted_allocation['debt'] = max(0.3, original_allocation.get('debt', 0) - 0.05)
                            
                            balanced_strategies[idx]['recommendation']['time_horizon_balance']['adjusted_allocation'] = adjusted_allocation
                            balanced_strategies[idx]['recommendation']['time_horizon_balance']['notes'] = [
                                "Adjusted to balanced allocation suitable for mid-term goals.",
                                "Moderate equity exposure for growth with reasonable stability."
                            ]
                    
                    else:  # Long-term goals
                        if long_term_allocation < ideal_long_term:
                            # Long-term goals should be more equity-oriented
                            adjusted_allocation['equity'] = min(0.75, original_allocation.get('equity', 0) + 0.1)
                            adjusted_allocation['debt'] = max(0.2, original_allocation.get('debt', 0) - 0.1)
                            
                            balanced_strategies[idx]['recommendation']['time_horizon_balance']['adjusted_allocation'] = adjusted_allocation
                            balanced_strategies[idx]['recommendation']['time_horizon_balance']['notes'] = [
                                "Adjusted to growth-oriented allocation suitable for long-term goals.",
                                "Higher equity exposure to maximize long-term returns."
                            ]
        
        # Add overall balance notes to all strategies
        if balance_notes:
            for strategy in balanced_strategies:
                if 'recommendation' in strategy:
                    if 'time_horizon_balance' not in strategy['recommendation']:
                        strategy['recommendation']['time_horizon_balance'] = {}
                    
                    if 'overall_notes' not in strategy['recommendation']['time_horizon_balance']:
                        strategy['recommendation']['time_horizon_balance']['overall_notes'] = []
                    
                    strategy['recommendation']['time_horizon_balance']['overall_notes'].extend(balance_notes)
        
        return balanced_strategies
    
    def optimize_contribution_timing(self, strategy: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine optimal timing for contributions based on Indian market conditions,
        salary cycles, and tax year considerations.
        
        Args:
            strategy: Funding strategy for a specific goal
            profile: User profile with income and bonus information
            
        Returns:
            Strategy with optimized contribution timing
        """
        if not strategy or not profile or 'recommendation' not in strategy:
            return strategy
        
        # Clone strategy to avoid modifying original
        optimized_strategy = dict(strategy)
        
        # Extract relevant information
        monthly_income = profile.get('monthly_income', 0)
        has_annual_bonus = profile.get('has_annual_bonus', False)
        bonus_month = profile.get('bonus_month', 3)  # Default March
        bonus_amount = profile.get('bonus_amount', 0)
        
        monthly_investment = optimized_strategy['recommendation'].get('total_monthly_investment', 0)
        lump_sum_alternative = optimized_strategy['recommendation'].get('lump_sum_alternative', 0)
        goal_type = optimized_strategy.get('goal_type', '')
        time_horizon = optimized_strategy.get('time_horizon', 0)
        
        # Initialize timing recommendations
        timing_recommendation = {
            'sip_vs_lumpsum': {},
            'contribution_schedule': {},
            'notes': []
        }
        
        # Current month (for tax year end planning)
        current_month = datetime.now().month
        
        # 1. SIP vs Lumpsum decision
        sip_preference_threshold = self.params['contribution_timing']['sip_preference_threshold']
        
        if monthly_investment >= sip_preference_threshold:
            # High monthly amount may benefit from splitting into multiple SIPs
            timing_recommendation['sip_vs_lumpsum']['recommendation'] = 'split_sip'
            timing_recommendation['sip_vs_lumpsum']['split_frequency'] = 'bi_weekly'
            timing_recommendation['sip_vs_lumpsum']['split_amount'] = round(monthly_investment / 2)
            timing_recommendation['notes'].append(
                f"Monthly investment of ₹{monthly_investment:,} exceeds ₹{sip_preference_threshold:,}. "
                f"Consider splitting into bi-weekly SIPs of ₹{round(monthly_investment / 2):,} each for better rupee cost averaging."
            )
        else:
            # Regular SIP is appropriate
            timing_recommendation['sip_vs_lumpsum']['recommendation'] = 'regular_sip'
            timing_recommendation['sip_vs_lumpsum']['frequency'] = 'monthly'
            timing_recommendation['sip_vs_lumpsum']['amount'] = monthly_investment
        
        # 2. Lump sum deployment strategy (if applicable)
        lumpsum_threshold = self.params['contribution_timing']['lumpsum_threshold']
        
        if lump_sum_alternative >= lumpsum_threshold or (has_annual_bonus and bonus_amount >= lumpsum_threshold):
            # Determine staggered deployment period based on amount
            staggered_amount = max(lump_sum_alternative, bonus_amount if has_annual_bonus else 0)
            
            deployment_period = 3  # Default
            if staggered_amount >= 2500000:  # ₹25 lakhs+
                deployment_period = self.params['contribution_timing']['staggered_deployment_period']['large']
            elif staggered_amount >= 1000000:  # ₹10 lakhs+
                deployment_period = self.params['contribution_timing']['staggered_deployment_period']['medium']
            else:
                deployment_period = self.params['contribution_timing']['staggered_deployment_period']['small']
            
            monthly_deployment = round(staggered_amount / deployment_period)
            
            timing_recommendation['lump_sum_deployment'] = {
                'strategy': 'staggered',
                'total_amount': round(staggered_amount),
                'deployment_period_months': deployment_period,
                'monthly_deployment': monthly_deployment
            }
            
            timing_recommendation['notes'].append(
                f"Lump sum amount of ₹{staggered_amount:,} should be deployed gradually over {deployment_period} months "
                f"(₹{monthly_deployment:,} per month) to mitigate market timing risk."
            )
            
            # STP recommendation if applicable
            if time_horizon > 3 and staggered_amount >= 500000:
                timing_recommendation['lump_sum_deployment']['stp_recommendation'] = {
                    'initial_fund': 'Liquid Fund',
                    'target_fund': 'Equity Fund' if time_horizon > 7 else 'Balanced Fund',
                    'monthly_transfer': monthly_deployment
                }
                
                timing_recommendation['notes'].append(
                    f"Use Systematic Transfer Plan (STP) from liquid fund to {timing_recommendation['lump_sum_deployment']['stp_recommendation']['target_fund']} "
                    f"for efficient deployment and to earn returns during the staggering period."
                )
        
        # 3. Tax year end planning
        tax_year_end_months = self.params['contribution_timing']['tax_year_end_months']
        
        if current_month in tax_year_end_months:
            months_to_year_end = (3 - current_month) % 12 + 1  # Months until March 31
            
            timing_recommendation['tax_year_planning'] = {
                'months_to_year_end': months_to_year_end,
                'action_required': months_to_year_end <= 3
            }
            
            if months_to_year_end <= 3:
                timing_recommendation['notes'].append(
                    f"Tax year ends in {months_to_year_end} month(s). Prioritize tax-saving investments like ELSS, PPF, and NPS "
                    f"before March 31st to claim deductions in current financial year."
                )
        
        # 4. Salary cycle and bonus optimization
        if has_annual_bonus and bonus_month > 0:
            # Calculate months to next bonus
            months_to_bonus = (bonus_month - current_month) % 12
            if months_to_bonus == 0:
                months_to_bonus = 12
            
            timing_recommendation['bonus_planning'] = {
                'bonus_month': bonus_month,
                'months_to_next_bonus': months_to_bonus
            }
            
            if bonus_amount > monthly_income:
                # Significant bonus that can be strategically allocated
                if months_to_bonus <= 3:
                    timing_recommendation['notes'].append(
                        f"Annual bonus expected in {months_to_bonus} month(s). Consider planning for lump sum investment allocation "
                        f"rather than increasing monthly SIP amount."
                    )
                else:
                    timing_recommendation['notes'].append(
                        f"Continue regular SIPs now. Plan strategic allocation of annual bonus expected in {months_to_bonus} month(s)."
                    )
        
        # Add timing recommendations to strategy
        optimized_strategy['recommendation']['contribution_timing'] = timing_recommendation
        
        return optimized_strategy


class CompoundStrategy:
    """
    Class for handling complex Indian financial goals through compound strategies.
    Combines multiple strategies, handles irregular income patterns, and performs
    scenario analysis for optimal financial planning in the Indian context.
    """
    
    def __init__(self):
        """Initialize with financial parameter service and optional life event registry"""
        self.param_service = get_financial_parameter_service()
        
        # Default parameters
        self.params = {
            "combination_rules": {
                "max_allocation_per_asset_class": {
                    "equity": 0.80,        # Maximum 80% in equity across all goals
                    "debt": 0.70,          # Maximum 70% in debt across all goals
                    "gold": 0.15,          # Maximum 15% in gold across all goals
                    "cash": 0.30,          # Maximum 30% in cash across all goals
                    "alternatives": 0.10   # Maximum 10% in alternatives across all goals
                },
                "min_allocation_per_asset_class": {
                    "cash": 0.05           # Minimum 5% in cash for liquidity
                },
                "time_horizon_overlap_threshold": 0.5,  # 50% overlap triggers combining
                "priority_preservation_factor": 0.8     # Maintain 80% of original priority
            },
            "irregular_income": {
                "bonus_deployment": {
                    "emergency_fund": 0.20,   # 20% to emergency fund
                    "short_term_goals": 0.30, # 30% to short-term goals
                    "long_term_goals": 0.40,  # 40% to long-term goals
                    "discretionary": 0.10     # 10% discretionary/enjoyment
                },
                "windfall_deployment": {
                    "emergency_fund": 0.10,    # 10% to emergency fund
                    "debt_repayment": 0.20,    # 20% to eliminate high-interest debt
                    "long_term_goals": 0.50,   # 50% to long-term investments
                    "medium_term_goals": 0.15, # 15% to medium-term goals
                    "discretionary": 0.05      # 5% discretionary
                },
                "seasonal_income_buffer": 0.30, # 30% buffer for seasonal income volatility
                "staggered_deployment_periods": {
                    "small": 3,            # 3 months for amount < ₹10L
                    "medium": 6,           # 6 months for ₹10L - ₹50L
                    "large": 12,           # 12 months for amounts > ₹50L
                    "very_large": 24       # 24 months for amounts > ₹1Cr
                }
            },
            "scenario_analysis": {
                "market_conditions": {
                    "optimistic": {
                        "equity": 0.14,    # 14% annualized returns
                        "debt": 0.08,      # 8% annualized returns
                        "gold": 0.10,      # 10% annualized returns
                        "cash": 0.04,      # 4% annualized returns
                        "alternatives": 0.12  # 12% annualized returns
                    },
                    "baseline": {
                        "equity": 0.10,    # 10% annualized returns
                        "debt": 0.06,      # 6% annualized returns
                        "gold": 0.07,      # 7% annualized returns
                        "cash": 0.03,      # 3% annualized returns
                        "alternatives": 0.09  # 9% annualized returns
                    },
                    "pessimistic": {
                        "equity": 0.06,    # 6% annualized returns
                        "debt": 0.04,      # 4% annualized returns
                        "gold": 0.08,      # 8% annualized returns
                        "cash": 0.025,     # 2.5% annualized returns
                        "alternatives": 0.05  # 5% annualized returns
                    }
                },
                "contribution_patterns": {
                    "increasing": 0.05,    # 5% annual increase
                    "steady": 0.0,         # No change
                    "decreasing": -0.03    # 3% annual decrease
                },
                "confidence_thresholds": {
                    "high": 0.75,          # 75% success rate for high confidence
                    "medium": 0.60,        # 60% success rate for medium confidence
                    "low": 0.50            # 50% success rate for low confidence
                },
                "simulation_iterations": 1000  # Number of Monte Carlo iterations
            }
        }
        
        # Try importing life event registry
        try:
            from models.life_event_registry import LifeEventRegistry
            self.life_event_registry = LifeEventRegistry()
            self.has_life_event_registry = True
            logger.info("Initialized with access to centralized LifeEventRegistry")
        except ImportError:
            self.life_event_registry = None
            self.has_life_event_registry = False
            logger.warning("LifeEventRegistry not available, falling back to static analysis")
        
        # Override defaults with service parameters
        self._load_compound_parameters()
    
    def _load_compound_parameters(self):
        """Load compound strategy parameters from financial parameter service if available"""
        if self.param_service:
            try:
                # Load combination rules
                combination_rules = self.param_service.get_parameter('combination_rules')
                if combination_rules:
                    self.params['combination_rules'].update(combination_rules)
                
                # Load irregular income parameters
                irregular_income = self.param_service.get_parameter('irregular_income')
                if irregular_income:
                    self.params['irregular_income'].update(irregular_income)
                
                # Load scenario analysis parameters
                scenario_analysis = self.param_service.get_parameter('scenario_analysis')
                if scenario_analysis:
                    self.params['scenario_analysis'].update(scenario_analysis)
                    
            except Exception as e:
                logger.error(f"Error loading compound strategy parameters: {e}")
                # Continue with default parameters
    
    def combine_strategies(self, strategy_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create hybrid approaches for multi-purpose goals by combining multiple strategies.
        
        Args:
            strategy_list: List of funding strategies to combine
            
        Returns:
            Combined strategy with integrated approach
        """
        if not strategy_list or len(strategy_list) < 2:
            if strategy_list:
                return strategy_list[0]  # Return single strategy unchanged
            return {}  # Return empty dict if no strategies
        
        # Extract key elements from each strategy
        combined_elements = {
            "goal_types": [],
            "time_horizons": [],
            "target_amounts": [],
            "current_savings": [],
            "monthly_contributions": [],
            "priorities": [],
            "allocations": [],
            "risk_profiles": []
        }
        
        # Process each strategy to extract key elements
        for strategy in strategy_list:
            combined_elements["goal_types"].append(strategy.get("goal_type", "unknown"))
            combined_elements["time_horizons"].append(strategy.get("time_horizon", 0))
            
            # Extract target amount and current status
            current_status = strategy.get("current_status", {})
            combined_elements["target_amounts"].append(current_status.get("target_amount", 0))
            combined_elements["current_savings"].append(current_status.get("current_savings", 0))
            combined_elements["monthly_contributions"].append(current_status.get("monthly_contribution", 0))
            
            # Extract allocation and risk profile from recommendation
            recommendation = strategy.get("recommendation", {})
            combined_elements["allocations"].append(recommendation.get("asset_allocation", {}))
            
            # Determine priority based on goal type
            priority = 0.5  # Default priority
            goal_type = strategy.get("goal_type", "").lower()
            if goal_type in ["emergency fund"]:
                priority = 0.9
            elif goal_type in ["retirement", "pension"]:
                priority = 0.8
            elif goal_type in ["education", "higher education"]:
                priority = 0.7
            elif goal_type in ["home", "home purchase"]:
                priority = 0.6
            elif goal_type in ["wedding", "marriage"]:
                priority = 0.5
            elif goal_type in ["vacation", "travel", "vehicle"]:
                priority = 0.3
            combined_elements["priorities"].append(priority)
            
            # Extract risk profile
            risk_profile = "moderate"  # Default
            if "risk_profile" in strategy:
                risk_profile = strategy["risk_profile"]
            combined_elements["risk_profiles"].append(risk_profile)
        
        # Create combined strategy framework
        combined_strategy = {
            "goal_type": "_".join(combined_elements["goal_types"]),
            "display_name": " + ".join(combined_elements["goal_types"]).title(),
            "is_compound": True,
            "original_strategies": strategy_list,
            "compound_analysis": {}
        }
        
        # Analyze time horizons for overlaps
        time_horizons = combined_elements["time_horizons"]
        min_horizon = min(time_horizons)
        max_horizon = max(time_horizons)
        avg_horizon = sum(time_horizons) / len(time_horizons)
        
        # Determine if time horizons overlap significantly
        overlap_threshold = self.params["combination_rules"]["time_horizon_overlap_threshold"]
        time_overlap_ratio = min_horizon / max_horizon if max_horizon > 0 else 0
        has_significant_overlap = time_overlap_ratio >= overlap_threshold
        
        # Set combined time horizon based on overlaps
        if has_significant_overlap:
            # If significant overlap, use weighted average
            combined_strategy["time_horizon"] = round(
                sum(th * p for th, p in zip(time_horizons, combined_elements["priorities"])) / 
                sum(combined_elements["priorities"])
            )
        else:
            # If limited overlap, preserve individual horizons
            combined_strategy["time_horizon"] = round(avg_horizon)
            combined_strategy["compound_analysis"]["distinct_horizons"] = sorted(time_horizons)
        
        # Analyze financial targets
        combined_strategy["current_status"] = {
            "target_amount": sum(combined_elements["target_amounts"]),
            "current_savings": sum(combined_elements["current_savings"]),
            "monthly_contribution": sum(combined_elements["monthly_contributions"])
        }
        
        # Calculate gap
        target = combined_strategy["current_status"]["target_amount"]
        savings = combined_strategy["current_status"]["current_savings"]
        combined_strategy["current_status"]["gap"] = max(0, target - savings)
        combined_strategy["current_status"]["percent_funded"] = (savings / target * 100) if target > 0 else 0
        
        # Determine combined risk profile
        risk_levels = {"conservative": 1, "moderate": 2, "aggressive": 3}
        weighted_risk = sum(risk_levels.get(rp, 2) * p for rp, p in zip(combined_elements["risk_profiles"], combined_elements["priorities"]))
        weighted_risk /= sum(combined_elements["priorities"])
        
        if weighted_risk <= 1.5:
            combined_risk = "conservative"
        elif weighted_risk <= 2.5:
            combined_risk = "moderate"
        else:
            combined_risk = "aggressive"
        
        # Calculate combined asset allocation while respecting limits
        combined_allocation = {"equity": 0, "debt": 0, "gold": 0, "cash": 0, "alternatives": 0}
        total_weight = sum(combined_elements["priorities"])
        
        for allocation, priority in zip(combined_elements["allocations"], combined_elements["priorities"]):
            weight = priority / total_weight if total_weight > 0 else 0
            for asset, percentage in allocation.items():
                if asset in combined_allocation:
                    combined_allocation[asset] += percentage * weight
        
        # Apply limits to asset classes
        max_limits = self.params["combination_rules"]["max_allocation_per_asset_class"]
        min_limits = self.params["combination_rules"]["min_allocation_per_asset_class"]
        
        for asset, limit in max_limits.items():
            if asset in combined_allocation and combined_allocation[asset] > limit:
                excess = combined_allocation[asset] - limit
                combined_allocation[asset] = limit
                
                # Redistribute excess to other assets
                other_assets = [a for a in combined_allocation if a != asset and combined_allocation[a] < max_limits.get(a, 1.0)]
                if other_assets:
                    per_asset = excess / len(other_assets)
                    for other_asset in other_assets:
                        combined_allocation[other_asset] += per_asset
        
        # Ensure minimum allocation requirements are met
        for asset, minimum in min_limits.items():
            if asset in combined_allocation and combined_allocation[asset] < minimum:
                shortfall = minimum - combined_allocation[asset]
                combined_allocation[asset] = minimum
                
                # Reduce other allocations proportionally
                other_assets = [a for a in combined_allocation if a != asset and combined_allocation[a] > 0]
                if other_assets:
                    total_other = sum(combined_allocation[a] for a in other_assets)
                    for other_asset in other_assets:
                        reduction = shortfall * (combined_allocation[other_asset] / total_other)
                        combined_allocation[other_asset] = max(0, combined_allocation[other_asset] - reduction)
        
        # Round allocation percentages
        for asset in combined_allocation:
            combined_allocation[asset] = round(combined_allocation[asset], 2)
        
        # Create combined recommendation
        combined_strategy["recommendation"] = {
            "asset_allocation": combined_allocation,
            "risk_profile": combined_risk,
            "expected_annual_return": self._calculate_expected_return(combined_allocation)
        }
        
        # Calculate aggregated monthly investment required
        monthly_required = 0
        for strategy in strategy_list:
            if "recommendation" in strategy and "additional_monthly_required" in strategy["recommendation"]:
                monthly_required += strategy["recommendation"]["additional_monthly_required"]
        
        combined_strategy["recommendation"]["additional_monthly_required"] = monthly_required
        combined_strategy["recommendation"]["total_monthly_investment"] = (
            combined_strategy["current_status"]["monthly_contribution"] + monthly_required
        )
        
        # Add investment instruments by combining from individual strategies
        combined_instruments = {"monthly": {}, "lump_sum": {}, "rationale": {}}
        
        for strategy in strategy_list:
            if "recommendation" in strategy and "investment_instruments" in strategy["recommendation"]:
                instruments = strategy["recommendation"]["investment_instruments"]
                
                for category in ["monthly", "lump_sum"]:
                    if category in instruments:
                        for instrument, amount in instruments[category].items():
                            if instrument in combined_instruments[category]:
                                combined_instruments[category][instrument] += amount
                            else:
                                combined_instruments[category][instrument] = amount
                
                # Combine rationales
                if "rationale" in instruments:
                    for key, rationale in instruments["rationale"].items():
                        if key not in combined_instruments["rationale"]:
                            combined_instruments["rationale"][key] = []
                        
                        if rationale not in combined_instruments["rationale"][key]:
                            combined_instruments["rationale"][key].append(rationale)
        
        combined_strategy["recommendation"]["investment_instruments"] = combined_instruments
        
        # Add compound-specific recommendations
        if not has_significant_overlap:
            combined_strategy["compound_analysis"]["time_horizon_conflict"] = True
            combined_strategy["compound_analysis"]["recommendations"] = [
                "Consider separate investment buckets for goals with different time horizons",
                "Use a glide path approach to transition between allocations as goals approach"
            ]
        else:
            combined_strategy["compound_analysis"]["time_horizon_conflict"] = False
            combined_strategy["compound_analysis"]["recommendations"] = [
                "Combined strategy is efficient due to similar time horizons",
                "Use a unified investment approach with the recommended asset allocation"
            ]
        
        # Add tax efficiency considerations
        combined_strategy["compound_analysis"]["tax_efficiency_notes"] = [
            "Ensure tax-advantaged accounts are prioritized appropriately across combined goals",
            "Consider tax-efficient asset location - holding tax-inefficient assets in tax-advantaged accounts"
        ]
        
        # Register with life event registry if available
        if self.has_life_event_registry:
            self._register_compound_strategy(combined_strategy)
        
        return combined_strategy
    
    def _register_compound_strategy(self, strategy: Dict[str, Any]) -> None:
        """Register compound strategy creation as a life event for future tracking"""
        if not self.has_life_event_registry:
            return
            
        try:
            # Extract profile ID if available
            profile_id = None
            for original in strategy.get("original_strategies", []):
                if "user_profile_id" in original:
                    profile_id = original["user_profile_id"]
                    break
            
            if not profile_id:
                return
                
            # Create custom life event
            from models.life_event_registry import LifeEvent, EventCategory, EventSeverity
            
            event = LifeEvent(
                name="Compound Goal Creation",
                description=f"Created compound goal strategy: {strategy.get('display_name', 'Combined Goals')}",
                category=EventCategory.FINANCIAL,
                severity=EventSeverity.MEDIUM,
                user_profile_id=profile_id,
                metadata={
                    "compound_goal_types": strategy.get("goal_type", ""),
                    "time_horizon": strategy.get("time_horizon", 0),
                    "target_amount": strategy.get("current_status", {}).get("target_amount", 0),
                    "rebalancing_impacts": {
                        "allocation_shift": "moderate",
                        "goal_priority_shift": True,
                        "requires_multi_bucket_approach": strategy.get("compound_analysis", {}).get("time_horizon_conflict", False)
                    }
                },
                trigger_source="compound_strategy_generator"
            )
            
            # Register the event
            self.life_event_registry.register_event(event)
            
        except Exception as e:
            logger.error(f"Error registering compound strategy with life event registry: {e}")
    
    def incorporate_irregular_income(self, strategy: Dict[str, Any], income_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize strategy to incorporate irregular income patterns like bonuses and windfalls.
        
        Args:
            strategy: The funding strategy to enhance
            income_events: List of irregular income events with amounts and dates
            
        Returns:
            Enhanced strategy with irregular income incorporation
        """
        if not strategy or not income_events:
            return strategy
        
        # Clone strategy to avoid modifying original
        enhanced_strategy = dict(strategy)
        if "irregular_income_plan" not in enhanced_strategy:
            enhanced_strategy["irregular_income_plan"] = {
                "events": [],
                "deployment_plan": {},
                "impact_analysis": {},
                "recommendations": []
            }
        
        # Process each income event
        total_irregular_amount = 0
        for event in income_events:
            event_type = event.get("type", "").lower()
            amount = event.get("amount", 0)
            date = event.get("date", "")
            frequency = event.get("frequency", "one_time")
            
            if amount <= 0:
                continue
                
            total_irregular_amount += amount
            
            # Add to events list
            enhanced_strategy["irregular_income_plan"]["events"].append({
                "type": event_type,
                "amount": amount,
                "date": date,
                "frequency": frequency
            })
            
            # Create deployment strategy based on event type
            deployment_plan = {}
            deployment_percentages = {}
            
            if event_type in ["bonus", "annual_bonus", "diwali_bonus"]:
                deployment_percentages = self.params["irregular_income"]["bonus_deployment"]
                deployment_plan["type"] = "bonus_deployment"
                
                # Determine staggered deployment period
                deployment_plan["deployment_schedule"] = self._create_staggered_deployment(
                    amount, event_type, date
                )
                
            elif event_type in ["windfall", "inheritance", "property_sale"]:
                deployment_percentages = self.params["irregular_income"]["windfall_deployment"]
                deployment_plan["type"] = "windfall_deployment"
                
                # Windfalls need more careful deployment
                deployment_plan["deployment_schedule"] = self._create_staggered_deployment(
                    amount, event_type, date
                )
                
                # Add tax considerations for windfalls
                if event_type == "property_sale":
                    deployment_plan["tax_considerations"] = [
                        "Consider Section 54/54F exemption for capital gains if reinvested in residential property",
                        "Explore options to invest in specified bonds under Section 54EC within 6 months",
                        "Long-term capital gains are subject to 20% tax with indexation benefits"
                    ]
                elif event_type == "inheritance":
                    deployment_plan["tax_considerations"] = [
                        "Inheritances are generally not taxable in India",
                        "Keep documentation for inherited assets to establish cost basis for future sales",
                        "Consider professional tax advice for complex inheritance situations"
                    ]
                
            elif event_type in ["seasonal_income", "business_income", "agricultural_income"]:
                # For seasonal income, focus on building buffers
                deployment_percentages = {
                    "emergency_fund": 0.30,    # 30% to emergency/buffer fund
                    "short_term_goals": 0.20,  # 20% to short-term goals
                    "long_term_goals": 0.30,   # 30% to long-term goals 
                    "discretionary": 0.10,     # 10% discretionary
                    "reinvestment": 0.10       # 10% business reinvestment
                }
                deployment_plan["type"] = "seasonal_income_deployment"
                
                # Create seasonal income strategy with buffers
                buffer_percentage = self.params["irregular_income"]["seasonal_income_buffer"]
                deployment_plan["income_volatility_buffer"] = round(amount * buffer_percentage)
                deployment_plan["deployment_schedule"] = {
                    "immediate": {
                        "amount": round(amount * (1 - buffer_percentage)),
                        "purpose": "Current goals and expenses"
                    },
                    "buffer": {
                        "amount": round(amount * buffer_percentage),
                        "purpose": "Reserve for lean periods"
                    }
                }
            
            # Apply deployment percentages to different goal categories
            time_horizon = strategy.get("time_horizon", 0)
            monthly_required = strategy.get("recommendation", {}).get("additional_monthly_required", 0)
            
            # Calculate allocated amounts
            allocated_amounts = {}
            for category, percentage in deployment_percentages.items():
                allocated_amounts[category] = round(amount * percentage)
            
            # Determine how much can be applied to this specific goal
            if time_horizon <= 2:
                # Short-term goal
                goal_allocation = allocated_amounts.get("short_term_goals", 0)
            elif time_horizon <= 7:
                # Medium-term goal
                goal_allocation = allocated_amounts.get("medium_term_goals", 
                                                      allocated_amounts.get("short_term_goals", 0) * 0.5)
            else:
                # Long-term goal
                goal_allocation = allocated_amounts.get("long_term_goals", 0)
            
            # If emergency fund goal, allocate from that category
            if strategy.get("goal_type", "").lower() == "emergency fund":
                goal_allocation = allocated_amounts.get("emergency_fund", 0)
            
            # Calculate impact on goal progress
            current_gap = strategy.get("current_status", {}).get("gap", 0)
            if current_gap > 0:
                gap_reduction_percent = min(1.0, goal_allocation / current_gap)
                months_accelerated = 0
                
                if monthly_required > 0:
                    months_accelerated = round(goal_allocation / monthly_required)
                
                deployment_plan["goal_impact"] = {
                    "allocated_to_goal": goal_allocation,
                    "gap_reduction_percent": round(gap_reduction_percent * 100, 1),
                    "timeline_acceleration_months": months_accelerated
                }
            
            # Add deployment plan to strategy
            plan_key = f"{event_type}_{len(enhanced_strategy['irregular_income_plan']['deployment_plan'])}"
            enhanced_strategy["irregular_income_plan"]["deployment_plan"][plan_key] = deployment_plan
        
        # Calculate overall impact of irregular income
        if total_irregular_amount > 0:
            monthly_required = strategy.get("recommendation", {}).get("additional_monthly_required", 0)
            monthly_contribution = strategy.get("current_status", {}).get("monthly_contribution", 0)
            total_monthly = monthly_required + monthly_contribution
            
            # Calculate equivalent months of regular contributions
            if total_monthly > 0:
                equivalent_months = round(total_irregular_amount / total_monthly)
                enhanced_strategy["irregular_income_plan"]["impact_analysis"]["equivalent_months"] = equivalent_months
                
                # Calculate potential timeline acceleration
                time_horizon = strategy.get("time_horizon", 0)
                if time_horizon > 0:
                    time_horizon_months = time_horizon * 12
                    acceleration_percent = min(100, (equivalent_months / time_horizon_months) * 100)
                    enhanced_strategy["irregular_income_plan"]["impact_analysis"]["timeline_acceleration_percent"] = round(acceleration_percent, 1)
            
            # Add overall recommendations
            enhanced_strategy["irregular_income_plan"]["recommendations"] = [
                "Use staggered deployment to minimize market timing risk",
                "Prioritize high-interest debt repayment with irregular income",
                "Create a formal irregular income deployment policy to avoid impulsive decisions",
                "Set aside a portion for tax provisions before allocating to goals"
            ]
            
            # Add specific recommendations based on event types
            event_types = [event.get("type", "").lower() for event in income_events]
            
            if any(et in ["bonus", "annual_bonus", "diwali_bonus"] for et in event_types):
                enhanced_strategy["irregular_income_plan"]["recommendations"].append(
                    "For predictable bonuses, pre-plan allocations and automate transfers when received"
                )
            
            if any(et in ["windfall", "inheritance", "property_sale"] for et in event_types):
                enhanced_strategy["irregular_income_plan"]["recommendations"].append(
                    "For large windfalls, consider engaging a financial advisor for tax-optimized deployment"
                )
            
            if any(et in ["seasonal_income", "business_income", "agricultural_income"] for et in event_types):
                enhanced_strategy["irregular_income_plan"]["recommendations"].append(
                    "For seasonal income, maintain a larger emergency buffer to smooth consumption"
                )
        
        return enhanced_strategy
    
    def _create_staggered_deployment(self, amount: float, event_type: str, date: str) -> Dict[str, Any]:
        """Create a staggered deployment schedule for lump sum amounts"""
        deployment_schedule = {}
        
        # Determine deployment period based on amount
        if amount < 1000000:  # Less than 10 lakhs
            period = self.params["irregular_income"]["staggered_deployment_periods"]["small"]
        elif amount < 5000000:  # Less than 50 lakhs
            period = self.params["irregular_income"]["staggered_deployment_periods"]["medium"]
        elif amount < 10000000:  # Less than 1 crore
            period = self.params["irregular_income"]["staggered_deployment_periods"]["large"]
        else:  # 1 crore or more
            period = self.params["irregular_income"]["staggered_deployment_periods"]["very_large"]
        
        monthly_amount = round(amount / period)
        
        # Create initial deployment
        deployment_schedule["immediate_allocation"] = {
            "amount": round(amount * 0.2),  # 20% immediately
            "purpose": "Initial deployment"
        }
        
        # Create staggered deployment
        deployment_schedule["staggered_allocation"] = {
            "amount": round(amount * 0.8),  # 80% staggered
            "monthly_amount": monthly_amount,
            "period_months": period,
            "purpose": "Staggered deployment to minimize market timing risk"
        }
        
        # Add STP recommendation for larger amounts
        if amount >= 500000:  # 5 lakhs or more
            deployment_schedule["recommended_method"] = "STP"
            deployment_schedule["stp_recommendation"] = {
                "from_instrument": "Liquid Fund or Overnight Fund",
                "to_instrument": "Balanced Advantage Fund or target asset allocation",
                "monthly_amount": monthly_amount,
                "rationale": "Reduces market timing risk while earning returns during deployment"
            }
        else:
            deployment_schedule["recommended_method"] = "Direct SIP"
        
        return deployment_schedule
    
    def analyze_scenarios(self, strategy: Dict[str, Any], parameters_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform scenario analysis to evaluate different approaches for a funding strategy.
        
        Args:
            strategy: The base funding strategy to analyze
            parameters_list: List of parameter sets defining different scenarios
            
        Returns:
            Enhanced strategy with scenario analysis results
        """
        if not strategy:
            return strategy
        
        # Clone strategy to avoid modifying original
        analyzed_strategy = dict(strategy)
        
        # Create scenario analysis section if not exists
        if "scenario_analysis" not in analyzed_strategy:
            analyzed_strategy["scenario_analysis"] = {
                "scenarios": [],
                "comparison": {},
                "recommendations": []
            }
        
        # If no parameter sets provided, use default scenarios
        if not parameters_list:
            parameters_list = [
                {"name": "Baseline", "market_condition": "baseline", "contribution_pattern": "steady"},
                {"name": "Optimistic", "market_condition": "optimistic", "contribution_pattern": "increasing"},
                {"name": "Pessimistic", "market_condition": "pessimistic", "contribution_pattern": "steady"},
                {"name": "Aggressive Saving", "market_condition": "baseline", "contribution_pattern": "increasing", 
                 "monthly_increase_factor": 0.10},  # 10% higher contributions
                {"name": "Conservative Allocation", "market_condition": "baseline", "contribution_pattern": "steady", 
                 "allocation_shift": "conservative"},
                {"name": "Extended Timeline", "market_condition": "baseline", "contribution_pattern": "steady", 
                 "time_horizon_extension": 2}  # 2 years longer
            ]
        
        # Extract base strategy parameters
        base_monthly = strategy.get("recommendation", {}).get("total_monthly_investment", 0)
        base_allocation = strategy.get("recommendation", {}).get("asset_allocation", {})
        base_time_horizon = strategy.get("time_horizon", 10)
        base_target = strategy.get("current_status", {}).get("inflation_adjusted_target", 
                                                           strategy.get("current_status", {}).get("target_amount", 0))
        base_current = strategy.get("current_status", {}).get("current_savings", 0)
        
        # Process each scenario
        for params in parameters_list:
            scenario_name = params.get("name", "Unnamed Scenario")
            scenario_result = {"name": scenario_name, "parameters": {}}
            
            # Extract scenario parameters
            market_condition = params.get("market_condition", "baseline")
            contribution_pattern = params.get("contribution_pattern", "steady")
            
            # Copy relevant parameters to result
            for key, value in params.items():
                if key != "name":
                    scenario_result["parameters"][key] = value
            
            # Get expected returns based on market condition
            expected_returns = self.params["scenario_analysis"]["market_conditions"].get(
                market_condition, self.params["scenario_analysis"]["market_conditions"]["baseline"]
            )
            
            # Adjust allocation if specified
            allocation = dict(base_allocation)
            if "allocation_shift" in params:
                allocation_shift = params["allocation_shift"]
                if allocation_shift == "conservative":
                    # Reduce equity, increase debt and cash
                    for asset in allocation:
                        if asset == "equity" or asset == "alternatives":
                            allocation[asset] = max(0, allocation[asset] - 0.15)
                        elif asset == "debt" or asset == "cash":
                            allocation[asset] = min(1.0, allocation[asset] + 0.1)
                elif allocation_shift == "aggressive":
                    # Increase equity, reduce debt and cash
                    for asset in allocation:
                        if asset == "equity":
                            allocation[asset] = min(0.9, allocation[asset] + 0.15)
                        elif asset == "debt" or asset == "cash":
                            allocation[asset] = max(0, allocation[asset] - 0.1)
            
            # Calculate portfolio expected return based on allocation
            portfolio_return = 0
            for asset, percentage in allocation.items():
                if asset in expected_returns:
                    portfolio_return += percentage * expected_returns[asset]
            
            # Adjust monthly contribution based on pattern
            monthly_factor = 1.0
            if contribution_pattern == "increasing":
                monthly_factor = 1.0 + self.params["scenario_analysis"]["contribution_patterns"]["increasing"]
            elif contribution_pattern == "decreasing":
                monthly_factor = 1.0 + self.params["scenario_analysis"]["contribution_patterns"]["decreasing"]
            
            # Apply explicit monthly adjustment if specified
            if "monthly_increase_factor" in params:
                monthly_factor = 1.0 + params["monthly_increase_factor"]
            
            monthly_contribution = base_monthly * monthly_factor
            
            # Adjust time horizon if specified
            time_horizon = base_time_horizon
            if "time_horizon_extension" in params:
                time_horizon += params["time_horizon_extension"]
            elif "time_horizon_reduction" in params:
                time_horizon = max(1, base_time_horizon - params["time_horizon_reduction"])
            
            # Calculate future value based on parameters
            future_value = self._calculate_future_value(
                base_current, monthly_contribution, time_horizon, portfolio_return, contribution_pattern
            )
            
            # Calculate success metrics
            goal_achievement_ratio = future_value / base_target if base_target > 0 else 0
            goal_achieved = future_value >= base_target
            
            # Determine confidence level
            confidence_thresholds = self.params["scenario_analysis"]["confidence_thresholds"]
            confidence_level = "low"
            if goal_achievement_ratio >= confidence_thresholds["high"]:
                confidence_level = "high"
            elif goal_achievement_ratio >= confidence_thresholds["medium"]:
                confidence_level = "medium"
            
            # Store calculated results
            scenario_result["calculations"] = {
                "expected_portfolio_return": round(portfolio_return * 100, 2),
                "monthly_contribution": round(monthly_contribution),
                "projected_future_value": round(future_value),
                "goal_achievement_ratio": round(goal_achievement_ratio * 100, 1),
                "goal_achieved": goal_achieved,
                "confidence_level": confidence_level
            }
            
            # Add recommendations specific to this scenario
            scenario_result["recommendations"] = []
            
            if goal_achieved:
                scenario_result["recommendations"].append(
                    f"This scenario successfully meets the goal target with {round(goal_achievement_ratio * 100, 1)}% achievement."
                )
                if goal_achievement_ratio > 1.2:
                    scenario_result["recommendations"].append(
                        "Consider reducing monthly contributions or achieving the goal sooner."
                    )
            else:
                shortfall_percent = round((1 - goal_achievement_ratio) * 100, 1)
                scenario_result["recommendations"].append(
                    f"This scenario falls short of the goal target by {shortfall_percent}%."
                )
                
                # Suggest adjustments
                if time_horizon < base_time_horizon + 3:
                    scenario_result["recommendations"].append(
                        f"Consider extending the timeline by {round(shortfall_percent / 10)} years to meet the goal."
                    )
                
                if monthly_contribution < base_monthly * 1.3:
                    required_increase = round((base_target - future_value) / (monthly_contribution * time_horizon * 12), 2)
                    scenario_result["recommendations"].append(
                        f"Consider increasing monthly contribution by {round(required_increase * 100)}% to meet the goal."
                    )
            
            # Add to scenarios list
            analyzed_strategy["scenario_analysis"]["scenarios"].append(scenario_result)
        
        # Create comparison summary across scenarios
        scenarios = analyzed_strategy["scenario_analysis"]["scenarios"]
        if scenarios:
            # Find best performing scenario
            best_scenario = max(scenarios, key=lambda s: s["calculations"]["goal_achievement_ratio"])
            
            # Find most efficient scenario (highest ratio of goal achievement to contribution)
            most_efficient = max(scenarios, 
                               key=lambda s: s["calculations"]["goal_achievement_ratio"] / 
                                           (s["calculations"]["monthly_contribution"] / base_monthly))
            
            # Find lowest risk scenario that still achieves goal
            achieving_scenarios = [s for s in scenarios if s["calculations"]["goal_achieved"]]
            lowest_risk_success = None
            if achieving_scenarios:
                lowest_risk_success = min(achieving_scenarios, 
                                        key=lambda s: s["calculations"]["expected_portfolio_return"])
            
            # Build comparison summary
            analyzed_strategy["scenario_analysis"]["comparison"] = {
                "best_performing": best_scenario["name"],
                "most_efficient": most_efficient["name"],
                "lowest_risk_success": lowest_risk_success["name"] if lowest_risk_success else "None",
                "percentage_of_successful_scenarios": round(len([s for s in scenarios if s["calculations"]["goal_achieved"]]) / len(scenarios) * 100)
            }
            
            # Generate overall recommendations
            analyzed_strategy["scenario_analysis"]["recommendations"] = []
            
            # Start with the recommended scenario
            recommended_scenario = most_efficient
            if most_efficient["calculations"]["goal_achievement_ratio"] < 85:
                # If most efficient scenario isn't close enough, recommend best performer
                recommended_scenario = best_scenario
            
            analyzed_strategy["scenario_analysis"]["recommendations"].append(
                f"Recommended approach: {recommended_scenario['name']} scenario."
            )
            
            # Add key insights
            if recommended_scenario["calculations"]["goal_achieved"]:
                analyzed_strategy["scenario_analysis"]["recommendations"].append(
                    f"This approach achieves {round(recommended_scenario['calculations']['goal_achievement_ratio'])}% of the goal target with ₹{recommended_scenario['calculations']['monthly_contribution']:,} monthly investment."
                )
            else:
                analyzed_strategy["scenario_analysis"]["recommendations"].append(
                    f"Even the recommended approach only achieves {round(recommended_scenario['calculations']['goal_achievement_ratio'])}% of the goal. Consider adjusting your target amount or timeline."
                )
            
            # Add market sensitivity insight
            baseline = next((s for s in scenarios if s["name"] == "Baseline"), scenarios[0])
            optimistic = next((s for s in scenarios if s["name"] == "Optimistic"), None)
            pessimistic = next((s for s in scenarios if s["name"] == "Pessimistic"), None)
            
            if optimistic and pessimistic:
                variance = (optimistic["calculations"]["goal_achievement_ratio"] - 
                           pessimistic["calculations"]["goal_achievement_ratio"])
                
                if variance > 0.5:  # More than 50% difference
                    analyzed_strategy["scenario_analysis"]["recommendations"].append(
                        "This goal is highly sensitive to market conditions. Consider a more conservative allocation to reduce volatility."
                    )
                elif variance < 0.2:  # Less than 20% difference
                    analyzed_strategy["scenario_analysis"]["recommendations"].append(
                        "This goal shows low sensitivity to market conditions, indicating a robust strategy."
                    )
            
            # Add contribution pattern insight
            aggressive_saving = next((s for s in scenarios if s["name"] == "Aggressive Saving"), None)
            if aggressive_saving and not baseline["calculations"]["goal_achieved"] and aggressive_saving["calculations"]["goal_achieved"]:
                analyzed_strategy["scenario_analysis"]["recommendations"].append(
                    "Increasing your contributions over time significantly improves your chances of success."
                )
            
            # Add timeline insight
            extended = next((s for s in scenarios if s["name"] == "Extended Timeline"), None)
            if extended and not baseline["calculations"]["goal_achieved"] and extended["calculations"]["goal_achieved"]:
                analyzed_strategy["scenario_analysis"]["recommendations"].append(
                    f"Extending your timeline by {params.get('time_horizon_extension', 2)} years dramatically improves feasibility."
                )
        
        return analyzed_strategy
    
    def _calculate_future_value(self, current_savings: float, monthly_contribution: float, 
                              time_horizon: float, annual_return: float, contribution_pattern: str) -> float:
        """Calculate future value based on parameters and contribution patterns"""
        # Convert annual return to monthly
        monthly_return = (1 + annual_return) ** (1/12) - 1
        
        # Calculate how current savings will grow
        future_value_current = current_savings * ((1 + annual_return) ** time_horizon)
        
        # Calculate future value of contributions based on pattern
        months = time_horizon * 12
        
        if contribution_pattern == "steady":
            # Standard future value of periodic payments formula
            if monthly_return > 0:
                future_value_contributions = monthly_contribution * ((((1 + monthly_return) ** months) - 1) / monthly_return)
            else:
                future_value_contributions = monthly_contribution * months
                
        elif contribution_pattern == "increasing":
            # For increasing contributions, simulate month by month
            future_value_contributions = 0
            annual_increase = self.params["scenario_analysis"]["contribution_patterns"]["increasing"]
            
            current_monthly = monthly_contribution
            for m in range(int(months)):
                # Apply annual increase every 12 months
                if m > 0 and m % 12 == 0:
                    current_monthly *= (1 + annual_increase)
                
                # Add this month's contribution and grow everything
                future_value_contributions = (future_value_contributions + current_monthly) * (1 + monthly_return)
                
        elif contribution_pattern == "decreasing":
            # For decreasing contributions, simulate month by month
            future_value_contributions = 0
            annual_decrease = abs(self.params["scenario_analysis"]["contribution_patterns"]["decreasing"])
            
            current_monthly = monthly_contribution
            for m in range(int(months)):
                # Apply annual decrease every 12 months
                if m > 0 and m % 12 == 0:
                    current_monthly *= (1 - annual_decrease)
                
                # Add this month's contribution and grow everything
                future_value_contributions = (future_value_contributions + current_monthly) * (1 + monthly_return)
        else:
            # Default to steady contributions
            if monthly_return > 0:
                future_value_contributions = monthly_contribution * ((((1 + monthly_return) ** months) - 1) / monthly_return)
            else:
                future_value_contributions = monthly_contribution * months
        
        # Total future value
        return future_value_current + future_value_contributions
    
    def _calculate_expected_return(self, allocation: Dict[str, float]) -> float:
        """Calculate expected return based on asset allocation"""
        baseline_returns = self.params["scenario_analysis"]["market_conditions"]["baseline"]
        expected_return = 0
        
        for asset, percentage in allocation.items():
            if asset in baseline_returns:
                expected_return += percentage * baseline_returns[asset]
        
        return round(expected_return * 100, 2)