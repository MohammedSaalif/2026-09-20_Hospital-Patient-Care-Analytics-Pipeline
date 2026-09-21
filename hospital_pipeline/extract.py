import os
import json
import pandas as pd
import logging
from hospital_pipeline.config import RAW_DATA_DIR

logger = logging.getLogger('hospital_pipeline')

def extract(api_base_url: str = None, api_key: str = None, run_id: str = None) -> dict[str, pd.DataFrame]:
    """
    Extracts raw data files from data/raw directory into Pandas DataFrames.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    extracted_data = {}
    
    files_to_extract = {
        'patients': ('patients.csv', 'csv'),
        'doctors': ('doctors.csv', 'csv'),
        'departments': ('departments.csv', 'csv'),
        'appointments': ('appointments.csv', 'csv'),
        'lab_results': ('lab_results.csv', 'csv'),
        'wearable_readings': ('wearable_readings.json', 'json'),
        'consultation_notes': ('consultation_notes.json', 'json')
    }
    
    for name, (filename, file_type) in files_to_extract.items():
        file_path = os.path.join(RAW_DATA_DIR, filename)
        
        # Fallback for csv/json extension variations
        if not os.path.exists(file_path):
            alt_filename = filename.replace('.json', '.csv') if file_type == 'json' else filename.replace('.csv', '.json')
            alt_path = os.path.join(RAW_DATA_DIR, alt_filename)
            if os.path.exists(alt_path):
                file_path = alt_path
                file_type = 'csv' if alt_filename.endswith('.csv') else 'json'
                
        if os.path.exists(file_path):
            logger.info(f"Extracting {name} from {file_path}...")
            if file_type == 'csv':
                df = pd.read_csv(file_path)
            else:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            extracted_data[name] = df
            logger.info(f"Extracted {len(df)} rows for {name}.")
        else:
            logger.warning(f"File {file_path} not found. Returning empty DataFrame.")
            extracted_data[name] = pd.DataFrame()
            
    return extracted_data
