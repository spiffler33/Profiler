import os
import json
import uuid
import logging
import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Union, Tuple

class GoalCategory:
    """
    Model for predefined goal categories with hierarchical structure.
    
    Categories are organized in a hierarchy aligned with financial security:
    1. Security (emergency fund and insurance goals)
    2. Essential (home, education, and debt goals)
    3. Retirement
    4. Lifestyle
    5. Legacy
    6. Custom
    """
    
    # Define standard hierarchy levels
    SECURITY = 1
    ESSENTIAL = 2
    RETIREMENT = 3
    LIFESTYLE = 4
    LEGACY = 5
    CUSTOM = 6
    
    def __init__(self, id: int = None, name: str = "", description: str = "", 
                order: int = 0, is_foundation: bool = False, hierarchy_level: int = None,
                parent_category_id: int = None):
        """
        Initialize a goal category.
        
        Args:
            id (int): Primary key (database ID)
            name (str): Category name (e.g., 'emergency_fund', 'retirement')
            description (str): Description of the goal category
            order (int): Display order for UI
            is_foundation (bool): Whether this is a foundation goal (emergency fund, insurance)
                                 Maintained for backward compatibility
            hierarchy_level (int): Priority level in financial hierarchy (1-6, lower = higher priority)
            parent_category_id (int): ID of parent category for subcategories, None for top-level categories
        """
        self.id = id
        self.name = name
        self.description = description
        self.order = order
        self.is_foundation = is_foundation
        
        # Map is_foundation to hierarchy_level for backward compatibility if hierarchy_level not provided
        if hierarchy_level is None:
            self.hierarchy_level = self.SECURITY if is_foundation else self.CUSTOM
        else:
            self.hierarchy_level = hierarchy_level
            
        self.parent_category_id = parent_category_id
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert category to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "is_foundation": self.is_foundation,
            "hierarchy_level": self.hierarchy_level,
            "parent_category_id": self.parent_category_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoalCategory':
        """
        Create a GoalCategory from a dictionary.
        
        Args:
            data (dict): Dictionary with category data
            
        Returns:
            GoalCategory: New instance
        """
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            order=data.get('order', 0),
            is_foundation=data.get('is_foundation', False),
            hierarchy_level=data.get('hierarchy_level'),
            parent_category_id=data.get('parent_category_id')
        )
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'GoalCategory':
        """
        Create a GoalCategory from a database row.
        
        Args:
            row (sqlite3.Row): Database row
            
        Returns:
            GoalCategory: New instance
        """
        # Handle both old and new database schemas for backward compatibility
        # Check if the columns exist in the row before accessing them
        hierarchy_level = None
        parent_category_id = None
        
        try:
            if 'hierarchy_level' in row.keys():
                hierarchy_level = row['hierarchy_level']
            if 'parent_category_id' in row.keys():
                parent_category_id = row['parent_category_id']
        except Exception:
            # For older versions of SQLite where keys() might not be available
            pass
        
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            order=row['order_index'],
            is_foundation=bool(row['is_foundation']),
            hierarchy_level=hierarchy_level,
            parent_category_id=parent_category_id
        )

class Goal:
    """
    Model for user financial goals.
    
    This class includes backward compatibility features:
    1. Property getters that map new field names to old ones
    2. Sensible defaults for all new fields 
    3. to_dict() method that can return legacy format
    4. from_legacy_dict() method to populate from old data structures
    """
    
    # Flexibility enum values
    FLEXIBILITY_FIXED = "fixed"
    FLEXIBILITY_SOMEWHAT = "somewhat_flexible"
    FLEXIBILITY_VERY = "very_flexible"
    
    # Importance enum values
    IMPORTANCE_HIGH = "high"
    IMPORTANCE_MEDIUM = "medium"
    IMPORTANCE_LOW = "low"
    
    # Legacy field names and their mappings (for backward compatibility)
    LEGACY_FIELD_MAPPINGS = {
        "priority": "importance",            # Old code used "priority" instead of "importance"
        "time_horizon": "timeframe",         # Old code used "time_horizon" instead of "timeframe"
        "target_value": "target_amount",     # Old code sometimes used "target_value" 
        "current_value": "current_amount",   # Old code sometimes used "current_value"
        "progress": "current_progress",      # Old code sometimes used "progress"
        "description": "notes",              # Old code sometimes used "description" instead of "notes"
        "profile_id": "user_profile_id"      # Old code sometimes used "profile_id"
    }
    
    def __init__(self, id: str = None, user_profile_id: str = "", category: str = "",
                title: str = "", target_amount: float = 0.0, timeframe: str = "",
                current_amount: float = 0.0, importance: str = "medium", 
                flexibility: str = "somewhat_flexible", notes: str = "",
                created_at: str = None, updated_at: str = None,
                # New fields
                current_progress: float = 0.0,
                priority_score: float = 0.0,
                additional_funding_sources: str = "",
                goal_success_probability: float = 0.0,
                adjustments_required: bool = False,
                funding_strategy: str = "",
                # Enhanced probability analysis fields
                simulation_data: str = None,
                scenarios: str = None,
                adjustments: str = None,
                last_simulation_time: str = None,
                simulation_parameters_json: str = None,
                # Additional probability fields
                probability_partial_success: float = 0.0,
                simulation_iterations: int = 1000,
                simulation_path_data: str = None,
                monthly_sip_recommended: float = 0.0,
                probability_metrics: str = None,
                success_threshold: float = 0.8):
        """
        Initialize a Goal.
        
        Args:
            id (str): Primary key (UUID)
            user_profile_id (str): Foreign key to UserProfile
            category (str): Goal category (e.g., 'emergency_fund', 'retirement')
            title (str): User-defined goal name
            target_amount (float): Target amount for the goal
            timeframe (str): Timeframe for achieving the goal
            current_amount (float): Current progress amount
            importance (str): Importance level ('high', 'medium', 'low')
            flexibility (str): Goal flexibility ('fixed', 'somewhat_flexible', 'very_flexible')
            notes (str): Additional notes about the goal
            created_at (str): Creation timestamp
            updated_at (str): Last update timestamp
            current_progress (float): Percentage of goal achieved (0.0 to 100.0)
            priority_score (float): Calculated score for automated goal prioritization
            additional_funding_sources (str): Other planned funding sources
            goal_success_probability (float): Calculated probability of achieving the goal (0.0 to 100.0)
            adjustments_required (bool): Flag to indicate if adjustments are needed
            funding_strategy (str): JSON or text storing the recommended funding approach
            simulation_data (str): JSON-serialized Monte Carlo simulation results, including SIP information
            scenarios (str): JSON-serialized alternative scenarios for the goal
            adjustments (str): JSON-serialized recommended adjustments to increase success probability
        """
        # Set core fields
        self.id = id or str(uuid.uuid4())
        self.user_profile_id = user_profile_id
        self.category = category
        self.title = title
        self.target_amount = target_amount
        self.timeframe = timeframe
        self.current_amount = current_amount
        self.importance = importance
        self.flexibility = flexibility
        self.notes = notes
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        
        # Set new fields with sensible defaults
        self.additional_funding_sources = additional_funding_sources
        self.goal_success_probability = goal_success_probability
        self.adjustments_required = adjustments_required
        self.funding_strategy = funding_strategy
        
        # Set enhanced probability analysis fields
        self.simulation_data = simulation_data
        self.scenarios = scenarios
        self.adjustments = adjustments
        self.last_simulation_time = last_simulation_time or datetime.now().isoformat()
        self.simulation_parameters_json = simulation_parameters_json
        
        # Set additional probability fields
        self.probability_partial_success = probability_partial_success
        self.simulation_iterations = simulation_iterations
        self.simulation_path_data = simulation_path_data
        self.monthly_sip_recommended = monthly_sip_recommended
        self.probability_metrics = probability_metrics
        self.success_threshold = success_threshold
        
        # Set current_progress if provided, otherwise calculate it
        if current_progress > 0.0:
            self.current_progress = current_progress
        elif self.target_amount > 0:
            self.current_progress = min(100.0, (self.current_amount / self.target_amount) * 100.0)
        else:
            self.current_progress = 0.0
        
        # Calculate priority score if not provided
        self.priority_score = priority_score
        if self.priority_score == 0.0:
            self.calculate_priority_score()
    
    # Property getters for backward compatibility with old field names
    
    @property
    def priority(self) -> str:
        """Legacy getter: Returns 'importance' for backward compatibility"""
        return self.importance

    @property
    def time_horizon(self) -> float:
        """
        Legacy getter: Approximates time_horizon in years from timeframe
        Returns years as a float, or 0.0 if timeframe can't be parsed
        """
        try:
            target_date = datetime.fromisoformat(self.timeframe.replace('Z', '+00:00'))
            today = datetime.now()
            days = (target_date - today).days
            return max(0.0, days / 365.0)  # Convert days to years, minimum 0
        except (ValueError, AttributeError, TypeError):
            # If timeframe is not a valid date string, return 0
            return 0.0
            
    @property
    def target_value(self) -> float:
        """Legacy getter: Returns 'target_amount' for backward compatibility"""
        return self.target_amount
    
    @property
    def current_value(self) -> float:
        """Legacy getter: Returns 'current_amount' for backward compatibility"""
        return self.current_amount
    
    @property
    def progress(self) -> float:
        """Legacy getter: Returns 'current_progress' for backward compatibility"""
        return self.current_progress
    
    @property
    def description(self) -> str:
        """Legacy getter: Returns 'notes' for backward compatibility"""
        return self.notes
    
    @property
    def profile_id(self) -> str:
        """Legacy getter: Returns 'user_profile_id' for backward compatibility"""
        return self.user_profile_id
    
    def to_dict(self, legacy_mode: bool = False) -> Dict[str, Any]:
        """
        Convert goal to dictionary for serialization.
        
        Args:
            legacy_mode (bool): If True, return only fields expected by legacy code
            
        Returns:
            dict: Dictionary representation
        """
        # Core fields (always included)
        result = {
            "id": self.id,
            "user_profile_id": self.user_profile_id,
            "category": self.category,
            "title": self.title,
            "target_amount": self.target_amount,
            "timeframe": self.timeframe,
            "current_amount": self.current_amount,
            "importance": self.importance,
            "flexibility": self.flexibility,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
        if not legacy_mode:
            # New fields (only included in modern mode)
            result.update({
                "current_progress": self.current_progress,
                "priority_score": self.priority_score,
                "additional_funding_sources": self.additional_funding_sources,
                "goal_success_probability": self.goal_success_probability,
                "adjustments_required": self.adjustments_required,
                "funding_strategy": self.funding_strategy,
                # Enhanced probability analysis fields
                "simulation_data": self.simulation_data,
                "scenarios": self.scenarios,
                "adjustments": self.adjustments,
                "last_simulation_time": self.last_simulation_time,
                "simulation_parameters_json": self.simulation_parameters_json,
                # Additional probability fields
                "probability_partial_success": self.probability_partial_success,
                "simulation_iterations": self.simulation_iterations,
                "simulation_path_data": self.simulation_path_data,
                "monthly_sip_recommended": self.monthly_sip_recommended,
                "probability_metrics": self.probability_metrics,
                "success_threshold": self.success_threshold
            })
        else:
            # Legacy fields (only included in legacy mode)
            # Convert timeframe to time_horizon for legacy compatibility
            time_horizon = self.time_horizon
            if time_horizon > 0:
                result["time_horizon"] = time_horizon
                
            # Add priority for legacy code that expects it
            result["priority"] = self.importance
            
            # If there are any additional legacy fields needed, add them here
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """
        Create a Goal from a dictionary.
        
        Args:
            data (dict): Dictionary with goal data
            
        Returns:
            Goal: New instance
        """
        return cls(
            id=data.get('id'),
            user_profile_id=data.get('user_profile_id', ''),
            category=data.get('category', ''),
            title=data.get('title', ''),
            target_amount=data.get('target_amount', 0.0),
            timeframe=data.get('timeframe', ''),
            current_amount=data.get('current_amount', 0.0),
            importance=data.get('importance', 'medium'),
            flexibility=data.get('flexibility', 'somewhat_flexible'),
            notes=data.get('notes', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            # New fields with default values for backward compatibility
            current_progress=data.get('current_progress', 0.0),
            priority_score=data.get('priority_score', 0.0),
            additional_funding_sources=data.get('additional_funding_sources', ''),
            goal_success_probability=data.get('goal_success_probability', 0.0),
            adjustments_required=data.get('adjustments_required', False),
            funding_strategy=data.get('funding_strategy', ''),
            # Enhanced probability analysis fields
            simulation_data=data.get('simulation_data'),
            scenarios=data.get('scenarios'),
            adjustments=data.get('adjustments'),
            last_simulation_time=data.get('last_simulation_time'),
            simulation_parameters_json=data.get('simulation_parameters_json'),
            # Additional probability fields
            probability_partial_success=data.get('probability_partial_success', 0.0),
            simulation_iterations=data.get('simulation_iterations', 1000),
            simulation_path_data=data.get('simulation_path_data'),
            monthly_sip_recommended=data.get('monthly_sip_recommended', 0.0),
            probability_metrics=data.get('probability_metrics'),
            success_threshold=data.get('success_threshold', 0.8)
        )
    
    @classmethod
    def from_legacy_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """
        Create a Goal from a legacy dictionary format.
        Maps old field names to new field names and provides appropriate defaults.
        
        Args:
            data (dict): Dictionary with legacy goal data
            
        Returns:
            Goal: New instance with properly mapped fields
        """
        # Map of legacy fields to new fields
        field_mapping = cls.LEGACY_FIELD_MAPPINGS
        mapped_data = {}
        
        # Process core fields first with appropriate mappings
        mapped_data['id'] = data.get('id')
        
        # Map user_profile_id from profile_id if present
        mapped_data['user_profile_id'] = data.get('user_profile_id', 
                                                data.get('profile_id', ''))
        
        mapped_data['category'] = data.get('category', '')
        mapped_data['title'] = data.get('title', '')
        
        # Map target_amount from either target_amount or target_value
        mapped_data['target_amount'] = data.get('target_amount', 
                                             data.get('target_value', 0.0))
        
        # Handle timeframe/time_horizon mapping
        if 'timeframe' in data:
            mapped_data['timeframe'] = data['timeframe']
        elif 'time_horizon' in data and isinstance(data['time_horizon'], (int, float)):
            # Convert time_horizon (years) to a timeframe (date string)
            years = float(data['time_horizon'])
            if years > 0:
                target_date = datetime.now() + timedelta(days=int(years * 365))
                mapped_data['timeframe'] = target_date.isoformat()
            else:
                mapped_data['timeframe'] = ''
        else:
            mapped_data['timeframe'] = ''
        
        # Map current_amount from either current_amount or current_value
        mapped_data['current_amount'] = data.get('current_amount', 
                                              data.get('current_value', 0.0))
        
        # Map importance from either importance or priority
        mapped_data['importance'] = data.get('importance', 
                                          data.get('priority', 'medium'))
        
        mapped_data['flexibility'] = data.get('flexibility', 'somewhat_flexible')
        
        # Map notes from either notes or description
        mapped_data['notes'] = data.get('notes', 
                                      data.get('description', ''))
        
        mapped_data['created_at'] = data.get('created_at')
        mapped_data['updated_at'] = data.get('updated_at')
        
        # Handle new fields with appropriate defaults
        progress_value = data.get('current_progress', data.get('progress', None))
        if progress_value is not None:
            mapped_data['current_progress'] = progress_value
        # Other fields don't need to be explicitly set as the constructor will use defaults
        
        if 'priority_score' in data:
            mapped_data['priority_score'] = data['priority_score']
            
        if 'additional_funding_sources' in data:
            mapped_data['additional_funding_sources'] = data['additional_funding_sources']
            
        if 'goal_success_probability' in data:
            mapped_data['goal_success_probability'] = data['goal_success_probability']
            
        if 'adjustments_required' in data:
            mapped_data['adjustments_required'] = data['adjustments_required']
            
        if 'funding_strategy' in data:
            mapped_data['funding_strategy'] = data['funding_strategy']
        
        # Create new Goal instance with mapped data
        return cls(**mapped_data)
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Goal':
        """
        Create a Goal from a database row.
        
        Args:
            row (sqlite3.Row): Database row
            
        Returns:
            Goal: New instance
        """
        # Start with required core fields
        init_args = {
            'id': row['id'],
            'user_profile_id': row['user_profile_id'],
            'category': row['category'],
            'title': row['title'],
            'target_amount': row['target_amount'],
            'timeframe': row['timeframe'],
            'current_amount': row['current_amount'],
            'importance': row['importance'],
            'flexibility': row['flexibility'],
            'notes': row['notes'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }
        
        # Handle both old and new database schemas for backward compatibility
        # Add new fields if they exist, otherwise use defaults
        try:
            # Get all column names from the row if possible
            if hasattr(row, 'keys'):
                column_names = row.keys()
            else:
                # Fall back to known enhanced columns
                column_names = [
                    'current_progress', 'priority_score', 'additional_funding_sources',
                    'goal_success_probability', 'adjustments_required', 'funding_strategy',
                    'simulation_data', 'scenarios', 'adjustments'
                ]
            
            # Check if each new field exists and add it to init_args if it does
            if 'current_progress' in column_names:
                init_args['current_progress'] = row['current_progress']
                
            if 'priority_score' in column_names:
                init_args['priority_score'] = row['priority_score']
                
            if 'additional_funding_sources' in column_names:
                init_args['additional_funding_sources'] = row['additional_funding_sources']
                
            if 'goal_success_probability' in column_names:
                init_args['goal_success_probability'] = row['goal_success_probability']
                
            if 'adjustments_required' in column_names:
                init_args['adjustments_required'] = bool(row['adjustments_required'])
                
            if 'funding_strategy' in column_names:
                init_args['funding_strategy'] = row['funding_strategy']
            
            # Enhanced probability analysis fields
            if 'simulation_data' in column_names:
                init_args['simulation_data'] = row['simulation_data']
                
            if 'scenarios' in column_names:
                init_args['scenarios'] = row['scenarios']
                
            if 'adjustments' in column_names:
                init_args['adjustments'] = row['adjustments']
                
            if 'last_simulation_time' in column_names:
                init_args['last_simulation_time'] = row['last_simulation_time']
                
            if 'simulation_parameters_json' in column_names:
                init_args['simulation_parameters_json'] = row['simulation_parameters_json']
                
            # Additional probability fields
            if 'probability_partial_success' in column_names:
                init_args['probability_partial_success'] = row['probability_partial_success']
                
            if 'simulation_iterations' in column_names:
                init_args['simulation_iterations'] = row['simulation_iterations']
                
            if 'simulation_path_data' in column_names:
                init_args['simulation_path_data'] = row['simulation_path_data']
                
            if 'monthly_sip_recommended' in column_names:
                init_args['monthly_sip_recommended'] = row['monthly_sip_recommended']
                
            if 'probability_metrics' in column_names:
                init_args['probability_metrics'] = row['probability_metrics']
                
            if 'success_threshold' in column_names:
                init_args['success_threshold'] = row['success_threshold']
                
            # Support for legacy fields: check if any legacy fields are present
            # and use them if the modern field is not available
            for legacy_field, modern_field in cls.LEGACY_FIELD_MAPPINGS.items():
                if modern_field not in init_args and legacy_field in column_names:
                    # Special case for time_horizon (needs conversion)
                    if legacy_field == 'time_horizon' and row[legacy_field]:
                        years = float(row[legacy_field])
                        if years > 0:
                            target_date = datetime.now() + timedelta(days=int(years * 365))
                            init_args['timeframe'] = target_date.isoformat()
                    else:
                        # Direct mapping for other fields
                        init_args[modern_field] = row[legacy_field]
                    
        except Exception as e:
            # If there's any error, just use the required fields
            # This ensures backward compatibility
            logging.warning(f"Error processing enhanced goal fields: {str(e)}")
            
        # Create and return the Goal instance
        return cls(**init_args)
    
    # Helper methods for enhanced probability fields
    
    def get_simulation_data(self) -> Dict[str, Any]:
        """
        Get parsed simulation data.
        
        Returns:
            dict: Parsed simulation data or empty dict if not available
        """
        if not self.simulation_data:
            return {}
        
        try:
            return json.loads(self.simulation_data)
        except (json.JSONDecodeError, TypeError):
            return {}
            
    def set_simulation_data(self, data: Dict[str, Any]) -> None:
        """
        Set simulation data.
        
        Args:
            data: Dictionary with simulation data
        """
        self.simulation_data = json.dumps(data) if data else None
        
    def get_scenarios(self) -> Dict[str, Any]:
        """
        Get parsed scenarios.
        
        Returns:
            dict: Parsed scenarios or empty dict if not available
        """
        if not self.scenarios:
            return {}
        
        try:
            return json.loads(self.scenarios)
        except (json.JSONDecodeError, TypeError):
            return {}
            
    def set_scenarios(self, data: Dict[str, Any]) -> None:
        """
        Set scenarios.
        
        Args:
            data: Dictionary with scenarios
        """
        self.scenarios = json.dumps(data) if data else None
        
    def get_adjustments(self) -> Dict[str, Any]:
        """
        Get parsed adjustments.
        
        Returns:
            dict: Parsed adjustments or empty dict if not available
        """
        if not self.adjustments:
            return {}
        
        try:
            return json.loads(self.adjustments)
        except (json.JSONDecodeError, TypeError):
            return {}
            
    def set_adjustments(self, data: Dict[str, Any]) -> None:
        """
        Set adjustments.
        
        Args:
            data: Dictionary with adjustments
        """
        self.adjustments = json.dumps(data) if data else None
        
    def get_simulation_parameters(self) -> Dict[str, Any]:
        """
        Get parsed simulation parameters.
        
        Returns:
            dict: Parsed simulation parameters or empty dict if not available
        """
        if not self.simulation_parameters_json:
            return {}
        
        try:
            return json.loads(self.simulation_parameters_json)
        except (json.JSONDecodeError, TypeError):
            return {}
            
    def set_simulation_parameters(self, data: Dict[str, Any]) -> None:
        """
        Set simulation parameters.
        
        Args:
            data: Dictionary with simulation parameters
        """
        self.simulation_parameters_json = json.dumps(data) if data else None
        
    def update_simulation_time(self) -> None:
        """
        Update the last simulation time to the current timestamp.
        """
        self.last_simulation_time = datetime.now().isoformat()
        
    def get_probability_metrics(self) -> Dict[str, Any]:
        """
        Get parsed probability metrics.
        
        Returns:
            dict: Parsed probability metrics or empty dict if not available
        """
        if not self.probability_metrics:
            return {}
        
        try:
            return json.loads(self.probability_metrics)
        except (json.JSONDecodeError, TypeError):
            return {}
            
    def set_probability_metrics(self, data: Dict[str, Any]) -> None:
        """
        Set probability metrics.
        
        Args:
            data: Dictionary with probability metrics
        """
        self.probability_metrics = json.dumps(data) if data else None
        
    def get_simulation_paths(self) -> Dict[str, Any]:
        """
        Get parsed simulation path data for visualization.
        
        Returns:
            dict: Parsed simulation paths or empty dict if not available
        """
        if not self.simulation_path_data:
            return {}
        
        try:
            return json.loads(self.simulation_path_data)
        except (json.JSONDecodeError, TypeError):
            return {}
            
    def set_simulation_paths(self, data: Dict[str, Any]) -> None:
        """
        Set simulation path data.
        
        Args:
            data: Dictionary with simulation paths
        """
        self.simulation_path_data = json.dumps(data) if data else None
        
    def get_sip_details(self) -> Dict[str, Any]:
        """
        Get SIP (Systematic Investment Plan) details from simulation data.
        Convenience method for the Indian financial context.
        
        Returns:
            dict: SIP details or empty dict if not available
        """
        simulation_data = self.get_simulation_data()
        if not simulation_data or 'investment_options' not in simulation_data:
            return {}
            
        return simulation_data.get('investment_options', {}).get('sip', {})
        
    def calculate_priority_score(self) -> float:
        """
        Calculate a priority score based on importance, timeframe, and flexibility.
        Higher score means higher priority.
        
        Returns:
            float: Priority score between 0 and 100
        """
        # Base score from importance (0-50 points)
        importance_scores = {
            self.IMPORTANCE_HIGH: 50,
            self.IMPORTANCE_MEDIUM: 30,
            self.IMPORTANCE_LOW: 10
        }
        score = importance_scores.get(self.importance, 30)
        
        # Add points for urgency based on timeframe (0-30 points)
        try:
            # Try to parse timeframe as a date
            target_date = datetime.fromisoformat(self.timeframe.replace('Z', '+00:00'))
            today = datetime.now()
            days_remaining = (target_date - today).days
            
            if days_remaining <= 0:
                # Overdue goals get maximum urgency
                urgency_points = 30
            elif days_remaining <= 30:
                # Within a month (25-30 points)
                urgency_points = 25 + (30 - days_remaining) / 30 * 5
            elif days_remaining <= 365:
                # Within a year (15-25 points)
                urgency_points = 15 + (365 - days_remaining) / 365 * 10
            elif days_remaining <= 1825:  # 5 years
                # Within 5 years (5-15 points)
                urgency_points = 5 + (1825 - days_remaining) / 1825 * 10
            else:
                # Beyond 5 years (0-5 points)
                urgency_points = max(0, 5 - (days_remaining - 1825) / 1825)
        except (ValueError, TypeError):
            # Default urgency if timeframe isn't a parseable date
            urgency_points = 15
            
        score += urgency_points
        
        # Add points for flexibility (0-20 points)
        flexibility_scores = {
            self.FLEXIBILITY_FIXED: 20,          # Fixed goals get higher priority
            self.FLEXIBILITY_SOMEWHAT: 10,       # Somewhat flexible goals get medium priority
            self.FLEXIBILITY_VERY: 5             # Very flexible goals get lower priority
        }
        score += flexibility_scores.get(self.flexibility, 10)
        
        # Adjust score based on progress (0-100%)
        if self.target_amount > 0 and self.current_amount > 0:
            progress_percent = min(100, (self.current_amount / self.target_amount) * 100)
            
            # Apply a modest bonus for partially completed goals (to avoid abandonment)
            # Maximum bonus of 5 points at 50% progress, tapering off at 0% and 100%
            progress_bonus = 5 * (1 - abs(0.5 - progress_percent / 100) * 2)
            score += progress_bonus
        
        # Round to 2 decimal places and store
        self.priority_score = round(score, 2)
        return self.priority_score

class GoalManager:
    """
    Manager for handling goal operations.
    """
    
    # Define standard hierarchy levels - duplicated here for easy reference within manager
    SECURITY_LEVEL = 1
    ESSENTIAL_LEVEL = 2
    RETIREMENT_LEVEL = 3
    LIFESTYLE_LEVEL = 4
    LEGACY_LEVEL = 5
    CUSTOM_LEVEL = 6
    
    # Predefined category definitions
    PREDEFINED_CATEGORIES = [
        {
            "name": "Security", 
            "description": "Foundation level for emergency fund and insurance goals",
            "order": 1,
            "is_foundation": True,
            "hierarchy_level": SECURITY_LEVEL,
            "parent_category_id": None
        },
        {
            "name": "Essential", 
            "description": "Basic needs like home, education, and debt goals",
            "order": 2,
            "is_foundation": False,
            "hierarchy_level": ESSENTIAL_LEVEL,
            "parent_category_id": None
        },
        {
            "name": "Retirement", 
            "description": "Long-term retirement planning goals",
            "order": 3,
            "is_foundation": False,
            "hierarchy_level": RETIREMENT_LEVEL,
            "parent_category_id": None
        },
        {
            "name": "Lifestyle", 
            "description": "Quality of life goals like travel, vehicles, etc.",
            "order": 4,
            "is_foundation": False,
            "hierarchy_level": LIFESTYLE_LEVEL,
            "parent_category_id": None
        },
        {
            "name": "Legacy", 
            "description": "Estate planning, charitable giving, and impact goals",
            "order": 5,
            "is_foundation": False,
            "hierarchy_level": LEGACY_LEVEL,
            "parent_category_id": None
        },
        {
            "name": "Custom", 
            "description": "User-defined goals that don't fit other categories",
            "order": 6,
            "is_foundation": False,
            "hierarchy_level": CUSTOM_LEVEL,
            "parent_category_id": None
        }
    ]
    
    # Subcategory mapping for pre-existing categories
    # Ensures consistency with goal types used throughout the application
    SUBCATEGORY_MAPPING = {
        "emergency_fund": {"parent": "Security", "description": "Funds for unexpected expenses"},
        "health_insurance": {"parent": "Security", "description": "Medical and health coverage"},
        "life_insurance": {"parent": "Security", "description": "Protection for dependents"},
        "home_purchase": {"parent": "Essential", "description": "Primary residence acquisition"},
        "education": {"parent": "Essential", "description": "Education and skill development"},
        "debt_repayment": {"parent": "Essential", "description": "Paying off outstanding debts"},
        "retirement": {"parent": "Retirement", "description": "Long-term savings for retirement years"},
        "early_retirement": {"parent": "Retirement", "description": "Achieving financial independence before traditional retirement age"},
        "wedding": {"parent": "Lifestyle", "description": "Saving for wedding expenses"},
        "travel": {"parent": "Lifestyle", "description": "Vacation and travel experiences"},
        "vehicle": {"parent": "Lifestyle", "description": "Automobile or transportation purchases"},
        "home_improvement": {"parent": "Lifestyle", "description": "Enhancing existing property"},
        "legacy_planning": {"parent": "Legacy", "description": "Planning for wealth transfer"},
        "charitable_giving": {"parent": "Legacy", "description": "Donations and philanthropy"},
        "tax_optimization": {"parent": "Security", "description": "Investments for tax efficiency"}
    }
    
    def __init__(self, db_path="/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles.db"):
        """
        Initialize the GoalManager.
        
        Args:
            db_path (str): Path to SQLite database
        """
        self.db_path = db_path
        logging.basicConfig(level=logging.INFO)
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for getting a database connection.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable dictionary rows
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def get_all_categories(self) -> List[GoalCategory]:
        """
        Get all goal categories.
        
        Returns:
            list: List of GoalCategory objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Try to query with new schema fields, fall back to old schema if needed
                try:
                    cursor.execute("""
                        SELECT id, name, description, order_index, is_foundation,
                               hierarchy_level, parent_category_id
                        FROM goal_categories
                        ORDER BY hierarchy_level, order_index
                    """)
                except sqlite3.OperationalError:
                    # Fall back to old schema if new columns don't exist
                    cursor.execute("""
                        SELECT id, name, description, order_index, is_foundation
                        FROM goal_categories
                        ORDER BY order_index
                    """)
                
                rows = cursor.fetchall()
                return [GoalCategory.from_row(row) for row in rows]
                
        except Exception as e:
            logging.error(f"Failed to get goal categories: {str(e)}")
            return []
    
    def get_categories_by_hierarchy_level(self, level: int) -> List[GoalCategory]:
        """
        Get goal categories by hierarchy level.
        
        Args:
            level (int): Hierarchy level (1-6)
            
        Returns:
            list: List of GoalCategory objects at the specified hierarchy level
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Try to query with hierarchy_level column
                    cursor.execute("""
                        SELECT id, name, description, order_index, is_foundation,
                               hierarchy_level, parent_category_id
                        FROM goal_categories
                        WHERE hierarchy_level = ?
                        ORDER BY order_index
                    """, (level,))
                except sqlite3.OperationalError:
                    # Fall back to is_foundation for backward compatibility
                    is_foundation = (level == GoalCategory.SECURITY)
                    cursor.execute("""
                        SELECT id, name, description, order_index, is_foundation
                        FROM goal_categories
                        WHERE is_foundation = ?
                        ORDER BY order_index
                    """, (is_foundation,))
                
                rows = cursor.fetchall()
                return [GoalCategory.from_row(row) for row in rows]
                
        except Exception as e:
            logging.error(f"Failed to get goal categories for level {level}: {str(e)}")
            return []
    
    def initialize_predefined_categories(self, force_update=False) -> bool:
        """
        Initialize the database with predefined hierarchical goal categories.
        If categories already exist, they are preserved unless force_update is True.
        
        This method should be run after migrating the database schema to include 
        hierarchy_level and parent_category_id columns.
        
        Args:
            force_update (bool): If True, update existing categories to match predefined values
            
        Returns:
            bool: True if initialization succeeded, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if the hierarchy columns exist
                cursor.execute("PRAGMA table_info(goal_categories)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'hierarchy_level' not in columns or 'parent_category_id' not in columns:
                    logging.error("Database schema is missing hierarchy columns. Run the migration script first.")
                    logging.error("Execute: python migrate_goal_categories.py")
                    return False
                
                # Get existing categories
                cursor.execute("SELECT id, name FROM goal_categories")
                existing_categories = {row['name']: row['id'] for row in cursor.fetchall()}
                
                # Insert main categories if they don't exist
                category_ids = {}
                
                for category in self.PREDEFINED_CATEGORIES:
                    name = category['name']
                    if name in existing_categories and not force_update:
                        # Category exists and we're not forcing an update
                        category_ids[name] = existing_categories[name]
                        logging.info(f"Category '{name}' already exists with ID {existing_categories[name]}")
                    else:
                        if name in existing_categories:
                            # Update existing category
                            cursor.execute("""
                                UPDATE goal_categories
                                SET description = ?, order_index = ?, is_foundation = ?,
                                    hierarchy_level = ?, parent_category_id = ?
                                WHERE name = ?
                            """, (
                                category['description'],
                                category['order'],
                                category['is_foundation'],
                                category['hierarchy_level'],
                                category['parent_category_id'],
                                name
                            ))
                            category_ids[name] = existing_categories[name]
                            logging.info(f"Updated existing category '{name}' with ID {existing_categories[name]}")
                        else:
                            # Insert new category
                            cursor.execute("""
                                INSERT INTO goal_categories
                                (name, description, order_index, is_foundation, hierarchy_level, parent_category_id)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                name,
                                category['description'],
                                category['order'],
                                category['is_foundation'],
                                category['hierarchy_level'],
                                category['parent_category_id']
                            ))
                            category_id = cursor.lastrowid
                            category_ids[name] = category_id
                            logging.info(f"Created new category '{name}' with ID {category_id}")
                
                # Now handle existing subcategories - map them to the appropriate parent categories
                for subcategory_name, subcategory_info in self.SUBCATEGORY_MAPPING.items():
                    parent_name = subcategory_info['parent']
                    
                    if subcategory_name in existing_categories and parent_name in category_ids:
                        parent_id = category_ids[parent_name]
                        subcategory_id = existing_categories[subcategory_name]
                        
                        # Get parent's hierarchy level
                        cursor.execute("SELECT hierarchy_level FROM goal_categories WHERE id = ?", (parent_id,))
                        parent_level = cursor.fetchone()['hierarchy_level']
                        
                        # Update the subcategory to link to the parent and inherit its hierarchy level
                        cursor.execute("""
                            UPDATE goal_categories
                            SET hierarchy_level = ?, parent_category_id = ?, description = ?
                            WHERE id = ?
                        """, (
                            parent_level,  # Inherit parent's hierarchy level
                            parent_id,     # Link to parent
                            subcategory_info['description'],  # Update description
                            subcategory_id
                        ))
                        logging.info(f"Mapped subcategory '{subcategory_name}' to parent '{parent_name}'")
                
                conn.commit()
                logging.info("Goal categories initialization completed successfully")
                return True
                
        except Exception as e:
            logging.error(f"Failed to initialize goal categories: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def get_category_by_name(self, name: str) -> Optional[GoalCategory]:
        """
        Get a goal category by name.
        
        Args:
            name (str): Category name
            
        Returns:
            GoalCategory: Category object or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Try to query with new schema fields
                    cursor.execute("""
                        SELECT id, name, description, order_index, is_foundation,
                               hierarchy_level, parent_category_id
                        FROM goal_categories
                        WHERE name = ?
                    """, (name,))
                except sqlite3.OperationalError:
                    # Fall back to old schema if new columns don't exist
                    cursor.execute("""
                        SELECT id, name, description, order_index, is_foundation
                        FROM goal_categories
                        WHERE name = ?
                    """, (name,))
                
                row = cursor.fetchone()
                return GoalCategory.from_row(row) if row else None
                
        except Exception as e:
            logging.error(f"Failed to get goal category '{name}': {str(e)}")
            return None
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """
        Get a goal by ID.
        
        Args:
            goal_id (str): Goal ID
            
        Returns:
            Goal: Goal object or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM goals WHERE id = ?
                """, (goal_id,))
                
                row = cursor.fetchone()
                return Goal.from_row(row) if row else None
                
        except Exception as e:
            logging.error(f"Failed to get goal {goal_id}: {str(e)}")
            return None
    
    def get_profile_goals(self, profile_id: str) -> List[Goal]:
        """
        Get all goals for a profile.
        
        Args:
            profile_id (str): Profile ID
            
        Returns:
            list: List of Goal objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM goals 
                    WHERE user_profile_id = ?
                    ORDER BY category, created_at
                """, (profile_id,))
                
                rows = cursor.fetchall()
                return [Goal.from_row(row) for row in rows]
                
        except Exception as e:
            logging.error(f"Failed to get goals for profile {profile_id}: {str(e)}")
            return []
    
    def get_all_goals(self) -> List[Goal]:
        """
        Get all goals from all profiles.
        
        Returns:
            list: List of all Goal objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM goals 
                    ORDER BY user_profile_id, category, created_at
                """)
                
                rows = cursor.fetchall()
                return [Goal.from_row(row) for row in rows]
                
        except Exception as e:
            logging.error(f"Failed to get all goals: {str(e)}")
            return []
    
    def get_goals_by_priority(self, profile_id: str = None) -> List[Goal]:
        """
        Get goals sorted by priority score (highest to lowest).
        
        Args:
            profile_id (str, optional): Filter goals by profile ID. If None, returns goals from all profiles.
            
        Returns:
            list: List of Goal objects sorted by priority
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if the priority_score column exists
                cursor.execute("PRAGMA table_info(goals)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'priority_score' in columns:
                    # Use priority_score for sorting if it exists
                    if profile_id:
                        cursor.execute("""
                            SELECT * FROM goals 
                            WHERE user_profile_id = ?
                            ORDER BY priority_score DESC, importance DESC, timeframe ASC
                        """, (profile_id,))
                    else:
                        cursor.execute("""
                            SELECT * FROM goals 
                            ORDER BY priority_score DESC, importance DESC, timeframe ASC
                        """)
                else:
                    # Fall back to importance and timeframe sorting if priority_score doesn't exist
                    if profile_id:
                        cursor.execute("""
                            SELECT * FROM goals 
                            WHERE user_profile_id = ?
                            ORDER BY CASE 
                                WHEN importance = 'high' THEN 1
                                WHEN importance = 'medium' THEN 2
                                ELSE 3
                            END,
                            timeframe ASC
                        """, (profile_id,))
                    else:
                        cursor.execute("""
                            SELECT * FROM goals 
                            ORDER BY CASE 
                                WHEN importance = 'high' THEN 1
                                WHEN importance = 'medium' THEN 2
                                ELSE 3
                            END,
                            timeframe ASC
                        """)
                
                rows = cursor.fetchall()
                goals = [Goal.from_row(row) for row in rows]
                
                # Recalculate priority scores just in case
                for goal in goals:
                    if goal.priority_score == 0:
                        goal.calculate_priority_score()
                
                # Return sorted by priority score (as a backup in case the DB sorting failed)
                return sorted(goals, key=lambda g: g.priority_score, reverse=True)
                
        except Exception as e:
            profile_msg = f" for profile {profile_id}" if profile_id else ""
            logging.error(f"Failed to get goals by priority{profile_msg}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return []
    
    def create_goal(self, goal: Goal) -> Optional[Goal]:
        """
        Create a new goal.
        
        Args:
            goal (Goal): Goal to create
            
        Returns:
            Goal: Created goal with ID or None if failed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Set timestamps
                current_time = datetime.now().isoformat()
                if not goal.created_at:
                    goal.created_at = current_time
                goal.updated_at = current_time
                
                # Calculate current_progress if not set
                if goal.current_progress == 0.0 and goal.target_amount > 0:
                    goal.current_progress = min(100.0, (goal.current_amount / goal.target_amount) * 100.0)
                
                # Calculate priority score if not set
                if goal.priority_score == 0.0:
                    goal.calculate_priority_score()
                
                # Check if the new columns exist in the goals table
                cursor.execute("PRAGMA table_info(goals)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'current_progress' in columns:
                    # Check if enhanced probability fields exist
                    has_enhanced_fields = 'simulation_data' in columns
                    
                    if has_enhanced_fields:
                        # Enhanced schema with all fields including probability analysis
                        cursor.execute("""
                            INSERT INTO goals (
                                id, user_profile_id, category, title, 
                                target_amount, timeframe, current_amount,
                                importance, flexibility, notes, 
                                created_at, updated_at,
                                current_progress, priority_score, 
                                additional_funding_sources, goal_success_probability,
                                adjustments_required, funding_strategy,
                                simulation_data, scenarios, adjustments,
                                last_simulation_time, simulation_parameters_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            goal.id, goal.user_profile_id, goal.category, goal.title,
                            goal.target_amount, goal.timeframe, goal.current_amount,
                            goal.importance, goal.flexibility, goal.notes,
                            goal.created_at, goal.updated_at,
                            goal.current_progress, goal.priority_score, 
                            goal.additional_funding_sources, goal.goal_success_probability,
                            1 if goal.adjustments_required else 0, goal.funding_strategy,
                            goal.simulation_data, goal.scenarios, goal.adjustments,
                            goal.last_simulation_time, goal.simulation_parameters_json
                        ))
                    else:
                        # New schema with basic fields but without enhanced probability fields
                        cursor.execute("""
                            INSERT INTO goals (
                                id, user_profile_id, category, title, 
                                target_amount, timeframe, current_amount,
                                importance, flexibility, notes, 
                                created_at, updated_at,
                                current_progress, priority_score, 
                                additional_funding_sources, goal_success_probability,
                                adjustments_required, funding_strategy,
                                last_simulation_time, simulation_parameters_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            goal.id, goal.user_profile_id, goal.category, goal.title,
                            goal.target_amount, goal.timeframe, goal.current_amount,
                            goal.importance, goal.flexibility, goal.notes,
                            goal.created_at, goal.updated_at,
                            goal.current_progress, goal.priority_score, 
                            goal.additional_funding_sources, goal.goal_success_probability,
                            1 if goal.adjustments_required else 0, goal.funding_strategy,
                            goal.last_simulation_time, goal.simulation_parameters_json
                        ))
                else:
                    # Old schema without new fields
                    cursor.execute("""
                        INSERT INTO goals (
                            id, user_profile_id, category, title, 
                            target_amount, timeframe, current_amount,
                            importance, flexibility, notes, 
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        goal.id, goal.user_profile_id, goal.category, goal.title,
                        goal.target_amount, goal.timeframe, goal.current_amount,
                        goal.importance, goal.flexibility, goal.notes,
                        goal.created_at, goal.updated_at
                    ))
                
                conn.commit()
                logging.info(f"Created goal {goal.id} for profile {goal.user_profile_id}")
                return goal
                
        except Exception as e:
            logging.error(f"Failed to create goal: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return None
    
    def update_goal(self, goal: Goal) -> Optional[Goal]:
        """
        Update an existing goal.
        
        Args:
            goal (Goal): Goal to update
            
        Returns:
            Goal: Updated goal or None if failed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Update timestamp
                goal.updated_at = datetime.now().isoformat()
                
                # Calculate current_progress if target_amount is available
                if goal.target_amount > 0:
                    goal.current_progress = min(100.0, (goal.current_amount / goal.target_amount) * 100.0)
                
                # Calculate priority score
                goal.calculate_priority_score()
                
                # Check if the new columns exist
                cursor.execute("PRAGMA table_info(goals)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'current_progress' in columns:
                    # Check if enhanced probability fields exist
                    has_enhanced_fields = 'simulation_data' in columns
                    
                    if has_enhanced_fields:
                        # Enhanced schema with all fields including probability analysis
                        cursor.execute("""
                            UPDATE goals SET
                                category = ?, 
                                title = ?,
                                target_amount = ?,
                                timeframe = ?,
                                current_amount = ?,
                                importance = ?,
                                flexibility = ?,
                                notes = ?,
                                updated_at = ?,
                                current_progress = ?,
                                priority_score = ?,
                                additional_funding_sources = ?,
                                goal_success_probability = ?,
                                adjustments_required = ?,
                                funding_strategy = ?,
                                simulation_data = ?,
                                scenarios = ?,
                                adjustments = ?,
                                last_simulation_time = ?,
                                simulation_parameters_json = ?
                            WHERE id = ?
                        """, (
                            goal.category, goal.title, 
                            goal.target_amount, goal.timeframe, goal.current_amount,
                            goal.importance, goal.flexibility, goal.notes,
                            goal.updated_at,
                            goal.current_progress, goal.priority_score, 
                            goal.additional_funding_sources, goal.goal_success_probability,
                            1 if goal.adjustments_required else 0, goal.funding_strategy,
                            goal.simulation_data, goal.scenarios, goal.adjustments,
                            goal.last_simulation_time, goal.simulation_parameters_json,
                            goal.id
                        ))
                    else:
                        # New schema with basic fields but without enhanced probability fields
                        cursor.execute("""
                            UPDATE goals SET
                                category = ?, 
                                title = ?,
                                target_amount = ?,
                                timeframe = ?,
                                current_amount = ?,
                                importance = ?,
                                flexibility = ?,
                                notes = ?,
                                updated_at = ?,
                                current_progress = ?,
                                priority_score = ?,
                                additional_funding_sources = ?,
                                goal_success_probability = ?,
                                adjustments_required = ?,
                                funding_strategy = ?,
                                last_simulation_time = ?,
                                simulation_parameters_json = ?
                            WHERE id = ?
                        """, (
                            goal.category, goal.title, 
                            goal.target_amount, goal.timeframe, goal.current_amount,
                            goal.importance, goal.flexibility, goal.notes,
                            goal.updated_at,
                            goal.current_progress, goal.priority_score, 
                            goal.additional_funding_sources, goal.goal_success_probability,
                            1 if goal.adjustments_required else 0, goal.funding_strategy,
                            goal.last_simulation_time, goal.simulation_parameters_json,
                            goal.id
                        ))
                else:
                    # Old schema without new fields
                    cursor.execute("""
                        UPDATE goals SET
                            category = ?, 
                            title = ?,
                            target_amount = ?,
                            timeframe = ?,
                            current_amount = ?,
                            importance = ?,
                            flexibility = ?,
                            notes = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        goal.category, goal.title, 
                        goal.target_amount, goal.timeframe, goal.current_amount,
                        goal.importance, goal.flexibility, goal.notes,
                        goal.updated_at, goal.id
                    ))
                
                conn.commit()
                logging.info(f"Updated goal {goal.id}")
                return goal
                
        except Exception as e:
            logging.error(f"Failed to update goal {goal.id}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return None
    
    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a goal.
        
        Args:
            goal_id (str): Goal ID to delete
            
        Returns:
            bool: Success status
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                
                conn.commit()
                logging.info(f"Deleted goal {goal_id}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to delete goal {goal_id}: {str(e)}")
            return False