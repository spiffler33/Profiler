# Implementation Guide

## Project Structure

```
project_root/
├── app.py                   # Main entry point (Flask)
├── config.py                # Configurations, environment variables
├── requirements.txt         # Dependencies
├── README.md                # Project documentation
├── /data                    # Data storage directory
│   └── /profiles            # User profile storage
├── /models
│   ├── profile_manager.py   # Profile management functionality
│   └── question_repository.py # Question definitions and access
├── /services
│   ├── question_service.py  # Core question flow logic
│   └── llm_service.py       # LLM integration (future)
├── /static                  # Static assets
│   ├── /css                 # Stylesheets
│   └── /js                  # JavaScript files
├── /templates               # HTML templates
└── /tests                   # Unit and integration tests
```

## Core Components Implementation

### 1. Profile Manager (`models/profile_manager.py`)

The Profile Manager is responsible for all profile operations including:

- **Creating new profiles** with unique IDs and standard structure
- **Loading profiles** from storage with proper validation
- **Saving profiles** with verification and backup mechanisms
- **Tracking object references** for debugging and data integrity
- **Version management** for profile history

Key implementation considerations:
- Use extensive logging for debugging
- Create backups before critical operations
- Verify saved data by reading it back
- Track object IDs to ensure consistent references
- Implement robust error handling

### 2. Question Repository (`models/question_repository.py`)

This component manages the question definitions:

- Loads questions from JSON configuration
- Organizes questions by type (core, next-level, behavioral)
- Provides lookup methods by ID, category, and dependencies
- Tracks metadata like completion requirements and validation rules

Implementation considerations:
- Structure questions with consistent schema
- Include validation rules within question definitions
- Organize by categories for better flow management
- Include help text and UI hints in the definitions

### 3. Question Service (`services/question_service.py`)

The Question Service handles the core logic for determining question flow:

- **Saves answers** to profiles with proper validation
- **Determines the next question** based on profile state
- **Calculates completion percentages** by category and tier
- **Manages progression** through question tiers

Key algorithm considerations:
- Complete core questions before moving to next-level
- Group questions by category for organized progression
- Track completion percentages to guide the flow
- Handle conditional questions based on previous answers

### 4. Flask Application (`app.py`)

The main application integrates all components:

- Initializes services and repositories
- Defines routes for profile creation and questions
- Manages session data for user tracking
- Handles answer submission and profile updates
- Renders templates with appropriate context

Implementation considerations:
- Maintain detailed logging
- Track object references during profile operations
- Implement proper error handling
- Use clear session management

## HTML Templates Structure

### 1. Landing Page (`templates/index.html`)

A simple welcome page that introduces the financial profiler and provides a button to create a new profile.

### 2. Profile Creation (`templates/profile_create.html`)

Collects basic user information (name, email) to initialize a new profile.

### 3. Question Interface (`templates/questions.html`)

The main interface for presenting questions and collecting answers, including:
- Progress tracking bars
- Category badges
- Dynamic form elements based on question type
- Help text and explanations
- Navigation controls

### 4. Profile Complete (`templates/profile_complete.html`)

A summary page showing profile completion and category breakdown.

## CSS Structure

### Main Stylesheet (`static/css/style.css`)

Contains base styles, typography, buttons, forms, and layout components.

### Chat Interface (`static/css/chat.css`)

Specialized styles for the question interface, including:
- Question containers
- Progress indicators
- Input styling for different question types
- Animation and transitions

## JavaScript Functionality (`static/js/main.js`)

Client-side functionality:
- Dynamic input handling (sliders, selects)
- Form validation
- Progress visualization
- Smooth transitions between questions

## Database Design

### Profile Storage

Profiles are stored as JSON files with the following structure:

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
  ]
}
```

### Question Definition Structure

Questions are defined with a consistent schema:

```json
{
  "id": "unique_question_id",
  "text": "Question text",
  "type": "core|next_level|behavioral",
  "category": "demographics|financial_basics|assets_and_debts|special_cases",
  "input_type": "text|number|select|slider|radio",
  "options": ["Option1", "Option2"],
  "min": 0,
  "max": 100,
  "step": 1,
  "required": true,
  "order": 1,
  "help_text": "Explanation of why we ask this question",
  "validation": {
    "type": "number|string|boolean",
    "min": 0,
    "max": 100
  }
}
```

## Deployment Guidelines

1. **Development Environment**
   - Use virtual environments for dependency management
   - Set DEBUG=True for development
   - Use SQLite for local testing

2. **Testing Process**
   - Write unit tests for core components
   - Focus on profile management and question flow
   - Test persistence across server restarts

3. **Production Deployment**
   - Set appropriate environment variables
   - Configure proper logging
   - Set up backup mechanisms for profile data
   - Use a production-grade server (Gunicorn, uWSGI)

## Error Handling Strategy

1. **Profile Management Errors**
   - Log detailed information
   - Create backup files before operations
   - Implement automatic recovery mechanisms

2. **Question Flow Errors**
   - Default to core questions if flow determination fails
   - Maintain session state for recovery
   - Prevent duplicate questions

3. **User Input Errors**
   - Client and server-side validation
   - Clear error messages
   - Allow correction without progress loss

## Performance Considerations

1. **Profile Loading**
   - Cache frequently accessed profiles
   - Optimize JSON parsing
   - Load only necessary data

2. **Question Determination**
   - Optimize category and completion calculations
   - Cache results where appropriate
   - Prioritize responsiveness

3. **File Operations**
   - Use atomic writes for data integrity
   - Implement proper file locking
   - Handle concurrent access

## Security Considerations

1. **User Data Protection**
   - Sanitize all inputs
   - Validate profile IDs against session data
   - Prevent unauthorized profile access

2. **Session Management**
   - Use secure session cookies
   - Implement proper timeout mechanisms
   - Validate user identity for profile access

3. **Data Storage**
   - Secure file permissions
   - Consider encryption for sensitive data
   - Regular backups

## Future Enhancements

1. **LLM Integration**
   - Add the `llm_service.py` module for AI integration
   - Implement sentiment analysis for behavioral questions
   - Use NLP for open-ended question processing

2. **Advanced Analytics**
   - Implement profile comparison features
   - Track historical changes
   - Generate insights based on answers

3. **Expanded Question Sets**
   - Add more behavioral questions
   - Implement conditional question paths
   - Develop life event update workflows

---

This implementation guide provides a structured approach to building the Financial Profiler system. It focuses on robust data management, logical question flow, and an intuitive user experience while setting the foundation for future enhancements.
