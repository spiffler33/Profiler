#!/usr/bin/env python3
"""
Migration script to set up financial parameters with Indian market assumptions.

This script implements a financial parameters migration for the Indian market context:
1. Creates a backup of current parameters
2. Sets up a parameters database if not exists
3. Populates default Indian market parameters including:
   - Market returns (equity, debt, gold, real estate)
   - Inflation rates (general, education, healthcare)
   - Tax slabs for Indian income tax
   - SIP-related parameters
   - EPF/PPF rates and other India-specific financial parameters

Usage:
    python run_financial_parameters_migration.py

The script is idempotent and includes error handling to ensure data integrity.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
import shutil
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/financial_analysis.log'
)
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = "data/backups/parameters"
PARAMETERS_DB_PATH = "data/parameters.db"
VERSION = "1.0.0"  # Initial version

@contextmanager
def get_db_connection(db_path: str = PARAMETERS_DB_PATH):
    """
    Context manager for database connections.
    
    Args:
        db_path: Path to the SQLite database
        
    Yields:
        sqlite3.Connection: Database connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_backup() -> str:
    """
    Create a backup of the current parameters.
    
    Returns:
        str: Path to the backup file
    """
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"parameters_backup_{timestamp}.json")
        
        # If parameters.db exists, create a backup
        if os.path.exists(PARAMETERS_DB_PATH):
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM parameters")
                    parameters = cursor.fetchall()
                    
                    # Convert parameters to dictionary
                    params_dict = {}
                    for param in parameters:
                        params_dict[param['parameter_name']] = param['parameter_value']
                    
                    # Create a backup file
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "timestamp": timestamp,
                            "version": VERSION,
                            "parameters": params_dict
                        }, f, indent=2)
                    
                    # Also backup the database
                    db_backup_path = os.path.join(BACKUP_DIR, f"parameters_db_backup_{timestamp}.db")
                    shutil.copy2(PARAMETERS_DB_PATH, db_backup_path)
                    logger.info(f"Created database backup at {db_backup_path}")
            except Exception as e:
                logger.warning(f"Could not backup existing parameters: {e}")
                # Create an empty backup file
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "timestamp": timestamp,
                        "version": VERSION,
                        "parameters": {}
                    }, f, indent=2)
        else:
            # Create an empty backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "version": VERSION,
                    "parameters": {}
                }, f, indent=2)
        
        logger.info(f"Created parameters backup at {backup_path}")
        return backup_path
    
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise

def initialize_database(db_path: str = PARAMETERS_DB_PATH) -> None:
    """
    Initialize the parameters database with necessary tables.
    
    Args:
        db_path: Path to the SQLite database
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Create parameters table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_group TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                parameter_value REAL NOT NULL,
                parameter_description TEXT,
                is_india_specific BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(parameter_group, parameter_name)
            )
            ''')
            
            # Create migration_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                backup_file TEXT
            )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_indian_financial_parameters() -> List[Dict[str, Any]]:
    """
    Get default financial parameters for the Indian market.
    
    Returns:
        List[Dict[str, Any]]: List of parameter dictionaries
    """
    # Current timestamp
    current_time = datetime.now().isoformat()
    
    # Parameters list - comprehensive set of Indian financial parameters
    parameters = [
        #
        # MARKET RETURNS - Detailed by asset class
        #
        
        # Equity returns
        {
            "parameter_group": "market.equity",
            "parameter_name": "equity_large_cap",
            "parameter_value": 12.0,
            "parameter_description": "Long-term large cap equity return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.equity",
            "parameter_name": "equity_mid_cap",
            "parameter_value": 14.0,
            "parameter_description": "Long-term mid cap equity return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.equity",
            "parameter_name": "equity_small_cap",
            "parameter_value": 15.0,
            "parameter_description": "Long-term small cap equity return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.equity",
            "parameter_name": "equity_index",
            "parameter_value": 11.0,
            "parameter_description": "Long-term index fund return in India (Nifty/Sensex)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.equity",
            "parameter_name": "equity_intl",
            "parameter_value": 9.0,
            "parameter_description": "Long-term international equity return for Indian investors",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.equity",
            "parameter_name": "equity_sectoral",
            "parameter_value": 13.0,
            "parameter_description": "Average sectoral equity fund return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Debt returns
        {
            "parameter_group": "market.debt",
            "parameter_name": "debt_govt",
            "parameter_value": 7.0,
            "parameter_description": "Government debt securities return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.debt",
            "parameter_name": "debt_corporate",
            "parameter_value": 8.0,
            "parameter_description": "Corporate bond return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.debt",
            "parameter_name": "debt_liquid",
            "parameter_value": 6.0,
            "parameter_description": "Liquid fund return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.debt",
            "parameter_name": "debt_fixed_deposit",
            "parameter_value": 6.5,
            "parameter_description": "Fixed deposit average return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.debt",
            "parameter_name": "debt_short_term",
            "parameter_value": 6.5,
            "parameter_description": "Short-term debt fund return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.debt",
            "parameter_name": "debt_long_term",
            "parameter_value": 7.5,
            "parameter_description": "Long-term debt fund return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Alternative investments
        {
            "parameter_group": "market.alternative",
            "parameter_name": "gold",
            "parameter_value": 8.0,
            "parameter_description": "Long-term gold return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.alternative",
            "parameter_name": "real_estate_residential",
            "parameter_value": 8.0,
            "parameter_description": "Residential real estate return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.alternative",
            "parameter_name": "real_estate_commercial",
            "parameter_value": 10.0,
            "parameter_description": "Commercial real estate return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.alternative",
            "parameter_name": "commodities",
            "parameter_value": 7.0,
            "parameter_description": "Average commodities return for Indian investors",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.alternative",
            "parameter_name": "reit",
            "parameter_value": 9.0,
            "parameter_description": "Real Estate Investment Trust return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Cash/savings
        {
            "parameter_group": "market.cash",
            "parameter_name": "savings_account",
            "parameter_value": 3.5,
            "parameter_description": "Savings account interest rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "market.cash",
            "parameter_name": "money_market",
            "parameter_value": 5.5,
            "parameter_description": "Money market fund return in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # INFLATION RATES - Detailed by category
        #
        
        # General inflation
        {
            "parameter_group": "inflation",
            "parameter_name": "general_inflation",
            "parameter_value": 6.0,
            "parameter_description": "General inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Education inflation
        {
            "parameter_group": "inflation.education",
            "parameter_name": "education_school",
            "parameter_value": 10.0,
            "parameter_description": "School education inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.education",
            "parameter_name": "education_undergraduate",
            "parameter_value": 9.0,
            "parameter_description": "Undergraduate education inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.education",
            "parameter_name": "education_postgraduate",
            "parameter_value": 8.0,
            "parameter_description": "Postgraduate education inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.education",
            "parameter_name": "education_professional",
            "parameter_value": 12.0,
            "parameter_description": "Professional education (MD, MBA, etc.) inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.education",
            "parameter_name": "education_foreign",
            "parameter_value": 8.0,
            "parameter_description": "Foreign education inflation rate in India (in USD terms)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Healthcare inflation
        {
            "parameter_group": "inflation.healthcare",
            "parameter_name": "healthcare_general",
            "parameter_value": 12.0,
            "parameter_description": "General healthcare inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.healthcare",
            "parameter_name": "healthcare_hospitalization",
            "parameter_value": 15.0,
            "parameter_description": "Hospitalization cost inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.healthcare",
            "parameter_name": "healthcare_chronic",
            "parameter_value": 10.0,
            "parameter_description": "Chronic condition management inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.healthcare",
            "parameter_name": "healthcare_insurance",
            "parameter_value": 8.0,
            "parameter_description": "Health insurance premium inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.healthcare",
            "parameter_name": "healthcare_senior",
            "parameter_value": 14.0,
            "parameter_description": "Senior citizen healthcare inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Housing inflation
        {
            "parameter_group": "inflation.housing",
            "parameter_name": "housing_metro",
            "parameter_value": 7.0,
            "parameter_description": "Housing cost inflation in metro cities in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.housing",
            "parameter_name": "housing_tier1",
            "parameter_value": 6.0,
            "parameter_description": "Housing cost inflation in tier 1 cities in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.housing",
            "parameter_name": "housing_tier2",
            "parameter_value": 5.0,
            "parameter_description": "Housing cost inflation in tier 2 cities in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.housing",
            "parameter_name": "housing_rent",
            "parameter_value": 8.0,
            "parameter_description": "Rental cost inflation in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.housing",
            "parameter_name": "housing_maintenance",
            "parameter_value": 10.0,
            "parameter_description": "Housing maintenance cost inflation in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Other inflation categories
        {
            "parameter_group": "inflation.other",
            "parameter_name": "food_inflation",
            "parameter_value": 7.0,
            "parameter_description": "Food inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.other",
            "parameter_name": "transport_inflation",
            "parameter_value": 5.0,
            "parameter_description": "Transportation inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.other",
            "parameter_name": "utilities_inflation",
            "parameter_value": 6.0,
            "parameter_description": "Utilities inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "inflation.other",
            "parameter_name": "luxury_inflation",
            "parameter_value": 8.0,
            "parameter_description": "Luxury item inflation rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # TAX PARAMETERS - Comprehensive Indian tax system
        #
        
        # Income tax - New regime slabs and rates (FY 2024-25)
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_1_limit",
            "parameter_value": 300000.0,
            "parameter_description": "Income tax slab 1 upper limit (₹3,00,000) new regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_1_rate",
            "parameter_value": 0.0,
            "parameter_description": "Income tax rate for income up to ₹3,00,000 (new regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_2_limit",
            "parameter_value": 600000.0,
            "parameter_description": "Income tax slab 2 upper limit (₹6,00,000) new regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_2_rate",
            "parameter_value": 5.0,
            "parameter_description": "Income tax rate for income ₹3,00,001 to ₹6,00,000 (new regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_3_limit",
            "parameter_value": 900000.0,
            "parameter_description": "Income tax slab 3 upper limit (₹9,00,000) new regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_3_rate",
            "parameter_value": 10.0,
            "parameter_description": "Income tax rate for income ₹6,00,001 to ₹9,00,000 (new regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_4_limit",
            "parameter_value": 1200000.0,
            "parameter_description": "Income tax slab 4 upper limit (₹12,00,000) new regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_4_rate",
            "parameter_value": 15.0,
            "parameter_description": "Income tax rate for income ₹9,00,001 to ₹12,00,000 (new regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_5_limit",
            "parameter_value": 1500000.0,
            "parameter_description": "Income tax slab 5 upper limit (₹15,00,000) new regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_5_rate",
            "parameter_value": 20.0,
            "parameter_description": "Income tax rate for income ₹12,00,001 to ₹15,00,000 (new regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.new_regime",
            "parameter_name": "income_tax_slab_6_rate",
            "parameter_value": 30.0,
            "parameter_description": "Income tax rate for income above ₹15,00,000 (new regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Income tax - Old regime slabs and rates (FY 2024-25)
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_1_limit",
            "parameter_value": 250000.0,
            "parameter_description": "Income tax slab 1 upper limit (₹2,50,000) old regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_1_rate",
            "parameter_value": 0.0,
            "parameter_description": "Income tax rate for income up to ₹2,50,000 (old regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_2_limit",
            "parameter_value": 500000.0,
            "parameter_description": "Income tax slab 2 upper limit (₹5,00,000) old regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_2_rate",
            "parameter_value": 5.0,
            "parameter_description": "Income tax rate for income ₹2,50,001 to ₹5,00,000 (old regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_3_limit",
            "parameter_value": 1000000.0,
            "parameter_description": "Income tax slab 3 upper limit (₹10,00,000) old regime",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_3_rate",
            "parameter_value": 20.0,
            "parameter_description": "Income tax rate for income ₹5,00,001 to ₹10,00,000 (old regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.income.old_regime",
            "parameter_name": "income_tax_old_slab_4_rate",
            "parameter_value": 30.0,
            "parameter_description": "Income tax rate for income above ₹10,00,000 (old regime)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Tax surcharges and cess
        {
            "parameter_group": "tax.surcharge",
            "parameter_name": "surcharge_50L_1Cr",
            "parameter_value": 10.0,
            "parameter_description": "Income tax surcharge for income between ₹50L and ₹1Cr",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.surcharge",
            "parameter_name": "surcharge_1Cr_2Cr",
            "parameter_value": 15.0,
            "parameter_description": "Income tax surcharge for income between ₹1Cr and ₹2Cr",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.surcharge",
            "parameter_name": "surcharge_2Cr_5Cr",
            "parameter_value": 25.0,
            "parameter_description": "Income tax surcharge for income between ₹2Cr and ₹5Cr",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.surcharge",
            "parameter_name": "surcharge_above_5Cr",
            "parameter_value": 37.0,
            "parameter_description": "Income tax surcharge for income above ₹5Cr",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.cess",
            "parameter_name": "education_cess",
            "parameter_value": 4.0,
            "parameter_description": "Education and health cess on income tax",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Capital gains tax
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "ltcg_equity_limit",
            "parameter_value": 100000.0,
            "parameter_description": "Long-term capital gains tax exemption limit for equity",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "ltcg_equity",
            "parameter_value": 10.0,
            "parameter_description": "Long-term capital gains tax on equity (>1 year holding)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "stcg_equity",
            "parameter_value": 15.0,
            "parameter_description": "Short-term capital gains tax on equity (<1 year holding)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "ltcg_debt",
            "parameter_value": 20.0,
            "parameter_description": "Long-term capital gains tax on debt (>3 years holding) with indexation",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "ltcg_debt_holding_period",
            "parameter_value": 3.0,
            "parameter_description": "Holding period in years to qualify for long-term capital gains in debt",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "ltcg_property",
            "parameter_value": 20.0,
            "parameter_description": "Long-term capital gains tax on property with indexation",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.capital_gains",
            "parameter_name": "ltcg_gold",
            "parameter_value": 20.0,
            "parameter_description": "Long-term capital gains tax on gold with indexation",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Tax deductions and exemptions
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "section_80c_limit",
            "parameter_value": 150000.0,
            "parameter_description": "Maximum deduction under Section 80C",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "section_80ccd_1b_limit",
            "parameter_value": 50000.0,
            "parameter_description": "Additional NPS deduction under Section 80CCD(1B)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "section_80d_self_limit",
            "parameter_value": 25000.0,
            "parameter_description": "Health insurance deduction limit for self under Section 80D",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "section_80d_parents_limit",
            "parameter_value": 50000.0,
            "parameter_description": "Health insurance deduction limit for senior citizen parents under Section 80D",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "section_80e_limit",
            "parameter_value": -1.0,  # No limit, full interest deduction
            "parameter_description": "Education loan interest deduction under Section 80E (no upper limit)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "section_24_home_loan_limit",
            "parameter_value": 200000.0,
            "parameter_description": "Home loan interest deduction limit under Section 24",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "tax.deductions",
            "parameter_name": "standard_deduction",
            "parameter_value": 50000.0,
            "parameter_description": "Standard deduction for salaried individuals",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # RETIREMENT AND PROVIDENT FUND PARAMETERS
        #
        
        # EPF and PPF
        {
            "parameter_group": "retirement.epf",
            "parameter_name": "epf_rate",
            "parameter_value": 8.15,
            "parameter_description": "Current EPF interest rate",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.epf",
            "parameter_name": "epf_contribution_percent",
            "parameter_value": 12.0,
            "parameter_description": "Employee EPF contribution as percentage of basic salary",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.epf",
            "parameter_name": "employer_epf_contribution_percent",
            "parameter_value": 12.0,
            "parameter_description": "Employer EPF contribution as percentage of basic salary",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.ppf",
            "parameter_name": "ppf_rate",
            "parameter_value": 7.1,
            "parameter_description": "Current PPF interest rate",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.ppf",
            "parameter_name": "ppf_min_contribution",
            "parameter_value": 500.0,
            "parameter_description": "Minimum annual PPF contribution",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.ppf",
            "parameter_name": "ppf_max_contribution",
            "parameter_value": 150000.0,
            "parameter_description": "Maximum annual PPF contribution",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.ppf",
            "parameter_name": "ppf_lock_in_years",
            "parameter_value": 15.0,
            "parameter_description": "PPF lock-in period in years",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # NPS parameters
        {
            "parameter_group": "retirement.nps",
            "parameter_name": "nps_expected_return",
            "parameter_value": 10.0,
            "parameter_description": "Expected long-term return from NPS (National Pension System)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.nps",
            "parameter_name": "nps_min_contribution",
            "parameter_value": 1000.0,
            "parameter_description": "Minimum annual NPS contribution (Tier 1)",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.nps",
            "parameter_name": "nps_lock_in_till_age",
            "parameter_value": 60.0,
            "parameter_description": "NPS lock-in till retirement age",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.nps",
            "parameter_name": "nps_tax_free_withdrawal",
            "parameter_value": 60.0,
            "parameter_description": "Percentage of NPS corpus that can be withdrawn tax-free at retirement",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Retirement planning
        {
            "parameter_group": "retirement.planning",
            "parameter_name": "retirement_age",
            "parameter_value": 60.0,
            "parameter_description": "Typical retirement age in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.planning",
            "parameter_name": "life_expectancy",
            "parameter_value": 85.0,
            "parameter_description": "Life expectancy for retirement planning in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.planning",
            "parameter_name": "retirement_corpus_annual_income_multiple",
            "parameter_value": 25.0,
            "parameter_description": "Retirement corpus as multiple of annual expenses at retirement",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.planning",
            "parameter_name": "safe_withdrawal_rate",
            "parameter_value": 4.0,
            "parameter_description": "Safe withdrawal rate from retirement corpus",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "retirement.planning",
            "parameter_name": "post_retirement_expense_percent",
            "parameter_value": 80.0,
            "parameter_description": "Post-retirement expenses as percentage of pre-retirement expenses",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # INVESTMENT PARAMETERS - SIP and mutual funds
        #
        
        # SIP parameters
        {
            "parameter_group": "investments.sip",
            "parameter_name": "minimum_sip",
            "parameter_value": 500.0,
            "parameter_description": "Minimum SIP amount in most mutual funds",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "investments.sip",
            "parameter_name": "typical_sip_increment",
            "parameter_value": 500.0,
            "parameter_description": "Typical increment amount for SIPs",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "investments.sip",
            "parameter_name": "sip_annual_increase",
            "parameter_value": 10.0,
            "parameter_description": "Recommended annual percentage increase in SIP amounts",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Mutual fund parameters
        {
            "parameter_group": "investments.mutual_funds",
            "parameter_name": "elss_lock_in",
            "parameter_value": 3.0,
            "parameter_description": "ELSS mutual fund lock-in period in years",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "investments.mutual_funds",
            "parameter_name": "equity_mf_expense_ratio",
            "parameter_value": 1.5,
            "parameter_description": "Average equity mutual fund expense ratio percentage",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "investments.mutual_funds",
            "parameter_name": "debt_mf_expense_ratio",
            "parameter_value": 1.0,
            "parameter_description": "Average debt mutual fund expense ratio percentage",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "investments.mutual_funds",
            "parameter_name": "index_fund_expense_ratio",
            "parameter_value": 0.5,
            "parameter_description": "Average index fund expense ratio percentage",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Asset allocation models
        {
            "parameter_group": "asset_allocation.age_based",
            "parameter_name": "equity_percent_20s",
            "parameter_value": 80.0,
            "parameter_description": "Recommended equity allocation percentage for investors in their 20s",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.age_based",
            "parameter_name": "equity_percent_30s",
            "parameter_value": 70.0,
            "parameter_description": "Recommended equity allocation percentage for investors in their 30s",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.age_based",
            "parameter_name": "equity_percent_40s",
            "parameter_value": 60.0,
            "parameter_description": "Recommended equity allocation percentage for investors in their 40s",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.age_based",
            "parameter_name": "equity_percent_50s",
            "parameter_value": 50.0,
            "parameter_description": "Recommended equity allocation percentage for investors in their 50s",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.age_based",
            "parameter_name": "equity_percent_60s",
            "parameter_value": 40.0,
            "parameter_description": "Recommended equity allocation percentage for investors in their 60s",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.risk_based",
            "parameter_name": "equity_percent_conservative",
            "parameter_value": 30.0,
            "parameter_description": "Equity allocation percentage for conservative risk profile",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.risk_based",
            "parameter_name": "equity_percent_moderate",
            "parameter_value": 50.0,
            "parameter_description": "Equity allocation percentage for moderate risk profile",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.risk_based",
            "parameter_name": "equity_percent_aggressive",
            "parameter_value": 70.0,
            "parameter_description": "Equity allocation percentage for aggressive risk profile",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "asset_allocation.risk_based",
            "parameter_name": "equity_percent_very_aggressive",
            "parameter_value": 90.0,
            "parameter_description": "Equity allocation percentage for very aggressive risk profile",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # INSURANCE PARAMETERS
        #
        
        # Life insurance
        {
            "parameter_group": "insurance.life",
            "parameter_name": "life_cover_income_multiple",
            "parameter_value": 10.0,
            "parameter_description": "Recommended life insurance coverage as multiple of annual income",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "insurance.life",
            "parameter_name": "life_cover_expense_multiple",
            "parameter_value": 20.0,
            "parameter_description": "Recommended life insurance coverage as multiple of annual expenses",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "insurance.life",
            "parameter_name": "term_insurance_age_limit",
            "parameter_value": 70.0,
            "parameter_description": "Typical maximum age limit for term insurance coverage",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Health insurance
        {
            "parameter_group": "insurance.health",
            "parameter_name": "health_cover_individual",
            "parameter_value": 500000.0,
            "parameter_description": "Recommended individual health insurance coverage in INR",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "insurance.health",
            "parameter_name": "health_cover_family",
            "parameter_value": 1000000.0,
            "parameter_description": "Recommended family floater health insurance coverage in INR",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "insurance.health",
            "parameter_name": "health_cover_senior",
            "parameter_value": 750000.0,
            "parameter_description": "Recommended health insurance coverage for seniors in INR",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "insurance.health",
            "parameter_name": "critical_illness_cover",
            "parameter_value": 2500000.0,
            "parameter_description": "Recommended critical illness coverage in INR",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # LOAN PARAMETERS
        #
        
        # Home loan
        {
            "parameter_group": "loans.home",
            "parameter_name": "home_loan_typical_rate",
            "parameter_value": 8.5,
            "parameter_description": "Typical home loan interest rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "loans.home",
            "parameter_name": "home_loan_max_tenure",
            "parameter_value": 30.0,
            "parameter_description": "Maximum home loan tenure in years",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "loans.home",
            "parameter_name": "home_loan_typical_ltv",
            "parameter_value": 80.0,
            "parameter_description": "Typical loan-to-value ratio for home loans in percentage",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "loans.home",
            "parameter_name": "home_loan_foir_max",
            "parameter_value": 50.0,
            "parameter_description": "Maximum fixed obligation to income ratio for home loans in percentage",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Other loans
        {
            "parameter_group": "loans.personal",
            "parameter_name": "personal_loan_typical_rate",
            "parameter_value": 14.0,
            "parameter_description": "Typical personal loan interest rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "loans.auto",
            "parameter_name": "car_loan_typical_rate",
            "parameter_value": 9.5,
            "parameter_description": "Typical car loan interest rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "loans.education",
            "parameter_name": "education_loan_typical_rate",
            "parameter_value": 8.5,
            "parameter_description": "Typical education loan interest rate in India",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "loans.education",
            "parameter_name": "education_loan_moratorium",
            "parameter_value": 1.0,
            "parameter_description": "Typical education loan moratorium period after course completion in years",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        #
        # FINANCIAL PLANNING RULES OF THUMB
        #
        
        # Emergency fund and savings
        {
            "parameter_group": "rules_of_thumb.emergency",
            "parameter_name": "emergency_fund_months",
            "parameter_value": 6.0,
            "parameter_description": "Recommended emergency fund size in months of expenses",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.emergency",
            "parameter_name": "emergency_fund_self_employed",
            "parameter_value": 12.0,
            "parameter_description": "Recommended emergency fund for self-employed in months of expenses",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.savings",
            "parameter_name": "min_savings_rate",
            "parameter_value": 20.0,
            "parameter_description": "Minimum recommended savings rate as percentage of income",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.savings",
            "parameter_name": "ideal_savings_rate",
            "parameter_value": 30.0,
            "parameter_description": "Ideal savings rate as percentage of income",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Debt and affordability
        {
            "parameter_group": "rules_of_thumb.debt",
            "parameter_name": "debt_service_ratio_max",
            "parameter_value": 40.0,
            "parameter_description": "Maximum recommended debt service ratio (percent of income)",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.debt",
            "parameter_name": "debt_to_income_ratio_max",
            "parameter_value": 50.0,
            "parameter_description": "Maximum recommended debt-to-income ratio",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.housing",
            "parameter_name": "housing_cost_income_percent",
            "parameter_value": 30.0,
            "parameter_description": "Maximum recommended housing cost as percentage of income",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.housing",
            "parameter_name": "home_price_income_multiple",
            "parameter_value": 5.0,
            "parameter_description": "Maximum recommended home price as multiple of annual income",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "rules_of_thumb.vehicle",
            "parameter_name": "vehicle_price_income_percent",
            "parameter_value": 35.0,
            "parameter_description": "Maximum recommended vehicle price as percentage of annual income",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        
        # Risk modeling parameters
        {
            "parameter_group": "monte_carlo",
            "parameter_name": "simulation_runs",
            "parameter_value": 10000.0,
            "parameter_description": "Default number of Monte Carlo simulation runs",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "monte_carlo",
            "parameter_name": "success_threshold",
            "parameter_value": 85.0,
            "parameter_description": "Success probability threshold percentage for financial goals",
            "is_india_specific": False,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "monte_carlo",
            "parameter_name": "equity_volatility",
            "parameter_value": 18.0,
            "parameter_description": "Standard deviation of equity returns in Indian market",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "monte_carlo",
            "parameter_name": "debt_volatility",
            "parameter_value": 5.0,
            "parameter_description": "Standard deviation of debt returns in Indian market",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "parameter_group": "monte_carlo",
            "parameter_name": "gold_volatility",
            "parameter_value": 15.0,
            "parameter_description": "Standard deviation of gold returns in Indian market",
            "is_india_specific": True,
            "created_at": current_time,
            "updated_at": current_time
        }
    ]
    
    return parameters

def migrate_parameters() -> None:
    """
    Migrate parameters to the database with Indian market assumptions.
    """
    try:
        # First create a backup
        backup_path = create_backup()
        
        # Initialize the database
        initialize_database()
        
        # Get Indian financial parameters
        parameters = get_indian_financial_parameters()
        
        # Insert parameters into database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Check if parameters already exist
                cursor.execute("SELECT COUNT(*) FROM parameters")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    logger.info("Parameters already exist in the database, checking for updates")
                    
                    # Update existing parameters if values differ
                    for param in parameters:
                        cursor.execute(
                            "SELECT parameter_value FROM parameters WHERE parameter_group = ? AND parameter_name = ?",
                            (param["parameter_group"], param["parameter_name"])
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            # If parameter exists but value is different, update it
                            if existing[0] != param["parameter_value"]:
                                cursor.execute(
                                    "UPDATE parameters SET parameter_value = ?, updated_at = ? WHERE parameter_group = ? AND parameter_name = ?",
                                    (param["parameter_value"], param["updated_at"], param["parameter_group"], param["parameter_name"])
                                )
                                logger.info(f"Updated parameter {param['parameter_group']}.{param['parameter_name']} to {param['parameter_value']}")
                        else:
                            # If parameter doesn't exist, insert it
                            cursor.execute(
                                "INSERT INTO parameters (parameter_group, parameter_name, parameter_value, parameter_description, is_india_specific, created_at, updated_at) "
                                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (param["parameter_group"], param["parameter_name"], param["parameter_value"], param["parameter_description"], 
                                param["is_india_specific"], param["created_at"], param["updated_at"])
                            )
                            logger.info(f"Added new parameter {param['parameter_group']}.{param['parameter_name']}")
                else:
                    # Insert all parameters
                    for param in parameters:
                        cursor.execute(
                            "INSERT INTO parameters (parameter_group, parameter_name, parameter_value, parameter_description, is_india_specific, created_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (param["parameter_group"], param["parameter_name"], param["parameter_value"], param["parameter_description"], 
                            param["is_india_specific"], param["created_at"], param["updated_at"])
                        )
                    logger.info(f"Inserted {len(parameters)} Indian financial parameters")
                
                # Record the migration
                current_time = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO migration_history (version, description, applied_at, backup_file) VALUES (?, ?, ?, ?)",
                    (VERSION, "Migration of Indian financial parameters", current_time, backup_path)
                )
                
                # Commit transaction
                conn.commit()
                logger.info("Successfully migrated financial parameters with Indian market assumptions")
                
            except Exception as e:
                # Rollback transaction on error
                conn.rollback()
                logger.error(f"Error during migration, rolled back: {e}")
                raise
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def main():
    """
    Main function to run the financial parameters migration.
    """
    try:
        # Ensure log directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Display start message
        print("Starting financial parameters migration for Indian market...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run the migration
        migrate_parameters()
        
        print("=" * 60)
        print("Migration completed successfully!")
        print("The financial parameters have been set up with Indian market assumptions.")
        print("A backup of any existing parameters has been created in the data/backups/parameters directory.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        print("\nThe migration was unsuccessful. See the error message above for details.")
        print("No changes have been made to your production data.")
        sys.exit(1)

if __name__ == "__main__":
    main()