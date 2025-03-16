import logging
from typing import Dict, Any, List, Optional

# Define the understanding levels and their requirements
PROFILE_UNDERSTANDING_LEVELS = {
    "RED": {
        "label": "Basic Information",
        "description": "We're gathering basic information about your financial situation",
        "requirements": {
            "core_completion_pct": 0  # Any level of core questions
        },
        "css_class": "profile-level-red"
    },
    "AMBER": {
        "label": "Financial Foundation",
        "description": "We understand your financial foundation and are exploring your goals",
        "requirements": {
            "core_completion_pct": 100,
            "goal_questions_min": 3
        },
        "css_class": "profile-level-amber"
    },
    "YELLOW": {
        "label": "Deeper Insights",
        "description": "We're gaining deeper insights into your financial situation",
        "requirements": {
            "core_completion_pct": 100,
            "goal_questions_min": 7,
            "next_level_questions_min": 5
        },
        "css_class": "profile-level-yellow"
    },
    "GREEN": {
        "label": "Behavioral Understanding",
        "description": "We have a strong understanding of your finances and behaviors",
        "requirements": {
            "core_completion_pct": 100,
            "goal_questions_min": 7,
            "next_level_questions_min": 5,
            "behavioral_questions_min": 3
        },
        "css_class": "profile-level-green"
    },
    "DARK_GREEN": {
        "label": "Complete Profile",
        "description": "We have a comprehensive understanding of your financial situation and behaviors",
        "requirements": {
            "core_completion_pct": 100,
            "goal_questions_min": 7,
            "next_level_questions_min": 15,
            "behavioral_questions_min": 7
        },
        "css_class": "profile-level-dark-green"
    }
}

class ProfileUnderstandingCalculator:
    """
    Calculates the qualitative understanding level of a profile based on 
    question types answered and completion metrics.
    """
    
    def __init__(self, understanding_levels=None):
        """
        Initialize the calculator with understanding levels.
        
        Args:
            understanding_levels (dict): Optional custom definition of understanding levels
        """
        self.understanding_levels = understanding_levels or PROFILE_UNDERSTANDING_LEVELS
        logging.basicConfig(level=logging.INFO)
    
    def calculate_level(self, profile: Dict[str, Any], completion_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the current understanding level for a profile based on 
        completion metrics and questions answered.
        
        Args:
            profile (Dict): The user profile
            completion_metrics (Dict): Metrics from question_service.get_profile_completion()
            
        Returns:
            Dict: The understanding level information
        """
        # Log start of calculation
        profile_id = profile.get('id', 'unknown')
        logging.info(f"Calculating understanding level for profile: {profile_id}")
        
        # Extract values needed for level calculation
        answered_questions = profile.get('answers', [])
        
        # Count specific question types
        goal_questions_count = len([a for a in answered_questions 
                                   if a.get('question_id', '').startswith('goals_')
                                   and not a.get('question_id', '').endswith('_insights')])
        
        next_level_questions_count = 0
        # Count all types of next-level questions using same pattern as in question_service
        for answer in answered_questions:
            q_id = answer.get('question_id', '')
            if q_id.startswith("next_level_") and not q_id.endswith("_insights"):
                next_level_questions_count += 1
            # Count dynamic/LLM generated questions
            elif (q_id.startswith("llm_next_level_") or 
                  q_id.startswith("gen_question_") or 
                  q_id.startswith("fallback_")) and not q_id.endswith("_insights"):
                next_level_questions_count += 1
        
        behavioral_questions_count = len([a for a in answered_questions 
                                         if a.get('question_id', '').startswith('behavioral_')
                                         and not a.get('question_id', '').endswith('_insights')])
        
        # Get core completion percentage from completion metrics
        core_completion_pct = completion_metrics.get('core', {}).get('overall', 0)
        
        # Log the factors being evaluated
        logging.info(f"Understanding Level Factors - Core: {core_completion_pct}%, " +
                     f"Goals: {goal_questions_count}, Next-Level: {next_level_questions_count}, " +
                     f"Behavioral: {behavioral_questions_count}")
        
        # Determine the highest level achieved
        current_level = None
        for level_id, level_info in self.understanding_levels.items():
            requirements = level_info.get('requirements', {})
            
            # Check if this level's requirements are met
            meets_requirements = True
            
            # Check core completion requirement
            if 'core_completion_pct' in requirements:
                required_core = requirements['core_completion_pct']
                if core_completion_pct < required_core:
                    meets_requirements = False
            
            # Check goal questions requirement
            if 'goal_questions_min' in requirements:
                required_goals = requirements['goal_questions_min']
                if goal_questions_count < required_goals:
                    meets_requirements = False
            
            # Check next-level questions requirement
            if 'next_level_questions_min' in requirements:
                required_next_level = requirements['next_level_questions_min']
                if next_level_questions_count < required_next_level:
                    meets_requirements = False
            
            # Check behavioral questions requirement
            if 'behavioral_questions_min' in requirements:
                required_behavioral = requirements['behavioral_questions_min']
                if behavioral_questions_count < required_behavioral:
                    meets_requirements = False
            
            # If all requirements are met, this is a candidate for the current level
            if meets_requirements:
                current_level = level_id
                logging.info(f"Profile {profile_id} meets requirements for level: {level_id}")
        
        # Ensure we always have at least RED level
        if not current_level:
            current_level = "RED"
            logging.info(f"Profile {profile_id} defaults to RED level")
        
        # Return the level information
        level_info = self.understanding_levels[current_level].copy()
        level_info['id'] = current_level
        
        # Add counts for debugging and display
        level_info['counts'] = {
            'goal_questions': goal_questions_count,
            'next_level_questions': next_level_questions_count,
            'behavioral_questions': behavioral_questions_count,
            'core_completion': core_completion_pct
        }
        
        # Add next level information for UI
        next_level = self._get_next_level(current_level, level_info['counts'])
        if next_level:
            level_info['next_level'] = next_level
            
        logging.info(f"Final understanding level for profile {profile_id}: {current_level}")
        return level_info
    
    def _get_next_level(self, current_level: str, current_counts: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """
        Determine the next level and what's needed to achieve it.
        
        Args:
            current_level (str): The current understanding level
            current_counts (Dict): Counts of questions by type
            
        Returns:
            Dict or None: Information about the next level, or None if at highest level
        """
        # Check if already at highest level
        if current_level == "DARK_GREEN":
            return None
            
        # Determine the next level
        levels = list(self.understanding_levels.keys())
        current_index = levels.index(current_level)
        next_level_id = levels[current_index + 1]
        next_level_info = self.understanding_levels[next_level_id]
        
        # Calculate what's needed for the next level
        needed = {
            'id': next_level_id,
            'label': next_level_info['label'],
            'requirements': []
        }
        
        requirements = next_level_info['requirements']
        
        # Check core completion
        if requirements.get('core_completion_pct', 0) > current_counts['core_completion']:
            needed['requirements'].append(
                f"Complete all core questions ({requirements['core_completion_pct']}%)"
            )
        
        # Check goal questions
        if requirements.get('goal_questions_min', 0) > current_counts['goal_questions']:
            remaining = requirements['goal_questions_min'] - current_counts['goal_questions']
            needed['requirements'].append(
                f"Answer {remaining} more goal question{'s' if remaining > 1 else ''}"
            )
        
        # Check next-level questions
        if requirements.get('next_level_questions_min', 0) > current_counts['next_level_questions']:
            remaining = requirements['next_level_questions_min'] - current_counts['next_level_questions']
            needed['requirements'].append(
                f"Answer {remaining} more next-level question{'s' if remaining > 1 else ''}"
            )
        
        # Check behavioral questions
        if requirements.get('behavioral_questions_min', 0) > current_counts['behavioral_questions']:
            remaining = requirements['behavioral_questions_min'] - current_counts['behavioral_questions']
            needed['requirements'].append(
                f"Answer {remaining} more behavioral question{'s' if remaining > 1 else ''}"
            )
        
        return needed