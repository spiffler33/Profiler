# Strategy Enhancement Tests

This folder contains test files for all the enhanced funding strategy classes in the Indian financial planning system. Each test file verifies the optimization and constraint features added to a specific strategy class.

## Available Test Files

- [test_enhanced_custom_goal_strategy.py](test_enhanced_custom_goal_strategy.py) - Tests for enhanced CustomGoalStrategy
- [test_enhanced_charitable_giving_strategy.py](test_enhanced_charitable_giving_strategy.py) - Tests for enhanced CharitableGivingStrategy
- [test_enhanced_retirement_strategy.py](test_enhanced_retirement_strategy.py) - Tests for enhanced RetirementStrategy
- [test_enhanced_home_strategy.py](test_enhanced_home_strategy.py) - Tests for enhanced HomeStrategy
- [test_enhanced_wedding_strategy.py](test_enhanced_wedding_strategy.py) - Tests for enhanced WeddingStrategy
- [test_enhanced_debt_repayment_strategy.py](test_enhanced_debt_repayment_strategy.py) - Tests for enhanced DebtRepaymentStrategy
- [test_enhanced_legacy_planning_strategy.py](test_enhanced_legacy_planning_strategy.py) - Tests for enhanced LegacyPlanningStrategy

## Common Test Pattern

Each test file follows a consistent pattern:

1. **Initialization Tests**
   - Test the lazy initialization methods (optimizer, constraints, compound_strategy)

2. **Parameter Loading Tests**
   - Test the loading of strategy-specific parameters

3. **Constraint Assessment Tests**
   - Test each constraint assessment method
   - Verify the structure and content of the assessment results

4. **Optimization Tests**
   - Test each optimization method
   - Verify the structure and content of the optimization results

5. **Core Method Tests**
   - Test the enhanced generate_funding_strategy() method
   - Test other core methods specific to the strategy

## Running Tests

To run all strategy tests:

```bash
cd /Users/coddiwomplers/Desktop/Python/Profiler4
python -m unittest discover tests/strategies
```

To run a specific strategy test:

```bash
cd /Users/coddiwomplers/Desktop/Python/Profiler4
python -m unittest tests/strategies/test_enhanced_custom_goal_strategy.py
```