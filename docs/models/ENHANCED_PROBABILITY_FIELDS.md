# Enhanced Probability Analysis Fields

This document explains the enhanced probability analysis capabilities added to the Goal model, including how to leverage the Monte Carlo simulation data, scenarios, and adjustments fields for financial planning in an Indian context.

## Overview

The Goal model has been enhanced with three new fields to support probability analysis, scenario planning, and goal adjustments:

1. `simulation_data` - Stores Monte Carlo simulation results and investment options including SIP (Systematic Investment Plan) details
2. `scenarios` - Stores alternative scenarios for the goal with different assumptions
3. `adjustments` - Stores recommended adjustments to improve goal success probability

These fields support the existing `goal_success_probability` and `adjustments_required` fields to provide a more comprehensive probability analysis system.

## Migration

The migration script `enhance_probability_fields.py` handles adding these fields to the database and populates them with sensible defaults. The migration:

1. Creates a backup of the database before migration
2. Adds the new fields to the goals table
3. Populates the new fields with default values based on existing goal data
4. Validates the migration to ensure data integrity

To run the migration:
```bash
python migrations/enhance_probability_fields.py
```

## Field Structures

### simulation_data

The `simulation_data` field stores a JSON structure with the following format:

```json
{
  "monte_carlo": {
    "trials": 1000,
    "success_rate": 75.5,
    "confidence_interval": [60.5, 85.5],
    "market_conditions": [
      {"scenario": "bearish", "probability": 45.5},
      {"scenario": "normal", "probability": 75.5},
      {"scenario": "bullish", "probability": 95.5}
    ]
  },
  "investment_options": {
    "sip": {
      "monthly_amount": 15000,
      "annual_increase": 10,
      "tax_benefits": {
        "section_80c": true,
        "section_80d": false
      }
    },
    "lumpsum": {
      "amount": 200000,
      "timing": "immediate"
    }
  },
  "target": {
    "amount": 1000000,
    "formatted": "₹10.00 L"
  }
}
```

### scenarios

The `scenarios` field stores a JSON structure with different scenarios:

```json
{
  "conservative": {
    "return_rate": 6.0,
    "inflation": 5.0,
    "success_probability": 60.5,
    "sip_amount": 18750
  },
  "moderate": {
    "return_rate": 9.0,
    "inflation": 4.0,
    "success_probability": 75.5,
    "sip_amount": 15000
  },
  "aggressive": {
    "return_rate": 12.0,
    "inflation": 4.0,
    "success_probability": 90.5,
    "sip_amount": 12750
  }
}
```

### adjustments

The `adjustments` field stores a JSON structure with recommended adjustments:

```json
{
  "recommended": [
    {
      "type": "increase_sip",
      "amount": 3000,
      "impact": 15.0,
      "description": "Increase monthly SIP by 20%"
    },
    {
      "type": "extend_timeline",
      "amount": 2,
      "impact": 12.0,
      "description": "Extend goal timeline by 2 years"
    },
    {
      "type": "lumpsum_investment",
      "amount": 100000,
      "impact": 10.0,
      "description": "Add lumpsum of ₹1.00 L"
    }
  ],
  "applied": [],
  "history": []
}
```

## Helper Methods

The Goal model provides helper methods to work with these JSON fields:

1. `get_simulation_data()` - Returns the parsed simulation data as a dictionary
2. `set_simulation_data(data)` - Sets the simulation data from a dictionary
3. `get_scenarios()` - Returns the parsed scenarios as a dictionary
4. `set_scenarios(data)` - Sets the scenarios from a dictionary
5. `get_adjustments()` - Returns the parsed adjustments as a dictionary
6. `set_adjustments(data)` - Sets the adjustments from a dictionary
7. `get_sip_details()` - Returns SIP details from the simulation data

## Indian Financial Context

The enhanced fields support the Indian financial context in several ways:

1. SIP (Systematic Investment Plan) - The simulation_data includes SIP details common in Indian investment approaches
2. Tax benefits - Section 80C and 80D tax benefits are tracked for relevant goals
3. Lakh/Crore formatting - Large amounts are formatted in lakhs and crores
4. Inflation assumptions - Scenario planning includes India-specific inflation rates

## Usage Examples

### Retrieving simulation data for a goal

```python
goal = goal_manager.get_goal("goal-id")
simulation_data = goal.get_simulation_data()

# Access SIP information
sip_info = goal.get_sip_details()
monthly_sip = sip_info.get("monthly_amount", 0)
print(f"Recommended monthly SIP: ₹{monthly_sip}")

# Check tax benefits
tax_benefits = sip_info.get("tax_benefits", {})
if tax_benefits.get("section_80c"):
    print("This goal qualifies for Section 80C tax benefits")
```

### Working with scenarios

```python
goal = goal_manager.get_goal("goal-id")
scenarios = goal.get_scenarios()

# Compare different scenarios
for scenario_name, scenario_data in scenarios.items():
    print(f"{scenario_name.capitalize()} scenario:")
    print(f"  Expected return: {scenario_data['return_rate']}%")
    print(f"  Success probability: {scenario_data['success_probability']}%")
    print(f"  Required SIP: ₹{scenario_data['sip_amount']}")
```

### Applying adjustments

```python
goal = goal_manager.get_goal("goal-id")
adjustments = goal.get_adjustments()

# Show recommended adjustments
for adjustment in adjustments.get("recommended", []):
    print(f"Recommendation: {adjustment['description']}")
    print(f"Impact: +{adjustment['impact']}% success probability")

# Apply an adjustment
if adjustments.get("recommended"):
    applied = adjustments["recommended"][0]
    
    # Move from recommended to applied
    if "applied" not in adjustments:
        adjustments["applied"] = []
    adjustments["applied"].append(applied)
    adjustments["recommended"].remove(applied)
    
    # Record in history
    if "history" not in adjustments:
        adjustments["history"] = []
    applied["applied_at"] = datetime.now().isoformat()
    adjustments["history"].append(applied)
    
    # Update the goal
    goal.set_adjustments(adjustments)
    goal_manager.update_goal(goal)
```

## Integration with Goal Adjustment Service

The enhanced fields are designed to integrate with the existing goal adjustment service. The service can:

1. Calculate the impact of different adjustments on goal success probability
2. Generate personalized recommendations
3. Track adjustment history over time
4. Simulate "what if" scenarios for different adjustment combinations

## Future Enhancements

Future enhancements to the probability analysis system may include:

1. More advanced Monte Carlo simulations with variable market conditions
2. Machine learning models to predict optimal goal adjustments
3. Integration with external financial data sources for more accurate projections
4. Support for more complex goal dependencies and interrelationships