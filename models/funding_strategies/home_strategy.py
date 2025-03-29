import logging
import math
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_strategy import FundingStrategyGenerator
from .rebalancing_strategy import RebalancingStrategy

logger = logging.getLogger(__name__)

class HomeDownPaymentStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for home down payment goals with
    India-specific housing market and financing considerations.
    """
    
    def __init__(self):
        """Initialize with home down payment specific parameters"""
        super().__init__()
        
        # Additional home down payment specific parameters
        self.home_params = {
            "home_price_estimates": {
                "metro": {
                    "luxury": 20000000,  # 2 Cr for luxury in metro
                    "premium": 10000000,  # 1 Cr for premium in metro
                    "mid_range": 6000000,  # 60L for mid-range in metro
                    "affordable": 3500000   # 35L for affordable in metro
                },
                "tier_1": {
                    "luxury": 15000000,  # 1.5 Cr
                    "premium": 7500000,   # 75L
                    "mid_range": 4500000, # 45L
                    "affordable": 2500000  # 25L
                },
                "tier_2": {
                    "luxury": 10000000,  # 1 Cr
                    "premium": 5500000,   # 55L
                    "mid_range": 3500000, # 35L
                    "affordable": 2000000  # 20L
                },
                "tier_3": {
                    "luxury": 7500000,   # 75L
                    "premium": 4000000,  # 40L
                    "mid_range": 2500000, # 25L
                    "affordable": 1500000  # 15L
                }
            },
            "down_payment_percent": {
                "min_recommended": 0.2,  # 20% minimum recommended
                "optimal": 0.3,          # 30% optimal
                "max_benefit": 0.5       # 50% maximum benefit
            },
            "home_loan_details": {
                "interest_rates": {
                    "public_banks": {
                        "base_rate": 0.085,
                        "premium_segment": -0.001,  # 10 basis points lower for premium
                        "affordable_segment": 0.001  # 10 basis points higher for affordable
                    },
                    "private_banks": {
                        "base_rate": 0.087,
                        "premium_segment": -0.0015,  # 15 basis points lower for premium
                        "affordable_segment": 0.001   # 10 basis points higher for affordable
                    },
                    "nbfc": {
                        "base_rate": 0.089,
                        "premium_segment": -0.001,
                        "affordable_segment": 0.002
                    }
                },
                "loan_to_value": {
                    "max_ltv": 0.8,  # 80% maximum LTV
                    "optimal_ltv": 0.75  # 75% optimal LTV
                },
                "processing_fee": {
                    "percentage": 0.005,  # 0.5% of loan amount
                    "min_amount": 10000,  # Minimum 10,000
                    "max_amount": 50000   # Maximum 50,000
                },
                "loan_tenure": {
                    "max_years": 30,
                    "optimal_years": 20
                }
            },
            "property_additional_costs": {
                "registration": 0.01,  # 1% of property value
                "stamp_duty": {
                    "general": 0.06,    # 6% generally
                    "female_owner": 0.04  # 4% for female owners in some states
                },
                "legal_charges": 0.005,  # 0.5% approximately
                "gst": {
                    "under_construction": 0.05,  # 5% for affordable
                    "luxury": 0.12       # 12% for luxury
                },
                "other_charges": 0.02    # 2% miscellaneous
            },
            "pmay_details": {
                "credit_linked_subsidy": {
                    "ews_lig": {
                        "income_limit": 600000,  # 6L annual income
                        "subsidy_rate": 0.0635,   # 6.35% subsidy
                        "max_loan": 600000       # Subsidy on 6L
                    },
                    "mig_1": {
                        "income_limit": 1200000,  # 12L annual income
                        "subsidy_rate": 0.04,     # 4% subsidy
                        "max_loan": 900000        # Subsidy on 9L
                    },
                    "mig_2": {
                        "income_limit": 1800000,  # 18L annual income
                        "subsidy_rate": 0.03,     # 3% subsidy
                        "max_loan": 1200000       # Subsidy on 12L
                    }
                },
                "carpet_area_limits": {
                    "ews_lig": 60,  # 60 sq meters
                    "mig_1": 120,   # 120 sq meters
                    "mig_2": 150    # 150 sq meters
                }
            },
            "tax_benefits": {
                "principal_repayment": {
                    "section": "80C",
                    "max_deduction": 150000  # 1.5L max
                },
                "interest_payment": {
                    "section": "24",
                    "max_deduction": 200000,  # 2L for self-occupied
                    "rented_property": "No limit, can be set off against rental income"
                },
                "first_time_buyer": {
                    "section": "80EE",
                    "additional_deduction": 50000,  # 50K additional
                    "conditions": "Property value < 50L, Loan < 35L, No other property"
                },
                "affordable_housing": {
                    "section": "80EEA",
                    "additional_deduction": 150000,  # 1.5L additional
                    "conditions": "Property value < 45L, Carpet area < 60/90 sqm, No other property"
                }
            }
        }
        
        # Load home down payment specific parameters
        self._load_home_parameters()
        
    def _load_home_parameters(self):
        """Load home down payment specific parameters from service"""
        if self.param_service:
            try:
                # Load home price estimates
                price_estimates = self.param_service.get_parameter('home_price_estimates')
                if price_estimates:
                    self.home_params['home_price_estimates'].update(price_estimates)
                
                # Load down payment percent
                down_payment = self.param_service.get_parameter('down_payment_percent')
                if down_payment:
                    self.home_params['down_payment_percent'].update(down_payment)
                
                # Load home loan details
                loan_details = self.param_service.get_parameter('home_loan_details')
                if loan_details:
                    self.home_params['home_loan_details'].update(loan_details)
                
                # Load property additional costs
                additional_costs = self.param_service.get_parameter('property_additional_costs')
                if additional_costs:
                    self.home_params['property_additional_costs'].update(additional_costs)
                
                # Load PMAY details
                pmay_details = self.param_service.get_parameter('pmay_details')
                if pmay_details:
                    self.home_params['pmay_details'].update(pmay_details)
                
                # Load tax benefits
                tax_benefits = self.param_service.get_parameter('home_tax_benefits')
                if tax_benefits:
                    self.home_params['tax_benefits'].update(tax_benefits)
                
            except Exception as e:
                logger.error(f"Error loading home down payment parameters: {e}")
                # Continue with default parameters
    
    def estimate_home_price(self, city_tier, segment, area_sqft=None):
        """
        Estimate home price based on city tier and segment.
        
        Args:
            city_tier: 'metro', 'tier_1', 'tier_2', or 'tier_3'
            segment: 'luxury', 'premium', 'mid_range', or 'affordable'
            area_sqft: Area in square feet (optional for more accurate estimate)
            
        Returns:
            Estimated home price
        """
        # Get base price from parameters
        base_price = self.home_params['home_price_estimates'].get(
            city_tier, self.home_params['home_price_estimates']['tier_2']
        ).get(segment, self.home_params['home_price_estimates']['tier_2']['mid_range'])
        
        # Adjust for specific area if provided
        if area_sqft:
            # Get average price per sqft for the segment and tier
            if city_tier == 'metro':
                if segment == 'luxury':
                    price_per_sqft = 15000  # 15K per sqft
                elif segment == 'premium':
                    price_per_sqft = 10000  # 10K per sqft
                elif segment == 'mid_range':
                    price_per_sqft = 7000   # 7K per sqft
                else:  # affordable
                    price_per_sqft = 5000   # 5K per sqft
            elif city_tier == 'tier_1':
                if segment == 'luxury':
                    price_per_sqft = 12000  # 12K per sqft
                elif segment == 'premium':
                    price_per_sqft = 8000   # 8K per sqft
                elif segment == 'mid_range':
                    price_per_sqft = 5500   # 5.5K per sqft
                else:  # affordable
                    price_per_sqft = 4000   # 4K per sqft
            elif city_tier == 'tier_2':
                if segment == 'luxury':
                    price_per_sqft = 9000   # 9K per sqft
                elif segment == 'premium':
                    price_per_sqft = 6000   # 6K per sqft
                elif segment == 'mid_range':
                    price_per_sqft = 4500   # 4.5K per sqft
                else:  # affordable
                    price_per_sqft = 3000   # 3K per sqft
            else:  # tier_3
                if segment == 'luxury':
                    price_per_sqft = 7000   # 7K per sqft
                elif segment == 'premium':
                    price_per_sqft = 5000   # 5K per sqft
                elif segment == 'mid_range':
                    price_per_sqft = 3500   # 3.5K per sqft
                else:  # affordable
                    price_per_sqft = 2500   # 2.5K per sqft
                    
            # Calculate based on area
            area_based_price = area_sqft * price_per_sqft
            
            # Use the more appropriate of the two estimates
            base_price = (base_price + area_based_price) / 2
        
        return base_price
    
    def calculate_down_payment(self, home_price, down_payment_percent=None):
        """
        Calculate recommended down payment amount.
        
        Args:
            home_price: Home price
            down_payment_percent: Desired down payment percentage (optional)
            
        Returns:
            Recommended down payment amount
        """
        if down_payment_percent is None:
            down_payment_percent = self.home_params['down_payment_percent']['optimal']
            
        down_payment = home_price * down_payment_percent
        
        return down_payment
    
    def calculate_additional_costs(self, home_price, is_under_construction=False, 
                                 is_female_owner=False, segment='mid_range'):
        """
        Calculate additional costs beyond down payment.
        
        Args:
            home_price: Home price
            is_under_construction: Whether property is under construction
            is_female_owner: Whether property will be registered to female
            segment: Property segment
            
        Returns:
            Dictionary with additional costs breakdown
        """
        # Registration
        registration = home_price * self.home_params['property_additional_costs']['registration']
        
        # Stamp duty - varies by state and gender
        if is_female_owner:
            stamp_duty = home_price * self.home_params['property_additional_costs']['stamp_duty']['female_owner']
        else:
            stamp_duty = home_price * self.home_params['property_additional_costs']['stamp_duty']['general']
        
        # Legal charges
        legal = home_price * self.home_params['property_additional_costs']['legal_charges']
        
        # GST - applicable for under-construction properties
        gst = 0
        if is_under_construction:
            if segment in ['luxury', 'premium']:
                gst = home_price * self.home_params['property_additional_costs']['gst']['luxury']
            else:
                gst = home_price * self.home_params['property_additional_costs']['gst']['under_construction']
                
        # Other charges
        other = home_price * self.home_params['property_additional_costs']['other_charges']
        
        # Total additional costs
        total = registration + stamp_duty + legal + gst + other
        
        return {
            'registration': round(registration),
            'stamp_duty': round(stamp_duty),
            'legal_charges': round(legal),
            'gst': round(gst),
            'other_charges': round(other),
            'total_additional_costs': round(total)
        }
    
    def calculate_loan_eligibility(self, annual_income, existing_obligations=0, 
                                 age=35, retirement_age=60, home_price=None, segment='mid_range'):
        """
        Calculate home loan eligibility based on income and obligations.
        
        Args:
            annual_income: Annual income
            existing_obligations: Existing loan obligations (monthly)
            age: Current age
            retirement_age: Expected retirement age
            home_price: Home price (optional)
            segment: Property segment
            
        Returns:
            Dictionary with loan eligibility details
        """
        # Calculate monthly income
        monthly_income = annual_income / 12
        
        # Determine maximum EMI eligibility (usually 50-60% of monthly income)
        max_emi_factor = 0.5  # 50% of income for EMI
        
        # Adjust for existing obligations
        available_for_emi = monthly_income * max_emi_factor - existing_obligations
        
        # Get base interest rate
        base_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        
        # Adjust for segment
        if segment == 'luxury' or segment == 'premium':
            segment_adjustment = self.home_params['home_loan_details']['interest_rates']['public_banks']['premium_segment']
        else:
            segment_adjustment = self.home_params['home_loan_details']['interest_rates']['public_banks']['affordable_segment']
        
        interest_rate = base_rate + segment_adjustment
        
        # Determine maximum tenure based on retirement age
        max_years_to_retirement = retirement_age - age
        max_tenure_policy = self.home_params['home_loan_details']['loan_tenure']['max_years']
        max_tenure = min(max_years_to_retirement, max_tenure_policy)
        
        # Calculate loan eligibility using EMI formula
        # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        # Solving for P: P = EMI * ((1+r)^n - 1) / (r * (1+r)^n)
        monthly_rate = interest_rate / 12
        tenure_months = max_tenure * 12
        
        # Handle edge case for small or negative tenure
        if tenure_months <= 0 or available_for_emi <= 0:
            return {
                'eligible_loan_amount': 0,
                'max_loan_tenure': 0,
                'recommended_loan_amount': 0,
                'monthly_emi': 0,
                'interest_rate': round(interest_rate * 100, 2),
                'eligibility_status': 'Not Eligible',
                'reason': 'Insufficient tenure or income after obligations'
            }
            
        loan_amount = available_for_emi * ((1 + monthly_rate) ** tenure_months - 1) / (monthly_rate * (1 + monthly_rate) ** tenure_months)
        
        # Adjust loan amount based on LTV (Loan to Value) constraints if home price is provided
        recommended_loan = loan_amount
        ltv_constraint = None
        
        if home_price:
            max_ltv = self.home_params['home_loan_details']['loan_to_value']['max_ltv']
            ltv_constraint = home_price * max_ltv
            
            if ltv_constraint < loan_amount:
                recommended_loan = ltv_constraint
        
        # Calculate EMI for recommended loan
        emi = recommended_loan * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        
        # Determine eligibility status
        if recommended_loan < 500000:  # Less than 5 lakhs
            status = 'Low Eligibility'
            reason = 'Very low loan amount eligibility'
        elif recommended_loan < 2000000:  # Less than 20 lakhs
            status = 'Moderate Eligibility'
            reason = 'Consider affordable housing options'
        else:
            status = 'Good Eligibility'
            reason = 'Eligible for standard home loans'
            
        return {
            'eligible_loan_amount': round(loan_amount),
            'max_loan_tenure': max_tenure,
            'recommended_loan_amount': round(recommended_loan),
            'monthly_emi': round(emi),
            'interest_rate': round(interest_rate * 100, 2),
            'ltv_constraint': round(ltv_constraint) if ltv_constraint else None,
            'percentage_of_income': round(emi / monthly_income * 100, 1),
            'eligibility_status': status,
            'reason': reason
        }
    
    def estimate_pmay_benefit(self, annual_income, home_price, carpet_area=None):
        """
        Estimate PMAY (Pradhan Mantri Awas Yojana) benefit eligibility.
        
        Args:
            annual_income: Annual income
            home_price: Home price
            carpet_area: Carpet area in sq meters
            
        Returns:
            Dictionary with PMAY benefit details or None if not eligible
        """
        # Check income eligibility
        clss = self.home_params['pmay_details']['credit_linked_subsidy']
        
        if annual_income <= clss['ews_lig']['income_limit']:
            category = 'ews_lig'
            subsidy_rate = clss['ews_lig']['subsidy_rate']
            max_loan = clss['ews_lig']['max_loan']
            
        elif annual_income <= clss['mig_1']['income_limit']:
            category = 'mig_1'
            subsidy_rate = clss['mig_1']['subsidy_rate']
            max_loan = clss['mig_1']['max_loan']
            
        elif annual_income <= clss['mig_2']['income_limit']:
            category = 'mig_2'
            subsidy_rate = clss['mig_2']['subsidy_rate']
            max_loan = clss['mig_2']['max_loan']
            
        else:
            # Income too high for PMAY
            return None
            
        # Check carpet area eligibility if provided
        if carpet_area:
            carpet_limits = self.home_params['pmay_details']['carpet_area_limits']
            
            if carpet_area > carpet_limits[category]:
                # Carpet area exceeds limit
                return None
                
        # Calculate subsidy amount
        # NPV of interest subsidy payable = (Eligible loan amount) × (Subsidy rate) ÷ (12 × 100) × [1 - (1 + (Subsidy rate) ÷ (12 × 100))^-180] ÷ [(Subsidy rate) ÷ (12 × 100)]
        # Approximation: subsidy = eligible loan * subsidy rate * 9
        subsidy_amount = min(max_loan, home_price * 0.8) * subsidy_rate * 9
        
        return {
            'eligible': True,
            'category': category.upper(),
            'income_limit': clss[category]['income_limit'],
            'subsidy_rate': round(subsidy_rate * 100, 2),
            'eligible_loan_amount': min(max_loan, home_price * 0.8),
            'estimated_subsidy': round(subsidy_amount),
            'carpet_area_limit': self.home_params['pmay_details']['carpet_area_limits'][category],
            'application_requirements': [
                'Aadhaar Card',
                'PAN Card',
                'Income proof',
                'No existing pucca house',
                'Property documents'
            ]
        }
    
    def analyze_rent_vs_buy(self, home_price, monthly_rent, expected_appreciation=0.05, 
                          expected_rent_increase=0.07, holding_period=7, down_payment_percent=0.2):
        """
        Analyze rent vs. buy decision based on financial factors.
        
        Args:
            home_price: Home price
            monthly_rent: Current monthly rent
            expected_appreciation: Expected annual property appreciation
            expected_rent_increase: Expected annual rent increase
            holding_period: Expected years of ownership
            down_payment_percent: Down payment percentage
            
        Returns:
            Dictionary with rent vs. buy analysis
        """
        # Calculate down payment
        down_payment = home_price * down_payment_percent
        
        # Calculate loan amount
        loan_amount = home_price - down_payment
        
        # Get interest rate
        interest_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        
        # Calculate EMI (assume 20 year loan)
        monthly_rate = interest_rate / 12
        tenure_months = 20 * 12
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        
        # Calculate additional costs for ownership
        maintenance = home_price * 0.02 / 12  # Annual 2% for maintenance, converted to monthly
        property_tax = home_price * 0.01 / 12  # Annual 1% for property tax, converted to monthly
        insurance = home_price * 0.005 / 12  # Annual 0.5% for insurance, converted to monthly
        
        # Total monthly cost of ownership in first year
        monthly_ownership_cost = emi + maintenance + property_tax + insurance
        
        # Calculate opportunity cost of down payment
        opportunity_rate = 0.08  # 8% potential return on investment
        annual_opportunity_cost = down_payment * opportunity_rate
        monthly_opportunity_cost = annual_opportunity_cost / 12
        
        # Total effective monthly cost including opportunity cost
        total_effective_monthly_cost = monthly_ownership_cost + monthly_opportunity_cost
        
        # Calculate cumulative rent over holding period
        cumulative_rent = 0
        current_rent = monthly_rent
        
        for year in range(holding_period):
            annual_rent = current_rent * 12
            cumulative_rent += annual_rent
            current_rent *= (1 + expected_rent_increase)  # Increase rent for next year
            
        # Calculate home value after holding period
        final_home_value = home_price * ((1 + expected_appreciation) ** holding_period)
        
        # Calculate equity built through loan payments
        # Simplified calculation - actual would require amortization schedule
        principal_portion = emi * 0.3  # Assume 30% of EMI goes toward principal in early years
        equity_from_payments = principal_portion * 12 * holding_period
        
        # Calculate total equity (appreciation + principal payments)
        total_equity = (final_home_value - home_price) + equity_from_payments + down_payment
        
        # Calculate net cost of buying
        interest_portion = emi * 0.7  # Assume 70% of EMI is interest
        total_interest = interest_portion * 12 * holding_period
        total_other_costs = (maintenance + property_tax + insurance) * 12 * holding_period
        
        net_buying_cost = down_payment + total_interest + total_other_costs - (total_equity - down_payment)
        
        # Tax benefits
        # Principal repayment - Section 80C (capped at 1.5L per year)
        annual_principal = principal_portion * 12
        annual_principal_tax_benefit = min(annual_principal, 150000) * 0.3  # Assuming 30% tax bracket
        
        # Interest payment - Section 24 (capped at 2L per year)
        annual_interest = interest_portion * 12
        annual_interest_tax_benefit = min(annual_interest, 200000) * 0.3  # Assuming 30% tax bracket
        
        total_tax_benefit = (annual_principal_tax_benefit + annual_interest_tax_benefit) * holding_period
        
        # Adjust net buying cost for tax benefits
        net_buying_cost_after_tax = net_buying_cost - total_tax_benefit
        
        # Determine breakeven period
        # Simplified calculation - actual would require year-by-year comparison
        annual_rent_savings = monthly_rent * 12  # First year rent savings
        annual_ownership_premium = (monthly_ownership_cost - monthly_rent) * 12  # Additional cost of owning
        annual_appreciation_benefit = home_price * expected_appreciation  # First year appreciation
        
        annual_net_benefit = annual_appreciation_benefit + annual_rent_savings - annual_ownership_premium
        
        # If annual benefit is positive, calculate breakeven
        breakeven_years = 0
        if annual_net_benefit > 0:
            breakeven_years = down_payment / annual_net_benefit
            
        return {
            'monthly_comparison': {
                'rent': round(monthly_rent),
                'ownership_costs': {
                    'emi': round(emi),
                    'maintenance': round(maintenance),
                    'property_tax': round(property_tax),
                    'insurance': round(insurance),
                    'total': round(monthly_ownership_cost)
                },
                'opportunity_cost': round(monthly_opportunity_cost),
                'effective_monthly_cost': round(total_effective_monthly_cost),
                'monthly_premium_over_rent': round(total_effective_monthly_cost - monthly_rent)
            },
            'long_term_comparison': {
                'holding_period_years': holding_period,
                'cumulative_rent': round(cumulative_rent),
                'final_home_value': round(final_home_value),
                'total_equity_built': round(total_equity),
                'net_buying_cost': round(net_buying_cost),
                'tax_benefits': round(total_tax_benefit),
                'net_buying_cost_after_tax': round(net_buying_cost_after_tax)
            },
            'breakeven_analysis': {
                'estimated_breakeven_years': round(breakeven_years, 1),
                'annual_appreciation_benefit': round(annual_appreciation_benefit),
                'annual_rent_savings': round(annual_rent_savings),
                'annual_ownership_premium': round(annual_ownership_premium),
                'annual_net_benefit': round(annual_net_benefit)
            },
            'recommendation': {
                'financial_perspective': 'Buy' if net_buying_cost_after_tax < cumulative_rent else 'Rent',
                'considerations': [
                    'Stability vs flexibility needs',
                    'Long-term plans in the location',
                    'Potential for property appreciation',
                    'Comfort with debt and maintenance responsibilities',
                    'Current interest rate environment'
                ]
            }
        }
    
    def recommend_short_term_allocations(self, time_horizon, goal_amount):
        """
        Recommend short-term investment allocation for down payment savings.
        
        Args:
            time_horizon: Years to home purchase
            goal_amount: Down payment target amount
            
        Returns:
            Dictionary with recommended short-term allocations
        """
        allocations = {}
        
        if time_horizon < 1:
            # Less than 1 year: Focus on liquidity and capital preservation
            allocations = {
                'savings_account': 0.20,
                'sweep_fd': 0.40,
                'liquid_funds': 0.30,
                'ultra_short_debt': 0.10,
                'expected_return': 5.0  # 5% annualized
            }
            
        elif time_horizon < 2:
            # 1-2 years: Slightly more yield while maintaining safety
            allocations = {
                'savings_account': 0.10,
                'sweep_fd': 0.30,
                'liquid_funds': 0.20,
                'ultra_short_debt': 0.30,
                'short_term_debt': 0.10,
                'expected_return': 6.0  # 6% annualized
            }
            
        elif time_horizon < 3:
            # 2-3 years: Add some low-risk growth elements
            allocations = {
                'savings_account': 0.05,
                'sweep_fd': 0.15,
                'liquid_funds': 0.15,
                'short_term_debt': 0.40,
                'balanced_advantage': 0.15,
                'arbitrage_funds': 0.10,
                'expected_return': 7.0  # 7% annualized
            }
            
        elif time_horizon < 5:
            # 3-5 years: More growth-oriented while controlling volatility
            allocations = {
                'savings_account': 0.05,
                'short_term_debt': 0.30,
                'corporate_bond_funds': 0.20,
                'balanced_advantage': 0.25,
                'large_cap_index': 0.15,
                'arbitrage_funds': 0.05,
                'expected_return': 8.0  # 8% annualized
            }
            
        else:
            # 5+ years: Growth-focused with more equity exposure
            allocations = {
                'short_term_debt': 0.20,
                'corporate_bond_funds': 0.15,
                'balanced_advantage': 0.20,
                'large_cap_index': 0.25,
                'multi_cap_funds': 0.15,
                'gold_etf': 0.05,
                'expected_return': 9.0  # 9% annualized
            }
            
        # Calculate amounts for each allocation
        allocation_amounts = {}
        for instrument, percentage in allocations.items():
            if instrument != 'expected_return':
                allocation_amounts[instrument] = round(goal_amount * percentage)
                
        return {
            'time_horizon': time_horizon,
            'goal_amount': goal_amount,
            'percentage_allocations': {k: v for k, v in allocations.items() if k != 'expected_return'},
            'amount_allocations': allocation_amounts,
            'expected_return': allocations['expected_return'],
            'liquidity_profile': 'High' if time_horizon < 2 else ('Medium' if time_horizon < 4 else 'Moderate'),
            'rebalancing_frequency': 'Quarterly' if time_horizon < 3 else 'Semi-annually'
        }
    
    def evaluate_fhcb_utilization(self, down_payment_amount, first_time_buyer=True,
                               property_value=None, annual_income=None):
        """
        Evaluate First Home & Credit Benefit (FHCB) utilization opportunities.
        
        Args:
            down_payment_amount: Target down payment amount
            first_time_buyer: Whether this is a first-time purchase
            property_value: Expected property value
            annual_income: Annual income
            
        Returns:
            Dictionary with FHCB utilization recommendations
        """
        # Check first-time buyer status
        if not first_time_buyer:
            return {
                'eligible': False,
                'reason': 'Not a first-time home buyer',
                'alternatives': [
                    'Standard home loan tax benefits under Section 24 (interest) and 80C (principal)',
                    'Consider joint ownership with family member who is first-time buyer'
                ]
            }
            
        # Initialize benefits list
        benefits = []
        tax_savings = 0
        
        # Check 80EE benefit eligibility (additional interest deduction for first-time buyers)
        eligible_80ee = False
        if property_value and property_value <= 5000000 and down_payment_amount <= 3500000:
            eligible_80ee = True
            benefits.append({
                'section': '80EE',
                'benefit': 'Additional interest deduction of ₹50,000 per year',
                'conditions_met': True,
                'annual_tax_saving': 15000  # Assuming 30% tax bracket
            })
            tax_savings += 15000
            
        # Check 80EEA benefit eligibility (affordable housing)
        eligible_80eea = False
        if property_value and property_value <= 4500000:
            eligible_80eea = True
            benefits.append({
                'section': '80EEA',
                'benefit': 'Additional interest deduction of ₹1,50,000 per year for affordable housing',
                'conditions_met': True,
                'annual_tax_saving': 45000  # Assuming 30% tax bracket
            })
            tax_savings += 45000
            
        # Check PMAY CLSS eligibility
        pmay_eligible = False
        pmay_benefit = 0
        if annual_income and annual_income <= 1800000 and property_value:
            pmay_analysis = self.estimate_pmay_benefit(annual_income, property_value)
            if pmay_analysis and pmay_analysis['eligible']:
                pmay_eligible = True
                pmay_benefit = pmay_analysis['estimated_subsidy']
                benefits.append({
                    'scheme': 'PMAY-CLSS',
                    'benefit': f"Interest subsidy of approximately ₹{pmay_analysis['estimated_subsidy']}",
                    'conditions_met': True,
                    'subsidy_amount': pmay_analysis['estimated_subsidy']
                })
                
        # Check first-time buyer schemes from banks
        benefits.append({
            'scheme': 'Bank first-time buyer benefits',
            'benefit': 'Processing fee waiver or discount',
            'conditions_met': first_time_buyer,
            'estimated_saving': round(property_value * 0.005) if property_value else 'Varies by lender'
        })
        
        # Special interest rates
        benefits.append({
            'scheme': 'Special interest rates',
            'benefit': 'Some lenders offer 5-10 basis points lower rates for first-time buyers',
            'conditions_met': first_time_buyer,
            'estimated_annual_saving': round(((property_value - down_payment_amount) * 0.0005)) if property_value else 'Varies by lender'
        })
        
        # Calculate total benefits
        total_estimated_benefit = pmay_benefit
        if property_value:
            processing_fee_saving = round(property_value * 0.005)
            interest_rate_saving = round(((property_value - down_payment_amount) * 0.0005) * 5)  # 5 years benefit
            total_estimated_benefit += processing_fee_saving + interest_rate_saving
            
        total_tax_benefit = tax_savings * 5  # Assuming 5 years of tax benefits
        
        return {
            'eligible': first_time_buyer,
            'total_estimated_benefits': round(total_estimated_benefit + total_tax_benefit),
            'tax_benefits': benefits,
            'pmay_eligible': pmay_eligible,
            'action_items': [
                'Keep all income and identity documentation ready',
                'Maintain good credit score (above 750)',
                'Save all relevant property documentation',
                'Research lenders with special first-time buyer programs',
                'Consider applying for pre-approved loans'
            ]
        }
    
    def integrate_rebalancing_strategy(self, goal_data, profile_data=None):
        """
        Integrate rebalancing strategy tailored for home purchase goals.
        
        Home purchase goals have a specific end date and require a safety-oriented
        rebalancing approach, especially as the purchase date approaches. The
        strategy addresses Indian real estate market cycles and downpayment needs.
        
        Args:
            goal_data: Dictionary with home purchase goal details
            profile_data: Dictionary with user profile information
            
        Returns:
            Dictionary with home purchase-specific rebalancing strategy
        """
        # Create rebalancing instance
        rebalancing = RebalancingStrategy()
        
        # Extract home purchase specific information
        time_horizon = goal_data.get('time_horizon', 3)
        target_amount = goal_data.get('target_amount', 0)
        home_price = goal_data.get('home_price', 0)
        current_savings = goal_data.get('current_savings', 0)
        is_under_construction = goal_data.get('is_under_construction', False)
        
        # If profile data not provided, create minimal profile
        if not profile_data:
            profile_data = {
                'risk_profile': goal_data.get('risk_profile', 'moderate'),
                'portfolio_value': current_savings,
                'market_volatility': 'normal',
                'real_estate_timing': 'neutral'  # Special parameter for home purchase
            }
        
        # Get short-term allocation for home purchase
        allocation = self.recommend_short_term_allocations(time_horizon, target_amount)
        allocation_percentages = allocation['percentage_allocations']
        
        # Create goal data specifically for rebalancing
        rebalancing_goal = {
            'goal_type': 'home_purchase',
            'time_horizon': time_horizon,
            'target_allocation': allocation_percentages,
            'current_allocation': goal_data.get('current_allocation', allocation_percentages),
            'priority_level': 'high'  # Home purchase is typically high priority
        }
        
        # Design rebalancing schedule
        rebalancing_schedule = rebalancing.design_rebalancing_schedule(
            rebalancing_goal, profile_data
        )
        
        # Calculate safety-oriented threshold factors based on time to purchase
        safety_threshold_factor = 1.0
        if time_horizon < 1:
            safety_threshold_factor = 0.6  # Very tight thresholds when purchase is imminent
        elif time_horizon < 2:
            safety_threshold_factor = 0.8  # Tight thresholds when purchase is approaching
        elif time_horizon < 3:
            safety_threshold_factor = 0.9  # Slightly tightened thresholds
        else:
            safety_threshold_factor = 1.0  # Standard thresholds
        
        # Customize drift thresholds for home purchase strategy
        # Even tighter for cash/liquid components as purchase approaches
        custom_thresholds = {
            'equity': 0.05 * safety_threshold_factor,
            'debt': 0.03 * safety_threshold_factor,
            'savings_account': 0.005,  # Very tight for cash component
            'liquid_funds': 0.01,      # Tight for liquid funds
            'ultra_short_debt': 0.015, # Slightly wider for ultra short debt
            'short_term_debt': 0.02 * safety_threshold_factor,
            'balanced_advantage': 0.03 * safety_threshold_factor
        }
        
        drift_thresholds = rebalancing.calculate_drift_thresholds(custom_thresholds)
        
        # Consider Indian real estate cycles
        real_estate_cycle_factors = {
            'market_conditions': 'neutral',  # Can be "buyers_market", "sellers_market", or "neutral"
            'seasonal_factors': {
                'festival_season': 'Typically better property deals during festival season (Diwali/Navratri)',
                'financial_year_end': 'Developer offers often increased near financial year end (March)'
            },
            'rebalancing_implications': [
                'Accelerate saving rate if entering a favorable buyer\'s market',
                'Consider temporarily holding more liquid assets when approaching festival seasons',
                'Be prepared to act quickly if real estate opportunities arise unexpectedly'
            ]
        }
        
        # Create home purchase-specific rebalancing strategy
        home_rebalancing = {
            'goal_type': 'home_purchase',
            'rebalancing_schedule': rebalancing_schedule,
            'drift_thresholds': drift_thresholds,
            'property_specific_considerations': {
                'market_cycle_considerations': 'Account for real estate market cycles in rebalancing timing',
                'closing_cost_liquidity': 'Ensure sufficient liquidity for closing costs and registration',
                'construction_linked_payments': 'Align with construction payment schedule if applicable'
            },
            'implementation_priorities': [
                'Increase liquidity as property search intensifies',
                'Account for potential closing date adjustments in rebalancing timeline',
                'Coordinate rebalancing with loan application timing',
                'Ensure sufficient liquidity for registration and other closing costs'
            ]
        }
        
        # Add special considerations for under-construction properties
        if is_under_construction:
            home_rebalancing['construction_linked_strategy'] = {
                'approach': 'Align rebalancing with construction payment schedule',
                'liquidity_planning': 'Maintain higher liquidity for milestone-based developer payments',
                'considerations': [
                    'Schedule larger rebalancing events before major payment milestones',
                    'Maintain separate allocation for handling construction delays',
                    'Consider slightly higher allocation to floating-rate instruments as hedge against construction delays'
                ]
            }
        
        return home_rebalancing
    
    def _initialize_optimizer(self):
        """Initialize the strategy optimizer with lazy loading pattern"""
        if not hasattr(self, 'optimizer') or self.optimizer is None:
            # Initialize the optimizer with home-specific optimization parameters
            super()._initialize_optimizer()
            
            # Add home-specific optimization constraints to the optimizer
            self.optimizer.add_constraint('maximum_emi_ratio', 0.3)  # 30% of income max for EMI
            self.optimizer.add_constraint('minimum_liquidity_ratio', 0.4)  # 40% min liquidity for closing costs
            self.optimizer.add_constraint('down_payment_min_ratio', 0.15)  # 15% minimum down payment
            self.optimizer.add_constraint('down_payment_optimal_ratio', 0.25)  # 25% optimal down payment
    
    def _initialize_constraints(self):
        """Initialize the funding constraints with lazy loading pattern"""
        if not hasattr(self, 'constraints') or self.constraints is None:
            # Initialize base constraints
            super()._initialize_constraints()
            
            # Add home-specific constraints methods
            self.constraints.add_constraint_method('assess_home_purchase_feasibility', self.assess_home_purchase_feasibility)
            self.constraints.add_constraint_method('validate_emi_affordability', self.validate_emi_affordability)
            self.constraints.add_constraint_method('assess_down_payment_adequacy', self.assess_down_payment_adequacy)
    
    def _initialize_compound_strategy(self):
        """Initialize the compound strategy with lazy loading pattern"""
        if not hasattr(self, 'compound_strategy') or self.compound_strategy is None:
            # Initialize base compound strategy
            super()._initialize_compound_strategy()
            
            # Configure for home purchase specific needs
            self.compound_strategy.add_sub_strategy('home_loan_optimization', self.optimize_home_loan)
            self.compound_strategy.add_sub_strategy('down_payment_optimization', self.optimize_down_payment)
    
    def assess_home_purchase_feasibility(self, goal_data):
        """
        Assess the feasibility of the home purchase goal based on income, 
        timeline, and target property value.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with feasibility assessment
        """
        # Extract necessary information
        home_price = goal_data.get('home_price', 0)
        annual_income = goal_data.get('annual_income', 0)
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        time_horizon = goal_data.get('time_horizon', 3)
        
        # Get additional data
        down_payment_pct = self.home_params['down_payment_percent']['optimal']
        down_payment_amount = home_price * down_payment_pct
        existing_obligations = goal_data.get('monthly_debt', 0)
        
        # Calculate loan affordability
        loan_eligibility = self.calculate_loan_eligibility(
            annual_income, existing_obligations, home_price=home_price
        )
        
        # Calculate savings growth over time horizon
        # Using a simplified compound interest formula
        expected_return = 0.06  # 6% expected annual return on savings
        projected_savings = current_savings * ((1 + expected_return) ** time_horizon)
        projected_savings += monthly_contribution * (((1 + expected_return) ** time_horizon) - 1) / expected_return * 12
        
        # Check home price feasibility
        home_price_feasibility = {
            'status': 'Infeasible',
            'reason': 'Home price is not affordable based on income',
            'affordability_ratio': 0
        }
        
        # Check if home price is within 4-5x annual income (standard affordability metric)
        if home_price <= annual_income * 5:
            home_price_feasibility['status'] = 'Feasible'
            home_price_feasibility['reason'] = 'Home price is within reasonable income multiple'
            home_price_feasibility['affordability_ratio'] = annual_income / home_price
        
        # Check down payment feasibility
        down_payment_feasibility = {
            'status': 'Infeasible',
            'reason': 'Projected savings will not cover down payment',
            'coverage_ratio': 0
        }
        
        # Check if projected savings can cover the down payment
        if projected_savings >= down_payment_amount:
            down_payment_feasibility['status'] = 'Feasible'
            down_payment_feasibility['reason'] = 'Projected savings will cover down payment'
            down_payment_feasibility['coverage_ratio'] = projected_savings / down_payment_amount
        
        # Check loan eligibility
        loan_feasibility = {
            'status': 'Infeasible',
            'reason': 'Loan amount required exceeds eligibility',
            'coverage_ratio': 0
        }
        
        loan_required = home_price - down_payment_amount
        if loan_eligibility['recommended_loan_amount'] >= loan_required:
            loan_feasibility['status'] = 'Feasible'
            loan_feasibility['reason'] = 'Eligible loan amount covers required loan'
            loan_feasibility['coverage_ratio'] = loan_eligibility['recommended_loan_amount'] / loan_required
        
        # Overall feasibility
        overall_status = 'Feasible'
        limiting_factors = []
        recommendations = []
        
        if home_price_feasibility['status'] == 'Infeasible':
            overall_status = 'Challenging'
            limiting_factors.append('Home price too high relative to income')
            recommendations.append('Consider a more affordable property or location')
        
        if down_payment_feasibility['status'] == 'Infeasible':
            overall_status = 'Challenging'
            limiting_factors.append('Insufficient savings for down payment')
            
            # Calculate required monthly savings
            shortfall = down_payment_amount - projected_savings
            monthly_needed = shortfall / (time_horizon * 12)
            
            recommendations.append(f'Increase monthly savings by ₹{round(monthly_needed)} to meet down payment goal')
        
        if loan_feasibility['status'] == 'Infeasible':
            overall_status = 'Challenging'
            limiting_factors.append('Loan eligibility below required amount')
            
            # Calculate income needed for loan
            income_needed = annual_income * (loan_required / loan_eligibility['recommended_loan_amount'])
            
            recommendations.append(f'Additional annual income of ₹{round(income_needed - annual_income)} needed for loan eligibility')
        
        # If all three are infeasible, mark as infeasible
        if (home_price_feasibility['status'] == 'Infeasible' and
            down_payment_feasibility['status'] == 'Infeasible' and
            loan_feasibility['status'] == 'Infeasible'):
            overall_status = 'Infeasible'
        
        return {
            'overall_feasibility': overall_status,
            'home_price_feasibility': home_price_feasibility,
            'down_payment_feasibility': down_payment_feasibility,
            'loan_feasibility': loan_feasibility,
            'limiting_factors': limiting_factors,
            'recommendations': recommendations
        }
    
    def validate_emi_affordability(self, goal_data):
        """
        Validate if the EMI for the home loan is affordable based on income.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with EMI affordability assessment
        """
        # Extract necessary information
        home_price = goal_data.get('home_price', 0)
        annual_income = goal_data.get('annual_income', 0)
        down_payment_pct = goal_data.get('down_payment_percent', 
                                       self.home_params['down_payment_percent']['optimal'])
        existing_obligations = goal_data.get('monthly_debt', 0)
        
        # Calculate monthly income
        monthly_income = annual_income / 12
        
        # Calculate loan amount
        down_payment = home_price * down_payment_pct
        loan_amount = home_price - down_payment
        
        # Get interest rate
        interest_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        
        # Calculate EMI
        monthly_rate = interest_rate / 12
        tenure_months = 20 * 12  # 20 years standard
        
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        
        # Calculate FOIR (Fixed Obligation to Income Ratio)
        foir = (emi + existing_obligations) / monthly_income
        
        # Standard FOIR thresholds
        max_foir = 0.5  # 50% maximum
        optimal_foir = 0.4  # 40% optimal
        
        # Assess affordability
        if foir <= optimal_foir:
            affordability_status = 'Comfortable'
            reason = 'EMI is well within affordability limits'
        elif foir <= max_foir:
            affordability_status = 'Manageable'
            reason = 'EMI is within maximum limits but may be stretching budget'
        else:
            affordability_status = 'Stretched'
            reason = 'EMI exceeds recommended affordability limits'
        
        # Calculate affordable loan amount
        affordable_emi = monthly_income * optimal_foir - existing_obligations
        
        if affordable_emi <= 0:
            affordable_loan = 0
        else:
            affordable_loan = affordable_emi / (monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1))
        
        # Calculate affordable home price
        affordable_home_price = affordable_loan / (1 - down_payment_pct)
        
        return {
            'monthly_income': round(monthly_income),
            'emi': round(emi),
            'foir': round(foir * 100, 1),
            'affordability_status': affordability_status,
            'reason': reason,
            'affordable_emi': round(affordable_emi) if affordable_emi > 0 else 0,
            'affordable_loan': round(affordable_loan),
            'affordable_home_price': round(affordable_home_price),
            'recommendations': [
                f'Keep FOIR below {round(optimal_foir * 100)}% for comfortable affordability',
                f'Consider extending loan tenure to reduce EMI' if foir > optimal_foir else '',
                f'Consider increasing down payment to reduce loan amount' if foir > max_foir else ''
            ]
        }
    
    def assess_down_payment_adequacy(self, goal_data):
        """
        Assess if the down payment amount is adequate based on home price,
        loan eligibility, and future financial flexibility.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with down payment adequacy assessment
        """
        # Extract necessary information
        home_price = goal_data.get('home_price', 0)
        down_payment_pct = goal_data.get('down_payment_percent', 
                                       self.home_params['down_payment_percent']['optimal'])
        down_payment = home_price * down_payment_pct
        
        # Get down payment thresholds from parameters
        min_down_payment_pct = self.home_params['down_payment_percent']['min_recommended']
        optimal_down_payment_pct = self.home_params['down_payment_percent']['optimal']
        max_benefit_down_payment_pct = self.home_params['down_payment_percent']['max_benefit']
        
        # Assess adequacy
        if down_payment_pct < min_down_payment_pct:
            adequacy_status = 'Inadequate'
            reason = 'Down payment is below minimum recommended percentage'
        elif down_payment_pct < optimal_down_payment_pct:
            adequacy_status = 'Adequate'
            reason = 'Down payment meets minimum requirements but is below optimal level'
        elif down_payment_pct <= max_benefit_down_payment_pct:
            adequacy_status = 'Optimal'
            reason = 'Down payment is at an optimal level for balancing loan and equity'
        else:
            adequacy_status = 'Above Optimal'
            reason = 'Down payment exceeds the level of maximum financial benefit'
        
        # Calculate PMI (Private Mortgage Insurance) savings
        pmi_required = down_payment_pct < 0.2
        annual_pmi_rate = 0.005  # 0.5% typical PMI rate
        loan_amount = home_price - down_payment
        annual_pmi_cost = loan_amount * annual_pmi_rate if pmi_required else 0
        
        # Calculate interest savings from larger down payment
        interest_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        typical_down_payment = home_price * min_down_payment_pct
        additional_down_payment = down_payment - typical_down_payment
        interest_savings_over_5_years = additional_down_payment * interest_rate * 5
        
        # Calculate opportunity cost of larger down payment
        opportunity_rate = 0.08  # 8% potential return on investment
        opportunity_cost_over_5_years = additional_down_payment * opportunity_rate * 5
        
        # Net financial impact
        net_impact = interest_savings_over_5_years + (annual_pmi_cost * 5) - opportunity_cost_over_5_years
        
        return {
            'down_payment_amount': round(down_payment),
            'down_payment_percentage': round(down_payment_pct * 100, 1),
            'adequacy_status': adequacy_status,
            'reason': reason,
            'minimum_recommended': round(home_price * min_down_payment_pct),
            'optimal_recommended': round(home_price * optimal_down_payment_pct),
            'maximum_benefit': round(home_price * max_benefit_down_payment_pct),
            'pmi_required': pmi_required,
            'annual_pmi_cost': round(annual_pmi_cost),
            'interest_savings': round(interest_savings_over_5_years),
            'opportunity_cost': round(opportunity_cost_over_5_years),
            'net_financial_impact': round(net_impact),
            'recommendations': [
                f'Increase down payment to at least {round(min_down_payment_pct * 100)}% to meet minimum requirements' if down_payment_pct < min_down_payment_pct else '',
                f'Consider increasing down payment to {round(optimal_down_payment_pct * 100)}% for optimal balance' if min_down_payment_pct <= down_payment_pct < optimal_down_payment_pct else '',
                f'Consider keeping additional funds for liquidity instead of further increasing down payment' if down_payment_pct > max_benefit_down_payment_pct else ''
            ]
        }
    
    def optimize_down_payment(self, goal_data):
        """
        Optimize the down payment amount based on multiple factors including
        loan eligibility, PMI costs, interest rates, and opportunity costs.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with optimized down payment recommendation
        """
        # Extract necessary information
        home_price = goal_data.get('home_price', 0)
        annual_income = goal_data.get('annual_income', 0)
        current_savings = goal_data.get('current_savings', 0)
        
        # Get down payment thresholds from parameters
        min_down_payment_pct = self.home_params['down_payment_percent']['min_recommended']
        optimal_down_payment_pct = self.home_params['down_payment_percent']['optimal']
        max_benefit_down_payment_pct = self.home_params['down_payment_percent']['max_benefit']
        
        # Get interest rates
        base_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        
        # Calculate basic down payment options
        minimum_down_payment = home_price * min_down_payment_pct
        optimal_down_payment = home_price * optimal_down_payment_pct
        max_benefit_down_payment = home_price * max_benefit_down_payment_pct
        
        # Consider current savings constraint
        max_available_down_payment = min(current_savings, max_benefit_down_payment)
        
        # Calculate emi for different down payment scenarios
        def calculate_emi(down_payment_amount):
            loan_amount = home_price - down_payment_amount
            monthly_rate = base_rate / 12
            tenure_months = 20 * 12  # 20 years standard
            
            if loan_amount <= 0:
                return 0
                
            return loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        
        minimum_emi = calculate_emi(minimum_down_payment)
        optimal_emi = calculate_emi(optimal_down_payment)
        max_benefit_emi = calculate_emi(max_benefit_down_payment)
        
        # Calculate affordability ratio (monthly income to EMI)
        monthly_income = annual_income / 12
        minimum_affordability = monthly_income / minimum_emi if minimum_emi > 0 else float('inf')
        optimal_affordability = monthly_income / optimal_emi if optimal_emi > 0 else float('inf')
        max_benefit_affordability = monthly_income / max_benefit_emi if max_benefit_emi > 0 else float('inf')
        
        # PMI considerations (below 20% typically requires PMI)
        pmi_threshold = 0.2  # 20%
        pmi_rate = 0.005  # 0.5% annually
        
        # Calculate PMI costs
        minimum_pmi = (home_price - minimum_down_payment) * pmi_rate if min_down_payment_pct < pmi_threshold else 0
        optimal_pmi = (home_price - optimal_down_payment) * pmi_rate if optimal_down_payment_pct < pmi_threshold else 0
        max_benefit_pmi = (home_price - max_benefit_down_payment) * pmi_rate if max_benefit_down_payment_pct < pmi_threshold else 0
        
        # Consider opportunity cost (investing the extra down payment amount)
        opportunity_rate = 0.08  # 8% annual return
        
        # Calculate opportunity costs (compared to minimum down payment)
        optimal_opportunity_cost = (optimal_down_payment - minimum_down_payment) * opportunity_rate
        max_benefit_opportunity_cost = (max_benefit_down_payment - minimum_down_payment) * opportunity_rate
        
        # Calculate net annual benefit for each option
        # Formula: Interest savings + PMI savings - Opportunity cost
        min_net_benefit = 0  # Baseline
        optimal_net_benefit = ((minimum_emi - optimal_emi) * 12) + (minimum_pmi - optimal_pmi) - optimal_opportunity_cost
        max_benefit_net_benefit = ((minimum_emi - max_benefit_emi) * 12) + (minimum_pmi - max_benefit_pmi) - max_benefit_opportunity_cost
        
        # Determine optimized down payment based on net benefit
        optimized_percent = min_down_payment_pct
        if max_benefit_net_benefit > optimal_net_benefit and max_benefit_net_benefit > 0:
            optimized_percent = max_benefit_down_payment_pct
        elif optimal_net_benefit > 0:
            optimized_percent = optimal_down_payment_pct
        
        # Adjust based on available savings
        if current_savings < home_price * optimized_percent:
            if current_savings >= minimum_down_payment:
                # Find highest affordable percentage
                affordable_percent = current_savings / home_price
                optimized_percent = affordable_percent
            else:
                # Cannot afford minimum down payment
                optimized_percent = min_down_payment_pct
                
        optimized_down_payment = home_price * optimized_percent
        
        return {
            'home_price': round(home_price),
            'optimized_down_payment': round(optimized_down_payment),
            'optimized_down_payment_percent': round(optimized_percent * 100, 1),
            'down_payment_options': {
                'minimum': {
                    'amount': round(minimum_down_payment),
                    'percentage': round(min_down_payment_pct * 100, 1),
                    'emi': round(minimum_emi),
                    'affordability_ratio': round(minimum_affordability, 2),
                    'pmi_cost': round(minimum_pmi),
                    'net_benefit': 0  # Baseline
                },
                'optimal': {
                    'amount': round(optimal_down_payment),
                    'percentage': round(optimal_down_payment_pct * 100, 1),
                    'emi': round(optimal_emi),
                    'affordability_ratio': round(optimal_affordability, 2),
                    'pmi_cost': round(optimal_pmi),
                    'opportunity_cost': round(optimal_opportunity_cost),
                    'net_benefit': round(optimal_net_benefit)
                },
                'max_benefit': {
                    'amount': round(max_benefit_down_payment),
                    'percentage': round(max_benefit_down_payment_pct * 100, 1),
                    'emi': round(max_benefit_emi),
                    'affordability_ratio': round(max_benefit_affordability, 2),
                    'pmi_cost': round(max_benefit_pmi),
                    'opportunity_cost': round(max_benefit_opportunity_cost),
                    'net_benefit': round(max_benefit_net_benefit)
                }
            },
            'current_savings_constraint': {
                'available_for_down_payment': round(current_savings),
                'maximum_affordable_percent': round(current_savings / home_price * 100, 1) if home_price > 0 else 0,
                'shortfall_for_optimal': round(max(0, optimal_down_payment - current_savings)),
                'shortfall_for_max_benefit': round(max(0, max_benefit_down_payment - current_savings))
            },
            'recommendations': [
                f"Optimal down payment: {round(optimized_percent * 100, 1)}% (₹{round(optimized_down_payment)})",
                'Increase savings to reach optimal down payment' if current_savings < optimal_down_payment else '',
                'Consider keeping additional funds in liquid investments instead of putting all into down payment' if current_savings > max_benefit_down_payment else ''
            ]
        }
    
    def optimize_home_loan(self, goal_data):
        """
        Optimize home loan parameters including loan tenure, lender selection,
        and prepayment strategy.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with optimized home loan recommendation
        """
        # Extract necessary information
        home_price = goal_data.get('home_price', 0)
        annual_income = goal_data.get('annual_income', 0)
        down_payment_pct = goal_data.get('down_payment_percent', 
                                       self.home_params['down_payment_percent']['optimal'])
        segment = goal_data.get('segment', 'mid_range')
        monthly_surplus = goal_data.get('monthly_surplus', annual_income / 12 * 0.2)  # Assume 20% surplus
        
        # Calculate loan amount
        down_payment = home_price * down_payment_pct
        loan_amount = home_price - down_payment
        
        # Get base interest rates for different lenders
        public_bank_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        private_bank_rate = self.home_params['home_loan_details']['interest_rates']['private_banks']['base_rate']
        nbfc_rate = self.home_params['home_loan_details']['interest_rates']['nbfc']['base_rate']
        
        # Adjust based on segment
        if segment in ['luxury', 'premium']:
            public_bank_rate += self.home_params['home_loan_details']['interest_rates']['public_banks']['premium_segment']
            private_bank_rate += self.home_params['home_loan_details']['interest_rates']['private_banks']['premium_segment']
            nbfc_rate += self.home_params['home_loan_details']['interest_rates']['nbfc']['premium_segment']
        else:
            public_bank_rate += self.home_params['home_loan_details']['interest_rates']['public_banks']['affordable_segment']
            private_bank_rate += self.home_params['home_loan_details']['interest_rates']['private_banks']['affordable_segment']
            nbfc_rate += self.home_params['home_loan_details']['interest_rates']['nbfc']['affordable_segment']
        
        # Calculate processing fees
        fee_percentage = self.home_params['home_loan_details']['processing_fee']['percentage']
        fee_min = self.home_params['home_loan_details']['processing_fee']['min_amount']
        fee_max = self.home_params['home_loan_details']['processing_fee']['max_amount']
        
        public_bank_fee = min(max(loan_amount * fee_percentage, fee_min), fee_max)
        private_bank_fee = min(max(loan_amount * fee_percentage * 1.2, fee_min), fee_max * 1.2)  # 20% higher
        nbfc_fee = min(max(loan_amount * fee_percentage * 1.5, fee_min), fee_max * 1.5)  # 50% higher
        
        # Calculate EMI for different tenures and lenders
        # Standard tenures: 10, 15, 20, 25, 30 years
        tenures = [10, 15, 20, 25, 30]
        
        emi_options = {}
        for tenure in tenures:
            tenure_months = tenure * 12
            
            # Calculate EMI for each lender
            public_monthly_rate = public_bank_rate / 12
            private_monthly_rate = private_bank_rate / 12
            nbfc_monthly_rate = nbfc_rate / 12
            
            public_emi = loan_amount * public_monthly_rate * (1 + public_monthly_rate) ** tenure_months / ((1 + public_monthly_rate) ** tenure_months - 1)
            private_emi = loan_amount * private_monthly_rate * (1 + private_monthly_rate) ** tenure_months / ((1 + private_monthly_rate) ** tenure_months - 1)
            nbfc_emi = loan_amount * nbfc_monthly_rate * (1 + nbfc_monthly_rate) ** tenure_months / ((1 + nbfc_monthly_rate) ** tenure_months - 1)
            
            # Calculate total interest paid
            public_total_interest = (public_emi * tenure_months) - loan_amount
            private_total_interest = (private_emi * tenure_months) - loan_amount
            nbfc_total_interest = (nbfc_emi * tenure_months) - loan_amount
            
            # Store results
            emi_options[tenure] = {
                'public_bank': {
                    'emi': round(public_emi),
                    'interest_rate': round(public_bank_rate * 100, 2),
                    'total_interest': round(public_total_interest),
                    'processing_fee': round(public_bank_fee)
                },
                'private_bank': {
                    'emi': round(private_emi),
                    'interest_rate': round(private_bank_rate * 100, 2),
                    'total_interest': round(private_total_interest),
                    'processing_fee': round(private_bank_fee)
                },
                'nbfc': {
                    'emi': round(nbfc_emi),
                    'interest_rate': round(nbfc_rate * 100, 2),
                    'total_interest': round(nbfc_total_interest),
                    'processing_fee': round(nbfc_fee)
                }
            }
        
        # Calculate affordability ratio for each option
        monthly_income = annual_income / 12
        affordability_ratios = {}
        
        for tenure, lenders in emi_options.items():
            affordability_ratios[tenure] = {
                'public_bank': round(lenders['public_bank']['emi'] / monthly_income * 100, 1),
                'private_bank': round(lenders['private_bank']['emi'] / monthly_income * 100, 1),
                'nbfc': round(lenders['nbfc']['emi'] / monthly_income * 100, 1)
            }
        
        # Optimize prepayment strategy
        # Assume annual prepayment capacity as 12 times monthly surplus
        annual_prepayment_capacity = monthly_surplus * 12
        
        # Calculate impact of prepayment on 20-year loan from public bank
        base_loan_tenure = 20
        base_lender = 'public_bank'
        base_emi = emi_options[base_loan_tenure][base_lender]['emi']
        base_total_interest = emi_options[base_loan_tenure][base_lender]['total_interest']
        
        # Simplified prepayment impact calculation
        # Assuming prepayment directly reduces principal and shortens tenure
        prepayment_years_saved = annual_prepayment_capacity / base_emi * 12 / 5  # Approximate years saved over 5 years
        prepayment_interest_saved = prepayment_years_saved * 12 * base_emi
        
        # Determine optimal tenure based on affordability and total cost
        optimal_tenure = 20  # Default
        optimal_lender = 'public_bank'  # Default
        
        # Typical affordability threshold (EMI should be under 30% of monthly income)
        affordability_threshold = 0.3
        
        # Find shortest affordable tenure
        for tenure in sorted(tenures):
            if emi_options[tenure]['public_bank']['emi'] <= monthly_income * affordability_threshold:
                optimal_tenure = tenure
                break
        
        # Find cheapest lender for optimal tenure
        if (emi_options[optimal_tenure]['private_bank']['total_interest'] + 
            emi_options[optimal_tenure]['private_bank']['processing_fee']) < (
            emi_options[optimal_tenure]['public_bank']['total_interest'] + 
            emi_options[optimal_tenure]['public_bank']['processing_fee']):
            optimal_lender = 'private_bank'
        
        if (emi_options[optimal_tenure]['nbfc']['total_interest'] + 
            emi_options[optimal_tenure]['nbfc']['processing_fee']) < (
            emi_options[optimal_tenure][optimal_lender]['total_interest'] + 
            emi_options[optimal_tenure][optimal_lender]['processing_fee']):
            optimal_lender = 'nbfc'
        
        # Determine optimized balance transfer strategy
        # Check if switching from NBFC to bank after 3 years makes sense
        if optimal_lender == 'nbfc':
            # Approximate remaining principal after 3 years (assuming ~10% paid off)
            remaining_principal = loan_amount * 0.9
            
            # Potential new loan with public bank
            public_monthly_rate = public_bank_rate / 12
            remaining_tenure_months = (optimal_tenure - 3) * 12
            
            # New EMI with public bank
            new_emi = remaining_principal * public_monthly_rate * (1 + public_monthly_rate) ** remaining_tenure_months / ((1 + public_monthly_rate) ** remaining_tenure_months - 1)
            
            # Calculate new total interest
            new_total_interest = (new_emi * remaining_tenure_months) - remaining_principal
            
            # Interest already paid to NBFC in 3 years
            nbfc_interest_paid = (emi_options[optimal_tenure]['nbfc']['emi'] * 36) - (loan_amount * 0.1)
            
            # Total interest with balance transfer
            total_interest_with_transfer = nbfc_interest_paid + new_total_interest + public_bank_fee
            
            # Compare with continuing NBFC loan
            if total_interest_with_transfer < emi_options[optimal_tenure]['nbfc']['total_interest']:
                balance_transfer_savings = emi_options[optimal_tenure]['nbfc']['total_interest'] - total_interest_with_transfer
                balance_transfer_recommendation = f"Consider balance transfer to public bank after 3 years, potential savings: ₹{round(balance_transfer_savings)}"
            else:
                balance_transfer_recommendation = "Balance transfer not recommended, better to continue with original lender"
        else:
            balance_transfer_recommendation = "Balance transfer not necessary as optimal lender already selected"
        
        return {
            'loan_amount': round(loan_amount),
            'emi_options': emi_options,
            'affordability_ratios': affordability_ratios,
            'optimal_loan_recommendation': {
                'optimal_tenure': optimal_tenure,
                'optimal_lender': optimal_lender,
                'optimal_emi': round(emi_options[optimal_tenure][optimal_lender]['emi']),
                'total_interest': round(emi_options[optimal_tenure][optimal_lender]['total_interest']),
                'affordability_ratio': affordability_ratios[optimal_tenure][optimal_lender],
                'processing_fee': round(emi_options[optimal_tenure][optimal_lender]['processing_fee'])
            },
            'prepayment_strategy': {
                'monthly_surplus': round(monthly_surplus),
                'annual_prepayment_capacity': round(annual_prepayment_capacity),
                'years_saved': round(prepayment_years_saved, 1),
                'interest_saved': round(prepayment_interest_saved)
            },
            'balance_transfer': {
                'recommendation': balance_transfer_recommendation
            },
            'recommendations': [
                f"Optimal loan: {optimal_tenure}-year loan from {optimal_lender.replace('_', ' ')}",
                f"Consider prepayment strategy to save approximately {round(prepayment_years_saved, 1)} years and ₹{round(prepayment_interest_saved)} in interest",
                balance_transfer_recommendation
            ]
        }
    
    def run_scenario_analysis(self, goal_data):
        """
        Run scenario analysis for different home purchase scenarios
        including different property types, interest rates, and market conditions.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with scenario analysis results
        """
        # Extract necessary information
        home_price = goal_data.get('home_price', 0)
        annual_income = goal_data.get('annual_income', 0)
        down_payment_pct = goal_data.get('down_payment_percent', 
                                       self.home_params['down_payment_percent']['optimal'])
        city_tier = goal_data.get('city_tier', 'tier_2')
        segment = goal_data.get('segment', 'mid_range')
        
        # Base case
        base_down_payment = home_price * down_payment_pct
        base_loan = home_price - base_down_payment
        base_interest_rate = self.home_params['home_loan_details']['interest_rates']['public_banks']['base_rate']
        
        # Calculate base EMI
        base_monthly_rate = base_interest_rate / 12
        base_tenure_months = 20 * 12  # 20 years
        base_emi = base_loan * base_monthly_rate * (1 + base_monthly_rate) ** base_tenure_months / ((1 + base_monthly_rate) ** base_tenure_months - 1)
        
        # Price scenarios - variation from current price
        price_scenarios = {
            'current': 1.0,
            'modest_increase': 1.1,  # 10% higher
            'significant_increase': 1.2,  # 20% higher
            'modest_decrease': 0.9,  # 10% lower
            'significant_decrease': 0.8  # 20% lower
        }
        
        # Interest rate scenarios - absolute percentage point changes
        rate_scenarios = {
            'current': 0,
            'moderate_increase': 0.01,  # +1%
            'significant_increase': 0.02,  # +2%
            'moderate_decrease': -0.01,  # -1%
            'significant_decrease': -0.02  # -2%
        }
        
        # Property type scenarios - relative price to current segment
        property_scenarios = {
            'current': {
                'name': segment,
                'price_factor': 1.0
            },
            'upgrade': {
                'name': 'premium' if segment == 'mid_range' else ('luxury' if segment == 'premium' else 'luxury_plus'),
                'price_factor': 1.5
            },
            'downgrade': {
                'name': 'affordable' if segment == 'mid_range' else ('mid_range' if segment == 'premium' else 'premium'),
                'price_factor': 0.75
            }
        }
        
        # Location scenarios - relative price to current city tier
        location_scenarios = {
            'current': {
                'name': city_tier,
                'price_factor': 1.0
            },
            'upgrade': {
                'name': 'tier_1' if city_tier == 'tier_2' else ('metro' if city_tier == 'tier_1' else 'metro_premium'),
                'price_factor': 1.5
            },
            'downgrade': {
                'name': 'tier_3' if city_tier == 'tier_2' else ('tier_2' if city_tier == 'tier_1' else 'tier_1'),
                'price_factor': 0.7
            }
        }
        
        # Calculate scenario matrix for price and interest rate
        price_rate_matrix = {}
        
        for price_name, price_factor in price_scenarios.items():
            price_rate_matrix[price_name] = {}
            
            # Calculate new price
            scenario_price = home_price * price_factor
            scenario_down_payment = scenario_price * down_payment_pct
            scenario_loan = scenario_price - scenario_down_payment
            
            for rate_name, rate_change in rate_scenarios.items():
                # Calculate new rate and EMI
                scenario_rate = base_interest_rate + rate_change
                scenario_monthly_rate = scenario_rate / 12
                
                # Calculate EMI
                scenario_emi = scenario_loan * scenario_monthly_rate * (1 + scenario_monthly_rate) ** base_tenure_months / ((1 + scenario_monthly_rate) ** base_tenure_months - 1)
                
                # Calculate affordability ratio
                affordability_ratio = scenario_emi / (annual_income / 12) * 100
                
                # Determine feasibility
                if affordability_ratio <= 30:
                    feasibility = 'Comfortable'
                elif affordability_ratio <= 40:
                    feasibility = 'Manageable'
                elif affordability_ratio <= 50:
                    feasibility = 'Stretched'
                else:
                    feasibility = 'Infeasible'
                
                # Store results
                price_rate_matrix[price_name][rate_name] = {
                    'home_price': round(scenario_price),
                    'down_payment': round(scenario_down_payment),
                    'loan_amount': round(scenario_loan),
                    'interest_rate': round(scenario_rate * 100, 2),
                    'emi': round(scenario_emi),
                    'affordability_ratio': round(affordability_ratio, 1),
                    'feasibility': feasibility
                }
        
        # Calculate property and location scenarios
        property_location_scenarios = {}
        
        for property_key, property_data in property_scenarios.items():
            property_location_scenarios[property_key] = {}
            
            for location_key, location_data in location_scenarios.items():
                # Combined price factor
                combined_factor = property_data['price_factor'] * location_data['price_factor']
                
                # Calculate price and loan
                scenario_price = home_price * combined_factor
                scenario_down_payment = scenario_price * down_payment_pct
                scenario_loan = scenario_price - scenario_down_payment
                
                # Calculate EMI
                scenario_emi = scenario_loan * base_monthly_rate * (1 + base_monthly_rate) ** base_tenure_months / ((1 + base_monthly_rate) ** base_tenure_months - 1)
                
                # Calculate affordability ratio
                affordability_ratio = scenario_emi / (annual_income / 12) * 100
                
                # Determine feasibility
                if affordability_ratio <= 30:
                    feasibility = 'Comfortable'
                elif affordability_ratio <= 40:
                    feasibility = 'Manageable'
                elif affordability_ratio <= 50:
                    feasibility = 'Stretched'
                else:
                    feasibility = 'Infeasible'
                
                # Store results
                property_location_scenarios[property_key][location_key] = {
                    'property_type': property_data['name'],
                    'location': location_data['name'],
                    'home_price': round(scenario_price),
                    'down_payment': round(scenario_down_payment),
                    'loan_amount': round(scenario_loan),
                    'emi': round(scenario_emi),
                    'affordability_ratio': round(affordability_ratio, 1),
                    'feasibility': feasibility
                }
        
        # Find best case scenario (lowest affordable EMI)
        best_case = None
        best_case_emi = float('inf')
        
        for price_key in price_scenarios.keys():
            for rate_key in rate_scenarios.keys():
                scenario = price_rate_matrix[price_key][rate_key]
                if scenario['feasibility'] in ['Comfortable', 'Manageable'] and scenario['emi'] < best_case_emi:
                    best_case = f"Price: {price_key}, Interest Rate: {rate_key}"
                    best_case_emi = scenario['emi']
        
        # Find worst case scenario (highest EMI among manageable options)
        worst_case = None
        worst_case_emi = 0
        
        for price_key in price_scenarios.keys():
            for rate_key in rate_scenarios.keys():
                scenario = price_rate_matrix[price_key][rate_key]
                if scenario['feasibility'] in ['Manageable', 'Stretched'] and scenario['emi'] > worst_case_emi:
                    worst_case = f"Price: {price_key}, Interest Rate: {rate_key}"
                    worst_case_emi = scenario['emi']
        
        # Find most realistic scenario
        realistic_case = f"Price: modest_increase, Interest Rate: moderate_increase"
        realistic_emi = price_rate_matrix['modest_increase']['moderate_increase']['emi']
        
        return {
            'base_case': {
                'home_price': round(home_price),
                'down_payment': round(base_down_payment),
                'loan_amount': round(base_loan),
                'interest_rate': round(base_interest_rate * 100, 2),
                'emi': round(base_emi),
                'affordability_ratio': round(base_emi / (annual_income / 12) * 100, 1)
            },
            'price_interest_scenarios': price_rate_matrix,
            'property_location_scenarios': property_location_scenarios,
            'scenario_summary': {
                'best_case': {
                    'scenario': best_case,
                    'emi': round(best_case_emi) if best_case_emi != float('inf') else 'None found'
                },
                'worst_case': {
                    'scenario': worst_case,
                    'emi': round(worst_case_emi) if worst_case_emi > 0 else 'None found'
                },
                'realistic_case': {
                    'scenario': realistic_case,
                    'emi': round(realistic_emi)
                }
            },
            'recommendations': [
                'Prepare for the realistic case scenario as the most likely outcome',
                'Have a contingency plan for the worst case scenario',
                'Consider waiting for better market conditions if current scenarios are not favorable',
                'Explore alternative property types or locations if affordability is stretched'
            ]
        }
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive home down payment strategy with optimization features.
        
        Args:
            goal_data: Dictionary with home down payment goal details
            
        Returns:
            Dictionary with comprehensive home down payment strategy
        """
        # Extract home down payment specific information
        city_tier = goal_data.get('city_tier', 'tier_2')
        segment = goal_data.get('segment', 'mid_range')
        area_sqft = goal_data.get('area_sqft')
        time_horizon = goal_data.get('time_horizon', 3)
        risk_profile = goal_data.get('risk_profile', 'moderate')
        current_savings = goal_data.get('current_savings', 0)
        monthly_contribution = goal_data.get('monthly_contribution', 0)
        annual_income = goal_data.get('annual_income', 1200000)
        monthly_rent = goal_data.get('monthly_rent')
        first_time_buyer = goal_data.get('first_time_buyer', True)
        
        # Calculate home price and down payment if target amount not provided
        target_amount = goal_data.get('target_amount')
        home_price = goal_data.get('home_price')
        
        if not home_price and not target_amount:
            # Estimate home price
            home_price = self.estimate_home_price(city_tier, segment, area_sqft)
            # Calculate down payment
            target_amount = self.calculate_down_payment(home_price)
        elif home_price and not target_amount:
            # Calculate down payment from home price
            target_amount = self.calculate_down_payment(home_price)
        elif target_amount and not home_price:
            # Estimate home price based on target amount (assuming it's the down payment)
            home_price = target_amount / self.home_params['down_payment_percent']['optimal']
        
        # Calculate additional costs
        is_under_construction = goal_data.get('is_under_construction', False)
        is_female_owner = goal_data.get('is_female_owner', False)
        additional_costs = self.calculate_additional_costs(
            home_price, is_under_construction, is_female_owner, segment
        )
        
        # Create home purchase specific goal data
        home_goal = {
            'goal_type': 'home purchase',
            'target_amount': target_amount,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution,
            
            # Home purchase specific fields
            'home_price': home_price,
            'city_tier': city_tier,
            'segment': segment,
            'annual_income': annual_income,
            'first_time_buyer': first_time_buyer,
            'is_under_construction': is_under_construction
        }
        
        # Initialize constraint and optimization systems (lazy loading)
        self._initialize_constraints()
        self._initialize_optimizer()
        self._initialize_compound_strategy()
        
        # Get base funding strategy
        base_strategy = super().generate_funding_strategy(home_goal)
        
        # Run optimization analyses
        
        # Assess goal feasibility
        feasibility_assessment = self.assess_home_purchase_feasibility(home_goal)
        
        # Validate EMI affordability
        emi_assessment = self.validate_emi_affordability(home_goal)
        
        # Assess down payment adequacy
        down_payment_assessment = self.assess_down_payment_adequacy(home_goal)
        
        # Optimize down payment
        optimized_down_payment = self.optimize_down_payment(home_goal)
        
        # Optimize home loan
        optimized_loan = self.optimize_home_loan(home_goal)
        
        # Run scenario analysis
        scenario_analysis = self.run_scenario_analysis(home_goal)
        
        # Enhanced with home purchase specific analyses (from original)
        
        # Calculate loan eligibility
        loan_eligibility = self.calculate_loan_eligibility(
            annual_income, existing_obligations=0, home_price=home_price, segment=segment
        )
        
        # Short-term allocation recommendations
        short_term_allocations = self.recommend_short_term_allocations(
            time_horizon, target_amount
        )
        
        # Evaluate FHCB utilization if first-time buyer
        fhcb_analysis = None
        if first_time_buyer:
            fhcb_analysis = self.evaluate_fhcb_utilization(
                target_amount, first_time_buyer, home_price, annual_income
            )
        
        # Analyze rent vs. buy if monthly rent provided
        rent_vs_buy_analysis = None
        if monthly_rent:
            rent_vs_buy_analysis = self.analyze_rent_vs_buy(
                home_price, monthly_rent, holding_period=max(7, time_horizon)
            )
        
        # Evaluate PMAY benefit
        pmay_analysis = self.estimate_pmay_benefit(annual_income, home_price)
        
        # Add rebalancing strategy if profile data is available
        profile_data = goal_data.get('profile_data')
        if profile_data:
            home_goal['rebalancing_strategy'] = self.integrate_rebalancing_strategy(
                home_goal, profile_data
            )
        
        # Combine into comprehensive strategy with optimizations
        strategy = {
            **base_strategy,
            'home_details': {
                'estimated_price': round(home_price),
                'recommended_down_payment': round(target_amount),
                'down_payment_percentage': round(target_amount / home_price * 100, 1),
                'city_tier': city_tier,
                'segment': segment
            },
            'additional_costs': additional_costs,
            'loan_eligibility': loan_eligibility,
            'short_term_allocation': short_term_allocations,
            
            # Add optimization results
            'feasibility_assessment': feasibility_assessment,
            'emi_affordability': emi_assessment,
            'down_payment_assessment': down_payment_assessment,
            'optimized_down_payment': optimized_down_payment,
            'optimized_loan': optimized_loan,
            'scenario_analysis': scenario_analysis
        }
        
        # Add rebalancing strategy if available
        if 'rebalancing_strategy' in home_goal:
            strategy['rebalancing_strategy'] = home_goal['rebalancing_strategy']
        
        if fhcb_analysis:
            strategy['first_time_buyer_benefits'] = fhcb_analysis
            
        if rent_vs_buy_analysis:
            strategy['rent_vs_buy_analysis'] = rent_vs_buy_analysis
            
        if pmay_analysis:
            strategy['pmay_benefit'] = pmay_analysis
        
        # Add home purchase specific tax benefits
        strategy['tax_benefits'] = {
            'pre_purchase': [
                {
                    'section': '80C',
                    'benefit': 'Tax deduction on home loan principal of up to ₹1.5 lakhs annually',
                    'applicability': 'After home purchase'
                },
                {
                    'section': '24',
                    'benefit': 'Tax deduction on home loan interest of up to ₹2 lakhs annually for self-occupied property',
                    'applicability': 'After home purchase'
                }
            ],
            'first_time_buyer_specific': [
                {
                    'section': '80EE',
                    'benefit': 'Additional interest deduction of ₹50,000 per year',
                    'conditions': 'Property value ≤ ₹50 lakhs, Loan ≤ ₹35 lakhs, No other property'
                },
                {
                    'section': '80EEA',
                    'benefit': 'Additional interest deduction of ₹1,50,000 per year for affordable housing',
                    'conditions': 'Property value ≤ ₹45 lakhs, Carpet area < 60/90 sqm, No other property'
                }
            ]
        }
        
        # Compile optimized action plan from all analyses
        strategy['optimized_action_plan'] = {
            'immediate_actions': [
                f"Set optimal down payment target of ₹{round(optimized_down_payment['optimized_down_payment'])} ({optimized_down_payment['optimized_down_payment_percent']}% of home price)",
                f"Save ₹{round(monthly_contribution)} monthly toward down payment goal",
                "Optimize current savings allocation using recommended short-term allocation"
            ],
            'pre_approval_phase': [
                "Check and improve credit score to secure optimal interest rate",
                f"Target {optimized_loan['optimal_loan_recommendation']['optimal_lender'].replace('_', ' ')} for home loan",
                "Compare loan offers from multiple lenders with focus on effective interest rate"
            ],
            'property_search_phase': [
                f"Focus on {segment} properties in {city_tier} areas within budget of ₹{round(home_price)}",
                "Verify property legal documentation and approvals",
                "Consider properties with higher appreciation potential in emerging localities"
            ],
            'loan_application_phase': [
                f"Apply for {optimized_loan['optimal_loan_recommendation']['optimal_tenure']}-year loan term",
                "Negotiate processing fee waiver or reduction",
                "Prepare all documentation for smooth approval process"
            ],
            'post_purchase_strategy': [
                f"Set up prepayment fund of ₹{round(optimized_loan['prepayment_strategy']['annual_prepayment_capacity'])} annually",
                "Maximize tax benefits through proper documentation",
                "Review loan terms after 3-5 years for potential refinancing"
            ]
        }
        
        # Add home purchase specific milestones with optimization insights
        strategy['milestones'] = {
            'property_research': {
                'timeline': f"{max(1, time_horizon - 2)} years before purchase",
                'action_items': [
                    'Research localities and property options',
                    'Visit properties and shortlist options',
                    'Check builder reputation and project approvals'
                ]
            },
            'loan_pre_approval': {
                'timeline': f"{max(0.5, time_horizon - 1)} years before purchase",
                'action_items': [
                    'Check and improve credit score',
                    'Get loan pre-approval to understand budget',
                    'Compare loan options from multiple lenders'
                ]
            },
            'legal_verification': {
                'timeline': '3-6 months before purchase',
                'action_items': [
                    'Complete legal verification of property',
                    'Check all necessary approvals and documents',
                    'Prepare for down payment and other costs'
                ]
            },
            'final_preparation': {
                'timeline': '1-2 months before purchase',
                'action_items': [
                    'Finalize loan application and processing',
                    'Arrange for down payment and additional costs',
                    'Prepare for registration and stamp duty payment'
                ]
            },
            'post_purchase_optimization': {
                'timeline': 'Ongoing after purchase',
                'action_items': [
                    f'Implement prepayment strategy to save ₹{round(optimized_loan["prepayment_strategy"]["interest_saved"])} in interest',
                    'Maximize tax benefits through proper documentation',
                    'Review loan terms annually for potential refinancing opportunities'
                ]
            }
        }
        
        return strategy