import os
import json
import uuid
import logging
import copy
from datetime import datetime

class ProfileManager:
    """
    Profile Management System for creating, loading, updating, and versioning user profiles.
    Ensures data persistence and maintains integrity throughout profile lifecycle.
    """
    
    def __init__(self, data_directory="/Users/coddiwomplers/Desktop/Python/Profiler4/data/profiles"):
        """
        Initialize the ProfileManager with data directory for storage.
        
        Args:
            data_directory (str): Path to store profile JSON files
        """
        self.data_directory = data_directory
        
        # Ensure the directory structure exists
        try:
            os.makedirs(data_directory, exist_ok=True)
            logging.info(f"Ensured profile directory exists: {data_directory}")
        except Exception as e:
            logging.error(f"Failed to create profile directory {data_directory}: {str(e)}")
            raise RuntimeError(f"Cannot initialize ProfileManager: {str(e)}")
            
        self.cache = {}  # Memory cache for profiles to ensure single instance
        logging.basicConfig(level=logging.INFO)
        
    def create_profile(self, name, email):
        """
        Create a new user profile with basic info.
        
        Args:
            name (str): User's name
            email (str): User's email address
            
        Returns:
            dict: Newly created profile object
        """
        profile_id = str(uuid.uuid4())
        profile = {
            "id": profile_id,
            "name": name,
            "email": email,
            "answers": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "versions": [
                {
                    "version_id": 1,
                    "timestamp": datetime.now().isoformat(),
                    "reason": "initial_creation"
                }
            ],
            "_debug_marker": f"created_{uuid.uuid4().hex[:6]}"
        }
        
        # Store in cache to maintain reference
        self.cache[profile_id] = profile
        
        # Save to file
        self._save_profile_to_file(profile)
        
        logging.info(f"Created new profile with ID: {profile_id}")
        return profile
    
    def get_profile(self, profile_id):
        """
        Load a profile by ID, prioritizing cache for reference consistency.
        
        Args:
            profile_id (str): Unique ID of the profile to load
            
        Returns:
            dict: Profile object or None if not found
        """
        # First check the cache for existing reference
        if profile_id in self.cache:
            logging.info(f"Retrieved profile {profile_id} from cache (id: {id(self.cache[profile_id])})")
            return self.cache[profile_id]
        
        # Otherwise load from file system
        file_path = os.path.join(self.data_directory, f"{profile_id}.json")
        try:
            with open(file_path, 'r') as file:
                profile = json.load(file)
                # Store in cache for future reference consistency
                self.cache[profile_id] = profile
                logging.info(f"Loaded profile {profile_id} from file (id: {id(profile)})")
                return profile
        except FileNotFoundError:
            logging.error(f"Profile {profile_id} not found")
            return None
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in profile {profile_id}")
            return None
    
    def save_profile(self, profile):
        """
        Update profile in both cache and file system.
        
        Args:
            profile (dict): Profile object to save
            
        Returns:
            dict: Updated profile object
        """
        # Verify we have a valid profile
        if not profile or 'id' not in profile:
            logging.error(f"Cannot save invalid profile: {profile}")
            raise ValueError("Invalid profile object")
        
        profile_id = profile['id']
        
        # Make sure this exact object reference is in our cache
        if profile_id in self.cache and id(profile) != id(self.cache[profile_id]):
            logging.warning(f"Profile reference mismatch: {id(profile)} vs {id(self.cache[profile_id])}")
            # Update our cache to use this reference, to maintain consistency
            self.cache[profile_id] = profile
        
        # Update timestamp
        profile['updated_at'] = datetime.now().isoformat()
        
        # Save to file
        self._save_profile_to_file(profile)
        
        # Ensure it's in our cache
        self.cache[profile_id] = profile
        
        logging.info(f"Saved profile {profile_id} (answers: {len(profile.get('answers', []))})")
        return profile
    
    def add_answer(self, profile, question_id, answer_value):
        """
        Add a new answer to a profile or update existing answer.
        
        Args:
            profile (dict): Profile to update
            question_id (str): ID of the question being answered
            answer_value: The answer value (could be string, number, boolean, etc.)
            
        Returns:
            dict: Updated profile with new answer
        """
        if not profile or 'id' not in profile:
            logging.error("Invalid profile for adding answer")
            raise ValueError("Invalid profile")
        
        # Ensure this is the cached reference
        profile_id = profile['id']
        if profile_id in self.cache and id(profile) != id(self.cache[profile_id]):
            logging.warning(f"Using different profile reference for {profile_id}")
            profile = self.cache[profile_id]  # Use cached reference
        
        # Ensure answers array exists
        if 'answers' not in profile:
            profile['answers'] = []
        
        # Check if this question already has an answer
        answer_updated = False
        for answer in profile['answers']:
            if answer['question_id'] == question_id:
                answer['answer'] = answer_value
                answer['timestamp'] = datetime.now().isoformat()
                answer_updated = True
                break
        
        # If not found, create new answer
        if not answer_updated:
            new_answer = {
                "id": str(uuid.uuid4()),
                "question_id": question_id,
                "answer": answer_value,
                "timestamp": datetime.now().isoformat()
            }
            profile['answers'].append(new_answer)
        
        # Save changes
        self.save_profile(profile)
        
        # Verify answers are still there
        cache_profile = self.cache[profile_id]
        logging.info(f"After add_answer: Profile has {len(cache_profile.get('answers', []))} answers")
        
        return profile
    
    def create_version(self, profile, reason):
        """
        Create a new version of the profile for tracking major changes.
        
        Args:
            profile (dict): Profile to version
            reason (str): Reason for creating new version
            
        Returns:
            dict: Updated profile with new version
        """
        if not profile or 'id' not in profile:
            logging.error("Invalid profile for versioning")
            raise ValueError("Invalid profile")
        
        # Ensure profile is the cached reference
        profile_id = profile['id']
        if profile_id in self.cache and id(profile) != id(self.cache[profile_id]):
            logging.warning(f"Using different profile reference for versioning {profile_id}")
            profile = self.cache[profile_id]
        
        # Initialize versions array if needed
        if 'versions' not in profile:
            profile['versions'] = []
        
        # Get latest version ID
        latest_version = max([v['version_id'] for v in profile['versions']]) if profile['versions'] else 0
        
        # Create new version entry
        new_version = {
            "version_id": latest_version + 1,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        }
        
        profile['versions'].append(new_version)
        
        # Save version snapshot
        try:
            # Construct and ensure full directory path existence
            profile_dir = os.path.join(self.data_directory, profile['id'])
            version_dir = os.path.join(profile_dir, 'versions')
            
            # Create directories if they don't exist
            os.makedirs(profile_dir, exist_ok=True)
            os.makedirs(version_dir, exist_ok=True)
            
            logging.info(f"Ensured version directory exists: {version_dir}")
            
            version_path = os.path.join(
                version_dir,
                f"v{new_version['version_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Create a deep copy for the version snapshot
            version_snapshot = copy.deepcopy(profile)
            
            # Write the version file
            json_string = json.dumps(version_snapshot, indent=2)
            
            with open(version_path, 'w') as file:
                file.write(json_string)
                
            logging.info(f"Saved version {new_version['version_id']} of profile {profile['id']}")
            
        except Exception as e:
            logging.error(f"Failed to save version snapshot: {str(e)}")
            # Continue without version snapshot - not critical
        
        # Save the updated profile
        self.save_profile(profile)
        
        return profile
    
    def _save_profile_to_file(self, profile):
        """
        Internal method to save profile to file with validation and backup.
        
        Args:
            profile (dict): Profile to save
        """
        profile_id = profile['id']
        
        # Ensure the profiles directory exists
        try:
            os.makedirs(self.data_directory, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to ensure profile directory exists: {str(e)}")
            raise ValueError(f"Cannot access or create profiles directory: {str(e)}")
            
        file_path = os.path.join(self.data_directory, f"{profile_id}.json")
        
        # Create backup if file exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.bak"
            try:
                with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
                logging.info(f"Created backup of profile {profile_id}")
            except Exception as e:
                logging.error(f"Failed to create backup of profile {profile_id}: {str(e)}")
        
        # Verify structure before saving
        if 'answers' not in profile:
            profile['answers'] = []
        
        # Ensure required fields are present
        required_fields = ['id', 'created_at', 'updated_at']
        for field in required_fields:
            if field not in profile:
                if field == 'created_at' or field == 'updated_at':
                    profile[field] = datetime.now().isoformat()
                else:
                    logging.error(f"Required field {field} missing from profile")
                    raise ValueError(f"Required field {field} missing from profile")
        
        # Check answers count before serialization
        answers_count = len(profile.get('answers', []))
        logging.info(f"Before save: Profile has {answers_count} answers")
        
        # Create a copy for serialization to avoid reference issues
        profile_copy = copy.deepcopy(profile)
        
        # Remove debug fields for serialization
        if '_object_id' in profile_copy:
            del profile_copy['_object_id']
        
        # Serialize and verify
        try:
            json_string = json.dumps(profile_copy, indent=2)
            # Test that we can deserialize it
            test_load = json.loads(json_string)
            if len(test_load.get('answers', [])) != answers_count:
                logging.error(f"Serialization issue: answers count mismatch {answers_count} vs {len(test_load.get('answers', []))}")
                raise ValueError("Serialization verification failed: answers count mismatch")
        except Exception as e:
            logging.error(f"Profile serialization error: {str(e)}")
            raise ValueError(f"Failed to serialize profile: {str(e)}")
        
        # Write to file with atomic operation if possible
        try:
            # Create parent directory if it doesn't exist (again, to be absolutely sure)
            parent_dir = os.path.dirname(file_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                logging.info(f"Created parent directory: {parent_dir}")
            
            # Write to temporary file first
            temp_path = f"{file_path}.tmp"
            with open(temp_path, 'w') as file:
                file.write(json_string)
                
            # Rename for atomic operation (works on most systems)
            os.replace(temp_path, file_path)
            logging.info(f"Successfully saved profile {profile_id} to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save profile {profile_id}: {str(e)}")
            
            # Try to restore from backup
            if os.path.exists(f"{file_path}.bak"):
                try:
                    os.replace(f"{file_path}.bak", file_path)
                    logging.info(f"Restored profile {profile_id} from backup")
                except Exception as restore_error:
                    logging.error(f"Failed to restore backup for {profile_id}: {str(restore_error)}")
            
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logging.info(f"Cleaned up temporary file {temp_path}")
            except Exception as cleanup_error:
                logging.error(f"Failed to clean up temporary file: {str(cleanup_error)}")
                
            raise ValueError(f"Failed to save profile: {str(e)}")
        
        # Verify saved file
        try:
            with open(file_path, 'r') as file:
                saved_profile = json.load(file)
                saved_answers_count = len(saved_profile.get('answers', []))
                if saved_answers_count != answers_count:
                    logging.error(f"Saved file verification failed: answers count mismatch {answers_count} vs {saved_answers_count}")
                else:
                    logging.info(f"Verified saved profile has {saved_answers_count} answers")
        except Exception as e:
            logging.error(f"Failed to verify saved profile {profile_id}: {str(e)}")
            # File was saved but verification failed, leave it as is