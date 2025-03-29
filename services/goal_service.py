#!/usr/bin/env python3
"""
Goal Service Module

This service layer handles operations related to financial goals, providing an interface
between the data models and the application. It manages compatibility between simple and 
enhanced goal structures, handles goal-specific calculations and operations, and provides
specialized handlers for different goal categories.

This service ensures backward compatibility with legacy components while leveraging
the enhanced goal functionality.
"""

import logging
import json
import uuid
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from datetime import datetime

# Import models
from models.goal_models import Goal, GoalCategory, GoalManager
from models.goal_calculator import GoalCalculator

# Import Monte Carlo optimization components
from models.monte_carlo.cache import cached_simulation, invalidate_cache, get_cache_stats
from models.monte_carlo.array_fix import safe_array_compare, to_scalar, safe_median
from models.monte_carlo.parallel import run_parallel_monte_carlo

# Import probability analysis components
from models.goal_probability import GoalProbabilityAnalyzer, ProbabilityResult

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoalService:
    """
    Service layer for goal-related operations.
    
    This service provides an interface for creating, retrieving, updating, and analyzing
    financial goals while handling compatibility between simple and enhanced parameters.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the goal service with necessary dependencies.
        
        Args:
            db_path (str, optional): Path to the database. If None, uses default.
        """
        # Initialize core dependencies
        self.goal_manager = GoalManager(db_path) if db_path else GoalManager()
        
        # Initialize category mapping for specialized handlers
        self._category_handlers = {
            # Security goals
            "emergency_fund": self._handle_security_goal,
            "insurance": self._handle_security_goal,
            "life_insurance": self._handle_security_goal,
            "health_insurance": self._handle_security_goal,
            
            # Essential goals
            "home_purchase": self._handle_essential_goal,
            "education": self._handle_essential_goal,
            "debt_repayment": self._handle_essential_goal,
            "debt_elimination": self._handle_essential_goal,
            
            # Retirement goals
            "early_retirement": self._handle_retirement_goal,
            "traditional_retirement": self._handle_retirement_goal,
            
            # Lifestyle goals
            "travel": self._handle_lifestyle_goal,
            "vehicle": self._handle_lifestyle_goal,
            "home_improvement": self._handle_lifestyle_goal,
            
            # Legacy goals
            "estate_planning": self._handle_legacy_goal,
            "charitable_giving": self._handle_legacy_goal
        }
        
    # Core goal operations
    
    def create_goal(self, goal_data: Dict[str, Any], user_profile_id: str) -> Optional[Goal]:
        """
        Create a new goal with compatibility for both simple and enhanced parameters.
        
        Args:
            goal_data (Dict[str, Any]): Goal data in either simple or enhanced format
            user_profile_id (str): ID of the user profile
            
        Returns:
            Optional[Goal]: Created goal object or None if failed
            
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If field types are incorrect
            RuntimeError: If goal creation fails in the database
        """
        # Validate required fields
        required_fields = ['category', 'title', 'target_amount', 'timeframe']
        missing_fields = [field for field in required_fields if field not in goal_data]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Validate numeric fields
        numeric_fields = ['target_amount', 'current_amount']
        for field in numeric_fields:
            if field in goal_data:
                try:
                    goal_data[field] = float(goal_data[field])
                except (ValueError, TypeError):
                    error_msg = f"Field '{field}' must be a valid number"
                    logger.error(error_msg)
                    raise TypeError(error_msg)
        
        try:
            # Ensure user_profile_id is set
            if 'user_profile_id' not in goal_data:
                goal_data['user_profile_id'] = user_profile_id
                
            # Process legacy fields if present (backward compatibility)
            if 'priority' in goal_data and 'importance' not in goal_data:
                goal_data['importance'] = goal_data['priority']
                
            if 'time_horizon' in goal_data and 'timeframe' not in goal_data:
                # Convert time_horizon (years) to timeframe (date)
                try:
                    years = float(goal_data['time_horizon'])
                    if years > 0:
                        target_date = datetime.now().replace(
                            year=datetime.now().year + int(years)
                        )
                        goal_data['timeframe'] = target_date.isoformat()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert time_horizon to timeframe: {str(e)}")
                    
            if 'target_value' in goal_data and 'target_amount' not in goal_data:
                goal_data['target_amount'] = goal_data['target_value']
                
            if 'current_value' in goal_data and 'current_amount' not in goal_data:
                goal_data['current_amount'] = goal_data['current_value']
                
            if 'description' in goal_data and 'notes' not in goal_data:
                goal_data['notes'] = goal_data['description']
                
            # Handle category-specific processing based on goal type
            logger.debug(f"Processing category-specific data for {goal_data.get('category')}")
            goal_data = self._process_category_specific_data(goal_data)
            
            # Create goal from processed data
            if isinstance(goal_data, dict):
                logger.debug("Creating Goal object from dictionary")
                goal = Goal.from_dict(goal_data)
            else:
                # If somehow we received a Goal object directly
                logger.debug("Using provided Goal object directly")
                goal = goal_data
                
            # Save goal to database via manager
            created_goal = self.goal_manager.create_goal(goal)
            
            if not created_goal:
                error_msg = "Database operation failed while creating goal"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info(f"Successfully created goal {created_goal.id} for profile {created_goal.user_profile_id}")
            return created_goal
        
        except Exception as e:
            logger.error(f"Error creating goal: {str(e)}", exc_info=True)
            # Re-raise the exception to let the caller handle it appropriately
            raise
    
    def update_goal(self, goal_id: str, goal_data: Dict[str, Any]) -> Optional[Goal]:
        """
        Update an existing goal with compatibility for both simple and enhanced parameters.
        
        Args:
            goal_id (str): ID of the goal to update
            goal_data (Dict[str, Any]): Updated goal data
            
        Returns:
            Optional[Goal]: Updated goal object or None if failed
            
        Raises:
            ValueError: If goal_id is invalid or fields have invalid values
            TypeError: If field types are incorrect
            RuntimeError: If goal update fails in the database
        """
        # Validate that we have a valid goal_id
        if not goal_id:
            error_msg = "Goal ID is required for updates"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Validate numeric fields if present
        numeric_fields = ['target_amount', 'current_amount']
        for field in numeric_fields:
            if field in goal_data:
                try:
                    goal_data[field] = float(goal_data[field])
                except (ValueError, TypeError):
                    error_msg = f"Field '{field}' must be a valid number"
                    logger.error(error_msg)
                    raise TypeError(error_msg)
                    
        try:
            # Get the existing goal
            existing_goal = self.goal_manager.get_goal(goal_id)
            if not existing_goal:
                error_msg = f"Goal {goal_id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Process legacy fields if present (backward compatibility)
            if 'priority' in goal_data and 'importance' not in goal_data:
                goal_data['importance'] = goal_data['priority']
                
            if 'time_horizon' in goal_data and 'timeframe' not in goal_data:
                # Convert time_horizon (years) to timeframe (date)
                try:
                    years = float(goal_data['time_horizon'])
                    if years > 0:
                        target_date = datetime.now().replace(
                            year=datetime.now().year + int(years)
                        )
                        goal_data['timeframe'] = target_date.isoformat()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert time_horizon to timeframe: {str(e)}")
                    
            if 'target_value' in goal_data and 'target_amount' not in goal_data:
                goal_data['target_amount'] = goal_data['target_value']
                
            if 'current_value' in goal_data and 'current_amount' not in goal_data:
                goal_data['current_amount'] = goal_data['current_value']
                
            if 'description' in goal_data and 'notes' not in goal_data:
                goal_data['notes'] = goal_data['description']
            
            # Handle category-specific processing
            logger.debug(f"Processing category-specific data for {goal_data.get('category', existing_goal.category)}")
            goal_data = self._process_category_specific_data(goal_data)
            
            # Update goal attributes from processed data
            # Keep existing values for anything not in the update data
            # Skip known read-only properties
            read_only_properties = [
                'priority', 'time_horizon', 'target_value', 'current_value', 
                'progress', 'description', 'profile_id'
            ]
            
            for key, value in goal_data.items():
                if key in read_only_properties:
                    # Handle legacy field mappings
                    if key == 'priority':
                        existing_goal.importance = value
                    elif key == 'target_value':
                        existing_goal.target_amount = value
                    elif key == 'current_value':
                        existing_goal.current_amount = value
                    elif key == 'description':
                        existing_goal.notes = value
                    # Skip other read-only properties
                    continue
                elif hasattr(existing_goal, key):
                    try:
                        setattr(existing_goal, key, value)
                    except AttributeError as e:
                        logger.warning(f"Could not set attribute '{key}': {str(e)}")
                else:
                    logger.warning(f"Ignoring unknown field '{key}' during goal update")
                    
            # Update the goal in the database
            updated_goal = self.goal_manager.update_goal(existing_goal)
            
            if not updated_goal:
                error_msg = f"Database operation failed while updating goal {goal_id}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info(f"Successfully updated goal {updated_goal.id}")
            return updated_goal
        
        except Exception as e:
            logger.error(f"Error updating goal {goal_id}: {str(e)}", exc_info=True)
            # Re-raise the exception to let the caller handle it appropriately
            raise
    
    def get_goal(self, goal_id: str, legacy_mode: bool = False, 
                 include_probability_details: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a goal by ID with format compatibility for consuming components.
        
        Args:
            goal_id (str): ID of the goal to retrieve
            legacy_mode (bool): If True, return only fields expected by legacy code
            include_probability_details (bool): Include detailed probability metrics
            
        Returns:
            Optional[Dict[str, Any]]: Goal data or None if not found
        """
        try:
            # Retrieve the goal
            goal = self.goal_manager.get_goal(goal_id)
            if not goal:
                return None
                
            # Get the base goal data
            goal_data = goal.to_dict(legacy_mode=legacy_mode)
            
            # Add probability details if requested
            if include_probability_details and not legacy_mode:
                try:
                    if hasattr(goal, 'simulation_data') and goal.simulation_data:
                        # Parse simulation data
                        sim_data = json.loads(goal.simulation_data)
                        
                        # Extract probability metrics for API
                        if 'success_metrics' in sim_data:
                            goal_data['probability_metrics'] = sim_data['success_metrics']
                            
                        # Add time-based metrics
                        if 'time_based_metrics' in sim_data:
                            goal_data['time_metrics'] = sim_data['time_based_metrics']
                            
                        # Add simulation metadata
                        if 'meta' in sim_data:
                            goal_data['probability_meta'] = sim_data['meta']
                except Exception as e:
                    logger.warning(f"Error parsing probability data for goal {goal_id}: {str(e)}")
                
            return goal_data
        
        except Exception as e:
            logger.error(f"Error retrieving goal {goal_id}: {str(e)}")
            return None
    
    def get_profile_goals(self, profile_id: str, legacy_mode: bool = False,
                         include_probability_details: bool = True) -> List[Dict[str, Any]]:
        """
        Get all goals for a profile with format compatibility for consuming components.
        
        Args:
            profile_id (str): ID of the user profile
            legacy_mode (bool): If True, return only fields expected by legacy code
            include_probability_details (bool): Include detailed probability metrics
            
        Returns:
            List[Dict[str, Any]]: List of goal data
        """
        try:
            # Retrieve goals for the profile
            goals = self.goal_manager.get_profile_goals(profile_id)
            
            # Use get_goal for each to ensure consistent processing
            result = []
            for goal in goals:
                goal_data = self.get_goal(
                    goal_id=goal.id,
                    legacy_mode=legacy_mode,
                    include_probability_details=include_probability_details
                )
                if goal_data:
                    result.append(goal_data)
            
            return result
        
        except Exception as e:
            logger.error(f"Error retrieving goals for profile {profile_id}: {str(e)}")
            return []
            
    def get_goals_for_profile(self, profile_id: str, legacy_mode: bool = False,
                             include_probability_details: bool = True) -> List[Dict[str, Any]]:
        """
        Get all goals for a profile - alias for get_profile_goals to maintain compatibility.
        
        Args:
            profile_id (str): ID of the user profile
            legacy_mode (bool): If True, return only fields expected by legacy code
            include_probability_details (bool): Include detailed probability metrics
            
        Returns:
            List[Dict[str, Any]]: List of goal data
        """
        return self.get_profile_goals(
            profile_id=profile_id,
            legacy_mode=legacy_mode,
            include_probability_details=include_probability_details
        )
    
    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a goal.
        
        Args:
            goal_id (str): ID of the goal to delete
            
        Returns:
            bool: Success status
        """
        try:
            return self.goal_manager.delete_goal(goal_id)
        except Exception as e:
            logger.error(f"Error deleting goal {goal_id}: {str(e)}")
            return False
            
    def add_scenario_to_goal(self, goal_id: str, scenario: Dict[str, Any]) -> bool:
        """
        Add a scenario to a goal's list of scenarios.
        
        Args:
            goal_id (str): The ID of the goal to add the scenario to
            scenario (Dict[str, Any]): The scenario data to add
            
        Returns:
            bool: Success status
        """
        try:
            # Get the existing goal
            goal = self.goal_manager.get_goal(goal_id)
            if not goal:
                logger.error(f"Goal {goal_id} not found")
                return False
            
            # Get existing scenarios or initialize empty list
            current_scenarios = []
            if hasattr(goal, 'scenarios') and goal.scenarios:
                try:
                    if isinstance(goal.scenarios, str):
                        current_scenarios = json.loads(goal.scenarios)
                    else:
                        current_scenarios = goal.scenarios
                except Exception as e:
                    logger.error(f"Error parsing existing scenarios: {str(e)}")
                    current_scenarios = []
            
            # Validate and sanitize the scenario
            if 'id' not in scenario:
                scenario['id'] = str(uuid.uuid4())
            
            if 'created_at' not in scenario:
                scenario['created_at'] = datetime.now().isoformat()
            
            # Ensure baseline flag is set
            if 'is_baseline' not in scenario:
                scenario['is_baseline'] = False
            
            # Add the new scenario to the list
            current_scenarios.append(scenario)
            
            # Update the goal
            setattr(goal, 'scenarios', json.dumps(current_scenarios))
            
            # Save the updated goal
            self.goal_manager.update_goal(goal)
            return True
            
        except Exception as e:
            logger.error(f"Error adding scenario to goal {goal_id}: {str(e)}")
            return False
    
    def remove_scenario_from_goal(self, goal_id: str, scenario_id: str) -> bool:
        """
        Remove a scenario from a goal's list of scenarios.
        
        Args:
            goal_id (str): The ID of the goal to remove the scenario from
            scenario_id (str): The ID of the scenario to remove
            
        Returns:
            bool: Success status
        """
        try:
            # Get the existing goal
            goal = self.goal_manager.get_goal(goal_id)
            if not goal:
                logger.error(f"Goal {goal_id} not found")
                return False
            
            # Get existing scenarios
            current_scenarios = []
            if hasattr(goal, 'scenarios') and goal.scenarios:
                try:
                    if isinstance(goal.scenarios, str):
                        current_scenarios = json.loads(goal.scenarios)
                    else:
                        current_scenarios = goal.scenarios
                except Exception as e:
                    logger.error(f"Error parsing existing scenarios: {str(e)}")
                    return False
            
            # Check if scenario exists
            scenario_exists = any(s.get('id') == scenario_id for s in current_scenarios)
            if not scenario_exists:
                logger.error(f"Scenario {scenario_id} not found in goal {goal_id}")
                return False
            
            # Check if trying to delete baseline scenario
            if any(s.get('id') == scenario_id and s.get('is_baseline', False) for s in current_scenarios):
                logger.error(f"Cannot delete baseline scenario from goal {goal_id}")
                return False
            
            # Remove the scenario from the list
            current_scenarios = [s for s in current_scenarios if s.get('id') != scenario_id]
            
            # Update the goal
            setattr(goal, 'scenarios', json.dumps(current_scenarios))
            
            # Save the updated goal
            self.goal_manager.update_goal(goal)
            return True
            
        except Exception as e:
            logger.error(f"Error removing scenario from goal {goal_id}: {str(e)}")
            return False
    
    def calculate_goal_probabilities(self, goal_ids: List[str], profile_data: Dict[str, Any],
                                  simulation_iterations: int = 1000,
                                  force_recalculate: bool = False) -> Dict[str, ProbabilityResult]:
        """
        Calculate success probability for multiple goals using Monte Carlo simulations with caching.
        
        Args:
            goal_ids (List[str]): List of goal IDs to calculate probabilities for
            profile_data (Dict[str, Any]): Profile data with financial information
            simulation_iterations (int, optional): Number of Monte Carlo simulations
            force_recalculate (bool, optional): Force recalculation even if cached
            
        Returns:
            Dict[str, ProbabilityResult]: Dictionary mapping goal IDs to their probability results
        """
        results = {}
        
        # Calculate probability for each goal
        for goal_id in goal_ids:
            result = self.calculate_goal_probability(
                goal_id=goal_id,
                profile_data=profile_data,
                simulation_iterations=simulation_iterations,
                force_recalculate=force_recalculate
            )
            results[goal_id] = result
            
        return results
    
    def calculate_goal_probability(self, goal_id: str, profile_data: Dict[str, Any], 
                                 simulation_iterations: int = 1000,
                                 force_recalculate: bool = False) -> ProbabilityResult:
        """
        Calculate goal success probability using Monte Carlo simulations with caching.
        
        Args:
            goal_id (str): The ID of the goal to calculate probability for
            profile_data (Dict[str, Any]): Profile data with financial information
            simulation_iterations (int, optional): Number of Monte Carlo simulations
            force_recalculate (bool, optional): Force recalculation even if cached
            
        Returns:
            ProbabilityResult: Detailed probability results
        """
        try:
            # Get the goal
            goal = self.goal_manager.get_goal(goal_id)
            if not goal:
                logger.error(f"Goal {goal_id} not found")
                return ProbabilityResult()
            
            # Check for cached results if not forcing recalculation
            if not force_recalculate and hasattr(goal, 'probability_last_calculated'):
                last_calc = goal.probability_last_calculated
                if last_calc:
                    try:
                        # Parse last calculation time
                        if isinstance(last_calc, str):
                            last_calc_time = datetime.fromisoformat(last_calc)
                        else:
                            last_calc_time = last_calc
                            
                        # If calculated within last hour, check for cached results
                        if (datetime.now() - last_calc_time).total_seconds() < 3600:
                            if hasattr(goal, 'simulation_data') and goal.simulation_data:
                                # Deserialize simulation data
                                try:
                                    sim_data = json.loads(goal.simulation_data)
                                    logger.info(f"Using cached probability for goal {goal_id}")
                                    
                                    # Convert to ProbabilityResult
                                    return ProbabilityResult(
                                        success_metrics=sim_data.get('success_metrics', {}),
                                        time_based_metrics=sim_data.get('time_based_metrics', {}),
                                        distribution_data=sim_data.get('distribution_data', {}),
                                        risk_metrics=sim_data.get('risk_metrics', {})
                                    )
                                except Exception as e:
                                    logger.warning(f"Could not parse cached simulation data: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error parsing last calculation time: {str(e)}")
            
            # Get calculator for the goal
            calculator = GoalCalculator.get_calculator_for_goal(goal)
            
            # Create probability analyzer with cache-enabled simulations
            analyzer = GoalProbabilityAnalyzer()
            
            # Run the probability analysis with the cached_simulation decorator
            # This will automatically cache results based on input parameters
            @cached_simulation
            def run_goal_simulation(goal, profile_data, iterations):
                return analyzer.analyze_goal_probability(
                    goal=goal,
                    profile=profile_data,
                    simulations=iterations
                )
            
            # Start timing the simulation
            start_time = time.time()
            
            # Run or retrieve from cache
            probability_result = run_goal_simulation(
                goal=goal,
                profile_data=profile_data,
                iterations=simulation_iterations
            )
            
            # Log simulation time
            duration = time.time() - start_time
            logger.info(f"Goal probability calculation completed in {duration:.3f}s for goal {goal_id}")
            
            # Ensure result is valid
            if not probability_result or not isinstance(probability_result, ProbabilityResult):
                logger.error(f"Invalid probability result for goal {goal_id}")
                return ProbabilityResult()
                
            # Extract success probability from detailed results
            probability = probability_result.get_safe_success_probability()
            
            # Update goal using existing method
            self.update_goal_probability(
                goal_id=goal_id,
                probability=probability,
                factors=probability_result.get_probability_factors(),
                simulation_results=probability_result.to_dict()
            )
            
            return probability_result
            
        except Exception as e:
            logger.error(f"Error calculating probability for goal {goal_id}: {str(e)}", exc_info=True)
            return ProbabilityResult()

    def update_goal_probability(self, goal_id: str, probability: Union[float, int, str], 
                               factors: List[Dict[str, Any]] = None, 
                               simulation_results: Dict[str, Any] = None) -> bool:
        """
        Update a goal's probability metrics.
        
        Args:
            goal_id (str): The ID of the goal to update
            probability (float): The new probability value
            factors (List[Dict[str, Any]]): Probability factors
            simulation_results (Dict[str, Any]): Simulation results
            
        Returns:
            bool: Success status
        """
        try:
            # Get the existing goal
            goal = self.goal_manager.get_goal(goal_id)
            if not goal:
                logger.error(f"Goal {goal_id} not found")
                return False
            
            # Update probability fields
            # Validate probability value to ensure it's a valid number
            if probability is not None:
                try:
                    probability_value = float(probability)
                    if probability_value != probability_value:  # NaN check
                        logger.warning(f"Invalid probability value (NaN) for goal {goal_id}, setting to 0")
                        probability_value = 0.0
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting probability to float for goal {goal_id}: {str(e)}")
                    probability_value = 0.0
            else:
                logger.warning(f"Null probability value for goal {goal_id}, setting to 0")
                probability_value = 0.0
                
            goal.goal_success_probability = probability_value
            logger.info(f"Setting goal {goal_id} probability to {probability_value} (original: {probability})")
            
            # Check for partial success probability
            if simulation_results and 'success_metrics' in simulation_results:
                success_metrics = simulation_results['success_metrics']
                if 'partial_success_probability' in success_metrics:
                    goal.probability_partial_success = success_metrics['partial_success_probability']
                    
                if 'confidence_intervals' in success_metrics:
                    confidence = success_metrics['confidence_intervals']
                    if 'lower_bound' in confidence:
                        goal.probability_lower_bound = confidence['lower_bound']
                    if 'upper_bound' in confidence:
                        goal.probability_upper_bound = confidence['upper_bound']
            
            # Convert factors and simulation results to JSON and save
            simulation_data = {
                "success_probability": probability_value,
                "probability_factors": factors or []
            }
            
            # Add simulation results if provided
            if simulation_results:
                simulation_data.update(simulation_results)
            
            # Serialize to JSON
            goal.simulation_data = json.dumps(simulation_data)
            
            # Add timestamp
            goal.probability_last_calculated = datetime.now().isoformat()
            goal.last_simulation_time = datetime.now().isoformat()
            
            # Add simulation metadata
            if 'meta' not in simulation_data:
                simulation_data['meta'] = {}
            simulation_data['meta']['calculation_timestamp'] = datetime.now().isoformat()
            
            # Save the updated goal
            self.goal_manager.update_goal(goal)
            return True
            
        except Exception as e:
            logger.error(f"Error updating goal probability for {goal_id}: {str(e)}")
            return False
    
    # Goal calculation services
    
    def calculate_goal_probabilities_batch(self, profile_id: str, profile_data: Dict[str, Any],
                                      simulation_iterations: int = 1000,
                                      force_recalculate: bool = False,
                                      max_parallel: int = None) -> Dict[str, ProbabilityResult]:
        """
        Calculate probabilities for multiple goals in parallel.
        
        Args:
            profile_id (str): ID of the user profile
            profile_data (Dict[str, Any]): Profile data with financial information
            simulation_iterations (int, optional): Number of Monte Carlo simulations
            force_recalculate (bool, optional): Force recalculation even if cached
            max_parallel (int, optional): Maximum number of parallel calculations
            
        Returns:
            Dict[str, ProbabilityResult]: Dictionary of goal IDs to probability results
        """
        try:
            # Get all goals for the profile
            goals = self.goal_manager.get_profile_goals(profile_id)
            if not goals:
                logger.warning(f"No goals found for profile {profile_id}")
                return {}
                
            # Start timing
            start_time = time.time()
            
            # Track results
            results = {}
            
            # Process in parallel batches to avoid overloading the system
            batch_size = min(len(goals), 5 if max_parallel is None else max_parallel)
            
            logger.info(f"Calculating goal probabilities for {len(goals)} goals in batches of {batch_size}")
            
            # Use simple threading for parallelization
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit all calculation tasks
                futures = {
                    executor.submit(
                        self.calculate_goal_probability,
                        goal.id,
                        profile_data,
                        simulation_iterations,
                        force_recalculate
                    ): goal.id for goal in goals
                }
                
                # Process results as they complete
                for future in futures:
                    goal_id = futures[future]
                    try:
                        result = future.result()
                        results[goal_id] = result
                        logger.debug(f"Completed probability calculation for goal {goal_id}")
                    except Exception as e:
                        logger.error(f"Error calculating probability for goal {goal_id}: {str(e)}")
                        results[goal_id] = ProbabilityResult()
            
            # Log performance metrics
            duration = time.time() - start_time
            goals_per_second = len(goals) / duration if duration > 0 else 0
            logger.info(f"Batch probability calculation completed in {duration:.3f}s "
                       f"({goals_per_second:.2f} goals/s)")
            
            # Log cache statistics
            cache_stats = get_cache_stats()
            hit_rate = cache_stats.get('hit_rate', 0) * 100
            logger.info(f"Cache performance: {hit_rate:.1f}% hit rate "
                       f"({cache_stats.get('hits', 0)} hits, {cache_stats.get('misses', 0)} misses)")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch probability calculation: {str(e)}", exc_info=True)
            return {}
    
    def invalidate_goal_probability_cache(self, goal_id: str = None, profile_id: str = None) -> int:
        """
        Invalidate cached probability calculations.
        
        Args:
            goal_id (str, optional): Specific goal ID to invalidate, or None for all
            profile_id (str, optional): Profile ID to invalidate all goals for
            
        Returns:
            int: Number of cache entries invalidated
        """
        try:
            pattern = None
            
            # Create cache invalidation pattern based on parameters
            if goal_id:
                pattern = f"goal:{goal_id}"
            elif profile_id:
                # Get all goals for this profile
                goals = self.goal_manager.get_profile_goals(profile_id)
                
                # Invalidate each goal
                invalidated = 0
                for goal in goals:
                    invalidated += invalidate_cache(f"goal:{goal.id}")
                
                logger.info(f"Invalidated {invalidated} cache entries for profile {profile_id}")
                return invalidated
            
            # Invalidate with pattern or all
            invalidated = invalidate_cache(pattern)
            
            if pattern:
                logger.info(f"Invalidated {invalidated} cache entries matching '{pattern}'")
            else:
                logger.info(f"Invalidated all {invalidated} cache entries")
                
            return invalidated
            
        except Exception as e:
            logger.error(f"Error invalidating probability cache: {str(e)}")
            return 0
    
    def calculate_goal_amounts(self, profile_id: str, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate required amounts and savings rates for all goals in a profile.
        
        Args:
            profile_id (str): ID of the user profile
            profile_data (Dict[str, Any]): Profile data with financial information
            
        Returns:
            List[Dict[str, Any]]: List of goals with calculated fields
        """
        try:
            # Get all goals for the profile
            goals = self.goal_manager.get_profile_goals(profile_id)
            if not goals:
                return []
                
            # Calculate for each goal
            results = []
            for goal in goals:
                # Get appropriate calculator for the goal
                calculator = GoalCalculator.get_calculator_for_goal(goal)
                
                # Calculate key metrics
                amount_needed = calculator.calculate_amount_needed(goal, profile_data)
                monthly_savings = calculator.calculate_required_saving_rate(goal, profile_data)
                success_probability = calculator.calculate_goal_success_probability(goal, profile_data)
                
                # Update goal with calculated values
                goal.target_amount = amount_needed
                goal.goal_success_probability = success_probability
                
                # Create result with goal data and calculated fields
                result = goal.to_dict()
                result['required_monthly_savings'] = monthly_savings
                
                # Add category-specific calculated fields
                result = self._add_category_specific_calculations(result, calculator, profile_data)
                
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error calculating goal amounts for profile {profile_id}: {str(e)}")
            return []
    
    def analyze_goal_priorities(self, profile_id: str) -> List[Dict[str, Any]]:
        """
        Analyze and prioritize goals for a profile.
        
        Args:
            profile_id (str): ID of the user profile
            
        Returns:
            List[Dict[str, Any]]: Prioritized goals with analysis data
        """
        try:
            # Get goals sorted by priority
            goals = self.goal_manager.get_goals_by_priority(profile_id)
            if not goals:
                return []
                
            # Process each goal with priority information
            results = []
            for i, goal in enumerate(goals):
                result = goal.to_dict()
                
                # Add priority ranking (1-based)
                result['priority_rank'] = i + 1
                
                # Add category-based hierarchy level
                category = self.goal_manager.get_category_by_name(goal.category)
                if category:
                    result['hierarchy_level'] = category.hierarchy_level
                    result['is_foundation'] = category.is_foundation
                
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing goal priorities for profile {profile_id}: {str(e)}")
            return []
    
    def get_goal_categories(self, include_subcategories: bool = True) -> List[Dict[str, Any]]:
        """
        Get all goal categories, optionally including subcategories.
        
        Args:
            include_subcategories (bool): Whether to include subcategories
            
        Returns:
            List[Dict[str, Any]]: List of category data
        """
        try:
            # Get all categories
            categories = self.goal_manager.get_all_categories()
            
            # Filter if needed
            if not include_subcategories:
                categories = [c for c in categories if c.parent_category_id is None]
                
            # Convert to dictionaries
            return [category.to_dict() for category in categories]
            
        except Exception as e:
            logger.error(f"Error retrieving goal categories: {str(e)}")
            return []
    
    # Category-specific handlers
    
    def _process_category_specific_data(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process category-specific data for a goal.
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            
        Returns:
            Dict[str, Any]: Processed goal data
            
        Raises:
            ValueError: If the category is invalid or processing fails
        """
        # Get the category
        category = goal_data.get('category')
        if not category:
            logger.warning("No category specified in goal data, skipping category-specific processing")
            return goal_data
            
        # Check if this is a known category
        all_categories = list(self._category_handlers.keys()) + ['custom']
        if category not in all_categories:
            logger.warning(f"Unknown category '{category}', treating as custom")
            # Still process the data, but log the warning
        
        # Get handler for this category if it exists
        handler = self._category_handlers.get(category)
        if handler:
            try:
                logger.debug(f"Applying category handler for '{category}'")
                processed_data = handler(goal_data)
                return processed_data
            except Exception as e:
                error_msg = f"Error in category handler for '{category}': {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
        # No specific handler, return unchanged
        logger.debug(f"No specific handler for category '{category}', using default processing")
        return goal_data
    
    def _handle_security_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle security-related goals (emergency fund, insurance).
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            
        Returns:
            Dict[str, Any]: Processed goal data
            
        Raises:
            ValueError: If category-specific processing fails
        """
        try:
            # Set appropriate defaults for security goals
            if 'importance' not in goal_data:
                goal_data['importance'] = 'high'  # Security goals are high importance
                
            if 'flexibility' not in goal_data:
                goal_data['flexibility'] = 'fixed'  # Security goals are generally not flexible
                
            # Add foundation status via funding strategy
            if 'funding_strategy' not in goal_data or not goal_data['funding_strategy']:
                # Create new strategy
                strategy = {
                    'is_foundation': True,
                    'recommended_priority': 1  # Highest priority
                }
                
                # Add category-specific strategy elements
                if goal_data.get('category') == 'emergency_fund':
                    strategy['months'] = 6  # Default 6 months of expenses
                    
                elif goal_data.get('category') in ['insurance', 'life_insurance', 'health_insurance']:
                    strategy['insurance_type'] = goal_data.get('category').replace('_', ' ')
                    
                # Store as JSON string
                goal_data['funding_strategy'] = json.dumps(strategy)
                
            return goal_data
            
        except Exception as e:
            error_msg = f"Error processing security goal data: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _handle_essential_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle essential goals (home, education, debt).
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            
        Returns:
            Dict[str, Any]: Processed goal data
            
        Raises:
            ValueError: If category-specific processing fails
        """
        try:
            # Set appropriate defaults for essential goals
            if 'importance' not in goal_data:
                goal_data['importance'] = 'high'  # Essential goals are high importance
                
            # Add essential status via funding strategy
            if 'funding_strategy' not in goal_data or not goal_data['funding_strategy']:
                # Create new strategy
                strategy = {
                    'is_essential': True,
                    'recommended_priority': 2  # Second highest priority
                }
                
                # Add category-specific strategy elements
                if goal_data.get('category') == 'home_purchase':
                    strategy['down_payment_percent'] = 0.20  # Default 20% down payment
                    
                elif goal_data.get('category') == 'education':
                    strategy['education_inflation_rate'] = 0.08  # Education costs rise faster
                    
                elif goal_data.get('category') in ['debt_repayment', 'debt_elimination']:
                    strategy['debt_type'] = 'general'
                    strategy['interest_rate'] = 0.10  # Default 10% interest rate
                    
                # Store as JSON string
                goal_data['funding_strategy'] = json.dumps(strategy)
                
            return goal_data
            
        except Exception as e:
            error_msg = f"Error processing essential goal data: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _handle_retirement_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle retirement goals.
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            
        Returns:
            Dict[str, Any]: Processed goal data
            
        Raises:
            ValueError: If category-specific processing fails
        """
        try:
            # Set appropriate defaults for retirement goals
            if 'importance' not in goal_data:
                goal_data['importance'] = 'high'  # Retirement is high importance
                
            # Add retirement status via funding strategy
            if 'funding_strategy' not in goal_data or not goal_data['funding_strategy']:
                # Create new strategy
                strategy = {
                    'recommended_priority': 3  # Third highest priority
                }
                
                # Add category-specific strategy elements
                if goal_data.get('category') == 'early_retirement':
                    strategy['retirement_age'] = 45  # Default age for early retirement
                    strategy['withdrawal_rate'] = 0.035  # More conservative than traditional
                    
                elif goal_data.get('category') == 'traditional_retirement':
                    strategy['retirement_age'] = 60  # Default age for traditional retirement
                    strategy['withdrawal_rate'] = 0.04  # 4% rule
                    
                # Store as JSON string
                goal_data['funding_strategy'] = json.dumps(strategy)
                
            return goal_data
        
        except Exception as e:
            error_msg = f"Error processing retirement goal data: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _handle_lifestyle_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle lifestyle goals (travel, vehicle, home improvement).
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            
        Returns:
            Dict[str, Any]: Processed goal data
            
        Raises:
            ValueError: If category-specific processing fails
        """
        try:
            # Set appropriate defaults for lifestyle goals
            if 'importance' not in goal_data:
                goal_data['importance'] = 'medium'  # Lifestyle goals are medium importance
                
            if 'flexibility' not in goal_data:
                goal_data['flexibility'] = 'somewhat_flexible'  # Usually somewhat flexible
                
            # Add lifestyle status via funding strategy
            if 'funding_strategy' not in goal_data or not goal_data['funding_strategy']:
                # Create new strategy
                strategy = {
                    'recommended_priority': 4  # Fourth highest priority
                }
                
                # Add category-specific strategy elements
                if goal_data.get('category') == 'travel':
                    strategy['travel_type'] = 'general'
                    
                elif goal_data.get('category') == 'vehicle':
                    strategy['vehicle_type'] = 'car'
                    strategy['depreciation_rate'] = 0.15  # 15% annual depreciation
                    
                elif goal_data.get('category') == 'home_improvement':
                    strategy['improvement_type'] = 'general'
                    
                # Store as JSON string
                goal_data['funding_strategy'] = json.dumps(strategy)
                
            return goal_data
        
        except Exception as e:
            error_msg = f"Error processing lifestyle goal data: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _handle_legacy_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle legacy goals (estate planning, charitable giving).
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            
        Returns:
            Dict[str, Any]: Processed goal data
            
        Raises:
            ValueError: If category-specific processing fails
        """
        try:
            # Set appropriate defaults for legacy goals
            if 'importance' not in goal_data:
                goal_data['importance'] = 'medium'  # Legacy goals are medium importance
                
            if 'flexibility' not in goal_data:
                goal_data['flexibility'] = 'very_flexible'  # Usually very flexible
                
            # Add legacy status via funding strategy
            if 'funding_strategy' not in goal_data or not goal_data['funding_strategy']:
                # Create new strategy
                strategy = {
                    'recommended_priority': 5  # Fifth highest priority
                }
                
                # Add category-specific strategy elements
                if goal_data.get('category') == 'estate_planning':
                    strategy['estate_plan_type'] = 'general'
                    
                elif goal_data.get('category') == 'charitable_giving':
                    strategy['charity_type'] = 'general'
                    
                # Store as JSON string
                goal_data['funding_strategy'] = json.dumps(strategy)
                
            return goal_data
            
        except Exception as e:
            error_msg = f"Error processing legacy goal data: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _add_category_specific_calculations(self, goal_data: Dict[str, Any], 
                                          calculator: GoalCalculator,
                                          profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add category-specific calculated fields to goal data.
        
        Args:
            goal_data (Dict[str, Any]): Goal data
            calculator (GoalCalculator): Calculator for this goal
            profile_data (Dict[str, Any]): Profile data
            
        Returns:
            Dict[str, Any]: Goal data with additional calculated fields
            
        Raises:
            ValueError: If calculator is missing or invalid
        """
        # Verify calculator is valid
        if not calculator:
            error_msg = "Calculator is required for category-specific calculations"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        category = goal_data.get('category')
        if not category:
            logger.warning("No category specified, skipping category-specific calculations")
            return goal_data
            
        try:
            # Add recommended asset allocation
            if hasattr(calculator, 'get_recommended_allocation'):
                try:
                    # Reconstruct goal object from data for calculator
                    goal_obj = Goal.from_dict(goal_data)
                    allocation = calculator.get_recommended_allocation(goal_obj, profile_data)
                    goal_data['recommended_allocation'] = allocation
                except Exception as e:
                    logger.warning(f"Error getting recommended allocation: {str(e)}")
            
            # Add category-specific fields
            if category in ['early_retirement', 'traditional_retirement']:
                # Add retirement projection
                if hasattr(calculator, 'simulate_goal_progress'):
                    try:
                        goal_obj = Goal.from_dict(goal_data)
                        projection = calculator.simulate_goal_progress(goal_obj, profile_data, years=5)
                        goal_data['projection_5yr'] = projection
                    except Exception as e:
                        logger.warning(f"Error simulating retirement goal progress: {str(e)}")
            
            elif category == 'education':
                # Add education projection
                if hasattr(calculator, 'simulate_goal_progress'):
                    try:
                        goal_obj = Goal.from_dict(goal_data)
                        projection = calculator.simulate_goal_progress(goal_obj, profile_data, years=5)
                        goal_data['projection_5yr'] = projection
                    except Exception as e:
                        logger.warning(f"Error simulating education goal progress: {str(e)}")
            
            return goal_data
            
        except Exception as e:
            error_msg = f"Error adding category-specific calculations: {str(e)}"
            logger.error(error_msg)
            # This is non-critical, so log but don't raise to allow goal creation to continue
            return goal_data