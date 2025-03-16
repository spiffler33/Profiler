# Financial Profiler

A sophisticated financial profiler system that captures user financial information through a multi-tiered question approach. The profiler creates comprehensive user profiles combining objective financial data and subjective behavioral preferences to enable personalized financial guidance.

## Features

- **Multi-tier Question Flow**: Core questions → Next-level AI-generated questions
- **Profile Management**: Create, update and version user profiles
- **Analytics Dashboard**: Analyze financial profiles with metrics and visualizations
- **LLM Integration**: AI-powered question generation and response analysis
- **SQLite Database**: Robust data persistence with transaction support

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

# Run specific test file
pytest test_frontend_understanding_levels.py

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
├── /data                    # Data storage directory
│   └── profiles.db          # SQLite database
├── /models
│   ├── database_profile_manager.py   # Profile management functionality
│   └── question_repository.py        # Question definitions and access
├── /services
│   ├── question_service.py           # Core question flow logic
│   ├── llm_service.py                # LLM integration
│   └── profile_analytics_service.py  # Profile analysis
├── /static                  # Static assets
│   ├── /css                 # Stylesheets
│   └── /js                  # JavaScript files
└── /templates               # HTML templates
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