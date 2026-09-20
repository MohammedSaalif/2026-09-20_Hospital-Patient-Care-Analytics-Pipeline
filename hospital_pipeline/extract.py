import os
import time
import requests
import pandas as pd
import logging
from hospital_pipeline.config import RAW_DATA_DIR

logger = logging.getLogger('hospital_pipeline')

def _fetch_with_retry(url: str, headers: dict, params: dict = None, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    """Fetches data from an API with retry logic for 429 and 50x errors."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                logger.warning(f"Rate limited (429). Retrying in {retry_after}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_after)
                continue
                
            if response.status_code in [500, 503]:
                if attempt < 2:
                    logger.warning(f"Server error {response.status_code}. Retrying... (Attempt {attempt+1}/2)")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Failed after {attempt+1} attempts due to server errors.")
                    
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Request failed: {str(e)}")
                raise
            time.sleep(2 ** attempt)
            
    return response

def extract(api_base_url: str, api_key: str, run_id: str) -> dict[str, pd.DataFrame]:
    """
    Extracts data from the simulated source API.
    """
    headers = {}
    default_params = {'api_key': api_key}
    
    endpoints = {
        'patients': '/source/patients',
        'doctors': '/source/doctors',
        'departments': '/source/departments',
        'appointments': '/source/appointments',
        'lab_results': '/source/labs',
        'consultation_notes': '/source/notes'
    }
    
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    extracted_data = {}
    
    for name, path in endpoints.items():
        url = f"{api_base_url}{path}"
        logger.info(f"Extracting {name} from {url}...")
        
        response = _fetch_with_retry(url, headers=headers, params=default_params)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            extracted_data[name] = df
            # Save raw data
            df.to_csv(os.path.join(RAW_DATA_DIR, f"{name}.csv"), index=False)
            logger.info(f"Successfully extracted {len(df)} rows for {name}.")
            
        elif response.status_code == 204:
            logger.warning(f"No content returned for {name}.")
            extracted_data[name] = pd.DataFrame()
            
        elif response.status_code == 400:
            logger.error(f"Bad request for {name}: {response.text}")
            raise Exception(f"Bad Request: {response.text}")
            
        elif response.status_code == 401:
            logger.error("Invalid API key")
            raise Exception("Invalid API key")
            
        elif response.status_code == 404:
            logger.warning(f"Endpoint not found for {name}. Skipping.")
            
        else:
            logger.error(f"Unexpected status {response.status_code} for {name}.")
            
    # Wearables micro-batch (paginated)
    wearables_url = f"{api_base_url}/source/wearables"
    logger.info(f"Extracting wearables from {wearables_url} (paginated)...")
    page = 1
    all_wearables = []
    
    while True:
        params = {'api_key': api_key, 'page': page, 'page_size': 500}
        response = _fetch_with_retry(wearables_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            all_wearables.extend(data)
            page += 1
        elif response.status_code == 204:
            break
        elif response.status_code == 404:
            logger.warning("Wearables endpoint not found. Skipping.")
            break
        else:
            if response.status_code == 401:
                logger.error("Invalid API key")
                raise Exception("Invalid API key")
            logger.error(f"Error fetching wearables: {response.status_code}")
            break
            
    wearable_df = pd.DataFrame(all_wearables)
    extracted_data['wearable_readings'] = wearable_df
    if not wearable_df.empty:
        wearable_df.to_json(os.path.join(RAW_DATA_DIR, "wearable_readings.json"), orient='records')
        logger.info(f"Successfully extracted {len(wearable_df)} rows for wearable_readings.")
    
    return extracted_data
