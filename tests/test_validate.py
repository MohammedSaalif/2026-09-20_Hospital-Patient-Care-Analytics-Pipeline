import pytest
import pandas as pd
from src.hospital_pipeline.validate import validate

def test_null_pk_fails():
    """Test critical rule: null PK fails."""
    df = pd.DataFrame({'patient_id': [None, 'P-00001']})
    passed, results = validate({'patients': df}, 'test_run')
    assert not passed
    null_pk_rule = next((r for r in results if r['rule_name'] == 'NOT_NULL_PK' and r['table_name'] == 'patients'), None)
    assert not null_pk_rule['passed']

def test_duplicate_pk_fails():
    """Test critical rule: duplicate PK fails."""
    df = pd.DataFrame({'patient_id': ['P-1', 'P-1']})
    passed, results = validate({'patients': df}, 'test_run')
    assert not passed
    dup_pk_rule = next((r for r in results if r['rule_name'] == 'UNIQUE_PK' and r['table_name'] == 'patients'), None)
    assert not dup_pk_rule['passed']

def test_out_of_range_heart_rate_fails():
    """Test critical rule: out-of-range heart_rate fails."""
    df = pd.DataFrame({'patient_id': ['P-1'], 'reading_date': ['2023-01-01'], 'avg_heart_rate': [250]})
    passed, results = validate({'wearable_readings': df}, 'test_run')
    assert not passed
    hr_rule = next((r for r in results if r['rule_name'] == 'VALID_HEART_RATE'), None)
    assert not hr_rule['passed']

def test_incomplete_data_soft_rule():
    """Test soft rule: incomplete data warns but doesn't fail pipeline."""
    # Data missing 20%
    df = pd.DataFrame({
        'patient_id': ['P-1', 'P-2', 'P-3', 'P-4', 'P-5'],
        'col_a': [1, 2, None, None, None]  # 40% complete
    })
    passed, results = validate({'patients': df}, 'test_run')
    # Should still pass if only soft rules fail
    assert passed
    comp_rule = next((r for r in results if r['rule_name'] == 'COMPLETENESS_90'), None)
    assert not comp_rule['passed']

def test_all_rules_run():
    """Test that all rules run (not just first failure)."""
    df = pd.DataFrame({'patient_id': [None, None]}) # Fails NOT_NULL_PK and UNIQUE_PK
    passed, results = validate({'patients': df}, 'test_run')
    assert not passed
    failed_rules = [r['rule_name'] for r in results if not r['passed']]
    assert 'NOT_NULL_PK' in failed_rules
    assert 'UNIQUE_PK' in failed_rules
    assert len(results) > 1

def test_all_method_called():
    """Test .all() is called correctly."""
    # The fix ensures pandas series .all() is used instead of boolean context error
    df = pd.DataFrame({'patient_id': ['P-1', 'P-2']})
    passed, results = validate({'patients': df}, 'test_run')
    assert passed # If it evaluates without raising ValueError: The truth value of a Series is ambiguous, it's correct
