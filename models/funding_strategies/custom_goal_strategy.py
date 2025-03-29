import logging
import math
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class CustomGoalStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for custom user-defined goals that don't fit
    into standard categories, with flexible and adaptable approaches based on
    goal characteristics.
    """
    
    def __init__(self):
        """Initialize with custom goal specific parameters"""
        super().__init__()
        
        # Optimizer, constraints, and compound strategy objects will be lazy initialized
        self.optimizer = None
        self.constraints = None
        self.compound_strategy = None
        
        # Additional custom goal specific parameters
        self.custom_params = {
            "goal_classification_rubric": {
                "time_sensitivity": {
                    "critical": {
                        "description": "Goal has fixed, immovable deadline",
                        "funding_approach": "Maximize certainty and liquidity",
                        "weight": 3.0
                    },
                    "important": {
                        "description": "Goal has preferred timeline with limited flexibility",
                        "funding_approach": "Balance growth and certainty",
                        "weight": 2.0
                    },
                    "flexible": {
                        "description": "Goal timeline can be adjusted based on funding",
                        "funding_approach": "Prioritize growth over timing certainty",
                        "weight": 1.0
                    }
                },
                "wealth_building": {
                    "strong": {
                        "description": "Goal directly increases future financial capability",
                        "funding_approach": "Consider leverage and growth-oriented investments",
                        "weight": 3.0
                    },
                    "moderate": {
                        "description": "Goal has some positive financial implications",
                        "funding_approach": "Balance between growth and consumption",
                        "weight": 2.0
                    },
                    "minimal": {
                        "description": "Goal primarily represents consumption",
                        "funding_approach": "Fund from discretionary cash flow",
                        "weight": 1.0
                    }
                },
                "goal_magnitude": {
                    "major": {
                        "description": "Goal represents >20% of annual income",
                        "funding_approach": "Structured, long-term funding plan",
                        "weight": 3.0
                    },
                    "moderate": {
                        "description": "Goal represents 5-20% of annual income",
                        "funding_approach": "Dedicated savings approach",
                        "weight": 2.0
                    },
                    "minor": {
                        "description": "Goal represents <5% of annual income",
                        "funding_approach": "Cash flow management approach",
                        "weight": 1.0
                    }
                }
            },
            "allocation_templates": {
                "certainty_focused": {
                    "cash": 0.40,
                    "short_term_debt": 0.40,
                    "balanced_funds": 0.20,
                    "expected_return": 0.055  # 5.5% expected return
                },
                "balanced": {
                    "cash": 0.20,
                    "short_term_debt": 0.30,
                    "balanced_funds": 0.30,
                    "equity": 0.20,
                    "expected_return": 0.075  # 7.5% expected return
                },
                "growth_focused": {
                    "cash": 0.10,
                    "short_term_debt": 0.20,
                    "balanced_funds": 0.30,
                    "equity": 0.40,
                    "expected_return": 0.09  # 9% expected return
                }
            },
            "funding_approaches": {
                "systematic": {
                    "description": "Regular, structured contributions",
                    "best_for": ["Long-term goals", "Predictable income", "Disciplined savers"],
                    "method": "Monthly SIP / recurring deposit"
                },
                "milestone": {
                    "description": "Fund in discrete chunks at milestones",
                    "best_for": ["Variable income", "Bonus-dependent earners", "Multiple competing goals"],
                    "method": "Allocate percentage of bonuses, tax refunds, or windfalls"
                },
                "hybrid": {
                    "description": "Combination of regular contributions and milestone funding",
                    "best_for": ["Most custom goals", "Balance of consistency and flexibility"],
                    "method": "Base monthly contribution plus supplemental milestone funding"
                }
            },
            "reassessment_guidelines": {
                "timing": {
                    "regular": "Every 6 months",
                    "milestones": ["25% funded", "50% funded", "75% funded"],
                    "triggers": ["Major income change", "Goal parameter change", "Time horizon change"]
                },
                "evaluation_metrics": [
                    "Funding progress vs. target",
                    "Current market conditions",
                    "Change in goal priority",
                    "Change in financial capacity"
                ]
            },
            "indian_specific_patterns": {
                "common_goals": {
                    "vacation_to_pilgrimage": {
                        "description": "Cultural and religious travel to sacred sites",
                        "approach": "Structured savings with cultural considerations"
                    },
                    "family_events": {
                        "description": "Major family ceremonies and gatherings",
                        "approach": "Long-term planning with family participation"
                    },
                    "home_upgrades": {
                        "description": "Renovation or vastu-based home improvements",
                        "approach": "Blend of loan and savings-based funding"
                    },
                    "entrepreneurship": {
                        "description": "Starting family business or side venture",
                        "approach": "Balanced risk approach with family capital"
                    }
                },
                "tax_considerations": {
                    "elss_investments": "Equity-linked savings scheme for tax benefits",
                    "ppf_integration": "Public Provident Fund for tax-efficient goal funding",
                    "specified_asset_deductions": "Section 80C deductible investments for dual-purpose goals"
                }
            }
        }
        
        # Custom goal optimization parameters
        self.custom_optimization_params = {
            'classification_weight': 0.30,    # Weight for goal classification optimization
            'flexibility_weight': 0.25,       # Weight for funding flexibility optimization
            'integration_weight': 0.25,       # Weight for financial integration optimization
            'sustainability_weight': 0.20,    # Weight for long-term sustainability
            'minimum_goal_funding': 0.25,     # Minimum funding percentage for viable plan
            'classification_threshold': 0.60, # Threshold for classification confidence
            'flexibility_bands': 5,           # Number of flexibility bands for custom goal funding
            'tax_efficiency_factor': 0.15     # Weight for tax efficiency in custom goal optimization
        }
        
        # Load custom goal specific parameters
        self._load_custom_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with custom goal specific optimization parameters
            super()._initialize_optimizer()
            
            # Set custom goal specific optimization parameters
            if hasattr(self.optimizer, 'set_parameters'):
                self.optimizer.set_parameters({
                    'classification_weight': self.custom_optimization_params['classification_weight'],
                    'flexibility_weight': self.custom_optimization_params['flexibility_weight'],
                    'integration_weight': self.custom_optimization_params['integration_weight'],
                    'sustainability_weight': self.custom_optimization_params['sustainability_weight']
                })
    
    def _initialize_constraints(self):
        """Initialize the funding constraints with lazy loading pattern"""
        if not hasattr(self, 'constraints') or self.constraints is None:
            # Initialize base constraints
            super()._initialize_constraints()
            
            # Set custom goal specific constraint parameters
            if hasattr(self.constraints, 'register_constraint'):
                # Register minimum goal funding constraint
                self.constraints.register_constraint(
                    'minimum_goal_funding', 
                    self.custom_optimization_params['minimum_goal_funding']
                )
                
                # Register classification threshold constraint
                self.constraints.register_constraint(
                    'classification_threshold',
                    self.custom_optimization_params['classification_threshold']
                )
    
    def _initialize_compound_strategy(self):
        """Initialize the compound strategy with lazy loading pattern"""
        if not hasattr(self, 'compound_strategy') or self.compound_strategy is None:
            # Initialize base compound strategy
            super()._initialize_compound_strategy()
            
            # Register custom goal specific strategies
            if hasattr(self.compound_strategy, 'register_strategy'):
                # Register different strategies based on custom goal components
                self.compound_strategy.register_strategy(
                    'classification_optimization', 'custom_goal_classification'
                )
                
                self.compound_strategy.register_strategy(
                    'funding_flexibility', 'adaptive_funding_approach'
                )
                
                self.compound_strategy.register_strategy(
                    'integration_optimization', 'financial_integration'
                )
        
    def _load_custom_parameters(self):
        """Load custom goal specific parameters from service"""
        if self.param_service:
            try:
                # Load goal classification rubric
                classification_rubric = self.param_service.get_parameter('goal_classification_rubric')
                if classification_rubric:
                    self.custom_params['goal_classification_rubric'].update(classification_rubric)
                
                # Load allocation templates
                allocation_templates = self.param_service.get_parameter('custom_allocation_templates')
                if allocation_templates:
                    self.custom_params['allocation_templates'].update(allocation_templates)
                
                # Load funding approaches
                funding_approaches = self.param_service.get_parameter('custom_funding_approaches')
                if funding_approaches:
                    self.custom_params['funding_approaches'].update(funding_approaches)
                
                # Load reassessment guidelines
                reassessment_guidelines = self.param_service.get_parameter('custom_reassessment_guidelines')
                if reassessment_guidelines:
                    self.custom_params['reassessment_guidelines'].update(reassessment_guidelines)
                
            except Exception as e:
                logger.error(f"Error loading custom goal parameters: {e}")
                # Continue with default parameters
    
    def classify_custom_goal(self, goal_amount: float, time_horizon: float, annual_income: float,
                           goal_description: str = None, goal_tags: List[str] = None) -> Dict[str, Any]:
        """
        Classify a custom goal based on its characteristics to determine approach.
        
        Args:
            goal_amount: Target goal amount
            time_horizon: Years to goal
            annual_income: Annual income for reference
            goal_description: Description of the goal (for keyword analysis)
            goal_tags: List of tags or categories associated with the goal
            
        Returns:
            Dictionary with goal classification and recommended approach
        """
        # Initialize classification scores
        classification = {
            'time_sensitivity': '',
            'wealth_building': '',
            'goal_magnitude': ''
        }
        
        # Classify time sensitivity
        if time_horizon < 1:
            classification['time_sensitivity'] = 'critical'
        elif time_horizon < 3:
            classification['time_sensitivity'] = 'important'
        else:
            classification['time_sensitivity'] = 'flexible'
            
        # Classify goal magnitude relative to income
        goal_to_income_ratio = goal_amount / annual_income if annual_income > 0 else 0
        
        if goal_to_income_ratio > 0.2:
            classification['goal_magnitude'] = 'major'
        elif goal_to_income_ratio > 0.05:
            classification['goal_magnitude'] = 'moderate'
        else:
            classification['goal_magnitude'] = 'minor'
            
        # Classify wealth building aspect
        # Default to minimal unless we can determine otherwise
        classification['wealth_building'] = 'minimal'
        
        # Check tags if provided
        wealth_building_tags = ['investment', 'education', 'skill', 'business', 'career', 'asset']
        moderate_wealth_tags = ['health', 'work', 'networking', 'certification']
        
        if goal_tags:
            if any(tag.lower() in wealth_building_tags for tag in goal_tags):
                classification['wealth_building'] = 'strong'
            elif any(tag.lower() in moderate_wealth_tags for tag in goal_tags):
                classification['wealth_building'] = 'moderate'
                
        # Check description if provided
        if goal_description:
            description_lower = goal_description.lower()
            
            # Check for wealth building keywords
            wealth_keywords = ['invest', 'education', 'learn', 'skill', 'certification', 'business', 
                            'startup', 'career', 'professional', 'asset', 'property']
            moderate_keywords = ['health', 'improve', 'develop', 'grow', 'network', 'workshop']
            
            if any(keyword in description_lower for keyword in wealth_keywords):
                classification['wealth_building'] = 'strong'
            elif any(keyword in description_lower for keyword in moderate_keywords) and classification['wealth_building'] != 'strong':
                classification['wealth_building'] = 'moderate'
        
        # Calculate overall score for goal priority
        rubric = self.custom_params['goal_classification_rubric']
        
        time_weight = rubric['time_sensitivity'][classification['time_sensitivity']]['weight']
        wealth_weight = rubric['wealth_building'][classification['wealth_building']]['weight']
        magnitude_weight = rubric['goal_magnitude'][classification['goal_magnitude']]['weight']
        
        total_weight = time_weight + wealth_weight + magnitude_weight
        max_possible = 9.0  # 3 categories with max weight of 3.0 each
        priority_score = (total_weight / max_possible) * 100
        
        # Determine funding approach based on classification
        if classification['time_sensitivity'] == 'critical':
            allocation_template = 'certainty_focused'
        elif (classification['time_sensitivity'] == 'important' and 
             classification['wealth_building'] != 'strong'):
            allocation_template = 'balanced'
        else:
            allocation_template = 'growth_focused'
            
        # Determine funding method
        if classification['goal_magnitude'] == 'minor' or time_horizon < 1:
            funding_method = 'milestone'
        elif classification['time_sensitivity'] == 'critical' and time_horizon > 1:
            funding_method = 'systematic'
        else:
            funding_method = 'hybrid'
            
        return {
            'classification': classification,
            'priority_score': round(priority_score, 1),
            'recommended_approach': {
                'allocation_template': allocation_template,
                'funding_method': funding_method,
                'funding_details': self.custom_params['funding_approaches'][funding_method]
            },
            'classification_details': {
                'time_sensitivity': rubric['time_sensitivity'][classification['time_sensitivity']],
                'wealth_building': rubric['wealth_building'][classification['wealth_building']],
                'goal_magnitude': rubric['goal_magnitude'][classification['goal_magnitude']]
            }
        }
    
    def customize_allocation_model(self, base_template: str, time_horizon: float, 
                                risk_tolerance: str, goal_priority: float) -> Dict[str, float]:
        """
        Customize allocation model for a specific goal situation.
        
        Args:
            base_template: Base allocation template ('certainty_focused', 'balanced', 'growth_focused')
            time_horizon: Years to goal
            risk_tolerance: Risk tolerance level ('conservative', 'moderate', 'aggressive')
            goal_priority: Goal priority score (0-100)
            
        Returns:
            Dictionary with customized allocation percentages
        """
        # Get base template
        base_allocation = self.custom_params['allocation_templates'].get(
            base_template, self.custom_params['allocation_templates']['balanced']
        )
        
        # Create a working copy
        allocation = base_allocation.copy()
        
        # Adjust for time horizon
        if time_horizon < 1:
            # Short horizon - increase cash, decrease equity
            cash_increase = min(0.2, allocation.get('equity', 0) * 0.5)
            allocation['cash'] = allocation.get('cash', 0) + cash_increase
            allocation['equity'] = max(0, allocation.get('equity', 0) - cash_increase)
            
        elif time_horizon > 5:
            # Long horizon - increase equity if available
            if 'equity' in allocation:
                cash_decrease = min(allocation.get('cash', 0) * 0.5, 0.1)
                allocation['equity'] = allocation.get('equity', 0) + cash_decrease
                allocation['cash'] = max(0.05, allocation.get('cash', 0) - cash_decrease)
        
        # Adjust for risk tolerance
        risk_adjustments = {
            'conservative': -0.1,  # Decrease equity by 10%
            'moderate': 0,       # No change
            'aggressive': 0.1    # Increase equity by 10%
        }
        
        risk_adjustment = risk_adjustments.get(risk_tolerance, 0)
        if 'equity' in allocation and risk_adjustment != 0:
            # Apply risk adjustment to equity allocation
            current_equity = allocation.get('equity', 0)
            new_equity = max(0, min(0.8, current_equity + risk_adjustment))
            equity_change = new_equity - current_equity
            
            # If equity increased, decrease other allocations proportionally
            if equity_change > 0:
                total_other = sum(v for k, v in allocation.items() 
                               if k not in ['equity', 'expected_return'])
                
                if total_other > 0:
                    for k in list(allocation.keys()):
                        if k not in ['equity', 'expected_return']:
                            allocation[k] = max(0, allocation[k] - (equity_change * allocation[k] / total_other))
            
            # If equity decreased, increase other allocations proportionally
            elif equity_change < 0:
                total_other = sum(v for k, v in allocation.items() 
                               if k not in ['equity', 'expected_return'])
                
                if total_other > 0:
                    for k in list(allocation.keys()):
                        if k not in ['equity', 'expected_return']:
                            allocation[k] = allocation[k] - (equity_change * allocation[k] / total_other)
            
            # Set the new equity value
            allocation['equity'] = new_equity
        
        # Adjust based on goal priority
        # High priority goals get slightly more conservative treatment
        if goal_priority > 75 and 'equity' in allocation and 'cash' in allocation:
            priority_shift = min(allocation.get('equity', 0) * 0.2, 0.05)
            allocation['equity'] = allocation.get('equity', 0) - priority_shift
            allocation['cash'] = allocation.get('cash', 0) + priority_shift
            
        # Normalize to ensure allocations sum to 1
        total_allocation = sum(v for k, v in allocation.items() if k != 'expected_return')
        if abs(total_allocation - 1.0) > 0.001:  # If not very close to 1.0
            for k in list(allocation.keys()):
                if k != 'expected_return':
                    allocation[k] = allocation[k] / total_allocation
                    
        # Recalculate expected return
        expected_return = 0
        for asset, percent in allocation.items():
            if asset != 'expected_return':
                if asset == 'cash':
                    asset_return = 0.035  # 3.5%
                elif asset == 'short_term_debt':
                    asset_return = 0.06   # 6%
                elif asset == 'balanced_funds':
                    asset_return = 0.08   # 8%
                elif asset == 'equity':
                    asset_return = 0.12   # 12%
                else:
                    asset_return = 0.07   # Default 7%
                    
                expected_return += percent * asset_return
                
        allocation['expected_return'] = round(expected_return, 4)
        
        return allocation
    
    def design_custom_funding_plan(self, goal_amount: float, time_horizon: float, 
                                current_savings: float, monthly_capacity: float,
                                allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Design a customized funding plan based on goal parameters and allocation.
        
        Args:
            goal_amount: Target goal amount
            time_horizon: Years to goal
            current_savings: Current amount saved
            monthly_capacity: Monthly savings capacity
            allocation: Asset allocation dictionary
            
        Returns:
            Dictionary with customized funding plan
        """
        # Extract expected return from allocation
        expected_return = allocation.get('expected_return', 0.06)
        
        # Calculate future value of current savings
        future_value_current = current_savings * ((1 + expected_return) ** time_horizon)
        
        # Calculate funding gap
        funding_gap = goal_amount - future_value_current
        
        # Calculate required monthly contribution
        monthly_rate = expected_return / 12
        months = time_horizon * 12
        
        # Handle very short timelines
        if months <= 1:
            required_monthly = funding_gap
        else:
            # PMT formula: PMT = FV / ((1 + r)^n - 1) * (1 + r)
            denominator = ((1 + monthly_rate) ** months - 1) * (1 + monthly_rate)
            required_monthly = funding_gap / denominator if denominator > 0 else funding_gap / months
        
        # Check if monthly capacity is sufficient
        capacity_sufficient = monthly_capacity >= required_monthly
        
        # If capacity insufficient, calculate alternative scenarios
        alternative_scenarios = []
        
        if not capacity_sufficient:
            # Scenario 1: Extend timeframe
            # Find how long it would take with current capacity
            # FV = PMT * ((1+r)^n - 1) / r * (1+r)
            # Solving for n: n = log((FV*r)/(PMT) + 1) / log(1+r)
            if monthly_capacity > 0:
                try:
                    # Calculate how long it would take with available capacity
                    extended_months = math.log((funding_gap * monthly_rate / monthly_capacity) + 1) / math.log(1 + monthly_rate)
                    extended_years = extended_months / 12
                    
                    alternative_scenarios.append({
                        'scenario': 'Extended Timeframe',
                        'description': f"Reach goal with current capacity",
                        'monthly_contribution': round(monthly_capacity),
                        'extended_time_horizon': round(extended_years, 1),
                        'additional_time_required': round(extended_years - time_horizon, 1)
                    })
                except (ValueError, ZeroDivisionError):
                    # Handle calculation errors (e.g., negative or very large values)
                    pass
            
            # Scenario 2: Partial Goal
            # How much of the goal can be funded with current capacity
            achievable_future_value = monthly_capacity * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
            achievable_goal_percent = min(100, (future_value_current + achievable_future_value) / goal_amount * 100)
            
            alternative_scenarios.append({
                'scenario': 'Partial Goal',
                'description': f"Achieve portion of goal within original timeframe",
                'monthly_contribution': round(monthly_capacity),
                'achievable_percentage': round(achievable_goal_percent, 1),
                'achievable_amount': round(goal_amount * achievable_goal_percent / 100)
            })
            
            # Scenario 3: Supplemental Funding
            # How much lump sum would be needed to bridge the gap
            monthly_shortfall = required_monthly - monthly_capacity
            present_value_of_shortfall = monthly_shortfall * (((1 + monthly_rate) ** months - 1) / (monthly_rate * (1 + monthly_rate) ** months))
            
            alternative_scenarios.append({
                'scenario': 'Supplemental Funding',
                'description': f"Bridge gap with additional lump sum",
                'monthly_contribution': round(monthly_capacity),
                'lump_sum_needed': round(present_value_of_shortfall),
                'potential_sources': [
                    "Bonus or tax refund allocation",
                    "Sale of unused assets",
                    "Gift or family support",
                    "Side income project"
                ]
            })
        
        # Design the implementation plan
        monthly_contribution = min(required_monthly, monthly_capacity)
        
        implementation_plan = {
            'regular_contribution': {
                'amount': round(monthly_contribution),
                'frequency': 'Monthly',
                'allocation': {k: round(v * 100, 1) for k, v in allocation.items() if k != 'expected_return'}
            },
            'milestones': [
                {
                    'milestone': '25% Funded',
                    'projected_date': datetime.now().replace(year=datetime.now().year + int(time_horizon * 0.25)).strftime('%Y-%m'),
                    'review_actions': [
                        "Validate goal parameters",
                        "Check investment performance against expectations",
                        "Adjust contributions if needed"
                    ]
                },
                {
                    'milestone': '50% Funded',
                    'projected_date': datetime.now().replace(year=datetime.now().year + int(time_horizon * 0.5)).strftime('%Y-%m'),
                    'review_actions': [
                        "Comprehensive goal review",
                        "Adjust investment allocation if needed",
                        "Revisit goal priority"
                    ]
                },
                {
                    'milestone': '75% Funded',
                    'projected_date': datetime.now().replace(year=datetime.now().year + int(time_horizon * 0.75)).strftime('%Y-%m'),
                    'review_actions': [
                        "Begin transition to more conservative allocation",
                        "Finalize goal execution plans",
                        "Review goal completion logistics"
                    ]
                }
            ]
        }
        
        # Create funding plan
        funding_plan = {
            'goal_amount': round(goal_amount),
            'time_horizon': time_horizon,
            'current_savings': round(current_savings),
            'monthly_capacity': round(monthly_capacity),
            'projected_growth': {
                'future_value_of_current_savings': round(future_value_current),
                'funding_gap': round(funding_gap),
                'expected_annual_return': round(expected_return * 100, 2)
            },
            'funding_requirements': {
                'required_monthly_contribution': round(required_monthly),
                'capacity_sufficient': capacity_sufficient,
                'recommended_monthly_contribution': round(monthly_contribution)
            },
            'alternative_scenarios': alternative_scenarios if alternative_scenarios else None,
            'implementation_plan': implementation_plan,
            'tracking_frequency': "Monthly" if time_horizon < 1 else "Quarterly",
            'recommended_adjustments': [
                "Increase monthly contributions as income grows",
                "Review goal parameters and progress quarterly",
                "Adjust allocation as time horizon decreases"
            ] if capacity_sufficient else [
                "Consider one of the alternative scenarios",
                "Look for ways to increase monthly capacity",
                "Review goal priority relative to other goals"
            ]
        }
        
        return funding_plan
    
    def generate_custom_goal_insights(self, goal_description: str, goal_tags: List[str],
                                    goal_amount: float, time_horizon: float) -> Dict[str, Any]:
        """
        Generate custom insights for a specific goal based on description and parameters.
        
        Args:
            goal_description: User-provided description of the goal
            goal_tags: List of tags or categories associated with the goal
            goal_amount: Target goal amount
            time_horizon: Years to goal
            
        Returns:
            Dictionary with custom goal insights
        """
        # Initialize insights
        insights = {
            'potential_synergies': [],
            'potential_conflicts': [],
            'optimization_tips': [],
            'knowledge_resources': []
        }
        
        # Process description and tags for keywords
        education_keywords = ['education', 'learn', 'study', 'course', 'degree', 'skill', 'certification']
        business_keywords = ['business', 'startup', 'entrepreneur', 'venture', 'side hustle', 'passive income']
        property_keywords = ['property', 'house', 'apartment', 'real estate', 'home', 'renovation']
        travel_keywords = ['travel', 'trip', 'vacation', 'visit', 'journey', 'holiday', 'tour']
        vehicle_keywords = ['vehicle', 'car', 'bike', 'motorcycle', 'transportation']
        family_keywords = ['family', 'children', 'kid', 'parent', 'wedding', 'marriage']
        
        # Combine description and tags for analysis
        analysis_text = (goal_description or "").lower() + " " + " ".join(goal_tags or []).lower()
        
        # Detect potential goal categories
        goal_categories = []
        
        if any(keyword in analysis_text for keyword in education_keywords):
            goal_categories.append('education')
            
        if any(keyword in analysis_text for keyword in business_keywords):
            goal_categories.append('business')
            
        if any(keyword in analysis_text for keyword in property_keywords):
            goal_categories.append('property')
            
        if any(keyword in analysis_text for keyword in travel_keywords):
            goal_categories.append('travel')
            
        if any(keyword in analysis_text for keyword in vehicle_keywords):
            goal_categories.append('vehicle')
            
        if any(keyword in analysis_text for keyword in family_keywords):
            goal_categories.append('family')
            
        # Generate category-specific insights
        for category in goal_categories:
            if category == 'education':
                insights['potential_synergies'].append(
                    "Education goals often increase income potential, creating synergy with retirement and financial independence goals"
                )
                insights['optimization_tips'].append(
                    "Look for employer tuition reimbursement programs to reduce out-of-pocket costs"
                )
                insights['knowledge_resources'].append(
                    "Research tax benefits available for education (e.g., Section 80E interest deduction for education loans)"
                )
                
            elif category == 'business':
                insights['potential_synergies'].append(
                    "Business investments can create passive income supporting other financial goals"
                )
                insights['potential_conflicts'].append(
                    "Business funding may compete with emergency fund and retirement contributions"
                )
                insights['optimization_tips'].append(
                    "Consider business loans or investor funding to reduce personal financial burden"
                )
                
            elif category == 'property':
                insights['potential_synergies'].append(
                    "Property can serve dual purposes of housing and investment"
                )
                insights['optimization_tips'].append(
                    "Research home loan interest and principal tax benefits (Sections 24 and 80C)"
                )
                insights['knowledge_resources'].append(
                    "Connect with local real estate advisor to understand market trends in your area"
                )
                
            elif category == 'travel':
                insights['potential_conflicts'].append(
                    "Travel spending competes directly with long-term wealth building goals"
                )
                insights['optimization_tips'].append(
                    "Consider travel credit cards, off-peak timing, and advance bookings to reduce costs"
                )
                
            elif category == 'vehicle':
                insights['potential_conflicts'].append(
                    "Vehicle depreciation works against wealth-building objectives"
                )
                insights['optimization_tips'].append(
                    "Consider certified pre-owned vehicles to avoid initial depreciation"
                )
                
            elif category == 'family':
                insights['potential_synergies'].append(
                    "Family-related goals often align with legacy planning objectives"
                )
                insights['knowledge_resources'].append(
                    "Consult financial advisor regarding tax-efficient family financial planning"
                )
        
        # Generate time horizon specific insights
        if time_horizon < 1:
            insights['optimization_tips'].append(
                "For short-term goals, prioritize liquidity and safety over returns"
            )
            insights['optimization_tips'].append(
                "Consider sweep-in FDs or liquid funds for very short-term goals"
            )
            
        elif time_horizon > 10:
            insights['optimization_tips'].append(
                "For very long-term custom goals, equity allocation can be higher"
            )
            insights['optimization_tips'].append(
                "Set up automatic yearly increases in contribution amount (e.g., 5% annual increase)"
            )
            
        # Generate amount-specific insights
        if goal_amount > 1000000:  # 10 lakhs+
            insights['optimization_tips'].append(
                "For larger goals, consider breaking into phases or sub-goals for psychological wins"
            )
            insights['potential_conflicts'].append(
                "Large financial commitments may require careful balancing with other life priorities"
            )
            
        # Ensure each insight list has at least one item
        for category in insights:
            if not insights[category]:
                insights[category].append("No specific insights identified for this category")
                
        return {
            'detected_categories': goal_categories,
            'time_horizon_classification': 'short-term' if time_horizon < 1 else 
                                        ('medium-term' if time_horizon < 5 else 'long-term'),
            'insights': insights
        }
    
    def assess_goal_classification_confidence(self, goal_data):
        """
        Assess the confidence level in the custom goal classification to determine
        whether the goal is well-defined enough for optimization.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with classification confidence assessment
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        goal_title = goal_data.get('title', 'Custom Goal')
        goal_description = goal_data.get('description', '')
        goal_tags = goal_data.get('tags', [])
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        annual_income = goal_data.get('annual_income', 1200000)
        
        # Perform goal classification
        classification = self.classify_custom_goal(
            target_amount, time_horizon, annual_income, goal_description, goal_tags
        )
        
        # Extract classification components
        time_sensitivity = classification['classification']['time_sensitivity']
        wealth_building = classification['classification']['wealth_building']
        goal_magnitude = classification['classification']['goal_magnitude']
        priority_score = classification['priority_score']
        
        # Calculate confidence scores for each classification dimension
        time_sensitivity_confidence = 0.0
        wealth_building_confidence = 0.0
        goal_magnitude_confidence = 0.0
        
        # Time sensitivity confidence based on specificity of timeline
        if time_horizon > 0:
            if time_horizon < 1:
                time_sensitivity_confidence = 0.9  # Very specific short timeline
            elif time_horizon < 3:
                time_sensitivity_confidence = 0.8  # Medium-term timeline
            else:
                time_sensitivity_confidence = 0.7  # Longer timeline (more ambiguity)
        else:
            time_sensitivity_confidence = 0.4  # No specific timeline
        
        # Wealth building confidence based on goal description keywords
        wealth_building_keywords = {
            "strong": ["invest", "business", "asset", "property", "education", "skill", "certification", 
                       "career", "startup", "venture", "equity", "ownership", "financial growth"],
            "moderate": ["maintain", "repair", "upgrade", "improve", "update", "health", "well-being", 
                         "quality of life", "work tools", "equipment"],
            "minimal": ["vacation", "travel", "leisure", "entertainment", "celebration", "gift", 
                        "luxury", "hobby", "experience"]
        }
        
        # Count matching keywords for each wealth building category
        keyword_matches = {category: 0 for category in wealth_building_keywords}
        
        # Check goal description and tags for keywords
        combined_text = (goal_description + " " + " ".join(goal_tags)).lower()
        
        for category, keywords in wealth_building_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    keyword_matches[category] += 1
        
        # Calculate wealth building confidence
        total_matches = sum(keyword_matches.values())
        if total_matches > 0:
            primary_category = max(keyword_matches, key=keyword_matches.get)
            primary_matches = keyword_matches[primary_category]
            category_confidence = primary_matches / total_matches
            
            # If classification matches keyword analysis, higher confidence
            if primary_category == wealth_building:
                wealth_building_confidence = 0.7 + (category_confidence * 0.3)
            else:
                wealth_building_confidence = 0.5 + (category_confidence * 0.2)
        else:
            wealth_building_confidence = 0.5  # Default moderate confidence with no keywords
        
        # Goal magnitude confidence is high if target amount and income are provided
        if target_amount > 0 and annual_income > 0:
            goal_magnitude_confidence = 0.9
        elif target_amount > 0:
            goal_magnitude_confidence = 0.7
        else:
            goal_magnitude_confidence = 0.4
        
        # Calculate overall classification confidence (weighted average)
        rubric_weights = self.custom_params["goal_classification_rubric"]
        time_weight = float(rubric_weights["time_sensitivity"][time_sensitivity]["weight"])
        wealth_weight = float(rubric_weights["wealth_building"][wealth_building]["weight"])
        magnitude_weight = float(rubric_weights["goal_magnitude"][goal_magnitude]["weight"])
        
        total_weight = time_weight + wealth_weight + magnitude_weight
        
        if total_weight > 0:
            overall_confidence = (
                (time_sensitivity_confidence * time_weight) +
                (wealth_building_confidence * wealth_weight) +
                (goal_magnitude_confidence * magnitude_weight)
            ) / total_weight
        else:
            overall_confidence = (time_sensitivity_confidence + wealth_building_confidence + goal_magnitude_confidence) / 3
        
        # Determine confidence level
        if overall_confidence >= 0.8:
            confidence_level = "High"
            confidence_description = "Goal is well-defined and classification is reliable"
        elif overall_confidence >= 0.6:
            confidence_level = "Moderate"
            confidence_description = "Goal is reasonably defined but some aspects may need clarification"
        else:
            confidence_level = "Low"
            confidence_description = "Goal definition lacks clarity; consider providing more detail"
        
        # Determine if confidence meets threshold for optimization
        threshold_met = overall_confidence >= self.custom_optimization_params['classification_threshold']
        
        # Generate recommendations
        recommendations = []
        
        if not threshold_met:
            if time_sensitivity_confidence < 0.6:
                recommendations.append({
                    'priority': 'High',
                    'action': "Clarify goal timeline",
                    'rationale': "Timeline precision is important for effective planning",
                    'implementation': "Specify a target date or time period for goal completion"
                })
                
            if wealth_building_confidence < 0.6:
                recommendations.append({
                    'priority': 'Medium',
                    'action': "Clarify goal purpose and expected outcomes",
                    'rationale': "Understanding how this goal builds wealth helps optimize approach",
                    'implementation': "Describe anticipated benefits or returns from achieving this goal"
                })
                
            if goal_magnitude_confidence < 0.6:
                recommendations.append({
                    'priority': 'High',
                    'action': "Specify target amount",
                    'rationale': "Financial target is essential for funding strategy",
                    'implementation': "Estimate required amount based on research or similar goals"
                })
                
        # For moderate confidence, suggest refinements
        elif overall_confidence < 0.8:
            recommendations.append({
                'priority': 'Medium',
                'action': "Refine goal details",
                'rationale': "More precise goal definition enables better optimization",
                'implementation': "Add descriptive tags and specific milestones to goal"
            })
        
        # Generate classification refinement if suitable
        classification_refinement = None
        if combined_text and not threshold_met:
            # Analyze text for potential goal refinement
            indian_specific_patterns = self.custom_params["indian_specific_patterns"]["common_goals"]
            for pattern_name, pattern_data in indian_specific_patterns.items():
                pattern_keywords = pattern_name.replace("_", " ").split()
                matches = sum(1 for keyword in pattern_keywords if keyword.lower() in combined_text)
                if matches >= len(pattern_keywords) // 2:
                    classification_refinement = {
                        'suggested_pattern': pattern_name,
                        'description': pattern_data['description'],
                        'recommended_approach': pattern_data['approach']
                    }
                    break
        
        return {
            'classification': classification['classification'],
            'priority_score': priority_score,
            'confidence_scores': {
                'time_sensitivity': round(time_sensitivity_confidence, 2),
                'wealth_building': round(wealth_building_confidence, 2),
                'goal_magnitude': round(goal_magnitude_confidence, 2),
                'overall': round(overall_confidence, 2)
            },
            'confidence_level': confidence_level,
            'confidence_description': confidence_description,
            'threshold_met': threshold_met,
            'recommendations': recommendations,
            'classification_refinement': classification_refinement,
            'india_specific_considerations': {
                'pilgrimage_classification': 'Treat pilgrimage goals with appropriate cultural sensitivity',
                'major_ceremonies': 'Family events often require significant flexibility in timing',
                'business_ventures': 'Entrepreneurial goals should consider family structure implications'
            }
        }
    
    def assess_funding_flexibility(self, goal_data):
        """
        Assess the flexibility in funding approaches for the custom goal based on
        income patterns, competing goals, and timing considerations.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with funding flexibility assessment
        """
        # Initialize the constraints if needed
        self._initialize_constraints()
        
        # Extract necessary information
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        annual_income = goal_data.get('annual_income', 1200000)
        income_stability = goal_data.get('income_stability', 'stable')  # stable, variable, seasonal
        competing_goals = goal_data.get('competing_goals', [])
        current_savings = goal_data.get('current_savings', 0)
        bonus_structure = goal_data.get('bonus_structure', {})
        
        # Get goal classification for context
        classification = self.classify_custom_goal(
            target_amount, time_horizon, annual_income, 
            goal_data.get('description', ''), goal_data.get('tags', [])
        )
        
        # Calculate monthly capacity
        monthly_capacity = goal_data.get('monthly_capacity', annual_income * 0.1 / 12)
        
        # Calculate baseline monthly requirement
        if time_horizon <= 0:
            monthly_requirement = target_amount  # Immediate funding needed
        else:
            # Simple linear calculation without returns
            monthly_requirement = (target_amount - current_savings) / (time_horizon * 12)
        
        # Calculate flexibility score components
        
        # 1. Timing flexibility
        time_sensitivity = classification['classification']['time_sensitivity']
        if time_sensitivity == 'critical':
            timing_flexibility = 0.2  # Very low flexibility
        elif time_sensitivity == 'important':
            timing_flexibility = 0.5  # Moderate flexibility
        else:  # 'flexible'
            timing_flexibility = 0.9  # High flexibility
            
        # 2. Funding flexibility based on income pattern
        if income_stability == 'stable':
            funding_pattern_flexibility = 0.7  # Regular contributions viable
        elif income_stability == 'variable':
            funding_pattern_flexibility = 0.4  # Harder to commit to regular amounts
        else:  # 'seasonal'
            funding_pattern_flexibility = 0.3  # Very cyclical funding capability
        
        # 3. Capacity flexibility
        if monthly_capacity >= monthly_requirement * 1.5:
            capacity_flexibility = 0.9  # High excess capacity
        elif monthly_capacity >= monthly_requirement:
            capacity_flexibility = 0.7  # Sufficient capacity
        elif monthly_capacity >= monthly_requirement * 0.7:
            capacity_flexibility = 0.4  # Slightly tight
        else:
            capacity_flexibility = 0.2  # Very constrained
        
        # 4. Competition flexibility (other goals competing for resources)
        competing_goal_count = len(competing_goals)
        if competing_goal_count == 0:
            competition_flexibility = 0.9  # No competition
        elif competing_goal_count <= 2:
            competition_flexibility = 0.6  # Some competition
        else:
            competition_flexibility = 0.3  # High competition
            
        # Calculate overall funding flexibility (weighted average)
        overall_flexibility = (
            (timing_flexibility * 0.3) +
            (funding_pattern_flexibility * 0.25) +
            (capacity_flexibility * 0.35) +
            (competition_flexibility * 0.1)
        )
        
        # Determine flexibility level
        if overall_flexibility >= 0.7:
            flexibility_level = "High"
            flexibility_description = "Multiple viable funding approaches available"
        elif overall_flexibility >= 0.4:
            flexibility_level = "Moderate"
            flexibility_description = "Some flexibility in funding approaches with constraints"
        else:
            flexibility_level = "Low"
            flexibility_description = "Limited options for funding; structured approach required"
        
        # Identify suitable funding approaches
        suitable_approaches = []
        for approach_name, approach_data in self.custom_params["funding_approaches"].items():
            suitability_score = 0
            
            if approach_name == "systematic":
                # Systematic approach works best with stable income and sufficient capacity
                suitability_score = (funding_pattern_flexibility * 0.6) + (capacity_flexibility * 0.4)
                
            elif approach_name == "milestone":
                # Milestone approach works best with variable income and flexible timing
                suitability_score = (1 - funding_pattern_flexibility) * 0.5 + (timing_flexibility * 0.5)
                
            elif approach_name == "hybrid":
                # Hybrid approach is versatile but best with moderate flexibility across all dimensions
                suitability_score = overall_flexibility
                if 0.4 <= overall_flexibility <= 0.7:
                    suitability_score += 0.2  # Bonus for truly hybrid situations
            
            suitable_approaches.append({
                'approach': approach_name,
                'description': approach_data['description'],
                'method': approach_data['method'],
                'suitability_score': round(suitability_score, 2),
                'is_recommended': suitability_score >= 0.6
            })
        
        # Sort approaches by suitability
        suitable_approaches.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        # Determine primary recommended approach
        recommended_approach = suitable_approaches[0]['approach'] if suitable_approaches else None
        
        # Generate optimization opportunities
        optimization_opportunities = []
        
        if capacity_flexibility < 0.5:
            optimization_opportunities.append({
                'opportunity': "Increase Funding Capacity",
                'potential_impact': "Critical for goal viability",
                'implementation_options': [
                    "Reduce allocation to lower-priority goals",
                    "Explore additional income sources",
                    "Extend timeline if possible"
                ]
            })
            
        if income_stability == 'variable' or income_stability == 'seasonal':
            optimization_opportunities.append({
                'opportunity': "Structured Windfall Allocation",
                'potential_impact': "Maximize variable income utility",
                'implementation_options': [
                    "Create percentage-based allocation rules for bonuses",
                    "Establish minimum baseline funding from fixed income",
                    "Set up automatic transfers from variable income sources"
                ]
            })
            
        if competing_goal_count > 0:
            optimization_opportunities.append({
                'opportunity': "Goal Integration Strategy",
                'potential_impact': "Reduce competition for resources",
                'implementation_options': [
                    "Sequence goals to reduce simultaneous funding pressure",
                    "Find synergies between goals with similar timelines",
                    "Create unified funding pool with dynamic allocation rules"
                ]
            })
            
        # Indian-specific financial patterns
        india_specific_patterns = {
            'seasonal_income_management': "Plan for festival and agricultural cycle variations in income",
            'family_resource_pooling': "Consider joint family funding capabilities if applicable",
            'tax_planning_integration': "Coordinate with 80C investments and tax-saving strategies",
            'gold_accumulation': "Potential for systematic gold purchases as alternative funding vehicle"
        }
        
        return {
            'flexibility_scores': {
                'timing_flexibility': round(timing_flexibility, 2),
                'funding_pattern_flexibility': round(funding_pattern_flexibility, 2),
                'capacity_flexibility': round(capacity_flexibility, 2),
                'competition_flexibility': round(competition_flexibility, 2),
                'overall_flexibility': round(overall_flexibility, 2)
            },
            'flexibility_level': flexibility_level,
            'flexibility_description': flexibility_description,
            'funding_requirement': {
                'monthly_requirement': round(monthly_requirement),
                'monthly_capacity': round(monthly_capacity),
                'capacity_to_requirement_ratio': round(monthly_capacity / monthly_requirement, 2) if monthly_requirement > 0 else "N/A",
                'funding_gap': round(max(0, monthly_requirement - monthly_capacity) * time_horizon * 12)
            },
            'suitable_approaches': suitable_approaches,
            'recommended_approach': recommended_approach,
            'optimization_opportunities': optimization_opportunities,
            'india_specific_patterns': india_specific_patterns
        }
    
    def assess_financial_integration(self, goal_data):
        """
        Assess how well the custom goal integrates with existing financial plans,
        tax strategies, and overall portfolio.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with financial integration assessment
        """
        # Initialize the compound strategy if needed
        self._initialize_compound_strategy()
        
        # Extract necessary information
        goal_title = goal_data.get('title', 'Custom Goal')
        goal_description = goal_data.get('description', '')
        goal_tags = goal_data.get('tags', [])
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        tax_bracket = goal_data.get('tax_bracket', 0.3)
        existing_financial_plans = goal_data.get('existing_financial_plans', [])
        existing_investments = goal_data.get('existing_investments', {})
        
        # Get goal classification
        classification = self.classify_custom_goal(
            target_amount, time_horizon, goal_data.get('annual_income', 1200000),
            goal_description, goal_tags
        )
        
        # Get recommended allocation template
        base_template = classification['recommended_approach']['allocation_template']
        
        # Calculate integration metrics
        
        # 1. Tax efficiency potential
        tax_efficiency_potential = 0.0
        tax_efficiency_strategies = []
        
        # Detect potential tax advantages based on goal characteristics and Indian tax system
        if classification['classification']['wealth_building'] == 'strong':
            tax_efficiency_potential += 0.3
            
            if "education" in goal_description.lower() or "education" in goal_tags:
                tax_efficiency_potential += 0.2
                tax_efficiency_strategies.append({
                    'strategy': "Education Loan Interest Deduction",
                    'applicable_section': "Section 80E",
                    'benefit_description': "Unlimited deduction for interest on education loan"
                })
            
            if "business" in goal_description.lower() or "business" in goal_tags:
                tax_efficiency_potential += 0.2
                tax_efficiency_strategies.append({
                    'strategy': "Business Expense Deductions",
                    'applicable_section': "Various sections",
                    'benefit_description': "Multiple deductions available for business goals"
                })
        
        # Check for potential Section 80C benefits
        if time_horizon > 3 and target_amount > 150000:
            tax_efficiency_potential += 0.2
            tax_efficiency_strategies.append({
                'strategy': "ELSS Mutual Funds for Goal Funding",
                'applicable_section': "Section 80C",
                'benefit_description': "Tax deduction up to ₹1.5 lakh with 3-year lock-in"
            })
        
        # 2. Portfolio alignment
        portfolio_alignment = 0.0
        
        # Check if existing investments align with recommended allocation
        if existing_investments:
            # Calculate current allocation percentages
            total_investments = sum(existing_investments.values())
            current_allocation = {k: v / total_investments for k, v in existing_investments.items()}
            
            # Get recommended allocation from template
            recommended_allocation = {k: v for k, v in self.custom_params["allocation_templates"][base_template].items() 
                                    if k != 'expected_return'}
            
            # Calculate alignment score
            alignment_scores = []
            for asset_class, recommended_pct in recommended_allocation.items():
                current_pct = current_allocation.get(asset_class, 0)
                difference = abs(recommended_pct - current_pct)
                
                # Closer allocations get higher scores
                if difference < 0.05:
                    asset_alignment = 0.9
                elif difference < 0.1:
                    asset_alignment = 0.7
                elif difference < 0.2:
                    asset_alignment = 0.5
                else:
                    asset_alignment = 0.3
                    
                alignment_scores.append(asset_alignment)
            
            # Calculate overall portfolio alignment
            if alignment_scores:
                portfolio_alignment = sum(alignment_scores) / len(alignment_scores)
        
        # 3. Plan integration
        plan_integration = 0.0
        plan_synergies = []
        
        if existing_financial_plans:
            for plan in existing_financial_plans:
                plan_type = plan.get('type', '')
                plan_timeline = plan.get('timeline', 0)
                plan_amount = plan.get('amount', 0)
                
                synergy_score = 0
                synergy_description = ""
                
                # Check for timeline synergies
                if abs(plan_timeline - time_horizon) < 1:
                    synergy_score += 0.3
                    synergy_description += "Similar timeline; "
                
                # Check for complementary goals
                if (plan_type == 'retirement' and 
                    classification['classification']['wealth_building'] == 'strong'):
                    synergy_score += 0.3
                    synergy_description += "Complementary wealth-building; "
                
                # Check for potential conflicts (e.g., two major expenses at same time)
                if (abs(plan_timeline - time_horizon) < 1 and 
                    plan_amount > 500000 and target_amount > 500000):
                    synergy_score -= 0.3
                    synergy_description += "Potential resource competition; "
                
                if synergy_score != 0:
                    plan_synergies.append({
                        'plan_type': plan_type,
                        'synergy_score': round(synergy_score, 2),
                        'synergy_description': synergy_description.strip('; ')
                    })
                    
            # Calculate overall plan integration score
            if plan_synergies:
                total_synergy = sum(s['synergy_score'] for s in plan_synergies)
                plan_integration = (total_synergy / len(plan_synergies) + 1) / 2  # Normalize to 0-1
                plan_integration = max(0, min(1, plan_integration))  # Clamp to 0-1
        
        # Calculate overall integration score
        overall_integration = (
            (tax_efficiency_potential * 0.3) +
            (portfolio_alignment * 0.4) +
            (plan_integration * 0.3)
        )
        
        # Determine integration level
        if overall_integration >= 0.7:
            integration_level = "High"
            integration_description = "Goal integrates well with existing financial plans and portfolio"
        elif overall_integration >= 0.4:
            integration_level = "Moderate"
            integration_description = "Goal has some integration points but additional alignment possible"
        else:
            integration_level = "Low"
            integration_description = "Goal exists largely separate from other financial plans"
        
        # Generate optimization recommendations
        optimization_recommendations = []
        
        if tax_efficiency_potential < 0.5:
            optimization_recommendations.append({
                'priority': 'Medium',
                'action': "Explore tax-efficient funding vehicles",
                'rationale': "Improve after-tax returns on goal funding",
                'implementation': "Consider ELSS investments, PPF, or other tax-advantaged accounts"
            })
            
        if portfolio_alignment < 0.5:
            optimization_recommendations.append({
                'priority': 'High',
                'action': "Align goal investments with existing portfolio",
                'rationale': "Reduce complexity and improve overall efficiency",
                'implementation': "Consolidate similar asset classes and use existing investment vehicles"
            })
            
        if plan_integration < 0.5 and existing_financial_plans:
            optimization_recommendations.append({
                'priority': 'Medium',
                'action': "Coordinate goal timeline with existing plans",
                'rationale': "Avoid resource competition and leverage synergies",
                'implementation': "Adjust timing or funding approach to complement existing goals"
            })
            
        # Indian-specific integration considerations
        india_specific_integration = {
            'tax_optimizations': {
                'section_80c_integration': "Consider ELSS mutual funds for dual-purpose goal funding",
                'ppf_integration': "Public Provident Fund can serve multiple goals simultaneously",
                'sukanya_samriddhi': "For girl child education/wedding goals, highly tax-efficient option"
            },
            'cultural_considerations': {
                'joint_family_resources': "Consider shared family resources for certain goal types",
                'multi_generational_planning': "Align with family lifecycle events across generations",
                'religious_timing': "Consider auspicious dates for major financial decisions"
            }
        }
        
        return {
            'integration_scores': {
                'tax_efficiency_potential': round(tax_efficiency_potential, 2),
                'portfolio_alignment': round(portfolio_alignment, 2),
                'plan_integration': round(plan_integration, 2),
                'overall_integration': round(overall_integration, 2)
            },
            'integration_level': integration_level,
            'integration_description': integration_description,
            'tax_efficiency_strategies': tax_efficiency_strategies,
            'plan_synergies': plan_synergies,
            'optimization_recommendations': optimization_recommendations,
            'india_specific_integration': india_specific_integration
        }
    
    def assess_sustainability_metrics(self, goal_data):
        """
        Assess the long-term sustainability of the custom goal, including
        environmental and social impact factors where applicable.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with sustainability assessment
        """
        # Extract necessary information
        goal_title = goal_data.get('title', 'Custom Goal')
        goal_description = goal_data.get('description', '')
        goal_tags = goal_data.get('tags', [])
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        annual_income = goal_data.get('annual_income', 1200000)
        
        # Get goal classification
        classification = self.classify_custom_goal(
            target_amount, time_horizon, annual_income, goal_description, goal_tags
        )
        
        # Detect sustainability-related keywords in goal description and tags
        combined_text = (goal_description + " " + " ".join(goal_tags)).lower()
        
        # Sustainability keyword categories
        sustainability_categories = {
            'environmental': [
                'environment', 'sustainable', 'green', 'eco', 'renewable', 
                'solar', 'conservation', 'climate', 'pollution', 'organic'
            ],
            'social': [
                'community', 'education', 'health', 'welfare', 'charity', 
                'nonprofit', 'donation', 'volunteer', 'social impact'
            ],
            'ethical': [
                'ethical', 'responsible', 'fair trade', 'governance', 
                'transparency', 'values-based', 'integrity'
            ]
        }
        
        # Check for sustainability keywords
        sustainability_matches = {category: 0 for category in sustainability_categories}
        for category, keywords in sustainability_categories.items():
            for keyword in keywords:
                if keyword in combined_text:
                    sustainability_matches[category] += 1
        
        # Calculate sustainability relevance
        total_matches = sum(sustainability_matches.values())
        sustainability_relevance = min(1.0, total_matches / 5)  # Cap at 1.0
        
        # Financial sustainability metrics
        # 1. Income sustainability: ratio of goal to income
        income_ratio = target_amount / annual_income if annual_income > 0 else float('inf')
        
        if income_ratio < 0.1:
            income_sustainability = 0.9  # Very sustainable
        elif income_ratio < 0.3:
            income_sustainability = 0.7  # Sustainable
        elif income_ratio < 0.5:
            income_sustainability = 0.5  # Moderately sustainable
        elif income_ratio < 1.0:
            income_sustainability = 0.3  # Challenging
        else:
            income_sustainability = 0.1  # Very challenging
            
        # 2. Timeline sustainability: realistic timeframe
        if income_ratio > 0 and time_horizon > 0:
            annual_funding_required = target_amount / time_horizon
            annual_funding_ratio = annual_funding_required / annual_income
            
            if annual_funding_ratio < 0.05:
                timeline_sustainability = 0.9  # Very realistic timeline
            elif annual_funding_ratio < 0.1:
                timeline_sustainability = 0.7  # Realistic timeline
            elif annual_funding_ratio < 0.2:
                timeline_sustainability = 0.5  # Moderately realistic
            elif annual_funding_ratio < 0.3:
                timeline_sustainability = 0.3  # Challenging timeline
            else:
                timeline_sustainability = 0.1  # Very challenging timeline
        else:
            timeline_sustainability = 0.5  # Default moderate score
            
        # 3. Lifecycle sustainability: alignment with life stages
        # Extract age if available
        age = goal_data.get('age', 30)
        
        # Determine appropriate goals for life stage
        if age < 30:
            appropriate_goals = ['education', 'career', 'skills', 'travel', 'home']
        elif age < 45:
            appropriate_goals = ['home', 'family', 'career', 'business', 'education']
        elif age < 60:
            appropriate_goals = ['retirement', 'health', 'education', 'legacy']
        else:
            appropriate_goals = ['health', 'legacy', 'family', 'retirement']
            
        # Check if goal matches appropriate goals for life stage
        lifecycle_matches = sum(1 for goal in appropriate_goals if goal in combined_text)
        lifecycle_sustainability = min(0.9, lifecycle_matches * 0.3)
        
        if lifecycle_sustainability == 0:
            lifecycle_sustainability = 0.5  # Default moderate if no clear matches
            
        # Overall financial sustainability
        financial_sustainability = (
            (income_sustainability * 0.4) +
            (timeline_sustainability * 0.4) +
            (lifecycle_sustainability * 0.2)
        )
        
        # Determine overall sustainability level
        overall_sustainability = financial_sustainability
        
        # If sustainability is relevant to this goal, factor it in
        if sustainability_relevance > 0.3:
            esg_factor = 0.2  # Environmental/social/governance impact
            overall_sustainability = (financial_sustainability * (1 - esg_factor)) + (sustainability_relevance * esg_factor)
        
        # Determine sustainability level
        if overall_sustainability >= 0.7:
            sustainability_level = "High"
            sustainability_description = "Goal is financially and structurally sustainable"
        elif overall_sustainability >= 0.4:
            sustainability_level = "Moderate"
            sustainability_description = "Goal has reasonable sustainability with some challenges"
        else:
            sustainability_level = "Low"
            sustainability_description = "Goal sustainability faces significant challenges"
        
        # Generate optimization opportunities
        optimization_opportunities = []
        
        if income_sustainability < 0.5:
            optimization_opportunities.append({
                'opportunity': "Scale Goal Appropriately",
                'potential_impact': "Improve financial sustainability",
                'implementation_options': [
                    "Adjust target amount to more realistic level",
                    "Break into smaller sub-goals with phased approach",
                    "Explore alternative approaches with lower financial requirements"
                ]
            })
            
        if timeline_sustainability < 0.5:
            optimization_opportunities.append({
                'opportunity': "Extend Timeline",
                'potential_impact': "Reduce annual funding pressure",
                'implementation_options': [
                    "Extend goal completion timeframe",
                    "Implement phased achievement approach",
                    "Prioritize sub-components with sequential completion"
                ]
            })
            
        if sustainability_relevance > 0.3:
            optimization_opportunities.append({
                'opportunity': "Enhance Sustainable Impact",
                'potential_impact': "Align financial and impact objectives",
                'implementation_options': [
                    "Integrate ESG criteria into investment selections",
                    "Measure and track impact metrics alongside financial progress",
                    "Connect with like-minded communities for resource sharing"
                ]
            })
            
        # Indian-specific sustainability considerations
        india_specific_considerations = {
            'traditional_sustainability': "Consider traditional Indian sustainable practices relevant to goal",
            'local_resource_utilization': "Evaluate locally available resources to reduce imported dependencies",
            'community_sustainability': "Assess impact on local community and potential for shared resources",
            'intergenerational_transfer': "Consider sustainability across generations for long-term family goals"
        }
        
        return {
            'sustainability_metrics': {
                'income_sustainability': round(income_sustainability, 2),
                'timeline_sustainability': round(timeline_sustainability, 2),
                'lifecycle_sustainability': round(lifecycle_sustainability, 2),
                'overall_sustainability': round(overall_sustainability, 2)
            },
            'sustainability_level': sustainability_level,
            'sustainability_description': sustainability_description,
            'esg_relevance': {
                'relevance_score': round(sustainability_relevance, 2),
                'category_matches': sustainability_matches
            },
            'lifecycle_alignment': {
                'current_life_stage': 'Young adult' if age < 30 else 'Mid-career' if age < 45 else 'Pre-retirement' if age < 60 else 'Retirement',
                'appropriate_goals': appropriate_goals,
                'alignment_score': round(lifecycle_sustainability, 2)
            },
            'optimization_opportunities': optimization_opportunities,
            'india_specific_considerations': india_specific_considerations
        }
    
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy for custom goals with adaptable approaches
        based on goal classification, prioritization, and individual characteristics.
        
        Args:
            goal_data: Dictionary with custom goal details
            profile_data: Optional dictionary with profile details
            
        Returns:
            Dictionary with rebalancing strategy tailored for custom goals
        """
        # Create rebalancing strategy instance
        rebalancing = RebalancingStrategy()
        
        # Extract custom goal specific information
        goal_title = goal_data.get('title', 'Custom Goal')
        goal_description = goal_data.get('description', '')
        goal_tags = goal_data.get('tags', [])
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        annual_income = goal_data.get('annual_income', 1200000)
        
        # Create minimal profile if not provided
        if not profile_data:
            profile_data = {
                'risk_profile': risk_profile,
                'portfolio_value': target_amount * 0.5,  # Assumption for portfolio size
                'market_volatility': 'normal'
            }
        
        # Classify the custom goal
        goal_classification = self.classify_custom_goal(
            target_amount, time_horizon, annual_income, goal_description, goal_tags
        )
        
        # Get the base template based on classification
        base_template = goal_classification['recommended_approach']['allocation_template']
        priority_score = goal_classification['priority_score']
        
        # Get the custom allocation based on the goal's parameters
        allocation = self.customize_allocation_model(
            base_template, time_horizon, risk_profile, priority_score
        )
        
        # Convert allocation to rebalancing format (remove expected_return)
        rebalancing_allocation = {k: v for k, v in allocation.items() if k != 'expected_return'}
        
        # Create rebalancing goal with custom goal focus
        rebalancing_goal = {
            'goal_type': 'custom',
            'goal_title': goal_title,
            'goal_description': goal_description,
            'goal_tags': goal_tags,
            'time_horizon': time_horizon,
            'target_allocation': rebalancing_allocation,
            'target_amount': target_amount,
            'priority_score': priority_score,
            'profile_data': profile_data,
            'classification': goal_classification['classification']
        }
        
        # Design rebalancing schedule specific to custom goal
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(rebalancing_goal, profile_data)
        
        # Calculate threshold factors based on goal classification and priority
        threshold_factors = {}
        
        # Get time sensitivity classification (determines how strict thresholds should be)
        time_sensitivity = goal_classification['classification']['time_sensitivity']
        
        # Set base threshold factors based on time sensitivity
        if time_sensitivity == 'critical':
            # Critical time sensitivity requires tighter thresholds
            base_factors = {
                'cash': 0.7,          # 30% tighter for cash
                'short_term_debt': 0.8,  # 20% tighter for short-term debt
                'balanced_funds': 0.8,   # 20% tighter for balanced funds
                'equity': 0.7            # 30% tighter for equity
            }
        elif time_sensitivity == 'important':
            # Important time sensitivity requires moderately tight thresholds
            base_factors = {
                'cash': 0.8,          # 20% tighter for cash
                'short_term_debt': 0.9,  # 10% tighter for short-term debt
                'balanced_funds': 0.9,   # 10% tighter for balanced funds
                'equity': 0.8            # 20% tighter for equity
            }
        else:  # 'flexible'
            # Flexible time sensitivity allows for normal thresholds
            base_factors = {
                'cash': 1.0,          # Standard for cash
                'short_term_debt': 1.0,  # Standard for short-term debt
                'balanced_funds': 1.0,   # Standard for balanced funds
                'equity': 1.0            # Standard for equity
            }
        
        # Adjust based on goal magnitude (determines overall importance)
        goal_magnitude = goal_classification['classification']['goal_magnitude']
        magnitude_adjustment = 1.0
        
        if goal_magnitude == 'major':
            # Major goals get slightly tighter thresholds
            magnitude_adjustment = 0.9  # 10% tighter overall
        elif goal_magnitude == 'minor':
            # Minor goals can have slightly wider thresholds
            magnitude_adjustment = 1.1  # 10% wider overall
        
        # Adjust based on wealth building aspect (determines growth vs preservation focus)
        wealth_building = goal_classification['classification']['wealth_building']
        
        # Apply adjustments to base factors
        for asset in base_factors:
            # Start with base factor for this asset
            factor = base_factors[asset]
            
            # Apply magnitude adjustment
            factor *= magnitude_adjustment
            
            # Apply wealth building specific adjustments
            if wealth_building == 'strong':
                # For wealth building goals, allow more flexibility in growth assets
                if asset == 'equity':
                    factor *= 1.2  # 20% wider for equity
                elif asset == 'balanced_funds':
                    factor *= 1.1  # 10% wider for balanced funds
            elif wealth_building == 'minimal':
                # For consumption goals, be stricter with growth assets
                if asset == 'equity':
                    factor *= 0.9  # 10% tighter for equity
            
            # Apply time horizon specific adjustments
            if time_horizon < 1:
                # Very short timeframe - tighter control on volatile assets
                if asset == 'equity':
                    factor *= 0.8  # Additional 20% tighter for equity
                elif asset == 'balanced_funds':
                    factor *= 0.9  # Additional 10% tighter for balanced funds
            elif time_horizon > 5:
                # Longer timeframe - can be more flexible with all assets
                factor *= 1.1  # 10% wider across the board for long-term goals
            
            # Store final factor
            threshold_factors[asset] = factor
        
        # Ensure we have factors for all assets in our allocation
        for asset in rebalancing_allocation:
            if asset not in threshold_factors:
                # Default to moderate control for any asset not specifically addressed
                threshold_factors[asset] = 0.9  # 10% tighter than standard
        
        # Calculate base drift thresholds
        base_thresholds = rebalancing.calculate_drift_thresholds(rebalancing_allocation)
        
        # Apply custom threshold factors
        custom_thresholds = {
            'threshold_rationale': f"Custom goal thresholds for {goal_title} with priority score {priority_score}",
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
        
        # Create comprehensive custom goal rebalancing strategy
        custom_rebalancing_strategy = {
            'goal_type': 'custom',
            'goal_title': goal_title,
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': custom_thresholds,
            'goal_specific_considerations': {
                'classification_impact': f"Rebalancing approach tailored to {time_sensitivity} time sensitivity and {wealth_building} wealth building classification",
                'priority_impact': f"Goal priority score of {priority_score} influences rebalancing thresholds and frequency",
                'milestone_integration': "Rebalancing schedule aligned with goal's 25%, 50%, and 75% funding milestones"
            },
            'implementation_priorities': [
                f"Follow {base_template.replace('_', ' ')} allocation framework with custom adjustments",
                "Adjust rebalancing approach as time horizon decreases",
                "Review and potentially tighten thresholds at each milestone",
                "Integrate with overall portfolio rebalancing when possible for efficiency"
            ]
        }
        
        # Add goal category-specific considerations if available
        detected_categories = self.generate_custom_goal_insights(
            goal_description, goal_tags, target_amount, time_horizon
        )['detected_categories']
        
        if detected_categories:
            category_considerations = {}
            
            for category in detected_categories:
                if category == 'education':
                    category_considerations['education'] = "Align rebalancing with academic calendar and funding deadlines"
                elif category == 'business':
                    category_considerations['business'] = "Consider business cash flow cycles in rebalancing timing"
                elif category == 'property':
                    category_considerations['property'] = "Coordinate with real estate market seasonality when possible"
                elif category == 'travel':
                    category_considerations['travel'] = "Plan rebalancing to optimize for currency exchange if international travel"
                elif category == 'vehicle':
                    category_considerations['vehicle'] = "Consider end-of-model-year timing for potential cost savings"
                elif category == 'family':
                    category_considerations['family'] = "Align with family milestones and life events for meaningful integration"
            
            if category_considerations:
                custom_rebalancing_strategy['category_specific_considerations'] = category_considerations
        
        return custom_rebalancing_strategy
    
    def optimize_goal_classification(self, goal_data):
        """
        Optimize the goal classification for better targeting and effectiveness.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with optimized goal classification
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Get current classification
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        annual_income = goal_data.get('annual_income', 1200000)
        goal_description = goal_data.get('description', '')
        goal_tags = goal_data.get('tags', [])
        
        current_classification = self.classify_custom_goal(
            target_amount, time_horizon, annual_income, goal_description, goal_tags
        )
        
        # Get classification confidence assessment
        confidence_assessment = self.assess_goal_classification_confidence(goal_data)
        
        # Detect ambiguities or potential miscategorizations
        time_sensitivity = current_classification['classification']['time_sensitivity']
        wealth_building = current_classification['classification']['wealth_building']
        goal_magnitude = current_classification['classification']['goal_magnitude']
        
        # Identify potential refinements for each dimension
        time_sensitivity_refinement = None
        wealth_building_refinement = None
        goal_magnitude_refinement = None
        
        # Extract age if available for lifecycle-based refinements
        age = goal_data.get('age', 30)
        
        # Analyze combined text for keywords
        combined_text = (goal_description + " " + " ".join(goal_tags)).lower()
        
        # Time sensitivity refinement
        if confidence_assessment['confidence_scores']['time_sensitivity'] < 0.7:
            # Check for urgency keywords
            urgency_keywords = ['immediate', 'urgent', 'soon', 'quickly', 'deadline', 'asap']
            flexibility_keywords = ['flexible', 'adjustable', 'eventually', 'when possible', 'no rush']
            
            urgency_count = sum(1 for word in urgency_keywords if word in combined_text)
            flexibility_count = sum(1 for word in flexibility_keywords if word in combined_text)
            
            if urgency_count > 0 and time_sensitivity != 'critical':
                time_sensitivity_refinement = {
                    'proposed_classification': 'critical',
                    'confidence': min(0.7, 0.5 + urgency_count * 0.1),
                    'rationale': f"Detected urgency keywords: {', '.join([w for w in urgency_keywords if w in combined_text])}"
                }
            elif flexibility_count > 0 and time_sensitivity == 'critical':
                time_sensitivity_refinement = {
                    'proposed_classification': 'flexible',
                    'confidence': min(0.7, 0.5 + flexibility_count * 0.1),
                    'rationale': f"Detected flexibility keywords: {', '.join([w for w in flexibility_keywords if w in combined_text])}"
                }
        
        # Wealth building refinement
        if confidence_assessment['confidence_scores']['wealth_building'] < 0.7:
            # Detect Indian-specific wealth building patterns
            if 'business' in combined_text and 'family' in combined_text:
                wealth_building_refinement = {
                    'proposed_classification': 'strong',
                    'confidence': 0.8,
                    'rationale': "Family business ventures are key wealth-building vehicles in Indian context"
                }
            elif 'education' in combined_text and wealth_building != 'strong':
                wealth_building_refinement = {
                    'proposed_classification': 'strong',
                    'confidence': 0.8,
                    'rationale': "Education is a primary wealth-building investment in Indian context"
                }
            elif 'property' in combined_text and wealth_building != 'strong':
                wealth_building_refinement = {
                    'proposed_classification': 'strong',
                    'confidence': 0.8,
                    'rationale': "Property acquisition is a major wealth-building strategy in Indian context"
                }
            elif ('vacation' in combined_text or 'travel' in combined_text) and 'pilgrimage' in combined_text:
                # Religious travel often has deeper meaning than pure consumption
                wealth_building_refinement = {
                    'proposed_classification': 'moderate',
                    'confidence': 0.7,
                    'rationale': "Religious pilgrimage has cultural wealth building aspects beyond consumption"
                }
        
        # Goal magnitude refinement
        if confidence_assessment['confidence_scores']['goal_magnitude'] < 0.7:
            # Check for Indian-specific magnitude considerations
            if 'wedding' in combined_text and goal_magnitude != 'major':
                goal_magnitude_refinement = {
                    'proposed_classification': 'major',
                    'confidence': 0.9,
                    'rationale': "Weddings are typically major financial commitments in Indian context"
                }
            elif ('education' in combined_text and 'abroad' in combined_text) and goal_magnitude != 'major':
                goal_magnitude_refinement = {
                    'proposed_classification': 'major',
                    'confidence': 0.9,
                    'rationale': "Foreign education represents major financial commitment in Indian context"
                }
        
        # Generate optimized classification
        optimized_classification = {
            'original_classification': current_classification['classification'],
            'optimized_classification': {
                'time_sensitivity': time_sensitivity_refinement['proposed_classification'] if time_sensitivity_refinement else time_sensitivity,
                'wealth_building': wealth_building_refinement['proposed_classification'] if wealth_building_refinement else wealth_building,
                'goal_magnitude': goal_magnitude_refinement['proposed_classification'] if goal_magnitude_refinement else goal_magnitude
            },
            'refinements': {
                'time_sensitivity': time_sensitivity_refinement,
                'wealth_building': wealth_building_refinement,
                'goal_magnitude': goal_magnitude_refinement
            },
            'confidence_improvement': {
                'original_confidence': confidence_assessment['confidence_scores']['overall'],
                'optimized_confidence': min(1.0, confidence_assessment['confidence_scores']['overall'] + 
                                         (0.1 if time_sensitivity_refinement else 0) +
                                         (0.1 if wealth_building_refinement else 0) +
                                         (0.1 if goal_magnitude_refinement else 0))
            }
        }
        
        # Recalculate priority score
        original_priority = current_classification['priority_score']
        
        # Adjust priority score based on refinements
        priority_adjustment = 0
        
        if time_sensitivity_refinement:
            if time_sensitivity_refinement['proposed_classification'] == 'critical':
                priority_adjustment += 10
            elif time_sensitivity_refinement['proposed_classification'] == 'flexible':
                priority_adjustment -= 10
                
        if wealth_building_refinement:
            if wealth_building_refinement['proposed_classification'] == 'strong':
                priority_adjustment += 10
            elif wealth_building_refinement['proposed_classification'] == 'minimal':
                priority_adjustment -= 10
                
        if goal_magnitude_refinement:
            if goal_magnitude_refinement['proposed_classification'] == 'major':
                priority_adjustment += 10
            elif goal_magnitude_refinement['proposed_classification'] == 'minor':
                priority_adjustment -= 10
        
        optimized_priority = max(0, min(100, original_priority + priority_adjustment))
        
        optimized_classification['priority_scores'] = {
            'original_priority': original_priority,
            'optimized_priority': optimized_priority,
            'adjustment': priority_adjustment
        }
        
        # Generate implementation recommendations
        recommendations = []
        
        if time_sensitivity_refinement:
            if time_sensitivity_refinement['proposed_classification'] == 'critical':
                recommendations.append({
                    'priority': 'High',
                    'action': "Adjust timeline expectations",
                    'rationale': "Goal appears more time-critical than initially classified",
                    'implementation': "Create stricter timeline with specific milestones and deadlines"
                })
            elif time_sensitivity_refinement['proposed_classification'] == 'flexible':
                recommendations.append({
                    'priority': 'Medium',
                    'action': "Build in timeline flexibility",
                    'rationale': "Goal appears more time-flexible than initially classified",
                    'implementation': "Create adjustable timeline with optional acceleration points"
                })
                
        if wealth_building_refinement:
            if wealth_building_refinement['proposed_classification'] == 'strong':
                recommendations.append({
                    'priority': 'High',
                    'action': "Reframe as wealth-building investment",
                    'rationale': "Goal has stronger wealth-building potential than initially classified",
                    'implementation': "Approach goal as investment with expected returns, not consumption"
                })
            elif wealth_building_refinement['proposed_classification'] == 'minimal':
                recommendations.append({
                    'priority': 'Medium',
                    'action': "Budget as consumption expense",
                    'rationale': "Goal represents consumption rather than investment",
                    'implementation': "Fund from discretionary spending rather than investment portfolio"
                })
                
        # Indian-specific optimizations
        india_specific_optimizations = {
            'cultural_context': "Consider goal within joint family financial planning framework",
            'wealth_perception': "Adjust wealth-building classification based on Indian asset preferences",
            'priority_framework': "Align priority with cultural expectations and family considerations"
        }
        
        # Add classification refinement if detected by confidence assessment
        if confidence_assessment['classification_refinement']:
            india_specific_optimizations['cultural_pattern'] = {
                'pattern': confidence_assessment['classification_refinement']['suggested_pattern'],
                'description': confidence_assessment['classification_refinement']['description'],
                'approach': confidence_assessment['classification_refinement']['recommended_approach']
            }
        
        return {
            'optimized_classification': optimized_classification,
            'recommendations': recommendations,
            'india_specific_optimizations': india_specific_optimizations,
            'implementation_steps': [
                "Update goal classification in financial planning system",
                "Adjust funding approach based on optimized classification",
                "Revise timeline and milestone tracking if time sensitivity changed",
                "Reassess goal priority in overall financial plan"
            ]
        }
    
    def optimize_funding_approach(self, goal_data):
        """
        Optimize the funding approach for the custom goal based on goal characteristics,
        income patterns, and financial constraints.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with optimized funding approach
        """
        # Initialize constraints if needed
        self._initialize_constraints()
        
        # Get flexibility assessment
        flexibility_assessment = self.assess_funding_flexibility(goal_data)
        
        # Extract key information
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        current_savings = goal_data.get('current_savings', 0)
        monthly_capacity = goal_data.get('monthly_capacity', goal_data.get('annual_income', 1200000) * 0.1 / 12)
        income_stability = goal_data.get('income_stability', 'stable')
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        
        # Get recommended approach from flexibility assessment
        recommended_approach = flexibility_assessment['recommended_approach']
        
        # Get current funding gap
        monthly_requirement = flexibility_assessment['funding_requirement']['monthly_requirement']
        funding_gap = flexibility_assessment['funding_requirement']['funding_gap']
        
        # Optimize funding allocation based on approach
        optimized_allocation = {}
        
        if recommended_approach == 'systematic':
            # Systematic approach - focus on regular monthly contributions
            base_monthly = monthly_capacity * 0.8  # 80% of capacity for regular contributions
            buffer_monthly = monthly_capacity * 0.2  # 20% buffer for flexibility
            
            optimized_allocation = {
                'regular_monthly': round(base_monthly),
                'buffer_monthly': round(buffer_monthly),
                'annual_lump_sum': 0,
                'milestone_based': 0
            }
            
        elif recommended_approach == 'milestone':
            # Milestone approach - focus on lump sums at key points
            base_monthly = monthly_capacity * 0.4  # 40% of capacity for regular contributions
            annual_lump_sum = monthly_capacity * 3  # Quarterly lump sum
            
            optimized_allocation = {
                'regular_monthly': round(base_monthly),
                'buffer_monthly': 0,
                'annual_lump_sum': round(annual_lump_sum),
                'milestone_based': target_amount * 0.2  # 20% of goal at major milestones
            }
            
        else:  # hybrid approach
            # Hybrid approach - balanced between regular and milestone funding
            base_monthly = monthly_capacity * 0.6  # 60% of capacity for regular contributions
            annual_lump_sum = monthly_capacity * 2  # Semi-annual lump sum
            
            optimized_allocation = {
                'regular_monthly': round(base_monthly),
                'buffer_monthly': 0,
                'annual_lump_sum': round(annual_lump_sum),
                'milestone_based': target_amount * 0.1  # 10% of goal at major milestones
            }
        
        # Calculate overall funding coverage
        monthly_coverage = optimized_allocation['regular_monthly'] / monthly_requirement if monthly_requirement > 0 else 1
        annual_lump_sum_monthly_equivalent = optimized_allocation['annual_lump_sum'] / 12
        total_monthly_equivalent = optimized_allocation['regular_monthly'] + annual_lump_sum_monthly_equivalent
        total_coverage = total_monthly_equivalent / monthly_requirement if monthly_requirement > 0 else 1
        
        # Create implementation timeline
        implementation_timeline = []
        
        # Immediate actions
        implementation_timeline.append({
            'phase': 'Immediate (0-30 days)',
            'actions': [
                f"Set up automatic transfer of ₹{optimized_allocation['regular_monthly']} monthly",
                "Create goal tracking system with visual progress indicators",
                "Document funding strategy with specific milestones"
            ]
        })
        
        # Short-term actions
        short_term_actions = []
        if optimized_allocation['annual_lump_sum'] > 0:
            short_term_actions.append(f"Schedule first lump sum contribution of ₹{optimized_allocation['annual_lump_sum']}")
            
        if recommended_approach == 'milestone' or recommended_approach == 'hybrid':
            short_term_actions.append("Define specific milestones that trigger additional contributions")
            
        short_term_actions.append("Set up separate account or tracking mechanism for this goal")
        
        implementation_timeline.append({
            'phase': 'Short-term (1-3 months)',
            'actions': short_term_actions
        })
        
        # Medium-term actions
        medium_term_actions = [
            "Review and adjust regular contribution amounts quarterly",
            "Assess progress towards goal and adjust strategy as needed"
        ]
        
        implementation_timeline.append({
            'phase': 'Medium-term (3-12 months)',
            'actions': medium_term_actions
        })
        
        # Generate optimization strategies based on funding gap
        optimization_strategies = []
        
        if total_coverage < 0.9:
            # Significant funding gap - suggest more aggressive strategies
            optimization_strategies.append({
                'strategy': "Increase Funding Capacity",
                'potential_impact': "High - addresses fundamental gap",
                'implementation_options': [
                    "Reprioritize existing goals to free up capacity",
                    "Identify potential additional income sources",
                    "Extend goal timeline to reduce monthly requirement"
                ]
            })
            
        if income_stability != 'stable':
            # Variable income - need strategies to manage inconsistency
            optimization_strategies.append({
                'strategy': "Income Stability Management",
                'potential_impact': "Medium - improves consistency",
                'implementation_options': [
                    "Create buffer fund to normalize contribution pattern",
                    "Map contribution schedule to income cycle",
                    "Set percentage-based rules for variable income"
                ]
            })
            
        # Always include investment optimization
        allocation_template = "Growth-oriented" if time_horizon > 3 else "Balanced" if time_horizon > 1 else "Capital preservation"
        optimization_strategies.append({
            'strategy': "Investment Optimization",
            'potential_impact': "Medium - improves returns",
            'implementation_options': [
                f"Use {allocation_template} investment strategy",
                "Align investment selections with timeline",
                "Consider tax efficiency in investment selections"
            ]
        })
        
        # Indian-specific funding optimizations
        india_specific_optimizations = {
            'systematic_investment_plans': "Use SIPs in mutual funds for disciplined investing",
            'annual_investment_options': "Consider tax-saving investments like ELSS funds if applicable",
            'family_funding_mechanisms': {
                'joint_accounts': "Consider joint family accounts for major goals",
                'gift_contributions': "Incorporate family gift giving traditions for goal funding",
                'ceremonial_timing': "Align major contributions with auspicious occasions"
            }
        }
        
        # For short time horizons, suggest gold-based strategies (culturally relevant)
        if time_horizon < 2:
            india_specific_optimizations['short_term_strategies'] = {
                'gold_accumulation': "Gold accumulation as cultural alternative to financial instruments",
                'gold_monetization': "Consider gold monetization scheme for existing gold assets",
                'digital_gold': "Digital gold options for smaller regular contributions"
            }
        
        return {
            'funding_approach': {
                'recommended_approach': recommended_approach,
                'approach_rationale': flexibility_assessment['flexibility_description'],
                'optimized_allocation': optimized_allocation,
                'coverage_metrics': {
                    'monthly_requirement': round(monthly_requirement),
                    'monthly_coverage_percentage': round(monthly_coverage * 100, 1),
                    'total_coverage_percentage': round(total_coverage * 100, 1),
                    'funding_gap': round(funding_gap)
                }
            },
            'implementation_timeline': implementation_timeline,
            'optimization_strategies': optimization_strategies,
            'india_specific_optimizations': india_specific_optimizations,
            'monitoring_framework': {
                'contribution_tracking': "Monthly review of contribution adherence",
                'milestone_tracking': "Progress visualization with milestone markers",
                'adjustment_triggers': ["25% funding achieved", "Income changes", "50% time elapsed"]
            }
        }
    
    def optimize_financial_integration(self, goal_data):
        """
        Optimize how the custom goal integrates with the overall financial plan,
        including tax efficiency and portfolio alignment.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with optimized financial integration strategy
        """
        # Initialize compound strategy if needed
        self._initialize_compound_strategy()
        
        # Get integration assessment
        integration_assessment = self.assess_financial_integration(goal_data)
        
        # Extract key information
        goal_title = goal_data.get('title', 'Custom Goal')
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        tax_bracket = goal_data.get('tax_bracket', 0.3)
        
        # Get goal classification
        classification = self.classify_custom_goal(
            target_amount, time_horizon, goal_data.get('annual_income', 1200000),
            goal_data.get('description', ''), goal_data.get('tags', [])
        )
        
        # Develop tax optimization strategy
        tax_optimization = {}
        
        # Check for available tax efficiency strategies
        tax_efficiency_strategies = integration_assessment['tax_efficiency_strategies']
        
        if tax_efficiency_strategies:
            # Use available strategies from assessment
            tax_optimization = {
                'applicable_strategies': tax_efficiency_strategies,
                'implementation_plan': [{
                    'strategy': strategy['strategy'],
                    'action': f"Implement {strategy['strategy']}",
                    'timeline': "Next 30 days",
                    'potential_benefit': "Tax savings and improved after-tax returns"
                } for strategy in tax_efficiency_strategies],
                'annual_review_checklist': [
                    "Verify qualifying investments meet Section 80C/80G/80D requirements",
                    "Ensure proper documentation for tax filing",
                    "Reassess tax bracket and adjust strategy if needed"
                ]
            }
        else:
            # Generic tax optimization if no specific strategies identified
            tax_optimization = {
                'general_approach': "Standard tax efficiency measures",
                'implementation_plan': [{
                    'strategy': "Tax-efficient investments",
                    'action': "Consider ELSS funds for Section 80C benefits",
                    'timeline': "Before fiscal year end",
                    'potential_benefit': "Potential tax deduction up to ₹1.5 lakh"
                }],
                'annual_review_checklist': [
                    "Review tax law changes that may impact goal funding",
                    "Ensure proper documentation for tax filing",
                    "Reassess tax bracket and adjust strategy if needed"
                ]
            }
        
        # Develop portfolio integration strategy
        portfolio_integration = {}
        
        # Base integration strategy on classification and timeline
        if classification['classification']['wealth_building'] == 'strong':
            # For wealth-building goals, integrate more closely with core portfolio
            portfolio_integration = {
                'integration_approach': "High Integration",
                'integration_rationale': "Wealth-building goal aligns with core portfolio objectives",
                'implementation_steps': [
                    "Use same asset classes and investment vehicles as core portfolio",
                    "Apply consistent rebalancing approach",
                    "Track as integral part of overall financial progress"
                ],
                'separation_level': "Low - minimal separation from core portfolio"
            }
        elif time_horizon < 2:
            # For short-term goals, keep separate
            portfolio_integration = {
                'integration_approach': "Minimal Integration",
                'integration_rationale': "Short-term goal requires separate, conservative approach",
                'implementation_steps': [
                    "Use separate, low-risk investment vehicles",
                    "Track progress independently from core portfolio",
                    "Avoid market volatility exposure"
                ],
                'separation_level': "High - completely separate from core portfolio"
            }
        else:
            # For moderate cases, partial integration
            portfolio_integration = {
                'integration_approach': "Moderate Integration",
                'integration_rationale': "Balance between goal-specific needs and overall portfolio efficiency",
                'implementation_steps': [
                    "Use consistent asset classes but with goal-specific allocation",
                    "Coordinate rebalancing with overall portfolio",
                    "Track separately but review in context of overall plan"
                ],
                'separation_level': "Medium - partially integrated with core portfolio"
            }
        
        # Develop plan synergy strategy
        plan_synergy = {}
        
        # Check for existing plan synergies
        existing_synergies = integration_assessment['plan_synergies']
        
        if existing_synergies:
            # Sort synergies by score
            positive_synergies = [s for s in existing_synergies if s['synergy_score'] > 0]
            negative_synergies = [s for s in existing_synergies if s['synergy_score'] < 0]
            
            synergy_actions = []
            
            # Actions for positive synergies
            for synergy in positive_synergies:
                synergy_actions.append({
                    'plan_type': synergy['plan_type'],
                    'action': f"Leverage synergy with {synergy['plan_type']} plan",
                    'rationale': synergy['synergy_description'],
                    'implementation': "Coordinate timelines and resource allocation"
                })
                
            # Actions for negative synergies (conflicts)
            for synergy in negative_synergies:
                synergy_actions.append({
                    'plan_type': synergy['plan_type'],
                    'action': f"Mitigate conflict with {synergy['plan_type']} plan",
                    'rationale': synergy['synergy_description'],
                    'implementation': "Stagger timelines or create specialized funding approach"
                })
                
            plan_synergy = {
                'synergy_opportunities': positive_synergies,
                'potential_conflicts': negative_synergies,
                'integration_actions': synergy_actions
            }
        else:
            # Generic plan integration if no specific synergies
            plan_synergy = {
                'general_approach': "Standard plan integration",
                'integration_actions': [{
                    'action': "Add to overall financial dashboard",
                    'rationale': "Track progress in context of overall plan",
                    'implementation': "Update financial planning tools and tracking systems"
                }]
            }
        
        # Develop consolidated integration optimization strategy
        integration_optimization = {
            'tax_optimization': tax_optimization,
            'portfolio_integration': portfolio_integration,
            'plan_synergy': plan_synergy,
            'overall_strategy': {
                'integration_level': integration_assessment['integration_level'],
                'integration_focus': "Tax Efficiency" if integration_assessment['integration_scores']['tax_efficiency_potential'] > 0.6 else 
                                  "Portfolio Alignment" if integration_assessment['integration_scores']['portfolio_alignment'] > 0.6 else
                                  "Plan Coordination"
            }
        }
        
        # Indian-specific integration opportunities
        india_specific_integration = integration_assessment['india_specific_integration']
        
        # Add implementation roadmap
        implementation_roadmap = [
            {
                'phase': 'Immediate (0-30 days)',
                'actions': [
                    "Update financial plan to reflect integration strategy",
                    "Implement tax optimization recommendations if applicable",
                    "Align investment selections with integration approach"
                ]
            },
            {
                'phase': 'Short-term (1-3 months)',
                'actions': [
                    "Review overall portfolio allocation with new goal included",
                    "Coordinate with other financial plan components",
                    "Set up integration tracking metrics"
                ]
            },
            {
                'phase': 'Ongoing',
                'actions': [
                    "Review integration effectiveness quarterly",
                    "Adjust integration strategy as goal progresses",
                    "Re-optimize annually or when financial circumstances change"
                ]
            }
        ]
        
        return {
            'integration_metrics': integration_assessment['integration_scores'],
            'integration_optimization': integration_optimization,
            'implementation_roadmap': implementation_roadmap,
            'india_specific_integration': india_specific_integration,
            'monitoring_framework': {
                'integration_metrics': [
                    "Tax efficiency metrics",
                    "Portfolio correlation analysis",
                    "Progress coordination across goals"
                ],
                'review_frequency': "Quarterly",
                'adjustment_triggers': [
                    "Tax law changes",
                    "Major portfolio rebalancing",
                    "Changes to other financial goals"
                ]
            }
        }
    
    def optimize_goal_sustainability(self, goal_data):
        """
        Optimize the long-term sustainability of the custom goal, including
        financial, lifecycle, and where relevant, environmental/social factors.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with optimized sustainability strategy
        """
        # Get sustainability assessment
        sustainability_assessment = self.assess_sustainability_metrics(goal_data)
        
        # Extract key information
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        annual_income = goal_data.get('annual_income', 1200000)
        
        # Determine primary sustainability challenges
        sustainability_metrics = sustainability_assessment['sustainability_metrics']
        
        primary_challenges = []
        
        if sustainability_metrics['income_sustainability'] < 0.5:
            primary_challenges.append("Income Proportion")
        
        if sustainability_metrics['timeline_sustainability'] < 0.5:
            primary_challenges.append("Timeline Feasibility")
        
        if sustainability_metrics['lifecycle_sustainability'] < 0.5:
            primary_challenges.append("Lifecycle Alignment")
        
        # Develop optimization strategies for each challenge
        optimization_strategies = []
        
        if "Income Proportion" in primary_challenges:
            target_adjustment = target_amount * 0.8  # 20% reduction
            
            optimization_strategies.append({
                'challenge': "Income Proportion",
                'strategy': "Goal Amount Adjustment",
                'rationale': "Current goal amount may strain financial resources",
                'implementation_options': [
                    f"Reduce target amount to ₹{round(target_adjustment)}",
                    "Break goal into core (essential) and extended (optional) components",
                    "Identify alternative approaches with lower financial requirements"
                ],
                'expected_impact': {
                    'sustainability_improvement': "+0.2",
                    'goal_outcome_impact': "Moderate - requires scope adjustment"
                }
            })
        
        if "Timeline Feasibility" in primary_challenges:
            extended_timeline = time_horizon * 1.5  # 50% extension
            
            optimization_strategies.append({
                'challenge': "Timeline Feasibility",
                'strategy': "Timeline Extension",
                'rationale': "Current timeline creates unsustainable funding pressure",
                'implementation_options': [
                    f"Extend timeline to {round(extended_timeline, 1)} years",
                    "Create phased achievement approach with milestone targets",
                    "Implement progressive scaling of goal as resources allow"
                ],
                'expected_impact': {
                    'sustainability_improvement': "+0.3",
                    'goal_outcome_impact': "Low - primarily affects timing"
                }
            })
        
        if "Lifecycle Alignment" in primary_challenges:
            # Extract age if available
            age = goal_data.get('age', 30)
            
            # Determine appropriate life stage goals
            if age < 30:
                appropriate_goals = ['education', 'career', 'skills', 'travel', 'home']
            elif age < 45:
                appropriate_goals = ['home', 'family', 'career', 'business', 'education']
            elif age < 60:
                appropriate_goals = ['retirement', 'health', 'education', 'legacy']
            else:
                appropriate_goals = ['health', 'legacy', 'family', 'retirement']
                
            optimization_strategies.append({
                'challenge': "Lifecycle Alignment",
                'strategy': "Goal Reframing",
                'rationale': "Better alignment with current life stage priorities",
                'implementation_options': [
                    f"Reframe goal in context of appropriate life stage priorities: {', '.join(appropriate_goals)}",
                    "Adjust timing to align with natural lifecycle transitions",
                    "Connect goal more explicitly to long-term life planning"
                ],
                'expected_impact': {
                    'sustainability_improvement': "+0.2",
                    'goal_outcome_impact': "Moderate - enhances relevance and commitment"
                }
            })
        
        # ESG sustainability optimizations if relevant
        esg_optimizations = {}
        if sustainability_assessment['esg_relevance']['relevance_score'] > 0.3:
            primary_esg_category = max(
                sustainability_assessment['esg_relevance']['category_matches'], 
                key=lambda k: sustainability_assessment['esg_relevance']['category_matches'][k]
            )
            
            if primary_esg_category == 'environmental':
                esg_optimizations = {
                    'primary_focus': "Environmental Sustainability",
                    'integration_strategy': "Green Investment Alignment",
                    'implementation_options': [
                        "Direct portion of funding to green/sustainable investments",
                        "Track environmental impact metrics alongside financial progress",
                        "Consider certified green options when implementing goal"
                    ]
                }
            elif primary_esg_category == 'social':
                esg_optimizations = {
                    'primary_focus': "Social Impact",
                    'integration_strategy': "Social Value Integration",
                    'implementation_options': [
                        "Incorporate community benefit component into goal",
                        "Partner with socially-focused organizations",
                        "Structure goal to create broader social value"
                    ]
                }
            elif primary_esg_category == 'ethical':
                esg_optimizations = {
                    'primary_focus': "Ethical Alignment",
                    'integration_strategy': "Values-Based Approach",
                    'implementation_options': [
                        "Ensure goal implementation aligns with ethical values",
                        "Use ethical investment vehicles for funding",
                        "Build transparency and integrity into goal structure"
                    ]
                }
        
        # Indian-specific sustainability considerations
        india_specific_considerations = sustainability_assessment['india_specific_considerations']
        
        # Add family/intergenerational aspects (culturally important)
        india_specific_sustainability = {
            **india_specific_considerations,
            'family_considerations': {
                'intergenerational_support': "Consider how goal strengthens family across generations",
                'family_resource_preservation': "Balance individual goals with family resource preservation",
                'cultural_continuation': "Incorporate elements of cultural preservation where relevant"
            }
        }
        
        # Develop implementation roadmap
        implementation_roadmap = []
        
        # Add immediate steps based on primary challenges
        immediate_actions = []
        
        if "Income Proportion" in primary_challenges:
            immediate_actions.append("Reassess goal scope and revise target amount")
        
        if "Timeline Feasibility" in primary_challenges:
            immediate_actions.append("Revise timeline and create phased approach")
        
        if "Lifecycle Alignment" in primary_challenges:
            immediate_actions.append("Reframe goal in context of life stage priorities")
            
        if not immediate_actions:
            immediate_actions = ["Document sustainability assessment and monitoring approach"]
        
        implementation_roadmap.append({
            'phase': 'Immediate (0-30 days)',
            'actions': immediate_actions
        })
        
        # Add short-term steps
        implementation_roadmap.append({
            'phase': 'Short-term (1-3 months)',
            'actions': [
                "Implement revised funding approach based on optimizations",
                "Update goal tracking system to monitor sustainability metrics",
                "Communicate changes to relevant stakeholders"
            ]
        })
        
        # Add ongoing steps
        implementation_roadmap.append({
            'phase': 'Ongoing',
            'actions': [
                "Review sustainability metrics quarterly",
                "Adjust approach as financial circumstances evolve",
                "Re-optimize annually or when sustainability metrics decline"
            ]
        })
        
        return {
            'sustainability_metrics': sustainability_metrics,
            'primary_challenges': primary_challenges,
            'optimization_strategies': optimization_strategies,
            'esg_optimizations': esg_optimizations,
            'india_specific_sustainability': india_specific_sustainability,
            'implementation_roadmap': implementation_roadmap,
            'monitoring_framework': {
                'sustainability_metrics': [
                    "Income-to-goal ratio",
                    "Funding pressure metrics",
                    "Lifecycle alignment indicators",
                    "ESG impact measures (if applicable)"
                ],
                'review_frequency': "Quarterly",
                'adjustment_triggers': [
                    "Financial capacity changes",
                    "Life stage transitions",
                    "Significant goal progress milestones"
                ]
            }
        }
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive custom goal funding strategy with enhanced optimization.
        
        Args:
            goal_data: Dictionary with custom goal details
            
        Returns:
            Dictionary with comprehensive custom goal strategy
        """
        # Initialize all components
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # Extract custom goal specific information
        goal_title = goal_data.get('title', 'Custom Goal')
        goal_description = goal_data.get('description', '')
        goal_tags = goal_data.get('tags', [])
        target_amount = goal_data.get('target_amount', 100000)
        time_horizon = goal_data.get('time_horizon', 3)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        annual_income = goal_data.get('annual_income', 1200000)
        monthly_capacity = goal_data.get('monthly_capacity', monthly_contribution or annual_income * 0.1 / 12)
        
        # Create goal data for base funding strategy
        custom_goal = {
            'goal_type': 'custom',
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution
        }
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(custom_goal)
        
        # Enhanced with constraint assessments
        classification_assessment = self.assess_goal_classification_confidence(goal_data)
        flexibility_assessment = self.assess_funding_flexibility(goal_data)
        integration_assessment = self.assess_financial_integration(goal_data)
        sustainability_assessment = self.assess_sustainability_metrics(goal_data)
        
        # Enhanced with optimization strategies
        if classification_assessment['threshold_met']:
            # Only optimize if classification confidence meets threshold
            classification_optimization = self.optimize_goal_classification(goal_data)
            funding_optimization = self.optimize_funding_approach(goal_data)
            integration_optimization = self.optimize_financial_integration(goal_data)
            sustainability_optimization = self.optimize_goal_sustainability(goal_data)
        else:
            # If classification confidence too low, skip optimization
            classification_optimization = {
                'status': 'Deferred',
                'reason': 'Classification confidence below threshold',
                'necessary_action': 'Improve goal definition clarity'
            }
            funding_optimization = {
                'status': 'Deferred',
                'reason': 'Classification confidence below threshold',
                'necessary_action': 'Improve goal definition clarity'
            }
            integration_optimization = {
                'status': 'Deferred',
                'reason': 'Classification confidence below threshold',
                'necessary_action': 'Improve goal definition clarity'
            }
            sustainability_optimization = {
                'status': 'Deferred',
                'reason': 'Classification confidence below threshold',
                'necessary_action': 'Improve goal definition clarity'
            }
        
        # Traditional custom goal analyses
        
        # Classify the custom goal
        goal_classification = self.classify_custom_goal(
            target_amount, time_horizon, annual_income, goal_description, goal_tags
        )
        
        # Customize allocation based on classification
        base_template = goal_classification['recommended_approach']['allocation_template']
        allocation = self.customize_allocation_model(
            base_template, time_horizon, risk_profile, goal_classification['priority_score']
        )
        
        # Design custom funding plan
        funding_plan = self.design_custom_funding_plan(
            target_amount, time_horizon, current_savings, monthly_capacity, allocation
        )
        
        # Generate additional insights
        goal_insights = self.generate_custom_goal_insights(
            goal_description, goal_tags, target_amount, time_horizon
        )
        
        # Combine into comprehensive strategy
        strategy = {
            **base_strategy,  # Include base strategy components
            'goal_details': {
                'title': goal_title,
                'description': goal_description,
                'tags': goal_tags,
                'target_amount': target_amount,
                'time_horizon': time_horizon
            },
            'custom_goal_classification': goal_classification,
            'custom_allocation': allocation,
            'custom_funding_plan': funding_plan,
            'custom_goal_insights': goal_insights,
            'constraint_assessments': {
                'classification_confidence': classification_assessment,
                'funding_flexibility': flexibility_assessment,
                'financial_integration': integration_assessment,
                'sustainability_metrics': sustainability_assessment
            },
            'optimization_strategies': {
                'classification_optimization': classification_optimization,
                'funding_optimization': funding_optimization,
                'integration_optimization': integration_optimization,
                'sustainability_optimization': sustainability_optimization
            }
        }
        
        # Add India-specific guidance
        strategy['india_specific_guidance'] = {
            'cultural_context': {
                'family_implications': "Consider goal within joint family financial context",
                'cultural_significance': "Recognize cultural dimensions of financial goals",
                'ceremonial_timing': "Align with auspicious dates for major financial decisions"
            },
            'tax_optimization': {
                'section_80c_integration': "Consider Section 80C investments for dual-purpose goal funding",
                'progressive_approach': "Align goal funding with progressive tax thresholds",
                'documentation_requirements': "Maintain proper documentation for tax benefits"
            },
            'investment_approach': {
                'traditional_vehicles': "Consider traditional investment vehicles like gold and real estate",
                'emerging_options': "Explore digital options aligned with financial inclusion initiatives",
                'regulatory_considerations': "Navigate regulatory frameworks specific to Indian context"
            }
        }
        
        # Add implementation roadmap
        strategy['implementation_roadmap'] = {
            'immediate_actions': [
                "Establish goal tracking mechanism",
                "Set up funding structure based on recommended approach",
                "Implement highest priority optimization strategies"
            ],
            'short_term_actions': [
                "Complete initial optimization implementations",
                "Establish monitoring framework for tracking progress",
                "Schedule first review point at 3 months"
            ],
            'ongoing_monitoring': {
                'monthly_check': "Track contribution adherence and basic progress metrics",
                'quarterly_review': "Conduct comprehensive review of goal progress and strategy effectiveness",
                'annual_reassessment': "Completely reassess goal strategy and optimizations"
            }
        }
        
        # Add custom goal specific advice
        strategy['specific_advice'] = {
            'funding_approach': [
                f"Use {goal_classification['recommended_approach']['funding_method']} funding approach",
                f"Follow {base_template.replace('_', ' ')} allocation with adjustments for your specific situation",
                "Review and adjust strategy every six months or when financial situation changes",
                "Connect custom goal to broader financial objectives for better integration"
            ],
            'maximizing_success': [
                "Clearly define what goal completion looks like with specific metrics",
                "Create visual tracking system to maintain motivation",
                "Build in celebration points at 25%, 50%, and 75% milestones",
                "Share goal with accountability partner if appropriate"
            ]
        }
        
        # Integrate rebalancing strategy if profile data is available
        if 'profile_data' in goal_data:
            rebalancing_strategy = self.integrate_rebalancing_strategy(goal_data, goal_data['profile_data'])
            strategy['rebalancing_strategy'] = rebalancing_strategy
        
        return strategy