import pandas as pd
import numpy as np
import hashlib
import logging
import os
from src.hospital_pipeline.config import STAGING_DATA_DIR

logger = logging.getLogger('hospital_pipeline')

def _hash_value(val):
    if pd.isna(val) or val == '':
        return val
    return hashlib.sha256(str(val).encode('utf-8')).hexdigest()

def transform(raw_data: dict[str, pd.DataFrame], run_id: str) -> dict[str, pd.DataFrame]:
    """
    Cleans, normalizes, and enriches raw data.
    """
    transformed = {}
    os.makedirs(STAGING_DATA_DIR, exist_ok=True)
    
    for name, df in raw_data.items():
        if df.empty:
            transformed[name] = df
            continue
            
        logger.info(f"Transforming {name} ({len(df)} rows)...")
        df_clean = df.copy()
        
        # Standardize IDs (especially patient_id)
        if 'patient_id' in df_clean.columns:
            # Handle forms like 'P-1', '1', '0001' -> 'P-00001'
            df_clean['patient_id'] = df_clean['patient_id'].astype(str).str.replace('P-', '', regex=False)
            df_clean['patient_id'] = df_clean['patient_id'].apply(lambda x: f"P-{str(x).zfill(5)}" if x and x != 'nan' else x)
            
        # Standardize Dates
        date_cols = [c for c in df_clean.columns if 'date' in c.lower() or 'timestamp' in c.lower() or 'time' in c.lower()]
        for col in date_cols:
            if 'time' in col.lower() and 'date' not in col.lower() and 'timestamp' not in col.lower():
                # Just time like '08:30:00', skip converting to full datetime or let it be
                pass
            else:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        
        # Deduplicate
        if 'patient_id' in df_clean.columns and name == 'patients':
            df_clean = df_clean.drop_duplicates(subset=['patient_id'])
        elif 'appointment_id' in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=['appointment_id'])
        elif 'lab_result_id' in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=['lab_result_id'])
        elif 'reading_id' in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=['reading_id'])
        elif 'note_id' in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=['note_id'])

        # Patients specific
        if name == 'patients':
            if 'gender' in df_clean.columns:
                df_clean['gender'] = df_clean['gender'].fillna(df_clean['gender'].mode()[0] if not df_clean['gender'].mode().empty else 'U')
            if 'blood_group' in df_clean.columns:
                df_clean['blood_group'] = df_clean['blood_group'].fillna(df_clean['blood_group'].mode()[0] if not df_clean['blood_group'].mode().empty else 'Unknown')
                
            # PHI Masking
            if 'first_name' in df_clean.columns and 'last_name' in df_clean.columns:
                df_clean['name_hash'] = df_clean['first_name'].astype(str) + df_clean['last_name'].astype(str)
                df_clean['name_hash'] = df_clean['name_hash'].apply(_hash_value)
            if 'phone' in df_clean.columns:
                df_clean['phone_hash'] = df_clean['phone'].apply(_hash_value)
            df_clean = df_clean.drop(columns=['first_name', 'last_name', 'phone', 'email'], errors='ignore')
            
        # Appointments specific
        if name == 'appointments':
            # Calculate wait time
            try:
                check_in = pd.to_timedelta(df_clean['check_in_time'].astype(str))
                start = pd.to_timedelta(df_clean['consultation_start_time'].astype(str))
                df_clean['waiting_time_minutes'] = (start - check_in).dt.total_seconds() / 60.0
            except:
                df_clean['waiting_time_minutes'] = 0
                
            df_clean['no_show'] = (df_clean['status'] == 'no_show').astype(int)
            
            if 'patients' in raw_data and not raw_data['patients'].empty:
                pat_df = raw_data['patients'].copy()
                pat_df['patient_id'] = pat_df['patient_id'].astype(str).str.replace('P-', '').str.zfill(5).apply(lambda x: f"P-{x}")
                pat_df['date_of_birth'] = pd.to_datetime(pat_df['date_of_birth'], errors='coerce')
                
                # Approximate age
                now = pd.Timestamp.now()
                pat_df['age'] = (now - pat_df['date_of_birth']).dt.days / 365.25
                
                merged = df_clean.merge(pat_df[['patient_id', 'age']], on='patient_id', how='left')
                bins = [-1, 17, 35, 55, 70, 150]
                labels = ['Pediatric', 'Young Adult', 'Middle Aged', 'Senior', 'Elderly']
                df_clean['age_group'] = pd.cut(merged['age'], bins=bins, labels=labels)
            
        # Lab Results specific
        if name == 'lab_results':
            df_clean['result_value'] = pd.to_numeric(df_clean['result_value'], errors='coerce')
            df_clean['normal_range_low'] = pd.to_numeric(df_clean['normal_range_low'], errors='coerce')
            df_clean['normal_range_high'] = pd.to_numeric(df_clean['normal_range_high'], errors='coerce')
            
            df_clean['result_value'] = df_clean['result_value'].fillna(df_clean['result_value'].median())
            
            abnormal = (df_clean['result_value'] < df_clean['normal_range_low']) | (df_clean['result_value'] > df_clean['normal_range_high'])
            df_clean['abnormal_flag'] = abnormal.astype(int)

        # Wearables specific
        if name == 'wearable_readings':
            df_clean['heart_rate'] = pd.to_numeric(df_clean['heart_rate'], errors='coerce')
            df_clean['spo2'] = pd.to_numeric(df_clean['spo2'], errors='coerce')
            df_clean['steps'] = pd.to_numeric(df_clean['steps'], errors='coerce')
            
            # Impute and Cap Outliers
            df_clean['heart_rate'] = df_clean['heart_rate'].fillna(df_clean['heart_rate'].median())
            df_clean['spo2'] = df_clean['spo2'].fillna(df_clean['spo2'].median())
            
            df_clean['heart_rate'] = df_clean['heart_rate'].clip(lower=30, upper=220)
            df_clean['spo2'] = df_clean['spo2'].clip(lower=70, upper=100)
            df_clean['steps'] = df_clean['steps'].clip(lower=0, upper=100000)
            
            # Aggregate
            df_clean['reading_date'] = pd.to_datetime(df_clean['timestamp']).dt.date
            agg_df = df_clean.groupby(['patient_id', 'reading_date']).agg(
                avg_heart_rate=('heart_rate', 'mean'),
                min_heart_rate=('heart_rate', 'min'),
                max_heart_rate=('heart_rate', 'max'),
                avg_spo2=('spo2', 'mean'),
                total_steps=('steps', 'sum')
            ).reset_index()
            df_clean = agg_df

        # Notes specific
        if name == 'consultation_notes':
            df_clean['note_text'] = df_clean['note_text'].fillna('').astype(str).str.lower()
            df_clean['chest_pain_flag'] = df_clean['note_text'].str.contains('chest pain').astype(int)
            df_clean['diabetes_flag'] = df_clean['note_text'].str.contains('diabetes').astype(int)
            df_clean['hypertension_flag'] = df_clean['note_text'].str.contains('hypertension').astype(int)
            df_clean['shortness_of_breath_flag'] = df_clean['note_text'].str.contains('shortness of breath').astype(int)
            
        logger.info(f"Completed {name}: {len(df_clean)} rows remaining.")
        
        # Save to staging
        if name in ['wearable_readings', 'consultation_notes']:
            df_clean.to_json(os.path.join(STAGING_DATA_DIR, f"{name}.json"), orient='records')
        else:
            df_clean.to_csv(os.path.join(STAGING_DATA_DIR, f"{name}.csv"), index=False)
            
        transformed[name] = df_clean
        
    return transformed
