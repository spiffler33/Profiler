# Profiler4: Financial Goal Planning System

A sophisticated financial profiler system that captures user financial information through a multi-tiered question approach and provides probabilistic goal planning. The profiler creates comprehensive user profiles combining objective financial data and subjective behavioral preferences to enable personalized financial guidance.

## Standardized Goal Types

The application uses the following consistent goal types across all components:

1. **retirement/early_retirement**: Saving for retirement or early financial independence
2. **education**: Saving for education expenses (with 80C tax benefits in Indian context)
3. **emergency_fund**: Building liquid funds for unexpected expenses
4. **home_purchase**: Saving for property acquisition (with 80C tax benefits in Indian context)
5. **debt_repayment**: Paying off outstanding debts
6. **wedding**: Saving for wedding expenses
7. **charitable_giving**: Donations and philanthropy (with 80G tax benefits in Indian context)
8. **legacy_planning**: Planning for wealth transfer
9. **tax_optimization**: Investments specifically for tax efficiency (80C, 80D, 80G benefits)
10. **custom**: User-defined goals that don't fit standard categories

## Goal Categories Hierarchy

Goals are organized in a hierarchical structure with six predefined levels:

1. **Security** (Level 1): emergency_fund, tax_optimization, insurance-related
2. **Essential** (Level 2): home_purchase, education, debt_repayment
3. **Retirement** (Level 3): retirement, early_retirement
4. **Lifestyle** (Level 4): wedding, travel, vehicle, etc.
5. **Legacy** (Level 5): legacy_planning, charitable_giving
6. **Custom** (Level 6): User-defined goals

## Features

- **Multi-tier Question Flow**: Core questions → Next-level AI-generated questions
- **Profile Management**: Create, update and version user profiles
- **Analytics Dashboard**: Analyze financial profiles with metrics and visualizations
- **LLM Integration**: AI-powered question generation and response analysis
- **SQLite Database**: Robust data persistence with transaction support
- **Goal Management**: Set and track financial goals with enhanced categorization
- **API Versioning**: Support for backward compatibility and progressive enhancement

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- OpenAI API key (for AI features)

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/financial-profiler.git
cd financial-profiler
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables

Create a `.env` file in the project root with the following variables:

```
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=True
SECRET_KEY=your_secret_key_here
```

Alternatively, you can set these environment variables directly in your system.

### API Key Setup

The Financial Profiler uses OpenAI's API for:
- Generating personalized follow-up questions
- Analyzing free-text responses
- Extracting structured insights from unstructured data

To enable these features, you need to:

1. Create an account at [OpenAI](https://platform.openai.com/)
2. Generate an API key in your account dashboard
3. Set the `OPENAI_API_KEY` environment variable or add it to the `.env` file

Without an API key, the application will still function, but AI features will be disabled. The system will use default follow-up questions instead of personalized ones.

### Running the Application

```bash
python app.py
```

The application will be available at http://127.0.0.1:5000/

### Running Tests

```bash
# Run all tests
pytest

# Run tests by category
pytest tests/frontend/  # Run frontend tests
pytest tests/models/    # Run model tests
pytest tests/api/       # Run API tests

# Run with verbose output
pytest -v
```

### Admin Dashboard Access

To access the admin dashboard:
1. Navigate to http://127.0.0.1:5000/admin
2. Log in with the default credentials:
   - Username: admin
   - Password: admin

You can change these credentials by setting the `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables.

## Usage

1. Create a new profile by providing basic information
2. Answer core financial questions
3. The system will automatically generate personalized follow-up questions
4. View your financial profile analytics after completing the questionnaire

## Project Structure

```
project_root/
├── app.py                   # Main entry point (Flask)
├── config.py                # Configuration management
├── requirements.txt         # Dependencies
├── README.md                # Project documentation
├── .env                     # Environment variables (create this file)
├── Procfile                 # For web deployment
├── data/                    # Data storage directory
│   ├── profiles.db          # Profiles SQLite database
│   ├── parameters.db        # Parameters SQLite database
│   ├── profiles/            # JSON profile data
│   ├── backups/             # Database backups
│   └── question_logs/       # Question logs by session
├── docs/                    # Documentation
│   ├── analysis/            # Analysis documents
│   ├── goal_system/         # Goal system documentation
│   ├── migrations/          # Migration guides
│   ├── overview/            # System overview documents
│   ├── parameters/          # Parameter documentation
│   ├── strategy_enhancements/ # Strategy enhancement documentation
│   └── test_results/        # Test summaries and results
├── logs/                    # Log files
├── migrations/              # Migration scripts
│   ├── scripts/             # Core migration logic
│   └── runners/             # Migration runner scripts
├── models/                  # Core business logic
│   ├── funding_strategies/  # Goal funding strategy implementations
│   ├── goal_calculators/    # Goal calculator implementations
│   ├── backups/             # Code backups
│   ├── database_profile_manager.py
│   ├── financial_parameters.py
│   ├── financial_projection.py
│   ├── funding_strategy.py
│   ├── goal_calculator.py
│   ├── goal_models.py
│   ├── life_event_registry.py
│   ├── parameter_extensions.py
│   ├── profile_manager.py
│   ├── profile_understanding.py
│   ├── question_repository.py
│   └── rebalancing_strategy_integration.py
├── reports/                 # Generated reports
├── services/                # Service layer
│   ├── financial_parameter_service.py
│   ├── goal_service.py
│   ├── llm_service.py                # LLM integration
│   ├── profile_analytics_service.py  # Profile analysis
│   └── question_service.py           # Core question flow logic
├── static/                  # Static assets
│   ├── css/                 # Stylesheets
│   └── js/                  # JavaScript files
├── templates/               # HTML templates
│   └── admin/               # Admin dashboard templates
├── tests/                   # Automated tests
│   ├── api/                 # API tests
│   ├── calculators/         # Calculator tests
│   ├── frontend/            # Frontend tests
│   ├── integration/         # Integration tests
│   ├── migrations/          # Migration tests
│   ├── models/              # Model tests
│   ├── parameters/          # Parameter tests
│   ├── projections/         # Projection tests
│   ├── services/            # Service layer tests
│   ├── strategies/          # Strategy tests
│   └── utils/               # Utility tests
└── utils/                   # Utility scripts
```

## API Documentation

### Parameter Management System

The Financial Profiler uses a centralized parameter management system for all financial constants, market assumptions, tax rules, and other configuration values. The system is accessible through multiple interfaces:

#### 1. Web Admin Interface

The web admin interface is accessible at `/admin/parameters` for authorized administrators. It provides visual parameter browsing, editing, and historical tracking.

#### 2. REST API

For programmatic access, a comprehensive RESTful API is available:

```
GET /api/v2/parameters?group=market.equity
GET /api/v2/parameters/{parameter_path}
PUT /api/v2/parameters/{parameter_path}
POST /api/v2/parameters
POST /api/v2/parameters/bulk
GET /api/v2/parameters/history/{parameter_path}
DELETE /api/v2/parameters/{parameter_path}
```

All parameter API endpoints require HTTP Basic Authentication.

#### 3. Command-line Tool

For automation and DevOps integration, use the `manage_parameters.py` script:

```bash
# List parameters 
python manage_parameters.py list --group market.equity

# Set a parameter
python manage_parameters.py set market.equity.equity_large_cap 13.0

# Import/export parameters
python manage_parameters.py import parameters.json
python manage_parameters.py export --output parameters.json
```

For full documentation on parameter management, see the [Parameter Management Guide](docs/parameters/PARAMETER_MANAGEMENT_GUIDE.md).

### Goal Management API

The goal management API provides endpoints for creating, retrieving, updating, and deleting financial goals.

#### API Versioning

The API supports versioning through:

1. URL path prefixes (e.g., `/api/v2/goals`)
2. Request headers (`API-Version` header)

When using the header method, include the following header in your requests:
```
API-Version: v2
```

If no version is specified, the API defaults to v1 for backward compatibility.

#### Standard Response Format (v2)

All v2 API responses follow this standard format:

```json
{
  "version": "v2",
  "metadata": {
    "timestamp": "2025-03-19T13:45:30.123456",
    ...additional metadata fields specific to the endpoint
  },
  "data": {
    ...response data
  }
}
```

#### Endpoints

##### Core Goal Operations

**GET /api/v2/goals**
- Description: Get all goals for the current user profile with enhanced fields
- Response: Array of goal objects with enhanced fields
- Query Parameters: None
- Authentication: Session-based

**GET /api/v2/goals/:goal_id**
- Description: Get a specific goal with enhanced fields
- Response: Goal object with enhanced fields
- Path Parameters: `goal_id` - ID of the goal
- Authentication: Session-based

**POST /api/v2/goals**
- Description: Create a new goal with enhanced fields
- Request Body: Goal object (JSON)
- Response: Created goal object with enhanced fields
- Authentication: Session-based

**PUT /api/v2/goals/:goal_id**
- Description: Update a goal with enhanced fields
- Request Body: Goal object (JSON)
- Response: Updated goal object with enhanced fields
- Path Parameters: `goal_id` - ID of the goal
- Authentication: Session-based

**DELETE /api/v2/goals/:goal_id**
- Description: Delete a goal
- Response: Success status
- Path Parameters: `goal_id` - ID of the goal
- Authentication: Session-based

##### Category-Specific Operations

**GET /api/v2/goal-categories**
- Description: Get all goal categories
- Response: Array of category objects
- Query Parameters:
  - `include_subcategories` (boolean, default: true) - Whether to include subcategories
- Authentication: Session-based

**GET /api/v2/goal-categories/:hierarchy_level**
- Description: Get goals by hierarchy level
- Response: Array of goal objects with the specified hierarchy level
- Path Parameters: `hierarchy_level` (integer) - Hierarchy level (1-6)
- Authentication: Session-based

**GET /api/v2/goals/category/:category_name**
- Description: Get goals by category name
- Response: Array of goal objects with the specified category
- Path Parameters: `category_name` - Name of the category
- Authentication: Session-based

##### Enhanced Goal Operations

**GET /api/v2/goals/simulation/:goal_id**
- Description: Simulate goal progress over time
- Response: Goal projection data
- Path Parameters: `goal_id` - ID of the goal
- Query Parameters:
  - `years` (integer, default: 5) - Number of years to simulate
- Authentication: Session-based

**GET /api/v2/goals/funding-strategy/:goal_id**
- Description: Get detailed funding strategy for a goal
- Response: Funding strategy object
- Path Parameters: `goal_id` - ID of the goal
- Authentication: Session-based

##### Legacy Endpoints (v1)

**GET /api/goals/priority**
- Description: Get prioritized goals for the current profile
- Response: Array of prioritized goals
- Authentication: Session-based

**GET /api/goals/allocation_data/:goal_id**
- Description: Get asset allocation data for a goal
- Response: Asset allocation data formatted for chart display
- Path Parameters: `goal_id` - ID of the goal
- Authentication: Session-based

**GET /api/monthly_expenses**
- Description: Get monthly expenses for the current profile
- Response: Monthly expenses value
- Authentication: Session-based

### Goal Model

#### Standard Goal Fields

```json
{
  "id": "string",
  "user_profile_id": "string",
  "category": "string",
  "title": "string",
  "target_amount": "number",
  "timeframe": "string (ISO date)",
  "current_amount": "number",
  "importance": "string (high|medium|low)",
  "flexibility": "string (fixed|somewhat_flexible|very_flexible)",
  "notes": "string",
  "created_at": "string (ISO date)",
  "updated_at": "string (ISO date)"
}
```

#### Enhanced Goal Fields (v2)

```json
{
  ...standard goal fields,
  "current_progress": "number (0-100)",
  "priority_score": "number",
  "additional_funding_sources": "string",
  "goal_success_probability": "number (0-100)",
  "adjustments_required": "boolean",
  "funding_strategy": "string (JSON)"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | OpenAI API key for LLM features | None (LLM disabled) |
| OPENAI_MODEL | OpenAI model to use | gpt-4o |
| DEBUG | Enable debug mode | False |
| SECRET_KEY | Flask secret key | Random generated key |
| DB_PATH | Path to SQLite database | data/profiles.db |
| ADMIN_USERNAME | Admin dashboard username | admin |
| ADMIN_PASSWORD | Admin dashboard password | admin |

## License

[MIT License](LICENSE)