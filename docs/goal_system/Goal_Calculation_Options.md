# Goal Calculation Options Guide

This document outlines the various calculation options available in the goal calculator system, including specialized calculators for different goal types.

## Overview

The goal calculator system provides specialized calculation methods for different types of financial goals, each with unique parameters and calculation approaches.

## Calculator Selection

The system automatically selects the appropriate calculator type based on the goal's category:

```python
from models.goal_calculator import GoalCalculator
from models.goal_models import Goal

# Create a goal 
retirement_goal = Goal(
    category="traditional_retirement",
    # other properties...
)

# Get the appropriate calculator
calculator = GoalCalculator.get_calculator_for_goal(retirement_goal)
# Returns an instance of RetirementCalculator
```

## Available Specialized Calculators

| Goal Category | Calculator Class | Specialized Features |
|---------------|-----------------|----------------------|
| emergency_fund | EmergencyFundCalculator | Based on monthly expenses |
| insurance | InsuranceCalculator | Life, health insurance calculations |
| home_purchase | HomeDownPaymentCalculator | Down payment + loan structure |
| education | EducationCalculator | Education inflation, scholarships |
| debt_elimination, debt_repayment | DebtEliminationCalculator | Interest rates, payoff strategies |
| early_retirement | EarlyRetirementCalculator | FIRE approach, withdrawal rates |
| traditional_retirement | RetirementCalculator | Income replacement, life expectancy |
| travel, lifestyle | LifestyleGoalCalculator | Discretionary spending approach |
| vehicle | VehicleCalculator | Depreciation, loan vs. cash |
| home_improvement | HomeImprovementCalculator | ROI on improvements |
| estate_planning | LegacyGoalCalculator | Inheritance planning |
| charitable_giving | CharitableGivingCalculator | Giving capacity, tax benefits |

## Core Calculation Methods

All calculator types implement these core methods:

```python
# Calculate the total amount needed for the goal
amount_needed = calculator.calculate_amount_needed(goal, profile)

# Calculate the months available until goal deadline
months = calculator.calculate_time_available(goal, profile)

# Calculate required monthly savings rate
monthly_savings = calculator.calculate_required_saving_rate(goal, profile)

# Calculate the probability of achieving the goal
probability = calculator.calculate_goal_success_probability(goal, profile)
```

## Specialized Calculation Examples

### Emergency Fund Calculator

```python
from models.goal_calculator import EmergencyFundCalculator

calculator = EmergencyFundCalculator()

# Monthly expenses in profile used to determine target amount
profile = {
    "monthly_expenses": 60000
}

goal = {
    "category": "emergency_fund",
    "title": "Emergency Fund",
    "target_amount": 0  # If not provided, will be calculated
}

# Calculates target amount as months × expenses
# Default is 6 months of expenses from parameters
amount = calculator.calculate_amount_needed(goal, profile)  # 360,000
```

### Retirement Calculator

```python
from models.goal_calculator import RetirementCalculator

calculator = RetirementCalculator()

profile = {
    "monthly_income": 150000,
    "age": 35,
    "retirement_age": 60
}

retirement_goal = {
    "category": "traditional_retirement",
    "timeframe": "2048-01-01"  # Or could use time_horizon in years
}

# Calculates corpus needed based on:
# - Years in retirement (life expectancy - retirement age)
# - Income replacement ratio (default 70%)
# - Inflation-adjusted withdrawal rate
# - Corpus multiplier from parameters
corpus_needed = calculator.calculate_amount_needed(retirement_goal, profile)

# Calculate monthly savings required
monthly_savings = calculator.calculate_required_saving_rate(retirement_goal, profile)
```

### Education Calculator

```python
from models.goal_calculator import EducationCalculator

calculator = EducationCalculator()

profile = {"risk_profile": "moderate"}

education_goal = {
    "category": "education",
    "title": "Child's College",
    "target_amount": 2500000,
    "timeframe": "2035-06-01"
}

# Uses education-specific inflation rate
# Considers scholarship probability
monthly_savings = calculator.calculate_required_saving_rate(education_goal, profile)

# Calculate goal success probability
# Considers funding gap analysis and time available
probability = calculator.calculate_goal_success_probability(education_goal, profile)
```

## Investment Return Rates

The calculator system uses different investment return rates based on:

1. **Goal Timeframe**: 
   - Short-term (0-3 years): Conservative returns
   - Medium-term (3-7 years): Moderate returns 
   - Long-term (7+ years): Aggressive returns

2. **Goal Flexibility**:
   - Fixed goals: More conservative allocation
   - Somewhat flexible: Moderate allocation
   - Very flexible: More aggressive allocation

3. **Goal Category**:
   - Security goals (emergency fund): Very conservative
   - Essential goals (home, education): Conservative to moderate
   - Aspirational goals (travel): Moderate to aggressive

## Extending with Custom Calculators

You can create custom calculators by extending the base calculator:

```python
from models.goal_calculator import GoalCalculator

class CustomGoalCalculator(GoalCalculator):
    """Calculator for a custom goal type"""
    
    def calculate_amount_needed(self, goal, profile):
        # Custom implementation
        base_amount = super().calculate_amount_needed(goal, profile)
        # Apply custom adjustments
        return base_amount * 1.2  # 20% buffer
    
    def calculate_required_saving_rate(self, goal, profile):
        # Custom implementation
        return super().calculate_required_saving_rate(goal, profile)
```

## Parameter Integration

All calculators integrate with the financial parameter system:

```python
# Inside a calculator method
inflation_rate = self.param_service.get("inflation.general")
education_inflation = self.param_service.get("inflation.education.college")
equity_return = self.param_service.get_asset_return("equity", "large_cap")
```

## Asset Allocation Recommendations

The calculator can provide asset allocation recommendations based on:

```python
# Get allocation model based on timeframe
timeframe_allocation = calculator._get_allocation_for_timeframe(goal, profile)

# Blend allocation based on goal type
allocation_strategy = calculator._get_recommended_allocation(goal, profile)
```

The allocation strategy is used in the `funding_strategy` field of the goal to provide detailed guidance on how to invest for the goal.