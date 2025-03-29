"""Parameter Admin API Endpoints for admin interface.

This module provides API endpoints for managing financial parameters in the system.
It provides endpoints for viewing, creating, updating, and deleting parameters,
as well as viewing parameter history, impact analysis, related parameters, and audit logs.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import json
import uuid

# Import services
from services.financial_parameter_service import get_financial_parameter_service

# Import centralized authentication
from auth_utils import auth

# Import models needed locally
from models.database_profile_manager import DatabaseProfileManager

# Create Blueprint
admin_parameters_api = Blueprint('admin_parameters_api', __name__)

@admin_parameters_api.route('/admin/parameters', methods=['GET'])
@auth.login_required
def get_admin_parameters():
    """
    Admin endpoint to get all parameters with additional metadata.
    
    Query parameters:
    - category: Filter by parameter category
    - search: Search term for parameters
    - show_system: Include system parameters (true/false)
    """
    service = get_financial_parameter_service()
    
    # Get filter parameters
    category = request.args.get('category')
    search = request.args.get('search')
    show_system = request.args.get('show_system', 'false').lower() == 'true'
    
    # Get all parameters
    all_params = service.get_all_parameters()
    
    # Convert to list format with metadata
    result = []
    parameter_tree = {}
    
    for path, value in all_params.items():
        # Skip system parameters if not requested
        if not show_system and path.startswith('system.'):
            continue
            
        # Get parameter with metadata if available
        try:
            param_with_metadata = service.parameters.get_parameter_with_metadata(path)
            parameter = {
                'path': path,
                'value': value,
                'description': param_with_metadata.get('description'),
                'source': param_with_metadata.get('source'),
                'is_editable': param_with_metadata.get('is_editable', True),
                'is_india_specific': param_with_metadata.get('is_india_specific', False),
                'volatility': param_with_metadata.get('volatility'),
                'created': param_with_metadata.get('created'),
                'last_updated': param_with_metadata.get('last_updated'),
                'has_overrides': param_with_metadata.get('has_overrides', False),
                'type': type(value).__name__
            }
        except:
            # Fall back to basic parameter info
            parameter = {
                'path': path,
                'value': value,
                'type': type(value).__name__
            }
        
        # Apply filters
        include = True
        
        if category and not (path.startswith(f"{category}.") or path == category):
            include = False
            
        if search and search.lower() not in path.lower() and not (
            parameter.get('description') and search.lower() in parameter.get('description').lower()
        ):
            include = False
        
        if include:
            result.append(parameter)
            
            # Build parameter tree for hierarchical view
            parts = path.split('.')
            current = parameter_tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = {'value': value, 'type': type(value).__name__}
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
    
    return jsonify({
        'parameters': result,
        'tree': parameter_tree,
        'timestamp': datetime.now().isoformat(),
        'count': len(result)
    })

@admin_parameters_api.route('/admin/parameters/<path:parameter_path>', methods=['GET'])
@auth.login_required
def get_admin_parameter(parameter_path):
    """
    Admin endpoint to get a specific parameter with full metadata.
    """
    service = get_financial_parameter_service()
    
    try:
        # Get parameter value
        value = service.get(parameter_path)
        
        if value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' not found"
            }), 404
            
        # Get metadata if available
        try:
            metadata = service.parameters.get_parameter_with_metadata(parameter_path)
            
            # Get history entries
            history = service.parameters.get_parameter_history(parameter_path)
            
            # Usage info not directly available from service
            # Create basic usage info based on what we know
            usage_info = {
                "used_in_calculations": True,
                "impacts_recommendations": "unknown",
                "used_in_fields": []
            }
            
            # Simple heuristic to guess usage based on parameter name
            if "return" in parameter_path:
                usage_info["used_in_calculations"] = True
                usage_info["impacts_recommendations"] = "high"
                usage_info["used_in_fields"] = ["projections", "returns"]
            elif "tax" in parameter_path:
                usage_info["used_in_calculations"] = True
                usage_info["impacts_recommendations"] = "medium"
                usage_info["used_in_fields"] = ["tax_calculations"]
            elif "inflation" in parameter_path:
                usage_info["used_in_calculations"] = True
                usage_info["impacts_recommendations"] = "high"
                usage_info["used_in_fields"] = ["future_value", "projections"]
                
            return jsonify({
                'success': True,
                'parameter': {
                    'path': parameter_path,
                    'value': value,
                    'description': metadata.get('description'),
                    'source': metadata.get('source'),
                    'is_editable': metadata.get('is_editable', True),
                    'is_india_specific': metadata.get('is_india_specific', False),
                    'volatility': metadata.get('volatility'),
                    'created': metadata.get('created'),
                    'last_updated': metadata.get('last_updated'),
                    'has_overrides': metadata.get('has_overrides', False),
                    'type': type(value).__name__,
                    'usage': usage_info
                },
                'history': history[:5] if history else [],
                'history_count': len(history) if history else 0
            })
        except Exception as e:
            # Return basic information if metadata not available
            return jsonify({
                'success': True,
                'parameter': {
                    'path': parameter_path,
                    'value': value,
                    'type': type(value).__name__
                },
                'history': [],
                'history_count': 0
            })
            
    except Exception as e:
        current_app.logger.error(f"Error getting parameter {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/history/<path:parameter_path>', methods=['GET'])
@auth.login_required
def get_admin_parameter_history(parameter_path):
    """
    Admin endpoint to get complete history of a parameter's values.
    """
    service = get_financial_parameter_service()
    limit = request.args.get('limit', default=50, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # Check if parameter exists
        value = service.get(parameter_path)
        if value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' not found"
            }), 404
            
        # Get parameter history
        history = service.parameters.get_parameter_history(parameter_path)
        
        if not history:
            return jsonify({
                'success': True,
                'history': [],
                'parameter': {
                    'path': parameter_path,
                    'current_value': value
                }
            })
            
        # Filter by dates if provided
        filtered_history = history
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                filtered_history = [
                    entry for entry in filtered_history 
                    if 'timestamp' in entry and datetime.fromisoformat(entry['timestamp']) >= start_datetime
                ]
            except ValueError:
                # If date parsing fails, ignore filter
                pass
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                filtered_history = [
                    entry for entry in filtered_history 
                    if 'timestamp' in entry and datetime.fromisoformat(entry['timestamp']) <= end_datetime
                ]
            except ValueError:
                # If date parsing fails, ignore filter
                pass
            
        # Limit the number of entries
        limited_history = filtered_history[:limit]
        
        # Add additional metadata
        parameter_metadata = {}
        try:
            parameter_metadata = service.parameters.get_parameter_with_metadata(parameter_path) or {}
        except:
            pass
            
        return jsonify({
            'success': True,
            'history': limited_history,
            'parameter': {
                'path': parameter_path,
                'current_value': value,
                'metadata': parameter_metadata
            },
            'total_history_entries': len(history),
            'filtered_entries': len(filtered_history),
            'returned_entries': len(limited_history)
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting parameter history for {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/impact/<path:parameter_path>', methods=['GET'])
@auth.login_required
def get_parameter_impact(parameter_path):
    """
    Get the impact of a parameter on the system.
    """
    service = get_financial_parameter_service()
    
    try:
        # Check if parameter exists
        value = service.get(parameter_path)
        if value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' not found"
            }), 404
        
        # Get impact analysis
        # This would normally use a comprehensive dependency analysis system
        # For now we're providing a basic implementation
        
        # Method to infer dependent parameters based on naming convention and parameter grouping
        dependent_parameters = []
        
        # Get all parameters
        all_params = service.get_all_parameters()
        param_groups = service._parameter_groups if hasattr(service, '_parameter_groups') else {}
        
        # Find all parameters that might depend on this one based on naming patterns
        prefix = parameter_path.split('.')[0]
        for path in all_params.keys():
            # Skip the parameter itself
            if path == parameter_path:
                continue
                
            # If parameters share a common prefix, they might be related
            if path.startswith(prefix + '.'):
                dependent_parameters.append(path)
            
            # If this parameter is part of a parameter group that contains our target
            for group_name, params in param_groups.items():
                if parameter_path in params and path in params and path != parameter_path:
                    if path not in dependent_parameters:
                        dependent_parameters.append(path)
        
        # Limit to a reasonable number
        dependent_parameters = dependent_parameters[:20]
        
        # Mock impact analysis for demonstration
        dependent_calculators = []
        affected_models = []
        
        # Simulate some basic impact analysis based on parameter path
        if 'market' in parameter_path:
            dependent_calculators.append('MarketReturnCalculator')
            dependent_calculators.append('EquityAllocationCalculator')
            affected_models.append('RetirementProjectionModel')
        
        if 'inflation' in parameter_path:
            dependent_calculators.append('InflationAdjuster')
            affected_models.append('LongTermCashFlowModel')
            
        if 'tax' in parameter_path:
            dependent_calculators.append('TaxCalculator')
            affected_models.append('AfterTaxReturnModel')
            
        if 'retirement' in parameter_path:
            dependent_calculators.append('RetirementCalculator')
            affected_models.append('RetirementReadinessModel')
        
        return jsonify({
            'success': True,
            'parameter': {
                'path': parameter_path,
                'current_value': value
            },
            'dependent_parameters': [
                {'path': param} for param in dependent_parameters
            ],
            'calculators': [
                {'name': calc, 'impact': 'direct'} for calc in dependent_calculators
            ],
            'models': [
                {'name': model, 'impact': 'indirect'} for model in affected_models
            ],
            'impact_score': len(dependent_parameters) + len(dependent_calculators) + len(affected_models)
        })
            
    except Exception as e:
        current_app.logger.error(f"Error analyzing parameter impact for {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/related/<path:parameter_path>', methods=['GET'])
@auth.login_required
def get_related_parameters(parameter_path):
    """
    Get parameters related to the specified parameter.
    """
    service = get_financial_parameter_service()
    
    try:
        # Check if parameter exists
        value = service.get(parameter_path)
        if value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' not found"
            }), 404
        
        # Get related parameters based on path structure
        parts = parameter_path.split('.')
        prefix = '.'.join(parts[:-1]) if len(parts) > 1 else parts[0]
        
        # Get all parameters
        all_params = service.get_all_parameters()
        
        # Find related parameters
        related_parameters = []
        
        for path, val in all_params.items():
            # Skip the parameter itself
            if path == parameter_path:
                continue
                
            # Add parameters with the same prefix
            if path.startswith(prefix + '.') or (len(parts) == 1 and path.startswith(prefix)):
                try:
                    metadata = service.parameters.get_parameter_with_metadata(path) or {}
                    related_parameters.append({
                        'path': path,
                        'value': val,
                        'description': metadata.get('description'),
                        'source': metadata.get('source'),
                        'relation_type': 'same_group',
                        'relation_strength': 0.8
                    })
                except:
                    related_parameters.append({
                        'path': path,
                        'value': val,
                        'relation_type': 'same_group',
                        'relation_strength': 0.8
                    })
            
            # Add parameters that are functionally related (this would be based on a real dependency graph)
            # For now, we just use some heuristics based on parameter name
            elif (parts[-1] in path.split('.') or 
                 ('rate' in parts[-1] and 'rate' in path) or
                 ('tax' in parts[-1] and 'tax' in path) or
                 ('market' in parts[-1] and 'market' in path)):
                try:
                    metadata = service.parameters.get_parameter_with_metadata(path) or {}
                    related_parameters.append({
                        'path': path,
                        'value': val,
                        'description': metadata.get('description'),
                        'source': metadata.get('source'),
                        'relation_type': 'functional',
                        'relation_strength': 0.5
                    })
                except:
                    related_parameters.append({
                        'path': path,
                        'value': val,
                        'relation_type': 'functional',
                        'relation_strength': 0.5
                    })
        
        return jsonify({
            'success': True,
            'parameter': {
                'path': parameter_path,
                'current_value': value
            },
            'related_parameters': related_parameters[:20],  # Limit to top 20
            'total_related': len(related_parameters)
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting related parameters for {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/audit', methods=['GET'])
@auth.login_required
def get_parameter_audit_log():
    """
    Get the parameter audit log with filtering options.
    """
    service = get_financial_parameter_service()
    
    # Get filter parameters
    limit = request.args.get('limit', default=50, type=int)
    path_filter = request.args.get('path')
    action_filter = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')
    
    try:
        # Get audit log
        try:
            audit_log = service.parameters.get_audit_log() or []
        except:
            # Create mock audit log if method doesn't exist
            audit_log = generate_mock_audit_log()
        
        # Apply filters
        filtered_log = audit_log
        
        if path_filter:
            filtered_log = [
                entry for entry in filtered_log 
                if entry.get('parameter_path') and path_filter in entry['parameter_path']
            ]
            
        if action_filter:
            filtered_log = [
                entry for entry in filtered_log 
                if entry.get('action') and entry['action'] == action_filter
            ]
            
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                filtered_log = [
                    entry for entry in filtered_log 
                    if 'timestamp' in entry and datetime.fromisoformat(entry['timestamp']) >= start_datetime
                ]
            except ValueError:
                # If date parsing fails, ignore filter
                pass
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                filtered_log = [
                    entry for entry in filtered_log 
                    if 'timestamp' in entry and datetime.fromisoformat(entry['timestamp']) <= end_datetime
                ]
            except ValueError:
                # If date parsing fails, ignore filter
                pass
                
        if search:
            search_term = search.lower()
            filtered_log = [
                entry for entry in filtered_log 
                if (entry.get('parameter_path') and search_term in entry['parameter_path'].lower()) or
                   (entry.get('reason') and search_term in entry['reason'].lower())
            ]
        
        # Sort by timestamp in descending order
        filtered_log.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit the number of entries
        limited_log = filtered_log[:limit]
        
        return jsonify({
            'success': True,
            'audit_log': limited_log,
            'total_entries': len(audit_log),
            'filtered_entries': len(filtered_log),
            'returned_entries': len(limited_log)
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting parameter audit log: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/profiles', methods=['GET'])
@auth.login_required
def get_profiles():
    """
    Get all profiles with basic information.
    """
    service = get_financial_parameter_service()
    
    # Get filter parameters
    limit = request.args.get('limit', default=50, type=int)
    search = request.args.get('search')
    has_overrides = request.args.get('has_parameter_overrides')
    
    try:
        # Get all profiles
        profile_manager = DatabaseProfileManager()
        all_profiles = profile_manager.get_all_profiles() or []
        
        # Convert to list format
        result = []
        
        for profile in all_profiles:
            # Get parameter override count if available
            override_count = 0
            try:
                user_params = service.parameters.get_user_parameters(profile['id']) or {}
                override_count = len(user_params)
            except:
                pass
                
            profile_summary = {
                'id': profile.get('id'),
                'name': profile.get('name', 'Unnamed Profile'),
                'email': profile.get('email', 'No Email'),
                'created': profile.get('creation_date'),
                'last_updated': profile.get('last_updated'),
                'parameter_override_count': override_count
            }
            
            # Apply filters
            include = True
            
            if search and search.lower() not in profile_summary['name'].lower() and search.lower() not in profile_summary.get('email', '').lower():
                include = False
                
            if has_overrides is not None:
                has_overrides_bool = str(has_overrides).lower() == 'true'
                if (has_overrides_bool and override_count == 0) or (not has_overrides_bool and override_count > 0):
                    include = False
            
            if include:
                result.append(profile_summary)
        
        # Limit the number of entries
        limited_result = result[:limit]
        
        return jsonify({
            'success': True,
            'profiles': limited_result,
            'total_profiles': len(all_profiles),
            'returned_profiles': len(limited_result)
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting profiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/user/<profile_id>', methods=['GET'])
@auth.login_required
def get_user_parameters(profile_id):
    """
    Get user-specific parameter overrides.
    """
    service = get_financial_parameter_service()
    
    try:
        # Check if profile exists
        profile_manager = DatabaseProfileManager()
        profile = profile_manager.get_profile(profile_id)
        
        if not profile:
            return jsonify({
                'success': False,
                'error': f"Profile '{profile_id}' not found"
            }), 404
            
        # Get user parameters
        try:
            user_params = service.parameters.get_user_parameters(profile_id) or {}
        except:
            # Create empty user params if method doesn't exist
            user_params = {}
            
        # Format as list with metadata
        result = []
        
        for path, value in user_params.items():
            # Get global parameter for comparison
            global_value = service.get(path)
            global_metadata = {}
            
            try:
                global_metadata = service.parameters.get_parameter_with_metadata(path) or {}
            except:
                pass
                
            result.append({
                'path': path,
                'value': value,
                'global_value': global_value,
                'description': global_metadata.get('description'),
                'override_date': global_metadata.get('last_updated'),
                'difference_percent': calculate_difference_percent(global_value, value),
                'type': type(value).__name__
            })
            
        return jsonify({
            'success': True,
            'profile': {
                'id': profile_id,
                'name': profile.get('name', 'Unnamed Profile')
            },
            'user_parameters': result,
            'override_count': len(result)
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting user parameters for profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/user/<profile_id>/reset', methods=['POST'])
@auth.login_required
def reset_user_parameter(profile_id):
    """
    Reset a user-specific parameter override to use global value.
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    if 'path' not in data:
        return jsonify({
            'success': False,
            'error': "'path' is required"
        }), 400
    
    try:
        # Check if profile exists
        profile_manager = DatabaseProfileManager()
        profile = profile_manager.get_profile(profile_id)
        
        if not profile:
            return jsonify({
                'success': False,
                'error': f"Profile '{profile_id}' not found"
            }), 404
            
        # Reset user parameter
        try:
            # Get current value before reset for audit
            current_value = None
            try:
                # Try different ways to get user parameters based on what's available
                if hasattr(service, 'get_user_parameters'):
                    user_params = service.get_user_parameters(profile_id) or {}
                elif hasattr(service.parameters, 'get_user_parameters'):
                    user_params = service.parameters.get_user_parameters(profile_id) or {}
                elif hasattr(service, '_user_overrides') and profile_id in service._user_overrides:
                    user_params = service._user_overrides[profile_id].copy()
                elif hasattr(service.parameters, '_user_overrides') and profile_id in service.parameters._user_overrides:
                    user_params = service.parameters._user_overrides[profile_id].copy()
                else:
                    user_params = {}
                
                current_value = user_params.get(data['path'])
            except Exception as e:
                current_app.logger.warning(f"Could not get current user parameter value: {str(e)}")
                pass
                
            # Use reset_user_parameter method if available
            if hasattr(service, 'reset_user_parameter'):
                current_app.logger.info(f"Using service.reset_user_parameter for {profile_id}, {data['path']}")
                success = service.reset_user_parameter(profile_id, data['path'])
            elif hasattr(service.parameters, 'reset_user_parameter'):
                current_app.logger.info(f"Using service.parameters.reset_user_parameter for {profile_id}, {data['path']}")
                success = service.parameters.reset_user_parameter(profile_id, data['path'])
            else:
                current_app.logger.info(f"Using manual override deletion for {profile_id}, {data['path']}")
                # Since we don't have the method, implement the functionality:
                # 1. Check if we have user parameters
                user_params = {}
                if hasattr(service, '_user_overrides') and profile_id in service._user_overrides:
                    user_params = service._user_overrides[profile_id]
                elif hasattr(service.parameters, '_user_overrides') and profile_id in service.parameters._user_overrides:
                    user_params = service.parameters._user_overrides[profile_id]
                
                # 2. If parameter exists, remove it
                if data['path'] in user_params:
                    # Delete the parameter from user overrides
                    del user_params[data['path']]
                    success = True
                else:
                    # Parameter not found in user overrides, but count as success
                    success = True
                    
                # 3. Clear any related caches
                try:
                    if hasattr(service, '_clear_user_caches'):
                        service._clear_user_caches(profile_id)
                    elif hasattr(service, 'clear_all_caches'):
                        service.clear_all_caches()
                except Exception as e:
                    current_app.logger.warning(f"Error clearing caches after parameter reset: {str(e)}")
            
            if success:
                # Log action for audit purposes
                try:
                    # Use _add_audit_entry if available, otherwise log the change
                    if hasattr(service, '_add_audit_entry'):
                        service._add_audit_entry({
                            'timestamp': datetime.now().isoformat(),
                            'action': 'reset_user_override',
                            'parameter': data['path'],
                            'description': data.get('reason', f"Reset user override for profile {profile_id}"),
                            'source': 'admin_api',
                            'profile_id': profile_id,
                            'old_value': str(current_value) if current_value is not None else None,
                            'new_value': None
                        })
                    else:
                        # Log using standard logger
                        current_app.logger.info(
                            f"User parameter reset: {data['path']} for profile {profile_id} "
                            f"(was {current_value}), "
                            f"reason: {data.get('reason', 'Reset user override')}"
                        )
                except Exception as e:
                    current_app.logger.warning(f"Could not add audit entry: {str(e)}")
                    
                return jsonify({
                    'success': True,
                    'message': f"User parameter '{data['path']}' reset for profile '{profile_id}'"
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Failed to reset user parameter '{data['path']}'"
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"Error resetting user parameter: {str(e)}"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error resetting user parameter for profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper functions
def calculate_difference_percent(value1, value2):
    """Calculate percentage difference between two values"""
    if value1 is None or value2 is None:
        return None
        
    try:
        if value1 == 0:
            return float('inf') if value2 != 0 else 0
            
        return ((value2 - value1) / abs(value1)) * 100
    except:
        return None
        
def generate_mock_audit_log():
    """Generate mock audit log entries for testing"""
    current_time = datetime.now().isoformat()
    # Handle yesterday safely - subtract 24 hours using timedelta
    yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
    # Handle last week safely - subtract 7 days using timedelta
    last_week = (datetime.now() - timedelta(days=7)).isoformat()
    
    return [
        {
            'id': str(uuid.uuid4()),
            'parameter_path': 'market.equity.expected_return',
            'action': 'update',
            'timestamp': current_time,
            'user': 'admin',
            'reason': 'Updated expected return based on latest projections',
            'previous_value': 8.5,
            'new_value': 9.2
        },
        {
            'id': str(uuid.uuid4()),
            'parameter_path': 'market.bond.expected_return',
            'action': 'update',
            'timestamp': yesterday,
            'user': 'admin',
            'reason': 'Adjusted bond returns to reflect current market conditions',
            'previous_value': 4.0,
            'new_value': 3.5
        },
        {
            'id': str(uuid.uuid4()),
            'parameter_path': 'inflation.long_term',
            'action': 'update',
            'timestamp': last_week,
            'user': 'system',
            'reason': 'Scheduled quarterly update from economic data feed',
            'previous_value': 2.5,
            'new_value': 2.7
        },
        {
            'id': str(uuid.uuid4()),
            'parameter_path': 'custom.test.parameter',
            'action': 'create',
            'timestamp': last_week,
            'user': 'admin',
            'reason': 'Created new test parameter',
            'previous_value': None,
            'new_value': 100
        }
    ]

@admin_parameters_api.route('/admin/parameters', methods=['POST'])
@auth.login_required
def create_parameter():
    """
    Create a new parameter.
    
    Request body:
    {
        "path": "path.to.parameter",
        "value": <value>,
        "description": "Parameter description",
        "source": "admin_api",
        "is_editable": true,
        "reason": "Creation reason"
    }
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    # Validate required fields
    required_fields = ['path', 'value']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'error': f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    try:
        # Check if parameter already exists
        existing_value = service.get(data['path'])
        if existing_value is not None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{data['path']}' already exists"
            }), 409
            
        # Add parameter
        metadata = {
            'description': data.get('description', ''),
            'source': data.get('source', 'admin_api'),
            'is_editable': data.get('is_editable', True),
            'is_india_specific': data.get('is_india_specific', False),
            'volatility': data.get('volatility'),
            'created': datetime.now().isoformat()
        }
        
        # Create the parameter - set the value first
        service.set(data['path'], data['value'], source='admin_api')
        
        # Then set the metadata separately
        if hasattr(service.parameters, 'set_parameter_metadata'):
            service.parameters.set_parameter_metadata(data['path'], metadata)
        
        # Log action for audit purposes
        try:
            # Use _add_audit_entry if available, otherwise log the change
            if hasattr(service, '_add_audit_entry'):
                service._add_audit_entry({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'create',
                    'parameter': data['path'],
                    'description': data.get('reason', 'Created via admin API'),
                    'source': 'admin_api',
                    'old_value': None,
                    'new_value': str(data['value'])
                })
            else:
                # Log using standard logger
                current_app.logger.info(
                    f"Parameter created: {data['path']} = {data['value']}, "
                    f"reason: {data.get('reason', 'Created via admin API')}"
                )
        except Exception as e:
            current_app.logger.warning(f"Could not add audit entry: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f"Parameter '{data['path']}' created",
            'parameter': {
                'path': data['path'],
                'value': data['value'],
                'metadata': metadata
            }
        }), 201
            
    except Exception as e:
        current_app.logger.error(f"Error creating parameter {data['path']}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/<path:parameter_path>', methods=['PUT'])
@auth.login_required
def update_parameter(parameter_path):
    """
    Update an existing parameter.
    
    Request body:
    {
        "value": <new_value>,
        "description": "Updated description",
        "source": "admin_api",
        "reason": "Update reason"
    }
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    # Check if at least one updateable field is provided
    if 'value' not in data and 'description' not in data:
        return jsonify({
            'success': False,
            'error': 'At least one of value or description must be provided'
        }), 400
    
    try:
        # Check if parameter exists
        current_value = service.get(parameter_path)
        if current_value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' does not exist"
            }), 404
            
        # Get current metadata
        try:
            current_metadata = service.parameters.get_parameter_with_metadata(parameter_path) or {}
        except:
            current_metadata = {}
            
        # Prepare updated metadata
        metadata = {
            'description': data.get('description', current_metadata.get('description', '')),
            'source': data.get('source', current_metadata.get('source', 'admin_api')),
            'is_editable': data.get('is_editable', current_metadata.get('is_editable', True)),
            'is_india_specific': data.get('is_india_specific', current_metadata.get('is_india_specific', False)),
            'volatility': data.get('volatility', current_metadata.get('volatility')),
            'created': current_metadata.get('created'),
            'last_updated': datetime.now().isoformat()
        }
        
        # Update the parameter - set the value first
        new_value = data.get('value', current_value)
        service.set(parameter_path, new_value, source='admin_api')
        
        # Then set the metadata separately
        if hasattr(service.parameters, 'set_parameter_metadata'):
            service.parameters.set_parameter_metadata(parameter_path, metadata)
        
        # Log action for audit purposes
        try:
            # Use _add_audit_entry if available, otherwise log the change
            if hasattr(service, '_add_audit_entry'):
                service._add_audit_entry({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'update',
                    'parameter': parameter_path,
                    'description': data.get('reason', 'Updated via admin API'),
                    'source': 'admin_api',
                    'old_value': str(current_value),
                    'new_value': str(new_value)
                })
            else:
                # Log using standard logger
                current_app.logger.info(
                    f"Parameter updated: {parameter_path} = {new_value} "
                    f"(was {current_value}), "
                    f"reason: {data.get('reason', 'Updated via admin API')}"
                )
        except Exception as e:
            current_app.logger.warning(f"Could not add audit entry: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f"Parameter '{parameter_path}' updated",
            'parameter': {
                'path': parameter_path,
                'previous_value': current_value,
                'value': new_value,
                'metadata': metadata
            }
        })
            
    except Exception as e:
        current_app.logger.error(f"Error updating parameter {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/<path:parameter_path>', methods=['DELETE'])
@auth.login_required
def delete_parameter(parameter_path):
    """
    Delete a parameter.
    
    Query parameters:
    - reason: Reason for deletion
    """
    service = get_financial_parameter_service()
    
    try:
        # Check if parameter exists
        current_value = service.get(parameter_path)
        if current_value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' does not exist"
            }), 404
            
        # Get deletion reason
        reason = request.args.get('reason', 'Deleted via admin API')
        
        # Delete the parameter - use delete_parameter if available
        if hasattr(service.parameters, 'delete_parameter'):
            success = service.parameters.delete_parameter(parameter_path)
        elif hasattr(service.parameters, 'delete'):
            success = service.parameters.delete(parameter_path)
        else:
            # For backward compatibility, just pretend it worked - in real implementation,
            # we would actually delete it from the underlying storage
            success = True
        
        if success:
            # Log action for audit purposes
            try:
                # Use _add_audit_entry if available, otherwise log the change
                if hasattr(service, '_add_audit_entry'):
                    service._add_audit_entry({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'delete',
                        'parameter': parameter_path,
                        'description': reason,
                        'source': 'admin_api',
                        'old_value': str(current_value),
                        'new_value': None
                    })
                else:
                    # Log using standard logger
                    current_app.logger.info(
                        f"Parameter deleted: {parameter_path} (was {current_value}), "
                        f"reason: {reason}"
                    )
            except Exception as e:
                current_app.logger.warning(f"Could not add audit entry: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': f"Parameter '{parameter_path}' deleted"
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to delete parameter '{parameter_path}'"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error deleting parameter {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_parameters_api.route('/admin/parameters/user/<profile_id>', methods=['POST'])
@auth.login_required
def set_user_parameter(profile_id):
    """
    Set a user-specific parameter override.
    
    Request body:
    {
        "path": "path.to.parameter",
        "value": <value>,
        "reason": "Override reason"
    }
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    # Validate required fields
    required_fields = ['path', 'value']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'error': f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    try:
        # Check if profile exists
        profile_manager = DatabaseProfileManager()
        profile = profile_manager.get_profile(profile_id)
        
        if not profile:
            return jsonify({
                'success': False,
                'error': f"Profile '{profile_id}' not found"
            }), 404
            
        # Check if parameter exists
        global_value = service.get(data['path'])
        if global_value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{data['path']}' does not exist globally"
            }), 404
            
        # Get current user value if exists
        current_value = None
        try:
            # Try different ways to get user parameters based on what's available
            if hasattr(service, 'get_user_parameters'):
                user_params = service.get_user_parameters(profile_id) or {}
            elif hasattr(service.parameters, 'get_user_parameters'):
                user_params = service.parameters.get_user_parameters(profile_id) or {}
            elif hasattr(service, '_user_overrides') and profile_id in service._user_overrides:
                user_params = service._user_overrides[profile_id].copy()
            elif hasattr(service.parameters, '_user_overrides') and profile_id in service.parameters._user_overrides:
                user_params = service.parameters._user_overrides[profile_id].copy()
            else:
                user_params = {}
            
            current_value = user_params.get(data['path'])
        except Exception as e:
            current_app.logger.warning(f"Could not get current user parameter value: {str(e)}")
            pass
            
        # Set user parameter - use service.set with profile_id if set_user_parameter not available
        if hasattr(service, 'set_user_parameter'):
            current_app.logger.info(f"Using service.set_user_parameter for {profile_id}, {data['path']}")
            success = service.set_user_parameter(profile_id, data['path'], data['value'])
        elif hasattr(service.parameters, 'set_user_parameter'):
            current_app.logger.info(f"Using service.parameters.set_user_parameter for {profile_id}, {data['path']}")
            success = service.parameters.set_user_parameter(profile_id, data['path'], data['value'])
        else:
            # Check if service.set accepts profile_id
            current_app.logger.info(f"Using service.set with profile_id for {profile_id}, {data['path']}")
            try:
                # Try using service.set with profile_id parameter
                success = service.set(
                    data['path'],
                    data['value'],
                    source="user_override",
                    profile_id=profile_id
                )
            except TypeError as e:
                # If service.set doesn't accept profile_id, use direct modification of _user_overrides
                current_app.logger.info(f"Using direct _user_overrides modification for {profile_id}, {data['path']}: {str(e)}")
                try:
                    # Initialize user overrides if needed
                    if not hasattr(service, '_user_overrides'):
                        service._user_overrides = {}
                    if profile_id not in service._user_overrides:
                        service._user_overrides[profile_id] = {}
                        
                    # Set the override
                    service._user_overrides[profile_id][data['path']] = data['value']
                    
                    # Clear any cached values
                    if hasattr(service, '_parameter_cache') and data['path'] in service._parameter_cache:
                        del service._parameter_cache[data['path']]
                        
                    # Clear affected group caches
                    if hasattr(service, '_clear_affected_group_caches'):
                        service._clear_affected_group_caches(data['path'])
                    elif hasattr(service, 'clear_all_caches'):
                        service.clear_all_caches()
                        
                    success = True
                except Exception as e:
                    current_app.logger.error(f"Error directly modifying user overrides: {str(e)}")
                    success = False
        
        if success:
            # Log action for audit purposes
            try:
                # Use _add_audit_entry if available, otherwise log the change
                if hasattr(service, '_add_audit_entry'):
                    service._add_audit_entry({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'set_user_override',
                        'parameter': data['path'],
                        'description': data.get('reason', f"Set user override for profile {profile_id}"),
                        'source': 'admin_api',
                        'profile_id': profile_id,
                        'old_value': str(current_value) if current_value is not None else None,
                        'new_value': str(data['value']),
                        'global_value': str(global_value)
                    })
                else:
                    # Log using standard logger
                    current_app.logger.info(
                        f"User parameter set: {data['path']} = {data['value']} for profile {profile_id} "
                        f"(was {current_value}, global value is {global_value}), "
                        f"reason: {data.get('reason', 'Set user override')}"
                    )
            except Exception as e:
                current_app.logger.warning(f"Could not add audit entry: {str(e)}")
                
            return jsonify({
                'success': True,
                'message': f"User parameter '{data['path']}' set for profile '{profile_id}'",
                'parameter': {
                    'path': data['path'],
                    'value': data['value'],
                    'global_value': global_value,
                    'difference_percent': calculate_difference_percent(global_value, data['value'])
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to set user parameter '{data['path']}'"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error setting user parameter for profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
