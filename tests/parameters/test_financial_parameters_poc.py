#!/usr/bin/env python3
"""
Financial Parameters Proof of Concept

This script demonstrates how to use the FinancialParameters system.
It shows both the new hierarchical access and compatibility with older flat access patterns.
"""

import sys
import os
import json
from pprint import pprint

# Adjust this path to point to your project's root directory
sys.path.append('.')

try:
    from models.financial_parameters import FinancialParameters, ParameterCompatibilityAdapter
except ImportError:
    print("Could not import FinancialParameters. Make sure the path is correct.")
    sys.exit(1)

def demonstrate_parameter_access():
    """
    Demonstrates basic parameter access patterns.
    """
    print("\n" + "="*80)
    print("DEMONSTRATING BASIC PARAMETER ACCESS")
    print("="*80)

    # Create an instance of the financial parameters
    params = FinancialParameters()

    # Access parameters using the hierarchical dot notation
    inflation_rate = params.get("economic.inflation.general")
    print(f"General inflation rate: {inflation_rate:.2f}%")

    # Access nested parameters
    equity_returns = params.get("asset_classes.equity.large_cap.expected_return")
    print(f"Expected return for large cap equity: {equity_returns:.2f}%")

    # Get risk profile based allocation
    conservative_allocation = params.get_allocation_model("conservative")
    print("\nConservative allocation model:")
    pprint(conservative_allocation)

    # Get parameters for a specific goal type
    emergency_fund_months = params.get("goals.emergency_fund.recommended_months")
    print(f"\nRecommended emergency fund: {emergency_fund_months} months of expenses")

def demonstrate_compatibility_adapter():
    """
    Demonstrates the compatibility adapter for legacy code.
    """
    print("\n" + "="*80)
    print("DEMONSTRATING COMPATIBILITY ADAPTER")
    print("="*80)

    # Create a compatibility adapter
    adapter = ParameterCompatibilityAdapter()

    # Access parameters using old flat keys
    inflation_rate = adapter.get("general_inflation_rate")
    print(f"General inflation rate (via adapter): {inflation_rate:.2f}%")

    # Access asset returns using legacy pattern
    equity_return = adapter.get_asset_return("equity", "large_cap", "moderate")
    print(f"Large cap equity return for moderate risk (via adapter): {equity_return:.2f}%")

    # Get legacy risk profile
    risk_profile = adapter.get_risk_profile("moderate")
    print("\nModerate risk profile (via adapter):")
    pprint(risk_profile)

def demonstrate_parameter_overrides():
    """
    Demonstrates parameter overrides and customization.
    """
    print("\n" + "="*80)
    print("DEMONSTRATING PARAMETER OVERRIDES")
    print("="*80)

    params = FinancialParameters()

    # Show current inflation rate
    current_inflation = params.get("economic.inflation.general")
    print(f"Current general inflation rate: {current_inflation:.2f}%")

    # Override with custom value
    params.set("economic.inflation.general", 7.5)
    new_inflation = params.get("economic.inflation.general")
    print(f"Custom general inflation rate: {new_inflation:.2f}%")

    # Create a context with different parameters for scenario analysis
    high_inflation_scenario = params.create_context("high_inflation")
    high_inflation_scenario.set("economic.inflation.general", 9.0)

    # Get values from different contexts
    base_inflation = params.get("economic.inflation.general")
    high_inflation = params.get_context("high_inflation").get("economic.inflation.general")

    print(f"Base scenario inflation: {base_inflation:.2f}%")
    print(f"High inflation scenario: {high_inflation:.2f}%")

    # Reset to defaults
    params.reset("economic.inflation.general")
    reset_inflation = params.get("economic.inflation.general")
    print(f"Reset inflation rate: {reset_inflation:.2f}%")

def demonstrate_goal_calculations():
    """
    Demonstrates how the parameters are used in goal calculations.
    """
    print("\n" + "="*80)
    print("DEMONSTRATING GOAL CALCULATIONS")
    print("="*80)

    try:
        from models.goal_calculator import GoalCalculator
        from models.goal_models import Goal
    except ImportError:
        print("Could not import goal-related modules. Skipping goal calculations demonstration.")
        return

    # Create a simple education goal
    education_goal = Goal(
        id=None,
        user_id="demo_user",
        title="Child's College Education",
        category_id=3,  # Education category
        target_date="2035-08-01",
        target_amount=2500000,  # 25 lakhs
        current_amount=500000,  # 5 lakhs already saved
        priority=8,
        description="Engineering degree at a top college"
    )

    # Calculate funding requirements
    calculator = GoalCalculator.create_for_goal(education_goal)

    print(f"Goal: {education_goal.title}")
    print(f"Target amount: ₹{education_goal.target_amount:,}")
    print(f"Current savings: ₹{education_goal.current_amount:,}")

    # Calculate monthly investment needed
    monthly_investment = calculator.calculate_monthly_investment_needed()
    print(f"Required monthly investment: ₹{monthly_investment:,.2f}")

    # Calculate future value with current investment
    future_value = calculator.calculate_future_value(monthly_investment / 2)
    shortfall = education_goal.target_amount - future_value

    print(f"Future value with half the needed investment: ₹{future_value:,.2f}")
    print(f"Projected shortfall: ₹{shortfall:,.2f}")

    # Show how inflation affects the goal
    params = FinancialParameters()
    inflation_rate = params.get("economic.inflation.education")
    future_cost = education_goal.target_amount * (1 + inflation_rate/100)**(calculator.years_to_goal())

    print(f"Education inflation rate: {inflation_rate:.2f}%")
    print(f"Years to goal: {calculator.years_to_goal()}")
    print(f"Future cost adjusted for inflation: ₹{future_cost:,.2f}")

def save_example_parameters():
    """
    Saves the current parameters to a JSON file for inspection.
    """
    params = FinancialParameters.get_instance()
    example_params = params.to_dict()

    with open("example_parameters.json", "w") as f:
        json.dump(example_params, f, indent=2)

    print("\nSaved example parameters to 'example_parameters.json' for inspection")

def main():
    print("\nFINANCIAL PARAMETERS PROOF OF CONCEPT")
    print("This script demonstrates the capabilities of the FinancialParameters system")

    # Basic parameter access
    demonstrate_parameter_access()

    # Compatibility adapter for legacy code
    demonstrate_compatibility_adapter()

    # Parameter overrides and contexts
    demonstrate_parameter_overrides()

    # Goal calculations using parameters
    demonstrate_goal_calculations()

    # Save parameters for inspection
    save_example_parameters()

    print("\nDemonstration complete!")

if __name__ == "__main__":
    main()
