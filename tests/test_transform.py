import pytest
import pandas as pd
from hospital_pipeline.transform import transform
import hashlib

def test_deduplication():
    """Test deduplication removes duplicates based on patient_id."""
    df = pd.DataFrame([
        {'patient_id': 'P-1', 'first_name': 'John'},
        {'patient_id': 'P-1', 'first_name': 'John'}
    ])
    res = transform({'patients': df}, 'test_run')
    assert len(res['patients']) == 1

def test_date_standardization():
    """Test date standardization handles invalid dates."""
    df = pd.DataFrame([
        {'patient_id': 'P-1', 'date_of_birth': 'invalid_date'},
        {'patient_id': 'P-2', 'date_of_birth': '1990-01-01'}
    ])
    res = transform({'patients': df}, 'test_run')
    dates = res['patients']['date_of_birth'].tolist()
    assert pd.isna(dates[0])
    assert pd.notna(dates[1])

def test_id_normalization():
    """Test ID normalization (various formats -> P-XXXXX)."""
    df = pd.DataFrame([
        {'patient_id': 'P-1', 'first_name': 'A'},
        {'patient_id': '2', 'first_name': 'B'},
        {'patient_id': '0003', 'first_name': 'C'}
    ])
    res = transform({'patients': df}, 'test_run')
    ids = res['patients']['patient_id'].tolist()
    assert 'P-00001' in ids
    assert 'P-00002' in ids
    assert 'P-00003' in ids

def test_outlier_capping():
    """Test outlier capping (heart_rate, spo2)."""
    df = pd.DataFrame([
        {'patient_id': 'P-00001', 'timestamp': '2023-01-01 10:00:00', 'heart_rate': 300, 'spo2': 50, 'steps': 200000}
    ])
    res = transform({'wearable_readings': df}, 'test_run')
    cap_hr = res['wearable_readings']['max_heart_rate'].iloc[0]
    cap_spo2 = res['wearable_readings']['avg_spo2'].iloc[0]
    assert cap_hr == 220
    assert cap_spo2 == 70

def test_waiting_time_minutes():
    """Test waiting_time_minutes calculation."""
    df = pd.DataFrame([
        {'appointment_id': 'A-1', 'check_in_time': '10:00:00', 'consultation_start_time': '10:30:00', 'status': 'completed'}
    ])
    res = transform({'appointments': df}, 'test_run')
    assert res['appointments']['waiting_time_minutes'].iloc[0] == 30.0

def test_no_show_flag():
    """Test no_show flag calculation."""
    df = pd.DataFrame([
        {'appointment_id': 'A-1', 'status': 'no_show'},
        {'appointment_id': 'A-2', 'status': 'completed'}
    ])
    res = transform({'appointments': df}, 'test_run')
    assert res['appointments'][res['appointments']['appointment_id'] == 'A-1']['no_show'].iloc[0] == 1
    assert res['appointments'][res['appointments']['appointment_id'] == 'A-2']['no_show'].iloc[0] == 0

def test_abnormal_flag():
    """Test abnormal_flag calculation."""
    df = pd.DataFrame([
        {'lab_result_id': 'L-1', 'result_value': 5, 'normal_range_low': 10, 'normal_range_high': 20}, # abnormal
        {'lab_result_id': 'L-2', 'result_value': 15, 'normal_range_low': 10, 'normal_range_high': 20}  # normal
    ])
    res = transform({'lab_results': df}, 'test_run')
    assert res['lab_results']['abnormal_flag'].tolist() == [1, 0]

def test_phi_masking():
    """Test PHI masking produces consistent hashes."""
    df = pd.DataFrame([
        {'patient_id': 'P-1', 'first_name': 'John', 'last_name': 'Doe', 'phone': '123'}
    ])
    res = transform({'patients': df}, 'test_run')
    assert 'first_name' not in res['patients'].columns
    expected_hash = hashlib.sha256('JohnDoe'.encode('utf-8')).hexdigest()
    assert res['patients']['name_hash'].iloc[0] == expected_hash
