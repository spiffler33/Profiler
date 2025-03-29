"""
Integration module connecting LifeEventRegistry with RebalancingStrategy.

This module serves as the bridge between the centralized life event system
and the portfolio rebalancing system, ensuring both systems can communicate
effectively while maintaining loose coupling.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import importlib

logger = logging.getLogger(__name__)

class RebalancingLifeEventIntegration:
    """
    Integration manager for connecting the life event registry to rebalancing strategies.
    
    This class implements the Observer pattern to allow rebalancing strategies to
    respond to life events detected by the centralized registry.
    """
    
    def __init__(self):
        """Initialize the integration manager"""
        self.registry = None
        self.rebalancing_strategy = None
        self.profile_callbacks = {}  # profile_id -> callback function
        
        # Try to import required modules
        try:
            self.life_event_registry_module = importlib.import_module('models.life_event_registry')
            self.rebalancing_strategy_module = importlib.import_module('models.funding_strategies.rebalancing_strategy')
            self.has_required_modules = True
            logger.info("Successfully imported required modules for life event integration")
        except ImportError as e:
            self.has_required_modules = False
            logger.warning(f"Failed to import modules for life event integration: {str(e)}")
    
    def initialize(self):
        """Initialize the registry and strategy connections"""
        if not self.has_required_modules:
            logger.warning("Cannot initialize integration, required modules not available")
            return False
            
        try:
            # Create/get registry instance
            self.registry = self.life_event_registry_module.LifeEventRegistry()
            
            # Create/get rebalancing strategy instance
            self.rebalancing_strategy = self.rebalancing_strategy_module.RebalancingStrategy()
            
            logger.info("Successfully initialized life event integration")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize life event integration: {str(e)}")
            return False
    
    def register_profile(self, profile_id: str, strategy_instance=None):
        """
        Register a profile for life event monitoring
        
        Args:
            profile_id: The user profile ID to monitor
            strategy_instance: Optional rebalancing strategy instance to use
        """
        if not self.has_required_modules or not self.registry:
            logger.warning(f"Cannot register profile {profile_id}, integration not initialized")
            return
            
        # Use the provided strategy instance or the default one
        strategy = strategy_instance or self.rebalancing_strategy
        
        # Create callback for this profile
        def rebalancing_event_callback(event):
            """
            Callback function that will be triggered when a life event occurs
            
            Args:
                event: The life event object
            """
            try:
                logger.info(f"Rebalancing event triggered for profile {profile_id}: {event.name}")
                
                # Check if event has rebalancing impacts
                if "rebalancing_impacts" in event.metadata:
                    # Get the current strategy for this profile
                    current_strategy = strategy.get_current_strategy(profile_id)
                    
                    if current_strategy:
                        # Process the event impact
                        logger.info(f"Processing rebalancing impact for event: {event.name}")
                        
                        # Add the event to the strategy's review triggers
                        if "review_schedule" in current_strategy:
                            if "life_event_triggers" not in current_strategy["review_schedule"]:
                                current_strategy["review_schedule"]["life_event_triggers"] = {"events": []}
                                
                            event_trigger = {
                                "event_id": event.id,
                                "event_name": event.name,
                                "date_detected": event.date_detected,
                                "severity": event.severity.value if hasattr(event.severity, "value") else event.severity,
                                "rebalancing_impacts": event.metadata["rebalancing_impacts"],
                                "processed": False
                            }
                            
                            current_strategy["review_schedule"]["life_event_triggers"]["events"].append(event_trigger)
                            
                            # Update the strategy
                            strategy.update_strategy(profile_id, current_strategy)
                            logger.info(f"Updated rebalancing strategy for profile {profile_id} with event {event.name}")
            except Exception as e:
                logger.error(f"Error in rebalancing event callback: {str(e)}")
        
        # Store the callback function for this profile
        self.profile_callbacks[profile_id] = rebalancing_event_callback
        
        # Subscribe to events for this profile
        self.registry.subscribe(f"profile_{profile_id}", rebalancing_event_callback)
        
        # Also subscribe to high-severity events
        self.registry.subscribe("severity_high", rebalancing_event_callback)
        
        logger.info(f"Registered profile {profile_id} for life event monitoring")
    
    def unregister_profile(self, profile_id: str):
        """
        Unregister a profile from life event monitoring
        
        Args:
            profile_id: The user profile ID to stop monitoring
        """
        if not self.has_required_modules or not self.registry:
            return
            
        if profile_id in self.profile_callbacks:
            # Get the callback for this profile
            callback = self.profile_callbacks[profile_id]
            
            # Unsubscribe from registry
            # Note: This would require the registry to implement an unsubscribe method
            # which isn't in our current implementation
            
            # Remove from our tracking
            del self.profile_callbacks[profile_id]
            
            logger.info(f"Unregistered profile {profile_id} from life event monitoring")
    
    def get_pending_events(self, profile_id: str) -> List[Dict[str, Any]]:
        """
        Get all pending life events for a profile that require rebalancing attention
        
        Args:
            profile_id: The user profile ID
            
        Returns:
            List of life events with rebalancing impacts
        """
        if not self.has_required_modules or not self.registry:
            return []
            
        try:
            # Get all events for this profile
            all_events = self.registry.get_profile_events(profile_id)
            
            # Filter for events with rebalancing impacts
            rebalancing_events = []
            for event in all_events:
                if "rebalancing_impacts" in event.metadata:
                    rebalancing_events.append({
                        "id": event.id,
                        "name": event.name,
                        "description": event.description,
                        "date_detected": event.date_detected,
                        "expected_date": event.expected_date,
                        "severity": event.severity.value if hasattr(event.severity, "value") else event.severity,
                        "category": event.category.value if hasattr(event.category, "value") else event.category,
                        "rebalancing_impacts": event.metadata["rebalancing_impacts"]
                    })
            
            return rebalancing_events
            
        except Exception as e:
            logger.error(f"Error getting pending events for profile {profile_id}: {str(e)}")
            return []
    
    def mark_event_processed(self, profile_id: str, event_id: str):
        """
        Mark a life event as processed in the rebalancing system
        
        Args:
            profile_id: The user profile ID
            event_id: The ID of the event to mark as processed
        """
        if not self.has_required_modules or not self.registry:
            return
            
        try:
            # Get the current strategy for this profile
            strategy = self.rebalancing_strategy
            current_strategy = strategy.get_current_strategy(profile_id)
            
            if current_strategy and "review_schedule" in current_strategy:
                if "life_event_triggers" in current_strategy["review_schedule"]:
                    events = current_strategy["review_schedule"]["life_event_triggers"].get("events", [])
                    
                    # Find and mark the event as processed
                    for event in events:
                        if event.get("event_id") == event_id:
                            event["processed"] = True
                            logger.info(f"Marked event {event_id} as processed for profile {profile_id}")
                            
                    # Update the strategy
                    strategy.update_strategy(profile_id, current_strategy)
        except Exception as e:
            logger.error(f"Error marking event {event_id} as processed: {str(e)}")
    
    def create_and_register_event(self, profile_id: str, event_type: str, 
                                  expected_date: Optional[str] = None,
                                  additional_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a standard life event and register it with rebalancing impacts
        
        Args:
            profile_id: The user profile ID
            event_type: The type of standard event to create
            expected_date: Optional date when the event is expected to occur
            additional_data: Optional additional data for the event
            
        Returns:
            The ID of the created event or None if failed
        """
        if not self.has_required_modules or not self.registry:
            logger.warning(f"Cannot create event, integration not initialized")
            return None
            
        try:
            # Create the standard event
            event_id = self.registry.create_standard_event(
                event_type=event_type,
                profile_id=profile_id,
                expected_date=expected_date,
                metadata=additional_data
            )
            
            if event_id:
                logger.info(f"Created and registered life event {event_type} for profile {profile_id}")
                
                # Ensure this profile is registered for monitoring
                if profile_id not in self.profile_callbacks:
                    self.register_profile(profile_id)
                    
                return event_id
            else:
                logger.warning(f"Failed to create life event {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating life event: {str(e)}")
            return None


# Create a singleton instance
integration_manager = RebalancingLifeEventIntegration()