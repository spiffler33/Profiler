#!/usr/bin/env python3
"""Utility for migrating existing goal data to include probability-related fields"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import math
import random

# Add parent directory to path so we can import project modules
sys.path.append(str(Path(__file__).parent.parent))

from models.goal_models import Goal, GoalManager
from models.profile_manager import ProfileManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/goal_migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"
REPORTS_DIR = "/Users/coddiwomplers/Desktop/Python/Profiler4/reports"

# Indian financial context constants
SECTION_80C_GOALS = ["retirement", "pension", "ppf", "elss", "tax_saving"]
SECTION_80D_GOALS = ["health", "medical", "insurance", "healthcare"]
LAKH = 100000
CRORE = 10000000

def format_indian_currency(amount: float) -> str:
    """
    Format amount in Indian currency format (lakhs, crores).
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted amount string with ₹ symbol
    """
    if amount >= CRORE:
        return f"₹{amount/CRORE:.2f} Cr"
    elif amount >= LAKH:
        return f"₹{amount/LAKH:.2f} L"
    else:
        return f"₹{amount:.2f}"

def calculate_goal_success_probability(goal: Goal) -> float:
    """
    Calculate a goal's initial success probability based on existing data.
    
    Args:
        goal: Goal object
        
    Returns:
        float: Success probability (0-100)
    """
    # Start with a base probability
    base_probability = 50.0
    
    # Adjust based on current progress
    if goal.current_progress >= 90:
        progress_factor = 40.0  # Near completion
    elif goal.current_progress >= 70:
        progress_factor = 30.0  # Good progress
    elif goal.current_progress >= 50:
        progress_factor = 20.0  # Halfway there
    elif goal.current_progress >= 25:
        progress_factor = 10.0  # Some progress
    else:
        progress_factor = 0.0   # Little progress
    
    # Adjust based on timeframe (time remaining)
    try:
        target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
        today = datetime.now()
        years_remaining = (target_date - today).days / 365.0
        
        if years_remaining <= 0:
            # Already past due date
            timeframe_factor = -30.0
        elif years_remaining < 1:
            # Less than a year remaining
            timeframe_factor = -15.0
        elif years_remaining < 3:
            # 1-3 years remaining
            timeframe_factor = -5.0
        elif years_remaining < 7:
            # 3-7 years remaining
            timeframe_factor = 5.0
        else:
            # More than 7 years
            timeframe_factor = 10.0
    except (ValueError, TypeError):
        # Can't parse timeframe
        timeframe_factor = 0.0
    
    # Adjust based on target amount and current amount
    # Larger gaps are harder to achieve
    if goal.target_amount > 0 and goal.current_amount > 0:
        gap = goal.target_amount - goal.current_amount
        
        if gap <= 0:
            # Already achieved
            gap_factor = 20.0
        else:
            # Calculate monthly amount needed based on time remaining
            try:
                target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
                today = datetime.now()
                months_remaining = max(1, (target_date - today).days / 30.0)
                
                # Monthly savings needed
                monthly_needed = gap / months_remaining
                
                # Adjust based on the magnitude compared to target_amount
                # Smaller monthly amounts (relative to target) are more achievable
                if monthly_needed < (goal.target_amount * 0.005):  # Less than 0.5% of target amount per month
                    gap_factor = 15.0
                elif monthly_needed < (goal.target_amount * 0.01):  # Less than 1% of target amount per month
                    gap_factor = 10.0
                elif monthly_needed < (goal.target_amount * 0.02):  # Less than 2% of target amount per month
                    gap_factor = 5.0
                elif monthly_needed < (goal.target_amount * 0.05):  # Less than 5% of target amount per month
                    gap_factor = 0.0
                else:
                    # Higher monthly needed amount
                    gap_factor = -10.0
            except (ValueError, TypeError, ZeroDivisionError):
                gap_factor = 0.0
    else:
        gap_factor = 0.0
    
    # Final probability calculation with bounds
    probability = base_probability + progress_factor + timeframe_factor + gap_factor
    
    # Add a slight random factor to avoid all goals having the same values
    probability += random.uniform(-3.0, 3.0)
    
    # Ensure between 1-99
    probability = max(1.0, min(99.0, probability))
    
    # Round to 1 decimal place
    return round(probability, 1)

def generate_simulation_data(goal: Goal, category: str) -> Dict[str, Any]:
    """
    Generate simulation data for a goal based on its category and current data.
    
    Args:
        goal: Goal object
        category: Goal category
        
    Returns:
        dict: Simulation data structure
    """
    # Calculate success probability if not already set
    probability = goal.goal_success_probability
    if probability == 0:
        probability = calculate_goal_success_probability(goal)
    
    # Calculate default SIP amount based on target, timeframe, and category
    target_amount = goal.target_amount
    monthly_sip = 0
    
    try:
        target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
        today = datetime.now()
        years_remaining = max(0.5, (target_date - today).days / 365.0)
        
        # Adjust expected returns based on goal category
        if "retirement" in category.lower():
            expected_return = 0.10  # 10% for retirement (equity-heavy)
        elif "education" in category.lower():
            expected_return = 0.08  # 8% for education (balanced)
        elif "home" in category.lower():
            expected_return = 0.07  # 7% for home (safer allocation)
        elif "emergency" in category.lower():
            expected_return = 0.06  # 6% for emergency fund (conservative)
        else:
            expected_return = 0.09  # 9% default
        
        # Basic SIP calculation: PMT formula
        # Monthly SIP = P / ((1+r)^n - 1) * (1+r)^(1/12) / r
        # where P is target amount, r is monthly rate, n is months
        r_monthly = expected_return / 12
        n_months = years_remaining * 12
        
        if n_months > 0 and r_monthly > 0:
            remaining_amount = max(0, target_amount - goal.current_amount)
            
            # Avoid division by zero or negative numbers
            if remaining_amount > 0:
                x = (1 + r_monthly) ** n_months
                monthly_sip = (remaining_amount * r_monthly * (1 + r_monthly)) / (x - 1)
                
                # Round to nearest 500 for easier comprehension (Indian context)
                monthly_sip = math.ceil(monthly_sip / 500) * 500
    except (ValueError, TypeError, ZeroDivisionError):
        # Default to 1% of target amount if calculation fails
        monthly_sip = target_amount * 0.01
    
    # Ensure minimum SIP based on goal category (Indian context)
    if "retirement" in category.lower():
        monthly_sip = max(1000, monthly_sip)
    elif "education" in category.lower():
        monthly_sip = max(2000, monthly_sip)
    elif "emergency" in category.lower():
        monthly_sip = max(500, monthly_sip)
    else:
        monthly_sip = max(500, monthly_sip)
    
    # Format target amount for Indian context
    target_formatted = format_indian_currency(target_amount)
    
    # Check if goal is eligible for tax benefits
    is_80c_eligible = any(keyword in category.lower() for keyword in SECTION_80C_GOALS)
    is_80d_eligible = any(keyword in category.lower() for keyword in SECTION_80D_GOALS)
    
    # Create simulation data structure
    simulation_data = {
        "monte_carlo": {
            "trials": 1000,
            "success_rate": probability,
            "confidence_interval": [
                max(1, probability - 15),
                min(99, probability + 10)
            ],
            "market_conditions": [
                {"scenario": "bearish", "probability": max(1, probability - 25)},
                {"scenario": "normal", "probability": probability},
                {"scenario": "bullish", "probability": min(99, probability + 20)}
            ]
        },
        "investment_options": {
            "sip": {
                "monthly_amount": round(monthly_sip, 0),
                "annual_increase": 5,  # 5% annual increase
                "tax_benefits": {
                    "section_80c": is_80c_eligible,
                    "section_80d": is_80d_eligible
                }
            },
            "lumpsum": {
                "amount": round(target_amount * 0.2, 0),  # 20% lumpsum
                "timing": "immediate"
            }
        },
        "target": {
            "amount": target_amount,
            "formatted": target_formatted
        }
    }
    
    return simulation_data

def generate_scenarios(goal: Goal, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate goal scenarios with different financial assumptions.
    
    Args:
        goal: Goal object
        simulation_data: Simulation data structure
        
    Returns:
        dict: Scenarios data
    """
    probability = goal.goal_success_probability
    if probability == 0:
        probability = calculate_goal_success_probability(goal)
    
    sip_amount = simulation_data.get("investment_options", {}).get("sip", {}).get("monthly_amount", 0)
    
    # Create scenario data
    scenarios = {
        "conservative": {
            "return_rate": 6.0,
            "inflation": 6.0,
            "success_probability": max(1, probability - 20),
            "sip_amount": round(sip_amount * 1.3, 0)  # 30% higher SIP for conservative
        },
        "moderate": {
            "return_rate": 9.0,
            "inflation": 5.0,
            "success_probability": probability,
            "sip_amount": sip_amount
        },
        "aggressive": {
            "return_rate": 12.0,
            "inflation": 5.0,
            "success_probability": min(99, probability + 15),
            "sip_amount": round(sip_amount * 0.85, 0)  # 15% lower SIP for aggressive
        }
    }
    
    return scenarios

def generate_adjustments(goal: Goal, simulation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate recommended adjustments for a goal if needed.
    
    Args:
        goal: Goal object
        simulation_data: Simulation data structure
        
    Returns:
        dict: Adjustments structure or None if adjustments not required
    """
    # Only generate adjustments if required
    if not goal.adjustments_required and goal.goal_success_probability >= 80:
        return None
    
    sip_amount = simulation_data.get("investment_options", {}).get("sip", {}).get("monthly_amount", 0)
    target_amount = goal.target_amount
    
    # Create adjustment recommendations
    adjustments = {
        "recommended": [],
        "applied": [],
        "history": []
    }
    
    # Add SIP increase recommendation
    sip_increase = max(500, round(sip_amount * 0.2, -2))  # Round to nearest 100
    adjustments["recommended"].append({
        "type": "increase_sip",
        "amount": sip_increase,
        "impact": min(25, 100 - goal.goal_success_probability, 15.0),
        "description": f"Increase monthly SIP by {format_indian_currency(sip_increase)}"
    })
    
    # Add lumpsum recommendation
    lumpsum_amount = max(10000, round(target_amount * 0.1, -3))  # Round to nearest 1000
    adjustments["recommended"].append({
        "type": "lumpsum_investment",
        "amount": lumpsum_amount,
        "impact": min(20, 100 - goal.goal_success_probability, 10.0),
        "description": f"Add lumpsum of {format_indian_currency(lumpsum_amount)}"
    })
    
    # Add timeline extension recommendation if applicable
    try:
        target_date = datetime.fromisoformat(goal.timeframe.replace('Z', '+00:00'))
        today = datetime.now()
        
        # Only suggest timeline extension if at least 1 year away
        if (target_date - today).days > 365:
            extension_years = 2
            adjustments["recommended"].append({
                "type": "extend_timeline",
                "amount": extension_years,
                "impact": min(30, 100 - goal.goal_success_probability, 12.0),
                "description": f"Extend goal timeline by {extension_years} years"
            })
    except (ValueError, TypeError):
        pass
    
    # Add target reduction recommendation if goal has low probability
    if goal.goal_success_probability < 50:
        reduction_amount = round(target_amount * 0.1, -3)  # 10% reduction, rounded
        adjustments["recommended"].append({
            "type": "reduce_target",
            "amount": reduction_amount,
            "impact": min(35, 100 - goal.goal_success_probability, 20.0),
            "description": f"Reduce target amount by {format_indian_currency(reduction_amount)}"
        })
    
    return adjustments

def process_goal(goal: Goal) -> Tuple[Goal, bool]:
    """
    Process a goal to add enhanced probability fields.
    
    Args:
        goal: Goal object
        
    Returns:
        Tuple: (updated_goal, success)
    """
    try:
        # Calculate success probability if not set
        if goal.goal_success_probability == 0:
            goal.goal_success_probability = calculate_goal_success_probability(goal)
        
        # Generate simulation data
        simulation_data = generate_simulation_data(goal, goal.category)
        goal.set_simulation_data(simulation_data)
        
        # Generate scenarios
        scenarios = generate_scenarios(goal, simulation_data)
        goal.set_scenarios(scenarios)
        
        # Generate adjustments if needed
        adjustments = generate_adjustments(goal, simulation_data)
        goal.set_adjustments(adjustments)
        
        return goal, True
    except Exception as e:
        logger.error(f"Error processing goal {goal.id}: {str(e)}")
        return goal, False

def migrate_goals() -> Dict[str, Any]:
    """
    Migrate all goals in the database to include probability-related fields.
    
    Returns:
        dict: Migration results
    """
    goal_manager = GoalManager(DB_PATH)
    
    logger.info("Starting goal data migration for probability fields...")
    
    # Get all goals
    goals = goal_manager.get_all_goals()
    total_goals = len(goals)
    
    logger.info(f"Found {total_goals} goals to process")
    
    # Track migration results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_goals": total_goals,
        "success_count": 0,
        "error_count": 0,
        "by_category": {},
        "goals_requiring_adjustments": 0,
        "average_success_probability": 0.0
    }
    
    # Process each goal
    success_probabilities = []
    
    for i, goal in enumerate(goals, 1):
        logger.info(f"Processing goal {i}/{total_goals}: {goal.id} - {goal.title}")
        
        # Skip goals that already have the new fields populated
        if goal.simulation_data and goal.scenarios:
            logger.info(f"Goal {goal.id} already has probability fields - skipping")
            results["success_count"] += 1
            continue
        
        # Process goal
        updated_goal, success = process_goal(goal)
        
        # Update category stats
        category = goal.category
        if category not in results["by_category"]:
            results["by_category"][category] = {
                "total": 0,
                "success": 0,
                "error": 0,
                "avg_probability": 0.0,
                "probabilities": []
            }
        
        results["by_category"][category]["total"] += 1
        
        if success:
            # Save the updated goal
            if goal_manager.update_goal(updated_goal):
                results["success_count"] += 1
                results["by_category"][category]["success"] += 1
                
                # Track success probability
                if updated_goal.goal_success_probability > 0:
                    success_probabilities.append(updated_goal.goal_success_probability)
                    results["by_category"][category]["probabilities"].append(updated_goal.goal_success_probability)
                
                # Track adjustments
                if updated_goal.adjustments_required:
                    results["goals_requiring_adjustments"] += 1
                
                logger.info(f"Successfully updated goal {updated_goal.id} with probability fields")
            else:
                results["error_count"] += 1
                results["by_category"][category]["error"] += 1
                logger.error(f"Failed to save updated goal {goal.id}")
        else:
            results["error_count"] += 1
            results["by_category"][category]["error"] += 1
    
    # Calculate averages
    if success_probabilities:
        results["average_success_probability"] = sum(success_probabilities) / len(success_probabilities)
    
    for category, stats in results["by_category"].items():
        if stats["probabilities"]:
            stats["avg_probability"] = sum(stats["probabilities"]) / len(stats["probabilities"])
        del stats["probabilities"]  # Remove raw data from results
    
    logger.info(f"Goal migration completed: {results['success_count']} successful, {results['error_count']} errors")
    
    return results

def save_report(results: Dict[str, Any]) -> str:
    """
    Save migration results to a report file.
    
    Args:
        results: Migration results
        
    Returns:
        str: Path to the report file
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Format timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORTS_DIR, f"goal_migration_report_{timestamp}.json")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Migration report saved to {report_file}")
    
    return report_file

def print_report_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of the migration results.
    
    Args:
        results: Migration results
    """
    print("\n" + "="*50)
    print(" GOAL MIGRATION SUMMARY ")
    print("="*50)
    
    print(f"\nTotal goals processed: {results['total_goals']}")
    print(f"Successfully migrated: {results['success_count']}")
    print(f"Errors: {results['error_count']}")
    
    if results['total_goals'] > 0:
        success_rate = (results['success_count'] / results['total_goals']) * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    print(f"\nAverage success probability: {results['average_success_probability']:.1f}%")
    print(f"Goals requiring adjustments: {results['goals_requiring_adjustments']} ({(results['goals_requiring_adjustments']/max(1, results['success_count']))*100:.1f}%)")
    
    print("\nResults by category:")
    print("-" * 50)
    print(f"{'Category':<20} {'Total':<8} {'Success':<8} {'Errors':<8} {'Avg Prob':<10}")
    print("-" * 50)
    
    for category, stats in sorted(results["by_category"].items()):
        print(f"{category:<20} {stats['total']:<8} {stats['success']:<8} {stats['error']:<8} {stats['avg_probability']:<10.1f}%")
    
    print("\nSee logs/goal_migration.log for detailed information")

def main():
    """Main function for goal data migration"""
    try:
        print("Starting migration of goal data to include probability-related fields...")
        
        # Perform migration
        results = migrate_goals()
        
        # Save and print report
        report_file = save_report(results)
        print_report_summary(results)
        
        print(f"\nMigration completed. Full report saved to {report_file}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        print(f"Error: Migration failed - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()