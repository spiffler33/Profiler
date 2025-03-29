# Gap Analysis Module

This module provides tools for analyzing mismatches between financial goals and available resources.
It helps identify funding gaps, timeframe issues, and prioritization conflicts to enable
better financial planning decisions.

## Module Structure

The module is organized into the following components:

- **core.py**: Core data structures and utilities
- **analyzer.py**: Main gap analysis engine
- **remediation_strategies.py**: Framework for remediation strategies
- **timeframe_adjustments.py**: Timeline extension strategies
- **allocation_adjustments.py**: Asset allocation optimization strategies
- **contribution_adjustments.py**: Contribution increase strategies
- **target_adjustments.py**: Target reduction strategies
- **priority_adjustments.py**: Goal prioritization strategies

## Key Features

- Gap metrics calculations (funding, time, capacity)
- Integration with asset and income projections
- India-specific context for financial analysis
- Support for various goal types with specialized calculations
- Holistic financial health analysis
- Gap aggregation and categorization
- Lifecycle-based goal analysis
- Risk exposure evaluation
- Indian tax efficiency and family structure analysis

## Usage

The main entry point is the `GapAnalysis` class, which provides methods to analyze gaps
for individual goals and across an entire financial plan:

```python
from models.gap_analysis import GapAnalysis

# Create analyzer
gap_analysis = GapAnalysis()

# Analyze a single goal
result = gap_analysis.analyze_goal_gap(goal, profile)

# Analyze all goals
overall_result = gap_analysis.analyze_overall_gap(goals, profile)
```

## Remediation Strategies

The module includes specialized strategies for addressing funding gaps:

- Timeline Extensions via `TimeframeAdjustment`
- Asset Allocation Changes via `AllocationAdjustment`
- Contribution Increases via `ContributionAdjustment`
- Target Reductions via `TargetAdjustment`
- Goal Reprioritization via `PriorityAdjustment`