import pytest
import os
import pandas as pd
from sqlalchemy import create_engine
import hospital_pipeline.config as config

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_hospital.db")

@pytest.fixture(scope="session", autouse=True)
def test_engine():
    """Create a file-based SQLite engine for tests."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    engine = create_engine(
        f'sqlite:///{TEST_DB_PATH}',
        connect_args={"check_same_thread": False}
    )
    
    # Create tables matching the star schema
    pd.DataFrame({
        'patient_id': pd.Series(dtype='str'),
        'first_name': pd.Series(dtype='str'),
        'last_name': pd.Series(dtype='str'),
        'date_of_birth': pd.Series(dtype='object'),
        'gender': pd.Series(dtype='str'),
        'phone': pd.Series(dtype='str'),
        'email': pd.Series(dtype='str'),
        'blood_group': pd.Series(dtype='str')
    }).to_sql('dim_patient', engine, index=False, if_exists='replace')
    
    pd.DataFrame({
        'patient_id': pd.Series(dtype='str'),
        'risk_score': pd.Series(dtype='int'),
        'risk_level': pd.Series(dtype='str'),
        'risk_reasons': pd.Series(dtype='str'),
        'assessed_date': pd.Series(dtype='str'),
        'run_id': pd.Series(dtype='str')
    }).to_sql('fact_patient_risk', engine, index=False, if_exists='replace')
    
    pd.DataFrame({
        'appointment_id': pd.Series(dtype='str'),
        'patient_id': pd.Series(dtype='str'),
        'doctor_id': pd.Series(dtype='str'),
        'department_id': pd.Series(dtype='str'),
        'appointment_date': pd.Series(dtype='object'),
        'check_in_time': pd.Series(dtype='str'),
        'consultation_start_time': pd.Series(dtype='str'),
        'consultation_end_time': pd.Series(dtype='str'),
        'status': pd.Series(dtype='str'),
        'waiting_time_minutes': pd.Series(dtype='float'),
        'no_show': pd.Series(dtype='int')
    }).to_sql('fact_appointments', engine, index=False, if_exists='replace')

    pd.DataFrame({
        'rule_name': pd.Series(dtype='str'),
        'table_name': pd.Series(dtype='str'),
        'severity': pd.Series(dtype='str'),
        'passed': pd.Series(dtype='str'),
        'details': pd.Series(dtype='str'),
        'checked_at': pd.Series(dtype='object'),
        'run_id': pd.Series(dtype='str')
    }).to_sql('data_quality_results', engine, index=False, if_exists='replace')

    pd.DataFrame({
        'run_id': pd.Series(dtype='str'),
        'status': pd.Series(dtype='str'),
        'start_time': pd.Series(dtype='object'),
        'end_time': pd.Series(dtype='object'),
        'duration_seconds': pd.Series(dtype='float')
    }).to_sql('pipeline_runs', engine, index=False, if_exists='replace')
    
    yield engine
    
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture
def sample_patient_df():
    """Sample patient dataframe."""
    return pd.DataFrame([
        {'patient_id': 'P-12345', 'first_name': 'John', 'last_name': 'Doe',
         'date_of_birth': '1990-01-01', 'gender': 'M', 'phone': '123',
         'email': 'john@example.com', 'blood_group': 'O+'}
    ])
