import uuid
import time
import pandas as pd
import logging
from datetime import datetime
from hospital_pipeline.config import get_engine, check_database_connection, API_BASE_URL, SOURCE_API_KEY
from hospital_pipeline.logging_setup import setup_logging
from hospital_pipeline.extract import extract
from hospital_pipeline.transform import transform
from hospital_pipeline.validate import validate
from hospital_pipeline.risk import calculate_risk_scores
from hospital_pipeline.load import load

def run_pipeline():
    """Orchestrates the entire ETL pipeline."""
    run_id = str(uuid.uuid4())
    logger = setup_logging(run_id)
    logger.info(f"Starting pipeline run {run_id}")
    
    start_time = time.time()
    engine = get_engine()
    
    summary = {
        'run_id': run_id,
        'status': 'STARTED',
        'start_time': datetime.now().isoformat(),
        'extracted': {},
        'transformed': {},
        'loaded': {}
    }
    
    try:
        # Check DB
        db_ok, db_msg = check_database_connection()
        if not db_ok:
            logger.error(f"Database check failed: {db_msg}")
            raise Exception("Database connection failed")
        logger.info(db_msg)
        
        # EXTRACT
        raw_data = extract(API_BASE_URL, SOURCE_API_KEY, run_id)
        summary['extracted'] = {k: len(v) for k, v in raw_data.items()}
        
        # TRANSFORM
        transformed_data = transform(raw_data, run_id)
        summary['transformed'] = {k: len(v) for k, v in transformed_data.items()}
        
        # VALIDATE
        passed, val_results = validate(transformed_data, run_id)
        
        # Save validation results
        val_df = pd.DataFrame(val_results)
        val_df['run_id'] = run_id
        if not val_df.empty:
            val_df.to_sql('data_quality_results', engine, if_exists='append', index=False)
            
        if not passed:
            logger.error("Pipeline blocked due to critical validation failures.")
            summary['status'] = 'FAILED_VALIDATION'
            return summary
            
        # RISK SCORING
        risk_df = calculate_risk_scores(
            transformed_data.get('patients', pd.DataFrame()),
            transformed_data.get('appointments', pd.DataFrame()),
            transformed_data.get('lab_results', pd.DataFrame()),
            transformed_data.get('wearable_readings', pd.DataFrame()),
            transformed_data.get('consultation_notes', pd.DataFrame()),
            run_id
        )
        transformed_data['patient_risk'] = risk_df
        
        # LOAD
        loaded_counts = load(transformed_data, engine, run_id)
        summary['loaded'] = loaded_counts
        
        summary['status'] = 'SUCCESS'
        logger.info(f"Pipeline {run_id} completed successfully.")
        
    except Exception as e:
        logger.exception(f"Pipeline {run_id} failed: {str(e)}")
        summary['status'] = 'FAILED'
        summary['error'] = str(e)
        
    finally:
        end_time = time.time()
        summary['duration_seconds'] = round(end_time - start_time, 2)
        summary['end_time'] = datetime.now().isoformat()
        
        # Record run
        run_df = pd.DataFrame([{
            'run_id': summary['run_id'],
            'status': summary['status'],
            'start_time': summary['start_time'],
            'end_time': summary['end_time'],
            'duration_seconds': summary['duration_seconds']
        }])
        run_df.to_sql('pipeline_runs', engine, if_exists='append', index=False)
        
    return summary

if __name__ == '__main__':
    run_pipeline()
