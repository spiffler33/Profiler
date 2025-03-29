#!/usr/bin/env python3
"""
Analyze Parameter Usage

This script runs a simple analysis of the application to gather statistics on
which legacy parameter keys are being used most frequently. This helps identify
parts of the codebase that need to be updated to use the new hierarchical paths.

Usage:
    python analyze_parameter_usage.py [--run-tests] [--create-report]
    
Options:
    --run-tests     Run all tests to capture parameter usage from test code
    --create-report Generate detailed HTML report with recommendations
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import argparse

# Import parameters module
from models.financial_parameters import (
    get_parameters, get_legacy_access_report, ParameterCompatibilityAdapter
)

def run_application_scenario() -> None:
    """Run common application scenarios to capture real usage patterns"""
    try:
        # Import necessary modules
        from app import app
        
        # Run in test mode with Flask test client
        client = app.test_client()
        
        # Hit key endpoints to generate parameter access
        client.get('/')
        client.get('/profiles')
        client.post('/profiles/create', data={'name': 'Test User', 'age': '35'})
        
        # Other operations that use financial parameters
        from models.goal_calculator import GoalCalculator
        calculator = GoalCalculator()
        calculator.calculate_amount_needed({'target_amount': 1000000, 'title': 'Test Goal'}, {})
        
        print("✓ Simulated typical application scenarios")
    except Exception as e:
        print(f"× Error simulating application scenarios: {str(e)}")

def run_all_tests() -> None:
    """Run all tests in the project to capture test-time parameter usage"""
    try:
        # Run all tests with unittest
        result = subprocess.run(
            ["python", "-m", "unittest", "discover"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ All tests passed")
        else:
            print("× Some tests failed")
            print(result.stderr)
    except Exception as e:
        print(f"× Error running tests: {str(e)}")

def generate_usage_report(access_report: Dict[str, int]) -> Dict[str, Any]:
    """
    Generate a detailed report from usage data
    
    Args:
        access_report: Dictionary mapping legacy keys to access counts
        
    Returns:
        Dict: Report data structure
    """
    # Get parameters instance to access mappings
    params = get_parameters()
    key_mapping = {}
    
    # Get the key mapping from the adapter if available
    if isinstance(params, ParameterCompatibilityAdapter):
        key_mapping = params._key_mapping
    
    # Prepare report data
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_legacy_keys_used": len(access_report),
        "total_access_count": sum(access_report.values()),
        "most_used_keys": [],
        "key_details": [],
        "recommendations": []
    }
    
    # Sort keys by access count (most frequent first)
    sorted_keys = sorted(access_report.items(), key=lambda x: x[1], reverse=True)
    
    # Add details for each key
    for key, count in sorted_keys:
        new_path = key_mapping.get(key, "unknown")
        
        # Add to most used keys if in top 5
        if len(report["most_used_keys"]) < 5:
            report["most_used_keys"].append({
                "key": key,
                "count": count,
                "new_path": new_path
            })
        
        # Add full details
        report["key_details"].append({
            "key": key,
            "count": count,
            "new_path": new_path,
            "recommendation": f"Replace all instances of '{key}' with '{new_path}'"
        })
    
    # Generate overall recommendations
    if report["total_legacy_keys_used"] > 0:
        report["recommendations"].append(
            "Update all code to use new hierarchical parameter paths"
        )
        
        if report["total_legacy_keys_used"] > 10:
            report["recommendations"].append(
                "Consider creating a migration plan to update code in stages"
            )
        
        # Recommend focusing on most frequently used keys first
        if len(report["most_used_keys"]) > 0:
            top_key = report["most_used_keys"][0]["key"]
            report["recommendations"].append(
                f"Start by replacing the most frequently used key: '{top_key}'"
            )
    else:
        report["recommendations"].append(
            "No legacy keys detected - your code is using the modern parameter system!"
        )
    
    return report

def create_html_report(report: Dict[str, Any], filename: str = "parameter_usage_report.html") -> None:
    """
    Generate an HTML report from the analysis data
    
    Args:
        report: Report data structure
        filename: Output HTML filename
    """
    # Simple HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Parameter Usage Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .warning {{ color: #e74c3c; }}
            .success {{ color: #2ecc71; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .recommendations {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; }}
            .recommendations li {{ margin-bottom: 10px; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Parameter Usage Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>
                    <strong>Legacy Keys Used:</strong> {report["total_legacy_keys_used"]}<br>
                    <strong>Total Access Count:</strong> {report["total_access_count"]}
                </p>
                
                <p class="{'warning' if report['total_legacy_keys_used'] > 0 else 'success'}">
                    {
                        "⚠️ Your codebase is using legacy parameter keys that should be updated." 
                        if report['total_legacy_keys_used'] > 0 else 
                        "✅ Your codebase is using the modern parameter system!"
                    }
                </p>
            </div>
            
            <h2>Most Frequently Used Legacy Keys</h2>
    """
    
    if report["most_used_keys"]:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Legacy Key</th>
                        <th>Access Count</th>
                        <th>New Hierarchical Path</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in report["most_used_keys"]:
            html += f"""
                    <tr>
                        <td>{item["key"]}</td>
                        <td>{item["count"]}</td>
                        <td>{item["new_path"]}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        """
    else:
        html += "<p>No legacy keys detected.</p>"
    
    html += """
            <h2>All Legacy Keys Used</h2>
    """
    
    if report["key_details"]:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Legacy Key</th>
                        <th>Access Count</th>
                        <th>New Hierarchical Path</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in report["key_details"]:
            html += f"""
                    <tr>
                        <td>{item["key"]}</td>
                        <td>{item["count"]}</td>
                        <td>{item["new_path"]}</td>
                        <td>{item["recommendation"]}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        """
    else:
        html += "<p>No legacy keys detected.</p>"
    
    html += """
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
    """
    
    for recommendation in report["recommendations"]:
        html += f"            <li>{recommendation}</li>\n"
    
    html += """
                </ul>
            </div>
            
            <div class="footer">
                <p>Generated by Parameter Usage Analyzer</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write to file
    with open(filename, "w") as f:
        f.write(html)
    
    print(f"✓ HTML report generated: {filename}")

def main():
    """Main function to run the analysis"""
    parser = argparse.ArgumentParser(description="Analyze parameter usage in the application")
    parser.add_argument("--run-tests", action="store_true", help="Run all tests to capture parameter usage")
    parser.add_argument("--create-report", action="store_true", help="Generate detailed HTML report")
    
    args = parser.parse_args()
    
    print("Parameter Usage Analysis")
    print("=======================")
    
    # Run application scenarios to trigger parameter usage
    run_application_scenario()
    
    # Run tests if requested
    if args.run_tests:
        print("\nRunning all tests to analyze parameter usage in test code...")
        run_all_tests()
    
    # Get access report
    print("\nGathering parameter usage statistics...")
    time.sleep(1)  # Small delay to ensure all async operations complete
    access_report = get_legacy_access_report()
    
    # Print summary
    print(f"\nFound {len(access_report)} legacy parameter keys in use")
    print(f"Total access count: {sum(access_report.values())}")
    
    if access_report:
        print("\nTop 5 most frequently used legacy keys:")
        for i, (key, count) in enumerate(
            sorted(access_report.items(), key=lambda x: x[1], reverse=True)[:5]
        ):
            print(f"{i+1}. '{key}' used {count} times")
    
    # Generate detailed report if requested
    if args.create_report:
        print("\nGenerating detailed usage report...")
        report_data = generate_usage_report(access_report)
        create_html_report(report_data)
    
    print("\nAnalysis complete!")
    
    if not args.create_report and len(access_report) > 0:
        print("\nTip: Run with --create-report to generate a detailed HTML report with recommendations")

if __name__ == "__main__":
    main()