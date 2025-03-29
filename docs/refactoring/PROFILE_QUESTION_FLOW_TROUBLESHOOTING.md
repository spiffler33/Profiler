# Profile Creation and Question Flow Troubleshooting Guide

This document outlines a systematic approach to identifying and fixing issues with the profile creation process and the question flow system.

## 1. Profile Creation Flow Issues

### Key Areas to Check
- **URL Endpoint Consistency**: 
  - Ensure client-side (`ProfileCreationWizard.jsx`) and server-side (`app.py`) endpoints match
  - Check for any duplicate `/api/v2` prefixes in URLs
  - Verify request methods (GET/POST) are consistent

- **Form Data Validation**:
  - Verify client-side validation in `ProfileCreationWizard.jsx`
  - Check server-side validation in `app.py` (`create_profile` route)
  - Ensure consistent error message formatting

- **Response Handling**:
  - Check JSON response structure for success and error cases
  - Verify client-side handling of API responses
  - Ensure proper redirect after successful profile creation

- **Session Management**:
  - Confirm profile_id is correctly stored in session
  - Check session persistence across requests
  - Verify session retrieval in question flow

## 2. Question Flow Mechanics

### Key Areas to Check
- **Question Retrieval**:
  - Trace the `get_next_question` method execution 
  - Check filtering of answered vs. unanswered questions
  - Verify question prioritization logic

- **Answer Submission**:
  - Trace the `submit_answer` route execution
  - Check proper storage of answers in the profile
  - Verify redirection includes profile context

- **Progress Tracking**:
  - Examine `get_profile_completion` implementation
  - Verify completion data formatting for templates
  - Check category-based completion calculations

- **Session Persistence**:
  - Ensure profile_id is maintained during redirects
  - Check URL parameter handling for profile_id
  - Verify session fallbacks when URL parameters are missing

## 3. Data Structure Compatibility Issues

### Key Areas to Check
- **Object Format Compatibility**:
  - Compare expected vs. actual data formats in:
    - Question objects
    - Profile objects
    - Completion metrics
    - Answer data objects

- **Required Template Fields**:
  - Check template requirements for:
    - `completion.by_category` attributes
    - Question properties (`is_dynamic`, `category`, etc.)
    - Answer formatting for display

- **Default Values**:
  - Ensure proper defaults for:
    - Missing question attributes
    - Incomplete profile data
    - Empty completion metrics
    - Missing answer properties

## 4. Authentication and Authorization

### Key Areas to Check
- **Session Requirements**:
  - Check if routes require authentication
  - Verify session handling for public vs. restricted routes

- **Error Handling**:
  - Ensure proper error messages for missing authentication
  - Check redirect behavior for unauthorized access

## 5. Service Initialization and Method Implementation

### Key Areas to Check
- **Required Dependencies**:
  - Verify all services receive required dependencies
  - Check `QuestionService` initialization with `QuestionRepository` and `ProfileManager`
  - Examine service fallbacks for missing dependencies

- **Method Implementation**:
  - Check that all services implement the methods expected by routes
  - Common error: `AttributeError: 'ServiceName' object has no attribute 'method_name'`
  - Check `GoalService` for missing methods like `get_goals_for_profile`
  - Verify interfaces used in the codebase match actual implementations

- **Error Handling**:
  - Ensure proper error handling during service initialization
  - Check graceful degradation when services fail to initialize
  - Add fallbacks for missing methods

## 6. Database Interactions

### Key Areas to Check
- **Profile Storage**:
  - Trace profile creation and storage in `database_profile_manager.py`
  - Verify proper JSON serialization/deserialization
  - Check error handling for database operations

- **Answer Storage**:
  - Trace answer submission flow from form to database
  - Verify answer data structure in profile document
  - Check for proper timestamps and metadata

## Testing Strategy

### Methodical Approach
1. **Test Profile Creation**:
   - Create a new profile with minimal data
   - Verify database entry created
   - Check session contains correct profile_id

2. **Test First Question**:
   - Load questions page with new profile
   - Verify first question appears
   - Check completion metrics are initialized properly

3. **Test Answer Submission**:
   - Submit answer to first question
   - Verify answer is stored in profile
   - Check redirection maintains profile context

4. **Test Question Progression**:
   - Verify next question differs from first
   - Check completion metrics increase
   - Test multiple question/answer cycles

### Debugging Tools
- **Server Logs**: Monitor app logs for errors and request flow
- **Browser Network Tab**: Check request/response cycles
- **Browser Console**: Look for JavaScript errors
- **Database Inspection**: Check database state directly

## Common Fixes

1. **Endpoint Mismatches**:
   - Update client-side API endpoint URLs
   - Ensure proper URL prefix handling
   - Check for hardcoded vs. configuration-driven URLs

2. **Missing Dependencies**:
   - Add proper dependency injection for services
   - Create fallbacks for missing dependencies
   - Log warnings for degraded functionality

3. **Missing Service Methods**:
   - Implement missing methods in service classes
   - Add fallback implementations that return reasonable defaults
   - Add try/catch blocks in routes to handle missing methods
   - Example error: `AttributeError: 'GoalService' object has no attribute 'get_goals_for_profile'`

4. **Data Format Issues**:
   - Add adapter functions to format data for templates
   - Ensure consistent data structures
   - Add default values for missing attributes

5. **Session Management**:
   - Maintain context in URL parameters when possible
   - Use session as fallback for context
   - Check and update session on each request

6. **Template Variables**:
   - Check template variable usage
   - Provide default values for all variables
   - Format data structures to match template expectations

## Implementation Checklist

- [x] Fix ApiService URL endpoint for profile creation (implemented at line 515 in ApiService.js)
- [x] Update `/questions` route to handle URL parameters (implemented in questions route at line 758-763)
- [x] Fix `/submit_answer` route to include profile_id in redirects (implemented at line 902)
- [x] Format completion data for template compatibility (implemented at line 812-826)
- [x] Add default values for missing question attributes (implemented at line 786-797)
- [x] Fix QuestionService initialization with required dependencies (implemented at line 774-775)
- [x] Format answered questions for display in template (implemented at line 834-856)
- [x] Fix template Jinja2 syntax issues in dynamic_question_indicator.html (using proper {# #} for comments)
- [x] Add missing methods to GoalService - get_goals_for_profile added today
- [x] Add error handling for potential AttributeError in service calls - added today
- [x] Add fallbacks in routes for missing service methods - added today
- [x] Enhanced fallbacks in goal-related routes to include direct GoalManager access if needed - added today
- [x] Added comprehensive error handling to create_goal and edit_goal routes - added today
- [x] Added proper error handling to simulation endpoint - added today
- [x] Implemented automated testing for profile creation and question flow cycle - added today
- [x] Implemented automated testing for goal display and management flow - added today

## Progress Tracking

| Issue | Status | Solution | Fixed In | Date Fixed |
|-------|--------|----------|----------|------------|
| ApiService missing createProfile | Fixed | Added createProfile method | ApiService.js (line 515) | Before today |
| Duplicate /api/v2 in endpoint URL | Fixed | Used relative endpoint path | ApiService.js (line 62) | Before today |
| QuestionService missing dependencies | Fixed | Added proper initialization | app.py (line 774-775) | Before today |
| Template expected by_category field | Fixed | Formatted completion data | app.py (line 812-826) | Before today |
| Jinja2 syntax error in template | Fixed | Using {# #} for comments | dynamic_question_indicator.html | Before today |
| Missing profile_id in redirects | Fixed | Added profile_id param to redirect | app.py (line 902) | Before today |
| GoalService missing get_goals_for_profile | Fixed | Added alias method that calls get_profile_goals | services/goal_service.py | 3/28/2025 |
| Potential AttributeError in service calls | Fixed | Added try/except with fallbacks in list_goals and admin_profile_detail routes | app.py | 3/28/2025 |
| Enhanced fallbacks in goal-related routes | Fixed | Added multi-level fallbacks including direct GoalManager access for profile goals | app.py (lines 935-942, 1114-1121) | 3/28/2025 |
| Error handling in create_goal | Fixed | Added robust error handling and result validation | app.py (lines 985-998) | 3/28/2025 |
| Error handling in edit_goal | Fixed | Added try/except blocks for get_goal and update_goal | app.py (lines 1015-1044) | 3/28/2025 |
| Error handling in simulation endpoint | Fixed | Added try/except for get_goal in test_simulation_endpoint | app.py (lines 619-631) | 3/28/2025 |
| Profile creation and question flow testing | Fixed | Added automated test endpoint for profile creation and question flow | app.py (lines 1059-1227) | 3/28/2025 |
| Goal management flow testing | Fixed | Added comprehensive test endpoint for goal management process | app.py (lines 1229-1461) | 3/28/2025 |
| Ongoing tasks | Completed | All tasks in troubleshooting guide implemented | - | 3/28/2025 |

## Implementation Summary

All identified issues in the profile creation and question flow system have been fixed. Key improvements include:

1. **Added Robust Error Handling**:
   - Added try/except blocks around all service method calls to handle AttributeError and other exceptions gracefully
   - Implemented multi-level fallbacks for critical API calls including direct database access
   - Added comprehensive error messages and logging

2. **Fixed Method Compatibility**:
   - Added alias method `get_goals_for_profile` to ensure backward compatibility
   - Ensured service methods have consistent return values with fallback to empty defaults

3. **Added Default Values**:
   - Ensured questions have all required attributes with default values
   - Provided fallbacks for completion metrics when values are missing

4. **Improved Session Management**:
   - Added proper handling of profile_id in URL parameters
   - Ensured session is updated when profile_id is provided in URL

5. **Automated Testing**:
   - Created test routes that verify the entire profile creation and question flow
   - Implemented comprehensive testing for goal creation, retrieval, updating, and listing
   - Built detailed error reporting for test results

These changes should make the system more robust and resilient to errors. Any future issues can be diagnosed using the test routes at:
- `/api/v2/test/profile_question_flow` - Tests profile creation and question flow
- `/api/v2/test/goal_management_flow` - Tests goal management functionality