import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration class for the Financial Profiler application.
    Loads settings from environment variables with sensible defaults.
    """
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Database settings
    DB_PATH = os.environ.get('DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'profiles.db')
    
    # LLM settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    
    # Allow explicit disabling of LLM via environment variable
    LLM_ENABLED_ENV = os.environ.get('LLM_ENABLED', 'True')
    LLM_ENABLED = LLM_ENABLED_ENV.lower() not in ('false', '0', 'f', 'no') and bool(OPENAI_API_KEY)
    
    # Profile settings
    DATA_DIRECTORY = os.environ.get('DATA_DIRECTORY') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    PROFILES_DIRECTORY = os.path.join(DATA_DIRECTORY, 'profiles')
    
    # Admin settings
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
    ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'default_admin_key')
    
    # API settings
    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', '100'))  # Requests per minute
    API_CACHE_TTL = int(os.environ.get('API_CACHE_TTL', '3600'))   # Default cache TTL in seconds
    API_CACHE_ENABLED = os.environ.get('API_CACHE_ENABLED', 'True').lower() in ('true', '1', 't')
    
    # Monte Carlo cache settings
    MONTE_CARLO_CACHE_SIZE = int(os.environ.get('MONTE_CARLO_CACHE_SIZE', '100'))
    MONTE_CARLO_CACHE_TTL = int(os.environ.get('MONTE_CARLO_CACHE_TTL', '3600'))  # 1 hour
    MONTE_CARLO_CACHE_SAVE_INTERVAL = int(os.environ.get('MONTE_CARLO_CACHE_SAVE_INTERVAL', '300'))  # 5 minutes
    MONTE_CARLO_CACHE_DIR = os.environ.get('MONTE_CARLO_CACHE_DIR') or os.path.join(DATA_DIRECTORY, 'cache')
    MONTE_CARLO_CACHE_FILE = os.environ.get('MONTE_CARLO_CACHE_FILE', 'monte_carlo_cache.pickle')
    
    # Feature flags
    FEATURE_GOAL_PROBABILITY_API = os.environ.get('FEATURE_GOAL_PROBABILITY_API', 'True').lower() in ('true', '1', 't')
    FEATURE_VISUALIZATION_API = os.environ.get('FEATURE_VISUALIZATION_API', 'True').lower() in ('true', '1', 't')
    FEATURE_ADMIN_CACHE_API = os.environ.get('FEATURE_ADMIN_CACHE_API', 'True').lower() in ('true', '1', 't')
    FEATURE_MONTE_CARLO_CACHE = os.environ.get('FEATURE_MONTE_CARLO_CACHE', 'True').lower() in ('true', '1', 't')
    
    # Authentication and environment settings
    DEV_MODE = os.environ.get('DEV_MODE', 'True').lower() in ('true', '1', 't')  # True for development, False for production
    
    @classmethod
    def get_llm_status_message(cls):
        """
        Get a user-friendly message about the LLM service status
        """
        if cls.LLM_ENABLED:
            return {
                "status": "enabled",
                "message": f"LLM service is enabled using model: {cls.OPENAI_MODEL}",
                "model": cls.OPENAI_MODEL
            }
        else:
            return {
                "status": "disabled",
                "message": "LLM service is disabled. Set OPENAI_API_KEY environment variable to enable AI-powered question generation and response analysis.",
                "model": None
            }
    
    @classmethod
    def init_app(cls, app):
        """
        Initialize Flask app with configuration
        """
        # Ensure data directories exist
        os.makedirs(cls.DATA_DIRECTORY, exist_ok=True)
        os.makedirs(cls.PROFILES_DIRECTORY, exist_ok=True)
        os.makedirs(cls.MONTE_CARLO_CACHE_DIR, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(cls.DATA_DIRECTORY, 'logs', 'debug.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.DEBUG if cls.DEBUG else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        # Log LLM status
        if cls.LLM_ENABLED:
            logging.info(f"LLM service is enabled using model: {cls.OPENAI_MODEL}")
        else:
            logging.warning("LLM service is disabled. Set OPENAI_API_KEY environment variable to enable advanced features.")
            
        # Log cache status
        if cls.FEATURE_MONTE_CARLO_CACHE:
            logging.info(f"Monte Carlo cache enabled with size={cls.MONTE_CARLO_CACHE_SIZE}, TTL={cls.MONTE_CARLO_CACHE_TTL}s")
        else:
            logging.info("Monte Carlo cache feature is disabled")
            
        # Log development mode status
        if cls.DEV_MODE:
            logging.info("Running in DEVELOPMENT MODE - Authentication will be bypassed for admin routes")
        else:
            logging.info("Running in PRODUCTION MODE - Full authentication required for admin routes")