import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger('hospital_pipeline')

def _check_rule(data, condition, rule_name, table_name, severity):
    passed = condition.all()
    failed_count = (~condition).sum() if not passed else 0
    
    details = f"All rows passed." if passed else f"{failed_count} rows failed."
    
    return {
        'rule_name': rule_name,
        'table_name': table_name,
        'severity': severity,
        'passed': bool(passed),
        'details': details,
        'checked_at': datetime.now().isoformat()
    }

def validate(data: dict[str, pd.DataFrame], run_id: str) -> tuple[bool, list[dict]]:
    """
    Rules-based data quality validation engine.
    """
    logger.info("Starting data quality validation...")
    results = []
    
    # Tables
    patients = data.get('patients', pd.DataFrame())
    appointments = data.get('appointments', pd.DataFrame())
    labs = data.get('lab_results', pd.DataFrame())
    wearables = data.get('wearable_readings', pd.DataFrame())
    notes = data.get('consultation_notes', pd.DataFrame())
    
    # 1. NOT_NULL_PK
    for table_name, df in data.items():
        if df.empty: continue
        pk = f"{table_name[:-1]}_id" if table_name.endswith('s') else f"{table_name}_id"
        if table_name == 'wearable_readings': pk = 'patient_id' # it's aggregated
        
        if pk in df.columns:
            cond = df[pk].notna()
            results.append(_check_rule(df, cond, 'NOT_NULL_PK', table_name, 'critical'))

    # 2. UNIQUE_PK
    for table_name, df in data.items():
        if df.empty: continue
        pk = f"{table_name[:-1]}_id" if table_name.endswith('s') else f"{table_name}_id"
        if table_name == 'wearable_readings': pk = ['patient_id', 'reading_date']
        
        if type(pk) is str and pk in df.columns:
            cond = ~df[pk].duplicated(keep=False)
            results.append(_check_rule(df, cond, 'UNIQUE_PK', table_name, 'critical'))
        elif type(pk) is list and all(c in df.columns for c in pk):
            cond = ~df.duplicated(subset=pk, keep=False)
            results.append(_check_rule(df, cond, 'UNIQUE_PK', table_name, 'critical'))

    # 3. VALID_HEART_RATE
    if not wearables.empty and 'avg_heart_rate' in wearables.columns:
        cond = (wearables['avg_heart_rate'] >= 30) & (wearables['avg_heart_rate'] <= 220)
        results.append(_check_rule(wearables, cond, 'VALID_HEART_RATE', 'wearable_readings', 'critical'))

    # 4. VALID_SPO2
    if not wearables.empty and 'avg_spo2' in wearables.columns:
        cond = (wearables['avg_spo2'] >= 70) & (wearables['avg_spo2'] <= 100)
        results.append(_check_rule(wearables, cond, 'VALID_SPO2', 'wearable_readings', 'critical'))
        
    # 5. REF_INTEGRITY_PATIENT
    valid_patients = set(patients['patient_id'].unique()) if not patients.empty else set()
    for table_name, df in data.items():
        if table_name != 'patients' and not df.empty and 'patient_id' in df.columns:
            cond = df['patient_id'].isin(valid_patients)
            results.append(_check_rule(df, cond, 'REF_INTEGRITY_PATIENT', table_name, 'critical'))

    # 6. REF_INTEGRITY_DOCTOR
    doctors = data.get('doctors', pd.DataFrame())
    valid_doctors = set(doctors['doctor_id'].unique()) if not doctors.empty else set()
    if not appointments.empty and 'doctor_id' in appointments.columns:
        cond = appointments['doctor_id'].isin(valid_doctors)
        results.append(_check_rule(appointments, cond, 'REF_INTEGRITY_DOCTOR', 'appointments', 'critical'))

    # 7. COMPLETENESS_90
    for table_name, df in data.items():
        if df.empty: continue
        completeness = df.notna().mean().mean()
        passed = completeness >= 0.90
        results.append({
            'rule_name': 'COMPLETENESS_90',
            'table_name': table_name,
            'severity': 'soft',
            'passed': bool(passed),
            'details': f"Completeness is {completeness*100:.1f}%",
            'checked_at': datetime.now().isoformat()
        })
        
    # 8. VALID_GENDER
    if not patients.empty and 'gender' in patients.columns:
        cond = patients['gender'].isin(['M', 'F'])
        results.append(_check_rule(patients, cond, 'VALID_GENDER', 'patients', 'soft'))

    # 9. POSITIVE_WAIT_TIME
    if not appointments.empty and 'waiting_time_minutes' in appointments.columns:
        cond = appointments['waiting_time_minutes'] >= 0
        results.append(_check_rule(appointments, cond, 'POSITIVE_WAIT_TIME', 'appointments', 'soft'))

    # Summarize
    all_critical_passed = True
    for r in results:
        level_str = "CRITICAL" if r['severity'] == 'critical' else "SOFT"
        pass_str = "PASSED" if r['passed'] else "FAILED"
        logger.info(f"[{level_str}] {r['rule_name']} on {r['table_name']}: {pass_str} - {r['details']}")
        
        if r['severity'] == 'critical' and not r['passed']:
            all_critical_passed = False
            
    if not all_critical_passed:
        logger.error("Data validation failed on one or more critical rules.")
    else:
        logger.info("All critical data validation rules passed.")
        
    return all_critical_passed, results
