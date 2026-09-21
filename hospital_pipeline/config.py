import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

# Fix #4: No hardcoded credentials — all from environment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'hospital_db'),
}

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
SOURCE_API_KEY = os.getenv('SOURCE_API_KEY', 'demo-key-change-me')

# Paths
RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'))
CLEANED_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned'))

def get_engine(test_mode: bool = False):
    """
    Returns a SQLAlchemy engine.
    If test_mode=True, returns a SQLite in-memory engine.
    Otherwise, uses DB_CONFIG to return a MySQL engine.
    """
    if test_mode:
        return create_engine('sqlite:///:memory:')
    
    conn_str = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_str)

def check_database_connection() -> tuple[bool, str]:
    """
    Attempts to connect to the configured database.
    Returns (success, message).
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Successfully connected to the database."
    except SQLAlchemyError as e:
        return False, f"Failed to connect to database. Ensure MySQL is running on {DB_CONFIG['host']}:{DB_CONFIG['port']}. Error: {str(e)}"
