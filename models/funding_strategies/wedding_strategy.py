import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class WeddingFundingStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for wedding/marriage goals with
    India-specific wedding customs and cost considerations.
    
    Enhanced with optimization and constraint features to balance traditional
    wedding expectations with budget constraints, optimize between family
    contributions, loan options, and savings strategies.
    """
    
    def __init__(self):
        """Initialize with wedding/marriage specific parameters"""
        super().__init__()
        
        # Optimizer, constraints, and compound strategy objects will be lazy initialized
        self.optimizer = None
        self.constraints = None
        self.compound_strategy = None
        
        # Additional wedding/marriage specific parameters
        self.wedding_params = {
            "wedding_cost_estimates": {
                "budget": {
                    "metro": 800000,      # 8L budget wedding in metro
                    "tier_1": 600000,     # 6L budget wedding in tier 1
                    "tier_2": 400000,     # 4L budget wedding in tier 2
                    "tier_3": 300000      # 3L budget wedding in tier 3
                },
                "moderate": {
                    "metro": 1500000,     # 15L moderate wedding in metro
                    "tier_1": 1000000,    # 10L moderate wedding in tier 1
                    "tier_2": 700000,     # 7L moderate wedding in tier 2
                    "tier_3": 500000      # 5L moderate wedding in tier 3
                },
                "premium": {
                    "metro": 3000000,     # 30L premium wedding in metro
                    "tier_1": 2000000,    # 20L premium wedding in tier 1
                    "tier_2": 1500000,    # 15L premium wedding in tier 2
                    "tier_3": 1000000     # 10L premium wedding in tier 3
                },
                "luxury": {
                    "metro": 8000000,     # 80L luxury wedding in metro
                    "tier_1": 5000000,    # 50L luxury wedding in tier 1
                    "tier_2": 3000000,    # 30L luxury wedding in tier 2
                    "tier_3": 2000000     # 20L luxury wedding in tier 3
                }
            },
            "expense_breakdown": {
                "venue": 0.35,            # 35% for venue and accommodations
                "catering": 0.25,         # 25% for food and beverages
                "clothing_jewelry": 0.15, # 15% for clothing and jewelry
                "decor": 0.10,            # 10% for decorations
                "photography": 0.05,      # 5% for photography/videography
                "entertainment": 0.05,    # 5% for entertainment and music
                "miscellaneous": 0.05     # 5% for miscellaneous
            },
            "regional_adjustments": {
                "north_india": 1.1,       # 10% higher for North Indian weddings
                "south_india": 0.9,       # 10% lower for South Indian weddings
                "west_india": 1.15,       # 15% higher for West Indian weddings
                "east_india": 0.85,       # 15% lower for East Indian weddings
                "northeast_india": 0.8    # 20% lower for Northeast Indian weddings
            },
            "wedding_season_premium": {
                "peak": 1.25,             # 25% premium for peak wedding season
                "shoulder": 1.1,          # 10% premium for shoulder season
                "off_peak": 0.85          # 15% discount for off-peak season
            },
            "guest_count_impact": {
                "small": {
                    "range": "Under 150 guests",
                    "adjustment": 0.7     # 30% less than baseline
                },
                "medium": {
                    "range": "150-300 guests",
                    "adjustment": 1.0     # Baseline
                },
                "large": {
                    "range": "300-500 guests",
                    "adjustment": 1.4     # 40% more than baseline
                },
                "very_large": {
                    "range": "Over 500 guests",
                    "adjustment": 1.8     # 80% more than baseline
                }
            },
            "wedding_loan_details": {
                "interest_rates": {
                    "banks": 0.12,        # 12% typical for bank wedding loans
                    "nbfcs": 0.15,        # 15% typical for NBFC wedding loans
                    "gold_loan": 0.09     # 9% for gold-backed loans
                },
                "loan_tenure": {
                    "min": 1,             # 1 year minimum
                    "max": 5,             # 5 years maximum
                    "typical": 3          # 3 years typical
                },
                "processing_fee": {
                    "percentage": 0.01,   # 1% processing fee
                    "minimum": 5000       # Minimum ₹5,000
                }
            }
        }
        
        # Load wedding/marriage specific parameters
        self._load_wedding_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with wedding-specific optimization parameters
            super()._initialize_optimizer()
            
            # Wedding-specific optimization parameters (these would normally be
            # used by the optimizer methods rather than being stored as constraints)
            self.wedding_optimization_params = {
                'max_wedding_budget_income_ratio': 1.0,  # Wedding cost should not exceed 1 year of income
                'min_family_contribution_ratio': 0.2,    # Family typically contributes at least 20%
                'max_wedding_loan_ratio': 0.3,           # Wedding loan should not exceed 30% of cost
                'optimal_guest_count_ratio': 0.7         # Optimal guest count vs desired count
            }
            
    def _initialize_constraints(self):
        """Initialize the funding constraints with lazy loading pattern"""
        if not hasattr(self, 'constraints') or self.constraints is None:
            # Initialize base constraints
            super()._initialize_constraints()
            
            # Wedding-specific constraint methods are defined in this class directly
            # No need to register them with the constraints object as it doesn't support that
            # These methods will be called directly from our specialized code
            
    def _initialize_compound_strategy(self):
        """Initialize the compound strategy with lazy loading pattern"""
        if not hasattr(self, 'compound_strategy') or self.compound_strategy is None:
            # Initialize base compound strategy
            super()._initialize_compound_strategy()
            
            # Wedding-specific strategies are defined in this class directly
            # They will be called explicitly in our optimization methods, not through
            # the compound strategy object as it doesn't support direct method registration
            
    def _load_wedding_parameters(self):
        """Load wedding/marriage specific parameters from service"""
        if self.param_service:
            try:
                # Load wedding cost estimates
                cost_estimates = self.param_service.get_parameter('wedding_cost_estimates')
                if cost_estimates:
                    self.wedding_params['wedding_cost_estimates'].update(cost_estimates)
                
                # Load expense breakdown
                expense_breakdown = self.param_service.get_parameter('wedding_expense_breakdown')
                if expense_breakdown:
                    self.wedding_params['expense_breakdown'].update(expense_breakdown)
                
                # Load regional adjustments
                regional_adjustments = self.param_service.get_parameter('wedding_regional_adjustments')
                if regional_adjustments:
                    self.wedding_params['regional_adjustments'].update(regional_adjustments)
                
                # Load wedding season premium
                season_premium = self.param_service.get_parameter('wedding_season_premium')
                if season_premium:
                    self.wedding_params['wedding_season_premium'].update(season_premium)
                
                # Load guest count impact
                guest_impact = self.param_service.get_parameter('wedding_guest_count_impact')
                if guest_impact:
                    self.wedding_params['guest_count_impact'].update(guest_impact)
                
                # Load wedding loan details
                loan_details = self.param_service.get_parameter('wedding_loan_details')
                if loan_details:
                    self.wedding_params['wedding_loan_details'].update(loan_details)
                
            except Exception as e:
                logger.error(f"Error loading wedding parameters: {e}")
                # Continue with default parameters
    
    def estimate_wedding_cost(self, tier="tier_1", category="moderate", region=None, 
                           season=None, guest_count=None):
        """
        Estimate wedding cost based on location, category, and other factors.
        
        Args:
            tier: 'metro', 'tier_1', 'tier_2', or 'tier_3'
            category: 'budget', 'moderate', 'premium', or 'luxury'
            region: Region in India (affects cost)
            season: Wedding season ('peak', 'shoulder', 'off_peak')
            guest_count: Number of guests or guest count category
            
        Returns:
            Estimated wedding cost
        """
        # Get base cost from wedding cost estimates
        base_cost = self.wedding_params['wedding_cost_estimates'].get(
            category, self.wedding_params['wedding_cost_estimates']['moderate']
        ).get(tier, self.wedding_params['wedding_cost_estimates']['moderate']['tier_1'])
        
        # Apply regional adjustment if applicable
        if region and region.lower() in self.wedding_params['regional_adjustments']:
            base_cost *= self.wedding_params['regional_adjustments'][region.lower()]
            
        # Apply season adjustment if applicable
        if season and season.lower() in self.wedding_params['wedding_season_premium']:
            base_cost *= self.wedding_params['wedding_season_premium'][season.lower()]
            
        # Apply guest count adjustment if applicable
        if guest_count:
            if isinstance(guest_count, str) and guest_count.lower() in self.wedding_params['guest_count_impact']:
                # If a category string is provided
                base_cost *= self.wedding_params['guest_count_impact'][guest_count.lower()]['adjustment']
            elif isinstance(guest_count, int):
                # If exact guest count is provided
                if guest_count < 150:
                    base_cost *= self.wedding_params['guest_count_impact']['small']['adjustment']
                elif guest_count < 300:
                    base_cost *= self.wedding_params['guest_count_impact']['medium']['adjustment']
                elif guest_count < 500:
                    base_cost *= self.wedding_params['guest_count_impact']['large']['adjustment']
                else:
                    base_cost *= self.wedding_params['guest_count_impact']['very_large']['adjustment']
                    
        return base_cost
    
    def breakdown_wedding_expenses(self, total_cost):
        """
        Break down total wedding cost into categories.
        
        Args:
            total_cost: Total wedding cost
            
        Returns:
            Dictionary with expense breakdown by category
        """
        breakdown = {}
        
        for category, percentage in self.wedding_params['expense_breakdown'].items():
            breakdown[category] = round(total_cost * percentage)
            
        return breakdown
    
    def calculate_wedding_loan(self, loan_amount, tenure=None, loan_type="banks"):
        """
        Calculate wedding loan details.
        
        Args:
            loan_amount: Loan amount
            tenure: Loan tenure in years (default: typical)
            loan_type: 'banks', 'nbfcs', or 'gold_loan'
            
        Returns:
            Dictionary with loan calculation details
        """
        # Use typical tenure if not specified
        if tenure is None:
            tenure = self.wedding_params['wedding_loan_details']['loan_tenure']['typical']
            
        # Ensure tenure is within allowed range
        min_tenure = self.wedding_params['wedding_loan_details']['loan_tenure']['min']
        max_tenure = self.wedding_params['wedding_loan_details']['loan_tenure']['max']
        tenure = max(min_tenure, min(max_tenure, tenure))
        
        # Get interest rate based on loan type
        interest_rate = self.wedding_params['wedding_loan_details']['interest_rates'].get(
            loan_type, self.wedding_params['wedding_loan_details']['interest_rates']['banks']
        )
        
        # Calculate EMI
        monthly_rate = interest_rate / 12
        tenure_months = tenure * 12
        
        # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        
        # Calculate total interest payable
        total_payment = emi * tenure_months
        total_interest = total_payment - loan_amount
        
        # Calculate processing fee
        processing_fee_percent = self.wedding_params['wedding_loan_details']['processing_fee']['percentage']
        min_processing_fee = self.wedding_params['wedding_loan_details']['processing_fee']['minimum']
        processing_fee = max(min_processing_fee, loan_amount * processing_fee_percent)
        
        return {
            'loan_amount': round(loan_amount),
            'interest_rate': round(interest_rate * 100, 2),
            'tenure_years': tenure,
            'monthly_emi': round(emi),
            'total_interest': round(total_interest),
            'processing_fee': round(processing_fee),
            'total_cost_of_loan': round(total_interest + processing_fee),
            'total_payment': round(total_payment + processing_fee),
            'percentage_cost': round((total_interest + processing_fee) / loan_amount * 100, 1)
        }
    
    def recommend_wedding_allocation(self, time_horizon):
        """
        Recommend asset allocation specifically for wedding savings.
        
        Args:
            time_horizon: Years to wedding
            
        Returns:
            Dictionary with recommended asset allocation
        """
        # Wedding savings allocation should be more conservative as the event has a fixed date
        allocations = {}
        
        if time_horizon < 1:
            # Less than 1 year: Maximum liquidity and safety
            allocations = {
                'savings_account': 0.40,
                'sweep_fd': 0.40,
                'liquid_funds': 0.20,
                'expected_return': 4.5  # 4.5% annualized
            }
            
        elif time_horizon < 2:
            # 1-2 years: Focus on stability with some yield
            allocations = {
                'savings_account': 0.20,
                'sweep_fd': 0.40,
                'liquid_funds': 0.30,
                'short_term_debt': 0.10,
                'expected_return': 5.5  # 5.5% annualized
            }
            
        elif time_horizon < 3:
            # 2-3 years: Moderate yield with capital preservation
            allocations = {
                'savings_account': 0.10,
                'sweep_fd': 0.30,
                'liquid_funds': 0.20,
                'short_term_debt': 0.30,
                'balanced_advantage': 0.10,
                'expected_return': 6.5  # 6.5% annualized
            }
            
        else:
            # 3+ years: More balanced approach with some growth focus
            allocations = {
                'savings_account': 0.05,
                'fixed_deposit': 0.25,
                'short_term_debt': 0.30,
                'balanced_advantage': 0.25,
                'large_cap_index': 0.15,
                'expected_return': 7.5  # 7.5% annualized
            }
            
        return allocations
    
    def analyze_family_contribution_scenarios(self, total_cost, self_contribution_percent=50):
        """
        Analyze different family contribution scenarios for wedding funding.
        
        Args:
            total_cost: Total wedding cost
            self_contribution_percent: Percentage contribution by the couple
            
        Returns:
            Dictionary with family contribution scenarios
        """
        # Calculate base scenario with given self contribution
        self_contribution = total_cost * (self_contribution_percent / 100)
        family_contribution = total_cost - self_contribution
        
        # Create alternative scenarios
        scenarios = {
            'base_scenario': {
                'self_contribution': round(self_contribution),
                'self_percentage': self_contribution_percent,
                'family_contribution': round(family_contribution),
                'family_percentage': 100 - self_contribution_percent
            },
            'alternative_scenarios': []
        }
        
        # Generate alternative distribution scenarios
        alternative_percentages = [0, 25, 50, 75, 100]
        
        for percent in alternative_percentages:
            if percent != self_contribution_percent:
                alt_self = total_cost * (percent / 100)
                alt_family = total_cost - alt_self
                
                scenarios['alternative_scenarios'].append({
                    'self_contribution': round(alt_self),
                    'self_percentage': percent,
                    'family_contribution': round(alt_family),
                    'family_percentage': 100 - percent
                })
                
        # Add considerations
        scenarios['considerations'] = [
            "Family traditions and expectations regarding wedding expenses",
            "Current financial capacity of both families",
            "Impact on other financial goals for all parties",
            "Preference for wedding size and style",
            "Cultural norms regarding contribution distribution"
        ]
        
        return scenarios
    
    def plan_wedding_budget_optimization(self, total_budget, priorities=None):
        """
        Plan wedding budget optimization based on priorities.
        
        Args:
            total_budget: Total wedding budget
            priorities: List of priority categories
            
        Returns:
            Dictionary with optimized budget allocation
        """
        # Default expense breakdown
        base_breakdown = self.breakdown_wedding_expenses(total_budget)
        
        # If no priorities specified, return standard breakdown
        if not priorities or len(priorities) == 0:
            return {
                'standard_allocation': base_breakdown,
                'total_budget': total_budget,
                'optimization_message': "Using standard allocation (no priorities specified)"
            }
            
        # Calculate priority-based allocation
        # Increase high-priority categories by 30%, decrease low-priority by 30%
        priority_adjustment = 0.3  # 30% adjustment
        optimization_messages = []
        optimized_breakdown = base_breakdown.copy()
        
        # Calculate adjustment amounts
        priority_increase = 0
        for category in priorities:
            if category in base_breakdown:
                increase_amount = base_breakdown[category] * priority_adjustment
                priority_increase += increase_amount
                
        # Calculate non-priority categories total
        non_priority_total = 0
        for category, amount in base_breakdown.items():
            if category not in priorities:
                non_priority_total += amount
                
        # Calculate reduction factor for non-priority categories
        if non_priority_total > 0:
            reduction_factor = priority_increase / non_priority_total
        else:
            reduction_factor = 0
            
        # Apply adjustments
        for category, amount in base_breakdown.items():
            if category in priorities:
                # Increase priority categories
                optimized_breakdown[category] = round(amount * (1 + priority_adjustment))
                optimization_messages.append(f"Increased {category} budget by {int(priority_adjustment*100)}% to prioritize this category")
            else:
                # Decrease non-priority categories
                optimized_breakdown[category] = round(amount * (1 - reduction_factor))
                if reduction_factor > 0:
                    optimization_messages.append(f"Reduced {category} budget by {int(reduction_factor*100)}% to accommodate priorities")
                    
        # Calculate actual adjusted total to ensure we match the original budget
        adjusted_total = sum(optimized_breakdown.values())
        
        # Scale to match original budget if needed
        if adjusted_total != total_budget:
            scaling_factor = total_budget / adjusted_total
            for category in optimized_breakdown:
                optimized_breakdown[category] = round(optimized_breakdown[category] * scaling_factor)
                
        return {
            'standard_allocation': base_breakdown,
            'optimized_allocation': optimized_breakdown,
            'priorities': priorities,
            'total_budget': total_budget,
            'optimization_messages': optimization_messages
        }
    
    def analyze_cost_saving_opportunities(self, wedding_cost, tier, category, guest_count):
        """
        Analyze cost saving opportunities for wedding.
        
        Args:
            wedding_cost: Estimated wedding cost
            tier: Location tier
            category: Wedding category
            guest_count: Guest count or category
            
        Returns:
            Dictionary with cost saving opportunities
        """
        # Calculate potential savings opportunities
        savings_opportunities = []
        total_potential_savings = 0
        
        # Guest list reduction
        guest_savings = 0
        guest_reduction_percentage = 0
        
        if isinstance(guest_count, int) and guest_count > 100:
            if guest_count >= 500:
                guest_reduction_percentage = 0.3  # 30% reduction for very large weddings
            elif guest_count >= 300:
                guest_reduction_percentage = 0.25  # 25% reduction for large weddings
            elif guest_count >= 150:
                guest_reduction_percentage = 0.2  # 20% reduction for medium weddings
            else:
                guest_reduction_percentage = 0.15  # 15% reduction for smaller weddings
                
        elif isinstance(guest_count, str):
            if guest_count.lower() == 'very_large':
                guest_reduction_percentage = 0.3
            elif guest_count.lower() == 'large':
                guest_reduction_percentage = 0.25
            elif guest_count.lower() == 'medium':
                guest_reduction_percentage = 0.2
            else:
                guest_reduction_percentage = 0.15
                
        if guest_reduction_percentage > 0:
            guest_savings = wedding_cost * 0.6 * guest_reduction_percentage  # 60% of cost affected by guest count
            savings_opportunities.append({
                'category': 'Guest list optimization',
                'potential_savings': round(guest_savings),
                'description': f"Reduce guest list by {int(guest_reduction_percentage*100)}% to focus on closer relationships",
                'impact': 'High impact on venue, catering, and invitation costs'
            })
            total_potential_savings += guest_savings
            
        # Off-season discount
        season_savings = wedding_cost * 0.15  # Up to 15% savings for off-season
        savings_opportunities.append({
            'category': 'Season optimization',
            'potential_savings': round(season_savings),
            'description': "Choose off-peak season dates for significant venue discounts",
            'impact': 'Moderate to high impact on venue costs'
        })
        total_potential_savings += season_savings
        
        # Venue cost reduction
        venue_alternatives_savings = wedding_cost * 0.15  # Up to 15% savings for venue alternatives
        savings_opportunities.append({
            'category': 'Venue alternatives',
            'potential_savings': round(venue_alternatives_savings),
            'description': "Consider non-traditional venues or combined venue-catering packages",
            'impact': 'High impact on overall budget'
        })
        total_potential_savings += venue_alternatives_savings
        
        # Decor optimization
        decor_savings = wedding_cost * 0.05  # Up to 5% on decor
        savings_opportunities.append({
            'category': 'Decor optimization',
            'potential_savings': round(decor_savings),
            'description': "Simplify decor, focus on key areas, use seasonal/local flowers",
            'impact': 'Moderate impact on aesthetics budget'
        })
        total_potential_savings += decor_savings
        
        # Food and beverage optimization
        food_savings = wedding_cost * 0.08  # Up to 8% on food
        savings_opportunities.append({
            'category': 'Food and beverage',
            'potential_savings': round(food_savings),
            'description': "Optimize menu selection, reduce variety but maintain quality",
            'impact': 'Moderate impact while maintaining guest experience'
        })
        total_potential_savings += food_savings
        
        # Digital invitations
        invitation_savings = wedding_cost * 0.02  # Up to 2% on invitations
        savings_opportunities.append({
            'category': 'Digital invitations',
            'potential_savings': round(invitation_savings),
            'description': "Use digital invitations for most guests, printed only for key family members",
            'impact': 'Low overall impact but environmentally friendly'
        })
        total_potential_savings += invitation_savings
        
        return {
            'wedding_cost_estimate': round(wedding_cost),
            'total_potential_savings': round(total_potential_savings),
            'optimized_cost': round(wedding_cost - total_potential_savings),
            'savings_percentage': round((total_potential_savings / wedding_cost) * 100, 1),
            'savings_opportunities': savings_opportunities,
            'implementation_recommendations': [
                "Prioritize savings opportunities based on your values and preferences",
                "Start with highest-impact categories (guest list, venue, season)",
                "Consider involving family in cost-saving decisions to align expectations",
                "Focus on enhancing guest experience in key areas while saving in others",
                "Research vendors thoroughly to negotiate better rates"
            ]
        }
    
    def assess_wedding_budget_feasibility(self, goal_data):
        """
        Assess the feasibility of the wedding budget based on income, 
        timeline, and savings capacity.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with feasibility assessment
        """
        # Extract necessary information
        wedding_cost = goal_data.get('target_amount', 0)
        if not wedding_cost:
            # If target amount not specified, estimate based on other parameters
            tier = goal_data.get('tier', 'tier_1')
            category = goal_data.get('category', 'moderate')
            region = goal_data.get('region')
            season = goal_data.get('season')
            guest_count = goal_data.get('guest_count', 'medium')
            wedding_cost = self.estimate_wedding_cost(tier, category, region, season, guest_count)
            
        annual_income = goal_data.get('annual_income', 0)
        if not annual_income and goal_data.get('monthly_income'):
            annual_income = goal_data.get('monthly_income', 0) * 12
            
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        time_horizon = goal_data.get('time_horizon', 1)
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        
        # Calculate self-contribution amount
        self_contribution = wedding_cost * (1 - family_contribution_pct / 100)
        
        # Calculate projected savings by wedding date
        # Using a simplified compound interest formula
        expected_return = 0.06  # 6% expected annual return for wedding savings
        projected_savings = current_savings * ((1 + expected_return) ** time_horizon)
        projected_savings += monthly_contribution * (((1 + expected_return) ** time_horizon) - 1) / expected_return * 12
        
        # Check wedding cost to income ratio
        income_ratio = wedding_cost / annual_income
        income_ratio_feasibility = {
            'status': 'Feasible',
            'reason': 'Wedding cost is within typical income ratios'
        }
        
        if income_ratio > 2.0:
            income_ratio_feasibility['status'] = 'Infeasible'
            income_ratio_feasibility['reason'] = 'Wedding cost exceeds 2 years of income, which is generally unsustainable'
        elif income_ratio > 1.0:
            income_ratio_feasibility['status'] = 'Challenging'
            income_ratio_feasibility['reason'] = 'Wedding cost exceeds 1 year of income, which is on the higher end'
        
        # Check self-contribution feasibility
        self_contribution_feasibility = {
            'status': 'Feasible',
            'reason': 'Projected savings will cover self-contribution'
        }
        
        if projected_savings < self_contribution:
            self_contribution_feasibility['status'] = 'Challenging'
            self_contribution_feasibility['reason'] = 'Projected savings may not fully cover your contribution'
            
            if projected_savings < self_contribution * 0.7:
                self_contribution_feasibility['status'] = 'Infeasible'
                self_contribution_feasibility['reason'] = 'Significant shortfall in projected savings to cover your contribution'
        
        # Check family contribution realism
        family_contribution_feasibility = {
            'status': 'Feasible',
            'reason': 'Family contribution percentage is realistic'
        }
        
        # Higher family contributions need more scrutiny
        if family_contribution_pct > 80:
            family_contribution_feasibility['status'] = 'Uncertain'
            family_contribution_feasibility['reason'] = 'Very high dependence on family contribution may need explicit confirmation'
        
        # Overall feasibility
        overall_status = 'Feasible'
        limiting_factors = []
        recommendations = []
        
        if income_ratio_feasibility['status'] == 'Infeasible':
            overall_status = 'Infeasible'
            limiting_factors.append('Wedding cost too high relative to income')
            recommendations.append('Consider a more modest wedding or extending timeline to save')
        elif income_ratio_feasibility['status'] == 'Challenging':
            overall_status = 'Challenging'
            limiting_factors.append('Wedding cost high relative to income')
            recommendations.append('Consider cost-saving opportunities or modest scale adjustment')
        
        if self_contribution_feasibility['status'] == 'Infeasible':
            overall_status = 'Infeasible'
            limiting_factors.append('Insufficient savings capacity for self-contribution')
            
            # Calculate required monthly savings
            shortfall = self_contribution - projected_savings
            monthly_needed = shortfall / (time_horizon * 12)
            
            recommendations.append(f'Increase monthly savings by ₹{round(monthly_needed)} to meet your contribution')
            recommendations.append('Consider a wedding loan for part of the expenses (max 30% recommended)')
        elif self_contribution_feasibility['status'] == 'Challenging':
            overall_status = max(overall_status, 'Challenging')
            limiting_factors.append('Tight savings capacity for self-contribution')
            recommendations.append('Increase monthly savings or extend timeline if possible')
        
        if family_contribution_feasibility['status'] == 'Uncertain':
            overall_status = max(overall_status, 'Challenging')
            limiting_factors.append('High dependence on family contribution')
            recommendations.append('Have explicit financial conversations with family about their contribution capability')
        
        return {
            'overall_feasibility': overall_status,
            'wedding_cost': round(wedding_cost),
            'annual_income': round(annual_income),
            'cost_to_income_ratio': round(income_ratio, 2),
            'income_ratio_feasibility': income_ratio_feasibility,
            'self_contribution': round(self_contribution),
            'projected_savings': round(projected_savings),
            'self_contribution_feasibility': self_contribution_feasibility,
            'family_contribution_percent': family_contribution_pct,
            'family_contribution_feasibility': family_contribution_feasibility,
            'limiting_factors': limiting_factors,
            'recommendations': recommendations
        }
    
    def validate_wedding_timing(self, goal_data):
        """
        Validate if the wedding timeline is appropriate
        given savings needs, cultural factors, and practical considerations.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with wedding timing assessment
        """
        # Extract necessary information
        time_horizon = goal_data.get('time_horizon', 1)
        wedding_date = goal_data.get('wedding_date')
        season = goal_data.get('season')
        annual_income = goal_data.get('annual_income', 0)
        if not annual_income and goal_data.get('monthly_income'):
            annual_income = goal_data.get('monthly_income', 0) * 12
        
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        
        # Get wedding cost details
        wedding_cost = goal_data.get('target_amount', 0)
        if not wedding_cost:
            # Estimate cost based on other parameters
            tier = goal_data.get('tier', 'tier_1')
            category = goal_data.get('category', 'moderate')
            region = goal_data.get('region')
            guest_count = goal_data.get('guest_count', 'medium')
            wedding_cost = self.estimate_wedding_cost(tier, category, region, season, guest_count)
        
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        self_contribution = wedding_cost * (1 - family_contribution_pct / 100)
        
        # Calculate time needed to save for wedding
        # Simple calculation: how long to save self_contribution
        if monthly_contribution > 0:
            months_needed = (self_contribution - current_savings) / monthly_contribution
            years_needed = months_needed / 12
        else:
            years_needed = float('inf')  # Cannot save without monthly contribution
        
        # Add additional buffer for wedding planning
        min_planning_time = 0.5  # 6 months minimum for basic planning
        
        if wedding_cost > 1500000:  # 15L+ weddings need more planning time
            min_planning_time = 0.75  # 9 months for larger weddings
            
        if wedding_cost > 3000000:  # 30L+ weddings need even more planning
            min_planning_time = 1.0  # 12 months for very large weddings
        
        total_time_needed = max(years_needed, min_planning_time)
        
        # Check if timeline is sufficient
        timeline_feasibility = 'Adequate'
        timeline_rationale = 'Timeline provides sufficient time for saving and planning'
        
        if time_horizon < total_time_needed:
            if time_horizon < years_needed:
                timeline_feasibility = 'Insufficient for savings'
                timeline_rationale = f'Current timeline allows saving only {round(time_horizon * monthly_contribution * 12)} vs. needed {round(self_contribution - current_savings)}'
            else:
                timeline_feasibility = 'Rushed planning'
                timeline_rationale = f'Current timeline provides limited planning time for a wedding of this scale'
        
        # Check for seasonal considerations
        seasonal_suitability = 'Suitable'
        seasonal_rationale = 'No specific seasonal concerns identified'
        
        if season:
            if season.lower() == 'peak':
                if time_horizon < 1.0:
                    seasonal_suitability = 'Challenging'
                    seasonal_rationale = 'Peak season venues and vendors often book 12+ months in advance'
        
        # Check for cultural timing considerations
        cultural_timing = 'No specific cultural timing constraints identified'
        if goal_data.get('region') in ['north_india', 'west_india']:
            cultural_timing = 'North and West Indian weddings are traditionally concentrated in winter months (Nov-Feb)'
        elif goal_data.get('region') in ['south_india']:
            cultural_timing = 'South Indian weddings traditionally consider auspicious dates based on lunar calendar'
        
        # Generate optimization recommendations
        recommendations = []
        
        if timeline_feasibility.startswith('Insufficient'):
            if self_contribution - current_savings > 0:
                needed_monthly = (self_contribution - current_savings) / (time_horizon * 12)
                if needed_monthly > monthly_contribution * 1.5:  # If needed is 50%+ more than current
                    recommendations.append(f'Extend timeline to {round(total_time_needed, 1)} years for more realistic saving goals')
                else:
                    recommendations.append(f'Increase monthly savings to ₹{round(needed_monthly)} to meet goal in current timeline')
        
        if season and season.lower() == 'peak' and timeline_feasibility.startswith('Rushed'):
            recommendations.append('Consider off-peak season to reduce costs and increase venue/vendor availability')
        
        if time_horizon < 0.5 and wedding_cost > 500000:  # Less than 6 months for 5L+ wedding
            recommendations.append('Consider a wedding planner to help with compressed timeline logistics')
        
        return {
            'wedding_timeline': f'{time_horizon:.1f} years',
            'time_needed_for_saving': f'{years_needed:.1f} years' if years_needed != float('inf') else 'Cannot determine without monthly savings',
            'time_needed_for_planning': f'{min_planning_time:.1f} years',
            'total_time_recommended': f'{total_time_needed:.1f} years',
            'timeline_feasibility': timeline_feasibility,
            'timeline_rationale': timeline_rationale,
            'seasonal_suitability': seasonal_suitability,
            'seasonal_rationale': seasonal_rationale,
            'cultural_timing_considerations': cultural_timing,
            'recommendations': recommendations
        }
    
    def assess_cultural_expectations(self, goal_data):
        """
        Assess cultural expectations and traditions that may impact wedding
        planning, budget, and family dynamics.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with cultural expectations assessment
        """
        # Extract necessary information
        region = goal_data.get('region')
        category = goal_data.get('category', 'moderate')
        total_budget = goal_data.get('target_amount', 0)
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        
        # Default cultural expectations
        cultural_factors = {
            'ceremonies': ['Engagement', 'Main wedding ceremony', 'Reception'],
            'key_expense_categories': ['Venue', 'Catering', 'Attire', 'Decorations', 'Photography'],
            'family_responsibilities': 'Typically split between both families',
            'guest_expectations': 'Medium-sized gathering of family and friends',
            'pressure_points': 'Balancing personal preferences with family expectations'
        }
        
        # Region-specific cultural expectations
        if region:
            if region.lower() == 'north_india':
                cultural_factors.update({
                    'ceremonies': ['Roka', 'Engagement', 'Mehendi', 'Sangeet', 'Haldi', 'Baraat', 'Pheras', 'Reception'],
                    'key_expense_categories': ['Venue', 'Catering', 'Bridal lehenga', 'Groom sherwani', 'Jewelry', 'Decorations', 'Band/DJ'],
                    'family_responsibilities': 'Traditionally bride family bears higher costs, shifting to more equal split in modern times',
                    'guest_expectations': 'Typically larger gatherings with extended family and community',
                    'pressure_points': 'Extended multi-day celebrations can significantly increase costs'
                })
            elif region.lower() == 'south_india':
                cultural_factors.update({
                    'ceremonies': ['Engagement', 'Mehendi', 'Haldi', 'Wedding ceremony', 'Reception'],
                    'key_expense_categories': ['Venue', 'Catering', 'Bridal saree', 'Temple donations', 'Gold jewelry', 'Traditional musicians'],
                    'family_responsibilities': 'Traditionally structured with specific responsibilities for each side',
                    'guest_expectations': 'Focus on religious ceremonies often with moderate guest lists',
                    'pressure_points': 'Traditional gold jewelry expectations can be significant cost factor'
                })
            elif region.lower() == 'west_india':
                cultural_factors.update({
                    'ceremonies': ['Engagement', 'Pithi/Haldi', 'Mehendi', 'Sangeet', 'Wedding ceremony', 'Reception'],
                    'key_expense_categories': ['Venue', 'Catering', 'Attire', 'Decorations', 'Entertainment'],
                    'family_responsibilities': 'Often shared between families with negotiations on key expenses',
                    'guest_expectations': 'Typically larger gatherings with strong focus on hospitality',
                    'pressure_points': 'Entertainment and venue expectations often drive up costs'
                })
            elif region.lower() == 'east_india':
                cultural_factors.update({
                    'ceremonies': ['Ashirwad', 'Mehendi', 'Haldi', 'Wedding ceremony', 'Reception'],
                    'key_expense_categories': ['Venue', 'Catering', 'Traditional attire', 'Decorations'],
                    'family_responsibilities': 'Often follows traditional division but with regional variations',
                    'guest_expectations': 'Typically moderate sized with focus on traditional elements',
                    'pressure_points': 'Traditional elements may require specialized vendors'
                })
        
        # Category-specific expectations (budget to luxury)
        category_expectations = {}
        if category == 'budget':
            category_expectations = {
                'venue_type': 'Community hall or home function',
                'guest_count': '100-150 guests',
                'meal_type': 'Simple traditional meal',
                'attire': 'Ready-made with some customization',
                'photography': 'Basic coverage of main events'
            }
        elif category == 'moderate':
            category_expectations = {
                'venue_type': 'Mid-range banquet hall or marriage garden',
                'guest_count': '150-300 guests',
                'meal_type': 'Multi-course traditional meal with some premium items',
                'attire': 'Custom-made with moderate embellishment',
                'photography': 'Professional coverage with digital album'
            }
        elif category == 'premium':
            category_expectations = {
                'venue_type': 'Premium hotel or resort',
                'guest_count': '300-500 guests',
                'meal_type': 'Elaborate multi-cuisine buffet with premium counters',
                'attire': 'Designer outfits with significant embellishment',
                'photography': 'Premium photo/video package with drone coverage'
            }
        elif category == 'luxury':
            category_expectations = {
                'venue_type': 'Luxury hotel, destination wedding, or palace venue',
                'guest_count': '500+ guests',
                'meal_type': 'Gourmet catering with international cuisines and premium services',
                'attire': 'High-end designer collections with extensive embellishment',
                'photography': 'Celebrity-style photography with destination pre-wedding shoots'
            }
        
        # Assess budget alignment with cultural expectations
        budget_alignment = 'Well aligned'
        budget_alignment_rationale = 'Budget appears appropriate for the cultural expectations'
        
        # Check if budget might be inadequate for cultural expectations
        typical_cost = 0
        if region and category:
            # Get baseline cost from wedding cost estimates
            tier = goal_data.get('tier', 'tier_1')
            baseline_cost = self.wedding_params['wedding_cost_estimates'].get(
                category, self.wedding_params['wedding_cost_estimates']['moderate']
            ).get(tier, self.wedding_params['wedding_cost_estimates']['moderate']['tier_1'])
            
            # Apply regional adjustment
            if region.lower() in self.wedding_params['regional_adjustments']:
                typical_cost = baseline_cost * self.wedding_params['regional_adjustments'][region.lower()]
            else:
                typical_cost = baseline_cost
            
            # Check budget alignment
            if total_budget < typical_cost * 0.7:
                budget_alignment = 'Potentially inadequate'
                budget_alignment_rationale = f'Budget is significantly below typical cost for {category} weddings in {region}'
            elif total_budget > typical_cost * 1.3:
                budget_alignment = 'Above typical'
                budget_alignment_rationale = f'Budget exceeds typical cost for {category} weddings in {region}'
        
        # Assess family contribution alignment with cultural expectations
        family_alignment = 'Well aligned'
        family_alignment_rationale = 'Family contribution matches cultural norms'
        
        if region:
            # North and West Indian weddings traditionally have higher bride family contribution
            if region.lower() in ['north_india', 'west_india']:
                if family_contribution_pct < 40:
                    family_alignment = 'Below traditional norms'
                    family_alignment_rationale = 'Family contribution is lower than traditional expectations in this region'
            # South Indian weddings often have more structured family contributions
            elif region.lower() == 'south_india':
                if family_contribution_pct < 30:
                    family_alignment = 'Below traditional norms'
                    family_alignment_rationale = 'Family contribution is lower than traditional expectations in this region'
        
        # Generate recommendations
        recommendations = []
        
        if budget_alignment == 'Potentially inadequate':
            recommendations.append('Consider adjusting wedding scale or increasing budget to meet regional cultural expectations')
            recommendations.append('Focus budget on ceremonies most important in your region, consider simplifying others')
        
        if family_alignment == 'Below traditional norms':
            recommendations.append('Have clear conversations with family about contribution expectations')
            recommendations.append('Consider modernizing some aspects while honoring key traditional ceremonies')
        
        if len(cultural_factors['ceremonies']) > 3 and category in ['budget', 'moderate']:
            recommendations.append('Consider combining some ceremonies to reduce venue and other fixed costs')
        
        return {
            'region': region or 'Not specified',
            'regional_cultural_expectations': cultural_factors,
            'category_expectations': category_expectations,
            'budget_cultural_alignment': {
                'status': budget_alignment,
                'rationale': budget_alignment_rationale,
                'typical_regional_cost': round(typical_cost) if typical_cost else 'Cannot determine without region and category'
            },
            'family_contribution_alignment': {
                'status': family_alignment,
                'rationale': family_alignment_rationale,
                'current_contribution_percent': family_contribution_pct
            },
            'recommendations': recommendations
        }
    
    def validate_family_contribution_balance(self, goal_data):
        """
        Validate if the family contribution balance is appropriate
        given cultural norms, financial realities, and relationship dynamics.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with family contribution assessment
        """
        # Extract necessary information
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        annual_income = goal_data.get('annual_income', 0)
        if not annual_income and goal_data.get('monthly_income'):
            annual_income = goal_data.get('monthly_income', 0) * 12
            
        wedding_cost = goal_data.get('target_amount', 0)
        region = goal_data.get('region')
        
        # Calculate self and family contributions
        family_contribution = wedding_cost * (family_contribution_pct / 100)
        self_contribution = wedding_cost - family_contribution
        
        # Check self-contribution affordability
        income_ratio = self_contribution / annual_income
        
        affordability = 'Affordable'
        affordability_rationale = 'Self-contribution is reasonable relative to income'
        
        if income_ratio > 1.0:
            affordability = 'Challenging'
            affordability_rationale = 'Self-contribution exceeds annual income, may be difficult to fund'
        elif income_ratio > 0.5:
            affordability = 'Significant'
            affordability_rationale = 'Self-contribution is a substantial portion of annual income'
        
        # Assess cultural alignment
        cultural_alignment = 'Aligned with modern practices'
        cultural_rationale = '50-50 split between couple and family is common in contemporary weddings'
        
        if region:
            if region.lower() in ['north_india', 'west_india'] and family_contribution_pct < 40:
                cultural_alignment = 'Lower than traditional'
                cultural_rationale = 'North/West Indian weddings traditionally have higher family contributions'
            elif region.lower() == 'south_india' and family_contribution_pct < 30:
                cultural_alignment = 'Lower than traditional'
                cultural_rationale = 'South Indian weddings traditionally have structured family contributions'
            elif region.lower() == 'east_india' and family_contribution_pct < 35:
                cultural_alignment = 'Lower than traditional' 
                cultural_rationale = 'East Indian weddings often have traditional family contribution patterns'
        
        # Generate alternative scenarios
        scenarios = {}
        
        # Current scenario
        scenarios['current'] = {
            'family_contribution_percent': family_contribution_pct,
            'family_contribution': round(family_contribution),
            'self_contribution': round(self_contribution),
            'self_to_income_ratio': round(income_ratio, 2)
        }
        
        # Traditional scenario (higher family contribution)
        traditional_pct = 70
        if region:
            if region.lower() in ['north_india', 'west_india']:
                traditional_pct = 70
            elif region.lower() == 'south_india':
                traditional_pct = 65
            elif region.lower() == 'east_india':
                traditional_pct = 60
        
        trad_family_contribution = wedding_cost * (traditional_pct / 100)
        trad_self_contribution = wedding_cost - trad_family_contribution
        trad_income_ratio = trad_self_contribution / annual_income if annual_income else 0
        
        scenarios['traditional'] = {
            'family_contribution_percent': traditional_pct,
            'family_contribution': round(trad_family_contribution),
            'self_contribution': round(trad_self_contribution),
            'self_to_income_ratio': round(trad_income_ratio, 2)
        }
        
        # Modern equal scenario (50-50)
        equal_family_contribution = wedding_cost * 0.5
        equal_self_contribution = wedding_cost * 0.5
        equal_income_ratio = equal_self_contribution / annual_income if annual_income else 0
        
        scenarios['equal'] = {
            'family_contribution_percent': 50,
            'family_contribution': round(equal_family_contribution),
            'self_contribution': round(equal_self_contribution),
            'self_to_income_ratio': round(equal_income_ratio, 2)
        }
        
        # Modern couple-focused scenario (lower family contribution)
        modern_pct = 30
        modern_family_contribution = wedding_cost * (modern_pct / 100)
        modern_self_contribution = wedding_cost - modern_family_contribution
        modern_income_ratio = modern_self_contribution / annual_income if annual_income else 0
        
        scenarios['modern'] = {
            'family_contribution_percent': modern_pct,
            'family_contribution': round(modern_family_contribution),
            'self_contribution': round(modern_self_contribution),
            'self_to_income_ratio': round(modern_income_ratio, 2)
        }
        
        # Generate recommendations
        recommendations = []
        
        if affordability == 'Challenging':
            if family_contribution_pct < traditional_pct:
                recommendations.append(f'Consider discussing higher family contribution (traditional level: {traditional_pct}%)')
                recommendations.append('Consider reducing overall wedding budget to improve self-contribution affordability')
            else:
                recommendations.append('Consider reducing overall wedding budget to improve affordability')
        
        if cultural_alignment == 'Lower than traditional' and affordability != 'Affordable':
            recommendations.append('Discuss expectations with family considering both traditional norms and current financial realities')
        
        if family_contribution_pct > 80:
            recommendations.append('Very high family contributions may come with implicit expectations about wedding decisions')
            recommendations.append('Ensure open communication about decision-making authority for key wedding elements')
        
        return {
            'current_family_contribution': {
                'percentage': family_contribution_pct,
                'amount': round(family_contribution),
                'self_contribution': round(self_contribution),
                'self_to_income_ratio': round(income_ratio, 2) if annual_income else 'Unknown (income not provided)'
            },
            'affordability_assessment': {
                'status': affordability,
                'rationale': affordability_rationale
            },
            'cultural_alignment': {
                'status': cultural_alignment,
                'rationale': cultural_rationale
            },
            'alternative_scenarios': scenarios,
            'recommendations': recommendations
        }
        
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy tailored for wedding goals.
        
        Wedding goals have a fixed date and require progressive risk reduction
        as the wedding date approaches. The strategy increases in safety
        and focuses on capital preservation in later stages.
        
        Args:
            goal_data: Dictionary with wedding goal details
            profile_data: Dictionary with user profile information
            
        Returns:
            Dictionary with wedding-specific rebalancing strategy
        """
        # Create rebalancing instance
        rebalancing = RebalancingStrategy()
        
        # Extract wedding specific information
        time_horizon = goal_data.get('time_horizon', 1)
        target_amount = goal_data.get('target_amount', 0)
        current_savings = goal_data.get('current_savings', 0)
        wedding_date = goal_data.get('wedding_date')
        season = goal_data.get('season')
        
        # If profile data not provided, create minimal profile
        if not profile_data:
            profile_data = {
                'risk_profile': 'conservative',  # Weddings typically use conservative profile
                'portfolio_value': current_savings,
                'market_volatility': 'normal'
            }
        
        # Get wedding-specific allocation
        allocation = self.recommend_wedding_allocation(time_horizon)
        allocation_percentages = {k: v for k, v in allocation.items() if k != 'expected_return'}
        
        # Create goal data specifically for rebalancing
        rebalancing_goal = {
            'goal_type': 'wedding',
            'time_horizon': time_horizon,
            'target_allocation': allocation_percentages,
            'current_allocation': goal_data.get('current_allocation', allocation_percentages),
            'priority_level': 'high'  # Wedding is typically high priority with fixed date
        }
        
        # Design rebalancing schedule
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(
            rebalancing_goal, profile_data
        )
        
        # Calculate time-based threshold factors - weddings need increasingly tighter thresholds
        time_threshold_factor = 1.0
        if time_horizon < 3:
            # Calculate more precise timing if wedding date is provided
            if wedding_date:
                wedding_datetime = datetime.strptime(wedding_date, '%Y-%m-%d')
                months_to_wedding = (wedding_datetime - datetime.now()).days / 30
                
                if months_to_wedding < 1:
                    time_threshold_factor = 0.5  # Very tight in final month
                elif months_to_wedding < 3:
                    time_threshold_factor = 0.6  # Very tight in final 3 months
                elif months_to_wedding < 6:
                    time_threshold_factor = 0.7  # Tight in final 6 months
                elif months_to_wedding < 9:
                    time_threshold_factor = 0.8  # Moderately tight in final 9 months
                else:
                    time_threshold_factor = 0.9  # Slightly tightened
            else:
                # If no specific date, use time horizon in years
                if time_horizon < 0.5:  # Less than 6 months
                    time_threshold_factor = 0.5  # Very tight
                elif time_horizon < 1:  # Less than 1 year
                    time_threshold_factor = 0.7  # Tight
                else:  # 1-3 years
                    time_threshold_factor = 0.8  # Moderately tight
        
        # Customize drift thresholds for wedding strategy
        # As wedding approaches, tighten thresholds dramatically for more conservative approach
        custom_thresholds = {
            'equity': 0.05 * time_threshold_factor,
            'debt': 0.03 * time_threshold_factor,
            'savings_account': 0.01,  # Always tight for savings component
            'sweep_fd': 0.01,         # Always tight for FD component
            'liquid_funds': 0.02 * time_threshold_factor,
            'short_term_debt': 0.03 * time_threshold_factor,
            'balanced_advantage': 0.04 * time_threshold_factor
        }
        
        drift_thresholds = rebalancing.calculate_drift_thresholds(custom_thresholds)
        
        # Customize threshold rationale for wedding specifics
        drift_thresholds['threshold_rationale'] = "Wedding-specific thresholds with milestone-based adjustments"
        
        # Consider Indian wedding seasons (typically winter and spring)
        wedding_season_factors = {}
        if season:
            if season.lower() == 'peak':
                wedding_season_factors = {
                    'season_type': 'Peak wedding season',
                    'vendor_payment_schedule': 'More advanced payments required (higher liquidity needs)',
                    'rebalancing_implications': 'Need higher cash allocation earlier'
                }
            elif season.lower() == 'shoulder':
                wedding_season_factors = {
                    'season_type': 'Shoulder wedding season',
                    'vendor_payment_schedule': 'Standard payment schedule',
                    'rebalancing_implications': 'Regular liquidity planning is adequate'
                }
            elif season.lower() == 'off_peak':
                wedding_season_factors = {
                    'season_type': 'Off-peak wedding season',
                    'vendor_payment_schedule': 'More flexibility in payment schedules',
                    'rebalancing_implications': 'Can maintain growth assets slightly longer'
                }
        
        # Create wedding-specific rebalancing strategy
        wedding_rebalancing = {
            'goal_type': 'wedding',
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': drift_thresholds,
            'wedding_specific_considerations': {
                'vendor_payment_milestones': 'Align rebalancing with vendor payment schedule',
                'seasonal_factors': 'Consider seasonal impacts on pricing and payment timing',
                'progressive_safety': 'Increase portfolio safety as wedding date approaches'
            },
            'implementation_priorities': [
                'Vendor payment schedule should drive liquidity planning',
                'Major venue/vendor deposits require specific liquidity windows',
                'Increase caution as wedding date approaches, prioritizing accessibility over returns',
                'Consider festival season timing for additional liquidity needs'
            ]
        }
        
        # Add seasonal considerations if available
        if wedding_season_factors:
            wedding_rebalancing['seasonal_considerations'] = wedding_season_factors
        
        # Add payment milestone-based rebalancing
        wedding_rebalancing['payment_milestone_rebalancing'] = {
            'venue_booking': {
                'typical_timing': '9-12 months before wedding',
                'typical_percentage': '20-30% of total cost',
                'rebalancing_action': 'Ensure sufficient liquidity for initial large deposit'
            },
            'vendor_deposits': {
                'typical_timing': '6-9 months before wedding',
                'typical_percentage': '30-40% of remaining costs',
                'rebalancing_action': 'Rebalance to provide liquidity for multiple vendor deposits'
            },
            'final_payments': {
                'typical_timing': '1-4 weeks before wedding',
                'typical_percentage': 'Remaining 30-50% of costs',
                'rebalancing_action': 'Complete transition to cash and liquid funds for final payments'
            }
        }
        
        return wedding_rebalancing
    
    def optimize_wedding_budget(self, goal_data):
        """
        Optimize the wedding budget allocation based on personal priorities,
        cultural expectations, and financial constraints.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with optimized wedding budget
        """
        # Extract necessary information
        wedding_cost = goal_data.get('target_amount', 0)
        if not wedding_cost:
            # Estimate wedding cost based on other parameters
            tier = goal_data.get('tier', 'tier_1')
            category = goal_data.get('category', 'moderate')
            region = goal_data.get('region')
            season = goal_data.get('season')
            guest_count = goal_data.get('guest_count', 'medium')
            wedding_cost = self.estimate_wedding_cost(tier, category, region, season, guest_count)
            
        annual_income = goal_data.get('annual_income', 0)
        if not annual_income and goal_data.get('monthly_income'):
            annual_income = goal_data.get('monthly_income', 0) * 12
            
        priorities = goal_data.get('priorities', ['venue', 'catering'])
        region = goal_data.get('region')
        guest_count = goal_data.get('guest_count', 'medium')
        time_horizon = goal_data.get('time_horizon', 1)
        
        # Get wedding-related affordability metrics
        income_ratio = wedding_cost / annual_income if annual_income else float('inf')
        
        # Calculate standard expense breakdown
        standard_breakdown = self.breakdown_wedding_expenses(wedding_cost)
        
        # Get regional adjustments if applicable
        regional_factor = 1.0
        if region and region.lower() in self.wedding_params['regional_adjustments']:
            regional_factor = self.wedding_params['regional_adjustments'][region.lower()]
        
        # Check if budget needs adjustment
        optimized_budget = wedding_cost
        budget_adjustment_rationale = "No adjustment needed, budget is appropriate"
        
        # Adjust budget if it's too high relative to income
        if income_ratio > 1.0:
            # Calculate more reasonable budget (max 80% of annual income for higher incomes, 
            # lower percentage for lower incomes)
            max_budget_factor = 0.8
            if annual_income < 1000000:  # Under 10L
                max_budget_factor = 0.6
            elif annual_income < 1500000:  # Under 15L
                max_budget_factor = 0.7
                
            optimized_budget = annual_income * max_budget_factor
            budget_adjustment_rationale = f"Budget adjusted to {max_budget_factor*100}% of annual income for better affordability"
            
        # Calculate savings required if using optimized budget
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        self_contribution = optimized_budget * (1 - family_contribution_pct / 100)
        
        # Check if self-contribution is realistic given timeline and savings capacity
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        
        # Simple projection of savings
        projected_savings = current_savings + (monthly_contribution * time_horizon * 12)
        
        # If projected savings < self-contribution, adjust budget further
        if projected_savings < self_contribution and time_horizon > 0:
            savings_factor = projected_savings / self_contribution
            if savings_factor < 0.8:  # If more than 20% shortfall
                total_contribution = projected_savings / (1 - family_contribution_pct / 100)
                optimized_budget = min(optimized_budget, total_contribution)
                budget_adjustment_rationale += f"; Further adjusted to ₹{round(optimized_budget)} based on realistic savings capacity"
        
        # Calculate optimized expense breakdown based on priorities
        optimized_breakdown = self.plan_wedding_budget_optimization(
            optimized_budget, priorities
        ).get('optimized_allocation', self.breakdown_wedding_expenses(optimized_budget))
        
        # Calculate potential savings from optimized budget
        savings_from_optimization = wedding_cost - optimized_budget
        
        # Calculate cost-saving opportunities for optimized budget
        saving_opportunities = self.analyze_cost_saving_opportunities(
            optimized_budget, goal_data.get('tier', 'tier_1'), 
            goal_data.get('category', 'moderate'), guest_count
        )
        
        # Calculate maximum additional savings from cost-saving opportunities
        additional_savings = saving_opportunities.get('total_potential_savings', 0)
        fully_optimized_budget = optimized_budget - additional_savings
        
        # Plan ceremony budget distribution
        ceremony_count = 3  # Default (engagement, main ceremony, reception)
        
        # Adjust ceremony count based on region
        if region:
            if region.lower() == 'north_india':
                ceremony_count = 6  # More ceremonies in North Indian weddings
            elif region.lower() == 'south_india':
                ceremony_count = 4  # Moderate number in South Indian weddings
            elif region.lower() == 'west_india':
                ceremony_count = 5  # Higher number in West Indian weddings
            elif region.lower() == 'east_india':
                ceremony_count = 4  # Moderate number in East Indian weddings
        
        # Calculate ceremony budget allocation based on importance
        ceremony_budget = {}
        
        if region and region.lower() == 'north_india':
            # North Indian wedding ceremony allocation
            ceremony_budget = {
                'Engagement': 0.10,
                'Mehendi': 0.10,
                'Sangeet': 0.20,
                'Haldi': 0.05,
                'Main Ceremony': 0.35,
                'Reception': 0.20
            }
        elif region and region.lower() == 'south_india':
            # South Indian wedding ceremony allocation
            ceremony_budget = {
                'Engagement': 0.15,
                'Pre-wedding rituals': 0.15,
                'Main Ceremony': 0.50,
                'Reception': 0.20
            }
        else:
            # Default ceremony allocation
            ceremony_budget = {
                'Engagement': 0.15,
                'Main Ceremony': 0.50,
                'Reception': 0.35
            }
        
        # Adjust ceremony allocations based on priorities
        if 'ceremonies' in priorities:
            # Re-balance ceremony budget based on specified ceremony priorities
            priority_ceremonies = [p for p in priorities if p.lower() in [c.lower() for c in ceremony_budget.keys()]]
            if priority_ceremonies:
                # Increase allocation for priority ceremonies by 20% each
                adjustment_factor = 0.2
                total_adjustment = len(priority_ceremonies) * adjustment_factor
                
                if total_adjustment < 0.9:  # Ensure we don't adjust more than 90% total
                    # Reduce non-priority ceremonies proportionally
                    non_priority_ceremonies = [c for c in ceremony_budget.keys() if c.lower() not in [p.lower() for p in priorities]]
                    non_priority_total = sum(ceremony_budget[c] for c in non_priority_ceremonies)
                    
                    if non_priority_total > 0:
                        reduction_factor = total_adjustment / non_priority_total
                        
                        # Apply adjustments
                        for ceremony in priority_ceremonies:
                            matching_ceremony = next((c for c in ceremony_budget.keys() if c.lower() == ceremony.lower()), None)
                            if matching_ceremony:
                                ceremony_budget[matching_ceremony] += adjustment_factor
                                
                        for ceremony in non_priority_ceremonies:
                            ceremony_budget[ceremony] -= ceremony_budget[ceremony] * reduction_factor
        
        # Calculate absolute amounts for each ceremony
        ceremony_amounts = {ceremony: round(optimized_budget * allocation) 
                          for ceremony, allocation in ceremony_budget.items()}
        
        return {
            'original_budget': round(wedding_cost),
            'optimized_budget': round(optimized_budget),
            'budget_adjustment_rationale': budget_adjustment_rationale,
            'budget_to_income_ratio': {
                'original': round(income_ratio, 2) if annual_income else 'Unknown',
                'optimized': round(optimized_budget / annual_income, 2) if annual_income else 'Unknown'
            },
            'standard_expense_breakdown': {
                category: round(amount) for category, amount in standard_breakdown.items()
            },
            'optimized_expense_breakdown': {
                category: round(amount) for category, amount in optimized_breakdown.items()
            },
            'priority_categories': priorities,
            'ceremony_budget_allocation': {
                'percentage': {k: round(v * 100) for k, v in ceremony_budget.items()},
                'amounts': ceremony_amounts
            },
            'total_potential_savings': {
                'from_budget_optimization': round(savings_from_optimization),
                'from_cost_saving_opportunities': round(additional_savings),
                'total_possible_savings': round(savings_from_optimization + additional_savings),
                'fully_optimized_budget': round(fully_optimized_budget)
            },
            'cost_saving_opportunities_detail': saving_opportunities.get('savings_opportunities', []),
            'recommendations': [
                f"Optimized wedding budget: ₹{round(optimized_budget)} ({round(optimized_budget/wedding_cost*100)}% of original)",
                "Prioritize spending on key elements most important to you and cultural traditions",
                "Consider additional cost-saving opportunities for further optimization",
                f"With all optimizations, potential budget of ₹{round(fully_optimized_budget)} would still provide a meaningful celebration"
            ]
        }
    
    def optimize_family_contribution(self, goal_data):
        """
        Optimize the family contribution balance based on cultural norms,
        financial capacity, and relationship factors.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with optimized family contribution recommendations
        """
        # Extract necessary information
        wedding_cost = goal_data.get('target_amount', 0)
        annual_income = goal_data.get('annual_income', 0)
        if not annual_income and goal_data.get('monthly_income'):
            annual_income = goal_data.get('monthly_income', 0) * 12
            
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        time_horizon = goal_data.get('time_horizon', 1)
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        region = goal_data.get('region')
        
        # Calculate current self and family contributions
        family_contribution = wedding_cost * (family_contribution_pct / 100)
        self_contribution = wedding_cost - family_contribution
        
        # Project savings by wedding date
        expected_return = 0.06  # 6% expected annual return on wedding savings
        projected_savings = current_savings * ((1 + expected_return) ** time_horizon)
        projected_savings += monthly_contribution * (((1 + expected_return) ** time_horizon) - 1) / expected_return * 12
        
        # Calculate affordable self-contribution
        affordable_self_contribution = projected_savings
        affordable_family_pct = 100 - (affordable_self_contribution / wedding_cost * 100)
        affordable_family_pct = min(max(affordable_family_pct, 0), 100)  # Clamp between 0-100%
        
        # Calculate income-based self-contribution (based on income ratio)
        income_based_contribution = annual_income * 0.5  # Assume 50% of annual income is reasonable max
        income_based_family_pct = 100 - (income_based_contribution / wedding_cost * 100)
        income_based_family_pct = min(max(income_based_family_pct, 0), 100)  # Clamp between 0-100%
        
        # Determine traditional cultural family contribution level
        traditional_family_pct = 60  # Default
        if region:
            if region.lower() in ['north_india', 'west_india']:
                traditional_family_pct = 70
            elif region.lower() == 'south_india':
                traditional_family_pct = 65
            elif region.lower() == 'east_india':
                traditional_family_pct = 60
                
        # Modern expectations (more equal sharing)
        modern_family_pct = 50
        
        # Calculate optimized family contribution based on multiple factors
        optimized_family_pct = family_contribution_pct  # Start with current
        
        # Adjust based on savings capacity
        if self_contribution > affordable_self_contribution:
            # Need higher family contribution
            optimized_family_pct = max(optimized_family_pct, affordable_family_pct)
            
        # Adjust based on income affordability
        if self_contribution > income_based_contribution:
            # Need higher family contribution
            optimized_family_pct = max(optimized_family_pct, income_based_family_pct)
            
        # Adjust based on traditional cultural expectations
        if traditional_family_pct > optimized_family_pct + 10:
            # Consider traditional expectations if significantly higher
            cultural_factor = 0.3  # Weight given to cultural norms
            optimized_family_pct = optimized_family_pct * (1 - cultural_factor) + traditional_family_pct * cultural_factor
            
        # Create scenarios for comparison
        scenarios = {}
        
        # Original scenario
        scenarios['original'] = {
            'family_contribution_percent': family_contribution_pct,
            'family_contribution': round(family_contribution),
            'self_contribution': round(self_contribution),
            'self_affordability': 'Challenging' if self_contribution > affordable_self_contribution else 'Affordable'
        }
        
        # Optimized scenario
        optimized_family_contribution = wedding_cost * (optimized_family_pct / 100)
        optimized_self_contribution = wedding_cost - optimized_family_contribution
        
        scenarios['optimized'] = {
            'family_contribution_percent': round(optimized_family_pct, 1),
            'family_contribution': round(optimized_family_contribution),
            'self_contribution': round(optimized_self_contribution),
            'self_affordability': 'Improved' if optimized_self_contribution < self_contribution else 'Unchanged'
        }
        
        # Traditional scenario
        traditional_family_contribution = wedding_cost * (traditional_family_pct / 100)
        traditional_self_contribution = wedding_cost - traditional_family_contribution
        
        scenarios['traditional'] = {
            'family_contribution_percent': traditional_family_pct,
            'family_contribution': round(traditional_family_contribution),
            'self_contribution': round(traditional_self_contribution),
            'self_affordability': 'Good' if traditional_self_contribution <= affordable_self_contribution else 'Challenging'
        }
        
        # Modern equal scenario
        modern_family_contribution = wedding_cost * (modern_family_pct / 100)
        modern_self_contribution = wedding_cost - modern_family_contribution
        
        scenarios['modern_equal'] = {
            'family_contribution_percent': modern_family_pct,
            'family_contribution': round(modern_family_contribution),
            'self_contribution': round(modern_self_contribution),
            'self_affordability': 'Good' if modern_self_contribution <= affordable_self_contribution else 'Challenging'
        }
        
        # Determine decision points and implications
        decision_points = []
        
        if abs(optimized_family_pct - family_contribution_pct) > 5:
            # Significant change is recommended
            if optimized_family_pct > family_contribution_pct:
                decision_points.append("Higher family contribution is recommended for financial feasibility")
            else:
                decision_points.append("Lower family contribution is possible if preferred for relationship dynamics")
                
        if abs(traditional_family_pct - optimized_family_pct) > 10:
            # Significant deviation from cultural traditions
            decision_points.append("Optimized contribution differs from traditional cultural expectations")
            
        if affordable_self_contribution < self_contribution:
            decision_points.append("Current savings trajectory insufficient for planned self-contribution")
            
        # Generate recommendations and potential implications
        recommendations = []
        implications = []
        
        if optimized_family_pct > family_contribution_pct:
            recommendations.append(f"Consider increasing family contribution to {round(optimized_family_pct)}% for better financial feasibility")
            implications.append("May require careful conversation with family about increased support")
        
        if traditional_family_pct > optimized_family_pct + 10:
            recommendations.append(f"Traditional expectation would be {traditional_family_pct}% family contribution in your region")
            implications.append("Deviating from traditional contribution patterns may require managing family expectations")
        
        if affordable_self_contribution < self_contribution:
            increase_needed = (self_contribution - affordable_self_contribution) / (time_horizon * 12)
            recommendations.append(f"Consider increasing monthly savings by ₹{round(increase_needed)} to fully fund your contribution")
            implications.append("Alternatively, consider a modest wedding loan (≤30% of your contribution) to bridge the gap")
        
        return {
            'current_contribution_split': {
                'family_percentage': family_contribution_pct,
                'family_amount': round(family_contribution),
                'self_percentage': 100 - family_contribution_pct,
                'self_amount': round(self_contribution)
            },
            'financial_capacity_assessment': {
                'projected_savings': round(projected_savings),
                'affordable_self_contribution': round(affordable_self_contribution),
                'self_contribution_gap': round(max(0, self_contribution - affordable_self_contribution)),
                'affordable_family_percentage': round(affordable_family_pct, 1),
                'income_based_affordable_percentage': round(income_based_family_pct, 1)
            },
            'cultural_considerations': {
                'region': region or 'Not specified',
                'traditional_family_percentage': traditional_family_pct,
                'modern_expectation_percentage': modern_family_pct
            },
            'optimized_contribution': {
                'recommended_family_percentage': round(optimized_family_pct, 1),
                'recommended_family_amount': round(optimized_family_contribution),
                'recommended_self_percentage': round(100 - optimized_family_pct, 1),
                'recommended_self_amount': round(optimized_self_contribution)
            },
            'scenarios': scenarios,
            'decision_points': decision_points,
            'recommendations': recommendations,
            'potential_implications': implications
        }
        
    def optimize_wedding_timing(self, goal_data):
        """
        Optimize the wedding timing based on financial readiness,
        cultural and seasonal factors, and venue availability.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with optimized wedding timing recommendations
        """
        # Extract necessary information
        time_horizon = goal_data.get('time_horizon', 1)
        wedding_date = goal_data.get('wedding_date')
        season = goal_data.get('season')
        region = goal_data.get('region')
        
        wedding_cost = goal_data.get('target_amount', 0)
        annual_income = goal_data.get('annual_income', 0)
        if not annual_income and goal_data.get('monthly_income'):
            annual_income = goal_data.get('monthly_income', 0) * 12
            
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        family_contribution_pct = goal_data.get('family_contribution_percent', 50)
        
        # Calculate self-contribution
        self_contribution = wedding_cost * (1 - family_contribution_pct / 100)
        
        # Calculate time needed to save self-contribution
        if monthly_contribution > 0:
            savings_gap = max(0, self_contribution - current_savings)
            months_needed = savings_gap / monthly_contribution
            years_needed_for_savings = months_needed / 12
        else:
            years_needed_for_savings = float('inf')  # Cannot save without monthly contribution
        
        # Add planning time buffer based on wedding size
        planning_buffer = 0.5  # Default 6 months
        
        if wedding_cost > 1500000:  # 15L
            planning_buffer = 0.75  # 9 months
        if wedding_cost > 3000000:  # 30L
            planning_buffer = 1.0  # 12 months
            
        # Minimum time needed is the max of savings time and planning buffer
        min_time_needed = max(years_needed_for_savings, planning_buffer)
        
        # Seasonal factors
        peak_seasons = {}
        off_peak_discount = 0.15  # 15% savings for off-peak
        
        if region:
            if region.lower() in ['north_india', 'west_india']:
                peak_seasons = {
                    'winter': {'months': [11, 12, 1, 2], 'premium': 0.2, 'description': 'Traditional peak season (Nov-Feb)'},
                    'spring': {'months': [3, 4], 'premium': 0.1, 'description': 'Shoulder season (Mar-Apr)'},
                    'summer': {'months': [5, 6, 7, 8, 9, 10], 'premium': -0.15, 'description': 'Off-peak summer/monsoon (May-Oct)'}
                }
            elif region.lower() == 'south_india':
                peak_seasons = {
                    'winter': {'months': [12, 1], 'premium': 0.15, 'description': 'Peak season (Dec-Jan)'},
                    'summer': {'months': [4, 5, 6], 'premium': -0.1, 'description': 'Off-peak summer (Apr-Jun)'},
                    'other': {'months': [2, 3, 7, 8, 9, 10, 11], 'premium': 0, 'description': 'Shoulder season (Feb-Mar, Jul-Nov)'}
                }
            else:
                peak_seasons = {
                    'winter': {'months': [11, 12, 1, 2], 'premium': 0.15, 'description': 'Peak season (Nov-Feb)'},
                    'other': {'months': [3, 4, 5, 6, 7, 8, 9, 10], 'premium': -0.1, 'description': 'Off-peak (Mar-Oct)'}
                }
        else:
            peak_seasons = {
                'winter': {'months': [11, 12, 1, 2], 'premium': 0.15, 'description': 'Peak season (Nov-Feb)'},
                'other': {'months': [3, 4, 5, 6, 7, 8, 9, 10], 'premium': -0.1, 'description': 'Off-peak (Mar-Oct)'}
            }
        
        # Calculate target date range based on minimum time needed
        import datetime
        
        current_date = datetime.datetime.now()
        earliest_possible_date = current_date + datetime.timedelta(days=min_time_needed * 365)
        
        # Find optimal month based on seasonal factors
        optimal_months = []
        
        # Find off-peak months first (for cost savings)
        for season_name, season_data in peak_seasons.items():
            for month in season_data['months']:
                if season_data['premium'] < 0:  # Off-peak has negative premium (discount)
                    optimal_months.append((month, season_name, season_data['premium'], 'Cost savings'))
        
        # If no optimal months, add shoulder seasons
        if not optimal_months:
            for season_name, season_data in peak_seasons.items():
                for month in season_data['months']:
                    if season_data['premium'] == 0:  # Neutral/shoulder season
                        optimal_months.append((month, season_name, season_data['premium'], 'Balanced option'))
                        
        # If still no optimal months, add peak season
        if not optimal_months:
            for season_name, season_data in peak_seasons.items():
                for month in season_data['months']:
                    optimal_months.append((month, season_name, season_data['premium'], 'Traditional timing'))
        
        # Get target year based on earliest_possible_date
        target_year = earliest_possible_date.year
        
        # If earliest date falls after optimal months in current year, increment year
        if earliest_possible_date.month > max(month for month, _, _, _ in optimal_months):
            target_year += 1
        
        # Generate optimal date windows
        optimal_date_windows = []
        for month, season_name, premium, rationale in optimal_months:
            season_info = next((s for s_name, s in peak_seasons.items() if s_name == season_name), None)
            
            # Create date window for the month
            optimal_date_windows.append({
                'month': month,
                'month_name': datetime.date(2000, month, 1).strftime('%B'),
                'year': target_year,
                'season': season_name,
                'cost_impact': f"{premium*100:.1f}% {'premium' if premium > 0 else 'discount'}",
                'rationale': rationale,
                'description': season_info['description'] if season_info else 'Standard season'
            })
        
        # Calculate financial impact of optimal timing
        original_cost = wedding_cost
        optimal_timing_cost = wedding_cost
        
        # Apply seasonal discount/premium if specified
        if season:
            if season.lower() == 'peak':
                original_cost *= 1.25  # 25% premium for peak
            elif season.lower() == 'shoulder':
                original_cost *= 1.1   # 10% premium for shoulder
            elif season.lower() == 'off_peak':
                original_cost *= 0.85  # 15% discount for off-peak
        
        # Calculate potential savings from optimal timing
        best_discount = min(premium for _, _, premium, _ in optimal_months)
        optimal_timing_cost = wedding_cost * (1 + best_discount)
        potential_savings = original_cost - optimal_timing_cost
        
        # Generate timing recommendations
        recommendations = []
        
        if years_needed_for_savings > time_horizon:
            savings_shortfall = self_contribution - (current_savings + (monthly_contribution * time_horizon * 12))
            recommendations.append(f"Consider extending timeline to {max(1, round(years_needed_for_savings, 1))} years for adequate savings")
            needed_monthly = savings_shortfall / (time_horizon * 12)
            recommendations.append(f"Alternatively, increase monthly savings to ₹{round(needed_monthly)} to meet current timeline")
        
        if potential_savings > 0:
            recommendations.append(f"Consider off-peak season for potential savings of ₹{round(potential_savings)} ({abs(best_discount)*100}% reduction)")
        
        if time_horizon < planning_buffer:
            recommendations.append(f"Allow at least {int(planning_buffer*12)} months for planning a wedding of this size")
        
        return {
            'timing_assessment': {
                'current_timeline': f'{time_horizon:.1f} years',
                'savings_timeline_needed': f'{years_needed_for_savings:.1f} years' if years_needed_for_savings != float('inf') else 'Cannot determine without monthly savings',
                'planning_time_needed': f'{planning_buffer:.1f} years',
                'minimum_time_needed': f'{min_time_needed:.1f} years',
                'timeline_feasibility': 'Adequate' if time_horizon >= min_time_needed else 'Insufficient'
            },
            'seasonal_considerations': {
                'current_season': season or 'Not specified',
                'peak_seasons_info': {name: data['description'] for name, data in peak_seasons.items()},
                'cost_impact': {
                    'original_cost': round(original_cost),
                    'optimal_timing_cost': round(optimal_timing_cost),
                    'potential_savings': round(potential_savings)
                }
            },
            'optimal_timing_options': sorted(optimal_date_windows, key=lambda x: x['month']),
            'earliest_possible_date': earliest_possible_date.strftime('%Y-%m-%d'),
            'recommended_date_range': f"{target_year} {', '.join(window['month_name'] for window in sorted(optimal_date_windows, key=lambda x: x['month'])[:3])}",
            'recommendations': recommendations
        }
    
    def optimize_guest_list(self, goal_data):
        """
        Optimize the wedding guest list size based on budget constraints,
        venue options, and cultural expectations.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with optimized guest list recommendations
        """
        # Extract necessary information
        wedding_cost = goal_data.get('target_amount', 0)
        guest_count = goal_data.get('guest_count')
        tier = goal_data.get('tier', 'tier_1')
        category = goal_data.get('category', 'moderate')
        region = goal_data.get('region')
        
        # Determine current guest count (numeric or category)
        current_count = 0
        guest_category = 'medium'
        
        if isinstance(guest_count, int):
            current_count = guest_count
            if guest_count < 150:
                guest_category = 'small'
            elif guest_count < 300:
                guest_category = 'medium'
            elif guest_count < 500:
                guest_category = 'large'
            else:
                guest_category = 'very_large'
        elif isinstance(guest_count, str):
            guest_category = guest_count.lower()
            if guest_category == 'small':
                current_count = 100  # Average of "Under 150"
            elif guest_category == 'medium':
                current_count = 225  # Average of "150-300"
            elif guest_category == 'large':
                current_count = 400  # Average of "300-500"
            elif guest_category == 'very_large':
                current_count = 600  # Average of "Over 500"
            else:
                guest_category = 'medium'
                current_count = 225
        else:
            # Default if not specified
            guest_category = 'medium'
            current_count = 225
        
        # Get guest impact factor
        guest_impact = self.wedding_params['guest_count_impact'].get(
            guest_category, self.wedding_params['guest_count_impact']['medium']
        ).get('adjustment', 1.0)
        
        # Calculate per-guest cost
        # Venue + catering + invitation are directly impacted by guest count
        directly_impacted_percent = 0.6  # 60% of costs directly tied to guest count
        
        # Base cost calculation - what it would be with baseline guest count (medium)
        base_adjustment = self.wedding_params['guest_count_impact']['medium']['adjustment']
        base_cost = wedding_cost / guest_impact * base_adjustment
        
        # Calculate variable cost per guest
        variable_cost = (wedding_cost * directly_impacted_percent) / current_count
        
        # Calculate fixed costs (not directly tied to guest count)
        fixed_cost = wedding_cost * (1 - directly_impacted_percent)
        
        # Calculate cultural expectations for guest count
        cultural_expectation = {}
        if region:
            if region.lower() in ['north_india', 'west_india']:
                cultural_expectation = {
                    'typical_min': 200,
                    'typical_max': 500,
                    'description': 'North/West Indian weddings traditionally have larger guest lists'
                }
            elif region.lower() == 'south_india':
                cultural_expectation = {
                    'typical_min': 150,
                    'typical_max': 350,
                    'description': 'South Indian weddings typically more focused on ceremonies than guest count'
                }
            elif region.lower() == 'east_india':
                cultural_expectation = {
                    'typical_min': 150,
                    'typical_max': 400,
                    'description': 'East Indian weddings balance tradition with practical considerations'
                }
            else:
                cultural_expectation = {
                    'typical_min': 150,
                    'typical_max': 400,
                    'description': 'Standard Indian wedding guest expectations'
                }
        else:
            cultural_expectation = {
                'typical_min': 150,
                'typical_max': 400,
                'description': 'Standard Indian wedding guest expectations'
            }
        
        # Category-based expectations
        category_expectation = {}
        if category == 'budget':
            category_expectation = {
                'recommended_range': '100-150 guests',
                'lower_bound': 100,
                'upper_bound': 150,
                'description': 'Budget weddings typically have more intimate guest lists'
            }
        elif category == 'moderate':
            category_expectation = {
                'recommended_range': '150-300 guests',
                'lower_bound': 150,
                'upper_bound': 300,
                'description': 'Moderate weddings balance inclusivity with budget constraints'
            }
        elif category == 'premium':
            category_expectation = {
                'recommended_range': '300-500 guests',
                'lower_bound': 300,
                'upper_bound': 500,
                'description': 'Premium weddings often have substantial guest lists'
            }
        elif category == 'luxury':
            category_expectation = {
                'recommended_range': '400+ guests',
                'lower_bound': 400,
                'upper_bound': 800,
                'description': 'Luxury weddings typically have large guest lists with extended social networks'
            }
        
        # Generate guest list optimization scenarios
        scenarios = []
        
        # Calculate percentage reduction for each tier
        reductions = [0, 0.1, 0.2, 0.3, 0.4]  # 0%, 10%, 20%, 30%, 40%
        
        for reduction in reductions:
            reduced_count = int(current_count * (1 - reduction))
            
            # Skip if reduced count is below reasonable minimum
            if reduced_count < 50:
                continue
                
            # Calculate reduced cost
            reduced_variable_cost = variable_cost * reduced_count
            reduced_total_cost = fixed_cost + reduced_variable_cost
            
            # Calculate savings
            savings = wedding_cost - reduced_total_cost
            
            # Determine social impact assessment based on cultural expectations
            social_impact = 'Minimal'
            if reduced_count < cultural_expectation.get('typical_min', 150):
                social_impact = 'Significant'
            elif reduced_count < current_count * 0.8:
                social_impact = 'Moderate'
                
            # Create scenario
            scenarios.append({
                'reduction_percentage': round(reduction * 100),
                'guest_count': reduced_count,
                'estimated_cost': round(reduced_total_cost),
                'savings': round(savings),
                'savings_percentage': round(savings / wedding_cost * 100, 1),
                'social_impact': social_impact
            })
        
        # Determine optimal guest count based on budget and cultural considerations
        lower_bound = max(50, category_expectation.get('lower_bound', 150))
        upper_bound = min(current_count, category_expectation.get('upper_bound', 300))
        
        # Optimal is typically lower than current but within category expectations
        optimal_count = max(lower_bound, int(current_count * 0.8))
        
        # Calculate optimal cost
        optimal_variable_cost = variable_cost * optimal_count
        optimal_total_cost = fixed_cost + optimal_variable_cost
        optimal_savings = wedding_cost - optimal_total_cost
        
        # Generate guest list tiering strategy
        tiering_strategy = {}
        
        if optimal_count > 100:
            # Calculate 3-tier approach
            tier_1_count = int(optimal_count * 0.3)  # 30% close family and friends
            tier_2_count = int(optimal_count * 0.4)  # 40% extended family and close friends
            tier_3_count = optimal_count - tier_1_count - tier_2_count  # Remaining: acquaintances, colleagues, etc.
            
            tiering_strategy = {
                'tier_1': {
                    'description': 'Close family and friends',
                    'count': tier_1_count,
                    'percentage': round(tier_1_count / optimal_count * 100),
                    'invite_type': 'All ceremonies + reception'
                },
                'tier_2': {
                    'description': 'Extended family and friends',
                    'count': tier_2_count,
                    'percentage': round(tier_2_count / optimal_count * 100),
                    'invite_type': 'Main ceremony + reception'
                },
                'tier_3': {
                    'description': 'Acquaintances, colleagues, broader social circle',
                    'count': tier_3_count,
                    'percentage': round(tier_3_count / optimal_count * 100),
                    'invite_type': 'Reception only'
                }
            }
        
        # Generate recommendations
        recommendations = []
        
        if current_count > optimal_count:
            recommendations.append(f"Consider reducing guest list to {optimal_count} guests for better budget management")
        
        if current_count > category_expectation.get('upper_bound', 300):
            recommendations.append(f"Current guest count exceeds typical range for {category} weddings")
        
        if cultural_expectation.get('typical_min', 0) > optimal_count:
            recommendations.append(f"Be mindful that optimal count is below cultural norms ({cultural_expectation.get('typical_min')}-{cultural_expectation.get('typical_max')} guests)")
        
        if optimal_count > 150:
            recommendations.append("Consider tiered invitation strategy to manage costs while honoring social obligations")
        
        return {
            'guest_list_assessment': {
                'current_guest_count': current_count,
                'guest_category': guest_category,
                'per_guest_cost': round(variable_cost),
                'fixed_costs': round(fixed_cost),
                'cultural_guest_expectations': cultural_expectation,
                'category_based_expectations': category_expectation
            },
            'optimization_scenarios': scenarios,
            'optimized_guest_list': {
                'recommended_count': optimal_count,
                'estimated_cost': round(optimal_total_cost),
                'potential_savings': round(optimal_savings),
                'savings_percentage': round(optimal_savings / wedding_cost * 100, 1)
            },
            'guest_list_tiering_strategy': tiering_strategy,
            'recommendations': recommendations
        }
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive wedding/marriage funding strategy with optimization.
        
        This enhanced version includes optimization and constraint features to balance
        traditional wedding expectations with budget constraints, optimize between family
        contributions, loan options, and savings strategies.
        
        Args:
            goal_data: Dictionary with wedding goal details
            
        Returns:
            Dictionary with comprehensive wedding funding strategy
        """
        # Initialize optimization utilities if needed
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # Extract wedding specific information
        tier = goal_data.get('tier', 'tier_1')
        category = goal_data.get('category', 'moderate')
        region = goal_data.get('region')
        season = goal_data.get('season')
        guest_count = goal_data.get('guest_count', 'medium')
        time_horizon = goal_data.get('time_horizon', 1)
        risk_profile = goal_data.get('risk_profile', 'conservative')  # Weddings usually need conservative approach
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        self_contribution_percent = goal_data.get('self_contribution_percent', 50)
        priorities = goal_data.get('priorities', ['venue', 'catering'])
        
        # Calculate wedding cost if target amount not provided
        target_amount = goal_data.get('target_amount')
        if not target_amount:
            target_amount = self.estimate_wedding_cost(
                tier, category, region, season, guest_count
            )
            
        # Calculate self-contribution amount
        self_contribution = target_amount * (self_contribution_percent / 100)
        
        # Create wedding specific goal data
        wedding_goal = {
            'goal_type': 'wedding',
            'target_amount': self_contribution,  # Use self-contribution as target
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution,
            'season': season,
            'wedding_date': goal_data.get('wedding_date')  # If specific date is provided
        }
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(wedding_goal)
        
        # Enhanced with wedding specific analyses
        
        # Breakdown expenses
        expense_breakdown = self.breakdown_wedding_expenses(target_amount)
        
        # Calculate loan options
        loan_amount = self_contribution * 0.4  # Assume loan for 40% of self-contribution
        loan_analysis = self.calculate_wedding_loan(loan_amount)
        
        # Optimized budget allocation
        budget_optimization = self.plan_wedding_budget_optimization(target_amount, priorities)
        
        # Family contribution scenarios
        family_scenarios = self.analyze_family_contribution_scenarios(target_amount, self_contribution_percent)
        
        # Cost saving opportunities
        saving_opportunities = self.analyze_cost_saving_opportunities(target_amount, tier, category, guest_count)
        
        # Add rebalancing strategy if profile data is available
        profile_data = goal_data.get('profile_data')
        if profile_data:
            wedding_goal['rebalancing_strategy'] = self.integrate_rebalancing_strategy(
                wedding_goal, profile_data
            )
        
        # Combine into comprehensive strategy
        strategy = {
            **base_strategy,
            'wedding_details': {
                'estimated_cost': round(target_amount),
                'self_contribution': round(self_contribution),
                'self_contribution_percent': self_contribution_percent,
                'family_contribution': round(target_amount - self_contribution),
                'family_contribution_percent': 100 - self_contribution_percent,
                'tier': tier,
                'category': category,
                'guest_count': guest_count
            },
            'expense_breakdown': expense_breakdown,
            'loan_options': loan_analysis,
            'budget_optimization': budget_optimization,
            'family_contribution_scenarios': family_scenarios,
            'cost_saving_opportunities': saving_opportunities
        }
        
        # Add wedding specific savings allocation
        strategy['wedding_specific_allocation'] = self.recommend_wedding_allocation(time_horizon)
        
        # Add rebalancing strategy if available
        if 'rebalancing_strategy' in wedding_goal:
            strategy['rebalancing_strategy'] = wedding_goal['rebalancing_strategy']
        
        # Add wedding specific advice
        strategy['specific_advice'] = {
            'planning_timeline': [
                "12+ months: Set budget, rough guest list, and start savings plan",
                "9 months: Book venue, compare vendor quotes, continue regular savings",
                "6 months: Finalize major vendors, check saving progress, adjust if needed",
                "3 months: Final payments coming due, ensure liquidity of investments"
            ],
            'budgeting_approach': [
                "Allocate 50-60% to 'must-haves', 30-40% to 'nice-to-haves', 10% buffer",
                "Track all deposits and planned expenses in a dedicated spreadsheet",
                "Consider wedding insurance for major wedding investments",
                "Build in 10-15% contingency for unexpected costs"
            ],
            'post_wedding_considerations': [
                "Plan for merging finances post-wedding",
                "Set new joint financial goals as a couple",
                "Avoid depleting emergency fund for wedding expenses",
                "If taking a loan, create a dedicated repayment plan"
            ]
        }
        
        # Run constraint assessments
        budget_feasibility = self.assess_wedding_budget_feasibility(goal_data)
        wedding_timing = self.validate_wedding_timing(goal_data)
        cultural_assessment = self.assess_cultural_expectations(goal_data)
        family_contribution_assessment = self.validate_family_contribution_balance(goal_data)
        
        # Run optimization strategies
        wedding_budget_optimization = self.optimize_wedding_budget(goal_data)
        family_contribution_optimization = self.optimize_family_contribution(goal_data)
        wedding_timing_optimization = self.optimize_wedding_timing(goal_data)
        guest_list_optimization = self.optimize_guest_list(goal_data)
        
        # Add optimization and constraint assessment results to strategy
        strategy['optimizations'] = {
            'budget_optimization': wedding_budget_optimization,
            'family_contribution_optimization': family_contribution_optimization,
            'timing_optimization': wedding_timing_optimization,
            'guest_list_optimization': guest_list_optimization
        }
        
        strategy['constraint_assessments'] = {
            'budget_feasibility': budget_feasibility,
            'wedding_timing': wedding_timing,
            'cultural_expectations': cultural_assessment,
            'family_contribution_assessment': family_contribution_assessment
        }
        
        # Compile key recommendations from all optimizations
        key_recommendations = []
        
        # Add budget recommendations if significant savings possible
        budget_savings = wedding_budget_optimization.get('total_potential_savings', {}).get('total_possible_savings', 0)
        original_budget = wedding_budget_optimization.get('original_budget', target_amount)
        if budget_savings > original_budget * 0.2:  # If savings > 20%
            key_recommendations.append(f"Consider budget optimization for potential savings of ₹{round(budget_savings)} ({round(budget_savings/original_budget*100)}% of budget)")
        
        # Add family contribution recommendation if challenging affordability
        if family_contribution_assessment.get('affordability_assessment', {}).get('status') == 'Challenging':
            optimized_family_pct = family_contribution_optimization.get('optimized_contribution', {}).get('recommended_family_percentage')
            current_family_pct = family_contribution_optimization.get('current_contribution_split', {}).get('family_percentage')
            if optimized_family_pct > current_family_pct + 10:
                key_recommendations.append(f"Consider increasing family contribution from {current_family_pct}% to {optimized_family_pct}% for better financial feasibility")
        
        # Add timing recommendations if applicable
        if wedding_timing.get('timeline_feasibility') == 'Insufficient':
            needed_time = wedding_timing_optimization.get('timing_assessment', {}).get('minimum_time_needed', '1.0')
            key_recommendations.append(f"Consider extending timeline to at least {needed_time} years for adequate savings and planning")
        
        # Add guest list recommendation if significant savings possible
        guest_savings = guest_list_optimization.get('optimized_guest_list', {}).get('potential_savings', 0)
        if guest_savings > original_budget * 0.1:  # If savings > 10%
            optimal_count = guest_list_optimization.get('optimized_guest_list', {}).get('recommended_count')
            current_count = guest_list_optimization.get('guest_list_assessment', {}).get('current_guest_count')
            key_recommendations.append(f"Consider optimizing guest list from {current_count} to {optimal_count} guests to save ₹{round(guest_savings)}")
        
        # Add to strategy
        strategy['key_optimization_recommendations'] = key_recommendations
        
        return strategy