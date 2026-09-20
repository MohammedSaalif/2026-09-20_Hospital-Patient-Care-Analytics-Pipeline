import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger('hospital_pipeline')

def calculate_risk_scores(patients_df: pd.DataFrame, appointments_df: pd.DataFrame, 
                          lab_results_df: pd.DataFrame, wearable_df: pd.DataFrame, 
                          notes_df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    Calculates patient risk scores based on aggregated clinical data.
    Returns a DataFrame of patient_id, risk_score, risk_level, risk_reasons, assessed_date.
    """
    logger.info("Calculating patient risk scores...")
    
    if patients_df.empty:
        return pd.DataFrame()
        
    risk_records = []
    now = datetime.now()
    
    for _, patient in patients_df.iterrows():
        p_id = patient['patient_id']
        score = 0
        reasons = []
        
        # Age rules
        age = 0
        if pd.notna(patient.get('date_of_birth')):
            try:
                dob = pd.to_datetime(patient['date_of_birth'])
                age = (now - dob).days / 365.25
            except:
                pass
                
        if age > 65:
            score += 2
            reasons.append('Age over 65')
        if age > 80:
            score += 1
            reasons.append('Age over 80')
            
        # Lab rules
        if not lab_results_df.empty:
            p_labs = lab_results_df[lab_results_df['patient_id'] == p_id]
            if not p_labs.empty and 'abnormal_flag' in p_labs.columns:
                abnormals = p_labs['abnormal_flag'].sum()
                if abnormals > 0:
                    score += 2
                    reasons.append('Abnormal lab results detected')
                if abnormals > 2:
                    score += 1
                    reasons.append('Multiple abnormal lab results')
                    
        # Wearable rules
        if not wearable_df.empty:
            p_wear = wearable_df[wearable_df['patient_id'] == p_id]
            if not p_wear.empty:
                if 'avg_spo2' in p_wear.columns and p_wear['avg_spo2'].mean() < 95:
                    score += 3
                    reasons.append('Low blood oxygen level')
                if 'avg_heart_rate' in p_wear.columns and p_wear['avg_heart_rate'].mean() > 100:
                    score += 2
                    reasons.append('Elevated heart rate')
                    
        # Appointment rules
        if not appointments_df.empty:
            p_appts = appointments_df[appointments_df['patient_id'] == p_id]
            if not p_appts.empty and 'no_show' in p_appts.columns:
                no_shows = p_appts['no_show'].sum()
                if no_shows > 1:
                    score += 1
                    reasons.append('Multiple missed appointments')
                    
        # Notes rules
        if not notes_df.empty:
            p_notes = notes_df[notes_df['patient_id'] == p_id]
            if not p_notes.empty:
                if 'chest_pain_flag' in p_notes.columns and p_notes['chest_pain_flag'].sum() > 0:
                    score += 2
                    reasons.append('Chest pain reported')
                if 'diabetes_flag' in p_notes.columns and p_notes['diabetes_flag'].sum() > 0:
                    score += 1
                    reasons.append('Diabetes indicated')
                if 'hypertension_flag' in p_notes.columns and p_notes['hypertension_flag'].sum() > 0:
                    score += 1
                    reasons.append('Hypertension indicated')
                    
        # Thresholds
        if score <= 3:
            level = 'Low'
        elif score <= 6:
            level = 'Medium'
        else:
            level = 'High'
            
        risk_records.append({
            'patient_id': p_id,
            'risk_score': score,
            'risk_level': level,
            'risk_reasons': '; '.join(reasons) if reasons else 'None',
            'assessed_date': now.date().isoformat(),
            'run_id': run_id
        })
        
    risk_df = pd.DataFrame(risk_records)
    logger.info(f"Calculated risk scores for {len(risk_df)} patients.")
    return risk_df

def train_demo_model(df: pd.DataFrame):
    """
    DEMO ONLY - trained on synthetic data.
    Demonstrates training a simple risk prediction model.
    """
    try:
        from sklearn.linear_model import LogisticRegression
        # Model training logic would go here
        logger.info("DEMO ONLY: Model training mock function called.")
    except ImportError:
        logger.warning("scikit-learn not installed, skipping demo model.")
