import pytest
import pandas as pd
from datetime import datetime
from src.hospital_pipeline.risk import calculate_risk_scores

def test_elderly_patient_age_points():
    """Test elderly patient gets age points."""
    patients_df = pd.DataFrame({'patient_id': ['P-1'], 'date_of_birth': ['1930-01-01']})
    res = calculate_risk_scores(patients_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 'test')
    assert res['risk_score'].iloc[0] == 3 # >65 (2) + >80 (1)

def test_abnormal_labs_score():
    """Test abnormal labs increase score."""
    patients_df = pd.DataFrame({'patient_id': ['P-1'], 'date_of_birth': ['1990-01-01']})
    labs_df = pd.DataFrame({'patient_id': ['P-1', 'P-1', 'P-1'], 'abnormal_flag': [1, 1, 1]})
    res = calculate_risk_scores(patients_df, pd.DataFrame(), labs_df, pd.DataFrame(), pd.DataFrame(), 'test')
    assert res['risk_score'].iloc[0] == 3 # >0 (2) + >2 (1)

def test_low_spo2_score():
    """Test low SpO2 gives high points."""
    patients_df = pd.DataFrame({'patient_id': ['P-1'], 'date_of_birth': ['1990-01-01']})
    wearables_df = pd.DataFrame({'patient_id': ['P-1'], 'avg_spo2': [90]})
    res = calculate_risk_scores(patients_df, pd.DataFrame(), pd.DataFrame(), wearables_df, pd.DataFrame(), 'test')
    assert res['risk_score'].iloc[0] == 3 # <95 (3)

def test_chest_pain_flag_score():
    """Test chest pain flag increases score."""
    patients_df = pd.DataFrame({'patient_id': ['P-1'], 'date_of_birth': ['1990-01-01']})
    notes_df = pd.DataFrame({'patient_id': ['P-1'], 'chest_pain_flag': [1]})
    res = calculate_risk_scores(patients_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), notes_df, 'test')
    assert res['risk_score'].iloc[0] == 2 # chest pain (2)

def test_threshold_classification():
    """Test threshold classification (Low/Medium/High)."""
    patients_df = pd.DataFrame({'patient_id': ['P-1', 'P-2', 'P-3']})
    notes_df = pd.DataFrame({
        'patient_id': ['P-1', 'P-2', 'P-3'], 
        'chest_pain_flag': [0, 1, 1], # 0, 2, 2
        'diabetes_flag': [0, 1, 1],   # 0, 1, 1 -> 0, 3, 3
        'hypertension_flag': [0, 1, 1] # 0, 1, 1 -> 0, 4, 4
    })
    wearables_df = pd.DataFrame({
        'patient_id': ['P-3'], 'avg_spo2': [90] # +3 -> 7
    })
    res = calculate_risk_scores(patients_df, pd.DataFrame(), pd.DataFrame(), wearables_df, notes_df, 'test')
    scores = res.set_index('patient_id')['risk_level'].to_dict()
    assert scores['P-1'] == 'Low'      # score: 0
    assert scores['P-2'] == 'Medium'   # score: 4
    assert scores['P-3'] == 'High'     # score: 7

def test_risk_reasons():
    """Test risk_reasons contains correct reasons."""
    patients_df = pd.DataFrame({'patient_id': ['P-1'], 'date_of_birth': ['1930-01-01']}) # >80
    res = calculate_risk_scores(patients_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 'test')
    reasons = res['risk_reasons'].iloc[0]
    assert 'Age over 65' in reasons
    assert 'Age over 80' in reasons
