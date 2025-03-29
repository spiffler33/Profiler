import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_calculator import GoalCalculator

logger = logging.getLogger(__name__)

class DiscretionaryGoalCalculator(GoalCalculator):
    """Calculator for discretionary/lifestyle goals like travel, vehicles, and leisure"""
    
    def calculate_amount_needed(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate the amount needed for a discretionary goal.
        
        Args:
            goal: The discretionary goal
            profile: User profile
            
        Returns:
            float: Calculated amount needed
        """
        # Extract user_id for parameter access
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        # Special handling for test cases
        if isinstance(goal, dict) and goal.get('id') == 'discretionary-test':
            # For test case, use target amount if provided or calculate with test parameters
            if goal.get('target_amount', 0) > 0:
                return goal['target_amount']
                
            # Print diagnostic for test case
            print(f"Using test inflation rate: {self.get_parameter('inflation.general', 0.06, user_id)}")
        
        # If goal already has target amount, use that
        if isinstance(goal, dict):
            if goal.get('target_amount', 0) > 0:
                return goal['target_amount']
        elif hasattr(goal, 'target_amount') and goal.target_amount > 0:
            return goal.target_amount
        
        # Extract goal category and time until goal
        goal_category = self._extract_goal_category(goal)
        time_until_goal = self.calculate_time_available(goal, profile) / 12  # Convert months to years
        
        # Calculate amount based on goal category
        amount = self._calculate_category_based_amount(goal_category, profile)
        
        # Get inflation rate from parameters
        inflation_rate = self.get_parameter("inflation.general", 0.06, user_id)
        
        # Adjust for inflation
        inflated_amount = amount * ((1 + inflation_rate) ** time_until_goal)
        
        return inflated_amount
    
    def calculate_goal_priorities(self, goals: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate and prioritize multiple discretionary goals.
        
        Args:
            goals: List of discretionary goals
            profile: User profile
            
        Returns:
            list: Prioritized goals with scores and recommendations
        """
        # Monthly income for reference
        monthly_income = self._get_monthly_income(profile)
        monthly_expenses = self._get_monthly_expenses(profile)
        
        # Available discretionary income
        available_income = max(0, monthly_income - monthly_expenses)
        
        # Calculate priority score for each goal
        prioritized_goals = []
        
        for goal in goals:
            # Extract basic goal details
            goal_id = goal.get('id')
            goal_title = goal.get('title')
            goal_category = self._extract_goal_category(goal)
            current_amount = goal.get('current_amount', 0)
            target_amount = goal.get('target_amount', 0)
            
            # If target amount not set, calculate it
            if target_amount <= 0:
                target_amount = self.calculate_amount_needed(goal, profile)
                
            # Calculate time available in months
            months_available = self.calculate_time_available(goal, profile)
            years_available = months_available / 12
            
            # Calculate required monthly contribution
            monthly_contribution = self.calculate_monthly_contribution(goal, profile)
            
            # Calculate affordability ratio (contribution as % of available income)
            if available_income > 0:
                affordability_ratio = monthly_contribution / available_income
            else:
                affordability_ratio = float('inf')
                
            # Calculate base priority score
            base_score = self.calculate_priority_score(goal, profile)
            
            # Adjust based on affordability
            if affordability_ratio <= 0.2:
                # Easily affordable
                affordability_modifier = 1.2
                affordability_status = "Easily affordable"
            elif affordability_ratio <= 0.5:
                # Moderately affordable
                affordability_modifier = 1.0
                affordability_status = "Moderately affordable"
            elif affordability_ratio <= 1.0:
                # Challenging but possible
                affordability_modifier = 0.8
                affordability_status = "Challenging but possible"
            else:
                # Very difficult
                affordability_modifier = 0.6
                affordability_status = "Very difficult"
                
            # Calculate final priority score
            final_score = base_score * affordability_modifier
            
            # Generate funding approach
            funding_approach = self._generate_funding_approach(goal, profile, affordability_ratio)
            
            # Add to list
            prioritized_goals.append({
                'goal_id': goal_id,
                'title': goal_title,
                'category': goal_category,
                'target_amount': round(target_amount),
                'current_amount': round(current_amount),
                'progress_percent': round((current_amount / target_amount * 100) if target_amount > 0 else 0, 1),
                'time_available_years': round(years_available, 1),
                'monthly_contribution': round(monthly_contribution),
                'affordability_ratio': round(affordability_ratio * 100, 1),
                'affordability_status': affordability_status,
                'priority_score': round(final_score, 1),
                'funding_approach': funding_approach
            })
            
        # Sort by priority score (highest first)
        prioritized_goals.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return prioritized_goals
    
    def analyze_goal_impact(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the impact of a discretionary goal on overall financial health.
        
        Args:
            goal: The discretionary goal
            profile: User profile
            
        Returns:
            dict: Impact analysis
        """
        # Calculate goal amount
        target_amount = self.calculate_amount_needed(goal, profile)
        
        # Calculate monthly contribution
        monthly_contribution = self.calculate_monthly_contribution(goal, profile)
        
        # Get financial metrics
        monthly_income = self._get_monthly_income(profile)
        annual_income = monthly_income * 12
        monthly_expenses = self._get_monthly_expenses(profile)
        
        # Available savings
        monthly_savings_capacity = max(0, monthly_income - monthly_expenses)
        
        # Impact on savings rate
        current_savings_rate = monthly_savings_capacity / monthly_income if monthly_income > 0 else 0
        adjusted_savings_rate = (monthly_savings_capacity - monthly_contribution) / monthly_income if monthly_income > 0 else 0
        savings_rate_impact = current_savings_rate - adjusted_savings_rate
        
        # Goal-to-income ratio (target amount as % of annual income)
        goal_to_income_ratio = target_amount / annual_income if annual_income > 0 else float('inf')
        
        # Assess overall impact
        if savings_rate_impact <= 0.05 and goal_to_income_ratio <= 0.2:
            impact_level = "Low"
            impact_description = "This goal has minimal impact on your overall financial health"
        elif savings_rate_impact <= 0.1 and goal_to_income_ratio <= 0.5:
            impact_level = "Moderate"
            impact_description = "This goal has a moderate impact on your finances that should be manageable"
        elif savings_rate_impact <= 0.2 and goal_to_income_ratio <= 1.0:
            impact_level = "Significant"
            impact_description = "This goal will significantly impact your finances and may delay other goals"
        else:
            impact_level = "High"
            impact_description = "This goal will have a major impact on your finances and should be carefully considered"
            
        # Identify affected financial areas
        affected_areas = []
        
        if savings_rate_impact > 0.1:
            affected_areas.append({
                'area': 'Monthly Savings',
                'impact': f"Reduces savings rate by {savings_rate_impact*100:.1f}%",
                'recommendation': "Consider extending timeframe to reduce monthly contribution"
            })
            
        if goal_to_income_ratio > 0.5:
            affected_areas.append({
                'area': 'Overall Savings Level',
                'impact': f"Goal represents {goal_to_income_ratio*100:.1f}% of annual income",
                'recommendation': "Consider scaling down the goal or finding alternative funding sources"
            })
            
        if monthly_contribution > monthly_savings_capacity * 0.5:
            affected_areas.append({
                'area': 'Other Financial Goals',
                'impact': "May delay progress on other financial priorities",
                'recommendation': "Ensure essential goals (emergency fund, retirement) remain on track"
            })
            
        # Add opportunity cost
        opportunity_cost = self._calculate_opportunity_cost(target_amount, goal, profile)
        
        return {
            'target_amount': round(target_amount),
            'monthly_contribution': round(monthly_contribution),
            'savings_rate_impact': {
                'current_savings_rate': f"{current_savings_rate*100:.1f}%",
                'adjusted_savings_rate': f"{adjusted_savings_rate*100:.1f}%",
                'percentage_reduction': f"{savings_rate_impact*100:.1f}%"
            },
            'goal_to_income_ratio': f"{goal_to_income_ratio*100:.1f}%",
            'overall_impact': {
                'level': impact_level,
                'description': impact_description
            },
            'affected_financial_areas': affected_areas,
            'opportunity_cost': opportunity_cost
        }
        
    def _extract_goal_category(self, goal) -> str:
        """Extract the specific discretionary goal category"""
        category = "discretionary"  # Default category
        
        # Try to extract from goal
        if isinstance(goal, dict):
            # Check category field
            if 'category' in goal:
                goal_category = goal['category'].lower()
                if goal_category in ['travel', 'vacation', 'vehicle', 'car', 'home_improvement', 'electronics', 'hobby']:
                    return goal_category
                    
            # Check title
            if 'title' in goal:
                title = goal['title'].lower()
                
                # Check for travel/vacation keywords
                if any(term in title for term in ['travel', 'vacation', 'trip', 'holiday', 'tour']):
                    return 'travel'
                    
                # Check for vehicle keywords
                if any(term in title for term in ['car', 'vehicle', 'bike', 'automobile', 'motorcycle']):
                    return 'vehicle'
                    
                # Check for home improvement keywords
                if any(term in title for term in ['home', 'house', 'renovation', 'remodel', 'furniture']):
                    return 'home_improvement'
                    
                # Check for electronics keywords
                if any(term in title for term in ['electronics', 'gadget', 'computer', 'phone', 'laptop']):
                    return 'electronics'
                    
                # Check for hobby keywords
                if any(term in title for term in ['hobby', 'sport', 'fitness', 'equipment']):
                    return 'hobby'
                    
            # Try metadata
            if 'metadata' in goal and goal['metadata']:
                try:
                    metadata = json.loads(goal['metadata'])
                    if 'goal_subcategory' in metadata:
                        return metadata['goal_subcategory'].lower()
                except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                    pass
        elif hasattr(goal, 'category'):
            # Object-based goal
            goal_category = goal.category.lower()
            if goal_category in ['travel', 'vacation', 'vehicle', 'car', 'home_improvement', 'electronics', 'hobby']:
                return goal_category
                
            # Check title
            if hasattr(goal, 'title'):
                title = goal.title.lower()
                
                # Check for travel/vacation keywords
                if any(term in title for term in ['travel', 'vacation', 'trip', 'holiday', 'tour']):
                    return 'travel'
                    
                # Check for vehicle keywords
                if any(term in title for term in ['car', 'vehicle', 'bike', 'automobile', 'motorcycle']):
                    return 'vehicle'
                    
                # Check for home improvement keywords
                if any(term in title for term in ['home', 'house', 'renovation', 'remodel', 'furniture']):
                    return 'home_improvement'
                    
                # Check for electronics keywords
                if any(term in title for term in ['electronics', 'gadget', 'computer', 'phone', 'laptop']):
                    return 'electronics'
                    
                # Check for hobby keywords
                if any(term in title for term in ['hobby', 'sport', 'fitness', 'equipment']):
                    return 'hobby'
                    
            # Try metadata
            if hasattr(goal, 'metadata') and goal.metadata:
                try:
                    metadata = json.loads(goal.metadata)
                    if 'goal_subcategory' in metadata:
                        return metadata['goal_subcategory'].lower()
                except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                    pass
        
        return category
    
    def _calculate_category_based_amount(self, category: str, profile: Dict[str, Any]) -> float:
        """Calculate default amount based on goal category"""
        # Get monthly income for reference
        monthly_income = self._get_monthly_income(profile)
        annual_income = monthly_income * 12
        
        if category == 'travel':
            # Travel typically 5-15% of annual income
            return annual_income * 0.10
        elif category == 'vehicle':
            # Vehicle typically 30-70% of annual income
            return annual_income * 0.50
        elif category == 'home_improvement':
            # Home improvement typically 10-30% of annual income
            return annual_income * 0.20
        elif category == 'electronics':
            # Electronics typically 2-8% of annual income
            return annual_income * 0.05
        elif category == 'hobby':
            # Hobby equipment typically 3-10% of annual income
            return annual_income * 0.06
        else:
            # Generic discretionary goal
            return annual_income * 0.15
    
    def _generate_funding_approach(self, goal, profile: Dict[str, Any], affordability_ratio: float) -> Dict[str, Any]:
        """Generate funding approach based on goal category and affordability"""
        # Extract goal category
        category = self._extract_goal_category(goal)
        
        # Base funding approach
        if affordability_ratio <= 0.2:
            # Easily affordable - regular contributions
            funding_type = "regular"
            description = "Regular monthly contributions from income"
        elif affordability_ratio <= 0.5:
            # Moderately affordable - hybrid approach
            funding_type = "hybrid"
            description = "Regular contributions with periodic boosts from bonuses or windfalls"
        elif affordability_ratio <= 1.0:
            # Challenging - milestone approach
            funding_type = "milestone"
            description = "Targeted funding from bonuses, tax refunds, or occasional savings drives"
        else:
            # Very difficult - windfall approach
            funding_type = "windfall"
            description = "Primarily funded through bonuses, gifts, or other one-time sources"
            
        # Category-specific recommendations
        recommendations = []
        
        if category == 'travel':
            recommendations.extend([
                "Look for travel deals, off-season pricing, and points/rewards",
                "Consider a dedicated travel fund with automated transfers",
                "Book accommodations and flights well in advance for better rates"
            ])
        elif category == 'vehicle':
            recommendations.extend([
                "Consider a balance between down payment and loan to optimize cash flow",
                "Look for model year-end or festive season discounts",
                "Factor in ongoing ownership costs when choosing vehicle budget"
            ])
        elif category == 'home_improvement':
            recommendations.extend([
                "Prioritize projects by ROI and break into phases if needed",
                "Get multiple quotes and consider timing projects during off-peak seasons",
                "Look into home improvement loans if the project adds significant value"
            ])
        elif category == 'electronics':
            recommendations.extend([
                "Time purchases with major sales events",
                "Consider previous-generation models for better value",
                "Look for cash back offers or zero-interest financing"
            ])
        elif category == 'hobby':
            recommendations.extend([
                "Start with essential equipment and upgrade gradually",
                "Look for second-hand or refurbished equipment",
                "Join clubs or groups to share resources and get discounts"
            ])
        else:
            recommendations.extend([
                "Create a separate savings account for this goal",
                "Set up automatic transfers to build the fund consistently",
                "Reassess the goal periodically to ensure it remains a priority"
            ])
            
        return {
            'funding_type': funding_type,
            'description': description,
            'recommendations': recommendations
        }
    
    def _calculate_opportunity_cost(self, amount: float, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the opportunity cost of the discretionary goal"""
        # Extract user_id for parameter access
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        # Calculate time to goal
        years_to_goal = self.calculate_time_available(goal, profile) / 12
        
        # Get investment return from parameters
        investment_return = self.get_parameter("discretionary.opportunity_cost.investment_return", 0.09, user_id)  # Default 9% annual return
        
        # Calculate opportunity cost (what the money could grow to if invested)
        future_value = amount * ((1 + investment_return) ** years_to_goal)
        opportunity_cost = future_value - amount
        
        # Get retirement age from parameters
        retirement_age = self.get_parameter("retirement.target_age", 60, user_id)  # Default retirement at 60
        
        # Calculate retirement impact
        retirement_years = 30  # Default assuming 30 years to retirement
        if 'age' in profile:
            current_age = profile['age']
            if current_age > 0:
                retirement_years = max(1, retirement_age - current_age)
                
        retirement_value = amount * ((1 + investment_return) ** retirement_years)
        
        return {
            'investment_potential': round(future_value),
            'growth_foregone': round(opportunity_cost),
            'retirement_impact': round(retirement_value),
            'assumptions': {
                'annual_return': f"{investment_return*100:.1f}%",
                'time_horizon_years': round(years_to_goal, 1),
                'retirement_horizon_years': retirement_years
            }
        }


class VehicleCalculator(DiscretionaryGoalCalculator):
    """Specialized calculator for vehicle purchase goals with additional vehicle-specific calculations"""
    
    def calculate_ownership_cost(self, goal, profile: Dict[str, Any], years: int = 5) -> Dict[str, Any]:
        """
        Calculate total cost of vehicle ownership over a period.
        
        Args:
            goal: The vehicle goal
            profile: User profile
            years: Years of ownership to calculate
            
        Returns:
            dict: Total cost of ownership breakdown
        """
        # Extract vehicle parameters
        vehicle_type, vehicle_cost, is_new = self._extract_vehicle_parameters(goal)
        
        # Calculate annual costs
        annual_costs = {}
        
        # Depreciation
        if is_new:
            # New cars depreciate faster initially
            first_year_depreciation = vehicle_cost * 0.20  # 20% first year
            subsequent_years = min(years - 1, 4)  # Calculate up to 5 years
            subsequent_depreciation = vehicle_cost * 0.10 * subsequent_years  # 10% subsequent years
            total_depreciation = first_year_depreciation + subsequent_depreciation
        else:
            # Used cars depreciate more steadily
            total_depreciation = vehicle_cost * 0.10 * min(years, 5)  # 10% per year up to 5 years
            
        annual_costs['depreciation'] = total_depreciation
        
        # Fuel costs
        monthly_fuel_cost = self._calculate_monthly_fuel_cost(vehicle_type)
        annual_costs['fuel'] = monthly_fuel_cost * 12 * years
        
        # Insurance
        annual_insurance = self._calculate_annual_insurance(vehicle_type, vehicle_cost, is_new)
        annual_costs['insurance'] = annual_insurance * years
        
        # Maintenance and repairs
        if is_new:
            # Lower maintenance in early years
            annual_maintenance = vehicle_cost * 0.02  # 2% of vehicle cost annually
        else:
            # Higher maintenance for used vehicles
            annual_maintenance = vehicle_cost * 0.04  # 4% of vehicle cost annually
            
        annual_costs['maintenance'] = annual_maintenance * years
        
        # Taxes and fees
        annual_taxes = vehicle_cost * 0.01  # 1% of vehicle cost annually (simplified)
        annual_costs['taxes_fees'] = annual_taxes * years
        
        # Loan interest (if applicable)
        loan_interest = self._calculate_loan_interest(vehicle_cost, goal, profile)
        annual_costs['loan_interest'] = loan_interest
        
        # Total cost of ownership
        total_ownership_cost = vehicle_cost + sum(annual_costs.values())
        
        # Calculate cost per kilometer
        annual_km = 15000  # Assumption: 15,000 km per year
        total_km = annual_km * years
        cost_per_km = total_ownership_cost / total_km if total_km > 0 else 0
        
        return {
            'vehicle_cost': round(vehicle_cost),
            'is_new': is_new,
            'years_of_ownership': years,
            'total_ownership_cost': round(total_ownership_cost),
            'annual_ownership_cost': round(total_ownership_cost / years),
            'monthly_ownership_cost': round(total_ownership_cost / (years * 12)),
            'cost_per_km': round(cost_per_km, 2),
            'cost_breakdown': {
                'initial_purchase': round(vehicle_cost),
                'depreciation': round(annual_costs['depreciation']),
                'fuel': round(annual_costs['fuel']),
                'insurance': round(annual_costs['insurance']),
                'maintenance': round(annual_costs['maintenance']),
                'taxes_fees': round(annual_costs['taxes_fees']),
                'loan_interest': round(annual_costs['loan_interest'])
            }
        }
    
    def compare_lease_vs_buy(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare leasing versus buying a vehicle.
        
        Args:
            goal: The vehicle goal
            profile: User profile
            
        Returns:
            dict: Lease vs buy comparison
        """
        # Extract vehicle parameters
        vehicle_type, vehicle_cost, is_new = self._extract_vehicle_parameters(goal)
        
        # Only compare if the vehicle is new
        if not is_new:
            vehicle_cost = vehicle_cost * 1.5  # Approximate new value
            
        # Calculate buying costs
        # Down payment (assuming 20%)
        down_payment = vehicle_cost * 0.20
        
        # Loan details (assuming 5-year loan)
        loan_amount = vehicle_cost - down_payment
        loan_years = 5
        interest_rate = 0.085  # 8.5% rate for vehicle loan
        
        # Calculate EMI
        monthly_rate = interest_rate / 12
        num_payments = loan_years * 12
        
        if monthly_rate > 0:
            emi = loan_amount * (
                (monthly_rate * ((1 + monthly_rate) ** num_payments)) / 
                (((1 + monthly_rate) ** num_payments) - 1)
            )
        else:
            emi = loan_amount / num_payments
            
        # Total loan cost
        total_loan_cost = emi * num_payments
        loan_interest = total_loan_cost - loan_amount
        
        # Total buying cost over 5 years
        ownership_costs = self.calculate_ownership_cost(goal, profile, 5)
        total_buying_cost = ownership_costs['total_ownership_cost']
        
        # Resale value after 5 years (approximately 40% of new value)
        resale_value = vehicle_cost * 0.40
        
        # Net buying cost
        net_buying_cost = total_buying_cost - resale_value
        
        # Calculate leasing costs
        # Monthly lease payment (approximately 1.5% of vehicle value)
        monthly_lease = vehicle_cost * 0.015
        
        # Down payment (typically lower for lease)
        lease_down_payment = vehicle_cost * 0.10
        
        # Additional lease costs
        acquisition_fee = 10000  # Approximate acquisition fee
        disposition_fee = 15000  # Fee when returning the vehicle
        excess_mileage = 0       # Assume within mileage limits
        excess_wear_tear = 0     # Assume normal wear and tear
        
        # Total lease cost over 3 years (typical lease term)
        lease_years = 3
        total_lease_cost = (
            lease_down_payment +
            (monthly_lease * lease_years * 12) +
            acquisition_fee +
            disposition_fee +
            excess_mileage +
            excess_wear_tear
        )
        
        # Calculate 5-year lease cost (to compare with buying)
        five_year_lease_cost = total_lease_cost
        if lease_years < 5:
            # Add cost of a second lease to compare equally
            additional_years = 5 - lease_years
            
            # Assume 10% higher costs for second lease
            additional_lease_cost = (
                lease_down_payment * 0.5 +  # Reduced down payment for returning customer
                (monthly_lease * 1.1 * additional_years * 12) +  # Slightly higher monthly payment
                acquisition_fee  # Pay acquisition fee again
            )
            
            five_year_lease_cost += additional_lease_cost
            
        # Compare monthly costs
        monthly_buy_cost = down_payment / 60 + emi  # Spread down payment over 5 years
        monthly_lease_cost = lease_down_payment / (lease_years * 12) + monthly_lease
        
        # Generate recommendation
        if net_buying_cost < five_year_lease_cost:
            recommendation = "Buying is likely more economical long-term"
            recommendation_detail = f"Buying saves approximately ₹{round(five_year_lease_cost - net_buying_cost):,} over 5 years"
        else:
            recommendation = "Leasing may be more economical for your situation"
            recommendation_detail = f"Leasing saves approximately ₹{round(net_buying_cost - five_year_lease_cost):,} over 5 years"
            
        return {
            'buying': {
                'initial_costs': {
                    'down_payment': round(down_payment),
                    'taxes_fees': round(vehicle_cost * 0.05)  # Estimate taxes and fees
                },
                'monthly_loan_payment': round(emi),
                'total_interest_paid': round(loan_interest),
                'total_5_year_cost': round(total_buying_cost),
                'estimated_resale_value': round(resale_value),
                'net_5_year_cost': round(net_buying_cost)
            },
            'leasing': {
                'initial_costs': {
                    'down_payment': round(lease_down_payment),
                    'acquisition_fee': round(acquisition_fee)
                },
                'monthly_lease_payment': round(monthly_lease),
                'lease_term_years': lease_years,
                'end_of_lease_fees': round(disposition_fee),
                'total_lease_term_cost': round(total_lease_cost),
                'equivalent_5_year_cost': round(five_year_lease_cost)
            },
            'monthly_comparison': {
                'buying': round(monthly_buy_cost),
                'leasing': round(monthly_lease_cost),
                'difference': round(abs(monthly_buy_cost - monthly_lease_cost)),
                'lower_option': 'Buying' if monthly_buy_cost < monthly_lease_cost else 'Leasing'
            },
            'recommendation': recommendation,
            'recommendation_detail': recommendation_detail,
            'additional_considerations': [
                "Buying builds equity and has no mileage restrictions",
                "Leasing provides a new vehicle every few years with lower repair costs",
                "Buying allows customization and modifications to the vehicle",
                "Leasing may include warranty coverage for the entire lease term"
            ]
        }
    
    def _extract_vehicle_parameters(self, goal) -> tuple:
        """
        Extract vehicle type, cost and whether it's new from goal data.
        
        Returns:
            tuple: (vehicle_type, vehicle_cost, is_new)
        """
        # Default values
        vehicle_type = "sedan"  # Default vehicle type
        vehicle_cost = 0.0      # Default cost
        is_new = True           # Default to new vehicle
        
        # Try to extract from goal
        if isinstance(goal, dict):
            # Get target amount as base cost
            vehicle_cost = goal.get('target_amount', 0)
            
            if 'metadata' in goal and goal['metadata']:
                try:
                    metadata = json.loads(goal['metadata'])
                    if 'vehicle_type' in metadata:
                        vehicle_type = metadata['vehicle_type'].lower()
                    if 'is_new' in metadata:
                        is_new = bool(metadata['is_new'])
                    if 'vehicle_cost' in metadata and vehicle_cost <= 0:
                        vehicle_cost = float(metadata['vehicle_cost'])
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
                    
            # Try to extract from notes
            if 'notes' in goal and goal['notes']:
                notes = goal['notes'].lower()
                
                # Check for vehicle type mentions
                if any(term in notes for term in ['suv', 'sport utility']):
                    vehicle_type = "suv"
                elif any(term in notes for term in ['hatchback', 'hatch']):
                    vehicle_type = "hatchback"
                elif any(term in notes for term in ['sedan']):
                    vehicle_type = "sedan"
                elif any(term in notes for term in ['luxury', 'premium']):
                    vehicle_type = "luxury"
                    
                # Check for new/used mentions
                if any(term in notes for term in ['used', 'second hand', 'pre-owned', 'preowned']):
                    is_new = False
                elif any(term in notes for term in ['new']):
                    is_new = True
                    
                # Try to extract cost if not already set
                if vehicle_cost <= 0:
                    import re
                    cost_matches = re.findall(r'(?:cost|price|value)[^\d]*\$?(\d+(?:,\d+)*(?:\.\d+)?)', notes)
                    if cost_matches:
                        try:
                            vehicle_cost = float(cost_matches[0].replace(',', ''))
                        except ValueError:
                            pass
        elif hasattr(goal, 'metadata') and goal.metadata:
            # Object-based goal
            # Get target amount as base cost
            vehicle_cost = getattr(goal, 'target_amount', 0)
            
            try:
                metadata = json.loads(goal.metadata)
                if 'vehicle_type' in metadata:
                    vehicle_type = metadata['vehicle_type'].lower()
                if 'is_new' in metadata:
                    is_new = bool(metadata['is_new'])
                if 'vehicle_cost' in metadata and vehicle_cost <= 0:
                    vehicle_cost = float(metadata['vehicle_cost'])
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
                
            # Try to extract from notes
            if hasattr(goal, 'notes') and goal.notes:
                notes = goal.notes.lower()
                
                # Check for vehicle type mentions
                if any(term in notes for term in ['suv', 'sport utility']):
                    vehicle_type = "suv"
                elif any(term in notes for term in ['hatchback', 'hatch']):
                    vehicle_type = "hatchback"
                elif any(term in notes for term in ['sedan']):
                    vehicle_type = "sedan"
                elif any(term in notes for term in ['luxury', 'premium']):
                    vehicle_type = "luxury"
                    
                # Check for new/used mentions
                if any(term in notes for term in ['used', 'second hand', 'pre-owned', 'preowned']):
                    is_new = False
                elif any(term in notes for term in ['new']):
                    is_new = True
                    
                # Try to extract cost if not already set
                if vehicle_cost <= 0:
                    import re
                    cost_matches = re.findall(r'(?:cost|price|value)[^\d]*\$?(\d+(?:,\d+)*(?:\.\d+)?)', notes)
                    if cost_matches:
                        try:
                            vehicle_cost = float(cost_matches[0].replace(',', ''))
                        except ValueError:
                            pass
        
        # If cost still not set, estimate based on vehicle type and condition
        if vehicle_cost <= 0:
            if vehicle_type == "luxury":
                base_cost = 5000000  # ₹50 lakh for luxury
            elif vehicle_type == "suv":
                base_cost = 1500000  # ₹15 lakh for SUV
            elif vehicle_type == "sedan":
                base_cost = 1000000  # ₹10 lakh for sedan
            else:  # hatchback or default
                base_cost = 700000   # ₹7 lakh for hatchback
                
            # Adjust for new/used
            if not is_new:
                base_cost *= 0.6  # 60% of new price for used
                
            vehicle_cost = base_cost
            
        return vehicle_type, vehicle_cost, is_new
    
    def _calculate_monthly_fuel_cost(self, vehicle_type: str) -> float:
        """Calculate monthly fuel cost based on vehicle type"""
        # Average monthly driving distance (in km)
        monthly_distance = 1250  # 15,000 km per year
        
        # Fuel efficiency by vehicle type (km/L)
        if vehicle_type == "luxury":
            fuel_efficiency = 8  # 8 km/L
        elif vehicle_type == "suv":
            fuel_efficiency = 12  # 12 km/L
        elif vehicle_type == "sedan":
            fuel_efficiency = 15  # 15 km/L
        else:  # hatchback or default
            fuel_efficiency = 18  # 18 km/L
            
        # Fuel price per liter (in INR)
        fuel_price = 100  # ₹100 per liter
        
        # Calculate monthly fuel consumption and cost
        monthly_fuel_consumption = monthly_distance / fuel_efficiency
        monthly_fuel_cost = monthly_fuel_consumption * fuel_price
        
        return monthly_fuel_cost
    
    def _calculate_annual_insurance(self, vehicle_type: str, vehicle_cost: float, is_new: bool) -> float:
        """Calculate annual insurance cost"""
        # Base insurance rate as percentage of vehicle value
        if is_new:
            if vehicle_type == "luxury":
                insurance_rate = 0.03  # 3% for luxury
            elif vehicle_type == "suv":
                insurance_rate = 0.025  # 2.5% for SUV
            else:
                insurance_rate = 0.02  # 2% for sedan/hatchback
        else:
            if vehicle_type == "luxury":
                insurance_rate = 0.04  # 4% for luxury
            elif vehicle_type == "suv":
                insurance_rate = 0.035  # 3.5% for SUV
            else:
                insurance_rate = 0.03  # 3% for sedan/hatchback
                
        annual_insurance = vehicle_cost * insurance_rate
        return annual_insurance
    
    def _calculate_loan_interest(self, vehicle_cost: float, goal, profile: Dict[str, Any]) -> float:
        """Calculate total loan interest over the life of the loan"""
        # Assume 80% financing
        loan_amount = vehicle_cost * 0.8
        
        # Loan term (in years)
        loan_term = 5
        
        # Interest rate
        interest_rate = 0.085  # 8.5% for vehicle loan
        
        # Calculate total interest using EMI formula
        monthly_rate = interest_rate / 12
        num_payments = loan_term * 12
        
        if monthly_rate > 0:
            emi = loan_amount * (
                (monthly_rate * ((1 + monthly_rate) ** num_payments)) / 
                (((1 + monthly_rate) ** num_payments) - 1)
            )
            total_payments = emi * num_payments
            total_interest = total_payments - loan_amount
        else:
            total_interest = 0
            
        return total_interest