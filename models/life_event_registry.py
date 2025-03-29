import logging
import json
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
from enum import Enum
import uuid
from collections import defaultdict

class EventCategory(Enum):
    """Categories for life events to organize and prioritize them"""
    FAMILY = "family"
    CAREER = "career"
    FINANCIAL = "financial"
    HEALTH = "health"
    HOUSING = "housing"
    EDUCATION = "education"
    LEGAL = "legal"
    MAJOR_PURCHASE = "major_purchase"
    TRAVEL = "travel"
    OTHER = "other"


class EventSeverity(Enum):
    """Impact level of life events on financial planning"""
    HIGH = "high"         # Major impact requiring significant strategy changes
    MEDIUM = "medium"     # Moderate impact requiring some adjustments
    LOW = "low"           # Minor impact requiring minimal changes
    INFORMATIONAL = "informational"  # Awareness only, no immediate changes needed


class LifeEvent:
    """
    Model for life events that can impact financial planning and portfolio rebalancing.
    """
    
    def __init__(self, 
                 id: str = None,
                 name: str = "",
                 description: str = "",
                 category: EventCategory = EventCategory.FINANCIAL,
                 severity: EventSeverity = EventSeverity.MEDIUM,
                 date_detected: str = None,
                 expected_date: str = None,
                 user_profile_id: str = None,
                 metadata: Dict[str, Any] = None,
                 trigger_source: str = "manual"):
        """
        Initialize a life event.
        
        Args:
            id: Unique identifier
            name: Short name of the event
            description: Detailed description
            category: Event category for organization
            severity: Impact severity on financial planning
            date_detected: When the event was detected (ISO format)
            expected_date: When the event is expected to occur (ISO format)
            user_profile_id: ID of the associated user profile
            metadata: Additional structured data about the event
            trigger_source: What system component detected this event
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.category = category
        self.severity = severity
        self.date_detected = date_detected or datetime.now().isoformat()
        self.expected_date = expected_date
        self.user_profile_id = user_profile_id
        self.metadata = metadata or {}
        self.trigger_source = trigger_source
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, EventCategory) else self.category,
            "severity": self.severity.value if isinstance(self.severity, EventSeverity) else self.severity,
            "date_detected": self.date_detected,
            "expected_date": self.expected_date,
            "user_profile_id": self.user_profile_id,
            "metadata": self.metadata,
            "trigger_source": self.trigger_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LifeEvent':
        """Create a LifeEvent from a dictionary"""
        # Convert string category and severity to enum types
        category = data.get('category')
        if isinstance(category, str):
            try:
                category = EventCategory(category)
            except ValueError:
                category = EventCategory.OTHER
                
        severity = data.get('severity')
        if isinstance(severity, str):
            try:
                severity = EventSeverity(severity)
            except ValueError:
                severity = EventSeverity.MEDIUM
        
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            category=category,
            severity=severity,
            date_detected=data.get('date_detected'),
            expected_date=data.get('expected_date'),
            user_profile_id=data.get('user_profile_id'),
            metadata=data.get('metadata', {}),
            trigger_source=data.get('trigger_source', 'manual')
        )


class LifeEventRegistry:
    """
    Central registry for life events that can impact financial planning,
    used by both profiling/questioning systems and portfolio rebalancing.
    """
    
    # Standard life events with rebalancing impacts
    STANDARD_EVENTS = {
        # Family events
        "marriage": {
            "name": "Marriage",
            "description": "Getting married or entering a domestic partnership",
            "category": EventCategory.FAMILY,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "moderate",
                "risk_profile_change": "reassess",
                "goal_priority_shift": True,
                "time_horizon_change": "expand"
            }
        },
        "divorce": {
            "name": "Divorce",
            "description": "Divorce or separation from partner",
            "category": EventCategory.FAMILY,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "significant",
                "risk_profile_change": "reassess",
                "goal_priority_shift": True,
                "time_horizon_change": "contract"
            }
        },
        "birth_adoption": {
            "name": "Birth or Adoption",
            "description": "Birth or adoption of a child",
            "category": EventCategory.FAMILY,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "moderate",
                "risk_profile_change": "more_conservative",
                "goal_priority_shift": True,
                "time_horizon_change": "expand"
            }
        },
        "dependent_care": {
            "name": "New Dependent Care",
            "description": "Taking on care for an elderly or disabled family member",
            "category": EventCategory.FAMILY,
            "severity": EventSeverity.MEDIUM,
            "rebalancing_impacts": {
                "allocation_shift": "moderate",
                "risk_profile_change": "more_conservative",
                "cash_allocation_increase": "significant",
                "goal_priority_shift": True
            }
        },
        
        # Career events
        "job_change": {
            "name": "Job Change",
            "description": "Starting a new job or changing employers",
            "category": EventCategory.CAREER,
            "severity": EventSeverity.MEDIUM,
            "rebalancing_impacts": {
                "allocation_shift": "minor",
                "contribution_pattern_change": True,
                "goal_timeline_adjustment": "possible"
            }
        },
        "job_loss": {
            "name": "Job Loss",
            "description": "Involuntary job loss or layoff",
            "category": EventCategory.CAREER,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "defensive",
                "cash_allocation_increase": "significant",
                "contribution_pattern_change": True,
                "goal_timeline_adjustment": "extend"
            }
        },
        "career_break": {
            "name": "Career Break",
            "description": "Voluntary career break or sabbatical",
            "category": EventCategory.CAREER,
            "severity": EventSeverity.MEDIUM,
            "rebalancing_impacts": {
                "allocation_shift": "defensive",
                "cash_allocation_increase": "moderate",
                "contribution_pause": True,
                "goal_timeline_adjustment": "extend"
            }
        },
        "business_start": {
            "name": "Business Start",
            "description": "Starting a new business venture",
            "category": EventCategory.CAREER,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "significant",
                "risk_profile_change": "typically_higher",
                "cash_allocation_increase": "significant",
                "contribution_pattern_change": True
            }
        },
        "retirement": {
            "name": "Retirement",
            "description": "Retirement from primary career",
            "category": EventCategory.CAREER,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "income_focused",
                "risk_profile_change": "more_conservative",
                "contribution_to_withdrawal": True,
                "bucket_strategy_implementation": True
            }
        },
        
        # Financial events
        "windfall": {
            "name": "Financial Windfall",
            "description": "Inheritance, lottery win, or large bonus",
            "category": EventCategory.FINANCIAL,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "significant",
                "risk_profile_review": True,
                "lump_sum_deployment_strategy": "required",
                "goal_acceleration_potential": True
            }
        },
        "major_expense": {
            "name": "Major Unexpected Expense",
            "description": "Large unplanned expense requiring significant funds",
            "category": EventCategory.FINANCIAL,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "emergency_liquidation": "possible",
                "allocation_shift": "defensive",
                "goal_timeline_adjustment": "extend",
                "recovery_strategy": "required"
            }
        },
        "debt_payoff": {
            "name": "Major Debt Payoff",
            "description": "Elimination of significant debt (mortgage, education loans)",
            "category": EventCategory.FINANCIAL,
            "severity": EventSeverity.MEDIUM,
            "rebalancing_impacts": {
                "allocation_shift": "growth_focused",
                "contribution_increase_potential": True,
                "goal_acceleration_potential": True
            }
        },
        
        # Housing events
        "home_purchase": {
            "name": "Home Purchase",
            "description": "Purchase of primary residence",
            "category": EventCategory.HOUSING,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "significant",
                "cash_reserve_depletion": "significant",
                "debt_service_impact": "increase",
                "asset_allocation_adjustment": "required"
            }
        },
        "relocation": {
            "name": "Relocation",
            "description": "Moving to a new city or region",
            "category": EventCategory.HOUSING,
            "severity": EventSeverity.MEDIUM,
            "rebalancing_impacts": {
                "allocation_shift": "moderate",
                "cost_of_living_adjustment": True,
                "goal_priority_reassessment": "recommended"
            }
        },
        
        # Health events
        "major_illness": {
            "name": "Major Illness",
            "description": "Diagnosis of major illness for self or dependent",
            "category": EventCategory.HEALTH,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "defensive",
                "cash_allocation_increase": "significant",
                "risk_profile_change": "more_conservative",
                "goal_priority_shift": True
            }
        },
        "disability": {
            "name": "Disability",
            "description": "Long-term disability affecting income potential",
            "category": EventCategory.HEALTH,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "income_focused",
                "risk_profile_change": "more_conservative",
                "goal_timeline_adjustment": "significant",
                "expense_forecast_revision": "required"
            }
        },
        
        # Indian-specific events
        "family_wedding": {
            "name": "Family Wedding",
            "description": "Wedding expenses for self or children (significant in Indian context)",
            "category": EventCategory.FAMILY,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "defensive",
                "cash_allocation_increase": "significant",
                "goal_milestone_acceleration": True,
                "lump_sum_requirement": "significant"
            }
        },
        "education_abroad": {
            "name": "Foreign Education",
            "description": "Child pursuing education abroad (common high-cost goal in India)",
            "category": EventCategory.EDUCATION,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "defensive",
                "forex_exposure_management": "required",
                "goal_milestone_acceleration": True,
                "lump_sum_requirement": "significant"
            }
        },
        "real_estate_investment": {
            "name": "Real Estate Investment",
            "description": "Investment in additional real estate (common in India)",
            "category": EventCategory.HOUSING,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "significant",
                "illiquidity_increase": "significant",
                "cash_flow_impact": "moderate",
                "portfolio_diversification_impact": "significant"
            }
        },
        "family_business_involvement": {
            "name": "Family Business Involvement",
            "description": "Joining or investing in family business",
            "category": EventCategory.CAREER,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "allocation_shift": "significant",
                "risk_concentration_increase": "significant",
                "income_pattern_change": True,
                "liquidity_requirement_change": "variable"
            }
        },
        "nri_status_change": {
            "name": "NRI Status Change",
            "description": "Change in residential status (resident to NRI or vice versa)",
            "category": EventCategory.LEGAL,
            "severity": EventSeverity.HIGH,
            "rebalancing_impacts": {
                "tax_status_change": "significant",
                "forex_exposure_change": "significant",
                "compliance_requirements_change": True,
                "investment_avenue_change": "significant"
            }
        },
        "ancestral_property": {
            "name": "Ancestral Property Issues",
            "description": "Inheritance or disputes related to ancestral property",
            "category": EventCategory.LEGAL,
            "severity": EventSeverity.MEDIUM,
            "rebalancing_impacts": {
                "illiquid_asset_increase": "possible",
                "legal_expense_provision": "recommended",
                "portfolio_complexity_increase": "possible",
                "tax_planning_requirement": "increased"
            }
        }
    }
    
    def __init__(self):
        """Initialize the life event registry"""
        self.events: Dict[str, LifeEvent] = {}  # All events by ID
        self.profile_events: Dict[str, List[str]] = defaultdict(list)  # User profile ID -> event IDs
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)  # Event type -> list of callbacks
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def register_event(self, event: LifeEvent) -> str:
        """
        Register a life event in the system
        
        Args:
            event: The life event to register
            
        Returns:
            The ID of the registered event
        """
        # Save the event
        self.events[event.id] = event
        
        # Add to profile's events if profile ID is provided
        if event.user_profile_id:
            self.profile_events[event.user_profile_id].append(event.id)
            
        # Log the registration
        self.logger.info(f"Registered life event: {event.name} [{event.id}] for profile: {event.user_profile_id}")
        
        # Notify subscribers
        event_type = event.name.lower().replace(" ", "_")
        self._notify_subscribers(event_type, event)
        
        # Also notify category subscribers
        if isinstance(event.category, EventCategory):
            category_name = event.category.value
        else:
            category_name = str(event.category)
        self._notify_subscribers(f"category_{category_name}", event)
        
        # Notify severity-based subscribers
        if isinstance(event.severity, EventSeverity):
            severity_name = event.severity.value
        else:
            severity_name = str(event.severity)
        self._notify_subscribers(f"severity_{severity_name}", event)
        
        # Notify "all" subscribers for any event
        self._notify_subscribers("all", event)
        
        return event.id
        
    def get_event(self, event_id: str) -> Optional[LifeEvent]:
        """Get a specific event by ID"""
        return self.events.get(event_id)
        
    def get_profile_events(self, profile_id: str, 
                          categories: Optional[List[EventCategory]] = None,
                          severities: Optional[List[EventSeverity]] = None) -> List[LifeEvent]:
        """
        Get all events for a specific user profile, with optional filtering
        
        Args:
            profile_id: The user profile ID
            categories: Optional filter by event categories
            severities: Optional filter by event severities
            
        Returns:
            List of life events matching the criteria
        """
        if profile_id not in self.profile_events:
            return []
            
        events = [self.events[event_id] for event_id in self.profile_events[profile_id] 
                 if event_id in self.events]
        
        # Apply category filter if provided
        if categories:
            category_values = set()
            for cat in categories:
                if isinstance(cat, EventCategory):
                    category_values.add(cat.value)
                else:
                    category_values.add(str(cat))
                    
            events = [e for e in events if (isinstance(e.category, EventCategory) and e.category.value in category_values) or 
                      (not isinstance(e.category, EventCategory) and str(e.category) in category_values)]
        
        # Apply severity filter if provided
        if severities:
            severity_values = set()
            for sev in severities:
                if isinstance(sev, EventSeverity):
                    severity_values.add(sev.value)
                else:
                    severity_values.add(str(sev))
                    
            events = [e for e in events if (isinstance(e.severity, EventSeverity) and e.severity.value in severity_values) or 
                      (not isinstance(e.severity, EventSeverity) and str(e.severity) in severity_values)]
        
        return events
        
    def create_standard_event(self, event_type: str, profile_id: str, 
                             expected_date: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a standard life event from pre-defined templates
        
        Args:
            event_type: The type of standard event (e.g., "marriage", "job_change")
            profile_id: The user profile ID
            expected_date: Optional date when the event is expected to occur
            metadata: Optional additional data for the event
            
        Returns:
            The ID of the created event, or None if the event type is not recognized
        """
        if event_type not in self.STANDARD_EVENTS:
            self.logger.warning(f"Unknown standard event type: {event_type}")
            return None
            
        template = self.STANDARD_EVENTS[event_type]
        
        # Create the event from template
        event = LifeEvent(
            name=template["name"],
            description=template["description"],
            category=template["category"],
            severity=template["severity"],
            expected_date=expected_date,
            user_profile_id=profile_id,
            metadata=metadata or {},
            trigger_source="standard_template"
        )
        
        # Add rebalancing impacts to metadata
        if "rebalancing_impacts" in template:
            event.metadata["rebalancing_impacts"] = template["rebalancing_impacts"]
        
        # Register the event
        return self.register_event(event)
        
    def subscribe(self, event_type: str, callback: Callable[[LifeEvent], None]) -> None:
        """
        Subscribe to a specific type of life event
        
        Args:
            event_type: The type of event to subscribe to:
                        - specific event name (lowercase with underscores)
                        - "category_X" for all events in category X
                        - "severity_X" for all events with severity X
                        - "all" for all events
            callback: Function to call when matching event is registered
        """
        self.subscribers[event_type].append(callback)
        self.logger.info(f"Added subscriber for event type: {event_type}")
        
    def _notify_subscribers(self, event_type: str, event: LifeEvent) -> None:
        """
        Notify all subscribers of a specific event type
        
        Args:
            event_type: The type of event that occurred
            event: The event object
        """
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback for {event_type}: {str(e)}")
                    
    def get_rebalancing_impacts(self, profile_id: str) -> Dict[str, Any]:
        """
        Get aggregated rebalancing impacts for all relevant life events for a profile
        
        Args:
            profile_id: The user profile ID
            
        Returns:
            Dictionary with aggregated rebalancing impacts and their severities
        """
        # Get all events for this profile
        events = self.get_profile_events(profile_id)
        
        # Track impact categories and their severities
        impacts = {
            "allocation_shifts": [],
            "risk_profile_changes": [],
            "goal_priority_shifts": [],
            "time_horizon_changes": [],
            "cash_allocation_changes": [],
            "contribution_pattern_changes": [],
            "lump_sum_requirements": [],
            "emergency_provisions": [],
            "other_impacts": []
        }
        
        # Aggregate impacts from all events
        for event in events:
            if "rebalancing_impacts" not in event.metadata:
                continue
                
            rebalancing_impacts = event.metadata["rebalancing_impacts"]
            
            # Process specific impact types
            if "allocation_shift" in rebalancing_impacts:
                impacts["allocation_shifts"].append({
                    "event_id": event.id,
                    "event_name": event.name,
                    "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                    "impact_type": rebalancing_impacts["allocation_shift"]
                })
                
            if "risk_profile_change" in rebalancing_impacts:
                impacts["risk_profile_changes"].append({
                    "event_id": event.id,
                    "event_name": event.name,
                    "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                    "impact_type": rebalancing_impacts["risk_profile_change"]
                })
                
            if "goal_priority_shift" in rebalancing_impacts and rebalancing_impacts["goal_priority_shift"]:
                impacts["goal_priority_shifts"].append({
                    "event_id": event.id,
                    "event_name": event.name,
                    "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity
                })
                
            if "time_horizon_change" in rebalancing_impacts:
                impacts["time_horizon_changes"].append({
                    "event_id": event.id,
                    "event_name": event.name,
                    "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                    "impact_type": rebalancing_impacts["time_horizon_change"]
                })
                
            if "cash_allocation_increase" in rebalancing_impacts:
                impacts["cash_allocation_changes"].append({
                    "event_id": event.id,
                    "event_name": event.name,
                    "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                    "impact_type": rebalancing_impacts["cash_allocation_increase"],
                    "direction": "increase"
                })
                
            # Check for contribution pattern changes
            for key in ["contribution_pattern_change", "contribution_pause", "contribution_to_withdrawal"]:
                if key in rebalancing_impacts and rebalancing_impacts[key]:
                    impacts["contribution_pattern_changes"].append({
                        "event_id": event.id,
                        "event_name": event.name,
                        "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                        "impact_type": key.replace("_change", "").replace("_", " ")
                    })
                    
            # Check for lump sum requirements
            for key in ["lump_sum_deployment_strategy", "lump_sum_requirement"]:
                if key in rebalancing_impacts:
                    impacts["lump_sum_requirements"].append({
                        "event_id": event.id,
                        "event_name": event.name,
                        "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                        "impact_type": rebalancing_impacts[key] if isinstance(rebalancing_impacts[key], str) else "required"
                    })
                    
            # Check for emergency provisions
            if "emergency_liquidation" in rebalancing_impacts:
                impacts["emergency_provisions"].append({
                    "event_id": event.id,
                    "event_name": event.name,
                    "severity": event.severity.value if isinstance(event.severity, EventSeverity) else event.severity,
                    "impact_type": "liquidation",
                    "status": rebalancing_impacts["emergency_liquidation"]
                })
                
        # Create summary with highest severity impacts
        summary = {
            "has_significant_impacts": any(impact for impact_list in impacts.values() 
                                         for impact in impact_list 
                                         if impact.get("severity") == "high"),
            "primary_allocation_impact": self._get_highest_severity_impact(impacts["allocation_shifts"]),
            "primary_risk_profile_impact": self._get_highest_severity_impact(impacts["risk_profile_changes"]),
            "requires_goal_reprioritization": len(impacts["goal_priority_shifts"]) > 0,
            "requires_cash_allocation_change": len(impacts["cash_allocation_changes"]) > 0,
            "requires_contribution_pattern_change": len(impacts["contribution_pattern_changes"]) > 0,
            "requires_emergency_provisions": len(impacts["emergency_provisions"]) > 0,
            "detailed_impacts": impacts
        }
        
        return summary
    
    def _get_highest_severity_impact(self, impacts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the highest severity impact from a list of impacts"""
        if not impacts:
            return None
            
        # Priority order for severity
        severity_order = {
            "high": 3,
            "medium": 2,
            "low": 1,
            "informational": 0
        }
        
        # Sort by severity and return the highest
        sorted_impacts = sorted(impacts, 
                              key=lambda x: severity_order.get(x.get("severity", "low"), 0), 
                              reverse=True)
        
        return sorted_impacts[0] if sorted_impacts else None