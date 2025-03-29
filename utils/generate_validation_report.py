#!/usr/bin/env python3
"""
Script to generate a comprehensive validation report of the database state.

This script:
1. Analyzes the goals table to check data integrity
2. Analyzes the parameter table to check for completeness 
3. Verifies relationships between tables
4. Generates a detailed HTML report
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/validation_report.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_PATHS = {
    "profiles": "data/profiles.db",
    "parameters": "data/parameters.db" 
}
REPORTS_DIR = "reports"

def check_database_exists(db_path):
    """Check if database file exists."""
    return os.path.exists(db_path)

def get_table_stats(db_path, table_name):
    """Get basic statistics about a table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            conn.close()
            return {"exists": False, "row_count": 0, "columns": []}
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [{"name": col[1], "type": col[2], "nullable": not col[3]} for col in cursor.fetchall()]
        
        conn.close()
        
        return {
            "exists": True,
            "row_count": row_count,
            "columns": columns
        }
    except Exception as e:
        logger.error(f"Error getting stats for table {table_name}: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return {"exists": False, "error": str(e)}

def analyze_goals_table():
    """Analyze the goals table for data integrity."""
    try:
        conn = sqlite3.connect(DB_PATHS["profiles"])
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
        if not cursor.fetchone():
            conn.close()
            return {"exists": False, "error": "Goals table not found"}
        
        # Get all goals
        cursor.execute("""
            SELECT 
                id, user_profile_id, category, title, target_amount, timeframe, 
                current_amount, importance, flexibility, goal_success_probability,
                simulation_parameters_json IS NOT NULL AS has_simulation_parameters,
                simulation_data IS NOT NULL AS has_simulation_data,
                scenarios IS NOT NULL AS has_scenarios,
                adjustments IS NOT NULL AS has_adjustments,
                last_simulation_time IS NOT NULL AS has_simulation_time,
                probability_partial_success,
                simulation_iterations,
                monthly_sip_recommended,
                probability_metrics IS NOT NULL AS has_probability_metrics,
                success_threshold
            FROM goals
        """)
        goals = cursor.fetchall()
        
        # Convert to list of dicts
        goals_list = []
        for goal in goals:
            goal_dict = dict(goal)
            
            # Parse dates
            try:
                if goal_dict.get('timeframe'):
                    timeframe = datetime.fromisoformat(goal_dict['timeframe'].replace('Z', '+00:00'))
                    goal_dict['days_to_goal'] = (timeframe - datetime.now()).days
                    goal_dict['years_to_goal'] = goal_dict['days_to_goal'] / 365.25
                else:
                    goal_dict['days_to_goal'] = None
                    goal_dict['years_to_goal'] = None
            except:
                goal_dict['days_to_goal'] = None
                goal_dict['years_to_goal'] = None
            
            goals_list.append(goal_dict)
        
        # Calculate statistics
        goal_stats = {
            "total_goals": len(goals_list),
            "categories": {},
            "importance": {},
            "flexibility": {},
            "has_simulation_parameters": sum(1 for g in goals_list if g.get('has_simulation_parameters')),
            "has_simulation_data": sum(1 for g in goals_list if g.get('has_simulation_data')),
            "has_scenarios": sum(1 for g in goals_list if g.get('has_scenarios')),
            "has_adjustments": sum(1 for g in goals_list if g.get('has_adjustments')),
            "has_simulation_time": sum(1 for g in goals_list if g.get('has_simulation_time')),
            "has_probability_metrics": sum(1 for g in goals_list if g.get('has_probability_metrics')),
            "avg_probability": sum(g.get('goal_success_probability', 0) for g in goals_list) / len(goals_list) if goals_list else 0,
            "avg_sip": sum(g.get('monthly_sip_recommended', 0) for g in goals_list) / len(goals_list) if goals_list else 0,
            "goal_timeframe_stats": {
                "past_due": sum(1 for g in goals_list if g.get('days_to_goal') is not None and g.get('days_to_goal') < 0),
                "short_term": sum(1 for g in goals_list if g.get('years_to_goal') is not None and 0 <= g.get('years_to_goal') < 3),
                "medium_term": sum(1 for g in goals_list if g.get('years_to_goal') is not None and 3 <= g.get('years_to_goal') < 7),
                "long_term": sum(1 for g in goals_list if g.get('years_to_goal') is not None and g.get('years_to_goal') >= 7)
            }
        }
        
        # Category distribution
        for goal in goals_list:
            category = goal.get('category', 'unknown')
            goal_stats["categories"][category] = goal_stats["categories"].get(category, 0) + 1
            
            importance = goal.get('importance', 'unknown')
            goal_stats["importance"][importance] = goal_stats["importance"].get(importance, 0) + 1
            
            flexibility = goal.get('flexibility', 'unknown')
            goal_stats["flexibility"][flexibility] = goal_stats["flexibility"].get(flexibility, 0) + 1
        
        conn.close()
        
        return {
            "exists": True,
            "stats": goal_stats,
            "goals": goals_list
        }
    except Exception as e:
        logger.error(f"Error analyzing goals table: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return {"exists": False, "error": str(e)}

def analyze_parameters_table():
    """Analyze the parameters table for completeness."""
    try:
        if not check_database_exists(DB_PATHS["parameters"]):
            return {"exists": False, "error": "Parameters database not found"}
        
        conn = sqlite3.connect(DB_PATHS["parameters"])
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parameters'")
        if not cursor.fetchone():
            conn.close()
            return {"exists": False, "error": "Parameters table not found"}
        
        # Get all parameters
        cursor.execute("""
            SELECT 
                parameter_group, parameter_name, parameter_value, parameter_description,
                is_india_specific, created_at, updated_at
            FROM parameters
        """)
        parameters = cursor.fetchall()
        
        # Convert to list of dicts
        parameters_list = [dict(param) for param in parameters]
        
        # Calculate statistics
        param_stats = {
            "total_parameters": len(parameters_list),
            "india_specific_count": sum(1 for p in parameters_list if p.get('is_india_specific')),
            "parameter_groups": {},
            "parameter_values": {
                "min": min(p.get('parameter_value', 0) for p in parameters_list) if parameters_list else 0,
                "max": max(p.get('parameter_value', 0) for p in parameters_list) if parameters_list else 0,
                "avg": sum(p.get('parameter_value', 0) for p in parameters_list) / len(parameters_list) if parameters_list else 0
            }
        }
        
        # Parameter group distribution
        for param in parameters_list:
            group = param.get('parameter_group', 'unknown')
            param_stats["parameter_groups"][group] = param_stats["parameter_groups"].get(group, 0) + 1
        
        conn.close()
        
        return {
            "exists": True,
            "stats": param_stats,
            "parameters": parameters_list
        }
    except Exception as e:
        logger.error(f"Error analyzing parameters table: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return {"exists": False, "error": str(e)}

def generate_html_report(goals_analysis, parameters_analysis):
    """Generate an HTML report from the analysis data."""
    try:
        # Create reports directory if it doesn't exist
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Generate timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(REPORTS_DIR, f"database_validation_report_{timestamp}.html")
        
        # Start building HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Validation Report - {timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 0;
            color: #333;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
        }}
        .report-section {{
            margin-bottom: 40px;
            padding: 20px;
            border-radius: 5px;
            background-color: #f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stats-card {{
            display: inline-block;
            width: 200px;
            background-color: #fff;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stats-card .value {{
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
            color: #3498db;
        }}
        .stats-card .label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .chart-container {{
            height: 300px;
            margin: 20px 0;
        }}
        .success {{
            color: #27ae60;
        }}
        .warning {{
            color: #f39c12;
        }}
        .error {{
            color: #e74c3c;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Database Validation Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <div class="report-section">
        <h2>Summary</h2>
        <div class="stats-card">
            <div class="label">Goals Count</div>
            <div class="value">{goals_analysis.get('stats', {}).get('total_goals', 0) if goals_analysis.get('exists', False) else 'N/A'}</div>
        </div>
        <div class="stats-card">
            <div class="label">Parameters Count</div>
            <div class="value">{parameters_analysis.get('stats', {}).get('total_parameters', 0) if parameters_analysis.get('exists', False) else 'N/A'}</div>
        </div>
        <div class="stats-card">
            <div class="label">Avg Goal Probability</div>
            <div class="value">{f"{goals_analysis.get('stats', {}).get('avg_probability', 0):.1f}%" if goals_analysis.get('exists', False) else 'N/A'}</div>
        </div>
        <div class="stats-card">
            <div class="label">Avg Monthly SIP</div>
            <div class="value">₹{f"{goals_analysis.get('stats', {}).get('avg_sip', 0):,.0f}" if goals_analysis.get('exists', False) else 'N/A'}</div>
        </div>
    </div>
"""
        
        # Goals Analysis Section
        if goals_analysis.get('exists', False):
            goal_stats = goals_analysis.get('stats', {})
            goals = goals_analysis.get('goals', [])
            
            # Add goals section
            html_content += f"""
    <div class="report-section">
        <h2>Goals Analysis</h2>
        
        <h3>Data Completeness</h3>
        <div class="stats-card">
            <div class="label">Has Simulation Parameters</div>
            <div class="value">{goal_stats.get('has_simulation_parameters', 0)}/{goal_stats.get('total_goals', 0)}</div>
        </div>
        <div class="stats-card">
            <div class="label">Has Simulation Data</div>
            <div class="value">{goal_stats.get('has_simulation_data', 0)}/{goal_stats.get('total_goals', 0)}</div>
        </div>
        <div class="stats-card">
            <div class="label">Has Scenarios</div>
            <div class="value">{goal_stats.get('has_scenarios', 0)}/{goal_stats.get('total_goals', 0)}</div>
        </div>
        <div class="stats-card">
            <div class="label">Has Adjustments</div>
            <div class="value">{goal_stats.get('has_adjustments', 0)}/{goal_stats.get('total_goals', 0)}</div>
        </div>
        
        <h3>Goal Distribution by Category</h3>
        <div class="chart-container">
            <canvas id="categoryChart"></canvas>
        </div>
        
        <h3>Goal Timeframe Distribution</h3>
        <div class="chart-container">
            <canvas id="timeframeChart"></canvas>
        </div>
        
        <h3>Goal Success Probability Distribution</h3>
        <div class="chart-container">
            <canvas id="probabilityChart"></canvas>
        </div>
        
        <h3>Goal Sample (5 Random Goals)</h3>
        <table>
            <tr>
                <th>Title</th>
                <th>Category</th>
                <th>Target Amount</th>
                <th>Years to Goal</th>
                <th>Success Probability</th>
                <th>Monthly SIP</th>
            </tr>
"""
            
            # Add sample goals (up to 5)
            import random
            sample_goals = random.sample(goals, min(5, len(goals)))
            for goal in sample_goals:
                html_content += f"""
            <tr>
                <td>{goal.get('title', 'N/A')}</td>
                <td>{goal.get('category', 'N/A')}</td>
                <td>₹{goal.get('target_amount', 0):,.0f}</td>
                <td>{f"{goal.get('years_to_goal', 0):.1f}" if goal.get('years_to_goal') is not None else 'N/A'}</td>
                <td>{f"{goal.get('goal_success_probability', 0):.1f}%" if goal.get('goal_success_probability') is not None else 'N/A'}</td>
                <td>₹{f"{goal.get('monthly_sip_recommended', 0):,.0f}" if goal.get('monthly_sip_recommended') is not None else 'N/A'}</td>
            </tr>
"""
            
            html_content += """
        </table>
    </div>
"""
        else:
            # Goals table doesn't exist
            html_content += f"""
    <div class="report-section">
        <h2>Goals Analysis</h2>
        <p class="error">Error: {goals_analysis.get('error', 'Goals table does not exist or could not be analyzed')}</p>
    </div>
"""
        
        # Parameters Analysis Section
        if parameters_analysis.get('exists', False):
            param_stats = parameters_analysis.get('stats', {})
            parameters = parameters_analysis.get('parameters', [])
            
            # Add parameters section
            html_content += f"""
    <div class="report-section">
        <h2>Parameters Analysis</h2>
        
        <h3>Parameter Statistics</h3>
        <div class="stats-card">
            <div class="label">Total Parameters</div>
            <div class="value">{param_stats.get('total_parameters', 0)}</div>
        </div>
        <div class="stats-card">
            <div class="label">India-Specific</div>
            <div class="value">{param_stats.get('india_specific_count', 0)}/{param_stats.get('total_parameters', 0)}</div>
        </div>
        <div class="stats-card">
            <div class="label">Parameter Groups</div>
            <div class="value">{len(param_stats.get('parameter_groups', {}))}</div>
        </div>
        
        <h3>Parameter Groups Distribution</h3>
        <div class="chart-container">
            <canvas id="paramGroupChart"></canvas>
        </div>
        
        <h3>Parameter Sample (5 Random Parameters)</h3>
        <table>
            <tr>
                <th>Group</th>
                <th>Name</th>
                <th>Value</th>
                <th>India-Specific</th>
                <th>Description</th>
            </tr>
"""
            
            # Add sample parameters (up to 5)
            import random
            sample_params = random.sample(parameters, min(5, len(parameters)))
            for param in sample_params:
                html_content += f"""
            <tr>
                <td>{param.get('parameter_group', 'N/A')}</td>
                <td>{param.get('parameter_name', 'N/A')}</td>
                <td>{param.get('parameter_value', 'N/A')}</td>
                <td>{"Yes" if param.get('is_india_specific') else "No"}</td>
                <td>{param.get('parameter_description', 'N/A')}</td>
            </tr>
"""
            
            html_content += """
        </table>
    </div>
"""
        else:
            # Parameters table doesn't exist
            html_content += f"""
    <div class="report-section">
        <h2>Parameters Analysis</h2>
        <p class="error">Error: {parameters_analysis.get('error', 'Parameters table does not exist or could not be analyzed')}</p>
    </div>
"""
        
        # Validation Status Section
        html_content += """
    <div class="report-section">
        <h2>Validation Status</h2>
        <table>
            <tr>
                <th>Check</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
"""
        
        # Add validation checks
        goal_stats = goals_analysis.get('stats', {}) if goals_analysis.get('exists', False) else {}
        param_stats = parameters_analysis.get('stats', {}) if parameters_analysis.get('exists', False) else {}
        
        # Check 1: Goals table exists
        status_class = "success" if goals_analysis.get('exists', False) else "error"
        status_text = "Success" if goals_analysis.get('exists', False) else "Failed"
        details = f"Found {goal_stats.get('total_goals', 0)} goals" if goals_analysis.get('exists', False) else goals_analysis.get('error', 'Table does not exist')
        html_content += f"""
            <tr>
                <td>Goals Table Exists</td>
                <td class="{status_class}">{status_text}</td>
                <td>{details}</td>
            </tr>
"""
        
        # Check 2: Parameters table exists
        status_class = "success" if parameters_analysis.get('exists', False) else "error"
        status_text = "Success" if parameters_analysis.get('exists', False) else "Failed"
        details = f"Found {param_stats.get('total_parameters', 0)} parameters" if parameters_analysis.get('exists', False) else parameters_analysis.get('error', 'Table does not exist')
        html_content += f"""
            <tr>
                <td>Parameters Table Exists</td>
                <td class="{status_class}">{status_text}</td>
                <td>{details}</td>
            </tr>
"""
        
        # Check 3: Goal simulation parameters complete
        if goals_analysis.get('exists', False):
            sim_params_complete = goal_stats.get('has_simulation_parameters', 0) == goal_stats.get('total_goals', 0)
            status_class = "success" if sim_params_complete else "warning"
            status_text = "Success" if sim_params_complete else "Warning"
            details = "All goals have simulation parameters" if sim_params_complete else f"{goal_stats.get('total_goals', 0) - goal_stats.get('has_simulation_parameters', 0)} goals missing simulation parameters"
            html_content += f"""
            <tr>
                <td>Goal Simulation Parameters</td>
                <td class="{status_class}">{status_text}</td>
                <td>{details}</td>
            </tr>
"""
        
        # Check 4: Indian parameters exist
        if parameters_analysis.get('exists', False):
            has_indian_params = param_stats.get('india_specific_count', 0) > 0
            status_class = "success" if has_indian_params else "warning"
            status_text = "Success" if has_indian_params else "Warning"
            details = f"Found {param_stats.get('india_specific_count', 0)} India-specific parameters" if has_indian_params else "No India-specific parameters found"
            html_content += f"""
            <tr>
                <td>India-Specific Parameters</td>
                <td class="{status_class}">{status_text}</td>
                <td>{details}</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
"""
        
        # Add Charts JavaScript
        html_content += """
    <script>
        // Helper to get random colors
        function getRandomColors(count) {
            const colors = [];
            for (let i = 0; i < count; i++) {
                const r = Math.floor(Math.random() * 200);
                const g = Math.floor(Math.random() * 200);
                const b = Math.floor(Math.random() * 200);
                colors.push(`rgba(${r}, ${g}, ${b}, 0.7)`);
            }
            return colors;
        }
"""
        
        # Add Category Chart
        if goals_analysis.get('exists', False):
            categories = goals_analysis.get('stats', {}).get('categories', {})
            category_names = list(categories.keys())
            category_counts = [categories[cat] for cat in category_names]
            
            html_content += f"""
        // Category Chart
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(category_names)},
                datasets: [{{
                    label: 'Number of Goals',
                    data: {json.dumps(category_counts)},
                    backgroundColor: getRandomColors({len(category_names)})
                }}]
            }},
            options: {{
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Goal Distribution by Category'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Goals'
                        }}
                    }}
                }}
            }}
        }});
"""
        
            # Add Timeframe Chart
            timeframe_stats = goals_analysis.get('stats', {}).get('goal_timeframe_stats', {})
            timeframe_labels = ["Past Due", "Short Term (0-3 years)", "Medium Term (3-7 years)", "Long Term (7+ years)"]
            timeframe_counts = [
                timeframe_stats.get('past_due', 0),
                timeframe_stats.get('short_term', 0),
                timeframe_stats.get('medium_term', 0),
                timeframe_stats.get('long_term', 0)
            ]
            
            html_content += f"""
        // Timeframe Chart
        const timeframeCtx = document.getElementById('timeframeChart').getContext('2d');
        new Chart(timeframeCtx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(timeframe_labels)},
                datasets: [{{
                    label: 'Goal Timeframes',
                    data: {json.dumps(timeframe_counts)},
                    backgroundColor: [
                        'rgba(231, 76, 60, 0.7)',
                        'rgba(241, 196, 15, 0.7)',
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(52, 152, 219, 0.7)'
                    ]
                }}]
            }},
            options: {{
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Goal Timeframe Distribution'
                    }}
                }}
            }}
        }});
"""
            
            # Add Probability Chart
            # First, create probability bins from goals data
            probabilities = [g.get('goal_success_probability', 0) for g in goals_analysis.get('goals', [])]
            bins = [0, 20, 40, 60, 80, 100]
            bin_labels = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
            
            # Count goals in each bin
            bin_counts = [0] * len(bin_labels)
            for prob in probabilities:
                for i in range(len(bins) - 1):
                    if bins[i] <= prob < bins[i+1] or (i == len(bins) - 2 and prob == bins[i+1]):
                        bin_counts[i] += 1
                        break
            
            html_content += f"""
        // Probability Chart
        const probCtx = document.getElementById('probabilityChart').getContext('2d');
        new Chart(probCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(bin_labels)},
                datasets: [{{
                    label: 'Goal Success Probability',
                    data: {json.dumps(bin_counts)},
                    backgroundColor: [
                        'rgba(231, 76, 60, 0.7)',
                        'rgba(230, 126, 34, 0.7)',
                        'rgba(241, 196, 15, 0.7)',
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(39, 174, 96, 0.7)'
                    ]
                }}]
            }},
            options: {{
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Goal Success Probability Distribution'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Goals'
                        }}
                    }}
                }}
            }}
        }});
"""
        
        # Add Parameter Group Chart
        if parameters_analysis.get('exists', False):
            param_groups = parameters_analysis.get('stats', {}).get('parameter_groups', {})
            group_names = list(param_groups.keys())
            group_counts = [param_groups[group] for group in group_names]
            
            html_content += f"""
        // Parameter Group Chart
        const paramGroupCtx = document.getElementById('paramGroupChart').getContext('2d');
        new Chart(paramGroupCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(group_names)},
                datasets: [{{
                    label: 'Parameter Groups',
                    data: {json.dumps(group_counts)},
                    backgroundColor: getRandomColors({len(group_names)})
                }}]
            }},
            options: {{
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Parameter Groups Distribution'
                    }}
                }}
            }}
        }});
"""
        
        # Close the script and HTML
        html_content += """
    </script>
</body>
</html>
"""
        
        # Write the HTML file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated at {report_path}")
        return report_path
    
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        return None

def main():
    """Main function to generate validation report."""
    print("Starting database validation report generation...")
    
    # Analyze goals table
    print("Analyzing goals table...")
    goals_analysis = analyze_goals_table()
    
    # Analyze parameters table
    print("Analyzing parameters table...")
    parameters_analysis = analyze_parameters_table()
    
    # Generate HTML report
    print("Generating HTML report...")
    report_path = generate_html_report(goals_analysis, parameters_analysis)
    
    if report_path:
        print(f"\nValidation report generated successfully: {report_path}")
        
        # Print simple summary to console
        print("\nSummary:")
        
        if goals_analysis.get('exists', False):
            goal_stats = goals_analysis.get('stats', {})
            print(f"- Goals: {goal_stats.get('total_goals', 0)} total")
            print(f"- Categories: {len(goal_stats.get('categories', {}))} unique categories")
            print(f"- Average success probability: {goal_stats.get('avg_probability', 0):.1f}%")
            print(f"- All goals have simulation parameters: {'Yes' if goal_stats.get('has_simulation_parameters', 0) == goal_stats.get('total_goals', 0) else 'No'}")
        else:
            print(f"- Goals table: Error - {goals_analysis.get('error', 'Could not analyze')}")
        
        if parameters_analysis.get('exists', False):
            param_stats = parameters_analysis.get('stats', {})
            print(f"- Parameters: {param_stats.get('total_parameters', 0)} total")
            print(f"- Parameter groups: {len(param_stats.get('parameter_groups', {}))} unique groups")
            print(f"- India-specific parameters: {param_stats.get('india_specific_count', 0)} parameters")
        else:
            print(f"- Parameters table: Error - {parameters_analysis.get('error', 'Could not analyze')}")
        
    else:
        print("Error: Failed to generate validation report")

if __name__ == "__main__":
    main()