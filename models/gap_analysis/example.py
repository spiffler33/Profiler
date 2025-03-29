"""
Example usage of the refactored Gap Analysis module
"""

from models.gap_analysis import GapAnalysis

def run_gap_analysis_example():
    """
    Example function demonstrating how to use the refactored Gap Analysis module
    """
    # Create a sample profile
    profile = {
        "id": "example-profile",
        "name": "Example User",
        "income": 80000,  # Monthly income
        "expenses": 50000,  # Monthly expenses
        "assets": {
            "cash": 100000,
            "equity": 500000,
            "debt": 300000,
            "gold": 200000
        }
    }
    
    # Create sample goals
    goals = [
        {
            "id": "goal-1",
            "title": "Emergency Fund",
            "category": "emergency_fund",
            "target_amount": 300000,
            "current_amount": 100000,
            "importance": "high",
            "target_date": "2025-12-31"
        },
        {
            "id": "goal-2",
            "title": "Retirement",
            "category": "retirement",
            "target_amount": 10000000,
            "current_amount": 2000000,
            "importance": "high",
            "target_date": "2045-12-31"
        },
        {
            "id": "goal-3",
            "title": "Vacation",
            "category": "discretionary",
            "target_amount": 200000,
            "current_amount": 50000,
            "importance": "low",
            "target_date": "2026-12-31"
        }
    ]
    
    # Initialize the gap analyzer
    gap_analysis = GapAnalysis()
    
    # Analyze individual goals
    print("Analyzing individual goals:")
    for goal in goals:
        result = gap_analysis.analyze_goal_gap(goal, profile)
        print(f"\nGoal: {result.goal_title}")
        print(f"Gap Amount: ₹{result.gap_amount:,.0f}")
        print(f"Gap Percentage: {result.gap_percentage:.1f}%")
        print(f"Severity: {result.severity.value}")
        print(f"Description: {result.description}")
    
    # Analyze overall financial health
    print("\nAnalyzing overall financial health:")
    overall_result = gap_analysis.analyze_overall_gap(goals, profile)
    print(f"\nOverall Assessment: {overall_result['overall_assessment']}")
    print(f"Total Gap Amount: ₹{overall_result['total_gap_amount']:,.0f}")
    print(f"Average Gap Percentage: {overall_result['average_gap_percentage']:.1f}%")
    
    # Check if there are any resource conflicts
    if overall_result['resource_conflicts']:
        print("\nResource Conflicts:")
        for conflict in overall_result['resource_conflicts']:
            print(f"- {conflict['description']}")
    
    return overall_result

if __name__ == "__main__":
    run_gap_analysis_example()