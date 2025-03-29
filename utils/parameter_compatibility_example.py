#!/usr/bin/env python3
"""
Parameter Compatibility Example

This script demonstrates how to use the parameter compatibility layer, showing
both legacy parameter access and new hierarchical path access working together.
"""

import logging
from models.financial_parameters import get_parameters, get_legacy_access_report

def demonstrate_compatibility():
    """Demonstrate the parameter compatibility adapter"""
    # Get parameters (returns compatibility adapter if LEGACY_ACCESS_ENABLED=True)
    params = get_parameters()
    
    print("Parameter Compatibility Example")
    print("==============================\n")
    
    # Example 1: Legacy key access
    print("Example 1: Legacy Key Access")
    inflation_legacy = params.get("inflation_rate")
    print(f"  inflation_rate = {inflation_legacy:.2%}")
    
    # Example 2: New hierarchical path access
    print("\nExample 2: New Hierarchical Path Access")
    inflation_new = params.get("inflation.general")
    print(f"  inflation.general = {inflation_new:.2%}")
    
    # Verify they return the same value
    print(f"  Same value? {'Yes' if inflation_legacy == inflation_new else 'No'}")
    
    # Example 3: Nested parameter access
    print("\nExample 3: Nested Parameter Access")
    school_inflation = params.get("inflation.education.school")
    college_inflation = params.get("inflation.education.college")
    print(f"  School education inflation: {school_inflation:.2%}")
    print(f"  College education inflation: {college_inflation:.2%}")
    
    # Example 4: Special method delegation for asset returns
    print("\nExample 4: Special Method Delegation")
    equity_large_cap = params.get_asset_return("equity", "large_cap")
    equity_conservative = params.get_asset_return("equity", None, "conservative")
    print(f"  Large cap equity return: {equity_large_cap:.2%}")
    print(f"  Conservative equity return: {equity_conservative:.2%}")
    
    # Example 5: Special method delegation for allocation models
    print("\nExample 5: Allocation Models")
    conservative_model = params.get_allocation_model("conservative")
    print("  Conservative allocation model:")
    for asset_class, allocation in conservative_model.items():
        if asset_class != "sub_allocation":
            print(f"    {asset_class}: {allocation:.2%}")
    
    # Example 6: Access log report
    print("\nExample 6: Accessing Legacy Key Usage Report")
    access_log = get_legacy_access_report()
    print("  Legacy key access log:")
    for key, count in access_log.items():
        print(f"    '{key}' accessed {count} times")

if __name__ == "__main__":
    # Configure logging to see deprecation warnings
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demonstration
    demonstrate_compatibility()