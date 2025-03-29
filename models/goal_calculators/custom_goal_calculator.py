import json
import logging
from typing import Dict, Any, List

from .base_calculator import GoalCalculator

logger = logging.getLogger(__name__)

class CustomGoalCalculator(GoalCalculator):
    """Calculator for custom user-defined goals that don't fit standard categories"""
    
    def calculate_amount_needed(self, goal, profile: Dict[str, Any]) -> float:
        """
        Calculate the amount needed for a custom goal.
        
        Args:
            goal: The custom goal
            profile: User profile
            
        Returns:
            float: Calculated amount needed
        """
        # Extract user_id for parameter access
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        # Special handling for test cases
        if isinstance(goal, dict) and goal.get('id') == 'custom-test':
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
        
        # Extract goal parameters
        goal_nature, goal_scope, time_until_goal = self._extract_custom_goal_parameters(goal, profile)
        
        # Get goal allocation percentages from parameters based on goal nature and scope
        if goal_nature == "asset_acquisition":
            # Use income-based estimation for asset acquisition
            monthly_income = self._get_monthly_income(profile)
            annual_income = monthly_income * 12
            
            if goal_scope == "major":
                # Get parameter for major asset acquisition
                allocation_pct = self.get_parameter("custom.allocation_percent.asset.major", 1.0, user_id)  # Default 100% of annual income
                base_amount = annual_income * allocation_pct
            elif goal_scope == "moderate":
                # Get parameter for moderate asset acquisition
                allocation_pct = self.get_parameter("custom.allocation_percent.asset.moderate", 0.5, user_id)  # Default 50% of annual income
                base_amount = annual_income * allocation_pct
            else:  # minor
                # Get parameter for minor asset acquisition
                allocation_pct = self.get_parameter("custom.allocation_percent.asset.minor", 0.2, user_id)  # Default 20% of annual income
                base_amount = annual_income * allocation_pct
                
        elif goal_nature == "experience":
            # Experience goals typically cost less than asset acquisition
            monthly_income = self._get_monthly_income(profile)
            annual_income = monthly_income * 12
            
            if goal_scope == "major":
                # Get parameter for major experience
                allocation_pct = self.get_parameter("custom.allocation_percent.experience.major", 0.5, user_id)  # Default 50% of annual income
                base_amount = annual_income * allocation_pct
            elif goal_scope == "moderate":
                # Get parameter for moderate experience
                allocation_pct = self.get_parameter("custom.allocation_percent.experience.moderate", 0.25, user_id)  # Default 25% of annual income
                base_amount = annual_income * allocation_pct
            else:  # minor
                # Get parameter for minor experience
                allocation_pct = self.get_parameter("custom.allocation_percent.experience.minor", 0.1, user_id)  # Default 10% of annual income
                base_amount = annual_income * allocation_pct
                
        elif goal_nature == "achievement":
            # Achievement goals vary widely but often involve education or skills
            monthly_income = self._get_monthly_income(profile)
            annual_income = monthly_income * 12
            
            if goal_scope == "major":
                # Get parameter for major achievement
                allocation_pct = self.get_parameter("custom.allocation_percent.achievement.major", 0.75, user_id)  # Default 75% of annual income
                base_amount = annual_income * allocation_pct
            elif goal_scope == "moderate":
                # Get parameter for moderate achievement
                allocation_pct = self.get_parameter("custom.allocation_percent.achievement.moderate", 0.3, user_id)  # Default 30% of annual income
                base_amount = annual_income * allocation_pct
            else:  # minor
                # Get parameter for minor achievement
                allocation_pct = self.get_parameter("custom.allocation_percent.achievement.minor", 0.15, user_id)  # Default 15% of annual income
                base_amount = annual_income * allocation_pct
                
        else:
            # Default estimation based on income
            monthly_income = self._get_monthly_income(profile)
            annual_income = monthly_income * 12
            
            # Get default allocation percentage
            allocation_pct = self.get_parameter("custom.allocation_percent.default", 0.4, user_id)  # Default 40% of annual income
            base_amount = annual_income * allocation_pct
        
        # Get inflation rate from parameters
        inflation_rate = self.get_parameter("inflation.general", 0.06, user_id)
        
        # Adjust for inflation
        inflated_amount = base_amount * ((1 + inflation_rate) ** time_until_goal)
        
        return inflated_amount
    
    def analyze_goal_characteristics(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze characteristics of a custom goal for better planning.
        
        Args:
            goal: The custom goal
            profile: User profile
            
        Returns:
            dict: Goal characteristics analysis
        """
        # Extract goal parameters
        goal_nature, goal_scope, time_until_goal = self._extract_custom_goal_parameters(goal, profile)
        
        # Get goal title and description
        if isinstance(goal, dict):
            goal_title = goal.get('title', 'Custom Goal')
            goal_description = goal.get('notes', '')
        else:
            goal_title = getattr(goal, 'title', 'Custom Goal')
            goal_description = getattr(goal, 'notes', '')
        
        # Classify goal characteristics
        time_sensitivity = self._classify_time_sensitivity(time_until_goal)
        financial_impact = self._classify_financial_impact(goal, profile)
        goal_flexibility = self._classify_flexibility(goal)
        
        # Generate suitability score for different funding approaches
        funding_approaches = self._evaluate_funding_approaches(
            time_sensitivity, financial_impact, goal_flexibility
        )
        
        # Determine recommended investment vehicles
        recommended_investments = self._recommend_investment_vehicles(
            time_until_goal, goal_nature, profile
        )
        
        # Assess opportunity cost and tradeoffs
        opportunity_cost = self._assess_opportunity_cost(goal, profile)
        
        return {
            'goal_title': goal_title,
            'goal_nature': goal_nature,
            'goal_scope': goal_scope,
            'time_until_goal_years': round(time_until_goal, 1),
            'characteristics': {
                'time_sensitivity': time_sensitivity,
                'financial_impact': financial_impact,
                'flexibility': goal_flexibility
            },
            'funding_approach_suitability': funding_approaches,
            'recommended_investments': recommended_investments,
            'opportunity_cost': opportunity_cost,
            'key_considerations': self._generate_key_considerations(
                goal_nature, goal_scope, time_sensitivity, financial_impact
            )
        }
    
    def generate_milestone_plan(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a milestone-based plan for achieving a custom goal.
        
        Args:
            goal: The custom goal
            profile: User profile
            
        Returns:
            dict: Milestone-based plan
        """
        # Get target amount and timeframe
        if isinstance(goal, dict):
            target_amount = goal.get('target_amount', 0)
            if target_amount <= 0:
                target_amount = self.calculate_amount_needed(goal, profile)
        else:
            target_amount = getattr(goal, 'target_amount', 0)
            if target_amount <= 0:
                target_amount = self.calculate_amount_needed(goal, profile)
                
        # Calculate time to goal in years
        months_to_goal = self.calculate_time_available(goal, profile)
        years_to_goal = months_to_goal / 12
        
        # Extract goal parameters
        goal_nature, goal_scope, _ = self._extract_custom_goal_parameters(goal, profile)
        
        # Determine number of milestones based on timeframe
        if years_to_goal < 1:
            num_milestones = 2  # Very short-term
        elif years_to_goal < 3:
            num_milestones = 3  # Short-term
        elif years_to_goal < 5:
            num_milestones = 4  # Medium-term
        else:
            num_milestones = 5  # Long-term
            
        # Create milestone percentages
        if goal_nature == "asset_acquisition":
            # Front-loaded for asset acquisition (need more funds earlier)
            milestone_percentages = self._generate_milestone_percentages(num_milestones, "front_loaded")
        elif goal_nature == "experience":
            # Back-loaded for experiences (need funds closer to goal date)
            milestone_percentages = self._generate_milestone_percentages(num_milestones, "back_loaded")
        else:
            # Even distribution for other goals
            milestone_percentages = self._generate_milestone_percentages(num_milestones, "even")
            
        # Calculate milestone amounts
        milestone_amounts = [target_amount * pct for pct in milestone_percentages]
        
        # Calculate milestone timing
        milestone_timing = []
        for i in range(num_milestones):
            milestone_timing.append(years_to_goal * (i + 1) / num_milestones)
            
        # Generate milestone plan
        milestones = []
        for i in range(num_milestones):
            milestone = {
                'milestone_number': i + 1,
                'description': self._generate_milestone_description(
                    i + 1, num_milestones, goal_nature, goal_scope
                ),
                'target_percentage': f"{milestone_percentages[i]*100:.1f}%",
                'target_amount': round(milestone_amounts[i]),
                'timing_years': round(milestone_timing[i], 1),
                'key_actions': self._generate_milestone_actions(
                    i + 1, num_milestones, goal_nature, goal_scope
                )
            }
            milestones.append(milestone)
            
        return {
            'total_goal_amount': round(target_amount),
            'total_timeframe_years': round(years_to_goal, 1),
            'number_of_milestones': num_milestones,
            'milestones': milestones,
            'success_metrics': self._generate_success_metrics(goal_nature, goal_scope),
            'adjustment_strategy': "Review progress quarterly and adjust milestone targets as needed"
        }
    
    def _extract_custom_goal_parameters(self, goal, profile: Dict[str, Any]) -> tuple:
        """
        Extract goal nature, scope, and time until goal from custom goal data.
        
        Returns:
            tuple: (goal_nature, goal_scope, time_until_goal)
        """
        # Default values
        goal_nature = "general"    # Default nature
        goal_scope = "moderate"    # Default scope
        time_until_goal = 3.0      # Default 3 years
        
        # Try to extract from goal
        if isinstance(goal, dict):
            if 'metadata' in goal and goal['metadata']:
                try:
                    metadata = json.loads(goal['metadata'])
                    if 'goal_nature' in metadata:
                        nature_val = metadata['goal_nature'].lower()
                        if nature_val in ['asset_acquisition', 'experience', 'achievement']:
                            goal_nature = nature_val
                            
                    if 'goal_scope' in metadata:
                        scope_val = metadata['goal_scope'].lower()
                        if scope_val in ['major', 'moderate', 'minor']:
                            goal_scope = scope_val
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
                    
            # Try notes field
            if 'notes' in goal and goal['notes']:
                notes = goal['notes'].lower()
                
                # Check for goal nature mentions
                if any(term in notes for term in ['purchase', 'buy', 'acquire', 'asset']):
                    goal_nature = "asset_acquisition"
                elif any(term in notes for term in ['experience', 'travel', 'event', 'attend']):
                    goal_nature = "experience"
                elif any(term in notes for term in ['achieve', 'certification', 'degree', 'complete']):
                    goal_nature = "achievement"
                    
                # Check for scope mentions
                if any(term in notes for term in ['major', 'significant', 'substantial']):
                    goal_scope = "major"
                elif any(term in notes for term in ['minor', 'small', 'modest']):
                    goal_scope = "minor"
                    
            # Calculate time until goal (years)
            months = self.calculate_time_available(goal, profile)
            time_until_goal = months / 12
        elif hasattr(goal, 'metadata') and goal.metadata:
            # Object-based goal
            try:
                metadata = json.loads(goal.metadata)
                if 'goal_nature' in metadata:
                    nature_val = metadata['goal_nature'].lower()
                    if nature_val in ['asset_acquisition', 'experience', 'achievement']:
                        goal_nature = nature_val
                        
                if 'goal_scope' in metadata:
                    scope_val = metadata['goal_scope'].lower()
                    if scope_val in ['major', 'moderate', 'minor']:
                        goal_scope = scope_val
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
                
            # Try notes field
            if hasattr(goal, 'notes') and goal.notes:
                notes = goal.notes.lower()
                
                # Check for goal nature mentions
                if any(term in notes for term in ['purchase', 'buy', 'acquire', 'asset']):
                    goal_nature = "asset_acquisition"
                elif any(term in notes for term in ['experience', 'travel', 'event', 'attend']):
                    goal_nature = "experience"
                elif any(term in notes for term in ['achieve', 'certification', 'degree', 'complete']):
                    goal_nature = "achievement"
                    
                # Check for scope mentions
                if any(term in notes for term in ['major', 'significant', 'substantial']):
                    goal_scope = "major"
                elif any(term in notes for term in ['minor', 'small', 'modest']):
                    goal_scope = "minor"
                    
            # Calculate time until goal (years)
            months = self.calculate_time_available(goal, profile)
            time_until_goal = months / 12
        
        return goal_nature, goal_scope, time_until_goal
    
    def _classify_time_sensitivity(self, time_until_goal: float) -> Dict[str, Any]:
        """Classify the time sensitivity of the goal"""
        if time_until_goal < 1:
            sensitivity = "urgent"
            description = "Goal is urgent with less than 1 year timeframe"
            flexibility = "low"
        elif time_until_goal < 3:
            sensitivity = "high"
            description = "Goal has high time sensitivity with 1-3 year timeframe"
            flexibility = "moderate"
        elif time_until_goal < 5:
            sensitivity = "moderate"
            description = "Goal has moderate time sensitivity with 3-5 year timeframe"
            flexibility = "moderate"
        else:
            sensitivity = "low"
            description = "Goal has low time sensitivity with more than 5 years available"
            flexibility = "high"
            
        return {
            'level': sensitivity,
            'description': description,
            'timing_flexibility': flexibility
        }
    
    def _classify_financial_impact(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the financial impact of the goal"""
        # Get target amount and income
        target_amount = self.calculate_amount_needed(goal, profile)
        monthly_income = self._get_monthly_income(profile)
        annual_income = monthly_income * 12
        
        # Calculate goal-to-income ratio
        if annual_income > 0:
            ratio = target_amount / annual_income
        else:
            ratio = float('inf')
            
        # Calculate monthly contribution
        monthly_contribution = self.calculate_monthly_contribution(goal, profile)
        
        # Calculate contribution-to-income ratio
        if monthly_income > 0:
            contribution_ratio = monthly_contribution / monthly_income
        else:
            contribution_ratio = float('inf')
            
        # Determine impact level
        if ratio > 1.0 or contribution_ratio > 0.3:
            impact = "high"
            description = "Goal requires significant financial resources"
        elif ratio > 0.5 or contribution_ratio > 0.15:
            impact = "moderate"
            description = "Goal requires moderate financial commitment"
        else:
            impact = "low"
            description = "Goal requires relatively modest financial resources"
            
        return {
            'level': impact,
            'description': description,
            'goal_to_income_ratio': round(ratio, 2),
            'monthly_contribution_to_income_ratio': round(contribution_ratio, 2)
        }
    
    def _classify_flexibility(self, goal) -> Dict[str, Any]:
        """Classify the flexibility of the goal"""
        # Default flexibility is moderate
        flexibility = "moderate"
        description = "Goal has moderate flexibility in timing and amount"
        
        # Try to extract from goal
        if isinstance(goal, dict):
            if 'flexibility' in goal:
                flexibility_value = goal['flexibility'].lower()
                if 'fixed' in flexibility_value or 'low' in flexibility_value:
                    flexibility = "low"
                    description = "Goal has low flexibility with fixed parameters"
                elif 'very' in flexibility_value or 'high' in flexibility_value:
                    flexibility = "high"
                    description = "Goal has high flexibility with adaptable parameters"
            
            # Check importance as a proxy for flexibility
            if 'importance' in goal:
                importance = goal['importance'].lower()
                if 'high' in importance:
                    # High importance often means lower flexibility
                    if flexibility != "low":
                        flexibility = "moderate"
                        description = "Goal has moderate flexibility due to high importance"
                elif 'low' in importance:
                    # Low importance often means higher flexibility
                    if flexibility != "high":
                        flexibility = "moderate"
                        description = "Goal has moderate flexibility due to lower importance"
        elif hasattr(goal, 'flexibility'):
            flexibility_value = goal.flexibility.lower()
            if 'fixed' in flexibility_value or 'low' in flexibility_value:
                flexibility = "low"
                description = "Goal has low flexibility with fixed parameters"
            elif 'very' in flexibility_value or 'high' in flexibility_value:
                flexibility = "high"
                description = "Goal has high flexibility with adaptable parameters"
            
            # Check importance as a proxy for flexibility
            if hasattr(goal, 'importance'):
                importance = goal.importance.lower()
                if 'high' in importance:
                    # High importance often means lower flexibility
                    if flexibility != "low":
                        flexibility = "moderate"
                        description = "Goal has moderate flexibility due to high importance"
                elif 'low' in importance:
                    # Low importance often means higher flexibility
                    if flexibility != "high":
                        flexibility = "moderate"
                        description = "Goal has moderate flexibility due to lower importance"
        
        return {
            'level': flexibility,
            'description': description
        }
    
    def _evaluate_funding_approaches(self, time_sensitivity: Dict[str, Any], 
                                  financial_impact: Dict[str, Any],
                                  flexibility: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate suitability of different funding approaches"""
        approaches = []
        
        # Regular contributions approach
        regular_score = 0
        if time_sensitivity['level'] in ['moderate', 'low']:
            regular_score += 2
        elif time_sensitivity['level'] == 'high':
            regular_score += 1
            
        if financial_impact['monthly_contribution_to_income_ratio'] < 0.15:
            regular_score += 2
        elif financial_impact['monthly_contribution_to_income_ratio'] < 0.3:
            regular_score += 1
            
        approaches.append({
            'approach': 'Regular Contributions',
            'suitability_score': regular_score,
            'suitability_level': 'High' if regular_score >= 3 else 'Medium' if regular_score >= 2 else 'Low',
            'description': "Consistent monthly contributions towards the goal",
            'best_for': [
                "Goals with longer timeframes",
                "Goals requiring manageable monthly contributions",
                "Individuals with stable income"
            ]
        })
        
        # Milestone funding approach
        milestone_score = 0
        if financial_impact['level'] in ['moderate', 'high']:
            milestone_score += 2
        else:
            milestone_score += 1
            
        if flexibility['level'] in ['moderate', 'high']:
            milestone_score += 2
        else:
            milestone_score += 1
            
        approaches.append({
            'approach': 'Milestone Funding',
            'suitability_score': milestone_score,
            'suitability_level': 'High' if milestone_score >= 3 else 'Medium' if milestone_score >= 2 else 'Low',
            'description': "Fund goal in distinct phases or milestones",
            'best_for': [
                "Goals that can be broken into stages",
                "Individuals with variable income",
                "Goals with moderate to high flexibility"
            ]
        })
        
        # Lump sum approach
        lump_score = 0
        if time_sensitivity['level'] == 'urgent':
            lump_score += 2
        elif time_sensitivity['level'] == 'high':
            lump_score += 1
            
        if financial_impact['level'] == 'low':
            lump_score += 2
        elif financial_impact['level'] == 'moderate':
            lump_score += 1
            
        approaches.append({
            'approach': 'Lump Sum Funding',
            'suitability_score': lump_score,
            'suitability_level': 'High' if lump_score >= 3 else 'Medium' if lump_score >= 2 else 'Low',
            'description': "Fund entire goal at once from savings or windfalls",
            'best_for': [
                "Urgent or time-sensitive goals",
                "Smaller goals with low financial impact",
                "Individuals with substantial liquid savings"
            ]
        })
        
        # Hybrid approach
        hybrid_score = 0
        if time_sensitivity['level'] in ['moderate', 'high']:
            hybrid_score += 2
        else:
            hybrid_score += 1
            
        if financial_impact['level'] == 'moderate':
            hybrid_score += 2
        else:
            hybrid_score += 1
            
        approaches.append({
            'approach': 'Hybrid Funding',
            'suitability_score': hybrid_score,
            'suitability_level': 'High' if hybrid_score >= 3 else 'Medium' if hybrid_score >= 2 else 'Low',
            'description': "Combination of regular contributions and milestone funding",
            'best_for': [
                "Complex goals with multiple components",
                "Goals with moderate time sensitivity",
                "Individuals with both regular income and periodic windfalls"
            ]
        })
        
        # Sort by suitability score (highest first)
        approaches.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return approaches
    
    def _recommend_investment_vehicles(self, time_until_goal: float, goal_nature: str, 
                                     profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend appropriate investment vehicles based on goal parameters"""
        # Extract user_id for parameter access
        user_id = profile.get('user_id') if isinstance(profile, dict) else None
        
        vehicles = []
        
        # Get risk profile
        risk_profile = self._get_risk_profile(profile)
        
        # Get short-term allocation percentages from parameters
        short_term_liquid_allocation = self.get_parameter("custom.investment.short_term.liquid_allocation", [60, 80], user_id)
        short_term_fixed_allocation = self.get_parameter("custom.investment.short_term.fixed_allocation", [20, 40], user_id)
        
        # Short-term vehicles (< 1 year)
        if time_until_goal < 1:
            vehicles.append({
                'vehicle': 'Liquid Funds',
                'suitability': 'High',
                'allocation_percentage': f'{short_term_liquid_allocation[0]}-{short_term_liquid_allocation[1]}%',
                'rationale': "Provides liquidity with minimal volatility for short time horizon"
            })
            
            vehicles.append({
                'vehicle': 'Short-term Fixed Deposits',
                'suitability': 'High',
                'allocation_percentage': f'{short_term_fixed_allocation[0]}-{short_term_fixed_allocation[1]}%',
                'rationale': "Provides slightly higher returns with minimal risk"
            })
            
        # Medium-term vehicles (1-3 years)
        elif time_until_goal < 3:
            if risk_profile == 'conservative':
                vehicles.append({
                    'vehicle': 'Ultra Short-term Debt Funds',
                    'suitability': 'High',
                    'allocation_percentage': '60-70%',
                    'rationale': "Provides stability with slightly better returns than liquid funds"
                })
                
                vehicles.append({
                    'vehicle': 'Fixed Deposits',
                    'suitability': 'High',
                    'allocation_percentage': '30-40%',
                    'rationale': "Provides guaranteed returns for medium-term goals"
                })
            else:
                vehicles.append({
                    'vehicle': 'Short-term Debt Funds',
                    'suitability': 'High',
                    'allocation_percentage': '50-60%',
                    'rationale': "Provides balance of returns and stability"
                })
                
                vehicles.append({
                    'vehicle': 'Balanced Advantage Funds',
                    'suitability': 'Medium',
                    'allocation_percentage': '20-30%',
                    'rationale': "Provides exposure to equity with risk management"
                })
                
                vehicles.append({
                    'vehicle': 'Fixed Deposits',
                    'suitability': 'Medium',
                    'allocation_percentage': '20-30%',
                    'rationale': "Provides stability to overall portfolio"
                })
                
        # Longer-term vehicles (3+ years)
        else:
            if risk_profile == 'conservative':
                vehicles.append({
                    'vehicle': 'Corporate Bond Funds',
                    'suitability': 'High',
                    'allocation_percentage': '50-60%',
                    'rationale': "Provides stable returns with moderate risk"
                })
                
                vehicles.append({
                    'vehicle': 'Conservative Hybrid Funds',
                    'suitability': 'Medium',
                    'allocation_percentage': '20-30%',
                    'rationale': "Provides balanced exposure to debt and equity"
                })
                
                vehicles.append({
                    'vehicle': 'PPF/Long-term FDs',
                    'suitability': 'Medium',
                    'allocation_percentage': '20-30%',
                    'rationale': "Provides tax-efficient returns for long-term goals"
                })
            elif risk_profile == 'moderate':
                vehicles.append({
                    'vehicle': 'Hybrid Equity Funds',
                    'suitability': 'High',
                    'allocation_percentage': '40-50%',
                    'rationale': "Provides balanced growth with moderate risk"
                })
                
                vehicles.append({
                    'vehicle': 'Index Funds',
                    'suitability': 'Medium',
                    'allocation_percentage': '30-40%',
                    'rationale': "Provides market returns with lower costs"
                })
                
                vehicles.append({
                    'vehicle': 'Corporate Bond Funds',
                    'suitability': 'Medium',
                    'allocation_percentage': '20-30%',
                    'rationale': "Provides stability to overall portfolio"
                })
            else:  # Aggressive
                vehicles.append({
                    'vehicle': 'Equity Funds',
                    'suitability': 'High',
                    'allocation_percentage': '60-70%',
                    'rationale': "Provides growth potential for long-term goals"
                })
                
                vehicles.append({
                    'vehicle': 'Index Funds',
                    'suitability': 'Medium',
                    'allocation_percentage': '20-30%',
                    'rationale': "Provides market returns with lower costs"
                })
                
                vehicles.append({
                    'vehicle': 'Hybrid Funds',
                    'suitability': 'Medium',
                    'allocation_percentage': '10-20%',
                    'rationale': "Provides some stability to equity-heavy portfolio"
                })
        
        # Adjust based on goal nature
        if goal_nature == "asset_acquisition" and time_until_goal > 3:
            # Special case: Consider specialized products for specific assets
            vehicles.append({
                'vehicle': 'Dedicated Goal-based Funds',
                'suitability': 'Medium',
                'allocation_percentage': '10-20%',
                'rationale': "Specialized products aligned with specific goal objectives"
            })
            
        return vehicles
    
    def _assess_opportunity_cost(self, goal, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Assess opportunity cost and tradeoffs of the goal"""
        # Calculate goal amount
        target_amount = self.calculate_amount_needed(goal, profile)
        
        # Calculate monthly contribution
        monthly_contribution = self.calculate_monthly_contribution(goal, profile)
        
        # Get time to goal in years
        months_to_goal = self.calculate_time_available(goal, profile)
        years_to_goal = months_to_goal / 12
        
        # Calculate what the money could grow to if invested for retirement instead
        # Assume 30 years until retirement (simplified)
        retirement_years = 30
        if 'age' in profile:
            age = profile['age']
            if isinstance(age, (int, float)) and age > 0:
                retirement_years = max(1, 60 - age)  # Assuming retirement at 60
                
        # Assume 9% average return for long-term equity investments
        equity_return = 0.09
        
        # Calculate future value of lump sum
        retirement_value_lump = target_amount * ((1 + equity_return) ** retirement_years)
        
        # Calculate future value of monthly contributions
        monthly_rate = equity_return / 12
        retirement_value_monthly = monthly_contribution * (
            ((1 + monthly_rate) ** (retirement_years * 12) - 1) / monthly_rate
        ) * (1 + monthly_rate)
        
        # Calculate retirement income these values could provide
        # Using 4% safe withdrawal rate
        annual_retirement_income_lump = retirement_value_lump * 0.04
        annual_retirement_income_monthly = retirement_value_monthly * 0.04
        
        return {
            'retirement_opportunity_cost': {
                'lump_sum_future_value': round(retirement_value_lump),
                'monthly_contributions_future_value': round(retirement_value_monthly),
                'potential_annual_retirement_income': round(annual_retirement_income_lump + annual_retirement_income_monthly),
                'assumptions': {
                    'years_to_retirement': retirement_years,
                    'annual_return': f"{equity_return*100:.1f}%",
                    'withdrawal_rate': "4.0%"
                }
            },
            'alternative_goals': self._suggest_alternative_goals(target_amount, monthly_contribution),
            'balanced_approach': self._suggest_balanced_approach(target_amount, monthly_contribution, years_to_goal)
        }
    
    def _suggest_alternative_goals(self, target_amount: float, monthly_contribution: float) -> List[Dict[str, Any]]:
        """Suggest alternative goals that could be funded with the same resources"""
        alternatives = []
        
        # Emergency fund
        if target_amount >= 200000:
            alternatives.append({
                'goal_type': 'Emergency Fund',
                'description': f"Build a ₹{min(target_amount, 600000):,.0f} emergency fund for financial security",
                'benefit': "Provides financial security and peace of mind"
            })
            
        # Education
        if target_amount >= 500000:
            alternatives.append({
                'goal_type': 'Education',
                'description': f"Fund professional certification or skill development courses",
                'benefit': "Increases earning potential and career opportunities"
            })
            
        # Debt repayment
        if monthly_contribution >= 5000:
            alternatives.append({
                'goal_type': 'Debt Repayment',
                'description': f"Accelerate debt repayment with ₹{monthly_contribution:,.0f} monthly",
                'benefit': "Reduces interest costs and improves financial health"
            })
            
        # Retirement boost
        alternatives.append({
            'goal_type': 'Retirement Boost',
            'description': f"Additional ₹{monthly_contribution:,.0f} monthly retirement contribution",
            'benefit': "Significantly increases long-term financial security"
        })
        
        # Home down payment
        if target_amount >= 1000000:
            alternatives.append({
                'goal_type': 'Home Down Payment',
                'description': f"Build ₹{target_amount:,.0f} towards home purchase",
                'benefit': "Builds equity and reduces housing costs long-term"
            })
            
        return alternatives
    
    def _suggest_balanced_approach(self, target_amount: float, monthly_contribution: float, 
                                years_to_goal: float) -> Dict[str, Any]:
        """Suggest a balanced approach to pursue the goal while minimizing opportunity cost"""
        # Base allocation percentages
        if years_to_goal < 1:
            # Very short-term: Prioritize goal over other objectives
            goal_allocation = 0.9  # 90% to goal
            other_allocation = 0.1  # 10% to other objectives
        elif years_to_goal < 3:
            # Short-term: Strong goal focus with some other objectives
            goal_allocation = 0.75  # 75% to goal
            other_allocation = 0.25  # 25% to other objectives
        elif years_to_goal < 5:
            # Medium-term: Balanced approach
            goal_allocation = 0.6  # 60% to goal
            other_allocation = 0.4  # 40% to other objectives
        else:
            # Long-term: More balanced with other financial priorities
            goal_allocation = 0.5  # 50% to goal
            other_allocation = 0.5  # 50% to other objectives
            
        # Calculate adjusted amounts
        adjusted_monthly = monthly_contribution * goal_allocation
        other_priorities_monthly = monthly_contribution * other_allocation
        
        # Calculate new timeline with reduced contribution
        if adjusted_monthly > 0:
            new_months = (target_amount / adjusted_monthly) * 0.9  # Assuming 10% return to simplify
            new_years = new_months / 12
            timeframe_extension = new_years - years_to_goal
        else:
            new_years = float('inf')
            timeframe_extension = float('inf')
            
        return {
            'recommended_monthly_to_goal': round(adjusted_monthly),
            'recommended_monthly_to_other_priorities': round(other_priorities_monthly),
            'new_estimated_timeframe_years': round(new_years, 1),
            'timeframe_extension_years': round(timeframe_extension, 1),
            'other_priorities_allocation': {
                'retirement': f"{other_allocation*0.5*100:.0f}%",  # 50% of other allocation
                'emergency_fund': f"{other_allocation*0.3*100:.0f}%",  # 30% of other allocation
                'other_essential_goals': f"{other_allocation*0.2*100:.0f}%"  # 20% of other allocation
            }
        }
    
    def _generate_key_considerations(self, goal_nature: str, goal_scope: str, 
                                  time_sensitivity: Dict[str, Any], 
                                  financial_impact: Dict[str, Any]) -> List[str]:
        """Generate key considerations for the custom goal"""
        considerations = []
        
        # Add general considerations
        considerations.append(f"Goal timeframe has {time_sensitivity['level']} sensitivity requiring appropriate investment strategy")
        considerations.append(f"Goal has {financial_impact['level']} financial impact requiring careful budgeting")
        
        # Add nature-specific considerations
        if goal_nature == "asset_acquisition":
            considerations.append("Asset goals often involve one-time large expenses; consider resale value in calculations")
            if goal_scope == "major":
                considerations.append("Major asset acquisition may require loan financing; evaluate interest costs")
        elif goal_nature == "experience":
            considerations.append("Experience goals provide intangible returns; weigh emotional benefits against financial costs")
            considerations.append("Experience costs may fluctuate; maintain flexibility in budget and timing")
        elif goal_nature == "achievement":
            considerations.append("Achievement goals often yield long-term returns through career/personal growth")
            considerations.append("Consider opportunity costs of time investment alongside financial costs")
            
        # Add timing considerations
        if time_sensitivity['level'] in ['urgent', 'high']:
            considerations.append("Short timeframe leaves limited room for investment growth; emphasize savings rate")
        else:
            considerations.append("Longer timeframe allows for compound growth; prioritize appropriate investment selection")
            
        # Add impact considerations
        if financial_impact['level'] in ['high', 'moderate']:
            considerations.append("Significant financial commitment; ensure goal aligns with core values and priorities")
            considerations.append("Consider impact on other financial objectives like retirement and emergency fund")
            
        return considerations
    
    def _generate_milestone_percentages(self, num_milestones: int, distribution: str) -> List[float]:
        """Generate milestone percentage distributions based on pattern"""
        if distribution == "front_loaded":
            # More in early milestones
            if num_milestones == 2:
                return [0.6, 0.4]
            elif num_milestones == 3:
                return [0.4, 0.35, 0.25]
            elif num_milestones == 4:
                return [0.35, 0.3, 0.2, 0.15]
            else:  # 5 milestones
                return [0.3, 0.25, 0.2, 0.15, 0.1]
        elif distribution == "back_loaded":
            # More in later milestones
            if num_milestones == 2:
                return [0.4, 0.6]
            elif num_milestones == 3:
                return [0.25, 0.35, 0.4]
            elif num_milestones == 4:
                return [0.15, 0.2, 0.3, 0.35]
            else:  # 5 milestones
                return [0.1, 0.15, 0.2, 0.25, 0.3]
        else:  # even distribution
            # Equal distribution
            percentage = 1.0 / num_milestones
            return [percentage] * num_milestones
    
    def _generate_milestone_description(self, milestone_num: int, total_milestones: int, 
                                      goal_nature: str, goal_scope: str) -> str:
        """Generate description for milestone based on goal characteristics"""
        if milestone_num == 1:
            if goal_nature == "asset_acquisition":
                return "Initial research and planning phase"
            elif goal_nature == "experience":
                return "Preliminary planning and research phase"
            else:
                return "Initial planning and preparation phase"
        elif milestone_num == total_milestones:
            return "Final goal achievement phase"
        elif milestone_num == 2 and total_milestones <= 3:
            if goal_nature == "asset_acquisition":
                return "Evaluation and selection phase"
            elif goal_nature == "experience":
                return "Booking and commitment phase"
            else:
                return "Development and progress phase"
        elif milestone_num == 2 and total_milestones > 3:
            return "Early development phase"
        elif milestone_num == total_milestones - 1:
            return "Pre-completion phase"
        else:
            return f"Intermediate development phase {milestone_num}"
    
    def _generate_milestone_actions(self, milestone_num: int, total_milestones: int, 
                                  goal_nature: str, goal_scope: str) -> List[str]:
        """Generate key actions for milestone based on goal characteristics"""
        actions = []
        
        if milestone_num == 1:
            actions.append("Establish detailed goal parameters and success criteria")
            actions.append("Research options and requirements thoroughly")
            actions.append("Create detailed budget and funding plan")
            
        elif milestone_num == total_milestones:
            actions.append("Complete final preparations for goal achievement")
            actions.append("Conduct final review of requirements and readiness")
            actions.append("Execute final stage of goal plan")
            
        elif milestone_num == 2 and total_milestones <= 3:
            if goal_nature == "asset_acquisition":
                actions.append("Compare specific options and narrow down choices")
                actions.append("Consult with experts if needed (e.g., agents, advisors)")
                actions.append("Prepare for final decision and commitment")
            elif goal_nature == "experience":
                actions.append("Finalize specific plans and make necessary reservations")
                actions.append("Secure required documentation or prerequisites")
                actions.append("Make partial payments or deposits if required")
            else:
                actions.append("Complete necessary prerequisites or requirements")
                actions.append("Evaluate progress and adjust plan if needed")
                actions.append("Prepare for final phase")
                
        elif milestone_num == 2 and total_milestones > 3:
            actions.append("Begin focused efforts toward goal achievement")
            actions.append("Refine plan based on research findings")
            actions.append("Build momentum with consistent progress")
            
        elif milestone_num == total_milestones - 1:
            actions.append("Finalize all major decisions and commitments")
            actions.append("Address any remaining obstacles or requirements")
            actions.append("Prepare for final execution phase")
            
        else:
            actions.append("Continue consistent progress toward goal")
            actions.append("Evaluate and adjust approach as needed")
            actions.append("Maintain focus and momentum")
            
        return actions
    
    def _generate_success_metrics(self, goal_nature: str, goal_scope: str) -> List[Dict[str, str]]:
        """Generate success metrics based on goal nature and scope"""
        metrics = []
        
        # Financial metrics
        metrics.append({
            'metric': 'Budget Adherence',
            'description': 'Stay within planned budget with <10% variance',
            'measurement': 'Actual costs vs. planned budget'
        })
        
        # Timeline metrics
        metrics.append({
            'metric': 'Timeline Adherence',
            'description': 'Complete goal within planned timeframe',
            'measurement': 'Actual completion date vs. target date'
        })
        
        # Nature-specific metrics
        if goal_nature == "asset_acquisition":
            metrics.append({
                'metric': 'Asset Quality',
                'description': 'Acquire asset meeting all specified requirements',
                'measurement': 'Checklist of desired features and qualities'
            })
            
            metrics.append({
                'metric': 'Value Retention',
                'description': 'Asset maintains or appreciates in value',
                'measurement': 'Asset value after acquisition vs. purchase price'
            })
            
        elif goal_nature == "experience":
            metrics.append({
                'metric': 'Experience Quality',
                'description': 'Experience meets or exceeds expectations',
                'measurement': 'Satisfaction rating (1-10 scale) post-experience'
            })
            
            metrics.append({
                'metric': 'Memory/Impact Value',
                'description': 'Experience creates lasting positive impact',
                'measurement': 'Reflection assessment 3-6 months after experience'
            })
            
        elif goal_nature == "achievement":
            metrics.append({
                'metric': 'Completion Quality',
                'description': 'Achievement meets recognized standards of excellence',
                'measurement': 'External validation or certification if applicable'
            })
            
            metrics.append({
                'metric': 'Skill/Knowledge Gain',
                'description': 'Measurable improvement in capabilities',
                'measurement': 'Before/after assessment of relevant skills'
            })
            
            metrics.append({
                'metric': 'Practical Application',
                'description': 'Achievement translates to practical benefits',
                'measurement': 'Instances of applying new abilities post-achievement'
            })
            
        # Scope-specific metrics
        if goal_scope == "major":
            metrics.append({
                'metric': 'Long-term Impact',
                'description': 'Goal creates sustained positive impact',
                'measurement': 'Benefits assessment 1-2 years after completion'
            })
            
        return metrics