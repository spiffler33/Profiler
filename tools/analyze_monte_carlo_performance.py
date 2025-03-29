#!/usr/bin/env python3
"""
Performance trend analyzer for Monte Carlo simulations.

This script analyzes performance benchmark results over time and generates
trend graphs and reports for visualization and regression detection.
"""

import json
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Dict, List, Tuple, Any
import numpy as np

# Constants
BENCHMARK_FILE = "../tests/models/benchmark_results.json"
OUTPUT_DIR = "."

def load_benchmark_data() -> List[Dict[str, Any]]:
    """Load benchmark data from the benchmark results file."""
    benchmark_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), BENCHMARK_FILE)
    
    try:
        with open(benchmark_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading benchmark data: {e}")
        return []

def parse_benchmark_data(benchmarks: List[Dict[str, Any]]) -> Dict[str, List[Tuple[datetime, float]]]:
    """Parse benchmark data into a format suitable for plotting."""
    parsed_data = {}
    
    for benchmark in benchmarks:
        name = benchmark.get('name')
        if not name:
            continue
            
        timestamp_str = benchmark.get('timestamp')
        duration = benchmark.get('duration')
        success = benchmark.get('success', True)
        
        if not timestamp_str or duration is None or not success:
            continue
            
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Try alternative format if ISO format fails
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue
        
        if name not in parsed_data:
            parsed_data[name] = []
            
        parsed_data[name].append((timestamp, duration))
    
    # Sort data by timestamp
    for name in parsed_data:
        parsed_data[name].sort(key=lambda x: x[0])
    
    return parsed_data

def calculate_performance_trends(data: Dict[str, List[Tuple[datetime, float]]]) -> Dict[str, Dict[str, float]]:
    """Calculate performance trends for each benchmark."""
    trends = {}
    
    for name, points in data.items():
        if len(points) < 2:
            continue
            
        # Extract timestamps and durations
        timestamps = [p[0] for p in points]
        durations = [p[1] for p in points]
        
        # Calculate statistics
        current = durations[-1]
        baseline = np.mean(durations[:-1])  # Average of previous runs
        change_pct = (current - baseline) / baseline * 100 if baseline > 0 else 0
        
        # Calculate trend (linear regression)
        x = np.array([(t - timestamps[0]).total_seconds() for t in timestamps])
        y = np.array(durations)
        if len(x) > 1:
            slope, _ = np.polyfit(x, y, 1)
            trend_direction = "improving" if slope < 0 else "degrading"
        else:
            slope = 0
            trend_direction = "stable"
        
        trends[name] = {
            "current": current,
            "baseline": baseline,
            "change_pct": change_pct,
            "slope": slope,
            "direction": trend_direction,
            "data_points": len(points)
        }
    
    return trends

def plot_performance_trends(data: Dict[str, List[Tuple[datetime, float]]]):
    """Generate performance trend plots."""
    if not data:
        print("No data to plot.")
        return
    
    # Set up the figure
    plt.figure(figsize=(12, 8))
    
    # Plot each benchmark
    for name, points in data.items():
        if len(points) < 2:
            continue
            
        # Extract timestamps and durations
        timestamps = [p[0] for p in points]
        durations = [p[1] for p in points]
        
        # Plot the data
        plt.plot(timestamps, durations, 'o-', label=name)
    
    # Set up the plot
    plt.xlabel('Date')
    plt.ylabel('Duration (seconds)')
    plt.title('Monte Carlo Performance Trends')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))  # Weekly ticks
    plt.gcf().autofmt_xdate()  # Rotate date labels
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Save the plot
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              OUTPUT_DIR, 'performance_trends.png')
    plt.savefig(output_path)
    print(f"Performance trend plot saved to: {output_path}")
    
    # Create individual plots for each benchmark
    for name, points in data.items():
        if len(points) < 2:
            continue
            
        plt.figure(figsize=(10, 6))
        
        # Extract timestamps and durations
        timestamps = [p[0] for p in points]
        durations = [p[1] for p in points]
        
        # Plot the data
        plt.plot(timestamps, durations, 'o-', color='blue')
        
        # Add trend line
        x = np.array([(t - timestamps[0]).total_seconds() for t in timestamps])
        y = np.array(durations)
        if len(x) > 1:
            slope, intercept = np.polyfit(x, y, 1)
            x_trend = np.array([min(x), max(x)])
            y_trend = slope * x_trend + intercept
            
            # Convert x back to dates for plotting
            x_dates = [timestamps[0] + np.timedelta64(int(t_seconds), 's') for t_seconds in x_trend]
            plt.plot(x_dates, y_trend, '--', color='red', label=f'Trend: {"Improving" if slope < 0 else "Degrading"}')
        
        # Set up the plot
        plt.xlabel('Date')
        plt.ylabel('Duration (seconds)')
        plt.title(f'Performance Trend: {name}')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))  # Weekly ticks
        plt.gcf().autofmt_xdate()  # Rotate date labels
        plt.grid(True, linestyle='--', alpha=0.7)
        if len(x) > 1:
            plt.legend()
        
        # Save the plot
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  OUTPUT_DIR, f'performance_trends_{name}.png')
        plt.savefig(output_path)
        print(f"Performance trend plot for {name} saved to: {output_path}")

def generate_markdown_report(trends: Dict[str, Dict[str, float]]):
    """Generate a Markdown report of performance trends."""
    if not trends:
        print("No trends to report.")
        return
    
    report = [
        "# Monte Carlo Performance Trend Report",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Performance Summary",
        "",
        "| Benchmark | Current (s) | Baseline (s) | Change | Trend | Data Points |",
        "|-----------|-------------|--------------|--------|-------|-------------|"
    ]
    
    # Add a row for each benchmark
    for name, data in trends.items():
        current = data['current']
        baseline = data['baseline']
        change_pct = data['change_pct']
        direction = data['direction'].capitalize()
        data_points = data['data_points']
        
        # Format with appropriate precision
        current_str = f"{current:.4f}"
        baseline_str = f"{baseline:.4f}"
        
        # Add emoji based on change
        if change_pct < -5:
            change_str = f"🟢 {change_pct:.1f}%"  # Significant improvement
        elif change_pct < 0:
            change_str = f"🟩 {change_pct:.1f}%"  # Modest improvement
        elif change_pct < 5:
            change_str = f"⬜ {change_pct:.1f}%"  # Negligible change
        elif change_pct < 10:
            change_str = f"🟨 {change_pct:.1f}%"  # Modest degradation
        else:
            change_str = f"🟥 {change_pct:.1f}%"  # Significant degradation
        
        row = f"| {name} | {current_str} | {baseline_str} | {change_str} | {direction} | {data_points} |"
        report.append(row)
    
    # Add section for flagged regressions
    significant_regressions = [(name, data) for name, data in trends.items() 
                              if data['change_pct'] > 10]
    
    if significant_regressions:
        report.extend([
            "",
            "## ⚠️ Flagged Regressions",
            ""
        ])
        
        for name, data in significant_regressions:
            report.extend([
                f"### {name}",
                f"- Current duration: {data['current']:.4f}s",
                f"- Baseline duration: {data['baseline']:.4f}s",
                f"- Performance change: {data['change_pct']:.1f}%",
                f"- Trend direction: {data['direction']}",
                ""
            ])
    
    # Write the report
    report_text = "\n".join(report)
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              OUTPUT_DIR, 'performance_report.md')
    
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"Performance report saved to: {output_path}")

def main():
    """Main function to analyze performance trends."""
    print("Analyzing Monte Carlo performance trends...")
    
    # Load benchmark data
    benchmarks = load_benchmark_data()
    if not benchmarks:
        print("No benchmark data found. Exiting.")
        sys.exit(1)
    
    # Parse benchmark data
    parsed_data = parse_benchmark_data(benchmarks)
    if not parsed_data:
        print("Failed to parse benchmark data. Exiting.")
        sys.exit(1)
    
    # Calculate performance trends
    trends = calculate_performance_trends(parsed_data)
    
    # Generate plots
    plot_performance_trends(parsed_data)
    
    # Generate Markdown report
    generate_markdown_report(trends)
    
    print("Performance trend analysis completed successfully.")

if __name__ == "__main__":
    main()