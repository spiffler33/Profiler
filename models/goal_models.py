import os
import json
import uuid
import logging
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Union, Tuple

class GoalCategory:
    """
    Model for predefined goal categories.
    """
    
    def __init__(self, id: int = None, name: str = "", description: str = "", 
                order: int = 0, is_foundation: bool = False):
        """
        Initialize a goal category.
        
        Args:
            id (int): Primary key (database ID)
            name (str): Category name (e.g., 'emergency_fund', 'retirement')
            description (str): Description of the goal category
            order (int): Display order for UI
            is_foundation (bool): Whether this is a foundation goal (emergency fund, insurance)
        """
        self.id = id
        self.name = name
        self.description = description
        self.order = order
        self.is_foundation = is_foundation
    
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
            "is_foundation": self.is_foundation
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
            is_foundation=data.get('is_foundation', False)
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
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            order=row['order_index'],
            is_foundation=bool(row['is_foundation'])
        )

class Goal:
    """
    Model for user financial goals.
    """
    
    def __init__(self, id: str = None, user_profile_id: str = "", category: str = "",
                title: str = "", target_amount: float = 0.0, timeframe: str = "",
                current_amount: float = 0.0, importance: str = "medium", 
                flexibility: str = "somewhat_flexible", notes: str = "",
                created_at: str = None, updated_at: str = None):
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
        """
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
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert goal to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation
        """
        return {
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
            "updated_at": self.updated_at
        }
    
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
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Goal':
        """
        Create a Goal from a database row.
        
        Args:
            row (sqlite3.Row): Database row
            
        Returns:
            Goal: New instance
        """
        return cls(
            id=row['id'],
            user_profile_id=row['user_profile_id'],
            category=row['category'],
            title=row['title'],
            target_amount=row['target_amount'],
            timeframe=row['timeframe'],
            current_amount=row['current_amount'],
            importance=row['importance'],
            flexibility=row['flexibility'],
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

class GoalManager:
    """
    Manager for handling goal operations.
    """
    
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