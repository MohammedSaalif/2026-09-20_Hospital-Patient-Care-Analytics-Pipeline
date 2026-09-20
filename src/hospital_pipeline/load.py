import pandas as pd
import logging
from sqlalchemy import MetaData, Table, Column, String, Integer, Float, Date, DateTime, Boolean, text

logger = logging.getLogger('hospital_pipeline')

def _upsert(df: pd.DataFrame, table_name: str, engine, primary_key: str | list):
    """
    Performs an upsert based on the database dialect.
    """
    if df.empty: return 0
    
    dialect = engine.dialect.name
    
    # First, let pandas create the table if it doesn't exist to ensure schema is ok
    # We use if_exists='append' to not drop the table if it exists
    try:
        df.head(0).to_sql(table_name, con=engine, if_exists='append', index=False)
    except:
        pass # Table likely exists
        
    if dialect == 'mysql':
        # MySQL INSERT ... ON DUPLICATE KEY UPDATE
        with engine.begin() as conn:
            for _, row in df.iterrows():
                row_dict = row.where(pd.notnull(row), None).to_dict()
                columns = ', '.join([f"`{k}`" for k in row_dict.keys()])
                placeholders = ', '.join([f":{k}" for k in row_dict.keys()])
                updates = ', '.join([f"`{k}` = VALUES(`{k}`)" for k in row_dict.keys()])
                
                sql = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}")
                conn.execute(sql, row_dict)
    elif dialect == 'sqlite':
        # SQLite uses REPLACE or INSERT ... ON CONFLICT (requires proper PK setup which we might not have explicitly via pandas)
        # Using a simpler DELETE then INSERT approach for idempotency in SQLite demo
        if type(primary_key) is str:
            pk_cols = [primary_key]
        else:
            pk_cols = primary_key
            
        with engine.begin() as conn:
            for _, row in df.iterrows():
                row_dict = row.where(pd.notnull(row), None).to_dict()
                
                # Delete existing
                where_clause = " AND ".join([f"{k} = :{k}" for k in pk_cols])
                conn.execute(text(f"DELETE FROM {table_name} WHERE {where_clause}"), row_dict)
                
                # Insert new
                columns = ', '.join(row_dict.keys())
                placeholders = ', '.join([f":{k}" for k in row_dict.keys()])
                conn.execute(text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"), row_dict)
    else:
        # Fallback to standard append
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        
    return len(df)

def load(data: dict[str, pd.DataFrame], engine, run_id: str) -> dict[str, int]:
    """
    Loads transformed and validated data into the database.
    """
    table_mapping = {
        'patients': ('dim_patient', 'patient_id'),
        'doctors': ('dim_doctor', 'doctor_id'),
        'departments': ('dim_department', 'department_id'),
        'appointments': ('fact_appointments', 'appointment_id'),
        'lab_results': ('fact_lab_results', 'lab_result_id'),
        'wearable_readings': ('fact_wearable_readings', ['patient_id', 'reading_date']),
        'patient_risk': ('fact_patient_risk', 'patient_id')
    }
    
    loaded_counts = {}
    
    for name, df in data.items():
        if df.empty:
            logger.info(f"Skipping load for {name} - DataFrame is empty.")
            loaded_counts[name] = 0
            continue
            
        if name not in table_mapping:
            continue
            
        table_name, pk = table_mapping[name]
        logger.info(f"Loading {name} into {table_name}...")
        
        try:
            count = _upsert(df, table_name, engine, pk)
            loaded_counts[table_name] = count
            logger.info(f"Successfully loaded {count} rows into {table_name}.")
        except Exception as e:
            logger.error(f"Failed to load {name} into {table_name}: {str(e)}")
            raise
            
    return loaded_counts
