#!/usr/bin/env python3
"""
Parameter Management API Module

This module provides RESTful API endpoints for managing financial parameters
in the Profiler4 system. It enables programmatic access to the parameter
management system.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

# Import services
from services.financial_parameter_service import get_financial_parameter_service

# Create Blueprint
parameter_api = Blueprint('parameter_api', __name__)

# Set up authentication for parameter API
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    """Verify credentials for API authentication."""
    from config import Config
    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        return username
    return None

@parameter_api.route('/parameters', methods=['GET'])
@auth.login_required
def get_parameters():
    """
    Get parameters, optionally filtered by group.
    
    Query parameters:
    - group: Filter by parameter group (e.g., "market.equity")
    - search: Search in parameter names and descriptions
    - is_india_specific: Filter India-specific parameters (true/false)
    
    Returns:
        JSON response with parameters
    """
    service = get_financial_parameter_service()
    
    # Get filter parameters
    group = request.args.get('group')
    search = request.args.get('search')
    is_india_specific = request.args.get('is_india_specific')
    
    # Get all parameters
    all_params = service.get_all_parameters()
    
    # Convert to list format with metadata
    result = []
    parameter_tree = {}
    
    for path, value in all_params.items():
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
                'has_overrides': param_with_metadata.get('has_overrides', False)
            }
        except:
            # Fall back to basic parameter info
            parameter = {
                'path': path,
                'value': value
            }
        
        # Apply filters
        include = True
        
        if group and not (path.startswith(f"{group}.") or path == group):
            include = False
            
        if search and search.lower() not in path.lower() and not (
            parameter.get('description') and search.lower() in parameter.get('description').lower()
        ):
            include = False
            
        if is_india_specific is not None:
            is_india = str(is_india_specific).lower() == 'true'
            if parameter.get('is_india_specific', False) != is_india:
                include = False
        
        if include:
            result.append(parameter)
            
            # Build parameter tree for hierarchical view
            parts = path.split('.')
            current = parameter_tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
    
    return jsonify({
        'parameters': result,
        'tree': parameter_tree
    })

@parameter_api.route('/parameters/<path:parameter_path>', methods=['GET'])
@auth.login_required
def get_parameter(parameter_path):
    """
    Get a specific parameter by path.
    
    Args:
        parameter_path: Path to the parameter
        
    Returns:
        JSON response with parameter details
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
            
            # Get history
            history = service.parameters.get_parameter_history(parameter_path)
            
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
                    'has_overrides': metadata.get('has_overrides', False)
                },
                'history': history[:10] if history else []
            })
        except Exception as e:
            # Return basic information if metadata not available
            return jsonify({
                'success': True,
                'parameter': {
                    'path': parameter_path,
                    'value': value
                },
                'history': []
            })
            
    except Exception as e:
        current_app.logger.error(f"Error getting parameter {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api.route('/parameters/<path:parameter_path>', methods=['PUT'])
@auth.login_required
def update_parameter(parameter_path):
    """
    Update an existing parameter.
    
    Args:
        parameter_path: Path to the parameter
        
    Body:
        {
            "value": <new value>,
            "description": "Optional description",
            "source": "Source of the update",
            "reason": "Reason for the update"
        }
        
    Returns:
        JSON response with update status
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    if 'value' not in data:
        return jsonify({
            'success': False,
            'error': 'Value is required'
        }), 400
    
    try:
        # Get metadata first
        try:
            metadata = service.parameters.get_parameter_with_metadata(parameter_path) or {}
        except:
            metadata = {}
            
        # Update metadata if provided
        if 'description' in data:
            metadata['description'] = data['description']
            
        if 'source' in data:
            metadata['source'] = data['source']
            
        # Set metadata if any updates were made
        if 'description' in data or 'source' in data:
            try:
                service.parameters.set_parameter_metadata(parameter_path, metadata)
            except Exception as e:
                current_app.logger.warning(f"Could not update parameter metadata: {str(e)}")
        
        # Update the parameter value
        success = service.set(
            parameter_path, 
            data['value'],
            source=data.get('source', 'api'),
            source_priority=data.get('source_priority'),
            reason=data.get('reason')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Parameter '{parameter_path}' updated successfully"
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to update parameter '{parameter_path}'"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error updating parameter {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api.route('/parameters', methods=['POST'])
@auth.login_required
def create_parameter():
    """
    Create a new parameter.
    
    Body:
        {
            "path": "parameter.path",
            "value": <value>,
            "description": "Optional description",
            "source": "Source of the parameter",
            "is_editable": true/false,
            "is_india_specific": true/false
        }
        
    Returns:
        JSON response with creation status
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    required_fields = ['path', 'value']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f"'{field}' is required"
            }), 400
    
    try:
        # Check if parameter already exists
        existing_value = service.get(data['path'])
        if existing_value is not None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{data['path']}' already exists"
            }), 409
            
        # Set the metadata
        metadata = {
            'description': data.get('description'),
            'source': data.get('source', 'api'),
            'is_editable': data.get('is_editable', True),
            'is_india_specific': data.get('is_india_specific', False)
        }
        
        try:
            service.parameters.set_parameter_metadata(data['path'], metadata)
        except Exception as e:
            current_app.logger.warning(f"Could not set parameter metadata: {str(e)}")
        
        # Create the parameter
        success = service.set(
            data['path'], 
            data['value'],
            source=data.get('source', 'api')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Parameter '{data['path']}' created successfully"
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to create parameter '{data['path']}'"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating parameter: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api.route('/parameters/<path:parameter_path>', methods=['DELETE'])
@auth.login_required
def delete_parameter(parameter_path):
    """
    Delete a parameter.
    
    Args:
        parameter_path: Path to the parameter
        
    Returns:
        JSON response with deletion status
    """
    service = get_financial_parameter_service()
    
    try:
        # Check if parameter exists
        existing_value = service.get(parameter_path)
        if existing_value is None:
            return jsonify({
                'success': False,
                'error': f"Parameter '{parameter_path}' not found"
            }), 404
            
        # Delete the parameter
        success = service.parameters.delete_parameter(parameter_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Parameter '{parameter_path}' deleted successfully"
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

@parameter_api.route('/parameters/bulk', methods=['POST'])
@auth.login_required
def bulk_update_parameters():
    """
    Update multiple parameters in a single request.
    
    Body:
        {
            "parameters": [
                {"path": "param1.path", "value": value1},
                {"path": "param2.path", "value": value2}
            ],
            "source": "Source of the update",
            "reason": "Reason for the bulk update"
        }
        
    Returns:
        JSON response with update status
    """
    service = get_financial_parameter_service()
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    if 'parameters' not in data or not isinstance(data['parameters'], list):
        return jsonify({
            'success': False,
            'error': 'parameters list is required'
        }), 400
    
    try:
        # Process each parameter
        results = []
        source = data.get('source', 'api_bulk')
        reason = data.get('reason')
        
        for param in data['parameters']:
            if 'path' not in param or 'value' not in param:
                results.append({
                    'path': param.get('path', 'unknown'),
                    'success': False,
                    'error': 'path and value are required'
                })
                continue
                
            try:
                success = service.set(
                    param['path'], 
                    param['value'],
                    source=source,
                    reason=reason
                )
                
                results.append({
                    'path': param['path'],
                    'success': success,
                    'error': None if success else 'Failed to update parameter'
                })
            except Exception as e:
                results.append({
                    'path': param['path'],
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate summary
        success_count = sum(1 for r in results if r['success'])
        failure_count = len(results) - success_count
        
        return jsonify({
            'success': failure_count == 0,
            'results': results,
            'summary': {
                'total': len(results),
                'success': success_count,
                'failure': failure_count
            }
        })
            
    except Exception as e:
        current_app.logger.error(f"Error during bulk parameter update: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api.route('/parameters/history/<path:parameter_path>', methods=['GET'])
@auth.login_required
def get_parameter_history(parameter_path):
    """
    Get history of a parameter's values.
    
    Args:
        parameter_path: Path to the parameter
        
    Query parameters:
    - limit: Maximum number of history entries to return
        
    Returns:
        JSON response with parameter history
    """
    service = get_financial_parameter_service()
    limit = request.args.get('limit', default=10, type=int)
    
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
                'history': []
            })
            
        # Limit the number of entries
        limited_history = history[:limit]
        
        return jsonify({
            'success': True,
            'history': limited_history
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting parameter history for {parameter_path}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500