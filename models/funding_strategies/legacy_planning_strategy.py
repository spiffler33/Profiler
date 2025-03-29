import logging
import math
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class LegacyPlanningStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for legacy planning goals including
    estate planning, charitable giving, and inheritance planning with
    India-specific legal and tax considerations.
    """
    
    def __init__(self):
        """Initialize with legacy planning specific parameters"""
        super().__init__()
        
        # Optimizer, constraints, and compound strategy objects will be lazy initialized
        self.optimizer = None
        self.constraints = None
        self.compound_strategy = None
        
        # Additional legacy planning specific parameters
        self.legacy_params = {
            "estate_planning_options": {
                "will": {
                    "importance": "essential",
                    "typical_cost": 20000,  # Basic will preparation cost
                    "requirements": [
                        "Inventory of assets and liabilities",
                        "Beneficiary designations",
                        "Executor appointment",
                        "Guardian nominations (if applicable)"
                    ],
                    "update_frequency": "Every 3-5 years or after major life events"
                },
                "trust": {
                    "importance": "recommended",
                    "types": {
                        "revocable": {
                            "typical_cost": 50000,
                            "benefits": [
                                "Avoids probate",
                                "Maintains privacy",
                                "Allows for changes during lifetime"
                            ]
                        },
                        "irrevocable": {
                            "typical_cost": 75000,
                            "benefits": [
                                "Potential tax benefits",
                                "Asset protection",
                                "Fixed terms not changeable"
                            ]
                        }
                    }
                },
                "power_of_attorney": {
                    "importance": "essential",
                    "types": ["Financial", "Healthcare"],
                    "typical_cost": 15000,
                    "update_frequency": "Every 3-5 years"
                }
            },
            "charitable_giving_options": {
                "direct_donation": {
                    "tax_benefit": "Section 80G deductions (50-100% depending on organization)",
                    "minimum": 500
                },
                "charitable_trust": {
                    "setup_cost": 100000,
                    "minimum_corpus": 1000000,
                    "benefits": [
                        "Long-term giving strategy",
                        "Family involvement",
                        "Defined charitable purpose"
                    ],
                    "tax_benefit": "Section 80G deductions"
                },
                "endowment": {
                    "minimum": 500000,
                    "benefits": [
                        "Perpetual impact",
                        "Named recognition possible",
                        "Specific purpose funding"
                    ]
                }
            },
            "wealth_transfer_options": {
                "gift": {
                    "annual_limit": 250000,  # Approximate limit for tax-free gifts
                    "documentation": "Gift deed recommended for substantial amounts"
                },
                "inheritance_planning": {
                    "hindu_succession_act": "Governs inheritance for Hindus",
                    "indian_succession_act": "Governs inheritance for other religions",
                    "muslim_personal_law": "Governs inheritance for Muslims"
                },
                "property_transfer": {
                    "methods": ["Will", "Gift", "Sale", "Trust"],
                    "considerations": [
                        "Stamp duty implications",
                        "Tax implications",
                        "Clear title transfer"
                    ]
                }
            },
            "tax_considerations": {
                "estate_planning": {
                    "india": "No inheritance tax currently in India",
                    "nri": "May have tax implications in country of residence"
                },
                "charitable_giving": {
                    "section_80g": {
                        "limit": "10% of gross total income",
                        "deduction": "50-100% depending on organization"
                    },
                    "section_35": {
                        "description": "Scientific research donations",
                        "deduction": "100-175% depending on organization"
                    }
                }
            }
        }
        
        # Legacy optimization parameters
        self.legacy_optimization_params = {
            'tax_efficiency_weight': 0.4,       # Weight for tax efficiency optimization
            'family_needs_weight': 0.3,         # Weight for family needs consideration
            'charitable_impact_weight': 0.2,    # Weight for charitable impact optimization
            'administrative_ease_weight': 0.1,  # Weight for ease of administration
            'liquidity_threshold': 0.15,        # Minimum liquidity ratio for estate (15%)
            'diversification_factor': 0.2,      # Diversification factor for legacy assets
            'rebalancing_frequency': 12,        # Monthly frequency for legacy allocation reviews
            'regional_cultural_factor': 0.25    # Weight for regional/cultural considerations in India
        }
        
        # Load legacy planning specific parameters
        self._load_legacy_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with legacy-specific optimization parameters
            super()._initialize_optimizer()
            
            # Set legacy-specific optimization parameters if needed
            # These would be implemented and used in actual optimizer class
            if hasattr(self.optimizer, 'set_parameters'):
                self.optimizer.set_parameters({
                    'tax_efficiency_weight': self.legacy_optimization_params['tax_efficiency_weight'],
                    'charitable_impact_weight': self.legacy_optimization_params['charitable_impact_weight'],
                    'family_needs_weight': self.legacy_optimization_params['family_needs_weight'],
                    'diversification_factor': self.legacy_optimization_params['diversification_factor']
                })
    
    def _initialize_constraints(self):
        """Initialize the funding constraints with lazy loading pattern"""
        if not hasattr(self, 'constraints') or self.constraints is None:
            # Initialize base constraints
            super()._initialize_constraints()
            
            # Set legacy-specific constraint parameters if needed
            # These would be implemented and used in actual constraint class
            if hasattr(self.constraints, 'register_constraint'):
                # Register minimum liquidity constraint for estate planning
                self.constraints.register_constraint(
                    'minimum_liquidity', 
                    self.legacy_optimization_params['liquidity_threshold']
                )
                
                # Register minimum diversification constraint
                self.constraints.register_constraint(
                    'diversification_requirement',
                    self.legacy_optimization_params['diversification_factor']
                )
    
    def _initialize_compound_strategy(self):
        """Initialize the compound strategy with lazy loading pattern"""
        if not hasattr(self, 'compound_strategy') or self.compound_strategy is None:
            # Initialize base compound strategy
            super()._initialize_compound_strategy()
            
            # Register legacy-specific strategies if compound strategy supports it
            if hasattr(self.compound_strategy, 'register_strategy'):
                # Register different strategies based on legacy planning components
                self.compound_strategy.register_strategy(
                    'estate_planning', 'conservative_capital_preservation'
                )
                
                self.compound_strategy.register_strategy(
                    'charitable_giving', 'tax_efficient_giving'
                )
                
                self.compound_strategy.register_strategy(
                    'wealth_transfer', 'multi_generational_growth'
                )
        
    def _load_legacy_parameters(self):
        """Load legacy planning specific parameters from service"""
        if self.param_service:
            try:
                # Load estate planning options
                estate_planning = self.param_service.get_parameter('estate_planning_options')
                if estate_planning:
                    self.legacy_params['estate_planning_options'].update(estate_planning)
                
                # Load charitable giving options
                charitable_giving = self.param_service.get_parameter('charitable_giving_options')
                if charitable_giving:
                    self.legacy_params['charitable_giving_options'].update(charitable_giving)
                
                # Load wealth transfer options
                wealth_transfer = self.param_service.get_parameter('wealth_transfer_options')
                if wealth_transfer:
                    self.legacy_params['wealth_transfer_options'].update(wealth_transfer)
                
                # Load tax considerations
                tax_considerations = self.param_service.get_parameter('legacy_tax_considerations')
                if tax_considerations:
                    self.legacy_params['tax_considerations'].update(tax_considerations)
                
            except Exception as e:
                logger.error(f"Error loading legacy planning parameters: {e}")
                # Continue with default parameters
    
    def estimate_estate_planning_cost(self, estate_value: float, estate_complexity: str = "moderate", 
                                    family_complexity: str = "simple") -> float:
        """
        Estimate estate planning costs based on estate value and complexity.
        
        Args:
            estate_value: Estimated total estate value
            estate_complexity: 'simple', 'moderate', or 'complex'
            family_complexity: 'simple', 'moderate', or 'complex'
            
        Returns:
            Estimated total estate planning cost
        """
        # Base will cost
        will_cost = self.legacy_params['estate_planning_options']['will']['typical_cost']
        
        # Adjustments for estate value
        if estate_value < 5000000:  # 50L
            value_factor = 1.0
        elif estate_value < 20000000:  # 2Cr
            value_factor = 1.5
        elif estate_value < 50000000:  # 5Cr
            value_factor = 2.0
        else:
            value_factor = 3.0
            
        # Adjustments for estate complexity
        complexity_factors = {
            "simple": 1.0,
            "moderate": 1.5,
            "complex": 2.5
        }
        estate_factor = complexity_factors.get(estate_complexity.lower(), 1.5)
        
        # Adjustments for family complexity
        family_factors = {
            "simple": 1.0,  # Single, no children
            "moderate": 1.3,  # Married with children
            "complex": 2.0  # Blended family, multiple marriages, etc.
        }
        family_factor = family_factors.get(family_complexity.lower(), 1.3)
        
        # Calculate total will cost
        adjusted_will_cost = will_cost * value_factor * estate_factor * family_factor
        
        # Add power of attorney costs
        poa_cost = self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost']
        
        # Consider if trust is needed based on complexity and value
        trust_cost = 0
        if ((estate_complexity == "complex" or family_complexity == "complex") 
                or estate_value > 20000000):  # 2Cr
            # Decide between revocable and irrevocable trust
            if estate_value > 50000000:  # 5Cr - consider irrevocable for larger estates
                trust_cost = self.legacy_params['estate_planning_options']['trust']['types']['irrevocable']['typical_cost']
            else:
                trust_cost = self.legacy_params['estate_planning_options']['trust']['types']['revocable']['typical_cost']
                
        total_cost = adjusted_will_cost + poa_cost + trust_cost
        
        return total_cost
    
    def analyze_charitable_giving_options(self, annual_income: float, charitable_goal: float,
                                        time_horizon: int, tax_bracket: float = 0.3) -> Dict[str, Any]:
        """
        Analyze charitable giving options and their tax implications.
        
        Args:
            annual_income: Annual income
            charitable_goal: Target charitable giving amount
            time_horizon: Years to achieve charitable goal
            tax_bracket: Income tax bracket as decimal
            
        Returns:
            Dictionary with charitable giving analysis
        """
        # Calculate maximum tax-advantaged annual giving (10% of income)
        max_annual_deduction = annual_income * 0.1
        
        # Calculate annual giving amount to meet goal
        annual_giving = charitable_goal / time_horizon if time_horizon > 0 else charitable_goal
        
        # Determine if goal can be fully tax-advantaged
        tax_advantaged_amount = min(annual_giving, max_annual_deduction)
        non_advantaged_amount = max(0, annual_giving - tax_advantaged_amount)
        
        # Calculate tax savings
        tax_savings = tax_advantaged_amount * tax_bracket
        
        # Recommend appropriate giving vehicle
        if charitable_goal > 1000000 and time_horizon > 5:
            # Large goal over long time - consider charitable trust
            recommended_vehicle = "Charitable Trust"
            vehicle_details = self.legacy_params['charitable_giving_options']['charitable_trust']
            
            setup_cost = vehicle_details['setup_cost']
            benefits = vehicle_details['benefits']
            
            # Calculate effective annual cost (accounting for tax benefits)
            effective_annual_cost = annual_giving - tax_savings
            
            # First year includes setup cost
            first_year_cost = effective_annual_cost + setup_cost
            
        elif charitable_goal > 500000 and time_horizon > 3:
            # Medium-large goal - consider endowment
            recommended_vehicle = "Endowment"
            vehicle_details = self.legacy_params['charitable_giving_options']['endowment']
            
            # Minimum required
            minimum = vehicle_details['minimum']
            benefits = vehicle_details['benefits']
            
            # Calculate effective annual cost (accounting for tax benefits)
            effective_annual_cost = annual_giving - tax_savings
            
            # No significant setup costs
            first_year_cost = effective_annual_cost
            
        else:
            # Smaller goal or shorter timeframe - direct donation
            recommended_vehicle = "Direct Donation"
            vehicle_details = self.legacy_params['charitable_giving_options']['direct_donation']
            
            # Minimum donation
            minimum = vehicle_details['minimum']
            tax_benefit = vehicle_details['tax_benefit']
            
            # Calculate effective annual cost (accounting for tax benefits)
            effective_annual_cost = annual_giving - tax_savings
            
            # No setup costs
            first_year_cost = effective_annual_cost
            
        return {
            'charitable_goal': round(charitable_goal),
            'time_horizon': time_horizon,
            'annual_giving_target': round(annual_giving),
            'tax_analysis': {
                'tax_bracket': f"{tax_bracket*100}%",
                'max_annual_deduction': round(max_annual_deduction),
                'tax_advantaged_amount': round(tax_advantaged_amount),
                'non_advantaged_amount': round(non_advantaged_amount),
                'estimated_annual_tax_savings': round(tax_savings)
            },
            'recommended_vehicle': {
                'type': recommended_vehicle,
                'details': vehicle_details,
                'effective_annual_cost': round(effective_annual_cost),
                'first_year_cost': round(first_year_cost)
            },
            'implementation_steps': [
                "Research qualified charitable organizations (look for 80G registration)",
                "Plan consistent giving schedule (monthly/quarterly/annual)",
                "Maintain proper documentation for tax purposes",
                f"Consider increasing giving as income grows ({round(annual_income*0.01)} per year)"
            ]
        }
    
    def create_inheritance_planning_framework(self, estate_value: float, beneficiaries: List[Dict[str, Any]],
                                           estate_components: Dict[str, float]) -> Dict[str, Any]:
        """
        Create inheritance planning framework with recommended distribution approach.
        
        Args:
            estate_value: Total estate value
            beneficiaries: List of beneficiary dictionaries with relationship and other details
            estate_components: Dictionary of estate components and their values
            
        Returns:
            Dictionary with inheritance planning framework
        """
        # Analyze beneficiary composition
        spouse_exists = any(b.get('relationship', '').lower() == 'spouse' for b in beneficiaries)
        child_count = sum(1 for b in beneficiaries if b.get('relationship', '').lower() in ['son', 'daughter', 'child'])
        other_dependents = sum(1 for b in beneficiaries 
                             if b.get('relationship', '').lower() in ['parent', 'sibling'] 
                             and b.get('dependent', False))
        
        # Analyze estate composition
        liquid_assets = estate_components.get('liquid_assets', 0)
        property_assets = estate_components.get('property', 0)
        investment_assets = estate_components.get('investments', 0)
        business_assets = estate_components.get('business', 0)
        
        # Calculate liquidity ratio (important for estate planning)
        liquidity_ratio = liquid_assets / estate_value if estate_value > 0 else 0
        
        # Determine necessary legal instruments
        required_instruments = ["Will"]
        
        if business_assets > 0:
            required_instruments.append("Business Succession Plan")
            
        if property_assets > 0 and (spouse_exists or child_count > 1):
            required_instruments.append("Property Succession Documentation")
            
        if estate_value > 20000000 or child_count > 1 or business_assets > 0:
            required_instruments.append("Trust")
            
        required_instruments.append("Power of Attorney (Financial)")
        required_instruments.append("Power of Attorney (Healthcare)")
        
        # Generate distribution recommendations
        distribution_recommendations = []
        
        # Handle spouse
        if spouse_exists:
            distribution_recommendations.append({
                'beneficiary_type': 'Spouse',
                'recommended_approach': 'Primary beneficiary for immediate assets',
                'considerations': [
                    "Consider spousal trust for protection",
                    "Ensure housing security",
                    "Balance immediate needs vs. long-term inheritance plan"
                ]
            })
            
        # Handle children
        if child_count > 0:
            if child_count == 1:
                distribution_recommendations.append({
                    'beneficiary_type': 'Child',
                    'recommended_approach': 'Direct inheritance with potential trust protection',
                    'considerations': [
                        "Consider age-based distribution milestones",
                        "Balance inheritance with spouse's needs",
                        "Consider education and life stage"
                    ]
                })
            else:
                distribution_recommendations.append({
                    'beneficiary_type': 'Multiple Children',
                    'recommended_approach': 'Equal distribution with specific bequests as appropriate',
                    'considerations': [
                        "Consider individual needs and circumstances",
                        "Balance equality with specific circumstances",
                        "Document reasons for any unequal distributions"
                    ]
                })
                
        # Handle other dependents
        if other_dependents > 0:
            distribution_recommendations.append({
                'beneficiary_type': 'Other Dependents',
                'recommended_approach': 'Provision for ongoing support if needed',
                'considerations': [
                    "Consider ongoing financial needs",
                    "Balance with primary beneficiary needs",
                    "Consider trust structure for long-term care"
                ]
            })
            
        # Handle business assets
        if business_assets > 0:
            distribution_recommendations.append({
                'beneficiary_type': 'Business Interest',
                'recommended_approach': 'Dedicated succession plan with clear ownership transfer',
                'considerations': [
                    "Consider capabilities of heirs",
                    "Consider buy-sell agreements",
                    "Balance business continuity with family needs"
                ]
            })
            
        # Recommend additional liquidity planning if needed
        liquidity_planning = None
        if liquidity_ratio < 0.2:
            liquidity_planning = {
                'recommendation': 'Improve estate liquidity',
                'current_liquidity': f"{round(liquidity_ratio*100)}%",
                'target_liquidity': "20-30%",
                'strategies': [
                    "Consider life insurance as an estate planning tool",
                    "Maintain dedicated liquid assets for estate expenses",
                    "Plan for potential property sale costs and taxes"
                ]
            }
            
        return {
            'estate_value': round(estate_value),
            'beneficiary_composition': {
                'spouse_exists': spouse_exists,
                'child_count': child_count,
                'other_dependents': other_dependents
            },
            'estate_composition': {
                'liquid_assets': round(liquid_assets),
                'property_assets': round(property_assets),
                'investment_assets': round(investment_assets),
                'business_assets': round(business_assets),
                'liquidity_ratio': round(liquidity_ratio*100, 1)
            },
            'required_legal_instruments': required_instruments,
            'distribution_recommendations': distribution_recommendations,
            'liquidity_planning': liquidity_planning,
            'implementation_timeline': [
                {
                    'timeframe': 'Immediate (0-3 months)',
                    'actions': [
                        "Create inventory of assets and liabilities",
                        "Identify beneficiaries and outline distribution wishes",
                        "Consult with legal professional specializing in estate planning"
                    ]
                },
                {
                    'timeframe': 'Near-term (3-6 months)',
                    'actions': [
                        "Draft and execute will",
                        "Create power of attorney documents",
                        "Update beneficiary designations on financial accounts"
                    ]
                },
                {
                    'timeframe': 'Medium-term (6-12 months)',
                    'actions': [
                        "Implement trust structures if applicable",
                        "Develop business succession plan if applicable",
                        "Review and optimize estate liquidity"
                    ]
                },
                {
                    'timeframe': 'Ongoing',
                    'actions': [
                        "Review plan every 3-5 years or after major life events",
                        "Update asset inventory annually",
                        "Communicate plan to key family members/executors"
                    ]
                }
            ]
        }
    
    def analyze_legacy_planning_allocations(self, total_assets: float, age: int, 
                                         family_status: str) -> Dict[str, Any]:
        """
        Analyze and recommend allocation of assets for legacy planning.
        
        Args:
            total_assets: Total assets for potential legacy planning
            age: Current age of the individual
            family_status: Family status (single, married, children, etc.)
            
        Returns:
            Dictionary with recommended legacy planning allocations
        """
        # Determine life stage based on age
        if age < 40:
            life_stage = "early"
        elif age < 60:
            life_stage = "mid"
        else:
            life_stage = "late"
            
        # Baseline allocation percentages
        allocation = {
            'estate_planning': 0.05,  # 5% to estate planning costs
            'charitable_giving': 0.05,  # 5% to charitable giving
            'wealth_transfer': 0.10,  # 10% to immediate wealth transfer
            'personal_use': 0.80  # 80% for personal use during lifetime
        }
        
        # Adjust based on life stage
        if life_stage == "early":
            # Early stage - focus more on personal use
            allocation['estate_planning'] = 0.03
            allocation['charitable_giving'] = 0.02
            allocation['wealth_transfer'] = 0.05
            allocation['personal_use'] = 0.90
        elif life_stage == "late":
            # Late stage - focus more on legacy planning
            allocation['estate_planning'] = 0.07
            allocation['charitable_giving'] = 0.10
            allocation['wealth_transfer'] = 0.23
            allocation['personal_use'] = 0.60
            
        # Adjust based on family status
        if family_status.lower() in ['single', 'unmarried']:
            # Single individuals might focus more on charitable giving
            allocation['charitable_giving'] += 0.05
            allocation['wealth_transfer'] -= 0.05
        elif family_status.lower() in ['married with children', 'children']:
            # Those with children might focus more on wealth transfer
            allocation['charitable_giving'] -= 0.02
            allocation['wealth_transfer'] += 0.07
            allocation['personal_use'] -= 0.05
            
        # Adjust if assets are very large (over 5 crores)
        if total_assets > 50000000:
            allocation['charitable_giving'] += 0.05
            allocation['personal_use'] -= 0.05
            
        # Calculate absolute amounts
        allocation_amounts = {}
        for category, percentage in allocation.items():
            allocation_amounts[category] = total_assets * percentage
            
        # Create specific recommendations based on allocations
        estate_planning_recommendation = {
            'allocation': round(allocation['estate_planning'] * 100, 1),
            'amount': round(allocation_amounts['estate_planning']),
            'recommendation': "Invest in comprehensive estate planning",
            'specific_actions': [
                "Create or update will and trust documents",
                "Establish powers of attorney and advance directives",
                "Review and optimize asset titling for estate purposes",
                "Consider tax-efficient wealth transfer strategies"
            ]
        }
        
        charitable_recommendation = {
            'allocation': round(allocation['charitable_giving'] * 100, 1),
            'amount': round(allocation_amounts['charitable_giving']),
            'recommendation': "Establish strategic charitable giving plan",
            'specific_actions': [
                "Identify causes aligned with personal values",
                "Consider structured giving vehicles for larger amounts",
                "Maximize tax efficiency of charitable contributions",
                "Consider legacy gifts and endowments"
            ]
        }
        
        wealth_transfer_recommendation = {
            'allocation': round(allocation['wealth_transfer'] * 100, 1),
            'amount': round(allocation_amounts['wealth_transfer']),
            'recommendation': "Implement strategic wealth transfer plan",
            'specific_actions': [
                "Make use of annual gift tax exemptions",
                "Consider education funding for next generation",
                "Evaluate trust structures for controlled wealth transfer",
                "Review beneficiary designations on all accounts"
            ]
        }
        
        personal_recommendation = {
            'allocation': round(allocation['personal_use'] * 100, 1),
            'amount': round(allocation_amounts['personal_use']),
            'recommendation': "Balance current needs with legacy objectives",
            'specific_actions': [
                "Ensure retirement needs are fully funded first",
                "Consider long-term care planning",
                "Maintain sufficient reserves for personal goals",
                "Gradually increase legacy planning as financial security grows"
            ]
        }
        
        return {
            'total_assets': round(total_assets),
            'age': age,
            'life_stage': life_stage,
            'family_status': family_status,
            'allocation_percentages': {k: round(v * 100, 1) for k, v in allocation.items()},
            'allocation_amounts': {k: round(v) for k, v in allocation_amounts.items()},
            'recommendations': {
                'estate_planning': estate_planning_recommendation,
                'charitable_giving': charitable_recommendation,
                'wealth_transfer': wealth_transfer_recommendation,
                'personal_use': personal_recommendation
            },
            'implementation_approach': "Gradual implementation with annual review and adjustment"
        }
    
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy for legacy planning goals with focus on
        long-term stability, tax efficiency, and gradual risk reduction.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            profile_data: Optional dictionary with profile details
            
        Returns:
            Dictionary with rebalancing strategy tailored for legacy planning
        """
        # Create rebalancing strategy instance
        rebalancing = RebalancingStrategy()
        
        # Extract legacy planning specific information
        goal_type = goal_data.get('goal_type', 'estate_planning').lower()
        target_amount = goal_data.get('target_amount')
        time_horizon = goal_data.get('time_horizon', 15)  # Legacy planning often has long horizons
        age = goal_data.get('age', 50)
        total_assets = goal_data.get('total_assets', 10000000)
        
        # Create minimal profile if not provided
        if not profile_data:
            profile_data = {
                'risk_profile': 'moderate_conservative',  # Default for legacy planning
                'portfolio_value': total_assets * 0.3,    # Assume 30% of assets for legacy
                'age': age,
                'market_volatility': 'normal'
            }
        
        # Get default allocation based on legacy planning type
        if goal_type == 'charitable_giving':
            # For charitable giving, use a balanced approach with some growth
            default_allocation = {
                'equity': 0.40,        # 40% equity for growth
                'debt': 0.40,          # 40% debt for stability
                'gold': 0.05,          # 5% gold for diversification
                'alternatives': 0.10,  # 10% alternatives (could include impact investments)
                'cash': 0.05           # 5% cash for liquidity
            }
        elif goal_type in ('estate_planning', 'inheritance'):
            # For estate planning, more conservative approach
            default_allocation = {
                'equity': 0.30,        # 30% equity for modest growth
                'debt': 0.45,          # 45% debt for stability
                'gold': 0.10,          # 10% gold for wealth preservation (important in India)
                'alternatives': 0.05,  # 5% alternatives
                'cash': 0.10           # 10% cash for estate liquidity needs
            }
        else:  # wealth_transfer or other
            # For wealth transfer, longer-term balanced approach
            default_allocation = {
                'equity': 0.35,        # 35% equity for growth
                'debt': 0.40,          # 40% debt for stability
                'gold': 0.10,          # 10% gold (cultural significance in Indian wealth transfer)
                'alternatives': 0.10,  # 10% alternatives (may include family business interests)
                'cash': 0.05           # 5% cash for liquidity
            }
        
        # Extract any existing allocation from goal data
        allocation = goal_data.get('investment_allocation', default_allocation)
        
        # Create rebalancing goal with legacy planning focus
        rebalancing_goal = {
            'goal_type': goal_type,
            'time_horizon': time_horizon,
            'target_allocation': allocation,
            'target_amount': target_amount,
            'profile_data': profile_data
        }
        
        # Design rebalancing schedule specific to legacy planning
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(rebalancing_goal, profile_data)
        
        # Calculate age-based and purpose-based threshold factors
        threshold_factors = {}
        
        # Adjust thresholds based on age and life stage
        if age < 50:
            # Younger individuals can have slightly wider thresholds
            age_based_factors = {
                'equity': 1.2,         # 20% wider for equity
                'debt': 1.1,           # 10% wider for debt
                'gold': 1.1,           # 10% wider for gold
                'alternatives': 1.2,   # 20% wider for alternatives
                'cash': 1.0            # Standard for cash
            }
        elif age < 65:
            # Middle-aged with standard thresholds
            age_based_factors = {
                'equity': 1.0,         # Standard thresholds
                'debt': 1.0,
                'gold': 1.0,
                'alternatives': 1.0,
                'cash': 1.0
            }
        else:
            # Older individuals need tighter thresholds
            age_based_factors = {
                'equity': 0.8,         # 20% tighter for equity
                'debt': 0.9,           # 10% tighter for debt
                'gold': 0.9,           # 10% tighter for gold
                'alternatives': 0.8,   # 20% tighter for alternatives
                'cash': 1.0            # Standard for cash (liquidity important for estate)
            }
        
        # Further adjust based on legacy planning goal type
        if goal_type == 'charitable_giving':
            # For charitable giving, tax efficiency and steady growth are priorities
            purpose_factors = {
                'equity': 1.1,         # Slightly wider for equity to allow growth
                'debt': 1.0,           # Standard for debt
                'gold': 0.9,           # Tighter for gold (less relevant for charitable goals)
                'alternatives': 1.1,   # Wider for alternatives (may include impact investments)
                'cash': 0.8            # Tighter for cash (optimize for tax-efficient giving)
            }
        elif goal_type in ('estate_planning', 'inheritance'):
            # For estate planning, stability and liquidity are priorities
            purpose_factors = {
                'equity': 0.9,         # Tighter for equity (stability priority)
                'debt': 1.0,           # Standard for debt
                'gold': 1.1,           # Wider for gold (wealth preservation)
                'alternatives': 0.9,   # Tighter for alternatives (stability priority)
                'cash': 1.2            # Wider for cash (liquidity for estate needs)
            }
        else:  # wealth_transfer or other
            # For wealth transfer, long-term growth with stability
            purpose_factors = {
                'equity': 1.0,         # Standard for equity
                'debt': 1.0,           # Standard for debt
                'gold': 1.1,           # Wider for gold (Indian cultural significance)
                'alternatives': 1.0,   # Standard for alternatives
                'cash': 0.9            # Tighter for cash (focus on long-term assets)
            }
        
        # Combine factors (multiply age and purpose factors)
        for asset in allocation.keys():
            threshold_factors[asset] = age_based_factors.get(asset, 1.0) * purpose_factors.get(asset, 1.0)
        
        # Calculate base drift thresholds
        base_thresholds = rebalancing.calculate_drift_thresholds(allocation)
        
        # Apply custom threshold factors for legacy planning
        custom_thresholds = {
            'threshold_rationale': f"Legacy planning {goal_type} thresholds with age {age} and time horizon {time_horizon} years",
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
        
        # Create comprehensive legacy planning rebalancing strategy
        legacy_rebalancing_strategy = {
            'goal_type': goal_type,
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': custom_thresholds,
            'legacy_specific_considerations': {
                'tax_efficiency': "Prioritize tax-efficient rebalancing to maximize legacy value",
                'estate_liquidity': "Maintain sufficient liquid assets for potential estate costs",
                'generational_timeline': "Consider multi-generational investment horizon where appropriate"
            },
            'implementation_priorities': [
                "Annual review aligned with tax year for optimal tax efficiency",
                "Coordinate rebalancing with charitable giving strategy for tax advantages",
                "Consider both immediate estate liquidity needs and long-term growth",
                "Gradually increase stability as specified legacy events approach"
            ]
        }
        
        # Add tax-focused considerations (important for legacy planning)
        tax_considerations = {
            'fiscal_year_timing': "Coordinate rebalancing with fiscal year-end for tax-loss harvesting",
            'charitable_tactics': "Consider in-kind donations of appreciated securities to avoid capital gains",
            'generational_tax_planning': "Time asset transfers to minimize tax impact across generations",
            'bracket_management': "Manage income recognition to optimize tax brackets year to year"
        }
        
        # Add Indian-specific legacy considerations
        india_specific = {
            'gold_allocation': "Maintain culturally significant gold allocation for Indian family traditions",
            'family_business': "Consider special rebalancing rules for family business interests",
            'joint_family_considerations': "Account for joint family financial structures in rebalancing decisions",
            'hindu_undivided_family': "Special considerations for HUF structure if applicable"
        }
        
        # Add these to the strategy
        legacy_rebalancing_strategy['tax_optimization'] = tax_considerations
        legacy_rebalancing_strategy['india_specific_legacy_factors'] = india_specific
        
        return legacy_rebalancing_strategy
    
    def assess_estate_planning_readiness(self, goal_data):
        """
        Assess the readiness of an individual's estate planning based on their
        current documentation, family situation, and assets.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with estate planning readiness assessment
        """
        # Initialize the constraints if needed
        self._initialize_constraints()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        total_assets = goal_data.get('total_assets', 10000000)
        family_status = goal_data.get('family_status', 'married')
        estate_complexity = goal_data.get('estate_complexity', 'moderate')
        existing_documents = goal_data.get('existing_documents', [])
        estate_components = goal_data.get('estate_components', {
            'liquid_assets': total_assets * 0.2,
            'property': total_assets * 0.4,
            'investments': total_assets * 0.3,
            'business': total_assets * 0.1
        })
        health_status = goal_data.get('health_status', 'good')
        nri_status = goal_data.get('nri_status', False)
        
        # Analyze family composition for complexity
        has_minor_children = 'minor_children' in family_status.lower() or goal_data.get('has_minor_children', False)
        has_special_needs_dependents = goal_data.get('has_special_needs_dependents', False)
        has_multiple_marriages = goal_data.get('has_multiple_marriages', False)
        has_business_interests = estate_components.get('business', 0) > 0
        
        # Assess documentation readiness
        essential_documents = {
            'will': {
                'exists': 'will' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'essential',
                'status': 'missing' if 'will' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists'
            },
            'financial_poa': {
                'exists': 'financial_poa' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'essential',
                'status': 'missing' if 'financial_poa' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists'
            },
            'healthcare_poa': {
                'exists': 'healthcare_poa' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'essential',
                'status': 'missing' if 'healthcare_poa' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists'
            }
        }
        
        # Recommended documents based on situation
        recommended_documents = {
            'revocable_trust': {
                'recommended': total_assets > 20000000 or has_business_interests or estate_complexity == 'complex',
                'exists': 'revocable_trust' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'recommended' if total_assets > 20000000 or has_business_interests else 'optional',
                'status': 'missing' if 'revocable_trust' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists'
            },
            'irrevocable_trust': {
                'recommended': total_assets > 50000000 or has_special_needs_dependents,
                'exists': 'irrevocable_trust' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'recommended' if total_assets > 50000000 or has_special_needs_dependents else 'optional',
                'status': 'missing' if 'irrevocable_trust' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists'
            },
            'business_succession_plan': {
                'recommended': has_business_interests,
                'exists': 'business_succession_plan' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'essential' if has_business_interests else 'not_applicable',
                'status': 'missing' if has_business_interests and 'business_succession_plan' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists' if has_business_interests else 'not_applicable'
            },
            'gift_deed': {
                'recommended': total_assets > 10000000,
                'exists': 'gift_deed' in [doc.get('type', '').lower() for doc in existing_documents],
                'importance': 'recommended' if total_assets > 10000000 else 'optional',
                'status': 'missing' if 'gift_deed' not in [doc.get('type', '').lower() for doc in existing_documents] else 'exists'
            }
        }
        
        # Calculate document readiness score (0-100)
        essential_score = sum(1 for doc in essential_documents.values() if doc['exists']) / len(essential_documents) * 60
        recommended_score = sum(1 for doc in recommended_documents.values() if doc['exists'] and doc['recommended']) / max(1, sum(1 for doc in recommended_documents.values() if doc['recommended'])) * 40
        document_score = essential_score + recommended_score
        
        # Assess overall readiness level
        if document_score >= 90:
            readiness_level = "Excellent"
            readiness_description = "Comprehensive estate planning in place"
        elif document_score >= 70:
            readiness_level = "Good"
            readiness_description = "Essential documents in place, some recommended documents may be missing"
        elif document_score >= 40:
            readiness_level = "Basic"
            readiness_description = "Some essential documents in place, significant gaps remain"
        else:
            readiness_level = "Inadequate"
            readiness_description = "Critical estate planning documents missing"
        
        # Assess document currency/relevance
        documents_outdated = False
        for doc in existing_documents:
            doc_age = datetime.now().year - doc.get('year', datetime.now().year - 6)
            # Documents older than 5 years or created before major life changes need review
            if doc_age > 5:
                documents_outdated = True
                break
        
        # Assess asset/liability inventory completeness
        has_asset_inventory = goal_data.get('has_asset_inventory', False)
        asset_inventory_status = "Complete" if has_asset_inventory else "Missing"
        
        # Assess estate liquidity
        liquid_assets = estate_components.get('liquid_assets', 0)
        liquidity_ratio = liquid_assets / total_assets if total_assets > 0 else 0
        
        if liquidity_ratio >= 0.3:
            liquidity_status = "Excellent"
            liquidity_description = "Sufficient liquid assets for estate settlement"
        elif liquidity_ratio >= 0.15:
            liquidity_status = "Adequate"
            liquidity_description = "Likely sufficient liquidity for estate settlement"
        else:
            liquidity_status = "Concerning"
            liquidity_description = "Potential liquidity issues for estate settlement"
        
        # Assess special considerations
        special_considerations = []
        
        if nri_status:
            special_considerations.append({
                'type': 'NRI Status',
                'description': 'Cross-border inheritance and tax issues need specialized planning',
                'urgency': 'High'
            })
            
        if has_minor_children:
            special_considerations.append({
                'type': 'Minor Children',
                'description': 'Guardian nominations and trust arrangements needed',
                'urgency': 'High'
            })
            
        if has_special_needs_dependents:
            special_considerations.append({
                'type': 'Special Needs Dependent',
                'description': 'Specialized trust arrangements recommended',
                'urgency': 'High'
            })
            
        if has_business_interests:
            special_considerations.append({
                'type': 'Business Interests',
                'description': 'Business succession planning required',
                'urgency': 'High'
            })
            
        if has_multiple_marriages:
            special_considerations.append({
                'type': 'Multiple Marriages',
                'description': 'Complex beneficiary planning needed',
                'urgency': 'Medium'
            })
            
        if health_status.lower() in ['poor', 'critical', 'concerning']:
            special_considerations.append({
                'type': 'Health Concerns',
                'description': 'Accelerated planning timeline recommended',
                'urgency': 'High'
            })
        
        # Generate recommendations
        recommendations = []
        
        for doc_name, doc_info in essential_documents.items():
            if not doc_info['exists']:
                recommendations.append({
                    'priority': 'Urgent',
                    'action': f"Create {doc_name.replace('_', ' ').title()}",
                    'rationale': f"Essential document missing from estate plan",
                    'estimated_cost': self.legacy_params['estate_planning_options'].get(doc_name.split('_')[0], {}).get('typical_cost', 15000)
                })
                
        for doc_name, doc_info in recommended_documents.items():
            if doc_info['recommended'] and not doc_info['exists']:
                recommendations.append({
                    'priority': 'High',
                    'action': f"Create {doc_name.replace('_', ' ').title()}",
                    'rationale': f"Recommended document missing given your circumstances",
                    'estimated_cost': self.legacy_params['estate_planning_options'].get('trust', {}).get('types', {}).get(doc_name, {}).get('typical_cost', 50000) if 'trust' in doc_name else 25000
                })
                
        if documents_outdated:
            recommendations.append({
                'priority': 'High',
                'action': "Update outdated estate documents",
                'rationale': "Documents should be reviewed every 3-5 years or after major life events",
                'estimated_cost': 15000
            })
            
        if not has_asset_inventory:
            recommendations.append({
                'priority': 'High',
                'action': "Create comprehensive asset and liability inventory",
                'rationale': "Essential for effective estate administration",
                'estimated_cost': 5000
            })
            
        if liquidity_ratio < 0.15:
            recommendations.append({
                'priority': 'Medium',
                'action': "Improve estate liquidity",
                'rationale': "Insufficient liquid assets may cause complications during estate settlement",
                'implementation': "Consider life insurance, maintaining emergency fund, or more liquid investments"
            })
        
        # Create timeline for implementation
        if readiness_level == "Inadequate":
            implementation_timeline = "Immediate (1-3 months)"
        elif readiness_level == "Basic":
            implementation_timeline = "Near-term (3-6 months)"
        elif readiness_level == "Good" and documents_outdated:
            implementation_timeline = "Near-term (3-6 months)"
        else:
            implementation_timeline = "Medium-term (6-12 months)"
        
        return {
            'readiness_assessment': {
                'document_score': round(document_score),
                'readiness_level': readiness_level,
                'readiness_description': readiness_description,
                'documents_current': not documents_outdated,
                'asset_inventory_status': asset_inventory_status,
                'liquidity_assessment': {
                    'status': liquidity_status,
                    'description': liquidity_description,
                    'liquidity_ratio': round(liquidity_ratio * 100, 1)
                }
            },
            'document_status': {
                'essential_documents': essential_documents,
                'recommended_documents': recommended_documents
            },
            'special_considerations': special_considerations,
            'recommendations': recommendations,
            'implementation_timeline': implementation_timeline,
            'estimated_total_cost': sum(rec.get('estimated_cost', 0) for rec in recommendations)
        }
    
    def assess_charitable_giving_capability(self, goal_data):
        """
        Assess the capability and capacity for charitable giving based on
        financial situation, tax considerations, and personal values.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with charitable giving capability assessment
        """
        # Initialize the constraints if needed
        self._initialize_constraints()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        annual_income = goal_data.get('annual_income', 1200000)
        total_assets = goal_data.get('total_assets', 10000000)
        discretionary_income = goal_data.get('discretionary_income', annual_income * 0.15)
        tax_bracket = goal_data.get('tax_bracket', 0.3)
        retirement_status = goal_data.get('retirement_status', 'pre_retirement')
        charitable_interests = goal_data.get('charitable_interests', [])
        current_giving = goal_data.get('current_giving', 0)
        other_financial_goals = goal_data.get('other_financial_goals', [])
        
        # Calculate giving capability metrics
        max_tax_advantaged_giving = annual_income * 0.1  # 10% of income limit for Section 80G
        
        # Calculate sustainable giving capacity based on discretionary income
        sustainable_annual_giving = discretionary_income * 0.3  # 30% of discretionary income is sustainable
        
        # Adjust based on retirement status
        if retirement_status == 'retired':
            sustainable_annual_giving *= 0.8  # More conservative for retirees
        
        # Calculate asset-based giving capacity (one-time major gifts)
        major_gift_capacity = total_assets * 0.05  # 5% of assets could be used for major gifts
        
        # Factor in tax efficiency
        tax_savings_rate = tax_bracket
        tax_savings_potential = min(sustainable_annual_giving, max_tax_advantaged_giving) * tax_savings_rate
        
        # Calculate giving efficiency ratio (potential impact per rupee of net cost)
        giving_efficiency = 1 / (1 - tax_savings_rate) if tax_savings_rate < 1 else 1.0
        
        # Assess giving vehicle suitability
        direct_donations_suitable = True  # Always an option
        
        charitable_trust_suitable = (
            total_assets > 20000000 and
            sustainable_annual_giving > 500000 and
            age < 70
        )
        
        endowment_suitable = (
            total_assets > 50000000 or
            sustainable_annual_giving > 1000000
        )
        
        # Assess competition with other financial goals
        goals_competition = []
        for goal in other_financial_goals:
            goal_type = goal.get('type', '').lower()
            goal_priority = goal.get('priority', 'medium').lower()
            goal_funding_status = goal.get('funding_status', 'partial').lower()
            
            if goal_priority in ['high', 'essential'] and goal_funding_status != 'complete':
                goals_competition.append({
                    'goal_type': goal_type,
                    'priority': goal_priority,
                    'funding_status': goal_funding_status,
                    'recommended_action': 'Balance with charitable giving, prioritizing essential goal'
                })
        
        # Determine overall giving capacity level
        if sustainable_annual_giving > current_giving * 2:
            capacity_level = "Significant Expansion Possible"
            capacity_description = "Capacity to substantially increase charitable giving"
        elif sustainable_annual_giving > current_giving * 1.2:
            capacity_level = "Moderate Expansion Possible"
            capacity_description = "Capacity to moderately increase charitable giving"
        elif sustainable_annual_giving >= current_giving * 0.8:
            capacity_level = "Maintaining Current Level"
            capacity_description = "Current giving is appropriately aligned with capacity"
        else:
            capacity_level = "Potentially Overextended"
            capacity_description = "Current giving may exceed sustainable capacity"
        
        # Generate recommendations for giving strategy
        recommendations = []
        
        if sustainable_annual_giving > current_giving * 1.5:
            recommendations.append({
                'priority': 'High',
                'action': "Increase annual charitable giving",
                'target': round(sustainable_annual_giving),
                'implementation': "Gradually increase giving to target over 1-2 years",
                'tax_benefit': f"Potential tax savings of ₹{round(min(sustainable_annual_giving, max_tax_advantaged_giving) * tax_savings_rate)} annually"
            })
            
        if current_giving > max_tax_advantaged_giving:
            recommendations.append({
                'priority': 'Medium',
                'action': "Optimize tax strategy for charitable giving",
                'rationale': "Current giving exceeds maximum tax-advantaged amount",
                'implementation': "Consider multi-year giving strategy or donor-advised fund"
            })
            
        if charitable_trust_suitable:
            recommendations.append({
                'priority': 'Medium',
                'action': "Explore establishing a charitable trust",
                'rationale': "Assets and giving level suitable for more structured approach",
                'estimated_cost': self.legacy_params['charitable_giving_options']['charitable_trust']['setup_cost']
            })
            
        if len(charitable_interests) < 2:
            recommendations.append({
                'priority': 'Low',
                'action': "Develop structured giving plan aligned with values",
                'rationale': "Clarify charitable mission and focus areas",
                'implementation': "Consider working with philanthropy advisor"
            })
        
        # Generate giving vehicle comparison
        giving_vehicles = [
            {
                'vehicle': 'Direct Donations',
                'suitability': 'High',
                'minimum_recommended': 0,
                'tax_benefits': 'Section 80G deductions (50-100% depending on organization)',
                'implementation_complexity': 'Low',
                'best_for': 'Regular giving to established organizations'
            }
        ]
        
        if charitable_trust_suitable:
            giving_vehicles.append({
                'vehicle': 'Charitable Trust',
                'suitability': 'Medium' if total_assets > 20000000 else 'Low',
                'minimum_recommended': self.legacy_params['charitable_giving_options']['charitable_trust']['minimum_corpus'],
                'tax_benefits': 'Section 80G deductions for contributions to trust',
                'implementation_complexity': 'High',
                'best_for': 'Long-term structured giving with family involvement'
            })
            
        if endowment_suitable:
            giving_vehicles.append({
                'vehicle': 'Endowment',
                'suitability': 'Medium' if total_assets > 50000000 else 'Low',
                'minimum_recommended': self.legacy_params['charitable_giving_options']['endowment']['minimum'],
                'tax_benefits': 'Depends on receiving organization',
                'implementation_complexity': 'Medium',
                'best_for': 'Perpetual support for specific institutions or causes'
            })
        
        return {
            'giving_capacity': {
                'sustainable_annual_giving': round(sustainable_annual_giving),
                'current_annual_giving': round(current_giving),
                'max_tax_advantaged_giving': round(max_tax_advantaged_giving),
                'major_gift_capacity': round(major_gift_capacity),
                'capacity_level': capacity_level,
                'capacity_description': capacity_description
            },
            'tax_efficiency': {
                'tax_bracket': f"{round(tax_bracket * 100)}%",
                'potential_tax_savings': round(tax_savings_potential),
                'giving_efficiency_ratio': round(giving_efficiency, 2),
                'effective_cost_per_1000': round(1000 / giving_efficiency)
            },
            'giving_vehicles': giving_vehicles,
            'competing_financial_goals': goals_competition,
            'recommendations': recommendations,
            'implementation_approach': "Structured giving plan with annual review and adjustment"
        }
    
    def evaluate_wealth_transfer_impact(self, goal_data):
        """
        Evaluate the impact of wealth transfer strategies on both donors
        and recipients, considering financial, tax, and family dynamics.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with wealth transfer impact assessment
        """
        # Initialize the constraints if needed
        self._initialize_constraints()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        total_assets = goal_data.get('total_assets', 10000000)
        annual_income = goal_data.get('annual_income', 1200000)
        retirement_status = goal_data.get('retirement_status', 'pre_retirement')
        estate_components = goal_data.get('estate_components', {
            'liquid_assets': total_assets * 0.2,
            'property': total_assets * 0.4,
            'investments': total_assets * 0.3,
            'business': total_assets * 0.1
        })
        beneficiaries = goal_data.get('beneficiaries', [])
        wealth_transfer_plans = goal_data.get('wealth_transfer_plans', [])
        nri_status = goal_data.get('nri_status', False)
        family_values = goal_data.get('family_values', [])
        
        # Calculate key metrics
        total_planned_transfers = sum(plan.get('amount', 0) for plan in wealth_transfer_plans)
        transfer_percentage = total_planned_transfers / total_assets if total_assets > 0 else 0
        
        # Assess donor financial security first
        retirement_needs = annual_income * 0.7 * 25  # Simple estimate: 70% of income for 25 years
        liquid_assets = estate_components.get('liquid_assets', 0)
        investment_assets = estate_components.get('investments', 0)
        
        assets_available_for_retirement = liquid_assets + investment_assets
        retirement_funding_ratio = assets_available_for_retirement / retirement_needs if retirement_needs > 0 else 0
        
        if retirement_status == 'retired':
            if retirement_funding_ratio < 0.7:
                donor_security_status = "At Risk"
                donor_security_description = "Retirement assets may be insufficient for lifetime needs"
            elif retirement_funding_ratio < 1.0:
                donor_security_status = "Adequate"
                donor_security_description = "Retirement assets likely sufficient with careful management"
            else:
                donor_security_status = "Secure"
                donor_security_description = "Retirement well-funded, capacity exists for wealth transfer"
        else:  # pre-retirement
            if retirement_funding_ratio < 0.5:
                donor_security_status = "Concerning"
                donor_security_description = "Retirement savings significantly behind target"
            elif retirement_funding_ratio < 0.8:
                donor_security_status = "Progressing"
                donor_security_description = "Retirement savings building, limited capacity for wealth transfer"
            else:
                donor_security_status = "Strong"
                donor_security_description = "Retirement on track, capacity exists for wealth transfer"
        
        # Assess asset distribution efficiency
        property_assets = estate_components.get('property', 0)
        business_assets = estate_components.get('business', 0)
        
        illiquid_assets = property_assets + business_assets
        illiquid_percentage = illiquid_assets / total_assets if total_assets > 0 else 0
        
        if illiquid_percentage > 0.7:
            liquidity_challenge = "High"
            liquidity_description = "Predominantly illiquid assets may complicate wealth transfer"
        elif illiquid_percentage > 0.5:
            liquidity_challenge = "Moderate"
            liquidity_description = "Balance of liquid and illiquid assets requires careful planning"
        else:
            liquidity_challenge = "Low"
            liquidity_description = "Sufficient liquid assets for flexible wealth transfer"
        
        # Assess tax efficiency of current plans
        annual_gift_limit = self.legacy_params['wealth_transfer_options']['gift']['annual_limit']
        
        tax_efficient_transfers = sum(
            min(plan.get('amount', 0), annual_gift_limit) 
            for plan in wealth_transfer_plans 
            if plan.get('type', '').lower() == 'gift'
        )
        
        tax_efficiency_ratio = tax_efficient_transfers / total_planned_transfers if total_planned_transfers > 0 else 0
        
        if tax_efficiency_ratio > 0.8:
            tax_efficiency_status = "Excellent"
            tax_efficiency_description = "Current plan maximizes tax-efficient transfers"
        elif tax_efficiency_ratio > 0.5:
            tax_efficiency_status = "Good"
            tax_efficiency_description = "Most transfers utilize tax-efficient methods"
        else:
            tax_efficiency_status = "Needs Improvement"
            tax_efficiency_description = "Opportunities exist to improve tax efficiency of transfers"
        
        # Assess recipient readiness and impact
        recipient_assessments = []
        
        for beneficiary in beneficiaries:
            recipient_age = beneficiary.get('age', 30)
            relationship = beneficiary.get('relationship', 'child')
            financial_maturity = beneficiary.get('financial_maturity', 'moderate')
            financial_need = beneficiary.get('financial_need', 'moderate')
            
            # Planned transfers to this beneficiary
            beneficiary_transfers = [
                plan for plan in wealth_transfer_plans 
                if plan.get('beneficiary_id') == beneficiary.get('id')
            ]
            total_to_beneficiary = sum(plan.get('amount', 0) for plan in beneficiary_transfers)
            
            # Assess readiness
            if financial_maturity == 'high':
                readiness_status = "High"
                readiness_description = "Well-prepared to manage transferred wealth"
            elif financial_maturity == 'moderate':
                readiness_status = "Moderate"
                readiness_description = "Some preparation for wealth management, more guidance beneficial"
            else:
                readiness_status = "Low"
                readiness_description = "Significant preparation needed before substantial transfers"
            
            # Assess potential impact
            if financial_need == 'high' and total_to_beneficiary > 0:
                impact_status = "Transformative"
                impact_description = "Transfer would address significant financial needs"
            elif financial_need == 'moderate' and total_to_beneficiary > 0:
                impact_status = "Supportive"
                impact_description = "Transfer would provide meaningful financial support"
            else:
                impact_status = "Enhancement"
                impact_description = "Transfer would enhance already stable financial situation"
            
            # Consider structure recommendations
            if recipient_age < 25 or financial_maturity == 'low':
                recommended_structure = "Trust with age-based milestones"
                structure_rationale = "Provides financial support with built-in maturity safeguards"
            elif recipient_age < 40 and financial_maturity == 'moderate':
                recommended_structure = "Phased transfers with guidance"
                structure_rationale = "Balances immediate benefit with ongoing mentorship"
            else:
                recommended_structure = "Direct transfers with education"
                structure_rationale = "Maximizes autonomy with appropriate preparation"
            
            recipient_assessments.append({
                'beneficiary': f"{relationship.title()} (Age {recipient_age})",
                'planned_transfer_amount': round(total_to_beneficiary),
                'readiness': {
                    'status': readiness_status,
                    'description': readiness_description
                },
                'impact': {
                    'status': impact_status,
                    'description': impact_description
                },
                'recommended_structure': {
                    'type': recommended_structure,
                    'rationale': structure_rationale
                }
            })
        
        # Generate recommendations
        recommendations = []
        
        # Address donor security first
        if retirement_funding_ratio < 0.8 and transfer_percentage > 0.2:
            recommendations.append({
                'priority': 'High',
                'action': "Reassess wealth transfer timing and amounts",
                'rationale': "Ensure personal financial security before significant transfers",
                'implementation': "Prioritize retirement funding, consider phased transfers over longer timeframe"
            })
        
        # Address tax efficiency
        if tax_efficiency_ratio < 0.5:
            recommendations.append({
                'priority': 'High',
                'action': "Restructure transfers for tax efficiency",
                'rationale': "Current plan may result in unnecessary tax implications",
                'implementation': "Utilize annual gift allowances, consider trust structures"
            })
        
        # Address liquidity challenges
        if illiquid_percentage > 0.7:
            recommendations.append({
                'priority': 'Medium',
                'action': "Develop strategy for transferring illiquid assets",
                'rationale': "High proportion of illiquid assets requires specialized planning",
                'implementation': "Consider family limited partnerships, staged business transition, or life insurance for equalization"
            })
        
        # Address beneficiary preparation
        if any(assessment['readiness']['status'] == 'Low' for assessment in recipient_assessments):
            recommendations.append({
                'priority': 'High',
                'action': "Implement financial literacy program for beneficiaries",
                'rationale': "Some beneficiaries may need preparation for wealth responsibility",
                'implementation': "Family financial education, guided investment experiences, mentorship"
            })
        
        # Address NRI considerations if applicable
        if nri_status:
            recommendations.append({
                'priority': 'High',
                'action': "Seek specialized cross-border estate planning advice",
                'rationale': "NRI status creates complex international tax and legal considerations",
                'implementation': "Consult with advisors experienced in both Indian and foreign jurisdictions"
            })
        
        # Ensure alignment with family values
        if family_values:
            recommendations.append({
                'priority': 'Medium',
                'action': "Document wealth transfer philosophy and expectations",
                'rationale': "Ensure wealth transfer aligns with stated family values",
                'implementation': "Create family mission statement, ethical will, or legacy letter"
            })
        
        return {
            'donor_financial_security': {
                'status': donor_security_status,
                'description': donor_security_description,
                'retirement_funding_ratio': round(retirement_funding_ratio * 100, 1),
                'assets_available': round(assets_available_for_retirement),
                'estimated_retirement_needs': round(retirement_needs)
            },
            'wealth_transfer_assessment': {
                'total_planned_transfers': round(total_planned_transfers),
                'percentage_of_total_assets': round(transfer_percentage * 100, 1),
                'asset_liquidity_challenge': {
                    'level': liquidity_challenge,
                    'description': liquidity_description,
                    'illiquid_percentage': round(illiquid_percentage * 100, 1)
                },
                'tax_efficiency': {
                    'status': tax_efficiency_status,
                    'description': tax_efficiency_description,
                    'efficiency_ratio': round(tax_efficiency_ratio * 100, 1)
                }
            },
            'recipient_assessments': recipient_assessments,
            'recommendations': recommendations,
            'implementation_priorities': [
                "Secure donor financial independence first",
                "Prepare recipients through education and graduated responsibility",
                "Optimize transfer methods for tax efficiency",
                "Structure transfers aligned with family values and recipient readiness"
            ]
        }
    
    def assess_legacy_planning_integration(self, goal_data):
        """
        Assess how well legacy planning is integrated with overall financial planning,
        including retirement, tax planning, and risk management.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with legacy planning integration assessment
        """
        # Initialize the constraints if needed
        self._initialize_constraints()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        total_assets = goal_data.get('total_assets', 10000000)
        annual_income = goal_data.get('annual_income', 1200000)
        retirement_status = goal_data.get('retirement_status', 'pre_retirement')
        financial_plans = goal_data.get('financial_plans', [])
        estate_plans = goal_data.get('estate_plans', [])
        risk_management = goal_data.get('risk_management', {})
        tax_planning = goal_data.get('tax_planning', {})
        
        # Assess retirement-legacy integration
        retirement_plan = next((plan for plan in financial_plans if plan.get('type', '').lower() == 'retirement'), None)
        
        if retirement_plan:
            retirement_legacy_integration = "Integrated" if retirement_plan.get('considers_legacy', False) else "Separate"
            retirement_funding_status = retirement_plan.get('funding_status', 'unknown')
            
            if retirement_funding_status == 'fully_funded' and retirement_legacy_integration == "Integrated":
                retirement_integration_status = "Excellent"
                retirement_integration_description = "Well-funded retirement with legacy planning integration"
            elif retirement_funding_status in ['fully_funded', 'on_track'] and retirement_legacy_integration == "Separate":
                retirement_integration_status = "Good"
                retirement_integration_description = "Retirement well-planned, could better integrate with legacy goals"
            elif retirement_funding_status in ['behind', 'at_risk']:
                retirement_integration_status = "Concerning"
                retirement_integration_description = "Prioritize retirement funding before substantial legacy planning"
            else:
                retirement_integration_status = "Adequate"
                retirement_integration_description = "Retirement planning in progress with some legacy considerations"
        else:
            retirement_integration_status = "Missing"
            retirement_integration_description = "No retirement plan found, critical foundation for legacy planning"
            retirement_legacy_integration = "None"
        
        # Assess tax planning integration
        has_tax_plan = bool(tax_planning)
        tax_legacy_integration = tax_planning.get('considers_legacy', False) if has_tax_plan else False
        
        if has_tax_plan and tax_legacy_integration:
            tax_integration_status = "Strong"
            tax_integration_description = "Tax planning fully integrates legacy considerations"
        elif has_tax_plan:
            tax_integration_status = "Partial"
            tax_integration_description = "Tax planning exists but lacks legacy integration"
        else:
            tax_integration_status = "Weak"
            tax_integration_description = "Tax planning not formalized, missing legacy optimization opportunities"
        
        # Assess risk management integration
        life_insurance = risk_management.get('life_insurance', 0)
        disability_insurance = risk_management.get('disability_insurance', False)
        property_insurance = risk_management.get('property_insurance', False)
        
        # Calculate life insurance adequacy for legacy protection
        annual_expenses = annual_income * 0.7  # Estimate expenses at 70% of income
        years_to_replace = 10 if age < 50 else 7 if age < 60 else 5
        insurance_need = annual_expenses * years_to_replace
        insurance_adequacy = life_insurance / insurance_need if insurance_need > 0 else 0
        
        if insurance_adequacy >= 0.9 and disability_insurance and property_insurance:
            risk_integration_status = "Comprehensive"
            risk_integration_description = "Risk management fully protects legacy planning goals"
        elif insurance_adequacy >= 0.5 and (disability_insurance or property_insurance):
            risk_integration_status = "Adequate"
            risk_integration_description = "Basic risk management in place, some gaps in legacy protection"
        else:
            risk_integration_status = "Insufficient"
            risk_integration_description = "Significant risk management gaps could undermine legacy goals"
        
        # Assess overall integration level
        integration_scores = {
            "Excellent": 4,
            "Strong": 3,
            "Good": 3,
            "Comprehensive": 4,
            "Adequate": 2,
            "Partial": 2,
            "Weak": 1,
            "Concerning": 1,
            "Insufficient": 1,
            "Missing": 0
        }
        
        integration_score = (
            integration_scores.get(retirement_integration_status, 0) +
            integration_scores.get(tax_integration_status, 0) +
            integration_scores.get(risk_integration_status, 0)
        ) / 3 * 25  # Scale to 0-100
        
        if integration_score >= 75:
            overall_integration = "Excellent"
            integration_description = "Legacy planning well-integrated with overall financial plan"
        elif integration_score >= 50:
            overall_integration = "Good"
            integration_description = "Legacy planning mostly integrated, some areas for improvement"
        elif integration_score >= 25:
            overall_integration = "Partial"
            integration_description = "Limited integration between legacy and financial planning"
        else:
            overall_integration = "Poor"
            integration_description = "Legacy planning disconnected from overall financial planning"
        
        # Generate recommendations
        recommendations = []
        
        if retirement_integration_status in ["Missing", "Concerning"]:
            recommendations.append({
                'priority': 'Urgent',
                'action': "Develop comprehensive retirement plan before legacy planning",
                'rationale': "Secure your financial future before planning legacy transfers",
                'implementation': "Work with financial planner to create retirement roadmap"
            })
            
        if tax_integration_status in ["Weak", "Partial"]:
            recommendations.append({
                'priority': 'High',
                'action': "Integrate tax planning with legacy objectives",
                'rationale': "Tax efficiency can significantly enhance legacy impact",
                'implementation': "Consult tax professional with estate planning expertise"
            })
            
        if risk_integration_status == "Insufficient":
            recommendations.append({
                'priority': 'High',
                'action': "Enhance risk management to protect legacy goals",
                'rationale': "Inadequate insurance and risk protection threatens legacy plans",
                'implementation': "Review life, disability, and property insurance coverage"
            })
            
        if overall_integration in ["Poor", "Partial"]:
            recommendations.append({
                'priority': 'Medium',
                'action': "Develop integrated financial and legacy planning approach",
                'rationale': "Siloed planning reduces effectiveness and efficiency",
                'implementation': "Consider family office approach or coordinated advisor team"
            })
        
        return {
            'overall_integration': {
                'status': overall_integration,
                'description': integration_description,
                'score': round(integration_score)
            },
            'component_integration': {
                'retirement_planning': {
                    'status': retirement_integration_status,
                    'description': retirement_integration_description,
                    'integration_level': retirement_legacy_integration
                },
                'tax_planning': {
                    'status': tax_integration_status,
                    'description': tax_integration_description,
                    'has_formal_tax_plan': has_tax_plan,
                    'considers_legacy': tax_legacy_integration
                },
                'risk_management': {
                    'status': risk_integration_status,
                    'description': risk_integration_description,
                    'insurance_adequacy': round(insurance_adequacy * 100, 1),
                    'key_protections': {
                        'life_insurance': bool(life_insurance),
                        'disability_insurance': bool(disability_insurance),
                        'property_insurance': bool(property_insurance)
                    }
                }
            },
            'recommendations': recommendations,
            'integration_framework': [
                "Establish clear legacy objectives and values",
                "Ensure retirement security as foundation for legacy planning",
                "Integrate tax planning to maximize legacy impact",
                "Implement risk management to protect legacy goals",
                "Create coordinated advisor team for holistic approach"
            ]
        }
    
    def optimize_estate_planning_structure(self, goal_data):
        """
        Optimize the estate planning structure based on asset composition,
        family dynamics, and tax considerations.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with optimized estate planning structure
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        total_assets = goal_data.get('total_assets', 10000000)
        family_status = goal_data.get('family_status', 'married')
        estate_complexity = goal_data.get('estate_complexity', 'moderate')
        beneficiaries = goal_data.get('beneficiaries', [])
        existing_documents = goal_data.get('existing_documents', [])
        estate_components = goal_data.get('estate_components', {
            'liquid_assets': total_assets * 0.2,
            'property': total_assets * 0.4,
            'investments': total_assets * 0.3,
            'business': total_assets * 0.1
        })
        nri_status = goal_data.get('nri_status', False)
        
        # Get estate planning readiness assessment
        readiness = self.assess_estate_planning_readiness(goal_data)
        
        # Determine appropriate estate planning structure based on assets and family situation
        # Calculate complexity factors
        has_minor_children = 'minor_children' in family_status.lower() or goal_data.get('has_minor_children', False)
        has_special_needs_dependents = goal_data.get('has_special_needs_dependents', False)
        has_multiple_marriages = goal_data.get('has_multiple_marriages', False)
        has_business_interests = estate_components.get('business', 0) > 0
        business_value = estate_components.get('business', 0)
        property_value = estate_components.get('property', 0)
        
        # Calculate family complexity score (0-100)
        family_complexity_score = 0
        if has_minor_children:
            family_complexity_score += 30
        if has_special_needs_dependents:
            family_complexity_score += 40
        if has_multiple_marriages:
            family_complexity_score += 30
        if len(beneficiaries) > 3:
            family_complexity_score += 20
        
        # Cap at 100
        family_complexity_score = min(100, family_complexity_score)
        
        # Calculate asset complexity score (0-100)
        asset_complexity_score = 0
        if has_business_interests:
            asset_complexity_score += 40 * (business_value / total_assets) if total_assets > 0 else 0
        if property_value > 0:
            asset_complexity_score += 20 * (property_value / total_assets) if total_assets > 0 else 0
        if nri_status:
            asset_complexity_score += 30
        if total_assets > 50000000:  # Over 5 crores
            asset_complexity_score += 20
        
        # Cap at 100
        asset_complexity_score = min(100, asset_complexity_score)
        
        # Calculate overall complexity score (weighted average)
        overall_complexity_score = (family_complexity_score * 0.6) + (asset_complexity_score * 0.4)
        
        # Determine optimized estate planning structure
        if overall_complexity_score >= 70:
            # Complex estate planning needed
            optimized_structure = "Comprehensive Estate Plan with Multiple Trusts"
            structural_components = [
                {
                    'component': 'Will',
                    'importance': 'Essential',
                    'purpose': 'Foundation document that directs asset distribution and names executor',
                    'estimated_cost': self.legacy_params['estate_planning_options']['will']['typical_cost'],
                    'priority': 'Very High'
                },
                {
                    'component': 'Financial Power of Attorney',
                    'importance': 'Essential',
                    'purpose': 'Designates financial decision-maker if incapacitated',
                    'estimated_cost': self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost'] / 2,
                    'priority': 'Very High'
                },
                {
                    'component': 'Healthcare Power of Attorney',
                    'importance': 'Essential',
                    'purpose': 'Designates healthcare decision-maker if incapacitated',
                    'estimated_cost': self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost'] / 2,
                    'priority': 'Very High'
                },
                {
                    'component': 'Revocable Living Trust',
                    'importance': 'Essential',
                    'purpose': 'Primary vehicle for asset management and distribution',
                    'estimated_cost': self.legacy_params['estate_planning_options']['trust']['types']['revocable']['typical_cost'],
                    'priority': 'High'
                }
            ]
            
            # Add special purpose trusts as needed
            if has_minor_children or has_special_needs_dependents:
                structural_components.append({
                    'component': 'Supplemental Needs Trust',
                    'importance': 'Recommended',
                    'purpose': 'Provides for special needs beneficiaries without disrupting government benefits',
                    'estimated_cost': self.legacy_params['estate_planning_options']['trust']['types']['irrevocable']['typical_cost'],
                    'priority': 'High' if has_special_needs_dependents else 'Medium'
                })
                
            if has_business_interests:
                structural_components.append({
                    'component': 'Business Succession Plan',
                    'importance': 'Essential',
                    'purpose': 'Structures orderly business transition',
                    'estimated_cost': 50000,
                    'priority': 'High'
                })
                
            if total_assets > 50000000:
                structural_components.append({
                    'component': 'Family Limited Partnership',
                    'importance': 'Recommended',
                    'purpose': 'Facilitates tax-efficient wealth transfer for large estates',
                    'estimated_cost': 100000,
                    'priority': 'Medium'
                })
                
            if nri_status:
                structural_components.append({
                    'component': 'International Estate Planning Provisions',
                    'importance': 'Essential',
                    'purpose': 'Addresses cross-border inheritance and tax issues',
                    'estimated_cost': 75000,
                    'priority': 'High'
                })
                
        elif overall_complexity_score >= 40:
            # Moderate estate planning needed
            optimized_structure = "Basic-Plus Estate Plan with Revocable Trust"
            structural_components = [
                {
                    'component': 'Will',
                    'importance': 'Essential',
                    'purpose': 'Foundation document that directs asset distribution and names executor',
                    'estimated_cost': self.legacy_params['estate_planning_options']['will']['typical_cost'],
                    'priority': 'Very High'
                },
                {
                    'component': 'Financial Power of Attorney',
                    'importance': 'Essential',
                    'purpose': 'Designates financial decision-maker if incapacitated',
                    'estimated_cost': self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost'] / 2,
                    'priority': 'Very High'
                },
                {
                    'component': 'Healthcare Power of Attorney',
                    'importance': 'Essential',
                    'purpose': 'Designates healthcare decision-maker if incapacitated',
                    'estimated_cost': self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost'] / 2,
                    'priority': 'Very High'
                },
                {
                    'component': 'Revocable Living Trust',
                    'importance': 'Recommended',
                    'purpose': 'Provides privacy and avoids probate for distributed assets',
                    'estimated_cost': self.legacy_params['estate_planning_options']['trust']['types']['revocable']['typical_cost'],
                    'priority': 'Medium'
                }
            ]
            
            # Add specific components based on situation
            if has_minor_children:
                structural_components.append({
                    'component': 'Guardian Nominations',
                    'importance': 'Essential',
                    'purpose': 'Designates caregivers for minor children',
                    'estimated_cost': 0,  # Included in will
                    'priority': 'Very High'
                })
                
            if has_business_interests:
                structural_components.append({
                    'component': 'Business Succession Plan',
                    'importance': 'Recommended',
                    'purpose': 'Structures orderly business transition',
                    'estimated_cost': 40000,
                    'priority': 'Medium'
                })
                
        else:
            # Basic estate planning is sufficient
            optimized_structure = "Essential Estate Plan"
            structural_components = [
                {
                    'component': 'Will',
                    'importance': 'Essential',
                    'purpose': 'Foundation document that directs asset distribution and names executor',
                    'estimated_cost': self.legacy_params['estate_planning_options']['will']['typical_cost'],
                    'priority': 'Very High'
                },
                {
                    'component': 'Financial Power of Attorney',
                    'importance': 'Essential',
                    'purpose': 'Designates financial decision-maker if incapacitated',
                    'estimated_cost': self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost'] / 2,
                    'priority': 'Very High'
                },
                {
                    'component': 'Healthcare Power of Attorney',
                    'importance': 'Essential',
                    'purpose': 'Designates healthcare decision-maker if incapacitated',
                    'estimated_cost': self.legacy_params['estate_planning_options']['power_of_attorney']['typical_cost'] / 2,
                    'priority': 'Very High'
                }
            ]
            
            if has_minor_children:
                structural_components.append({
                    'component': 'Guardian Nominations',
                    'importance': 'Essential',
                    'purpose': 'Designates caregivers for minor children',
                    'estimated_cost': 0,  # Included in will
                    'priority': 'Very High'
                })
        
        # Create implementation roadmap
        implementation_roadmap = []
        
        # Step 1: Complete essential documents
        missing_essential_docs = [doc for doc in readiness['document_status']['essential_documents'].values() if doc['status'] == 'missing']
        if missing_essential_docs:
            implementation_roadmap.append({
                'phase': 1,
                'timeframe': 'Immediate (1-3 months)',
                'actions': ["Create essential estate planning documents (will, powers of attorney)",
                           "Document asset inventory and beneficiary designations",
                           "Identify qualified estate planning attorney"]
            })
        
        # Step 2: Create trust structures if needed
        if overall_complexity_score >= 40:
            implementation_roadmap.append({
                'phase': 2,
                'timeframe': 'Near-term (3-6 months)',
                'actions': ["Establish revocable trust structure",
                           "Re-title assets to trust as appropriate",
                           "Update beneficiary designations to align with estate plan"]
            })
        
        # Step 3: Address special situations
        special_situation_actions = []
        if has_business_interests:
            special_situation_actions.append("Develop comprehensive business succession plan")
        if has_special_needs_dependents:
            special_situation_actions.append("Create specialized trust for special needs beneficiaries")
        if nri_status:
            special_situation_actions.append("Consult with international estate planning specialist")
            
        if special_situation_actions:
            implementation_roadmap.append({
                'phase': 3,
                'timeframe': 'Medium-term (6-12 months)',
                'actions': special_situation_actions
            })
            
        # Step 4: Ongoing maintenance
        implementation_roadmap.append({
            'phase': 4,
            'timeframe': 'Ongoing',
            'actions': ["Review estate plan every 3-5 years or after major life events",
                       "Update asset inventory annually",
                       "Communicate plan details to key family members or executor"]
        })
        
        # Calculate total estimated cost
        total_estimated_cost = sum(component.get('estimated_cost', 0) for component in structural_components)
        
        # Regional considerations for India
        regional_considerations = {
            'hindu_succession': "Hindu Succession Act may govern inheritance in absence of will",
            'muslim_personal_law': "Muslim Personal Law applies for Muslim individuals",
            'regional_customs': "Consider regional customs and practices for family inheritance traditions",
            'property_registration': "Ensure property transfers are properly registered per state requirements"
        }
        
        return {
            'optimized_structure': {
                'structure_type': optimized_structure,
                'complexity_assessment': {
                    'overall_score': round(overall_complexity_score),
                    'family_complexity_score': round(family_complexity_score),
                    'asset_complexity_score': round(asset_complexity_score),
                    'classification': 'Complex' if overall_complexity_score >= 70 else 'Moderate' if overall_complexity_score >= 40 else 'Basic'
                },
                'structural_components': structural_components,
                'total_estimated_cost': round(total_estimated_cost)
            },
            'implementation_roadmap': implementation_roadmap,
            'india_specific_considerations': regional_considerations,
            'optimization_rationale': "Structure optimized based on family complexity, asset composition, and estate size",
            'legal_disclaimer': "This optimized structure is a recommendation only. Consult with qualified legal professionals for implementation."
        }
    
    def optimize_charitable_giving_strategy(self, goal_data):
        """
        Optimize charitable giving strategy for maximum impact and tax efficiency.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with optimized charitable giving strategy
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        annual_income = goal_data.get('annual_income', 1200000)
        total_assets = goal_data.get('total_assets', 10000000)
        tax_bracket = goal_data.get('tax_bracket', 0.3)
        retirement_status = goal_data.get('retirement_status', 'pre_retirement')
        charitable_interests = goal_data.get('charitable_interests', [])
        current_giving = goal_data.get('current_giving', 0)
        giving_timeframe = goal_data.get('giving_timeframe', 'lifetime')  # 'lifetime', 'bequest', or 'both'
        target_amount = goal_data.get('target_amount', total_assets * 0.05)
        
        # Get charitable giving capability assessment
        capability = self.assess_charitable_giving_capability(goal_data)
        
        # Determine optimal giving vehicle based on amount, timeframe, and tax situation
        sustainable_annual_giving = capability['giving_capacity']['sustainable_annual_giving']
        max_tax_advantaged_giving = capability['giving_capacity']['max_tax_advantaged_giving']
        
        # Calculate optimal annual giving amount (balancing tax efficiency and capacity)
        if current_giving < sustainable_annual_giving:
            if max_tax_advantaged_giving >= sustainable_annual_giving:
                # Can give at sustainable level with full tax advantage
                optimal_annual_giving = sustainable_annual_giving
            else:
                # Tax advantage limit is lower than sustainable capacity
                # Balance between tax efficiency and giving goals
                # Give slightly above tax advantage limit
                optimal_annual_giving = max_tax_advantaged_giving * 1.1
        else:
            # Already giving at or above sustainable level
            optimal_annual_giving = max(sustainable_annual_giving, max_tax_advantaged_giving)
            
        # Determine optimal giving vehicle for different giving amounts
        # Small regular donations
        if optimal_annual_giving < 500000:  # Less than 5 lakhs annually
            primary_vehicle = {
                'vehicle': 'Direct Donations',
                'type': 'Recurring',
                'frequency': 'Monthly or Quarterly',
                'annual_amount': round(optimal_annual_giving),
                'tax_efficiency': 'High',
                'administrative_complexity': 'Low',
                'implementation': [
                    "Set up automatic recurring donations",
                    "Maintain receipts for Section 80G deductions",
                    "Spread across 2-4 organizations aligned with values"
                ],
                'section_80g_benefit': round(min(optimal_annual_giving, max_tax_advantaged_giving) * tax_bracket)
            }
            
            secondary_vehicle = {
                'vehicle': 'Annual Major Gift',
                'type': 'Periodic',
                'frequency': 'Annual',
                'amount': round(optimal_annual_giving * 0.5),  # One large gift per year
                'tax_efficiency': 'High',
                'administrative_complexity': 'Low',
                'implementation': [
                    "Identify one organization for significant impact each year",
                    "Schedule annual gift at fiscal year-end for tax planning",
                    "Request impact report for larger donations"
                ]
            }
            
            legacy_component = None
            if giving_timeframe in ['bequest', 'both']:
                legacy_component = {
                    'vehicle': 'Charitable Bequest in Will',
                    'type': 'Testamentary',
                    'estimated_amount': round(total_assets * 0.05),  # 5% of assets
                    'tax_efficiency': 'Not Applicable',
                    'administrative_complexity': 'Low',
                    'implementation': [
                        "Include specific charitable bequests in will",
                        "Designate specific organizations or cause areas",
                        "Consider percentage-based bequest rather than fixed amount"
                    ]
                }
            
        # Medium-sized donations with more structure
        elif optimal_annual_giving < 2000000:  # Between 5-20 lakhs annually
            primary_vehicle = {
                'vehicle': 'Donor-Advised Fund Equivalent',
                'type': 'Structured',
                'frequency': 'Annual contribution with ongoing grants',
                'annual_contribution': round(optimal_annual_giving),
                'tax_efficiency': 'High',
                'administrative_complexity': 'Medium',
                'implementation': [
                    "Identify philanthropic advisor or specialized tax professional",
                    "Make annual contribution to structured giving vehicle",
                    "Direct grants to multiple organizations throughout year"
                ],
                'section_80g_benefit': round(min(optimal_annual_giving, max_tax_advantaged_giving) * tax_bracket)
            }
            
            secondary_vehicle = {
                'vehicle': 'Strategic Major Gifts',
                'type': 'Periodic',
                'frequency': 'Semi-annual',
                'amount_per_gift': round(optimal_annual_giving / 3),
                'tax_efficiency': 'High',
                'administrative_complexity': 'Medium',
                'implementation': [
                    "Select 2-3 focus organizations for deeper relationship",
                    "Schedule strategic conversations with nonprofit leadership",
                    "Target specific programs or initiatives for funding"
                ]
            }
            
            legacy_component = None
            if giving_timeframe in ['bequest', 'both']:
                legacy_component = {
                    'vehicle': 'Charitable Trust Bequest',
                    'type': 'Testamentary',
                    'estimated_amount': round(total_assets * 0.07),  # 7% of assets
                    'tax_efficiency': 'Not Applicable',
                    'administrative_complexity': 'Medium',
                    'implementation': [
                        "Establish testamentary charitable trust in estate plan",
                        "Define mission and governance structure",
                        "Appoint trusted individuals to oversee distributions"
                    ]
                }
            
        # Large donations with full structured approach
        else:  # Over 20 lakhs annually
            primary_vehicle = {
                'vehicle': 'Charitable Trust',
                'type': 'Structured',
                'frequency': 'Annual contribution with ongoing grants',
                'annual_contribution': round(optimal_annual_giving),
                'tax_efficiency': 'Highest',
                'administrative_complexity': 'High',
                'implementation': [
                    "Establish formal charitable trust with legal counsel",
                    "Develop grant-making strategy and governance structure",
                    "Consider professional administration or family office support"
                ],
                'section_80g_benefit': round(min(optimal_annual_giving, max_tax_advantaged_giving) * tax_bracket),
                'setup_cost': self.legacy_params['charitable_giving_options']['charitable_trust']['setup_cost']
            }
            
            secondary_vehicle = {
                'vehicle': 'Strategic Philanthropy Program',
                'type': 'Comprehensive',
                'component_strategies': [
                    "Core support for 2-3 primary organizations",
                    "Capacity building grants for emerging organizations",
                    "Matching gift programs to encourage others"
                ],
                'tax_efficiency': 'Highest',
                'administrative_complexity': 'High',
                'implementation': [
                    "Engage philanthropy consultant or hire dedicated staff",
                    "Develop theory of change and evaluation metrics",
                    "Consider collaborative funding with other donors"
                ]
            }
            
            legacy_component = None
            if giving_timeframe in ['bequest', 'both']:
                legacy_component = {
                    'vehicle': 'Endowed Foundation',
                    'type': 'Perpetual',
                    'estimated_amount': round(total_assets * 0.1),  # 10% of assets
                    'tax_efficiency': 'Not Applicable',
                    'administrative_complexity': 'Highest',
                    'implementation': [
                        "Create detailed foundation charter and governance",
                        "Define multi-generational succession plan",
                        "Establish investment policy for perpetual operation"
                    ]
                }
        
        # Optimize allocation across cause areas if specified
        cause_allocation = {}
        if charitable_interests:
            # Calculate allocation percentages based on prioritization
            # Equally distribute if no priorities given
            allocation_per_cause = 1.0 / len(charitable_interests)
            
            for cause in charitable_interests:
                cause_name = cause.get('name', 'General Giving')
                priority = cause.get('priority', 'medium')
                
                # Adjust allocation based on priority
                priority_factor = 1.0
                if priority.lower() == 'high':
                    priority_factor = 1.5
                elif priority.lower() == 'low':
                    priority_factor = 0.7
                    
                # Initial allocation with priority adjustment
                cause_allocation[cause_name] = allocation_per_cause * priority_factor
            
            # Normalize to ensure sum is 100%
            total_allocation = sum(cause_allocation.values())
            for cause in cause_allocation:
                cause_allocation[cause] = cause_allocation[cause] / total_allocation
        else:
            cause_allocation['General Charitable Giving'] = 1.0
        
        # Create implementation timeline
        implementation_timeline = []
        
        # Setup phase
        setup_actions = []
        if optimal_annual_giving >= 2000000:
            setup_actions.append("Establish charitable trust or structured giving vehicle")
            setup_actions.append("Develop formal grant-making strategy and governance")
        else:
            setup_actions.append("Document charitable giving objectives and priorities")
            setup_actions.append("Research and select qualified donation recipients")
            
        implementation_timeline.append({
            'phase': 1,
            'timeframe': 'Near-term (1-3 months)',
            'actions': setup_actions
        })
        
        # Implementation phase
        implementation_actions = []
        implementation_actions.append(f"Implement {primary_vehicle['frequency'].lower()} giving schedule")
        if 'setup_cost' in primary_vehicle:
            implementation_actions.append("Complete legal documentation and registration")
            
        implementation_timeline.append({
            'phase': 2,
            'timeframe': 'Medium-term (3-6 months)',
            'actions': implementation_actions
        })
        
        # Optimization phase
        optimization_actions = ["Review giving impact and tax efficiency annually"]
        if optimal_annual_giving >= 500000:
            optimization_actions.append("Develop impact measurement system")
            optimization_actions.append("Consider expanded strategic partnerships")
            
        implementation_timeline.append({
            'phase': 3,
            'timeframe': 'Long-term (6-12 months)',
            'actions': optimization_actions
        })
        
        # Return optimized strategy
        return {
            'optimized_giving_strategy': {
                'primary_vehicle': primary_vehicle,
                'secondary_vehicle': secondary_vehicle,
                'legacy_component': legacy_component,
                'cause_allocation': {cause: f"{round(percentage * 100)}%" for cause, percentage in cause_allocation.items()},
                'optimized_annual_giving': round(optimal_annual_giving),
                'expected_tax_savings': round(min(optimal_annual_giving, max_tax_advantaged_giving) * tax_bracket)
            },
            'implementation_timeline': implementation_timeline,
            'india_specific_considerations': {
                'section_80g_verification': "Verify 80G registration of recipient organizations",
                'donation_receipts': "Maintain proper receipts with PAN details for tax filing",
                'fcra_compliance': "For international charities, verify FCRA compliance",
                'csr_alignment': "Consider alignment with corporate CSR activities if applicable"
            },
            'optimization_rationale': "Strategy optimized for tax efficiency, giving capacity, and impact potential",
            'review_frequency': "Annual review recommended to adjust based on financial changes and impact assessment"
        }
    
    def optimize_wealth_transfer_plan(self, goal_data):
        """
        Optimize wealth transfer plan for efficient transfer to heirs
        while balancing tax, family, and legacy considerations.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with optimized wealth transfer plan
        """
        # Initialize the optimizer if needed
        self._initialize_optimizer()
        
        # Extract necessary information
        age = goal_data.get('age', 50)
        total_assets = goal_data.get('total_assets', 10000000)
        annual_income = goal_data.get('annual_income', 1200000)
        retirement_status = goal_data.get('retirement_status', 'pre_retirement')
        estate_components = goal_data.get('estate_components', {
            'liquid_assets': total_assets * 0.2,
            'property': total_assets * 0.4,
            'investments': total_assets * 0.3,
            'business': total_assets * 0.1
        })
        beneficiaries = goal_data.get('beneficiaries', [])
        wealth_transfer_plans = goal_data.get('wealth_transfer_plans', [])
        family_values = goal_data.get('family_values', [])
        succession_plans = goal_data.get('succession_plans', {})
        
        # Get wealth transfer impact assessment
        transfer_impact = self.evaluate_wealth_transfer_impact(goal_data)
        
        # Determine optimal transfer timing and vehicles
        # Based on donor financial security and asset composition
        donor_security = transfer_impact['donor_financial_security']['status']
        retirement_funding_ratio = transfer_impact['donor_financial_security']['retirement_funding_ratio'] / 100  # Convert from percentage
        illiquid_percentage = transfer_impact['wealth_transfer_assessment']['asset_liquidity_challenge']['illiquid_percentage'] / 100  # Convert from percentage
        
        # Calculate appropriate percentage of assets to transfer
        # First, ensure donor security
        if donor_security in ["At Risk", "Concerning"]:
            # Prioritize donor security, minimal transfers
            transfer_percentage = 0.05  # 5% of assets
            timing_strategy = "Minimal Current Transfers"
            transfer_rationale = "Donor financial security at risk; focus on securing retirement before significant transfers"
        elif donor_security in ["Adequate", "Progressing"]:
            # Modest transfers with caution
            transfer_percentage = 0.10  # 10% of assets
            timing_strategy = "Gradual Phased Transfers"
            transfer_rationale = "Building donor financial security while beginning modest transfers"
        else:  # Strong or Secure
            # More generous transfers possible
            transfer_percentage = 0.20  # 20% of assets
            timing_strategy = "Accelerated Transfer Program"
            transfer_rationale = "Strong donor financial position enables significant wealth transfer"
        
        # Adjust based on age and retirement status
        if age > 65 or retirement_status == 'retired':
            # Older donors may want to accelerate transfers
            transfer_percentage += 0.05
            
        # Adjust based on illiquid asset percentage
        if illiquid_percentage > 0.7:
            # Highly illiquid portfolio requires structured approach
            transfer_percentage -= 0.03
            
        # Calculate optimal transfer amount
        optimal_transfer_amount = total_assets * transfer_percentage
        
        # Determine optimal transfer vehicles based on asset composition and beneficiaries
        transfer_vehicles = []
        
        # 1. Annual gifting program - always include for tax efficiency
        annual_gift_limit = self.legacy_params['wealth_transfer_options']['gift']['annual_limit']
        eligible_beneficiaries = [b for b in beneficiaries if b.get('relationship', '').lower() not in ['charity', 'organization']]
        
        if eligible_beneficiaries:
            annual_gifting_capacity = annual_gift_limit * len(eligible_beneficiaries)
            annual_gifting_years = min(10, math.ceil((optimal_transfer_amount * 0.3) / annual_gifting_capacity))
            
            transfer_vehicles.append({
                'vehicle': 'Annual Gifting Program',
                'type': 'Lifetime Transfer',
                'allocation': f"{round(min(annual_gifting_capacity * annual_gifting_years, optimal_transfer_amount * 0.3))}",
                'allocation_percentage': round(min(annual_gifting_capacity * annual_gifting_years / optimal_transfer_amount, 0.3) * 100) if optimal_transfer_amount > 0 else 0,
                'tax_efficiency': 'High',
                'implementation': [
                    f"Annual gifts of ₹{annual_gift_limit} to {len(eligible_beneficiaries)} beneficiaries",
                    f"Program duration: {annual_gifting_years} years",
                    "Maintain proper gift deed documentation"
                ],
                'suitable_assets': ["Cash", "Marketable securities", "Small property interests"]
            })
        
        # 2. Trust structures - for larger or controlled transfers
        has_minor_children = any(b.get('age', 30) < 18 for b in beneficiaries)
        has_financially_immature = any(b.get('financial_maturity', 'moderate').lower() == 'low' for b in beneficiaries)
        
        if has_minor_children or has_financially_immature or total_assets > 30000000:
            transfer_vehicles.append({
                'vehicle': 'Family Trust Structure',
                'type': 'Controlled Transfer',
                'allocation': f"{round(optimal_transfer_amount * 0.4)}",
                'allocation_percentage': 40,
                'tax_efficiency': 'Medium',
                'implementation': [
                    "Establish family trust with appropriate controls",
                    "Transfer assets in phases according to trust provisions",
                    "Define milestone-based distribution criteria for beneficiaries"
                ],
                'suitable_assets': ["Investment portfolio", "Property with income potential", "Business interests (minority)"],
                'estimated_cost': self.legacy_params['estate_planning_options']['trust']['types']['revocable']['typical_cost']
            })
        
        # 3. Business succession plan - if applicable
        business_value = estate_components.get('business', 0)
        if business_value > 0 and business_value / total_assets > 0.1:
            transfer_vehicles.append({
                'vehicle': 'Business Succession Plan',
                'type': 'Structured Transition',
                'allocation': f"{round(business_value * 0.7)}",  # Transfer 70% of business value
                'allocation_percentage': round(business_value * 0.7 / optimal_transfer_amount * 100) if optimal_transfer_amount > 0 else 0,
                'tax_efficiency': 'Medium',
                'implementation': [
                    "Develop comprehensive business succession plan",
                    "Phase leadership and ownership transition over 3-7 years",
                    "Consider family business governance structure"
                ],
                'suitable_assets': ["Business interests", "Intellectual property", "Operational assets"],
                'estimated_cost': 75000
            })
        
        # 4. Education funding - for younger beneficiaries
        has_education_needs = any(b.get('age', 30) < 25 for b in beneficiaries)
        if has_education_needs:
            education_beneficiaries = [b for b in beneficiaries if b.get('age', 30) < 25]
            education_fund_amount = min(optimal_transfer_amount * 0.2, 500000 * len(education_beneficiaries))
            
            transfer_vehicles.append({
                'vehicle': 'Education Funding Program',
                'type': 'Targeted Support',
                'allocation': f"{round(education_fund_amount)}",
                'allocation_percentage': round(education_fund_amount / optimal_transfer_amount * 100) if optimal_transfer_amount > 0 else 0,
                'tax_efficiency': 'Medium',
                'implementation': [
                    f"Establish dedicated education funds for {len(education_beneficiaries)} beneficiaries",
                    "Consider direct payment to educational institutions for tax efficiency",
                    "Structure as trust or annual gifts depending on timeframe"
                ],
                'suitable_assets': ["Cash", "Fixed deposits", "Liquid investments"]
            })
        
        # 5. Testamentary transfers - balance through estate
        # Calculate remaining allocation after other vehicles
        allocated_percentage = sum(v.get('allocation_percentage', 0) for v in transfer_vehicles)
        remaining_percentage = max(0, 100 - allocated_percentage)
        
        if remaining_percentage > 5:
            transfer_vehicles.append({
                'vehicle': 'Testamentary Transfers',
                'type': 'Estate Distribution',
                'allocation': f"{round(optimal_transfer_amount * (remaining_percentage / 100))}",
                'allocation_percentage': round(remaining_percentage),
                'tax_efficiency': 'Medium',
                'implementation': [
                    "Document detailed wishes in comprehensive will",
                    "Consider specific bequests for family heirlooms and significant assets",
                    "Review and update approximately every 3-5 years"
                ],
                'suitable_assets': ["Remaining investment assets", "Personal property", "Family heirlooms"]
            })
        
        # Create beneficiary-specific strategies
        beneficiary_strategies = []
        
        for beneficiary in beneficiaries:
            beneficiary_age = beneficiary.get('age', 30)
            relationship = beneficiary.get('relationship', 'child')
            financial_maturity = beneficiary.get('financial_maturity', 'moderate')
            financial_need = beneficiary.get('financial_need', 'moderate')
            
            # Determine optimal transfer approach based on beneficiary characteristics
            if financial_maturity == 'low' or beneficiary_age < 25:
                # Use controlled, phased transfers
                transfer_approach = "Controlled Transfer with Milestones"
                approach_rationale = "Limited financial experience requires structured approach with gradual responsibility"
                
                primary_vehicles = ["Trust with age-based milestones", "Education funding", "Limited annual gifts"]
                
            elif financial_maturity == 'moderate':
                # Balance between control and autonomy
                transfer_approach = "Balanced Transfer Approach"
                approach_rationale = "Developing financial capability with appropriate guidance and partial autonomy"
                
                primary_vehicles = ["Mixed trust and direct transfers", "Annual gifting program", "Structured financial mentoring"]
                
            else:  # high financial maturity
                # Emphasize direct transfers
                transfer_approach = "Direct Transfer with Minimal Restrictions"
                approach_rationale = "Strong financial capability permits direct wealth transfer with minimal controls"
                
                primary_vehicles = ["Direct transfers", "Annual gifting program", "Business interest transfers if applicable"]
            
            # Adjust based on financial need
            if financial_need == 'high':
                primary_vehicles.append("Accelerated transfer timeline")
                approach_rationale += ", prioritized due to financial need"
            
            # Calculate target allocation for this beneficiary
            # Default to equal distribution among beneficiaries
            equal_share = optimal_transfer_amount / len(beneficiaries) if beneficiaries else 0
            
            # Adjust for relationship and need
            relationship_factor = 1.0
            if relationship.lower() == 'spouse':
                relationship_factor = 1.5  # Prioritize spouse
            elif relationship.lower() in ['parent', 'sibling']:
                relationship_factor = 0.8  # Slightly lower priority for parents/siblings
                
            need_factor = 1.0
            if financial_need == 'high':
                need_factor = 1.3
            elif financial_need == 'low':
                need_factor = 0.8
                
            target_allocation = equal_share * relationship_factor * need_factor
            
            beneficiary_strategies.append({
                'beneficiary': f"{relationship.title()} (Age {beneficiary_age})",
                'transfer_approach': transfer_approach,
                'approach_rationale': approach_rationale,
                'primary_vehicles': primary_vehicles,
                'target_allocation': round(target_allocation),
                'allocation_percentage': round(target_allocation / optimal_transfer_amount * 100, 1) if optimal_transfer_amount > 0 else 0,
                'suggested_timing': "Immediate start" if financial_need == 'high' else "Phased implementation"
            })
        
        # Create implementation timeline
        implementation_timeline = []
        
        # Phase 1: Planning and documentation
        phase1_actions = ["Complete estate planning documentation (will, trusts, powers of attorney)"]
        if any(v['vehicle'] == 'Annual Gifting Program' for v in transfer_vehicles):
            phase1_actions.append("Document annual gifting strategy and recipient prioritization")
        if any(v['vehicle'] == 'Business Succession Plan' for v in transfer_vehicles):
            phase1_actions.append("Draft comprehensive business succession plan")
            
        implementation_timeline.append({
            'phase': 1,
            'timeframe': 'Near-term (0-6 months)',
            'actions': phase1_actions
        })
        
        # Phase 2: Initial implementation
        phase2_actions = []
        if any(v['vehicle'] == 'Annual Gifting Program' for v in transfer_vehicles):
            phase2_actions.append("Begin annual gifting program to priority beneficiaries")
        if any(v['vehicle'] == 'Education Funding Program' for v in transfer_vehicles):
            phase2_actions.append("Establish education funding structures")
        if any(v['vehicle'] == 'Family Trust Structure' for v in transfer_vehicles):
            phase2_actions.append("Establish and fund initial family trust structure")
            
        implementation_timeline.append({
            'phase': 2,
            'timeframe': 'Medium-term (6-18 months)',
            'actions': phase2_actions
        })
        
        # Phase 3: Full implementation
        phase3_actions = []
        if any(v['vehicle'] == 'Business Succession Plan' for v in transfer_vehicles):
            phase3_actions.append("Begin phased business leadership and ownership transition")
        phase3_actions.append("Implement full wealth transfer framework across all vehicles")
        phase3_actions.append("Establish regular review process for transfer strategy")
            
        implementation_timeline.append({
            'phase': 3,
            'timeframe': 'Long-term (18-36 months)',
            'actions': phase3_actions
        })
        
        # Return optimized plan
        return {
            'optimized_wealth_transfer': {
                'optimal_transfer_timing': timing_strategy,
                'timing_rationale': transfer_rationale,
                'optimal_transfer_amount': round(optimal_transfer_amount),
                'transfer_percentage': round(transfer_percentage * 100, 1),
                'transfer_vehicles': transfer_vehicles,
                'beneficiary_strategies': beneficiary_strategies,
                'total_estimated_costs': sum(v.get('estimated_cost', 0) for v in transfer_vehicles)
            },
            'implementation_timeline': implementation_timeline,
            'india_specific_considerations': {
                'gift_documentation': "Proper gift deed documentation essential for substantial transfers",
                'succession_laws': "Consider personal law implications based on religion for inheritance matters",
                'stamp_duty': "Account for state-specific stamp duty on property transfers",
                'wealth_trends': "Family wealth transfer increasing in importance in India's growing economy"
            },
            'optimization_rationale': "Transfer plan optimized for donor security, tax efficiency, and beneficiary readiness",
            'recommendation_disclaimer': "This optimized plan represents a strategic framework; adapt based on changing circumstances and consult qualified professionals for implementation."
        }
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive legacy planning funding strategy with optimization
        and constraint assessments.
        
        Args:
            goal_data: Dictionary with legacy planning goal details
            
        Returns:
            Dictionary with comprehensive legacy planning strategy
        """
        # Initialize utility classes
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # Extract legacy planning specific information
        goal_type = goal_data.get('goal_type', 'estate_planning').lower()
        target_amount = goal_data.get('target_amount')
        time_horizon = goal_data.get('time_horizon', 5)
        risk_profile = goal_data.get('risk_profile', 'conservative')  # Usually conservative for legacy
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        
        # Extract legacy-specific details
        age = goal_data.get('age', 50)
        annual_income = goal_data.get('annual_income', 1200000)
        total_assets = goal_data.get('total_assets', 10000000)
        family_status = goal_data.get('family_status', 'married')
        estate_complexity = goal_data.get('estate_complexity', 'moderate')
        beneficiaries = goal_data.get('beneficiaries', [])
        estate_components = goal_data.get('estate_components', {
            'liquid_assets': total_assets * 0.2,
            'property': total_assets * 0.4,
            'investments': total_assets * 0.3,
            'business': total_assets * 0.1
        })
        
        # Calculate target amount if not provided
        if not target_amount:
            if goal_type in ('estate_planning', 'inheritance'):
                # Estimate estate planning costs
                target_amount = self.estimate_estate_planning_cost(
                    total_assets, estate_complexity, 
                    'complex' if family_status.lower() in ['married with children', 'children'] else 'simple'
                )
            elif goal_type == 'charitable_giving':
                # Use percentage of assets for charitable giving (default 5%)
                target_amount = total_assets * 0.05
            else:
                # Default for other legacy goals
                target_amount = total_assets * 0.10
        
        # Create legacy planning specific goal data
        legacy_goal = {
            'goal_type': goal_type,
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution
        }
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(legacy_goal)
        
        # Apply constraint assessments
        # 1. Assess estate planning readiness
        estate_readiness = self.assess_estate_planning_readiness(goal_data)
        
        # 2. Assess charitable giving capability
        charitable_capability = self.assess_charitable_giving_capability(goal_data)
        
        # 3. Evaluate wealth transfer impact
        wealth_transfer_impact = self.evaluate_wealth_transfer_impact(goal_data)
        
        # 4. Assess legacy planning integration
        planning_integration = self.assess_legacy_planning_integration(goal_data)
        
        # Apply optimization strategies
        # 1. Optimize estate planning structure
        optimized_estate_planning = self.optimize_estate_planning_structure(goal_data)
        
        # 2. Optimize charitable giving strategy
        optimized_charitable_giving = self.optimize_charitable_giving_strategy(goal_data)
        
        # 3. Optimize wealth transfer plan
        optimized_wealth_transfer = self.optimize_wealth_transfer_plan(goal_data)
        
        # Enhanced with legacy planning specific analyses
        enhanced_strategies = {}
        
        # Add specific strategy based on goal type
        if goal_type in ('estate_planning', 'inheritance', 'wealth_transfer'):
            # Create inheritance planning framework
            inheritance_planning = self.create_inheritance_planning_framework(
                total_assets, beneficiaries, estate_components
            )
            enhanced_strategies['inheritance_planning'] = inheritance_planning
            
        elif goal_type == 'charitable_giving':
            # Analyze charitable giving options
            charitable_analysis = self.analyze_charitable_giving_options(
                annual_income, target_amount, time_horizon
            )
            enhanced_strategies['charitable_giving'] = charitable_analysis
        
        # Always include general legacy planning allocations
        allocation_analysis = self.analyze_legacy_planning_allocations(
            total_assets, age, family_status
        )
        enhanced_strategies['legacy_allocation'] = allocation_analysis
        
        # Combine into comprehensive strategy
        strategy = {
            **base_strategy,
            'legacy_details': {
                'goal_type': goal_type,
                'age': age,
                'total_assets': round(total_assets),
                'family_status': family_status
            },
            'constraint_assessments': {
                'estate_planning_readiness': estate_readiness,
                'charitable_giving_capability': charitable_capability,
                'wealth_transfer_impact': wealth_transfer_impact,
                'legacy_planning_integration': planning_integration
            },
            'optimization_strategies': {
                'estate_planning_structure': optimized_estate_planning,
                'charitable_giving_strategy': optimized_charitable_giving,
                'wealth_transfer_plan': optimized_wealth_transfer
            },
            'legacy_planning_strategies': enhanced_strategies
        }
        
        # Add India-specific guidance
        strategy['india_specific_guidance'] = {
            'succession_laws': [
                "Consider applicable personal law system (Hindu, Muslim, Indian Succession Act)",
                "Document wealth transfer intentions clearly to avoid disputes under succession laws",
                "Tailor estate planning approach to religious and cultural traditions"
            ],
            'tax_planning': [
                "No inheritance or estate tax currently in India, but monitor potential future changes",
                "Utilize Section 80G deductions for charitable giving (up to 10% of income)",
                "Structure trusts efficiently considering income tax implications",
                "Plan for potential state-specific stamp duty on property transfers"
            ],
            'cultural_considerations': [
                "Balance modern estate planning with traditional family expectations",
                "Consider joint family property concepts in Hindu Undivided Family",
                "Anticipate generational differences in wealth management approaches",
                "Incorporate religious and community giving traditions (daan, zakat, charity)"
            ],
            'implementation_guidance': [
                "Engage qualified Indian estate planning professionals familiar with local laws",
                "Consider additional planning if NRI or foreign assets are involved",
                "Ensure proper documentation of all gifts and transfers",
                "Register all relevant documents properly according to state requirements"
            ]
        }
        
        # Add legacy planning specific advice
        strategy['specific_advice'] = {
            'prioritization': [
                "Ensure basic estate planning (will, power of attorney) is in place before complex planning",
                "Focus on personal financial security before extensive legacy planning",
                "Integrate legacy planning with retirement and other essential goals",
                "Consider annual giving for charitable goals while building long-term legacy"
            ],
            'implementation': [
                "Work with qualified legal and financial professionals",
                "Create clear documentation for all legacy plans",
                "Communicate plans with affected family members as appropriate",
                "Review and update plans regularly, especially after major life events"
            ],
            'investment_approach': [
                "Use more conservative investment approach for near-term legacy funding",
                "Consider specialized vehicles (trusts, insurance) for long-term legacy goals",
                "Balance tax efficiency with legacy planning objectives",
                "Ensure adequate liquidity for estate settlement costs"
            ]
        }
        
        # Integrate rebalancing strategy if profile data is available
        if 'profile_data' in goal_data:
            # Create profile data with legacy-specific information
            profile_data = {
                **goal_data['profile_data'],
                'age': age,
                'total_assets': total_assets
            }
            rebalancing_strategy = self.integrate_rebalancing_strategy(goal_data, profile_data)
            strategy['rebalancing_strategy'] = rebalancing_strategy
        
        return strategy