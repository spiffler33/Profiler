#!/usr/bin/env python3
"""
Dependency analysis tool for Monte Carlo simulation components.

This script detects API dependencies and changes in the Monte Carlo simulation
system to prevent breaking changes.
"""

import ast
import os
import sys
import json
from typing import Dict, List, Set, Optional, Tuple
import glob
import difflib

# API signatures to track
CORE_API_SIGNATURES = {
    # core.py functions
    "run_simulation": {
        "params": ["goal", "return_assumptions", "inflation_rate", "simulation_count", "time_horizon_years"],
        "required": ["goal", "return_assumptions"]
    },
    "get_simulation_config": {
        "params": ["goal_type"],
        "required": ["goal_type"]
    },
    
    # cache.py functions
    "cached_simulation": {
        "params": ["func", "ttl", "key_prefix"],
        "required": []
    },
    "invalidate_cache": {
        "params": ["pattern"],
        "required": []
    },
    "get_cache_stats": {
        "params": [],
        "required": []
    },
    
    # parallel.py functions
    "run_parallel_monte_carlo": {
        "params": ["initial_amount", "contribution_pattern", "years", "allocation_strategy", 
                   "simulation_function", "simulations", "confidence_levels", "seed", 
                   "max_workers", "chunk_size"],
        "required": ["initial_amount", "contribution_pattern", "years", "allocation_strategy", 
                     "simulation_function"]
    },
    
    # array_fix.py functions
    "safe_array_compare": {
        "params": ["array", "value", "comparison"],
        "required": ["array", "value"]
    },
    "to_scalar": {
        "params": ["value"],
        "required": ["value"]
    },
    "safe_array_to_bool": {
        "params": ["array", "operation"],
        "required": ["array"]
    },
    "with_numpy_error_handled": {
        "params": ["func"],
        "required": ["func"]
    }
}

# Directory paths
MONTE_CARLO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "models", "monte_carlo")
API_SIGNATURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "monte_carlo_api_signatures.json")

class APIUsageAnalyzer(ast.NodeVisitor):
    """Analyze Python files for Monte Carlo API usage."""
    
    def __init__(self):
        self.api_calls = {}
        self.imports = {}
        
    def visit_Import(self, node):
        """Track imports."""
        for name in node.names:
            self.imports[name.name] = name.asname or name.name
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Track from imports."""
        if node.module and ('monte_carlo' in node.module):
            for name in node.names:
                self.imports[name.name] = name.asname or name.name
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Track function calls."""
        # Direct function calls
        if isinstance(node.func, ast.Name) and node.func.id in CORE_API_SIGNATURES:
            func_name = node.func.id
            args, kwargs = self._extract_args_kwargs(node)
            if func_name not in self.api_calls:
                self.api_calls[func_name] = []
            self.api_calls[func_name].append((args, kwargs))
            
        # Attribute calls (e.g. module.function)
        elif isinstance(node.func, ast.Attribute) and node.func.attr in CORE_API_SIGNATURES:
            func_name = node.func.attr
            args, kwargs = self._extract_args_kwargs(node)
            if func_name not in self.api_calls:
                self.api_calls[func_name] = []
            self.api_calls[func_name].append((args, kwargs))
            
        self.generic_visit(node)
        
    def _extract_args_kwargs(self, node):
        """Extract args and kwargs from a function call."""
        args = []
        kwargs = {}
        
        # Extract positional arguments
        for arg in node.args:
            if isinstance(arg, ast.Name):
                args.append(arg.id)
            else:
                args.append(None)  # Can't determine the name
                
        # Extract keyword arguments
        for keyword in node.keywords:
            if keyword.arg is not None:
                kwargs[keyword.arg] = True
                
        return args, kwargs

class APIDefinitionAnalyzer(ast.NodeVisitor):
    """Analyze Python files for API function definitions."""
    
    def __init__(self):
        self.api_definitions = {}
        
    def visit_FunctionDef(self, node):
        """Track function definitions."""
        if node.name in CORE_API_SIGNATURES:
            params = []
            required = []
            defaults_count = len(node.args.defaults)
            non_default_count = len(node.args.args) - defaults_count
            
            # Extract parameters
            for i, arg in enumerate(node.args.args):
                if hasattr(arg, 'arg'):  # Python 3
                    param_name = arg.arg
                else:  # Python 2
                    param_name = arg.id
                
                # Skip 'self' parameter
                if i == 0 and param_name == 'self':
                    continue
                    
                params.append(param_name)
                
                # Check if this is a required parameter
                if i < non_default_count:
                    required.append(param_name)
            
            self.api_definitions[node.name] = {
                "params": params,
                "required": required
            }
            
        self.generic_visit(node)

def analyze_file(file_path: str) -> Dict:
    """Analyze a Python file for Monte Carlo API usage."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            
        usage_analyzer = APIUsageAnalyzer()
        usage_analyzer.visit(tree)
        
        return {
            "file": file_path,
            "api_calls": usage_analyzer.api_calls,
            "imports": usage_analyzer.imports
        }
    except SyntaxError:
        print(f"Syntax error in file: {file_path}")
        return {
            "file": file_path,
            "api_calls": {},
            "imports": {}
        }

def extract_current_api_signatures() -> Dict:
    """Extract current API signatures from Monte Carlo module files."""
    signatures = {}
    
    # Check each Python file in the Monte Carlo directory
    for file_path in glob.glob(os.path.join(MONTE_CARLO_DIR, "*.py")):
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            definition_analyzer = APIDefinitionAnalyzer()
            definition_analyzer.visit(tree)
            
            # Add definitions to signatures
            signatures.update(definition_analyzer.api_definitions)
        except SyntaxError:
            print(f"Syntax error in file: {file_path}")
    
    return signatures

def save_api_signatures(signatures: Dict):
    """Save API signatures to a JSON file."""
    with open(API_SIGNATURE_FILE, 'w') as f:
        json.dump(signatures, f, indent=2)

def load_previous_api_signatures() -> Dict:
    """Load previous API signatures from a JSON file."""
    if os.path.exists(API_SIGNATURE_FILE):
        try:
            with open(API_SIGNATURE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def compare_signatures(previous: Dict, current: Dict) -> List[str]:
    """Compare previous and current API signatures to detect breaking changes."""
    changes = []
    
    # Check for removed functions
    for func_name in previous:
        if func_name not in current:
            changes.append(f"BREAKING CHANGE: Function '{func_name}' has been removed")
    
    # Check for parameter changes
    for func_name, prev_sig in previous.items():
        if func_name in current:
            curr_sig = current[func_name]
            
            # Check for removed parameters
            for param in prev_sig["params"]:
                if param not in curr_sig["params"]:
                    changes.append(f"BREAKING CHANGE: Parameter '{param}' removed from '{func_name}'")
            
            # Check for changed required parameters
            for param in prev_sig["required"]:
                if param in curr_sig["params"] and param not in curr_sig["required"]:
                    changes.append(f"BREAKING CHANGE: Parameter '{param}' in '{func_name}' is no longer required")
            
            # Check for added required parameters
            for param in curr_sig["required"]:
                if param not in prev_sig["required"]:
                    changes.append(f"BREAKING CHANGE: New required parameter '{param}' added to '{func_name}'")
    
    return changes

def check_usage_compatibility(usages: List[Dict], signatures: Dict) -> List[str]:
    """Check if current code usage is compatible with API signatures."""
    issues = []
    
    for usage in usages:
        file_path = usage["file"]
        
        for func_name, calls in usage["api_calls"].items():
            if func_name in signatures:
                sig = signatures[func_name]
                
                for args, kwargs in calls:
                    # Check positional arguments
                    for i, arg in enumerate(args):
                        if i >= len(sig["params"]):
                            issues.append(f"ERROR: Too many positional arguments for '{func_name}' in {file_path}")
                    
                    # Check that all required parameters are provided
                    for req_param in sig["required"]:
                        param_index = sig["params"].index(req_param) if req_param in sig["params"] else -1
                        
                        # Check if the required param is provided as positional arg
                        has_positional = param_index < len(args) and args[param_index] is not None
                        
                        # Check if the required param is provided as keyword arg
                        has_keyword = req_param in kwargs
                        
                        if not (has_positional or has_keyword):
                            issues.append(f"ERROR: Missing required parameter '{req_param}' for '{func_name}' in {file_path}")
    
    return issues

def analyze_codebase():
    """Analyze the codebase for Monte Carlo API usage and compatibility."""
    print("Analyzing Monte Carlo API dependencies...")
    
    # Get the current API signatures
    current_signatures = extract_current_api_signatures()
    
    # Get the previous API signatures (if available)
    previous_signatures = load_previous_api_signatures()
    
    # Compare signatures to detect breaking changes
    changes = compare_signatures(previous_signatures, current_signatures)
    
    # If there are breaking changes, show them and exit with an error
    if changes:
        print("\nBREAKING CHANGES DETECTED:")
        for change in changes:
            print(f"  - {change}")
        print("\nPlease update your API or use deprecation patterns before making breaking changes.")
        sys.exit(1)
    
    # Save the current signatures for future comparisons
    save_api_signatures(current_signatures)
    
    # Find all Python files in the project
    python_files = []
    for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        # Skip the venv directory and monte_carlo directory (we're checking files that USE the API)
        if 'venv' in root or 'monte_carlo' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Analyze each file for Monte Carlo API usage
    usages = []
    for file_path in python_files:
        usage = analyze_file(file_path)
        if usage["api_calls"]:
            usages.append(usage)
    
    # Check for compatibility issues
    issues = check_usage_compatibility(usages, current_signatures)
    
    if issues:
        print("\nAPIs USED IN AN INCOMPATIBLE WAY:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before committing.")
        sys.exit(1)
    
    # Print summary
    print("\nAPI DEPENDENCY ANALYSIS SUMMARY:")
    
    # Count unique files using each API
    api_usage_count = {}
    for usage in usages:
        for func_name in usage["api_calls"]:
            if func_name not in api_usage_count:
                api_usage_count[func_name] = set()
            api_usage_count[func_name].add(usage["file"])
    
    # Print usage counts
    for func_name, files in api_usage_count.items():
        print(f"  - {func_name}: used in {len(files)} files")
    
    print("\nAPI dependency analysis completed successfully. No issues found.")
    print(f"API signatures saved to: {API_SIGNATURE_FILE}")

if __name__ == "__main__":
    analyze_codebase()