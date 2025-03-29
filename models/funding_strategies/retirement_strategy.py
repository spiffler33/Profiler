import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class RetirementFundingStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for retirement goals with
    India-specific retirement planning concepts.
    """
    
    def __init__(self):
        """Initialize with retirement-specific parameters"""
        super().__init__()
        
        # Additional retirement-specific parameters
        self.retirement_params = {
            "life_expectancy": 85,
            "withdrawal_rate": 0.04,  # 4% safe withdrawal rate
            "nps_allocation": {
                "equity_cap": 0.75,
                "auto_decrease": True  # Auto decrease equity as retirement approaches
            },
            "annuity_rates": {
                "current": 0.065,  # Current annuity rate of 6.5%
                "projected": 0.06   # Projected average rate for planning
            },
            "pension_schemes": {
                "nps": {
                    "min_contribution": 6000,  # Minimum annual
                    "max_tax_benefit": 50000,  # 80CCD(1B) limit
                    "employer_contribution_limit": 750000  # 10% of salary up to this
                },
                "atal_pension": {
                    "max_age": 40,
                    "min_contribution": 210,  # Monthly
                    "max_pension": 5000       # Monthly
                }
            },
            "tax_benefits": {
                "80c_limit": 150000,
                "80ccd_1b": 50000,
                "health_insurance": 25000,
                "medical_expenses": 50000
            }
        }
        
        # Load retirement-specific parameters
        self._load_retirement_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the StrategyOptimizer instance if not already initialized"""
        super()._initialize_optimizer()
        
    def _initialize_constraints(self):
        """Initialize the FundingConstraints instance if not already initialized"""
        super()._initialize_constraints()
        
    def _initialize_compound_strategy(self):
        """Initialize the CompoundStrategy instance if not already initialized"""
        super()._initialize_compound_strategy()
        
    def _load_retirement_parameters(self):
        """Load retirement-specific parameters from service"""
        if self.param_service:
            try:
                # Load life expectancy
                life_expectancy = self.param_service.get_parameter('life_expectancy')
                if life_expectancy:
                    self.retirement_params['life_expectancy'] = life_expectancy
                
                # Load withdrawal rate
                withdrawal = self.param_service.get_parameter('retirement_withdrawal_rate')
                if withdrawal:
                    self.retirement_params['withdrawal_rate'] = withdrawal
                
                # Load NPS parameters
                nps = self.param_service.get_parameter('nps_allocation')
                if nps:
                    self.retirement_params['nps_allocation'].update(nps)
                
                # Load annuity rates
                annuity = self.param_service.get_parameter('annuity_rates')
                if annuity:
                    self.retirement_params['annuity_rates'].update(annuity)
                
                # Load pension scheme details
                pension = self.param_service.get_parameter('pension_schemes')
                if pension:
                    self.retirement_params['pension_schemes'].update(pension)
                
                # Load tax benefits
                tax = self.param_service.get_parameter('retirement_tax_benefits')
                if tax:
                    self.retirement_params['tax_benefits'].update(tax)
                
            except Exception as e:
                logger.error(f"Error loading retirement parameters: {e}")
                # Continue with default parameters
    
    def calculate_retirement_corpus(self, current_age, retirement_age, 
                                    monthly_expenses, inflation_rate=None):
        """
        Calculate required retirement corpus based on expenses and life expectancy.
        
        Args:
            current_age: Current age in years
            retirement_age: Expected retirement age
            monthly_expenses: Current monthly expenses
            inflation_rate: Annual inflation rate (default from params)
            
        Returns:
            Required retirement corpus
        """
        if inflation_rate is None:
            inflation_rate = self.params['inflation_rate']
            
        # Calculate years to retirement
        years_to_retirement = retirement_age - current_age
        
        # Calculate years in retirement (life expectancy - retirement age)
        life_expectancy = self.retirement_params['life_expectancy']
        years_in_retirement = life_expectancy - retirement_age
        
        # Calculate monthly expenses at retirement (adjusted for inflation)
        expenses_at_retirement = monthly_expenses * (
            (1 + inflation_rate) ** years_to_retirement
        )
        
        # Annual expenses at retirement
        annual_expenses_at_retirement = expenses_at_retirement * 12
        
        # Calculate required corpus using safe withdrawal rate
        # Formula: Annual Expenses / Safe Withdrawal Rate
        withdrawal_rate = self.retirement_params['withdrawal_rate']
        required_corpus = annual_expenses_at_retirement / withdrawal_rate
        
        return required_corpus
    
    def analyze_retirement_gap(self, current_age, retirement_age, monthly_expenses,
                               current_savings, monthly_contribution, expected_return=None):
        """
        Analyze retirement preparedness gap and projected shortfall.
        
        Args:
            current_age: Current age in years
            retirement_age: Expected retirement age
            monthly_expenses: Current monthly expenses
            current_savings: Current retirement savings
            monthly_contribution: Current monthly contribution to retirement
            expected_return: Expected annual return (default based on moderate allocation)
            
        Returns:
            Dictionary with gap analysis details
        """
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # Get expected return if not provided
        if expected_return is None:
            # Determine allocation based on years to retirement
            allocation = self.recommend_allocation(years_to_retirement, 'moderate')
            expected_return = self.get_expected_return(allocation)
        
        # Calculate required retirement corpus
        required_corpus = self.calculate_retirement_corpus(
            current_age, retirement_age, monthly_expenses
        )
        
        # Calculate future value of current savings
        future_value_of_current = current_savings * (
            (1 + expected_return) ** years_to_retirement
        )
        
        # Calculate future value of monthly contributions
        future_value_of_monthly = 0
        if monthly_contribution > 0 and years_to_retirement > 0:
            # Convert to monthly rate
            monthly_rate = expected_return / 12
            months = years_to_retirement * 12
            
            # Formula for future value of periodic payments
            future_value_of_monthly = monthly_contribution * (
                ((1 + monthly_rate) ** months - 1) / monthly_rate
            )
        
        # Calculate gap
        total_projected = future_value_of_current + future_value_of_monthly
        gap = required_corpus - total_projected
        
        # Calculate required additional monthly investment
        required_monthly = 0
        if gap > 0:
            required_monthly = self.calculate_monthly_investment(
                gap, years_to_retirement, expected_return
            )
        
        # Calculate percentage funded
        percent_funded = (total_projected / required_corpus * 100) if required_corpus > 0 else 0
        
        return {
            'required_corpus': round(required_corpus),
            'years_to_retirement': years_to_retirement,
            'current_status': {
                'current_savings': current_savings,
                'monthly_contribution': monthly_contribution,
                'projected_corpus': round(total_projected),
                'gap': round(gap) if gap > 0 else 0,
                'percent_funded': round(percent_funded, 1)
            },
            'recommendation': {
                'additional_monthly_required': round(required_monthly) if required_monthly > 0 else 0,
                'total_monthly_investment': round(monthly_contribution + required_monthly) 
            }
        }
    
    def recommend_retirement_asset_allocation(self, current_age, retirement_age, risk_profile='moderate'):
        """
        Recommend asset allocation specifically for retirement goal.
        
        Args:
            current_age: Current age in years
            retirement_age: Expected retirement age
            risk_profile: Risk tolerance level
            
        Returns:
            Dictionary with recommended asset allocation
        """
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # Use base allocation as starting point
        allocation = self.recommend_allocation(years_to_retirement, risk_profile)
        
        # Adjust for retirement-specific strategy
        if years_to_retirement > 20:
            # For very long horizons, increase equity slightly for retirement
            allocation['equity'] = min(allocation['equity'] * 1.1, 0.80)
            allocation['alternatives'] = min(allocation.get('alternatives', 0) + 0.05, 0.10)
            
            # Adjust other allocations to maintain total of 1.0
            total = sum(allocation.values())
            if total > 1.0:
                # Scale down debt first
                excess = total - 1.0
                if allocation.get('debt', 0) > excess:
                    allocation['debt'] -= excess
                else:
                    # Scale down proportionally if needed
                    for asset in allocation:
                        allocation[asset] = allocation[asset] / total
                        
        elif years_to_retirement < 5:
            # For near retirement, ensure sufficient stability
            if allocation['equity'] > 0.4:
                allocation['equity'] = 0.4
                allocation['debt'] = 0.5
                allocation['cash'] = 0.05
                allocation['gold'] = 0.05
        
        return allocation
    
    def recommend_nps_allocation(self, current_age, retirement_age, risk_profile='moderate', tax_bracket=None):
        """
        Recommend allocation within National Pension System (NPS) with optimized tax efficiency.
        
        Args:
            current_age: Current age in years
            retirement_age: Expected retirement age
            risk_profile: Risk profile of the investor (conservative, moderate, aggressive)
            tax_bracket: Income tax bracket (decimal). If None, highest bracket used.
            
        Returns:
            Dictionary with recommended NPS allocation percentages and tax benefits
        """
        # Initialize optimizer if needed
        self._initialize_optimizer()
        
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # NPS has three asset classes: E (equity), C (corporate debt), G (govt bonds)
        allocation = {'E': 0, 'C': 0, 'G': 0}
        
        # Max equity cap
        max_equity = self.retirement_params['nps_allocation']['equity_cap']
        
        # Base allocation strategy
        if years_to_retirement > 20:
            allocation['E'] = max_equity
            allocation['C'] = 0.20
            allocation['G'] = 1.0 - allocation['E'] - allocation['C']
            
        elif years_to_retirement > 10:
            allocation['E'] = max_equity * 0.8  # 80% of max
            allocation['C'] = 0.25
            allocation['G'] = 1.0 - allocation['E'] - allocation['C']
            
        elif years_to_retirement > 5:
            allocation['E'] = max_equity * 0.6  # 60% of max
            allocation['C'] = 0.25
            allocation['G'] = 1.0 - allocation['E'] - allocation['C']
            
        else:
            allocation['E'] = max_equity * 0.3  # 30% of max
            allocation['C'] = 0.20
            allocation['G'] = 1.0 - allocation['E'] - allocation['C']
        
        # Apply risk profile adjustments
        if risk_profile == 'conservative':
            # Reduce equity allocation for conservative investors
            equity_reduction = 0.15
            allocation['E'] = max(0.1, allocation['E'] - equity_reduction)
            allocation['G'] += equity_reduction
            
        elif risk_profile == 'aggressive':
            # Increase equity allocation for aggressive investors (up to max)
            equity_boost = 0.10
            allocation['E'] = min(max_equity, allocation['E'] + equity_boost)
            # Reduce G to accommodate more equity, maintaining C
            remaining = 1.0 - allocation['E'] - allocation['C']
            allocation['G'] = max(0.1, remaining)  # Ensure minimum 10% in G
            
            # If G went below minimum, adjust C
            if allocation['G'] < 0.1:
                allocation['G'] = 0.1
                allocation['C'] = 1.0 - allocation['E'] - allocation['G']
        
        # Calculate tax benefits
        tax_benefits = self._calculate_nps_tax_benefits(allocation, tax_bracket)
        
        # Combine allocation with tax benefits
        result = {
            'allocation': allocation,
            'tax_benefits': tax_benefits
        }
        
        return result
        
    def _calculate_nps_tax_benefits(self, allocation, tax_bracket=None):
        """
        Calculate tax benefits for NPS investments
        
        Args:
            allocation: NPS allocation percentages
            tax_bracket: Income tax bracket (decimal). If None, highest bracket used.
            
        Returns:
            Dictionary with tax benefit details
        """
        if tax_bracket is None:
            tax_bracket = self.params['tax_rates']['income_tax']['default']
            
        # Get section limits
        section_80c_limit = self.params['tax_optimization']['section_80c_limit'] if hasattr(self, 'params') and 'tax_optimization' in self.params else 150000
        section_80ccd_limit = self.params['tax_optimization']['section_80ccd_limit'] if hasattr(self, 'params') and 'tax_optimization' in self.params else 50000
        
        # Calculate tax benefit under Section 80CCD(1) - part of 80C
        benefit_80c = min(section_80c_limit, 150000) * tax_bracket
        
        # Calculate additional tax benefit under Section 80CCD(1B)
        benefit_80ccd = min(section_80ccd_limit, 50000) * tax_bracket
        
        # Total benefit
        total_benefit = benefit_80c + benefit_80ccd
        
        return {
            'section_80c': round(benefit_80c),
            'section_80ccd': round(benefit_80ccd),
            'total_annual_benefit': round(total_benefit),
            'effective_rate_of_return_boost': round(total_benefit / (section_80c_limit + section_80ccd_limit) * 100, 2) if (section_80c_limit + section_80ccd_limit) > 0 else 0
        }
    
    def calculate_annuity_income(self, corpus, annuity_rate=None):
        """
        Calculate monthly income from annuity using a retirement corpus.
        
        Args:
            corpus: Retirement corpus amount
            annuity_rate: Annuity rate (default from params)
            
        Returns:
            Expected monthly income from annuity
        """
        if annuity_rate is None:
            annuity_rate = self.retirement_params['annuity_rates']['projected']
            
        # Assuming annuity rate is annual, convert to monthly
        monthly_income = corpus * annuity_rate / 12
        
        return monthly_income
    
    def analyze_pension_options(self, goal_data):
        """
        Analyze different pension options for retirement income.
        
        Args:
            goal_data: Dictionary with retirement goal details
            
        Returns:
            Dictionary with pension analysis and recommendations
        """
        current_age = goal_data.get('current_age', 30)
        retirement_age = goal_data.get('retirement_age', 60)
        monthly_expenses = goal_data.get('monthly_expenses', 50000)
        current_savings = goal_data.get('current_savings', 0)
        annual_income = goal_data.get('annual_income', 1200000)
        
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # Calculate required corpus
        required_corpus = self.calculate_retirement_corpus(
            current_age, retirement_age, monthly_expenses
        )
        
        # Analyze NPS option
        nps_analysis = {}
        if current_age < 60:  # NPS available until 60
            # Recommended annual NPS contribution (10% of annual income)
            recommended_nps = min(annual_income * 0.1, 
                                 self.retirement_params['pension_schemes']['nps']['max_tax_benefit'])
            
            # Tax benefit calculation
            tax_benefit = self.estimate_tax_benefit(recommended_nps)
            
            # Projected NPS corpus 
            nps_returns = (self.params['expected_returns']['equity'] * 0.6 + 
                          self.params['expected_returns']['debt'] * 0.4)  # Assumed 60:40 allocation
            
            projected_nps_corpus = recommended_nps * (
                ((1 + nps_returns) ** years_to_retirement - 1) / nps_returns
            ) * (1 + nps_returns)
            
            # Annuity income (60% of corpus goes to annuity)
            annuity_corpus = projected_nps_corpus * 0.6
            monthly_annuity = self.calculate_annuity_income(annuity_corpus)
            
            # Lump sum (40% tax-free)
            lump_sum = projected_nps_corpus * 0.4
            
            nps_analysis = {
                'recommended_annual_contribution': round(recommended_nps),
                'tax_benefit': round(tax_benefit),
                'projected_corpus': round(projected_nps_corpus),
                'annuity_income': round(monthly_annuity),
                'tax_free_lump_sum': round(lump_sum),
                'contribution_as_percent_of_income': round(recommended_nps / annual_income * 100, 1)
            }
        
        # Analyze Atal Pension Yojana option
        apy_analysis = {}
        if current_age < self.retirement_params['pension_schemes']['atal_pension']['max_age']:
            # APY provides fixed pension based on contribution
            # Simple calculation based on current age
            years_to_contribute = min(retirement_age, 60) - current_age
            
            # Estimate monthly contribution for max pension
            if years_to_contribute >= 20:
                monthly_contribution = 210  # Minimum for age < 30
            elif years_to_contribute >= 10:
                monthly_contribution = 400  # Approximate for age 30-40
            else:
                monthly_contribution = 700  # Approximate for age 40-50
            
            # Max pension is fixed
            max_pension = self.retirement_params['pension_schemes']['atal_pension']['max_pension']
            
            apy_analysis = {
                'eligible': True,
                'monthly_contribution': monthly_contribution,
                'guaranteed_pension': max_pension,
                'annual_contribution': monthly_contribution * 12,
                'percent_of_expenses_covered': round(max_pension / monthly_expenses * 100, 1)
            }
        else:
            apy_analysis = {
                'eligible': False,
                'message': f"Age exceeds maximum eligibility age of {self.retirement_params['pension_schemes']['atal_pension']['max_age']}"
            }
        
        # Analyze traditional retirement funds
        traditional_analysis = {
            'required_monthly_savings': round(self.calculate_monthly_investment(
                required_corpus - (projected_nps_corpus if 'projected_corpus' in nps_analysis else 0),
                years_to_retirement,
                self.get_expected_return(self.recommend_allocation(years_to_retirement))
            )),
            'allocation': self.recommend_retirement_asset_allocation(current_age, retirement_age),
            'recommended_instruments': [
                'Equity mutual funds for long-term growth',
                'Debt funds for stability',
                'PPF for tax-free guaranteed returns',
                'Senior Citizen Saving Scheme (post-retirement)'
            ]
        }
        
        return {
            'required_corpus': round(required_corpus),
            'years_to_retirement': years_to_retirement,
            'nps_analysis': nps_analysis,
            'apy_analysis': apy_analysis,
            'traditional_investments': traditional_analysis,
            'portfolio_recommendation': {
                'nps_percent': 20,  # Recommended allocation to NPS
                'traditional_percent': 80,  # Remaining to traditional investments
                'nps_allocation': self.recommend_nps_allocation(current_age, retirement_age),
                'remarks': [
                    'NPS offers tax benefits but has lock-in until retirement',
                    'Consider maxing out NPS contribution for tax benefits under 80CCD(1B)',
                    'Traditional investments provide more flexibility and liquidity',
                    'Rebalance portfolio as retirement approaches to reduce risk'
                ]
            }
        }
    
    def recommend_retirement_income_strategy(self, goal_data):
        """
        Recommend income strategy for post-retirement phase.
        
        Args:
            goal_data: Dictionary with retirement goal details
            
        Returns:
            Dictionary with retirement income strategy
        """
        current_age = goal_data.get('current_age', 30)
        retirement_age = goal_data.get('retirement_age', 60)
        monthly_expenses = goal_data.get('monthly_expenses', 50000)
        expected_corpus = goal_data.get('expected_corpus')
        
        if not expected_corpus:
            # Calculate if not provided
            expected_corpus = self.calculate_retirement_corpus(
                current_age, retirement_age, monthly_expenses
            )
        
        # Withdraw phases
        # 1. Immediate needs (0-5 years) - Stable and liquid
        # 2. Mid-term (5-15 years) - Balanced growth
        # 3. Long-term (15+ years) - Growth focused
        
        # Allocation strategy
        bucket_strategy = {
            'immediate_bucket': {
                'allocation': round(expected_corpus * 0.25),  # 25% for first 5 years
                'instruments': {
                    'senior_citizen_fd': 0.4,
                    'liquid_funds': 0.2,
                    'short_term_debt': 0.3,
                    'arbitrage_funds': 0.1
                },
                'expected_return': 6.5,
                'withdrawal_strategy': 'Systematic Withdrawal Plan from liquid/short-term funds'
            },
            'mid_term_bucket': {
                'allocation': round(expected_corpus * 0.35),  # 35% for next 10 years
                'instruments': {
                    'balanced_funds': 0.3,
                    'debt_funds': 0.3,
                    'monthly_income_plans': 0.3,
                    'index_funds': 0.1
                },
                'expected_return': 8.0,
                'withdrawal_strategy': 'Leave untouched for first 5 years, then start systematic withdrawals'
            },
            'long_term_bucket': {
                'allocation': round(expected_corpus * 0.40),  # 40% for long-term
                'instruments': {
                    'diversified_equity': 0.5,
                    'index_funds': 0.3,
                    'value_funds': 0.2
                },
                'expected_return': 10.0,
                'withdrawal_strategy': 'No withdrawals for first 10 years, then systematic withdrawals'
            }
        }
        
        # Annuity considerations
        annuity_analysis = {
            'recommended_allocation': round(expected_corpus * 0.2),  # 20% to annuities
            'expected_monthly_income': round(self.calculate_annuity_income(
                expected_corpus * 0.2
            )),
            'annuity_types': [
                'Immediate annuity for guaranteed lifelong income',
                'Increasing annuity to counter inflation'
            ],
            'considerations': [
                'Annuities provide income security but have no legacy value',
                'Returns are generally lower than market investments',
                'Consider purchasing annuities in phases rather than all at once'
            ]
        }
        
        # Tax planning
        tax_planning = {
            'strategies': [
                'Utilize tax-free withdrawal limit from NPS (40% of corpus)',
                'Systematic withdrawals from equity funds after 1 year for LTCG benefits',
                'Debt fund withdrawals after 3 years for indexation benefits',
                'Utilize basic exemption limit and senior citizen benefits'
            ],
            'senior_citizen_benefits': {
                'additional_deduction': 50000,  # Medical insurance deduction
                'savings_interest_deduction': 50000,  # Interest income deduction for seniors
                'basic_exemption': 300000  # Basic exemption for senior citizens
            }
        }
        
        return {
            'monthly_income_requirement': round(monthly_expenses),
            'bucket_strategy': bucket_strategy,
            'annuity_analysis': annuity_analysis,
            'tax_planning': tax_planning,
            'rebalancing_strategy': {
                'frequency': 'Annual',
                'method': 'Refill immediate bucket from mid-term, and mid-term from long-term',
                'sequence_of_withdrawals': [
                    'Interest/dividends first',
                    'Debt funds/FDs next',
                    'Equity funds last to allow maximum growth'
                ]
            }
        }
    
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy tailored for retirement goals.
        
        Retirement strategies require dynamic rebalancing that gradually becomes
        more conservative as the retirement date approaches. The strategy implements
        age-based thresholds and considers the long time horizon typical of retirement goals.
        
        Args:
            goal_data: Dictionary with retirement goal details
            profile_data: Dictionary with user profile information
            
        Returns:
            Dictionary with retirement-specific rebalancing strategy
        """
        # Create rebalancing instance
        rebalancing = RebalancingStrategy()
        
        # Extract retirement-specific information
        current_age = goal_data.get('current_age', 30)
        retirement_age = goal_data.get('retirement_age', 60)
        current_savings = goal_data.get('current_savings', 0)
        
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # If profile data not provided, create minimal profile
        if not profile_data:
            profile_data = {
                'risk_profile': goal_data.get('risk_profile', 'moderate'),
                'portfolio_value': current_savings,
                'market_volatility': 'normal'
            }
        
        # Get retirement-specific asset allocation
        allocation = self.recommend_retirement_asset_allocation(
            current_age, retirement_age, goal_data.get('risk_profile', 'moderate')
        )
        
        # Create goal data specifically for rebalancing
        rebalancing_goal = {
            'goal_type': 'retirement',
            'time_horizon': years_to_retirement,
            'target_allocation': allocation,
            'current_allocation': goal_data.get('current_allocation', allocation),
            'priority_level': 'medium'  # Typically medium priority (behind emergency funds)
        }
        
        # Design rebalancing schedule
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(
            rebalancing_goal, profile_data
        )
        
        # Calculate age-based drift thresholds
        # More aggressive when young, more conservative near retirement
        age_based_threshold_factor = 1.0
        if years_to_retirement > 20:
            age_based_threshold_factor = 1.4  # 40% wider thresholds when far from retirement
        elif years_to_retirement > 10:
            age_based_threshold_factor = 1.2  # 20% wider thresholds when moderately far
        elif years_to_retirement > 5:
            age_based_threshold_factor = 1.0  # Standard thresholds
        else:
            age_based_threshold_factor = 0.8  # 20% tighter thresholds when close to retirement
        
        # Customize drift thresholds for retirement strategy
        custom_thresholds = {
            'equity': 0.05 * age_based_threshold_factor,
            'debt': 0.03 * age_based_threshold_factor,
            'gold': 0.02 * age_based_threshold_factor,
            'alternatives': 0.07 * age_based_threshold_factor,
            'cash': 0.01 * age_based_threshold_factor
        }
        
        drift_thresholds = rebalancing.calculate_drift_thresholds(custom_thresholds)
        
        # Create retirement-specific rebalancing strategy
        retirement_rebalancing = {
            'goal_type': 'retirement',
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': drift_thresholds,
            'age_based_factors': {
                'current_age': current_age,
                'retirement_age': retirement_age,
                'years_to_retirement': years_to_retirement,
                'threshold_factor': age_based_threshold_factor,
                'adjustment_frequency': '2 years'  # How often to adjust allocation based on age
            },
            'retirement_specific_considerations': {
                'bucket_approach': 'Three-bucket strategy for retirement phase',
                'age_based_adjustments': 'Gradually decrease risk exposure as retirement approaches',
                'tax_efficiency': 'Focus on tax-efficient rebalancing to minimize capital gains'
            },
            'implementation_priorities': [
                'Gradual reduction in equity exposure as retirement approaches',
                'Tax-efficient rebalancing to minimize capital gains taxes',
                'Use of new contributions for most rebalancing needs',
                'Periodic reassessment of risk tolerance and retirement timeline'
            ]
        }
        
        # Add retirement bucket strategy in final years
        if years_to_retirement < 10:
            retirement_rebalancing['bucket_strategy'] = {
                'immediate_bucket': {
                    'allocation': 0.25,  # 25% for first few years of retirement
                    'holdings': ['cash', 'liquid_funds', 'short_term_debt'],
                    'rebalancing_approach': 'Minimal - maintain liquidity for immediate needs'
                },
                'intermediate_bucket': {
                    'allocation': 0.35,  # 35% for years 3-10 of retirement
                    'holdings': ['balanced_funds', 'debt_funds', 'income_funds'],
                    'rebalancing_approach': 'Conservative - annual with tight thresholds'
                },
                'growth_bucket': {
                    'allocation': 0.40,  # 40% for long-term growth
                    'holdings': ['equity_funds', 'index_funds', 'dividend_funds'],
                    'rebalancing_approach': 'Moderate - annual with standard thresholds'
                }
            }
        
        return retirement_rebalancing
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive retirement funding strategy with optimization.
        
        Args:
            goal_data: Dictionary with retirement goal details
            
        Returns:
            Dictionary with comprehensive retirement strategy
        """
        # Initialize utility classes if needed
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # Extract retirement-specific information
        current_age = goal_data.get('current_age', 30)
        retirement_age = goal_data.get('retirement_age', 60)
        monthly_expenses = goal_data.get('monthly_expenses', 50000)
        inflation_rate = goal_data.get('inflation_rate', self.params['inflation_rate'])
        risk_profile = goal_data.get('risk_profile', 'moderate')
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        annual_income = goal_data.get('annual_income', 1200000)  # Default to 12L if not provided
        tax_bracket = goal_data.get('tax_bracket', None)
        irregular_income_details = goal_data.get('irregular_income', {})
        
        # Years to retirement
        years_to_retirement = retirement_age - current_age
        
        # Calculate target amount (required corpus)
        target_amount = self.calculate_retirement_corpus(
            current_age, retirement_age, monthly_expenses, inflation_rate
        )
        
        # Create goal data with calculated target
        retirement_goal = {
            'goal_type': 'retirement',
            'target_amount': target_amount,
            'time_horizon': years_to_retirement,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution,
            'current_age': current_age,
            'retirement_age': retirement_age,
            'monthly_expenses': monthly_expenses,
            'annual_income': annual_income
        }
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(retirement_goal)
        
        # Enhanced with retirement-specific analysis
        retirement_gap = self.analyze_retirement_gap(
            current_age, retirement_age, monthly_expenses,
            current_savings, monthly_contribution
        )
        
        pension_options = self.analyze_pension_options(retirement_goal)
        
        # Get NPS allocation with tax benefits
        nps_details = self.recommend_nps_allocation(
            current_age, retirement_age, risk_profile, tax_bracket
        )
        
        # Only include income strategy if near retirement or user wants it
        income_strategy = None
        if years_to_retirement < 5 or goal_data.get('include_income_strategy', False):
            income_strategy = self.recommend_retirement_income_strategy(retirement_goal)
        
        # Profile data for constraints and optimizations
        profile_data = goal_data.get('profile_data', {
            'monthly_income': annual_income / 12 if annual_income else 100000,
            'risk_profile': risk_profile
        })
        
        # Apply optimizations if profile data is available
        if profile_data:
            # Tax optimization
            base_strategy = self.optimize_strategy(base_strategy, profile_data)
            
            # Add rebalancing strategy
            retirement_goal['rebalancing_strategy'] = self.integrate_rebalancing_strategy(
                retirement_goal, profile_data
            )
            
            # Apply constraints
            base_strategy = self.apply_constraints_to_strategy(base_strategy, profile_data)
        
        # Handle irregular income patterns if present
        if irregular_income_details and hasattr(self, 'compound_strategy'):
            irregular_income_strategy = self.compound_strategy.optimize_irregular_income(
                base_strategy, 
                irregular_income_details, 
                profile_data
            )
            
            if irregular_income_strategy:
                base_strategy['irregular_income_strategy'] = irregular_income_strategy
        
        # Combine all analyses into comprehensive strategy
        strategy = {
            **base_strategy,
            'retirement_gap_analysis': retirement_gap,
            'pension_options': pension_options,
            'nps_allocation': nps_details
        }
        
        if income_strategy:
            strategy['retirement_income_strategy'] = income_strategy
        
        # Add rebalancing strategy if available
        if 'rebalancing_strategy' in retirement_goal:
            strategy['rebalancing_strategy'] = retirement_goal['rebalancing_strategy']
        
        # Add tax optimization specific to retirement
        strategy['tax_optimization'] = {
            'eligible_deductions': [
                {'section': '80C', 'instruments': ['EPF', 'PPF', 'ELSS', 'NSC'], 'limit': 150000},
                {'section': '80CCD(1B)', 'instruments': ['NPS'], 'limit': 50000},
                {'section': '80D', 'instruments': ['Health Insurance Premium'], 
                 'limit': 25000 if current_age < 60 else 50000}
            ],
            'recommended_allocation': {
                '80C': [
                    {'instrument': 'EPF/PPF', 'amount': min(150000 * 0.6, base_strategy['recommendation']['total_monthly_investment'] * 12 * 0.5)},
                    {'instrument': 'ELSS', 'amount': min(150000 * 0.4, base_strategy['recommendation']['total_monthly_investment'] * 12 * 0.3)}
                ],
                '80CCD(1B)': [
                    {'instrument': 'NPS', 'amount': 50000}
                ]
            },
            'potential_annual_tax_saving': nps_details['tax_benefits']['total_annual_benefit'] if 'tax_benefits' in nps_details else self.estimate_tax_benefit(150000 + 50000)
        }
        
        # Run scenario analysis if compound strategy is available
        if hasattr(self, 'compound_strategy'):
            try:
                scenario_analysis = self.compound_strategy.analyze_scenarios(strategy, profile_data)
                if scenario_analysis:
                    strategy['scenario_analysis'] = scenario_analysis
            except Exception as e:
                logger.error(f"Error in scenario analysis: {e}")
        
        # Add retirement-specific milestone tracking
        strategy['milestones'] = {
            '25%_funded': {
                'target_age': current_age + years_to_retirement * 0.3,
                'checkpoint_actions': [
                    'Review asset allocation',
                    'Consider increasing monthly contribution if behind target'
                ]
            },
            '50%_funded': {
                'target_age': current_age + years_to_retirement * 0.5,
                'checkpoint_actions': [
                    'Review retirement age assumptions',
                    'Consider additional income sources',
                    'Evaluate expense projections'
                ]
            },
            '75%_funded': {
                'target_age': current_age + years_to_retirement * 0.7,
                'checkpoint_actions': [
                    'Begin gradual shift to more conservative allocation',
                    'Review post-retirement income strategy',
                    'Evaluate health insurance coverage for retirement'
                ]
            },
            '90%_funded': {
                'target_age': current_age + years_to_retirement * 0.9,
                'checkpoint_actions': [
                    'Finalize retirement date plan',
                    'Begin setting up withdrawal mechanisms',
                    'Review estate planning'
                ]
            }
        }
        
        # Apply retirement budget constraints
        if hasattr(self, 'constraints'):
            feasibility = self.constraints.assess_retirement_budget_feasibility(
                strategy, profile_data, current_age, retirement_age
            )
            if feasibility:
                strategy['budget_feasibility'] = feasibility
        
        return strategy