#!/usr/bin/env python3
"""
Parameter Management Script

This script provides command-line interface for managing financial parameters
in the Profiler4 application.
"""

import os
import sys
import json
import argparse
import csv
from datetime import datetime

# Add parent directory to path to allow for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the financial parameter service
from services.financial_parameter_service import get_financial_parameter_service, FinancialParameterService

def setup_arg_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(description='Manage financial parameters')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List parameters')
    list_parser.add_argument('--group', help='Filter by parameter group (e.g., market.equity)')
    list_parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text',
                            help='Output format')
    list_parser.add_argument('--output', help='Output file path (optional)')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get a specific parameter')
    get_parser.add_argument('path', help='Parameter path (e.g., market.equity.equity_large_cap)')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set a parameter value')
    set_parser.add_argument('path', help='Parameter path (e.g., market.equity.equity_large_cap)')
    set_parser.add_argument('value', help='Parameter value')
    set_parser.add_argument('--source', default='command_line', help='Source of the parameter update')
    set_parser.add_argument('--description', help='Parameter description')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import parameters from a file')
    import_parser.add_argument('file', help='File path to import from')
    import_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                              help='Import format')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export parameters to a file')
    export_parser.add_argument('--output', required=True, help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                              help='Export format')
    export_parser.add_argument('--group', help='Filter by parameter group (e.g., market.equity)')
    
    # History command
    history_parser = subparsers.add_parser('history', help='View parameter history')
    history_parser.add_argument('path', help='Parameter path')
    history_parser.add_argument('--limit', type=int, default=10, help='Maximum number of history entries')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a parameter')
    delete_parser.add_argument('path', help='Parameter path to delete')
    delete_parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')
    
    # User command
    user_parser = subparsers.add_parser('user', help='Manage user parameter overrides')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='User parameter command')
    
    # User list command
    user_list_parser = user_subparsers.add_parser('list', help='List user parameter overrides')
    user_list_parser.add_argument('profile_id', help='User profile ID')
    
    # User set command
    user_set_parser = user_subparsers.add_parser('set', help='Set a user parameter override')
    user_set_parser.add_argument('profile_id', help='User profile ID')
    user_set_parser.add_argument('path', help='Parameter path')
    user_set_parser.add_argument('value', help='Parameter value')
    
    # User reset command
    user_reset_parser = user_subparsers.add_parser('reset', help='Reset a user parameter override')
    user_reset_parser.add_argument('profile_id', help='User profile ID')
    user_reset_parser.add_argument('path', help='Parameter path to reset')
    
    return parser

def list_parameters(args, service):
    """List parameters, optionally filtered by group."""
    # Get all parameters
    all_params = service.get_all_parameters()
    
    # Filter by group if specified
    filtered_params = {}
    if args.group:
        prefix = args.group + '.'
        for path, value in all_params.items():
            if path.startswith(prefix) or path == args.group:
                filtered_params[path] = value
    else:
        filtered_params = all_params
    
    # Format and output the results
    if args.format == 'json':
        output = json.dumps(filtered_params, indent=2)
    elif args.format == 'csv':
        output = "path,value\n"
        for path, value in sorted(filtered_params.items()):
            output += f"{path},{value}\n"
    else:  # text format
        output = "Parameter List:\n"
        output += "=" * 80 + "\n"
        for path, value in sorted(filtered_params.items()):
            output += f"{path}: {value}\n"
    
    # Write to file if specified, otherwise print to console
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Parameters exported to {args.output}")
    else:
        print(output)

def get_parameter(args, service):
    """Get a specific parameter value."""
    value = service.get(args.path)
    if value is None:
        print(f"Parameter '{args.path}' not found")
        return 1
    
    print(f"{args.path}: {value}")
    return 0

def set_parameter(args, service):
    """Set a parameter value."""
    # Parse the value based on its format
    value = args.value
    try:
        # Try to convert to number if possible
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'null':
            value = None
        elif '.' in value:
            value = float(value)
        else:
            value = int(value)
    except (ValueError, AttributeError):
        # If conversion fails, keep as string
        pass
    
    # Additional parameters
    params = {
        'source': args.source
    }
    
    if args.description:
        params['description'] = args.description
    
    # Set the parameter value
    success = service.set(args.path, value, **params)
    
    if success:
        print(f"Parameter '{args.path}' set to '{value}'")
        return 0
    else:
        print(f"Failed to set parameter '{args.path}'")
        return 1

def import_parameters(args, service):
    """Import parameters from a file."""
    try:
        if args.format == 'json':
            with open(args.file, 'r') as f:
                parameters = json.load(f)
            
            # JSON can be in different formats
            if isinstance(parameters, dict):
                # Flat dictionary format {path: value, ...}
                params_to_import = parameters
            elif isinstance(parameters, list):
                # List of parameter objects [{"path": path, "value": value}, ...]
                params_to_import = {p['path']: p['value'] for p in parameters}
            else:
                print(f"Invalid JSON format in {args.file}")
                return 1
        else:  # CSV format
            params_to_import = {}
            with open(args.file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'path' in row and 'value' in row:
                        params_to_import[row['path']] = row['value']
        
        # Import parameters
        success_count = 0
        failure_count = 0
        for path, value in params_to_import.items():
            success = service.set(path, value, source=f"import_{args.format}")
            if success:
                success_count += 1
            else:
                failure_count += 1
                print(f"Failed to import parameter: {path}")
        
        print(f"Import completed: {success_count} parameters imported successfully, {failure_count} failed")
        return 0 if failure_count == 0 else 1
    
    except Exception as e:
        print(f"Error importing parameters: {str(e)}")
        return 1

def export_parameters(args, service):
    """Export parameters to a file."""
    try:
        # Get parameters, filtered by group if specified
        all_params = service.get_all_parameters()
        
        # Filter by group if specified
        if args.group:
            prefix = args.group + '.'
            filtered_params = {path: value for path, value in all_params.items() 
                               if path.startswith(prefix) or path == args.group}
        else:
            filtered_params = all_params
        
        # Export in the specified format
        if args.format == 'json':
            with open(args.output, 'w') as f:
                json.dump(filtered_params, f, indent=2)
        else:  # CSV format
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['path', 'value'])
                for path, value in filtered_params.items():
                    writer.writerow([path, value])
        
        print(f"Parameters exported to {args.output}")
        return 0
    
    except Exception as e:
        print(f"Error exporting parameters: {str(e)}")
        return 1

def view_parameter_history(args, service):
    """View the history of a parameter."""
    try:
        # Get parameter history
        history = service.parameters.get_parameter_history(args.path)
        
        if not history:
            print(f"No history found for parameter '{args.path}'")
            return 0
        
        # Limit the number of entries
        history = history[:args.limit]
        
        # Display the history
        print(f"History for parameter '{args.path}':")
        print("=" * 80)
        for entry in history:
            timestamp = entry.get('timestamp', 'Unknown')
            value = entry.get('value', 'Unknown')
            source = entry.get('source', 'Unknown')
            
            print(f"{timestamp} | {value} | Source: {source}")
        
        return 0
    
    except Exception as e:
        print(f"Error retrieving parameter history: {str(e)}")
        return 1

def delete_parameter(args, service):
    """Delete a parameter."""
    # Confirm deletion if not forced
    if not args.force:
        confirm = input(f"Are you sure you want to delete parameter '{args.path}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return 0
    
    # Delete the parameter
    success = service.parameters.delete_parameter(args.path)
    
    if success:
        print(f"Parameter '{args.path}' deleted")
        return 0
    else:
        print(f"Failed to delete parameter '{args.path}'")
        return 1

def list_user_parameters(args, service):
    """List user parameter overrides."""
    user_params = service.get_user_parameters(args.profile_id)
    
    if not user_params:
        print(f"No parameter overrides found for profile '{args.profile_id}'")
        return 0
    
    print(f"Parameter overrides for profile '{args.profile_id}':")
    print("=" * 80)
    for path, value in sorted(user_params.items()):
        global_value = service.get(path)
        print(f"{path}:")
        print(f"  Override: {value}")
        print(f"  Global:   {global_value}")
    
    return 0

def set_user_parameter(args, service):
    """Set a user parameter override."""
    # Parse the value
    value = args.value
    try:
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'null':
            value = None
        elif '.' in value:
            value = float(value)
        else:
            value = int(value)
    except (ValueError, AttributeError):
        # If conversion fails, keep as string
        pass
    
    # Set the user parameter
    success = service.set_user_parameter(args.profile_id, args.path, value)
    
    if success:
        print(f"User parameter '{args.path}' set to '{value}' for profile '{args.profile_id}'")
        return 0
    else:
        print(f"Failed to set user parameter '{args.path}' for profile '{args.profile_id}'")
        return 1

def reset_user_parameter(args, service):
    """Reset a user parameter override."""
    success = service.reset_user_parameter(args.profile_id, args.path)
    
    if success:
        print(f"User parameter '{args.path}' reset to global value for profile '{args.profile_id}'")
        return 0
    else:
        print(f"Failed to reset user parameter '{args.path}' for profile '{args.profile_id}'")
        return 1

def main():
    """Main entry point for the script."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize the parameter service
    service = get_financial_parameter_service()
    
    # Execute the appropriate command
    if args.command == 'list':
        return list_parameters(args, service)
    
    elif args.command == 'get':
        return get_parameter(args, service)
    
    elif args.command == 'set':
        return set_parameter(args, service)
    
    elif args.command == 'import':
        return import_parameters(args, service)
    
    elif args.command == 'export':
        return export_parameters(args, service)
    
    elif args.command == 'history':
        return view_parameter_history(args, service)
    
    elif args.command == 'delete':
        return delete_parameter(args, service)
    
    elif args.command == 'user':
        if not args.user_command:
            parser.parse_args(['user', '--help'])
            return 1
        
        if args.user_command == 'list':
            return list_user_parameters(args, service)
        
        elif args.user_command == 'set':
            return set_user_parameter(args, service)
        
        elif args.user_command == 'reset':
            return reset_user_parameter(args, service)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())