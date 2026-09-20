import logging
import os

class RunIdFilter(logging.Filter):
    """Injects run_id into log records."""
    def __init__(self, run_id: str):
        super().__init__()
        self.run_id = run_id

    def filter(self, record):
        record.run_id = self.run_id
        return True

def setup_logging(run_id: str) -> logging.Logger:
    """
    Configures structured logging to both console and a file.
    Creates the logs/ directory if it doesn't exist.
    """
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"pipeline_{run_id}.log")
    
    logger = logging.getLogger('hospital_pipeline')
    logger.setLevel(logging.INFO)
    
    # Prevent adding handlers multiple times if called again
    if not logger.handlers:
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [run:%(run_id)s] %(name)s - %(message)s')
        
        # File Handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        
        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        # Add filter for run_id
        run_id_filter = RunIdFilter(run_id)
        logger.addFilter(run_id_filter)
        for handler in logger.handlers:
            handler.addFilter(run_id_filter)
            
    return logger
