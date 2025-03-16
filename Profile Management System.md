# Profile Management System

## Overview

The Profile Management System is a critical component of the Financial Profiler project. It's responsible for creating, loading, updating, and versioning user profiles. This system ensures data persistence and maintains the integrity of user financial profiles throughout their lifecycle.

## Core Functionality

### 1. Profile Creation
- Generate unique profile IDs using UUID
- Initialize standard profile attributes
- Create empty answers array
- Set creation and update timestamps
- Store profiles as JSON files in a structured directory

### 2. Profile Loading
- Retrieve profiles by ID
- Handle missing profiles gracefully
- Validate profile structure on load
- Maintain consistent object references
- Track profile object IDs for debugging

### 3. Answer Management
- Add new answers to profiles
- Update existing answers
- Preserve answer history
- Maintain answer uniqueness
- Track questions answered by ID

### 4. Profile Serialization
- Convert profile objects to JSON
- Handle complex data types
- Ensure data consistency
- Implement serialization verification
- Create backups before saving

### 5. Profile Versioning
- Maintain version history for profiles
- Create new versions for major life events
- Track changes between versions
- Allow comparison of profile evolution
- Support rollback if needed

## Profile Structure

```json
{
  "id": "unique-profile-id",
  "name": "User Name",
  "email": "user@example.com",
  "age": null,
  "answers": [
    {
      "id": "answer-uuid",
      "question_id": "demographics_age",
      "answer": "32",
      "timestamp": "2025-03-11T16:56:07.479371"
    }
  ],
  "created_at": "2025-03-11T16:56:05.319",
  "updated_at": "2025-03-11T16:56:07.479",
  "versions": [
    {
      "version_id": 1,
      "timestamp": "2025-03-11T16:56:05.319",
      "reason": "initial_creation"
    }
  ],
  "_debug_marker": "created_abc123" // For development only
}
```

## Implementation Guidelines

### File Structure
```
data/
  profiles/
    {profile-id}.json
    {profile-id}/
      versions/
        v1_{timestamp}.json
        v2_{timestamp}.json
```

### Error Handling
1. Implement robust error handling for all file operations
2. Create backup mechanisms before modifying profiles
3. Verify successful saves by reading back from disk
4. Add recovery mechanisms for corrupted profiles
5. Log all critical profile operations for debugging

### Object Reference Management
1. Maintain a single instance of profile in memory
2. Pass profile objects by reference, not by value
3. Use defensive copying for answers array when needed
4. Track object IDs throughout operations
5. Verify object identity before and after operations

### Concurrency Considerations
1. Implement file locking for concurrent access
2. Use atomic operations where possible
3. Handle race conditions in profile updates
4. Implement optimistic locking mechanism
5. Log conflicting operations for manual resolution

## ProfileManager Class Design

```python
class ProfileManager:
    def __init__(self, data_directory="data/profiles"):
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)

    def create_profile(self, name, email):
        """Create a new user profile with basic info."""
        profile_id = str(uuid.uuid4())
        profile = {
            "id": profile_id,
            "name": name,
            "email": email,
            "age": None,
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
            "_debug_marker": f"created_{uuid.uuid4().hex[:8]}"
        }
        self.save_profile(profile)
        return profile

    def get_profile(self, profile_id):
        """Load a profile from storage."""
        file_path = os.path.join(self.data_directory, f"{profile_id}.json")
        try:
            with open(file_path, 'r') as file:
                profile = json.load(file)
                # Add tracking for debugging
                profile['_object_id'] = id(profile)
                return profile
        except FileNotFoundError:
            logging.error(f"Profile {profile_id} not found")
            return None
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in profile {profile_id}")
            return None

    def save_profile(self, profile):
        """Save profile to storage."""
        # Log initial state for debugging
        logging.info(f"Initial profile object ID: {id(profile)}")
        logging.info(f"Initial answers count: {len(profile.get('answers', []))}")

        # Create backup of answers
        answers_backup = copy.deepcopy(profile.get('answers', []))

        file_path = os.path.join(self.data_directory, f"{profile['id']}.json")
        profile['updated_at'] = datetime.now().isoformat()

        # Verify structure before saving
        if 'answers' not in profile:
            profile['answers'] = []

        # Serialize and verify
        try:
            json_string = json.dumps(profile, indent=2)
            # Test deserialization
            test_load = json.loads(json_string)
            assert len(test_load.get('answers', [])) == len(profile.get('answers', []))
        except Exception as e:
            # Restore from backup if serialization fails
            profile['answers'] = answers_backup
            logging.error(f"Serialization error: {str(e)}")
            raise

        # Write to file
        with open(file_path, 'w') as file:
            file.write(json_string)

        # Verify saved file
        saved_profile = self.get_profile(profile['id'])
        logging.info(f"VERIFICATION: Saved profile has {len(saved_profile.get('answers', []))} answers")

        return profile

    def create_version(self, profile, reason):
        """Create a new version of the profile."""
        if 'versions' not in profile:
            profile['versions'] = []

        latest_version = max([v['version_id'] for v in profile['versions']]) if profile['versions'] else 0

        new_version = {
            "version_id": latest_version + 1,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        }

        profile['versions'].append(new_version)

        # Save version snapshot
        version_dir = os.path.join(self.data_directory, profile['id'], 'versions')
        os.makedirs(version_dir, exist_ok=True)

        version_path = os.path.join(
            version_dir,
            f"v{new_version['version_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(version_path, 'w') as file:
            json.dump(profile, file, indent=2)

        return profile
```

## Best Practices for Working with Profiles

1. **Single Responsibility**: Each method should do one thing well
2. **Defensive Programming**: Always validate before modifying
3. **Backup Mechanism**: Create backups before critical operations
4. **Verification**: Verify operations by reading back saved data
5. **Explicit References**: Track object references explicitly
6. **Debugging Support**: Add markers and logging for development
7. **Complete Transactions**: Ensure operations complete fully or rollback
8. **Error Recovery**: Have mechanisms to recover from failures
9. **Version Control**: Maintain profile history for auditing
10. **Clear Ownership**: Establish clear ownership of profile objects

## Troubleshooting Common Issues

### Profile Loading Issues
- Verify file paths and permissions
- Check for valid JSON format
- Ensure profile ID is correct
- Validate directory structure exists

### Answer Saving Problems
- Verify profile is not None before use
- Check object references match
- Ensure answers array exists
- Verify JSON serializable data types
- Confirm filesystem has write permissions

### Version Management Issues
- Check version directory structure
- Verify version IDs are sequential
- Ensure timestamps are in ISO format
- Validate reason codes are meaningful

### Object Reference Problems
- Track object IDs at key points
- Verify same profile instance is used throughout
- Avoid creating new dictionaries instead of modifying existing
- Use is operator to check identity, not equality

---

This document outlines the Profile Management System for the Financial Profiler project. It provides guidelines for implementation, error handling, and best practices for maintaining data integrity throughout the profile lifecycle.
