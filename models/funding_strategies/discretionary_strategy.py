import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator

logger = logging.getLogger(__name__)

class DiscretionaryGoalStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for discretionary goals like vacation,
    vehicle purchases, and general savings with India-specific considerations.
    """
    
    def __init__(self):
        """Initialize with discretionary goal specific parameters"""
        super().__init__()
        
        # Additional discretionary goal specific parameters
        self.discretionary_params = {
            "vacation_costs": {
                "domestic": {
                    "budget": 50000,      # Budget vacation in India
                    "mid_range": 100000,  # Mid-range vacation in India
                    "luxury": 200000      # Luxury vacation in India
                },
                "international": {
                    "budget": {
                        "asia": 150000,       # Budget Asia trip
                        "europe": 250000,     # Budget Europe trip
                        "americas": 300000,   # Budget Americas trip
                        "australia": 250000   # Budget Australia trip
                    },
                    "mid_range": {
                        "asia": 250000,
                        "europe": 400000,
                        "americas": 500000,
                        "australia": 400000
                    },
                    "luxury": {
                        "asia": 400000,
                        "europe": 700000,
                        "americas": 800000,
                        "australia": 700000
                    }
                }
            },
            "vehicle_costs": {
                "two_wheeler": {
                    "basic": 80000,        # Basic two-wheeler
                    "mid_range": 150000,   # Mid-range two-wheeler
                    "premium": 300000      # Premium two-wheeler
                },
                "car": {
                    "hatchback": {
                        "entry": 500000,    # Entry-level hatchback
                        "mid_range": 700000, # Mid-range hatchback
                        "premium": 1000000  # Premium hatchback
                    },
                    "sedan": {
                        "entry": 800000,
                        "mid_range": 1200000,
                        "premium": 2000000
                    },
                    "suv": {
                        "entry": 1000000,
                        "mid_range": 1500000,
                        "premium": 3000000
                    },
                    "luxury": {
                        "entry": 3500000,
                        "mid_range": 5000000,
                        "premium": 10000000
                    }
                },
                "electric": {
                    "two_wheeler": {
                        "entry": 100000,
                        "mid_range": 150000,
                        "premium": 250000
                    },
                    "car": {
                        "entry": 1000000,
                        "mid_range": 1500000,
                        "premium": 2500000
                    }
                }
            },
            "vehicle_loan_details": {
                "interest_rates": {
                    "two_wheeler": 0.12,    # 12% for two-wheeler loans
                    "car": {
                        "new": 0.09,        # 9% for new car loans
                        "used": 0.12,       # 12% for used car loans
                        "electric": 0.085   # 8.5% for electric vehicles
                    }
                },
                "loan_to_value": {
                    "two_wheeler": 0.85,    # 85% LTV for two-wheelers
                    "car": {
                        "new": 0.90,        # 90% LTV for new cars
                        "used": 0.70,       # 70% LTV for used cars
                        "electric": 0.95    # 95% LTV for electric vehicles
                    }
                },
                "tenure": {
                    "two_wheeler": 3,       # 3 years typical for two-wheelers
                    "car": {
                        "new": 7,           # 7 years typical for new cars
                        "used": 5,          # 5 years typical for used cars
                        "electric": 8       # 8 years typical for electric vehicles
                    }
                }
            },
            "general_savings_buckets": {
                "short_term_fun": {
                    "description": "Discretionary spending for entertainment, hobbies, etc.",
                    "typical_allocation": 0.3  # 30% of discretionary savings
                },
                "lifestyle_upgrade": {
                    "description": "Saving for lifestyle upgrades like electronics, furniture, etc.",
                    "typical_allocation": 0.4  # 40% of discretionary savings
                },
                "opportunity_fund": {
                    "description": "Funds for unexpected opportunities (not emergencies)",
                    "typical_allocation": 0.3  # 30% of discretionary savings
                }
            }
        }
        
        # Load discretionary goal specific parameters
        self._load_discretionary_parameters()
        
    def _load_discretionary_parameters(self):
        """Load discretionary goal specific parameters from service"""
        if self.param_service:
            try:
                # Load vacation costs
                vacation_costs = self.param_service.get_parameter('vacation_costs')
                if vacation_costs:
                    self.discretionary_params['vacation_costs'].update(vacation_costs)
                
                # Load vehicle costs
                vehicle_costs = self.param_service.get_parameter('vehicle_costs')
                if vehicle_costs:
                    self.discretionary_params['vehicle_costs'].update(vehicle_costs)
                
                # Load vehicle loan details
                vehicle_loan = self.param_service.get_parameter('vehicle_loan_details')
                if vehicle_loan:
                    self.discretionary_params['vehicle_loan_details'].update(vehicle_loan)
                
                # Load general savings buckets
                savings_buckets = self.param_service.get_parameter('general_savings_buckets')
                if savings_buckets:
                    self.discretionary_params['general_savings_buckets'].update(savings_buckets)
                
            except Exception as e:
                logger.error(f"Error loading discretionary goal parameters: {e}")
                # Continue with default parameters
    
    def estimate_vacation_cost(self, destination_type, destination=None, travel_class=None):
        """
        Estimate vacation cost based on destination and preferences.
        
        Args:
            destination_type: 'domestic' or 'international'
            destination: Specific destination or region (e.g., 'asia', 'europe')
            travel_class: 'budget', 'mid_range', or 'luxury'
            
        Returns:
            Estimated vacation cost
        """
        # Set defaults
        if not travel_class:
            travel_class = 'mid_range'
            
        # For domestic vacations
        if destination_type.lower() == 'domestic':
            return self.discretionary_params['vacation_costs']['domestic'].get(
                travel_class, self.discretionary_params['vacation_costs']['domestic']['mid_range']
            )
            
        # For international vacations
        else:
            # If no specific destination, use average of all regions
            if not destination:
                # Calculate average cost across all regions for the given travel class
                regions = self.discretionary_params['vacation_costs']['international'][travel_class]
                return sum(regions.values()) / len(regions)
                
            # If destination specified, use that cost
            return self.discretionary_params['vacation_costs']['international'].get(
                travel_class, {}
            ).get(destination, self.discretionary_params['vacation_costs']['international'][travel_class]['asia'])
    
    def estimate_vehicle_cost(self, vehicle_type, vehicle_class=None, vehicle_segment=None):
        """
        Estimate vehicle purchase cost.
        
        Args:
            vehicle_type: 'two_wheeler', 'car', or 'electric'
            vehicle_class: For cars - 'hatchback', 'sedan', 'suv', 'luxury'
                         For electric - 'two_wheeler', 'car'
            vehicle_segment: 'entry'/'basic', 'mid_range', or 'premium'
            
        Returns:
            Estimated vehicle cost
        """
        # Set defaults
        if not vehicle_segment:
            vehicle_segment = 'mid_range'
            
        # Normalize segment name
        if vehicle_segment == 'basic':
            vehicle_segment = 'entry'
            
        # For two wheelers
        if vehicle_type.lower() == 'two_wheeler':
            return self.discretionary_params['vehicle_costs']['two_wheeler'].get(
                vehicle_segment, self.discretionary_params['vehicle_costs']['two_wheeler']['mid_range']
            )
            
        # For electric vehicles
        elif vehicle_type.lower() == 'electric':
            if not vehicle_class:
                vehicle_class = 'car'
                
            return self.discretionary_params['vehicle_costs']['electric'].get(
                vehicle_class, {}
            ).get(vehicle_segment, self.discretionary_params['vehicle_costs']['electric']['car']['mid_range'])
            
        # For cars
        else:  # vehicle_type == 'car'
            if not vehicle_class:
                vehicle_class = 'hatchback'
                
            return self.discretionary_params['vehicle_costs']['car'].get(
                vehicle_class, {}
            ).get(vehicle_segment, self.discretionary_params['vehicle_costs']['car']['hatchback']['mid_range'])
    
    def calculate_vehicle_loan(self, vehicle_cost, vehicle_type, down_payment_percent=None,
                             is_used=False, is_electric=False):
        """
        Calculate vehicle loan details for vehicle purchase.
        
        Args:
            vehicle_cost: Total vehicle cost
            vehicle_type: 'two_wheeler' or 'car'
            down_payment_percent: Percentage of down payment (optional)
            is_used: Whether the vehicle is used/second-hand
            is_electric: Whether the vehicle is electric
            
        Returns:
            Dictionary with loan calculation details
        """
        # Determine appropriate loan-to-value ratio if down_payment_percent not provided
        if down_payment_percent is None:
            if vehicle_type.lower() == 'two_wheeler':
                loan_to_value = self.discretionary_params['vehicle_loan_details']['loan_to_value']['two_wheeler']
            elif is_electric:
                loan_to_value = self.discretionary_params['vehicle_loan_details']['loan_to_value']['car']['electric']
            elif is_used:
                loan_to_value = self.discretionary_params['vehicle_loan_details']['loan_to_value']['car']['used']
            else:
                loan_to_value = self.discretionary_params['vehicle_loan_details']['loan_to_value']['car']['new']
                
            down_payment_percent = 1 - loan_to_value
        
        # Calculate down payment and loan amount
        down_payment = vehicle_cost * down_payment_percent
        loan_amount = vehicle_cost - down_payment
        
        # Determine appropriate interest rate
        if vehicle_type.lower() == 'two_wheeler':
            interest_rate = self.discretionary_params['vehicle_loan_details']['interest_rates']['two_wheeler']
        elif is_electric:
            interest_rate = self.discretionary_params['vehicle_loan_details']['interest_rates']['car']['electric']
        elif is_used:
            interest_rate = self.discretionary_params['vehicle_loan_details']['interest_rates']['car']['used']
        else:
            interest_rate = self.discretionary_params['vehicle_loan_details']['interest_rates']['car']['new']
            
        # Determine appropriate tenure
        if vehicle_type.lower() == 'two_wheeler':
            tenure = self.discretionary_params['vehicle_loan_details']['tenure']['two_wheeler']
        elif is_electric:
            tenure = self.discretionary_params['vehicle_loan_details']['tenure']['car']['electric']
        elif is_used:
            tenure = self.discretionary_params['vehicle_loan_details']['tenure']['car']['used']
        else:
            tenure = self.discretionary_params['vehicle_loan_details']['tenure']['car']['new']
            
        # Calculate EMI
        monthly_rate = interest_rate / 12
        tenure_months = tenure * 12
        
        # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        
        # Calculate total interest payable
        total_payment = emi * tenure_months
        total_interest = total_payment - loan_amount
        
        return {
            'vehicle_cost': vehicle_cost,
            'down_payment': round(down_payment),
            'down_payment_percent': round(down_payment_percent * 100, 1),
            'loan_amount': round(loan_amount),
            'interest_rate': round(interest_rate * 100, 2),
            'tenure_years': tenure,
            'monthly_emi': round(emi),
            'total_interest': round(total_interest),
            'total_payment': round(total_payment),
            'cost_of_loan': round(total_interest / loan_amount * 100, 1)
        }
    
    def create_savings_automation_plan(self, monthly_amount, goal_type, time_horizon):
        """
        Create an automation plan for discretionary goal savings.
        
        Args:
            monthly_amount: Monthly amount to save
            goal_type: Type of discretionary goal
            time_horizon: Years to goal
            
        Returns:
            Dictionary with automation plan details
        """
        # Determine appropriate automation approach based on goal type and time horizon
        if time_horizon < 1:
            # Very short-term goals (less than 1 year)
            frequency = 'fortnightly'
            primary_method = 'auto-debit to savings account'
            sweep_percent = 80  # 80% in sweep account
            liquid_percent = 20  # 20% in liquid fund
            
        elif time_horizon < 2:
            # Short-term goals (1-2 years)
            frequency = 'monthly'
            primary_method = 'SIP in liquid funds'
            liquid_percent = 70  # 70% in liquid funds
            short_debt_percent = 30  # 30% in short-term debt funds
            
        elif time_horizon < 3:
            # Medium-term goals (2-3 years)
            frequency = 'monthly'
            primary_method = 'SIP in debt funds'
            short_debt_percent = 60  # 60% in short-term debt
            balanced_percent = 40  # 40% in balanced funds
            
        else:
            # Longer-term discretionary goals (3+ years)
            frequency = 'monthly'
            primary_method = 'SIP in balanced funds'
            balanced_percent = 60  # 60% in balanced funds
            equity_percent = 40  # 40% in equity funds
        
        # Create automation plan based on goal type
        if goal_type.lower() in ('vacation', 'travel'):
            plan = {
                'goal_type': 'Vacation/Travel',
                'automation_frequency': frequency,
                'primary_method': primary_method,
                'additional_methods': [
                    'Round-up savings from daily transactions',
                    'Vacation-specific sub-account',
                    'Travel rewards credit card for additional savings'
                ]
            }
            
        elif goal_type.lower() in ('vehicle', 'car', 'two_wheeler'):
            plan = {
                'goal_type': 'Vehicle Purchase',
                'automation_frequency': frequency,
                'primary_method': primary_method,
                'additional_methods': [
                    'Vehicle RD (Recurring Deposit)',
                    'Separate bank account for vehicle fund',
                    'Annual bonus allocation'
                ]
            }
            
        else:  # General savings
            plan = {
                'goal_type': 'General Savings',
                'automation_frequency': frequency,
                'primary_method': primary_method,
                'additional_methods': [
                    'Automated transfers after salary credit',
                    'Spending-linked savings (save X% of what you spend)',
                    'Windfall allocation strategy (bonuses, tax refunds, etc.)'
                ]
            }
            
        # Add allocation strategy based on time horizon
        if time_horizon < 1:
            plan['allocation_strategy'] = {
                'sweep_account': f"{sweep_percent}%",
                'liquid_funds': f"{liquid_percent}%"
            }
        elif time_horizon < 2:
            plan['allocation_strategy'] = {
                'liquid_funds': f"{liquid_percent}%",
                'short_term_debt': f"{short_debt_percent}%"
            }
        elif time_horizon < 3:
            plan['allocation_strategy'] = {
                'short_term_debt': f"{short_debt_percent}%",
                'balanced_funds': f"{balanced_percent}%"
            }
        else:
            plan['allocation_strategy'] = {
                'balanced_funds': f"{balanced_percent}%",
                'equity_funds': f"{equity_percent}%"
            }
            
        # Add specific automation steps
        plan['implementation_steps'] = [
            f"Set up {frequency} automated transfer of ₹{round(monthly_amount)}",
            f"Allocate to investment options according to allocation strategy",
            "Set up tracking and monitoring alerts",
            "Review and adjust quarterly"
        ]
        
        return plan
    
    def optimize_goal_amount(self, goal_type, base_amount, financial_capacity, 
                           time_horizon, priority_level='medium'):
        """
        Optimize discretionary goal amount based on financial capacity.
        
        Args:
            goal_type: Type of discretionary goal
            base_amount: Base goal amount
            financial_capacity: Dictionary with income and savings details
            time_horizon: Years to goal
            priority_level: 'low', 'medium', or 'high'
            
        Returns:
            Dictionary with optimized goal amount recommendations
        """
        # Extract financial capacity details
        monthly_income = financial_capacity.get('monthly_income', 100000)
        monthly_expenses = financial_capacity.get('monthly_expenses', 70000)
        existing_savings = financial_capacity.get('existing_savings', 0)
        monthly_surplus = financial_capacity.get('monthly_surplus', monthly_income - monthly_expenses)
        monthly_savings_capacity = financial_capacity.get('monthly_savings_capacity', monthly_surplus * 0.7)
        
        # Calculate maximum amount that can be saved in the given time horizon
        max_savings_possible = monthly_savings_capacity * time_horizon * 12 + existing_savings
        
        # Determine what percentage of savings capacity should go to this goal
        # based on priority level
        if priority_level.lower() == 'high':
            allocation_percent = 0.5  # 50% of savings capacity
        elif priority_level.lower() == 'low':
            allocation_percent = 0.2  # 20% of savings capacity
        else:  # medium
            allocation_percent = 0.3  # 30% of savings capacity
            
        # Calculate financially comfortable goal amount
        comfortable_amount = max_savings_possible * allocation_percent
        
        # Calculate minimum viable amount (70% of base)
        minimum_viable = base_amount * 0.7
        
        # Calculate aspirational amount (120% of base)
        aspirational_amount = base_amount * 1.2
        
        # Determine recommended amount based on financial capacity
        if comfortable_amount >= aspirational_amount:
            recommended_amount = aspirational_amount
            stretch_factor = "Easily achievable"
        elif comfortable_amount >= base_amount:
            recommended_amount = comfortable_amount
            stretch_factor = "Comfortably achievable"
        elif comfortable_amount >= minimum_viable:
            recommended_amount = comfortable_amount
            stretch_factor = "Reasonably achievable"
        else:
            recommended_amount = minimum_viable
            stretch_factor = "Financial stretch"
            
        # Calculate required monthly savings
        required_monthly = max(0, (recommended_amount - existing_savings) / (time_horizon * 12))
        
        # Calculate percentage of monthly surplus
        percent_of_surplus = (required_monthly / monthly_surplus * 100) if monthly_surplus > 0 else 0
        
        return {
            'original_goal_amount': base_amount,
            'recommended_amount': round(recommended_amount),
            'stretch_factor': stretch_factor,
            'options': {
                'minimum_viable': round(minimum_viable),
                'base_amount': round(base_amount),
                'aspirational': round(aspirational_amount)
            },
            'financial_impact': {
                'required_monthly_savings': round(required_monthly),
                'percent_of_monthly_surplus': round(percent_of_surplus, 1),
                'percent_of_savings_capacity': round(required_monthly / monthly_savings_capacity * 100, 1) if monthly_savings_capacity > 0 else 0
            }
        }
    
    def analyze_goal_tradeoffs(self, goal_data, other_goals=None):
        """
        Analyze tradeoffs between this discretionary goal and other financial priorities.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            other_goals: List of other financial goals and priorities (optional)
            
        Returns:
            Dictionary with tradeoff analysis
        """
        # Extract goal details
        goal_type = goal_data.get('goal_type', 'general savings')
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 1)
        priority_level = goal_data.get('priority_level', 'medium')
        
        # If other goals not provided, use some defaults for comparison
        if not other_goals:
            other_goals = [
                {'goal_type': 'emergency_fund', 'priority_level': 'high', 'status': 'in_progress'},
                {'goal_type': 'retirement', 'priority_level': 'high', 'status': 'in_progress'},
                {'goal_type': 'debt_repayment', 'priority_level': 'medium', 'status': 'in_progress'},
                {'goal_type': 'home_purchase', 'priority_level': 'medium', 'status': 'in_progress'},
                {'goal_type': 'education', 'priority_level': 'medium', 'status': 'in_progress'}
            ]
            
        # Define priority hierarchy for financial goals
        priority_hierarchy = {
            'emergency_fund': 1,
            'debt_repayment': 2,
            'retirement': 3,
            'education': 4,
            'home_purchase': 5,
            'vacation': 7,
            'travel': 7,
            'vehicle': 6,
            'car': 6,
            'two_wheeler': 6,
            'general_savings': 8
        }
        
        # Get normalized goal type for checking
        norm_goal_type = goal_type.lower().replace('_', '').replace(' ', '_')
        
        # Get priority level of current goal
        current_goal_priority = priority_hierarchy.get(norm_goal_type, 8)
        
        # Analyze potential impact on other goals
        impact_analysis = []
        
        for other_goal in other_goals:
            other_type = other_goal.get('goal_type', '').lower().replace('_', '').replace(' ', '_')
            other_priority = priority_hierarchy.get(other_type, 8)
            other_priority_level = other_goal.get('priority_level', 'medium')
            other_status = other_goal.get('status', 'in_progress')
            
            # Calculate impact
            if other_priority < current_goal_priority:
                # Higher priority goal
                if other_status == 'completed':
                    impact = "No impact - this goal is already completed"
                elif other_priority_level == 'high' and priority_level == 'high':
                    impact = "Significant impact - competing high-priority goals"
                elif other_priority_level == 'high':
                    impact = "Moderate impact - may delay higher-priority goal"
                else:
                    impact = "Minor impact - slight delay to higher-priority goal"
            else:
                # Equal or lower priority goal
                impact = "Minimal impact - appropriate prioritization"
                
            impact_analysis.append({
                'goal_type': other_goal.get('goal_type'),
                'priority_level': other_priority_level,
                'relative_priority': 'Higher' if other_priority < current_goal_priority else ('Equal' if other_priority == current_goal_priority else 'Lower'),
                'potential_impact': impact
            })
        
        # Determine opportunity cost
        # Calculate what this money could become if invested for long-term
        # Assume a moderate 8% return for long-term investment
        long_term_opportunity = target_amount * ((1 + 0.08) ** 20)  # 20 years
        
        # Calculate what the monthly savings could become if redirected to retirement
        monthly_savings = target_amount / (time_horizon * 12) if time_horizon > 0 else target_amount
        monthly_retirement_impact = monthly_savings * (((1 + 0.08/12) ** (30*12) - 1) / (0.08/12))  # 30 years
        
        # Make recommendation based on analysis
        if any(g.get('priority_level') == 'high' and g.get('status') == 'not_started' for g in other_goals):
            recommendation = "Defer this goal until high-priority financial foundations are established"
        elif target_amount > 500000 and time_horizon < 2:
            recommendation = "Consider extending the time horizon to reduce monthly financial strain"
        else:
            recommendation = "Goal appears appropriate within your financial priorities"
            
        return {
            'goal_type': goal_type,
            'target_amount': target_amount,
            'priority_relative_ranking': current_goal_priority,
            'impact_on_other_goals': impact_analysis,
            'opportunity_cost': {
                'long_term_investment_potential': round(long_term_opportunity),
                'monthly_retirement_impact': round(monthly_retirement_impact),
                'equivalent_purchases': [
                    {'item': 'Emergency fund contribution', 'value': f"{round(target_amount * 0.5)} to {round(target_amount * 1.0)}"},
                    {'item': 'Retirement fund contribution', 'value': f"{round(target_amount * 0.5)} to {round(target_amount * 1.0)}"},
                    {'item': 'Debt reduction', 'value': f"₹{round(target_amount)} of high-interest debt"}
                ]
            },
            'recommendation': recommendation,
            'balancing_strategy': [
                "Ensure emergency fund is fully funded first",
                "Maintain retirement contributions while saving for this goal",
                "Consider a slightly longer time horizon to reduce monthly burden",
                "Look for ways to reduce the cost without compromising core experience",
                "Continue regular investment in long-term goals alongside this goal"
            ]
        }
    
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with discretionary-specific optimization parameters
            super()._initialize_optimizer()
            
            # Add discretionary-specific optimization constraints to the optimizer
            self.optimizer.add_constraint('maximum_discretionary_spending_ratio', 0.2)  # Max 20% of income on discretionary
            self.optimizer.add_constraint('minimum_essential_goals_funded', 0.8)  # 80% of essential goals funded
            self.optimizer.add_constraint('maximum_priority_deviation', 0.15)  # 15% max deviation from priority allocation
            self.optimizer.add_constraint('maximum_time_horizon_extension', 0.5)  # Max 50% extension of time horizon
    
    def _initialize_constraints(self):
        """Initialize the funding constraints with lazy loading pattern"""
        if not hasattr(self, 'constraints') or self.constraints is None:
            # Initialize base constraints
            super()._initialize_constraints()
            
            # Add discretionary-specific constraints methods
            self.constraints.add_constraint_method('assess_goal_affordability', self.assess_goal_affordability)
            self.constraints.add_constraint_method('validate_priority_balance', self.validate_priority_balance)
            self.constraints.add_constraint_method('assess_goal_timing', self.assess_goal_timing)
    
    def _initialize_compound_strategy(self):
        """Initialize the compound strategy with lazy loading pattern"""
        if not hasattr(self, 'compound_strategy') or self.compound_strategy is None:
            # Initialize base compound strategy
            super()._initialize_compound_strategy()
            
            # Configure for discretionary goal specific needs
            self.compound_strategy.add_sub_strategy('timing_optimization', self.optimize_goal_timing)
            self.compound_strategy.add_sub_strategy('priority_optimization', self.optimize_goal_priority)
            self.compound_strategy.add_sub_strategy('multi_goal_coordination', self.coordinate_multiple_goals)
    
    def assess_goal_affordability(self, goal_data, other_goals=None):
        """
        Assess if the discretionary goal is affordable given the user's financial situation
        and other financial priorities.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            other_goals: List of other financial goals (optional)
            
        Returns:
            Dictionary with affordability assessment
        """
        # Extract necessary information
        target_amount = goal_data.get('target_amount', 0)
        time_horizon = goal_data.get('time_horizon', 1)
        monthly_income = goal_data.get('monthly_income', 100000)
        monthly_expenses = goal_data.get('monthly_expenses', 70000)
        current_savings = goal_data.get('current_savings', 0)
        priority_level = goal_data.get('priority_level', 'medium')
        
        # Calculate monthly surplus
        monthly_surplus = monthly_income - monthly_expenses
        
        # Calculate required monthly contribution
        remaining_amount = max(0, target_amount - current_savings)
        required_monthly = remaining_amount / (time_horizon * 12) if time_horizon > 0 else remaining_amount
        
        # Calculate percentage of monthly surplus required
        percent_of_surplus = required_monthly / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
        
        # Determine affordability thresholds based on priority level
        if priority_level.lower() == 'high':
            comfortable_threshold = 30  # Up to 30% of surplus for high priority
            stretched_threshold = 50     # Up to 50% of surplus is stretched but possible
        elif priority_level.lower() == 'low':
            comfortable_threshold = 10  # Up to 10% of surplus for low priority
            stretched_threshold = 20     # Up to 20% of surplus is stretched but possible
        else:  # medium priority
            comfortable_threshold = 20  # Up to 20% of surplus for medium priority
            stretched_threshold = 35     # Up to 35% of surplus is stretched but possible
        
        # Assess affordability
        if percent_of_surplus <= comfortable_threshold:
            affordability_status = 'Comfortably Affordable'
            affordability_description = f"This goal requires {percent_of_surplus:.1f}% of your monthly surplus, which is well within your means"
        elif percent_of_surplus <= stretched_threshold:
            affordability_status = 'Moderately Affordable'
            affordability_description = f"This goal requires {percent_of_surplus:.1f}% of your monthly surplus, which is manageable but will require some discipline"
        elif percent_of_surplus <= 100:
            affordability_status = 'Stretched but Possible'
            affordability_description = f"This goal requires {percent_of_surplus:.1f}% of your monthly surplus, which will significantly limit other discretionary spending"
        else:
            affordability_status = 'Not Affordable'
            affordability_description = f"This goal requires more than your entire monthly surplus ({percent_of_surplus:.1f}%), making it unaffordable in the current timeframe"
        
        # Check impact on other financial goals
        other_goals_impact = "No impact assessment available"
        if other_goals:
            essential_goals = [g for g in other_goals if g.get('goal_type') in 
                              ['emergency_fund', 'debt_repayment', 'retirement']]
            
            if essential_goals:
                essential_funding_required = sum(self._calculate_monthly_funding_need(g) for g in essential_goals)
                remaining_after_essential = monthly_surplus - essential_funding_required
                
                if remaining_after_essential <= 0:
                    other_goals_impact = "Essential financial goals already require your entire surplus. This goal will compete with those priorities."
                elif required_monthly > remaining_after_essential:
                    other_goals_impact = f"This goal will require {(required_monthly/essential_funding_required*100):.1f}% of the funding needed for essential goals, potentially delaying those priorities."
                else:
                    other_goals_impact = f"This goal can be funded without impacting essential financial priorities, using {(required_monthly/remaining_after_essential*100):.1f}% of remaining surplus."
        
        # Determine options to improve affordability
        improvement_options = []
        
        if percent_of_surplus > comfortable_threshold:
            # Calculate extended time horizon to bring to comfortable level
            extended_months = math.ceil(remaining_amount / (monthly_surplus * comfortable_threshold / 100))
            extended_years = extended_months / 12
            
            improvement_options.append({
                'approach': 'Extend Time Horizon',
                'details': f"Extending the time horizon to {extended_years:.1f} years would bring this goal to a comfortable affordability level",
                'revised_monthly': round(monthly_surplus * comfortable_threshold / 100)
            })
            
            # Calculate reduced goal amount to bring to comfortable level
            reduced_amount = monthly_surplus * comfortable_threshold / 100 * time_horizon * 12 + current_savings
            reduction_percent = (target_amount - reduced_amount) / target_amount * 100
            
            improvement_options.append({
                'approach': 'Adjust Goal Amount',
                'details': f"Reducing the goal amount by {reduction_percent:.1f}% would bring this goal to a comfortable affordability level",
                'revised_amount': round(reduced_amount)
            })
            
            # Adjust priority level
            if priority_level.lower() != 'low':
                lower_priority = 'medium' if priority_level.lower() == 'high' else 'low'
                improvement_options.append({
                    'approach': 'Adjust Priority Level',
                    'details': f"Considering this as a {lower_priority} priority goal would allow for a more appropriate allocation of resources"
                })
        
        return {
            'goal_amount': round(target_amount),
            'required_monthly_contribution': round(required_monthly),
            'percent_of_monthly_surplus': round(percent_of_surplus, 1),
            'affordability_status': affordability_status,
            'affordability_description': affordability_description,
            'impact_on_other_goals': other_goals_impact,
            'improvement_options': improvement_options
        }
    
    def validate_priority_balance(self, goal_data, other_goals=None):
        """
        Validate if the priority level of this discretionary goal is appropriate
        given the user's financial situation and other goals.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            other_goals: List of other financial goals (optional)
            
        Returns:
            Dictionary with priority balance assessment
        """
        # Extract necessary information
        goal_type = goal_data.get('goal_type', 'general_savings')
        priority_level = goal_data.get('priority_level', 'medium')
        target_amount = goal_data.get('target_amount', 0)
        annual_income = goal_data.get('monthly_income', 100000) * 12
        
        # Define priority hierarchy for financial goals
        priority_hierarchy = {
            'emergency_fund': 1,
            'debt_repayment': 2,
            'retirement': 3,
            'education': 4,
            'home_purchase': 5,
            'vacation': 7,
            'travel': 7,
            'vehicle': 6,
            'car': 6,
            'two_wheeler': 6,
            'general_savings': 8
        }
        
        # Get normalized goal type
        norm_goal_type = goal_type.lower().replace('_', '').replace(' ', '_')
        current_goal_priority = priority_hierarchy.get(norm_goal_type, 8)
        
        # Check if priority level is appropriate for goal type
        priority_appropriateness = 'Appropriate'
        priority_rationale = f"This {priority_level} priority level is typical for a {goal_type} goal"
        
        # Typical priority levels for different goal types
        typical_priority = {
            'vacation': 'low',
            'travel': 'low',
            'vehicle': 'medium',
            'car': 'medium',
            'two_wheeler': 'medium',
            'electronics': 'low',
            'hobby': 'low',
            'home_improvement': 'medium',
            'general_savings': 'low'
        }
        
        # Normalize goal type for checking
        check_type = norm_goal_type
        if check_type not in typical_priority:
            # Use a more general category if specific one not found
            for general_type in ['vacation', 'vehicle', 'general_savings']:
                if general_type in norm_goal_type:
                    check_type = general_type
                    break
            
            # If still not found, default to general_savings
            if check_type not in typical_priority:
                check_type = 'general_savings'
        
        # Check if priority is higher than typical
        if typical_priority[check_type] == 'low' and priority_level.lower() in ['medium', 'high']:
            priority_appropriateness = 'Higher than typical'
            priority_rationale = f"A {priority_level} priority is higher than the typical '{typical_priority[check_type]}' priority for {goal_type} goals"
        elif typical_priority[check_type] == 'medium' and priority_level.lower() == 'high':
            priority_appropriateness = 'Higher than typical'
            priority_rationale = f"A {priority_level} priority is higher than the typical '{typical_priority[check_type]}' priority for {goal_type} goals"
        
        # Check amount relative to income
        income_ratio = target_amount / annual_income
        
        if income_ratio > 0.5 and priority_level.lower() in ['medium', 'high']:
            priority_appropriateness = 'Potentially misaligned'
            priority_rationale = f"This goal represents {income_ratio*100:.1f}% of annual income, which is high for a {priority_level} priority discretionary goal"
        
        # Check impact on essential financial goals
        essential_goals_funded = True
        essential_goals_status = "No data on essential goals"
        
        if other_goals:
            essential_goals = [g for g in other_goals if g.get('goal_type') in 
                              ['emergency_fund', 'debt_repayment', 'retirement']]
            
            if essential_goals:
                unfunded_essential = [g for g in essential_goals if g.get('status') == 'not_started' or 
                                     (g.get('progress_percent', 0) < 50 and g.get('status') != 'completed')]
                
                if unfunded_essential:
                    essential_goals_funded = False
                    essential_goals_status = f"{len(unfunded_essential)} essential financial goals are insufficiently funded"
                else:
                    essential_goals_status = "All essential financial goals appear to be adequately funded"
        
        # Generate recommendations
        recommendations = []
        
        if priority_appropriateness != 'Appropriate':
            recommendations.append(f"Consider adjusting priority to '{typical_priority[check_type]}' to better align with financial best practices")
            
        if not essential_goals_funded and priority_level.lower() in ['medium', 'high']:
            recommendations.append("Focus on funding essential goals (emergency fund, debt repayment, retirement) before prioritizing this discretionary goal")
            
        if income_ratio > 0.3:
            recommendations.append(f"The goal amount is {income_ratio*100:.1f}% of annual income, which is significant. Consider a more modest goal or extended timeframe.")
        
        return {
            'goal_type': goal_type,
            'assigned_priority': priority_level,
            'typical_priority': typical_priority.get(check_type, 'low'),
            'priority_appropriateness': priority_appropriateness,
            'priority_rationale': priority_rationale,
            'goal_amount_to_income_ratio': f"{income_ratio*100:.1f}%",
            'essential_goals_status': essential_goals_status,
            'recommendations': recommendations
        }
    
    def assess_goal_timing(self, goal_data):
        """
        Assess if the timing of the discretionary goal is appropriate.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            
        Returns:
            Dictionary with timing assessment
        """
        # Extract necessary information
        goal_type = goal_data.get('goal_type', 'general_savings')
        time_horizon = goal_data.get('time_horizon', 1)
        target_amount = goal_data.get('target_amount', 0)
        current_savings = goal_data.get('current_savings', 0)
        monthly_income = goal_data.get('monthly_income', 100000)
        monthly_expenses = goal_data.get('monthly_expenses', 70000)
        
        # Calculate monthly surplus
        monthly_surplus = monthly_income - monthly_expenses
        
        # Calculate required monthly contribution
        remaining_amount = max(0, target_amount - current_savings)
        required_monthly = remaining_amount / (time_horizon * 12) if time_horizon > 0 else remaining_amount
        
        # Calculate percentage of monthly surplus required
        percent_of_surplus = required_monthly / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
        
        # Define appropriate time horizons for different goal types
        min_appropriate_horizon = 0.5  # 6 months minimum for any goal
        
        # Typical time horizons based on goal type and amount
        if goal_type.lower() in ['vacation', 'travel']:
            # For vacations, timing depends on cost relative to monthly income
            cost_to_income_ratio = target_amount / monthly_income
            
            if cost_to_income_ratio <= 1:
                # Less than 1 month's income: 3-6 months
                recommended_min = 0.25  # 3 months
                recommended_max = 0.5   # 6 months
            elif cost_to_income_ratio <= 3:
                # 1-3 months income: 6-12 months
                recommended_min = 0.5   # 6 months
                recommended_max = 1     # 1 year
            else:
                # More than 3 months income: 1-2 years
                recommended_min = 1     # 1 year
                recommended_max = 2     # 2 years
        
        elif goal_type.lower() in ['vehicle', 'car', 'two_wheeler']:
            # For vehicles, timing depends on cost relative to annual income
            annual_income = monthly_income * 12
            cost_to_annual_income_ratio = target_amount / annual_income
            
            if cost_to_annual_income_ratio <= 0.2:
                # Less than 20% of annual income: 6-12 months
                recommended_min = 0.5   # 6 months
                recommended_max = 1     # 1 year
            elif cost_to_annual_income_ratio <= 0.5:
                # 20-50% of annual income: 1-3 years
                recommended_min = 1     # 1 year
                recommended_max = 3     # 3 years
            else:
                # More than 50% of annual income: 3-5 years
                recommended_min = 3     # 3 years
                recommended_max = 5     # 5 years
        
        else:  # General savings or other discretionary goals
            # For general savings, timing depends on amount relative to monthly surplus
            months_of_surplus = target_amount / monthly_surplus if monthly_surplus > 0 else float('inf')
            
            if months_of_surplus <= 6:
                # Up to 6 months of surplus: 3-9 months
                recommended_min = 0.25  # 3 months
                recommended_max = 0.75  # 9 months
            elif months_of_surplus <= 12:
                # 6-12 months of surplus: 6-18 months
                recommended_min = 0.5   # 6 months
                recommended_max = 1.5   # 18 months
            else:
                # More than 12 months of surplus: 1-3 years
                recommended_min = 1     # 1 year
                recommended_max = 3     # 3 years
        
        # Assess timing appropriateness
        if time_horizon < recommended_min:
            timing_status = 'Too Short'
            timing_description = f"The current time horizon of {time_horizon} years is shorter than the recommended minimum of {recommended_min} years for this goal"
        elif time_horizon > recommended_max * 1.5:
            timing_status = 'Unnecessarily Long'
            timing_description = f"The current time horizon of {time_horizon} years is considerably longer than the recommended maximum of {recommended_max} years for this goal"
        else:
            timing_status = 'Appropriate'
            timing_description = f"The current time horizon of {time_horizon} years is within the recommended range of {recommended_min}-{recommended_max} years for this goal"
        
        # Provide recommendations for time horizon adjustment
        recommendations = []
        
        if timing_status == 'Too Short':
            # Calculate a more realistic time horizon
            realistic_horizon = max(recommended_min, math.ceil(remaining_amount / (monthly_surplus * 0.3) / 12))
            recommendations.append(f"Consider extending the time horizon to at least {realistic_horizon} years for more manageable monthly contributions")
            
            # Calculate what percentage of surplus would be required with recommended min
            adjusted_monthly = remaining_amount / (recommended_min * 12)
            adjusted_percent = adjusted_monthly / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
            
            recommendations.append(f"With a {recommended_min} year time horizon, monthly contributions would be ₹{round(adjusted_monthly)} ({adjusted_percent:.1f}% of monthly surplus)")
            
        elif timing_status == 'Unnecessarily Long':
            # Calculate a more efficient time horizon
            efficient_horizon = min(recommended_max, math.ceil(remaining_amount / (monthly_surplus * 0.2) / 12))
            
            if efficient_horizon < time_horizon:
                recommendations.append(f"Consider shortening the time horizon to around {efficient_horizon} years for more efficient goal achievement")
                
                # Calculate what percentage of surplus would be required with recommended max
                adjusted_monthly = remaining_amount / (efficient_horizon * 12)
                adjusted_percent = adjusted_monthly / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
                
                recommendations.append(f"With a {efficient_horizon} year time horizon, monthly contributions would be ₹{round(adjusted_monthly)} ({adjusted_percent:.1f}% of monthly surplus)")
        
        # If timing is appropriate but monthly burden is too high
        if timing_status == 'Appropriate' and percent_of_surplus > 30:
            # Calculate an extended time horizon for better affordability
            extended_horizon = math.ceil(remaining_amount / (monthly_surplus * 0.3) / 12)
            
            if extended_horizon > time_horizon:
                recommendations.append(f"While the current time horizon is appropriate for this type of goal, extending to {extended_horizon} years would reduce the monthly burden to a more manageable level")
        
        return {
            'goal_type': goal_type,
            'current_time_horizon': time_horizon,
            'recommended_range': f"{recommended_min}-{recommended_max} years",
            'timing_status': timing_status,
            'timing_description': timing_description,
            'required_monthly_contribution': round(required_monthly),
            'percent_of_monthly_surplus': round(percent_of_surplus, 1),
            'recommendations': recommendations
        }
    
    def optimize_goal_timing(self, goal_data):
        """
        Optimize the timing of the discretionary goal based on financial capacity
        and goal importance.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            
        Returns:
            Dictionary with optimized timing recommendations
        """
        # Extract necessary information
        goal_type = goal_data.get('goal_type', 'general_savings')
        current_time_horizon = goal_data.get('time_horizon', 1)
        target_amount = goal_data.get('target_amount', 0)
        current_savings = goal_data.get('current_savings', 0)
        monthly_income = goal_data.get('monthly_income', 100000)
        monthly_expenses = goal_data.get('monthly_expenses', 70000)
        priority_level = goal_data.get('priority_level', 'medium')
        annual_income = monthly_income * 12
        
        # Calculate monthly surplus
        monthly_surplus = monthly_income - monthly_expenses
        
        # Calculate remaining amount
        remaining_amount = max(0, target_amount - current_savings)
        
        # Define priority-based surplus allocation percentages
        if priority_level.lower() == 'high':
            max_surplus_allocation = 0.4  # Up to 40% of surplus for high priority
            ideal_surplus_allocation = 0.3  # Ideally 30% of surplus
        elif priority_level.lower() == 'low':
            max_surplus_allocation = 0.2  # Up to 20% of surplus for low priority
            ideal_surplus_allocation = 0.1  # Ideally 10% of surplus
        else:  # medium priority
            max_surplus_allocation = 0.3  # Up to 30% of surplus for medium priority
            ideal_surplus_allocation = 0.2  # Ideally 20% of surplus
        
        # Calculate potential time horizons
        minimum_horizon = math.ceil(remaining_amount / (monthly_surplus * max_surplus_allocation) / 12)
        ideal_horizon = math.ceil(remaining_amount / (monthly_surplus * ideal_surplus_allocation) / 12)
        comfortable_horizon = max(minimum_horizon, ideal_horizon * 1.2)  # Add 20% buffer to ideal
        
        # Calculate current monthly contribution and percent of surplus
        current_monthly = remaining_amount / (current_time_horizon * 12) if current_time_horizon > 0 else remaining_amount
        current_percent = current_monthly / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
        
        # For certain goal types, consider time-sensitivity and seasonality
        seasonal_factors = {}
        
        if goal_type.lower() in ['vacation', 'travel']:
            # Consider travel seasonality
            seasonal_factors = {
                'peak_season_premium': "Travel during peak season can cost 20-40% more",
                'booking_lead_time': "Booking flights 2-3 months in advance can save 15-25%",
                'off_peak_discounts': "Travel during off-peak season can offer 30-50% discounts"
            }
        
        elif goal_type.lower() in ['vehicle', 'car', 'two_wheeler']:
            # Consider vehicle purchase timing
            seasonal_factors = {
                'model_year_end': "Purchasing at model year end (Dec-Mar) can save 5-10%",
                'festival_season': "Festival season discounts can offer 3-7% savings",
                'inventory_clearing': "Year-end inventory clearing sales can offer better deals",
                'new_model_launch': "Waiting for new model launch may affect resale value positively"
            }
        
        # Calculate monthly contributions for different horizons
        min_monthly = remaining_amount / (minimum_horizon * 12) if minimum_horizon > 0 else remaining_amount
        ideal_monthly = remaining_amount / (ideal_horizon * 12) if ideal_horizon > 0 else remaining_amount
        comfortable_monthly = remaining_amount / (comfortable_horizon * 12) if comfortable_horizon > 0 else remaining_amount
        
        # Determine optimized time horizon
        if current_time_horizon < minimum_horizon:
            optimized_horizon = minimum_horizon
            optimization_rationale = f"Current timeline of {current_time_horizon} years is too aggressive, requiring {current_percent:.1f}% of monthly surplus"
        elif current_time_horizon > comfortable_horizon * 1.5:
            optimized_horizon = comfortable_horizon
            optimization_rationale = f"Current timeline of {current_time_horizon} years is unnecessarily long, delaying goal achievement"
        else:
            # Current horizon is reasonable
            optimized_horizon = current_time_horizon
            optimization_rationale = f"Current timeline of {current_time_horizon} years is reasonable for this goal"
        
        # Calculate impact on other goals based on optimized timeline
        optimized_monthly = remaining_amount / (optimized_horizon * 12) if optimized_horizon > 0 else remaining_amount
        optimized_percent = optimized_monthly / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
        
        # Determine opportunity cost of using different time horizons
        # Assuming money not used for this goal could earn 7% annually in investments
        investment_rate = 0.07
        
        # Opportunity cost of faster horizon (using more funds now vs. investing)
        min_horizon_opportunity_cost = 0
        for month in range(1, minimum_horizon * 12 + 1):
            min_horizon_opportunity_cost += min_monthly * ((1 + investment_rate/12) ** (minimum_horizon * 12 - month))
        
        # Opportunity cost of ideal horizon
        ideal_horizon_opportunity_cost = 0
        for month in range(1, ideal_horizon * 12 + 1):
            ideal_horizon_opportunity_cost += ideal_monthly * ((1 + investment_rate/12) ** (ideal_horizon * 12 - month))
        
        # Opportunity cost difference
        opportunity_cost_diff = min_horizon_opportunity_cost - ideal_horizon_opportunity_cost
        
        return {
            'current_time_horizon': current_time_horizon,
            'optimized_time_horizon': optimized_horizon,
            'optimization_rationale': optimization_rationale,
            'time_horizon_options': {
                'minimum_feasible': {
                    'years': minimum_horizon,
                    'monthly_contribution': round(min_monthly),
                    'percent_of_surplus': round(min_monthly / monthly_surplus * 100, 1) if monthly_surplus > 0 else 'N/A',
                    'financial_impact': 'Maximum reasonable financial commitment'
                },
                'ideal_balance': {
                    'years': ideal_horizon,
                    'monthly_contribution': round(ideal_monthly),
                    'percent_of_surplus': round(ideal_monthly / monthly_surplus * 100, 1) if monthly_surplus > 0 else 'N/A',
                    'financial_impact': 'Optimal balance between timeline and financial flexibility'
                },
                'comfortable_pace': {
                    'years': comfortable_horizon,
                    'monthly_contribution': round(comfortable_monthly),
                    'percent_of_surplus': round(comfortable_monthly / monthly_surplus * 100, 1) if monthly_surplus > 0 else 'N/A',
                    'financial_impact': 'Minimal impact on other financial goals and priorities'
                }
            },
            'opportunity_cost_analysis': {
                'faster_vs_ideal_timeline': round(opportunity_cost_diff),
                'assumption': f"7% annual return on investments over the goal period"
            },
            'seasonal_timing_factors': seasonal_factors,
            'recommendation': f"Optimize goal timeline to {optimized_horizon} years with ₹{round(optimized_monthly)} monthly contribution ({optimized_percent:.1f}% of surplus)"
        }
    
    def optimize_goal_priority(self, goal_data, other_goals=None):
        """
        Optimize the priority level of the discretionary goal based on its
        importance relative to other financial goals.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            other_goals: List of other financial goals (optional)
            
        Returns:
            Dictionary with optimized priority recommendations
        """
        # Extract necessary information
        goal_type = goal_data.get('goal_type', 'general_savings')
        current_priority = goal_data.get('priority_level', 'medium')
        target_amount = goal_data.get('target_amount', 0)
        time_horizon = goal_data.get('time_horizon', 1)
        annual_income = goal_data.get('monthly_income', 100000) * 12
        
        # Calculate goal amount as percentage of annual income
        income_ratio = target_amount / annual_income if annual_income > 0 else float('inf')
        
        # Define appropriate priority levels based on goal type and amount
        appropriate_priority = 'medium'  # Default
        
        # For vacations and travel, priority depends on income ratio
        if goal_type.lower() in ['vacation', 'travel']:
            if income_ratio <= 0.05:  # Less than 5% of annual income
                appropriate_priority = 'low'
            elif income_ratio <= 0.15:  # 5-15% of annual income
                appropriate_priority = 'medium'
            else:  # More than 15% of annual income
                appropriate_priority = 'low'  # Higher amounts should generally be lower priority
                
        # For vehicles, priority depends on necessity and income ratio
        elif goal_type.lower() in ['vehicle', 'car', 'two_wheeler']:
            # Vehicle necessity info (if available)
            vehicle_necessity = goal_data.get('vehicle_necessity', 'convenience')  # possible values: necessity, convenience, luxury
            
            if vehicle_necessity == 'necessity':
                if income_ratio <= 0.3:  # Up to 30% of annual income
                    appropriate_priority = 'high'
                elif income_ratio <= 0.5:  # 30-50% of annual income
                    appropriate_priority = 'medium'
                else:  # More than 50% of annual income
                    appropriate_priority = 'low'  # Too expensive relative to income
            elif vehicle_necessity == 'convenience':
                if income_ratio <= 0.2:  # Up to 20% of annual income
                    appropriate_priority = 'medium'
                else:  # More than 20% of annual income
                    appropriate_priority = 'low'
            else:  # luxury
                appropriate_priority = 'low'
                
        # For electronics and other discretionary purchases
        elif goal_type.lower() in ['electronics', 'hobby', 'home_improvement']:
            if income_ratio <= 0.03:  # Less than 3% of annual income
                appropriate_priority = 'low'
            elif income_ratio <= 0.1:  # 3-10% of annual income
                appropriate_priority = 'medium'
            else:  # More than 10% of annual income
                appropriate_priority = 'low'  # Higher amounts should generally be lower priority
        
        # For general savings, priority is typically low to medium
        else:
            if income_ratio <= 0.1:  # Less than 10% of annual income
                appropriate_priority = 'low'
            else:  # More than 10% of annual income
                appropriate_priority = 'medium'
        
        # Assess impact of essential goals
        essential_goals_status = {}
        priority_adjustment_factors = []
        
        if other_goals:
            # Check emergency fund status
            emergency_goals = [g for g in other_goals if g.get('goal_type') == 'emergency_fund']
            if emergency_goals:
                emergency_status = 'funded' if any(g.get('progress_percent', 0) >= 90 for g in emergency_goals) else 'in_progress' if any(g.get('progress_percent', 0) >= 30 for g in emergency_goals) else 'unfunded'
                essential_goals_status['emergency_fund'] = emergency_status
                
                if emergency_status == 'unfunded':
                    priority_adjustment_factors.append({
                        'factor': 'Emergency Fund Unfunded',
                        'impact': 'Downgrade Priority',
                        'rationale': 'Emergency fund should be fully funded before discretionary goals'
                    })
            
            # Check debt repayment status
            debt_goals = [g for g in other_goals if g.get('goal_type') == 'debt_repayment']
            if debt_goals:
                high_interest_debt = any(g.get('interest_rate', 0) > 10 for g in debt_goals)
                debt_status = 'high_interest' if high_interest_debt else 'low_interest' if debt_goals else 'none'
                essential_goals_status['debt_repayment'] = debt_status
                
                if debt_status == 'high_interest':
                    priority_adjustment_factors.append({
                        'factor': 'High Interest Debt',
                        'impact': 'Downgrade Priority',
                        'rationale': 'High-interest debt should be paid off before funding discretionary goals'
                    })
            
            # Check retirement funding status
            retirement_goals = [g for g in other_goals if g.get('goal_type') == 'retirement']
            if retirement_goals:
                retirement_status = 'on_track' if any(g.get('progress_percent', 0) >= g.get('target_progress_percent', 30) for g in retirement_goals) else 'behind'
                essential_goals_status['retirement'] = retirement_status
                
                if retirement_status == 'behind':
                    priority_adjustment_factors.append({
                        'factor': 'Retirement Savings Behind',
                        'impact': 'Downgrade Priority',
                        'rationale': 'Retirement savings should be on track before prioritizing discretionary goals'
                    })
        
        # Determine final optimized priority
        optimized_priority = appropriate_priority
        
        # Adjust based on essential goals status
        if priority_adjustment_factors:
            # If any factors suggest downgrading priority, downgrade by one level
            if any(f['impact'] == 'Downgrade Priority' for f in priority_adjustment_factors):
                if optimized_priority == 'high':
                    optimized_priority = 'medium'
                elif optimized_priority == 'medium':
                    optimized_priority = 'low'
        
        # Compare with current priority
        if optimized_priority == current_priority:
            priority_recommendation = f"Current priority level '{current_priority}' is appropriate for this goal"
        else:
            priority_recommendation = f"Consider changing priority level from '{current_priority}' to '{optimized_priority}' for better alignment with financial goals"
        
        # Calculate resource allocation based on priority
        if optimized_priority == 'high':
            recommended_surplus_allocation = 0.3  # 30% of surplus
        elif optimized_priority == 'medium':
            recommended_surplus_allocation = 0.2  # 20% of surplus
        else:  # low
            recommended_surplus_allocation = 0.1  # 10% of surplus
        
        # Calculate monthly allocation
        monthly_surplus = goal_data.get('monthly_surplus', goal_data.get('monthly_income', 100000) - goal_data.get('monthly_expenses', 70000))
        recommended_monthly = monthly_surplus * recommended_surplus_allocation
        
        # Calculate adjusted time horizon based on recommended monthly contribution
        remaining_amount = max(0, target_amount - goal_data.get('current_savings', 0))
        adjusted_time_horizon = math.ceil(remaining_amount / (recommended_monthly * 12)) if recommended_monthly > 0 else float('inf')
        
        return {
            'goal_type': goal_type,
            'current_priority': current_priority,
            'optimized_priority': optimized_priority,
            'goal_amount_to_income_ratio': f"{income_ratio*100:.1f}%",
            'essential_goals_status': essential_goals_status,
            'priority_adjustment_factors': priority_adjustment_factors,
            'priority_recommendation': priority_recommendation,
            'resource_allocation': {
                'recommended_surplus_percentage': f"{recommended_surplus_allocation*100:.1f}%",
                'recommended_monthly_contribution': round(recommended_monthly),
                'adjusted_time_horizon': adjusted_time_horizon if adjusted_time_horizon != float('inf') else "Indefinite"
            },
            'implementation_steps': [
                f"Allocate {recommended_surplus_allocation*100:.1f}% of monthly surplus (₹{round(recommended_monthly)}) to this goal",
                f"Expect to achieve this goal in approximately {adjusted_time_horizon} years at the recommended contribution rate" if adjusted_time_horizon != float('inf') else "Current contribution rate is insufficient to achieve this goal",
                "Review and adjust priority quarterly as financial situation evolves"
            ]
        }
    
    def coordinate_multiple_goals(self, goal_data, other_goals=None):
        """
        Coordinate multiple discretionary goals to optimize overall satisfaction
        and financial impact.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            other_goals: List of other financial goals (optional)
            
        Returns:
            Dictionary with coordination recommendations
        """
        # Extract necessary information
        goal_type = goal_data.get('goal_type', 'general_savings')
        goal_id = goal_data.get('id', 'current_goal')
        target_amount = goal_data.get('target_amount', 0)
        time_horizon = goal_data.get('time_horizon', 1)
        priority_level = goal_data.get('priority_level', 'medium')
        
        # Filter to only include discretionary goals
        discretionary_goal_types = ['vacation', 'travel', 'vehicle', 'car', 'two_wheeler', 
                                  'electronics', 'hobby', 'home_improvement', 'general_savings']
        
        # If no other goals provided, create empty list
        if not other_goals:
            other_goals = []
        
        # Filter other discretionary goals (excluding current goal)
        discretionary_goals = [g for g in other_goals 
                              if (g.get('goal_type', '').lower() in discretionary_goal_types) 
                              and g.get('id') != goal_id]
        
        # Sort by priority and timeline
        def goal_sort_key(g):
            # Convert priority to numeric value
            priority_value = {'high': 3, 'medium': 2, 'low': 1}.get(g.get('priority_level', 'low').lower(), 1)
            # Use negative priority value so higher priorities come first
            return (-priority_value, g.get('time_horizon', float('inf')))
        
        sorted_discretionary_goals = sorted(discretionary_goals, key=goal_sort_key)
        
        # Add current goal to the list for comprehensive analysis
        analysis_goals = sorted_discretionary_goals.copy()
        current_goal = {
            'id': goal_id,
            'goal_type': goal_type,
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'priority_level': priority_level,
            'is_current_goal': True
        }
        analysis_goals.append(current_goal)
        
        # Calculate total discretionary funding required
        monthly_surplus = goal_data.get('monthly_surplus', goal_data.get('monthly_income', 100000) - goal_data.get('monthly_expenses', 70000))
        
        total_monthly_required = 0
        for g in analysis_goals:
            remaining = max(0, g.get('target_amount', 0) - g.get('current_savings', 0))
            g['monthly_required'] = remaining / (g.get('time_horizon', 1) * 12) if g.get('time_horizon', 0) > 0 else remaining
            total_monthly_required += g['monthly_required']
        
        # Calculate percentage of surplus required
        total_percent_of_surplus = total_monthly_required / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
        
        # Determine if reallocation is needed
        reallocation_needed = total_percent_of_surplus > 50  # If more than 50% of surplus is required
        
        # Generate goal coordination strategies
        coordination_strategies = []
        
        if reallocation_needed:
            # Staggered timeline strategy
            coordination_strategies.append({
                'strategy': 'Staggered Timeline',
                'description': 'Focus on highest priority goals first, then move to lower priority goals',
                'implementation': [
                    "Fully fund high priority goals before allocating to medium/low priority goals",
                    "Delay start of lower priority goals until higher priority goals are 50%+ funded",
                    "Use milestone-based activation for lower priority goals"
                ]
            })
            
            # Proportional funding strategy
            coordination_strategies.append({
                'strategy': 'Proportional Funding',
                'description': 'Allocate funds to all goals based on priority weighting',
                'implementation': [
                    "Allocate 50% of discretionary funding to high priority goals",
                    "Allocate 30% of discretionary funding to medium priority goals",
                    "Allocate 20% of discretionary funding to low priority goals",
                    "Adjust timelines to accommodate reduced monthly contributions"
                ]
            })
            
            # Goal consolidation strategy
            coordination_strategies.append({
                'strategy': 'Goal Consolidation',
                'description': 'Combine similar goals or reduce total number of concurrent goals',
                'implementation': [
                    "Limit active discretionary goals to maximum of 3",
                    "Combine multiple small goals into themed saving categories",
                    "Create sequential goal achievement plan instead of parallel funding"
                ]
            })
        else:
            # Balanced funding strategy
            coordination_strategies.append({
                'strategy': 'Balanced Funding',
                'description': 'Fund all goals simultaneously with priority-based allocation',
                'implementation': [
                    "Maintain current funding approach for all goals",
                    "Review monthly to ensure consistency with overall financial plan",
                    "Use windfalls to accelerate highest priority goals first"
                ]
            })
        
        # Generate specific coordination recommendations for current goal
        specific_recommendations = []
        
        # Goal timing coordination
        if discretionary_goals:
            # Check if goals with similar timelines exist
            similar_timeline_goals = [g for g in discretionary_goals 
                                    if abs(g.get('time_horizon', 0) - time_horizon) <= 0.5]
            
            if similar_timeline_goals and reallocation_needed:
                specific_recommendations.append(f"Consider staggering this goal's timeline to avoid competing with {len(similar_timeline_goals)} other goal(s) with similar completion dates")
        
        # Priority balancing
        high_priority_count = len([g for g in analysis_goals 
                                 if g.get('priority_level', '').lower() == 'high'])
        
        if high_priority_count > 2 and priority_level.lower() == 'high':
            specific_recommendations.append("Reconsider 'high' priority designation - having too many high priority goals dilutes focus")
        
        # Funding approach
        current_goal_percent = current_goal['monthly_required'] / monthly_surplus * 100 if monthly_surplus > 0 else float('inf')
        
        if current_goal_percent > 25:
            specific_recommendations.append(f"This goal alone requires {current_goal_percent:.1f}% of monthly surplus, consider extending timeline or reducing target amount")
        
        # Recommended monthly allocation for current goal
        if reallocation_needed:
            # Reduced allocation based on priority
            if priority_level.lower() == 'high':
                allocation_percent = 0.25  # 25% of surplus
            elif priority_level.lower() == 'medium':
                allocation_percent = 0.15  # 15% of surplus
            else:  # low
                allocation_percent = 0.1   # 10% of surplus
        else:
            # Standard allocation based on priority
            if priority_level.lower() == 'high':
                allocation_percent = 0.3   # 30% of surplus
            elif priority_level.lower() == 'medium':
                allocation_percent = 0.2   # 20% of surplus
            else:  # low
                allocation_percent = 0.1   # 10% of surplus
        
        recommended_monthly = monthly_surplus * allocation_percent
        
        # Adjusted timeline based on recommended monthly allocation
        remaining_amount = max(0, target_amount - goal_data.get('current_savings', 0))
        adjusted_time_horizon = math.ceil(remaining_amount / (recommended_monthly * 12)) if recommended_monthly > 0 else float('inf')
        
        return {
            'total_discretionary_goals': len(analysis_goals),
            'total_monthly_funding_required': round(total_monthly_required),
            'percent_of_surplus_required': round(total_percent_of_surplus, 1),
            'funding_status': 'Overallocated' if reallocation_needed else 'Manageable',
            'coordination_strategies': coordination_strategies,
            'current_goal_allocation': {
                'recommended_monthly': round(recommended_monthly),
                'percent_of_surplus': round(allocation_percent * 100, 1),
                'adjusted_time_horizon': adjusted_time_horizon if adjusted_time_horizon != float('inf') else "Indefinite"
            },
            'specific_recommendations': specific_recommendations,
            'implementation_plan': [
                f"Allocate ₹{round(recommended_monthly)} monthly to this goal ({allocation_percent*100:.1f}% of surplus)",
                f"Expect to achieve this goal in approximately {adjusted_time_horizon} years at the recommended contribution rate" if adjusted_time_horizon != float('inf') else "Current contribution rate is insufficient to achieve this goal",
                "Revisit all discretionary goals quarterly to ensure continued alignment with priorities"
            ]
        }
    
    def _calculate_monthly_funding_need(self, goal):
        """
        Helper method to calculate monthly funding need for a goal.
        
        Returns:
            float: Monthly funding required
        """
        target_amount = goal.get('target_amount', 0)
        current_amount = goal.get('current_amount', 0)
        time_horizon = goal.get('time_horizon', 1)
        
        # Calculate remaining amount
        remaining = max(0, target_amount - current_amount)
        
        # Calculate monthly required
        monthly_required = remaining / (time_horizon * 12) if time_horizon > 0 else remaining
        
        return monthly_required
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive discretionary goal funding strategy with optimization.
        
        Args:
            goal_data: Dictionary with discretionary goal details
            
        Returns:
            Dictionary with comprehensive discretionary goal strategy
        """
        # Extract discretionary goal specific information
        goal_type = goal_data.get('goal_type', 'general savings')
        sub_type = goal_data.get('sub_type')  # For specific categorization
        target_amount = goal_data.get('target_amount')
        time_horizon = goal_data.get('time_horizon', 1)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        priority_level = goal_data.get('priority_level', 'medium')
        
        # Financial capacity for optimization
        financial_capacity = {
            'monthly_income': goal_data.get('monthly_income', 100000),
            'monthly_expenses': goal_data.get('monthly_expenses', 70000),
            'existing_savings': current_savings,
            'monthly_surplus': goal_data.get('monthly_surplus', 30000),
            'monthly_savings_capacity': goal_data.get('monthly_savings_capacity', 21000)
        }
        
        # Calculate target amount if not provided
        if not target_amount:
            if goal_type.lower() in ('vacation', 'travel'):
                # Get vacation details
                destination_type = goal_data.get('destination_type', 'domestic')
                destination = goal_data.get('destination')
                travel_class = goal_data.get('travel_class', 'mid_range')
                
                target_amount = self.estimate_vacation_cost(
                    destination_type, destination, travel_class
                )
                
            elif goal_type.lower() in ('vehicle', 'car', 'two_wheeler'):
                # Get vehicle details
                vehicle_type = goal_data.get('vehicle_type', 'car')
                vehicle_class = goal_data.get('vehicle_class')
                vehicle_segment = goal_data.get('vehicle_segment', 'mid_range')
                
                target_amount = self.estimate_vehicle_cost(
                    vehicle_type, vehicle_class, vehicle_segment
                )
                
            else:  # General savings
                # Default target for general savings
                target_amount = 100000  # 1 lakh for general savings goal
        
        # Create discretionary goal specific data
        discretionary_goal = {
            'goal_type': goal_type,
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution,
            'priority_level': priority_level
        }
        
        # Initialize constraint and optimization systems (lazy loading)
        self._initialize_constraints()
        self._initialize_optimizer()
        self._initialize_compound_strategy()
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(discretionary_goal)
        
        # Enhanced with discretionary goal specific analyses
        
        # Create savings automation plan
        automation_plan = self.create_savings_automation_plan(
            base_strategy['recommendation']['total_monthly_investment'],
            goal_type,
            time_horizon
        )
        
        # Optimize goal amount
        optimized_amount = self.optimize_goal_amount(
            goal_type,
            target_amount,
            financial_capacity,
            time_horizon,
            priority_level
        )
        
        # Get other goals if provided for optimization
        other_goals = goal_data.get('other_goals', [])
        
        # Run constraint assessments
        affordability_assessment = self.assess_goal_affordability(discretionary_goal, other_goals)
        priority_assessment = self.validate_priority_balance(discretionary_goal, other_goals)
        timing_assessment = self.assess_goal_timing(discretionary_goal)
        
        # Run optimization analyses
        optimized_timing = self.optimize_goal_timing(discretionary_goal)
        optimized_priority = self.optimize_goal_priority(discretionary_goal, other_goals)
        goal_coordination = self.coordinate_multiple_goals(discretionary_goal, other_goals)
        
        # Analyze goal tradeoffs
        tradeoff_analysis = self.analyze_goal_tradeoffs(
            discretionary_goal, other_goals
        )
        
        # Additional goal-specific analysis
        goal_specific_analysis = {}
        
        if goal_type.lower() in ('vehicle', 'car', 'two_wheeler'):
            # Get vehicle details
            vehicle_type = goal_data.get('vehicle_type', 'car')
            is_used = goal_data.get('is_used', False)
            is_electric = goal_data.get('is_electric', False)
            
            # Calculate loan options
            loan_analysis = self.calculate_vehicle_loan(
                target_amount,
                vehicle_type,
                0.3,  # 30% down payment
                is_used,
                is_electric
            )
            
            goal_specific_analysis['vehicle_loan_options'] = loan_analysis
            goal_specific_analysis['vehicle_type'] = vehicle_type
            goal_specific_analysis['ownership_considerations'] = [
                "Insurance costs: 3-5% of vehicle value annually",
                "Maintenance costs: 1-2% of vehicle value annually",
                "Fuel/charging costs based on usage pattern",
                "Resale value considerations",
                "Tax and registration fees"
            ]
            
        elif goal_type.lower() in ('vacation', 'travel'):
            # Get vacation details
            destination_type = goal_data.get('destination_type', 'domestic')
            destination = goal_data.get('destination')
            
            goal_specific_analysis['vacation_details'] = {
                'destination_type': destination_type,
                'destination': destination,
                'cost_breakdown': {
                    'travel': f"{round(target_amount * 0.4)} (40%)",
                    'accommodation': f"{round(target_amount * 0.3)} (30%)",
                    'food_and_activities': f"{round(target_amount * 0.2)} (20%)",
                    'miscellaneous': f"{round(target_amount * 0.1)} (10%)"
                },
                'saving_tips': [
                    "Book flights/trains 2-3 months in advance",
                    "Consider off-peak season for better rates",
                    "Look for package deals and discounts",
                    "Use travel credit cards for points/rewards",
                    "Set daily budget for expenses during the trip"
                ]
            }
            
        else:  # General savings
            # Suggested allocation for general savings
            goal_specific_analysis['general_savings_allocation'] = {
                'short_term_fun': round(target_amount * self.discretionary_params['general_savings_buckets']['short_term_fun']['typical_allocation']),
                'lifestyle_upgrade': round(target_amount * self.discretionary_params['general_savings_buckets']['lifestyle_upgrade']['typical_allocation']),
                'opportunity_fund': round(target_amount * self.discretionary_params['general_savings_buckets']['opportunity_fund']['typical_allocation'])
            }
            
            goal_specific_analysis['spending_guidelines'] = [
                "Follow 24-hour rule for discretionary purchases over ₹5,000",
                "Consider cost per use for lifestyle purchases",
                "Prioritize experiences over material possessions",
                "Allocate 'fun money' monthly with guilt-free spending",
                "Track discretionary expenses separately from necessities"
            ]
        
        # Combine into comprehensive strategy with optimizations
        strategy = {
            **base_strategy,
            'goal_details': {
                'goal_type': goal_type,
                'sub_type': sub_type,
                'target_amount': target_amount,
                'time_horizon': time_horizon,
                'priority_level': priority_level
            },
            'automation_plan': automation_plan,
            'goal_amount_optimization': optimized_amount,
            'constraint_assessments': {
                'affordability': affordability_assessment,
                'priority_balance': priority_assessment,
                'timing': timing_assessment
            },
            'optimization_results': {
                'timing_optimization': optimized_timing,
                'priority_optimization': optimized_priority,
                'multiple_goal_coordination': goal_coordination
            },
            'goal_tradeoff_analysis': tradeoff_analysis
        }
        
        # Add goal-specific analysis
        if goal_specific_analysis:
            strategy['goal_specific_analysis'] = goal_specific_analysis
        
        # Create optimized action plan from all analyses
        optimized_action_plan = {
            'immediate_actions': [
                f"Set target amount to ₹{round(optimized_amount['recommended_amount'])} ({optimized_amount['stretch_factor']})",
                f"Adjust timeline to {optimized_timing['optimized_time_horizon']} years for optimal funding pace",
                f"Set priority level to {optimized_priority['optimized_priority']} for appropriate resource allocation"
            ],
            'funding_approach': [
                f"Allocate ₹{goal_coordination['current_goal_allocation']['recommended_monthly']} monthly ({goal_coordination['current_goal_allocation']['percent_of_surplus']}% of surplus)",
                f"Set up {automation_plan['automation_frequency']} automated transfers using {automation_plan['primary_method']}",
                "Use allocation strategy appropriate for time horizon and risk profile"
            ],
            'optimization_benefits': [
                f"Improved affordability: {affordability_assessment['affordability_status']} with {affordability_assessment['percent_of_monthly_surplus']}% of surplus",
                f"Balanced priorities: Appropriate allocation relative to essential financial goals",
                f"Coordinated timing: Optimized timeline avoids competition with other discretionary goals"
            ]
        }
        
        strategy['optimized_action_plan'] = optimized_action_plan
        
        # Add discretionary goal specific advice
        strategy['specific_advice'] = {
            'balancing_priorities': [
                "Ensure emergency fund and retirement savings are on track first",
                "Consider this goal's importance relative to other financial priorities",
                "Avoid high-interest debt for discretionary spending"
            ],
            'spending_mindfulness': [
                "Evaluate wants vs. needs before commitment",
                "Research thoroughly to ensure satisfaction with purchase",
                "Consider alternatives like rentals or sharing for infrequent use items"
            ],
            'value_maximization': [
                "Focus on experiences that provide lasting satisfaction",
                "Consider total cost of ownership for purchases",
                "Look for off-peak or discount opportunities without compromising quality"
            ]
        }
        
        return strategy