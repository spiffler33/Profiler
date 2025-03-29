#!/usr/bin/env python3
"""
Test Parameter Interface

This script tests the extended parameter interface functionality.
"""

import json
from services.financial_parameter_service import get_financial_parameter_service

def main():
    # Get parameter service
    param_service = get_financial_parameter_service()
    parameters_obj = param_service.parameters
    
    # Test get_all_parameters
    print("Testing get_all_parameters...")
    all_params = parameters_obj.get_all_parameters()
    print(f"Retrieved {len(all_params)} parameters")
    
    # Print first few parameters
    print("\nSample Parameters:")
    for param in all_params[:5]:
        print(f"- {param['path']}: {param['value']}")
    
    # Test parameter metadata
    param_path = "inflation.general"
    print(f"\nTesting get_parameter_with_metadata for '{param_path}'...")
    param_data = parameters_obj.get_parameter_with_metadata(param_path)
    print(f"Parameter data: {json.dumps(param_data, indent=2)}")
    
    # Test setting metadata
    print(f"\nTesting set_parameter_metadata for '{param_path}'...")
    success = parameters_obj.set_parameter_metadata(param_path, {
        "description": "General inflation rate (annual)",
        "source": "RBI projections"
    })
    print(f"Metadata set: {success}")
    
    # Verify metadata was set
    param_data = parameters_obj.get_parameter_with_metadata(param_path)
    print(f"Updated parameter data: {json.dumps(param_data, indent=2)}")

if __name__ == "__main__":
    main()