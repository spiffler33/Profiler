import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class EducationFundingStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for education goals with
    India-specific education planning concepts.
    """
    
    def __init__(self):
        """Initialize with education-specific parameters"""
        super().__init__()
        
        # Additional education-specific parameters
        self.education_params = {
            "education_inflation": 0.10,  # Education inflation rate (10%)
            "education_cost_estimates": {
                "india": {
                    "undergraduate": {
                        "engineering": {"public": 800000, "private": 1600000},
                        "medical": {"public": 1200000, "private": 6000000},
                        "arts_commerce": {"public": 300000, "private": 800000},
                        "management": {"public": 500000, "private": 2000000}
                    },
                    "postgraduate": {
                        "engineering": {"public": 300000, "private": 1000000},
                        "medical": {"public": 1500000, "private": 3000000},
                        "mba": {"public": 500000, "private": 2500000},
                        "arts_commerce": {"public": 200000, "private": 500000}
                    }
                },
                "abroad": {
                    "usa": {
                        "undergraduate": {"public": 8000000, "private": 17500000},
                        "postgraduate": {"public": 6000000, "private": 12000000}
                    },
                    "uk": {
                        "undergraduate": {"average": 7500000},
                        "postgraduate": {"average": 6000000}
                    },
                    "canada": {
                        "undergraduate": {"average": 6000000},
                        "postgraduate": {"average": 5000000}
                    },
                    "australia": {
                        "undergraduate": {"average": 6500000},
                        "postgraduate": {"average": 5500000}
                    },
                    "singapore": {
                        "undergraduate": {"average": 5000000},
                        "postgraduate": {"average": 4000000}
                    }
                }
            },
            "scholarship_opportunities": {
                "india": ["Merit-based", "Need-based", "Specific category scholarships"],
                "international": ["Fulbright", "Commonwealth", "University-specific"]
            },
            "education_loan_details": {
                "max_amount": {
                    "india": 7500000,
                    "abroad": 15000000
                },
                "interest_rates": {
                    "public_banks": {
                        "base_rate": 0.085,
                        "india_premium": 0,
                        "abroad_premium": 0.01
                    },
                    "private_banks": {
                        "base_rate": 0.095,
                        "india_premium": 0,
                        "abroad_premium": 0.01
                    }
                },
                "tax_benefits": {
                    "interest_deduction": "Full interest deduction for 8 years"
                }
            },
            "education_saving_schemes": {
                "sukanya_samriddhi": {
                    "eligible": "Girl child only",
                    "max_age": 10,
                    "interest_rate": 0.0775,
                    "max_tenure": 21,
                    "tax_status": "Tax-free"
                }
            },
            "optimization_params": {
                "scholarship_probability_weights": {
                    "excellent": 0.85,
                    "good": 0.65,
                    "average": 0.35,
                    "below_average": 0.15
                },
                "loan_optimizations": {
                    "min_self_funding": 0.3,  # Minimum 30% through savings
                    "max_loan_burden": 0.4,   # Maximum 40% of education cost through loans
                    "loan_tax_efficiency_threshold": 0.06  # Interest rate above which tax benefits justify higher loan
                },
                "funding_mix_priorities": {
                    "savings_weight": 0.5,    
                    "scholarship_weight": 0.3,
                    "loan_weight": 0.1,
                    "family_support_weight": 0.1
                }
            }
        }
        
        # Load education-specific parameters
        self._load_education_parameters()
        
    def _initialize_optimizer(self):
        """Initialize the StrategyOptimizer instance if not already initialized"""
        super()._initialize_optimizer()
        
    def _initialize_constraints(self):
        """Initialize the FundingConstraints instance if not already initialized"""
        super()._initialize_constraints()
        
    def _initialize_compound_strategy(self):
        """Initialize the CompoundStrategy instance if not already initialized"""
        super()._initialize_compound_strategy()
        
    def _load_education_parameters(self):
        """Load education-specific parameters from service"""
        if self.param_service:
            try:
                # Load education inflation
                edu_inflation = self.param_service.get_parameter('education_inflation')
                if edu_inflation:
                    self.education_params['education_inflation'] = edu_inflation
                
                # Load education cost estimates
                cost_estimates = self.param_service.get_parameter('education_cost_estimates')
                if cost_estimates:
                    self.education_params['education_cost_estimates'].update(cost_estimates)
                
                # Load scholarship opportunities
                scholarships = self.param_service.get_parameter('scholarship_opportunities')
                if scholarships:
                    self.education_params['scholarship_opportunities'].update(scholarships)
                
                # Load education loan details
                loan_details = self.param_service.get_parameter('education_loan_details')
                if loan_details:
                    self.education_params['education_loan_details'].update(loan_details)
                
                # Load education saving schemes
                saving_schemes = self.param_service.get_parameter('education_saving_schemes')
                if saving_schemes:
                    self.education_params['education_saving_schemes'].update(saving_schemes)
                
            except Exception as e:
                logger.error(f"Error loading education parameters: {e}")
                # Continue with default parameters
    
    def estimate_education_cost(self, course_type, field, location, institution_type="average",
                               current_age=None, education_age=None, years_to_education=None):
        """
        Estimate education cost based on course type, field, and location.
        
        Args:
            course_type: 'undergraduate' or 'postgraduate'
            field: Subject field (e.g., 'engineering', 'medical')
            location: 'india' or country name abroad
            institution_type: 'public', 'private', or 'average'
            current_age: Child's current age (optional)
            education_age: Age at which education starts (optional)
            years_to_education: Direct specification of years to education (overrides ages)
            
        Returns:
            Estimated education cost adjusted for inflation
        """
        # Determine base cost from parameters
        base_cost = 1000000  # Default fallback
        
        try:
            if location.lower() == 'india':
                if field.lower() in self.education_params['education_cost_estimates']['india'][course_type]:
                    if institution_type in self.education_params['education_cost_estimates']['india'][course_type][field.lower()]:
                        base_cost = self.education_params['education_cost_estimates']['india'][course_type][field.lower()][institution_type]
                    else:
                        # Use average if specific type not found
                        field_costs = self.education_params['education_cost_estimates']['india'][course_type][field.lower()]
                        base_cost = sum(field_costs.values()) / len(field_costs)
            else:
                # Check if country exists in abroad section
                if location.lower() in self.education_params['education_cost_estimates']['abroad']:
                    if institution_type in self.education_params['education_cost_estimates']['abroad'][location.lower()][course_type]:
                        base_cost = self.education_params['education_cost_estimates']['abroad'][location.lower()][course_type][institution_type]
                    else:
                        # Use average if specific type not found
                        base_cost = self.education_params['education_cost_estimates']['abroad'][location.lower()][course_type]['average']
                else:
                    # Use USA as reference if country not found
                    if institution_type in self.education_params['education_cost_estimates']['abroad']['usa'][course_type]:
                        base_cost = self.education_params['education_cost_estimates']['abroad']['usa'][course_type][institution_type]
                    else:
                        # Average of public and private
                        usa_costs = self.education_params['education_cost_estimates']['abroad']['usa'][course_type]
                        base_cost = sum(usa_costs.values()) / len(usa_costs)
        except KeyError:
            logger.warning(f"Education cost estimation failed for {course_type}, {field}, {location}. Using default.")
        
        # Calculate years to education
        if years_to_education is None:
            if current_age is not None and education_age is not None:
                years_to_education = max(0, education_age - current_age)
            else:
                years_to_education = 0  # Default to immediate
        
        # Adjust for education inflation
        education_inflation = self.education_params['education_inflation']
        adjusted_cost = base_cost * ((1 + education_inflation) ** years_to_education)
        
        return adjusted_cost
    
    def evaluate_sukanya_samriddhi(self, child_age, is_girl, time_horizon, target_amount):
        """
        Evaluate Sukanya Samriddhi Yojana as an education funding option.
        
        Args:
            child_age: Age of the child in years
            is_girl: Boolean indicating if child is a girl
            time_horizon: Years to education goal
            target_amount: Education goal amount
            
        Returns:
            Dictionary with SSY evaluation details or None if not applicable
        """
        if not is_girl:
            return None  # SSY only applicable for girl children
            
        max_age = self.education_params['education_saving_schemes']['sukanya_samriddhi']['max_age']
        if child_age > max_age:
            return None  # Child too old for SSY
            
        interest_rate = self.education_params['education_saving_schemes']['sukanya_samriddhi']['interest_rate']
        max_tenure = self.education_params['education_saving_schemes']['sukanya_samriddhi']['max_tenure']
        
        # SSY matures when the girl is 21, calculate how that aligns with education goal
        years_to_maturity = 21 - child_age
        
        # Calculate maximum annual contribution (1.5 lakhs)
        max_annual = 150000
        
        # Calculate future value of maximum annual contribution
        future_value = max_annual * (((1 + interest_rate) ** years_to_maturity - 1) / interest_rate)
        
        # Calculate required annual contribution for target
        required_annual = min(max_annual, target_amount / (((1 + interest_rate) ** years_to_maturity - 1) / interest_rate))
        
        # Determine if SSY will be available for education (partial withdrawal at 18)
        available_for_education = child_age + time_horizon >= 18
        
        # Early withdrawal rules - 50% at 18 for education
        partial_withdrawal_age = 18
        years_to_partial = max(0, partial_withdrawal_age - child_age)
        
        # Calculate value at partial withdrawal
        partial_value = required_annual * (((1 + interest_rate) ** years_to_partial - 1) / interest_rate)
        
        return {
            'scheme': 'Sukanya Samriddhi Yojana',
            'eligible': True,
            'years_to_maturity': years_to_maturity,
            'interest_rate': interest_rate * 100,  # Convert to percentage
            'max_annual_contribution': max_annual,
            'recommended_annual_contribution': round(required_annual),
            'projected_value_at_maturity': round(future_value),
            'percent_of_target': round((future_value / target_amount) * 100, 1),
            'education_withdrawal': {
                'available': available_for_education,
                'withdrawal_age': partial_withdrawal_age,
                'years_to_withdrawal': years_to_partial,
                'estimated_withdrawal_value': round(partial_value * 0.5)  # 50% allowed
            },
            'tax_benefits': 'Tax exempt under Section 80C for contributions, and completely tax-free on maturity',
            'considerations': [
                'Annual contributions required for 14 years or until maturity',
                'Early withdrawal of 50% possible at age 18 for education',
                'Full withdrawal only at maturity (21 years)',
                'Interest rates may change over time'
            ]
        }
    
    def calculate_education_loan_eligibility(self, annual_income, course_type, location, existing_obligations=0):
        """
        Calculate education loan eligibility based on income and course details.
        
        Args:
            annual_income: Annual family income
            course_type: Type of course ('undergraduate' or 'postgraduate')
            location: Location of education ('india' or country abroad)
            existing_obligations: Existing loan obligations (monthly)
            
        Returns:
            Dictionary with loan eligibility details
        """
        # Determine maximum loan amount
        max_amount = self.education_params['education_loan_details']['max_amount']
        if location.lower() == 'india':
            loan_limit = max_amount['india']
        else:
            loan_limit = max_amount['abroad']
        
        # Calculate eligibility based on income (typically 10-15 times annual income)
        income_based_limit = annual_income * 12
        
        # Adjust for existing obligations
        # Typically, total EMI shouldn't exceed 50% of monthly income
        monthly_income = annual_income / 12
        available_for_emi = monthly_income * 0.5 - existing_obligations
        
        # Assuming education loan for 10 years (120 months) at typical interest rate
        if location.lower() == 'india':
            interest_rate = self.education_params['education_loan_details']['interest_rates']['public_banks']['base_rate']
        else:
            interest_rate = (self.education_params['education_loan_details']['interest_rates']['public_banks']['base_rate'] + 
                           self.education_params['education_loan_details']['interest_rates']['public_banks']['abroad_premium'])
        
        # Monthly interest rate
        monthly_rate = interest_rate / 12
        
        # Calculate loan amount based on affordable EMI
        # Using formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        # Solving for P: P = EMI * ((1+r)^n - 1) / (r * (1+r)^n)
        term_months = 120  # 10 years
        emi_based_limit = available_for_emi * ((1 + monthly_rate) ** term_months - 1) / (monthly_rate * (1 + monthly_rate) ** term_months)
        
        # Final eligibility is minimum of all limits
        eligible_amount = min(loan_limit, income_based_limit, emi_based_limit)
        
        # Calculate typical EMI for this amount
        # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        typical_emi = eligible_amount * monthly_rate * (1 + monthly_rate) ** term_months / ((1 + monthly_rate) ** term_months - 1)
        
        # Get interest rates for public and private banks
        public_rate = (self.education_params['education_loan_details']['interest_rates']['public_banks']['base_rate'] + 
                      (0 if location.lower() == 'india' else self.education_params['education_loan_details']['interest_rates']['public_banks']['abroad_premium']))
        
        private_rate = (self.education_params['education_loan_details']['interest_rates']['private_banks']['base_rate'] + 
                       (0 if location.lower() == 'india' else self.education_params['education_loan_details']['interest_rates']['private_banks']['abroad_premium']))
        
        return {
            'eligible_loan_amount': round(eligible_amount),
            'loan_term_years': 10,
            'interest_rates': {
                'public_banks': round(public_rate * 100, 2),  # Convert to percentage
                'private_banks': round(private_rate * 100, 2)  # Convert to percentage
            },
            'estimated_monthly_emi': round(typical_emi),
            'percentage_of_monthly_income': round(typical_emi / monthly_income * 100, 1),
            'tax_benefits': self.education_params['education_loan_details']['tax_benefits'],
            'considerations': [
                'No collateral usually required for loans up to ₹7.5 lakhs',
                'Collateral or guarantor required for higher amounts',
                'Moratorium period available during course plus 6 months to 1 year',
                'Interest subsidy may be available for economically weaker sections'
            ]
        }
    
    def analyze_scholarship_opportunities(self, course_type, field, location, academic_profile='average'):
        """
        Analyze potential scholarship opportunities based on course and profile.
        
        Args:
            course_type: 'undergraduate' or 'postgraduate'
            field: Subject field
            location: Education location
            academic_profile: 'excellent', 'good', 'average', or 'below_average'
            
        Returns:
            Dictionary with scholarship analysis
        """
        # Determine scholarship likelihood based on academic profile
        likelihood = {
            'excellent': 0.75,
            'good': 0.50,
            'average': 0.25,
            'below_average': 0.10
        }.get(academic_profile, 0.25)
        
        # Adjust likelihood based on field (some fields have more scholarships)
        field_adjustment = {
            'engineering': 1.2,
            'medical': 1.1,
            'science': 1.3,
            'arts': 0.9,
            'commerce': 0.8,
            'management': 0.9
        }.get(field.lower(), 1.0)
        
        likelihood *= field_adjustment
        
        # Determine potential scholarship types
        if location.lower() == 'india':
            available_scholarships = self.education_params['scholarship_opportunities']['india']
        else:
            available_scholarships = self.education_params['scholarship_opportunities']['international']
        
        # Estimate potential coverage percentage
        if academic_profile == 'excellent':
            potential_coverage = 0.5  # Up to 50% coverage
        elif academic_profile == 'good':
            potential_coverage = 0.3  # Up to 30% coverage
        elif academic_profile == 'average':
            potential_coverage = 0.15  # Up to 15% coverage
        else:
            potential_coverage = 0.05  # Up to 5% coverage
        
        # Adjust for location (international often has more generous scholarships)
        if location.lower() != 'india':
            potential_coverage *= 1.2
        
        # Specific scholarship opportunities
        specific_opportunities = []
        
        if location.lower() == 'india':
            specific_opportunities.extend([
                "KVPY for science students",
                "Central Sector Scholarship",
                "INSPIRE Scholarship",
                "Institution-specific merit scholarships"
            ])
            
            # Field-specific scholarships in India
            if field.lower() == 'engineering':
                specific_opportunities.extend([
                    "AICTE Scholarship",
                    "GATE Scholarship for PG studies"
                ])
            elif field.lower() == 'medical':
                specific_opportunities.append("ICMR Scholarship")
        else:
            specific_opportunities.extend([
                "Fulbright Scholarship (for USA)",
                "Commonwealth Scholarship (for UK and Commonwealth countries)",
                "University-specific scholarships",
                "Country-specific government scholarships"
            ])
        
        return {
            'scholarship_likelihood': f"{round(likelihood * 100)}%",
            'potential_coverage': f"{round(potential_coverage * 100)}%",
            'available_scholarship_types': available_scholarships,
            'specific_opportunities': specific_opportunities,
            'application_timeline': "12-18 months before course start",
            'requirements_checklist': [
                "Academic transcripts",
                "Recommendation letters",
                "Statement of purpose",
                "Standardized test scores",
                "Financial need documentation"
            ],
            'strategy': [
                "Apply early and to multiple scholarships",
                "Prepare strong application materials",
                "Research institution-specific opportunities",
                "Consider financial need-based and merit-based options",
                "Maintain academic excellence throughout"
            ]
        }
    
    def recommend_education_allocation(self, time_horizon, child_age=None):
        """
        Recommend asset allocation specifically for education goal.
        
        Args:
            time_horizon: Years to education goal
            child_age: Age of child (optional)
            
        Returns:
            Dictionary with recommended asset allocation
        """
        # Use base allocation as starting point
        allocation = self.recommend_allocation(time_horizon, 'moderate')
        
        # Adjust for education-specific strategy
        if time_horizon > 15:
            # For very long horizons (young children), increase equity slightly
            allocation['equity'] = min(allocation['equity'] * 1.1, 0.75)
            
            # Adjust other allocations to maintain total of 1.0
            total = sum(allocation.values())
            if total > 1.0:
                # Scale down proportionally
                for asset in allocation:
                    allocation[asset] = allocation[asset] / total
        elif time_horizon < 3:
            # For near-term education needs, focus on safety
            allocation['equity'] = min(allocation['equity'], 0.2)
            allocation['debt'] = 0.6
            allocation['cash'] = 0.2
            allocation['gold'] = 0.0
            allocation['alternatives'] = 0.0
        
        return allocation
    
    def create_education_funding_plan(self, goal_data):
        """
        Create detailed education funding plan with multiple options.
        
        Args:
            goal_data: Dictionary with education goal details
            
        Returns:
            Dictionary with comprehensive education funding plan
        """
        # Extract education-specific information
        course_type = goal_data.get('course_type', 'undergraduate')
        field = goal_data.get('field', 'general')
        location = goal_data.get('location', 'india')
        institution_type = goal_data.get('institution_type', 'average')
        child_age = goal_data.get('child_age')
        education_age = goal_data.get('education_age')
        time_horizon = goal_data.get('time_horizon')
        is_girl = goal_data.get('is_girl', False)
        academic_profile = goal_data.get('academic_profile', 'average')
        annual_income = goal_data.get('annual_income', 1200000)
        
        # Determine years to education if not provided
        if time_horizon is None and child_age is not None and education_age is not None:
            time_horizon = max(0, education_age - child_age)
        
        # Estimate education cost
        estimated_cost = self.estimate_education_cost(
            course_type, field, location, institution_type,
            child_age, education_age, time_horizon
        )
        
        # Evaluate Sukanya Samriddhi Yojana if applicable
        ssy_evaluation = None
        if is_girl and child_age is not None:
            ssy_evaluation = self.evaluate_sukanya_samriddhi(
                child_age, is_girl, time_horizon, estimated_cost
            )
        
        # Calculate loan eligibility
        loan_eligibility = self.calculate_education_loan_eligibility(
            annual_income, course_type, location
        )
        
        # Analyze scholarship opportunities
        scholarship_analysis = self.analyze_scholarship_opportunities(
            course_type, field, location, academic_profile
        )
        
        # Calculate funding required after scholarships
        # Assume midpoint of potential scholarship coverage
        scholarship_coverage = float(scholarship_analysis['potential_coverage'].strip('%')) / 100
        funding_after_scholarships = estimated_cost * (1 - scholarship_coverage / 2)
        
        # Calculate funding options: Savings, SSY, Loan
        savings_requirement = funding_after_scholarships
        
        # Adjust if SSY is applicable
        ssy_contribution = 0
        if ssy_evaluation and ssy_evaluation['education_withdrawal']['available']:
            ssy_contribution = ssy_evaluation['education_withdrawal']['estimated_withdrawal_value']
            savings_requirement -= ssy_contribution
        
        # Determine recommended loan component
        recommended_loan = 0
        if time_horizon < 5:
            # For short horizons, loan may be necessary
            recommended_loan = min(funding_after_scholarships * 0.4, loan_eligibility['eligible_loan_amount'])
            savings_requirement -= recommended_loan
        
        # Calculate required monthly investment for savings
        required_monthly = 0
        if savings_requirement > 0 and time_horizon > 0:
            # Get allocation and expected return
            allocation = self.recommend_education_allocation(time_horizon, child_age)
            expected_return = self.get_expected_return(allocation)
            
            required_monthly = self.calculate_monthly_investment(
                savings_requirement, time_horizon, expected_return
            )
        
        # Compile funding plan
        funding_plan = {
            'estimated_education_cost': round(estimated_cost),
            'time_horizon': time_horizon,
            'course_details': {
                'course_type': course_type,
                'field': field,
                'location': location,
                'institution_type': institution_type
            },
            'funding_options': {
                'personal_savings': {
                    'amount': round(savings_requirement),
                    'percentage_of_total': round(savings_requirement / estimated_cost * 100, 1),
                    'required_monthly_investment': round(required_monthly),
                    'recommended_allocation': self.recommend_education_allocation(time_horizon, child_age),
                    'expected_return': round(self.get_expected_return(self.recommend_education_allocation(time_horizon, child_age)) * 100, 2)
                },
                'scholarship_potential': {
                    'estimated_coverage': scholarship_analysis['potential_coverage'],
                    'amount': round(estimated_cost * scholarship_coverage / 2),
                    'likelihood': scholarship_analysis['scholarship_likelihood']
                }
            }
        }
        
        # Add SSY component if applicable
        if ssy_evaluation:
            funding_plan['funding_options']['sukanya_samriddhi'] = {
                'applicable': ssy_evaluation['eligible'],
                'contribution_to_education': round(ssy_contribution),
                'percentage_of_total': round(ssy_contribution / estimated_cost * 100, 1),
                'recommended_annual_contribution': ssy_evaluation['recommended_annual_contribution'],
                'details': ssy_evaluation
            }
        
        # Add loan component
        funding_plan['funding_options']['education_loan'] = {
            'recommended_amount': round(recommended_loan),
            'percentage_of_total': round(recommended_loan / estimated_cost * 100, 1),
            'eligibility_details': loan_eligibility
        }
        
        # Add detailed scholarship analysis
        funding_plan['scholarship_opportunities'] = scholarship_analysis
        
        return funding_plan
    
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy tailored for education goals.
        
        Education goals typically have a defined timeline with a specific end date.
        The rebalancing approach becomes progressively more conservative as the
        education start date approaches, with consideration for Indian academic calendars.
        
        Args:
            goal_data: Dictionary with education goal details
            profile_data: Dictionary with user profile information
            
        Returns:
            Dictionary with education-specific rebalancing strategy
        """
        # Create rebalancing instance
        rebalancing = RebalancingStrategy()
        
        # Extract education-specific information
        child_age = goal_data.get('child_age')
        education_age = goal_data.get('education_age')
        time_horizon = goal_data.get('time_horizon')
        current_savings = goal_data.get('current_savings', 0)
        
        # Determine years to education if not directly provided
        if time_horizon is None and child_age is not None and education_age is not None:
            time_horizon = max(0, education_age - child_age)
        elif time_horizon is None:
            time_horizon = 10  # Default assumption
        
        # If profile data not provided, create minimal profile
        if not profile_data:
            profile_data = {
                'risk_profile': goal_data.get('risk_profile', 'moderate'),
                'portfolio_value': current_savings,
                'market_volatility': 'normal'
            }
        
        # Get education-specific asset allocation
        allocation = self.recommend_education_allocation(time_horizon, child_age)
        
        # Create goal data specifically for rebalancing
        rebalancing_goal = {
            'goal_type': 'education',
            'time_horizon': time_horizon,
            'target_allocation': allocation,
            'current_allocation': goal_data.get('current_allocation', allocation),
            'priority_level': 'high'  # Education is typically high priority
        }
        
        # Design rebalancing schedule
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(
            rebalancing_goal, profile_data
        )
        
        # Calculate timeline-based drift thresholds
        # More aggressive for longer horizons, more conservative near education start
        timeline_threshold_factor = 1.0
        if time_horizon > 10:
            timeline_threshold_factor = 1.3  # 30% wider when far from education start
        elif time_horizon > 5:
            timeline_threshold_factor = 1.1  # 10% wider
        elif time_horizon > 2:
            timeline_threshold_factor = 0.9  # 10% tighter
        else:
            timeline_threshold_factor = 0.7  # 30% tighter when close to education start
        
        # Customize drift thresholds for education strategy
        custom_thresholds = {
            'equity': 0.05 * timeline_threshold_factor,
            'debt': 0.03 * timeline_threshold_factor,
            'gold': 0.02 * timeline_threshold_factor,
            'alternatives': 0.07 * timeline_threshold_factor,
            'cash': 0.01  # Keep cash threshold constant regardless of timeline
        }
        
        drift_thresholds = rebalancing.calculate_drift_thresholds(custom_thresholds)
        
        # Calculate Indian academic calendar considerations
        current_month = datetime.now().month
        # Standard Indian academic year starts in June/July
        months_to_academic_year = (6 - current_month) % 12
        
        # Create education-specific rebalancing strategy
        education_rebalancing = {
            'goal_type': 'education',
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': drift_thresholds,
            'education_specific_considerations': {
                'academic_calendar_sync': 'Align rebalancing with academic calendar cycles',
                'fee_payment_timing': 'Ensure liquidity ahead of standard fee payment periods',
                'progressive_risk_reduction': 'Gradually reduce risk as education start date approaches'
            },
            'implementation_priorities': [
                'Schedule major rebalancing 3-4 months before fee payment cycles',
                'Maintain sufficient liquidity for upcoming semester payments',
                'Progressive risk reduction as education date approaches',
                'Focus on capital protection in final year before education starts'
            ]
        }
        
        # Add special SSY considerations for girl child
        if goal_data.get('is_girl', False) and child_age is not None and child_age <= 10:
            education_rebalancing['ssy_integration'] = {
                'approach': 'Include SSY as part of overall education funding strategy',
                'rebalancing_impact': 'Treat SSY as separate allocation outside regular rebalancing',
                'withdrawal_timing': 'Plan for partial withdrawal at age 18 to align with education needs',
                'considerations': 'Coordinate SSY withdrawals with overall investment drawdown schedule'
            }
        
        return education_rebalancing
    
    def optimize_funding_mix(self, goal_data, education_plan):
        """
        Optimize the funding mix between savings, scholarships, and loans.
        
        Args:
            goal_data: Dictionary with education goal details
            education_plan: Education funding plan with options
            
        Returns:
            Optimized funding mix
        """
        # Initialize optimizer if needed
        self._initialize_optimizer()
        
        # Extract key parameters
        estimated_cost = education_plan['estimated_education_cost']
        time_horizon = education_plan['time_horizon']
        scholarship_likelihood = float(education_plan['funding_options']['scholarship_potential']['likelihood'].strip('%')) / 100
        scholarship_amount = education_plan['funding_options']['scholarship_potential']['amount']
        loan_eligibility = education_plan['funding_options']['education_loan']['eligibility_details']['eligible_loan_amount']
        academic_profile = goal_data.get('academic_profile', 'average')
        is_girl = goal_data.get('is_girl', False)
        annual_income = goal_data.get('annual_income', 1200000)
        tax_bracket = goal_data.get('tax_bracket', 0.30)
        
        # Get optimization parameters
        min_self_funding_pct = self.education_params['optimization_params']['loan_optimizations']['min_self_funding']
        max_loan_burden_pct = self.education_params['optimization_params']['loan_optimizations']['max_loan_burden']
        
        # Determine scholarship weight based on academic profile
        scholarship_weights = self.education_params['optimization_params']['scholarship_probability_weights']
        scholarship_weight = scholarship_weights.get(academic_profile, 0.35)
        
        # Base funding mix
        funding_mix = {
            'savings': {
                'amount': education_plan['funding_options']['personal_savings']['amount'],
                'percentage': education_plan['funding_options']['personal_savings']['percentage_of_total'],
                'monthly_investment': education_plan['funding_options']['personal_savings']['required_monthly_investment']
            },
            'scholarship': {
                'amount': scholarship_amount,
                'percentage': round(scholarship_amount / estimated_cost * 100, 1),
                'probability': scholarship_likelihood
            },
            'loan': {
                'amount': education_plan['funding_options']['education_loan']['recommended_amount'],
                'percentage': education_plan['funding_options']['education_loan']['percentage_of_total'],
                'max_eligible': loan_eligibility
            }
        }
        
        # Add SSY if applicable
        if is_girl and 'sukanya_samriddhi' in education_plan['funding_options']:
            ssy_contribution = education_plan['funding_options']['sukanya_samriddhi']['contribution_to_education']
            funding_mix['sukanya_samriddhi'] = {
                'amount': ssy_contribution,
                'percentage': round(ssy_contribution / estimated_cost * 100, 1),
                'annual_contribution': education_plan['funding_options']['sukanya_samriddhi']['recommended_annual_contribution']
            }
        
        # Optimize based on different scenarios
        optimized_mix = {}
        
        # 1. Calculate minimum self-funding requirement
        min_self_funding = estimated_cost * min_self_funding_pct
        
        # 2. Calculate maximum loan amount based on burden threshold
        max_loan = min(loan_eligibility, estimated_cost * max_loan_burden_pct)
        
        # 3. Adjust scholarship expectation based on academic profile
        adjusted_scholarship = scholarship_amount * scholarship_weight
        
        # 4. Calculate funding gap after expected scholarship and maximum loan
        funding_gap = estimated_cost - adjusted_scholarship - max_loan
        
        # 5. If funding gap < min_self_funding, increase self-funding
        if funding_gap < min_self_funding:
            required_self_funding = min_self_funding
        else:
            required_self_funding = funding_gap
        
        # 6. If loan has tax advantages, consider increasing loan portion
        if 'interest_rates' in education_plan['funding_options']['education_loan']['eligibility_details']:
            interest_rate = education_plan['funding_options']['education_loan']['eligibility_details']['interest_rates']['public_banks'] / 100
            loan_tax_efficiency = self.education_params['optimization_params']['loan_optimizations']['loan_tax_efficiency_threshold']
            
            if interest_rate > loan_tax_efficiency and tax_bracket > 0.2:
                # Increase loan portion for tax efficiency
                tax_efficient_loan = min(max_loan * 1.2, loan_eligibility)
                required_self_funding = max(min_self_funding, estimated_cost - adjusted_scholarship - tax_efficient_loan)
                optimized_mix['tax_optimization'] = {
                    'applied': True,
                    'rationale': f"Increased loan portion due to interest rate ({interest_rate:.1%}) exceeding tax efficiency threshold ({loan_tax_efficiency:.1%}) and high tax bracket ({tax_bracket:.0%})"
                }
        
        # Create optimized funding mix
        optimized_mix['funding_distribution'] = {
            'savings': {
                'amount': round(required_self_funding),
                'percentage': round(required_self_funding / estimated_cost * 100, 1),
                'monthly_investment': round(self.calculate_monthly_investment(
                    required_self_funding, time_horizon, 
                    self.get_expected_return(self.recommend_education_allocation(time_horizon, goal_data.get('child_age')))
                ))
            },
            'scholarship': {
                'expected_amount': round(adjusted_scholarship),
                'percentage': round(adjusted_scholarship / estimated_cost * 100, 1),
                'probability_adjusted': f"{round(scholarship_likelihood * scholarship_weight * 100)}%"
            },
            'loan': {
                'recommended_amount': round(min(max_loan, estimated_cost - required_self_funding - adjusted_scholarship)),
                'percentage': round(min(max_loan, estimated_cost - required_self_funding - adjusted_scholarship) / estimated_cost * 100, 1)
            }
        }
        
        # Add SSY if applicable
        if 'sukanya_samriddhi' in funding_mix:
            optimized_mix['funding_distribution']['sukanya_samriddhi'] = funding_mix['sukanya_samriddhi']
        
        # Add overall funding plan recommendation
        optimized_mix['recommendation'] = {
            'prioritization': [
                "Focus on building sufficient savings to cover minimum self-funding requirement",
                "Actively pursue scholarship opportunities to reduce overall cost",
                "Plan for loan application as education date approaches"
            ],
            'contingency_plans': [
                "If scholarship expectations aren't met, increase savings rate",
                "Consider larger loan if tax benefits justify it",
                "Explore part-time work options to supplement funding"
            ]
        }
        
        return optimized_mix
        
    def assess_education_budget_feasibility(self, strategy, profile_data, child_age=None, education_age=None):
        """
        Assess feasibility of education strategy with India-specific considerations.
        
        Args:
            strategy: Education funding strategy to assess
            profile_data: User profile with income and expense information
            child_age: Current age of child (optional)
            education_age: Age at which education starts (optional)
            
        Returns:
            Dictionary with education-specific feasibility assessment
        """
        # Initialize constraints if needed
        self._initialize_constraints()
        
        if not strategy or not profile_data:
            return None
            
        # Extract relevant profile information
        monthly_income = profile_data.get('monthly_income', 0)
        annual_income = monthly_income * 12 if monthly_income else profile_data.get('annual_income', 0)
        if not monthly_income and not annual_income:
            logger.warning("Missing income data, cannot assess education feasibility")
            return None
            
        if not monthly_income:
            monthly_income = annual_income / 12
            
        # Extract education parameters
        education_cost = strategy.get('education_details', {}).get('estimated_cost', 0)
        course_type = strategy.get('education_details', {}).get('course_type', 'undergraduate')
        field = strategy.get('education_details', {}).get('field', 'general')
        location = strategy.get('education_details', {}).get('location', 'india')
        time_horizon = strategy.get('time_horizon', 10)
        
        # Determine years to education if using ages
        if time_horizon <= 0 and child_age is not None and education_age is not None:
            time_horizon = max(0, education_age - child_age)
        
        # Get funding requirements
        monthly_investment = strategy.get('recommendation', {}).get('total_monthly_investment', 0)
        
        # Calculate as percentage of income
        contribution_percent = monthly_investment / monthly_income if monthly_income > 0 else 0
        
        # Initialize feasibility assessment
        feasibility = {
            'is_feasible': True,
            'education_cost_assessment': {
                'estimated_cost': round(education_cost),
                'annual_income': round(annual_income),
                'cost_to_income_ratio': round(education_cost / annual_income, 1),
                'status': 'reasonable' if education_cost <= annual_income * 3 else 'high'
            },
            'funding_requirement_assessment': {
                'monthly_investment': round(monthly_investment),
                'percent_of_income': round(contribution_percent * 100, 1),
                'status': 'manageable' if contribution_percent < 0.25 else 'challenging'
            },
            'timeline_assessment': {
                'years_to_education': time_horizon,
                'status': 'adequate' if time_horizon >= 3 else 'compressed'
            },
            'recommendations': []
        }
        
        # Assess cost reasonableness
        if education_cost > annual_income * 5:
            feasibility['is_feasible'] = False
            feasibility['education_cost_assessment']['status'] = 'excessive'
            feasibility['recommendations'].append(
                f"Education cost ({round(education_cost/100000)/10} lakhs) is extremely high relative to income ({round(annual_income/100000)/10} lakhs annual). Consider less expensive alternatives."
            )
        elif education_cost > annual_income * 3:
            feasibility['recommendations'].append(
                f"Education cost ({round(education_cost/100000)/10} lakhs) is high relative to income ({round(annual_income/100000)/10} lakhs annual). Consider supplementing with scholarships and loans."
            )
        
        # Assess funding burden
        if contribution_percent > 0.4:
            feasibility['is_feasible'] = False
            feasibility['funding_requirement_assessment']['status'] = 'excessive'
            feasibility['recommendations'].append(
                f"Monthly investment requirement ({round(contribution_percent * 100)}% of income) is unsustainable. Consider extending timeline or reducing education cost."
            )
        elif contribution_percent > 0.25:
            feasibility['recommendations'].append(
                f"Monthly investment requirement ({round(contribution_percent * 100)}% of income) is challenging. Consider increasing scholarship focus or exploring education loans."
            )
        
        # Assess timeline adequacy
        if time_horizon < 2:
            feasibility['timeline_assessment']['status'] = 'insufficient'
            feasibility['recommendations'].append(
                "Timeline is very short for significant savings. Consider loan options or delaying education start."
            )
        elif time_horizon < 5:
            feasibility['recommendations'].append(
                "Medium-term timeline requires consistent savings discipline. Prioritize higher yield investments while maintaining sufficient safety."
            )
        
        # Add field-specific recommendations
        if field.lower() == 'medical' and location.lower() == 'india':
            feasibility['field_specific_considerations'] = {
                'competitive_exams': 'Prepare for NEET/other entrance exams',
                'financial_challenges': 'Medical education in India can have unpredictable additional costs',
                'recommendation': 'Include a 15-20% buffer in your education budget for coaching, books, and equipment'
            }
        elif location.lower() != 'india':
            feasibility['international_considerations'] = {
                'forex_volatility': 'Plan for currency exchange rate fluctuations',
                'additional_costs': 'Include budget for travel, accommodation, and international student insurance',
                'recommendation': 'Include a 20-25% buffer in your education budget for international education'
            }
        
        return feasibility
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive education funding strategy with optimization.
        
        Args:
            goal_data: Dictionary with education goal details
            
        Returns:
            Dictionary with comprehensive education strategy
        """
        # Initialize utility classes
        self._initialize_optimizer()
        self._initialize_constraints()
        self._initialize_compound_strategy()
        
        # If this is a basic call with just goal amount and timeline, use base implementation
        if not goal_data.get('course_type') and not goal_data.get('field'):
            return super().generate_funding_strategy(goal_data)
        
        # Extract education-specific information
        course_type = goal_data.get('course_type', 'undergraduate')
        field = goal_data.get('field', 'general')
        location = goal_data.get('location', 'india')
        institution_type = goal_data.get('institution_type', 'average')
        child_age = goal_data.get('child_age')
        education_age = goal_data.get('education_age')
        time_horizon = goal_data.get('time_horizon')
        risk_profile = goal_data.get('risk_profile', 'moderate')
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        annual_income = goal_data.get('annual_income', 1200000)
        tax_bracket = goal_data.get('tax_bracket', 0.30)
        academic_profile = goal_data.get('academic_profile', 'average')
        
        # Determine years to education if not provided
        if time_horizon is None and child_age is not None and education_age is not None:
            time_horizon = max(0, education_age - child_age)
        
        # Estimate education cost if target amount not provided
        target_amount = goal_data.get('target_amount')
        if not target_amount:
            target_amount = self.estimate_education_cost(
                course_type, field, location, institution_type,
                child_age, education_age, time_horizon
            )
        
        # Create education-specific goal data
        education_goal = {
            'goal_type': 'education',
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution,
            
            # Education-specific fields
            'course_type': course_type,
            'field': field,
            'location': location,
            'institution_type': institution_type,
            'child_age': child_age,
            'education_age': education_age,
            'is_girl': goal_data.get('is_girl', False),
            'academic_profile': academic_profile,
            'annual_income': annual_income,
            'tax_bracket': tax_bracket
        }
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(education_goal)
        
        # Enhanced with education-specific funding plan
        education_plan = self.create_education_funding_plan(education_goal)
        
        # Profile data for constraints and optimizations
        profile_data = goal_data.get('profile_data', {
            'monthly_income': annual_income / 12 if annual_income else 100000,
            'risk_profile': risk_profile,
            'annual_income': annual_income
        })
        
        # Apply optimizations
        if profile_data:
            # Optimize funding mix between scholarships, loans, and savings
            optimized_funding = self.optimize_funding_mix(education_goal, education_plan)
            education_plan['optimized_funding_strategy'] = optimized_funding
            
            # Update recommended monthly investment
            if 'monthly_investment' in optimized_funding['funding_distribution']['savings']:
                base_strategy['recommendation']['total_monthly_investment'] = optimized_funding['funding_distribution']['savings']['monthly_investment']
                base_strategy['recommendation']['additional_monthly_required'] = max(0, optimized_funding['funding_distribution']['savings']['monthly_investment'] - monthly_contribution)
            
            # Tax optimization
            base_strategy = self.optimize_strategy(base_strategy, profile_data)
            
            # Add rebalancing strategy
            education_goal['rebalancing_strategy'] = self.integrate_rebalancing_strategy(
                education_goal, profile_data
            )
            
            # Apply constraints
            base_strategy = self.apply_constraints_to_strategy(base_strategy, profile_data)
            
            # Education-specific feasibility assessment
            education_feasibility = self.assess_education_budget_feasibility(
                {**base_strategy, 'education_details': {'course_type': course_type, 'field': field, 'location': location, 'estimated_cost': target_amount}},
                profile_data,
                child_age,
                education_age
            )
            if education_feasibility:
                base_strategy['education_feasibility'] = education_feasibility
        
        # Combine into comprehensive strategy
        strategy = {
            **base_strategy,
            'education_details': {
                'course_type': course_type,
                'field': field,
                'location': location,
                'institution_type': institution_type,
                'estimated_cost': round(target_amount)
            },
            'education_funding_plan': education_plan
        }
        
        # Add rebalancing strategy if available
        if 'rebalancing_strategy' in education_goal:
            strategy['rebalancing_strategy'] = education_goal['rebalancing_strategy']
        
        # Add education-specific tax benefits
        strategy['tax_benefits'] = {
            'available_deductions': [
                {
                    'section': '80C',
                    'applicable_instrument': 'Sukanya Samriddhi Yojana (if girl child)',
                    'annual_limit': 150000
                },
                {
                    'section': '80E',
                    'applicable_instrument': 'Education Loan Interest',
                    'limit': 'No limit for interest payment for 8 years'
                }
            ]
        }
        
        # If compound strategy is available, run scenario analysis
        if hasattr(self, 'compound_strategy'):
            try:
                scenario_analysis = self.compound_strategy.analyze_education_scenarios(
                    strategy, profile_data, self.education_params['education_inflation']
                )
                if scenario_analysis:
                    strategy['scenario_analysis'] = scenario_analysis
            except Exception as e:
                logger.error(f"Error in education scenario analysis: {e}")
        
        # Add education-specific milestones
        strategy['milestones'] = {
            'scholarship_research': {
                'timeline': f"{max(1, time_horizon - 2)} years before education starts",
                'action_items': [
                    'Research scholarship opportunities',
                    'Prepare documentation requirements',
                    'Build profile for better scholarship opportunities'
                ]
            },
            'entrance_exam_preparation': {
                'timeline': f"{max(1, time_horizon - 1.5)} years before education starts",
                'action_items': [
                    'Research entrance requirements',
                    'Begin preparation for required entrance exams',
                    'Consider coaching if necessary'
                ]
            },
            'loan_application': {
                'timeline': '6-8 months before education starts',
                'action_items': [
                    'Compare education loan options',
                    'Prepare documentation for loan application',
                    'Apply for pre-approved loan if available'
                ]
            },
            'final_fund_allocation': {
                'timeline': '3-4 months before education starts',
                'action_items': [
                    'Finalize scholarship applications',
                    'Confirm education loan approval',
                    'Prepare for initial fee payment and living expenses'
                ]
            }
        }
        
        return strategy