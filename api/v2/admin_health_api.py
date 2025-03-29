"""
Admin Health Dashboard API Module

This module provides endpoints for the SystemHealthDashboard component to display
real-time and historical system health metrics.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import json
import uuid
import os
import platform
import psutil
import time
import logging
from collections import deque

# Import centralized authentication
from auth_utils import auth

# Create Blueprint
admin_health_api = Blueprint('admin_health_api', __name__)

# In-memory store for historical metrics (last 24 hours)
# Stores metrics at 5-minute intervals
MAX_HISTORY_ENTRIES = 288  # 24 hours * 12 entries per hour (5-minute intervals)
health_metrics_history = deque(maxlen=MAX_HISTORY_ENTRIES)
last_metrics_time = None

def get_system_metrics():
    """
    Collect current system metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used
        memory_total = memory.total
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = disk.used
        disk_total = disk.total
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_cpu = process.cpu_percent(interval=0.1)
        process_memory = process.memory_info().rss
        
        # Collect API metrics from app context if available
        api_metrics = {}
        if hasattr(current_app, 'api_metrics'):
            api_metrics = current_app.api_metrics
        else:
            api_metrics = {
                'total_requests': 0,
                'active_requests': 0,
                'error_count': 0,
                'avg_response_time': 0
            }
        
        # Monte Carlo cache metrics
        cache_metrics = {}
        try:
            from models.monte_carlo.cache import get_cache_stats
            cache_metrics = get_cache_stats() or {}
        except Exception as e:
            current_app.logger.warning(f"Failed to get Monte Carlo cache stats: {e}")
            cache_metrics = {
                'entries': 0,
                'size_bytes': 0,
                'hit_rate': 0,
                'miss_rate': 0
            }
        
        # Parameter cache metrics
        param_cache_metrics = {}
        try:
            from services.financial_parameter_service import get_financial_parameter_service
            service = get_financial_parameter_service()
            if hasattr(service, 'get_cache_stats'):
                param_cache_metrics = service.get_cache_stats() or {}
            else:
                param_cache_metrics = {
                    'entries': 0,
                    'size_bytes': 0,
                    'hit_rate': 0,
                    'miss_rate': 0
                }
        except Exception as e:
            current_app.logger.warning(f"Failed to get parameter cache stats: {e}")
            param_cache_metrics = {
                'entries': 0,
                'size_bytes': 0,
                'hit_rate': 0,
                'miss_rate': 0
            }
        
        # Health status determination
        health_status = "healthy"
        alerts = []
        
        # Check CPU
        if cpu_percent > 90:
            health_status = "critical"
            alerts.append({
                'component': 'CPU',
                'status': 'critical',
                'message': f'CPU usage is critically high at {cpu_percent}%',
                'metric': cpu_percent,
                'threshold': 90
            })
        elif cpu_percent > 75:
            health_status = min(health_status, "warning")
            alerts.append({
                'component': 'CPU',
                'status': 'warning',
                'message': f'CPU usage is high at {cpu_percent}%',
                'metric': cpu_percent,
                'threshold': 75
            })
        
        # Check Memory
        if memory_percent > 90:
            health_status = "critical"
            alerts.append({
                'component': 'Memory',
                'status': 'critical',
                'message': f'Memory usage is critically high at {memory_percent}%',
                'metric': memory_percent,
                'threshold': 90
            })
        elif memory_percent > 80:
            health_status = min(health_status, "warning")
            alerts.append({
                'component': 'Memory',
                'status': 'warning',
                'message': f'Memory usage is high at {memory_percent}%',
                'metric': memory_percent,
                'threshold': 80
            })
        
        # Check Disk
        if disk_percent > 95:
            health_status = "critical"
            alerts.append({
                'component': 'Disk',
                'status': 'critical',
                'message': f'Disk usage is critically high at {disk_percent}%',
                'metric': disk_percent,
                'threshold': 95
            })
        elif disk_percent > 85:
            health_status = min(health_status, "warning")
            alerts.append({
                'component': 'Disk',
                'status': 'warning',
                'message': f'Disk usage is high at {disk_percent}%',
                'metric': disk_percent,
                'threshold': 85
            })
        
        # Check API errors
        error_rate = 0
        if api_metrics.get('total_requests', 0) > 0:
            error_rate = (api_metrics.get('error_count', 0) / api_metrics.get('total_requests', 1)) * 100
            
        if error_rate > 10:
            health_status = "critical"
            alerts.append({
                'component': 'API',
                'status': 'critical',
                'message': f'API error rate is critically high at {error_rate:.1f}%',
                'metric': error_rate,
                'threshold': 10
            })
        elif error_rate > 5:
            health_status = min(health_status, "warning")
            alerts.append({
                'component': 'API',
                'status': 'warning',
                'message': f'API error rate is high at {error_rate:.1f}%',
                'metric': error_rate,
                'threshold': 5
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used': memory_used,
                'memory_total': memory_total,
                'disk_percent': disk_percent,
                'disk_used': disk_used,
                'disk_total': disk_total,
                'platform': platform.system(),
                'platform_version': platform.version(),
                'python_version': platform.python_version()
            },
            'process': {
                'cpu_percent': process_cpu,
                'memory_bytes': process_memory,
                'uptime_seconds': time.time() - process.create_time()
            },
            'api': api_metrics,
            'cache': {
                'monte_carlo': cache_metrics,
                'parameters': param_cache_metrics
            },
            'health_status': health_status,
            'alerts': alerts
        }
    except Exception as e:
        current_app.logger.error(f"Error collecting system metrics: {str(e)}")
        return {
            'timestamp': datetime.now().isoformat(),
            'error': f"Failed to collect system metrics: {str(e)}",
            'health_status': 'unknown',
            'alerts': [{
                'component': 'Metrics Collection',
                'status': 'critical',
                'message': f'Failed to collect system metrics: {str(e)}',
                'metric': None,
                'threshold': None
            }]
        }

def update_metrics_history():
    """
    Update the metrics history if 5 minutes have passed since the last update
    """
    global last_metrics_time
    
    now = datetime.now()
    if last_metrics_time is None or now - last_metrics_time >= timedelta(minutes=5):
        metrics = get_system_metrics()
        health_metrics_history.append(metrics)
        last_metrics_time = now

@admin_health_api.route('/admin/health', methods=['GET'])
@auth.login_required
def get_health():
    """
    Get current system health metrics
    """
    metrics = get_system_metrics()
    update_metrics_history()
    
    return jsonify(metrics)

@admin_health_api.route('/admin/health/history', methods=['GET'])
@auth.login_required
def get_health_history():
    """
    Get historical system health metrics
    
    Query parameters:
    - start_time: ISO format datetime string for start of range
    - end_time: ISO format datetime string for end of range
    - interval: Time interval in minutes for aggregating data (default: 5)
    """
    # Get query parameters
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    interval_minutes = request.args.get('interval', default=5, type=int)
    
    # Update metrics history
    update_metrics_history()
    
    # Convert time strings to datetime objects
    start_time = None
    end_time = None
    
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return jsonify({
                'error': f"Invalid start_time format: {start_time_str}. Expected ISO format."
            }), 400
    
    if end_time_str:
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({
                'error': f"Invalid end_time format: {end_time_str}. Expected ISO format."
            }), 400
    
    # Default time range is last 24 hours
    if start_time is None:
        start_time = datetime.now() - timedelta(hours=24)
    
    if end_time is None:
        end_time = datetime.now()
    
    # Filter metrics by time range
    filtered_metrics = []
    
    for metrics in health_metrics_history:
        try:
            metric_time = datetime.fromisoformat(metrics['timestamp'])
            if start_time <= metric_time <= end_time:
                filtered_metrics.append(metrics)
        except (ValueError, KeyError):
            # Skip invalid metrics
            pass
    
    # Aggregate metrics based on interval if needed
    if interval_minutes > 5:
        aggregated_metrics = []
        current_group = []
        current_interval_start = start_time
        
        for metrics in filtered_metrics:
            metric_time = datetime.fromisoformat(metrics['timestamp'])
            
            # Check if metric belongs to current interval
            if metric_time < current_interval_start + timedelta(minutes=interval_minutes):
                current_group.append(metrics)
            else:
                # Aggregate current group
                if current_group:
                    aggregated_metrics.append(aggregate_metrics(current_group))
                
                # Move to next interval
                while metric_time >= current_interval_start + timedelta(minutes=interval_minutes):
                    current_interval_start += timedelta(minutes=interval_minutes)
                
                current_group = [metrics]
        
        # Aggregate last group
        if current_group:
            aggregated_metrics.append(aggregate_metrics(current_group))
        
        result_metrics = aggregated_metrics
    else:
        result_metrics = filtered_metrics
    
    return jsonify({
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'interval_minutes': interval_minutes,
        'metrics_count': len(result_metrics),
        'metrics': result_metrics
    })

def aggregate_metrics(metrics_list):
    """
    Aggregate multiple metrics into a single metric
    """
    if not metrics_list:
        return {}
    
    # Get first and last timestamps
    first_timestamp = metrics_list[0]['timestamp']
    last_timestamp = metrics_list[-1]['timestamp']
    
    # Initialize aggregated values
    cpu_values = []
    memory_percent_values = []
    disk_percent_values = []
    process_cpu_values = []
    process_memory_values = []
    api_requests = 0
    api_errors = 0
    monte_carlo_hits = 0
    monte_carlo_misses = 0
    param_hits = 0
    param_misses = 0
    alerts = []
    
    # Aggregate values
    for metrics in metrics_list:
        if 'system' in metrics:
            cpu_values.append(metrics['system'].get('cpu_percent', 0))
            memory_percent_values.append(metrics['system'].get('memory_percent', 0))
            disk_percent_values.append(metrics['system'].get('disk_percent', 0))
        
        if 'process' in metrics:
            process_cpu_values.append(metrics['process'].get('cpu_percent', 0))
            process_memory_values.append(metrics['process'].get('memory_bytes', 0))
        
        if 'api' in metrics:
            api_requests += metrics['api'].get('total_requests', 0)
            api_errors += metrics['api'].get('error_count', 0)
        
        if 'cache' in metrics and 'monte_carlo' in metrics['cache']:
            monte_carlo_hits += metrics['cache']['monte_carlo'].get('hits', 0)
            monte_carlo_misses += metrics['cache']['monte_carlo'].get('misses', 0)
        
        if 'cache' in metrics and 'parameters' in metrics['cache']:
            param_hits += metrics['cache']['parameters'].get('hits', 0)
            param_misses += metrics['cache']['parameters'].get('misses', 0)
        
        if 'alerts' in metrics:
            alerts.extend(metrics['alerts'])
    
    # Calculate averages
    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    avg_memory_percent = sum(memory_percent_values) / len(memory_percent_values) if memory_percent_values else 0
    avg_disk_percent = sum(disk_percent_values) / len(disk_percent_values) if disk_percent_values else 0
    avg_process_cpu = sum(process_cpu_values) / len(process_cpu_values) if process_cpu_values else 0
    avg_process_memory = sum(process_memory_values) / len(process_memory_values) if process_memory_values else 0
    
    # Calculate hit rates
    monte_carlo_hit_rate = 0
    if monte_carlo_hits + monte_carlo_misses > 0:
        monte_carlo_hit_rate = (monte_carlo_hits / (monte_carlo_hits + monte_carlo_misses)) * 100
    
    param_hit_rate = 0
    if param_hits + param_misses > 0:
        param_hit_rate = (param_hits / (param_hits + param_misses)) * 100
    
    # Calculate error rate
    error_rate = 0
    if api_requests > 0:
        error_rate = (api_errors / api_requests) * 100
    
    # Determine overall health status
    health_status = "healthy"
    if avg_cpu > 90 or avg_memory_percent > 90 or avg_disk_percent > 95 or error_rate > 10:
        health_status = "critical"
    elif avg_cpu > 75 or avg_memory_percent > 80 or avg_disk_percent > 85 or error_rate > 5:
        health_status = "warning"
    
    # Return aggregated metrics
    return {
        'timestamp': last_timestamp,
        'start_timestamp': first_timestamp,
        'end_timestamp': last_timestamp,
        'system': {
            'cpu_percent': avg_cpu,
            'memory_percent': avg_memory_percent,
            'disk_percent': avg_disk_percent
        },
        'process': {
            'cpu_percent': avg_process_cpu,
            'memory_bytes': avg_process_memory
        },
        'api': {
            'total_requests': api_requests,
            'error_count': api_errors,
            'error_rate': error_rate
        },
        'cache': {
            'monte_carlo': {
                'hits': monte_carlo_hits,
                'misses': monte_carlo_misses,
                'hit_rate': monte_carlo_hit_rate
            },
            'parameters': {
                'hits': param_hits,
                'misses': param_misses,
                'hit_rate': param_hit_rate
            }
        },
        'health_status': health_status,
        'alert_count': len(alerts),
        'alerts_sample': alerts[:5] if len(alerts) > 5 else alerts
    }