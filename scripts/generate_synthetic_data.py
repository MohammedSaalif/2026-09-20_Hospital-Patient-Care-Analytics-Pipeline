import os
import random
import csv
import json
from datetime import datetime, timedelta

def generate_synthetic_data():
    """Generates synthetic hospital data with deliberate defects."""
    random.seed(42)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'))
    os.makedirs(base_dir, exist_ok=True)
    
    print(f"Generating data in {base_dir}...")
    
    # 1. Departments
    departments = [
        ("DEPT-01", "Cardiology", 1),
        ("DEPT-02", "Orthopedics", 2),
        ("DEPT-03", "General Medicine", 1),
        ("DEPT-04", "Pediatrics", 3),
        ("DEPT-05", "Neurology", 4),
        ("DEPT-06", "Dermatology", 2),
        ("DEPT-07", "Oncology", 5),
        ("DEPT-08", "Emergency", 0)
    ]
    with open(os.path.join(base_dir, 'departments.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['department_id', 'department_name', 'floor_number'])
        writer.writerows(departments)
    
    # 2. Doctors
    doctor_ids = []
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Charles", "Joseph", "Thomas", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    doctors = []
    for i in range(1, 31):
        d_id = f"D-{i:04d}"
        doctor_ids.append(d_id)
        dept = random.choice(departments)
        doctors.append([
            d_id,
            random.choice(first_names),
            random.choice(last_names),
            dept[1],  # specialization
            dept[0]   # department_id
        ])
    with open(os.path.join(base_dir, 'doctors.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['doctor_id', 'first_name', 'last_name', 'specialization', 'department_id'])
        writer.writerows(doctors)

    # 3. Patients
    patient_ids = []
    patients = []
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    for i in range(1, 201):
        p_id = f"P-{i:05d}"
        
        # Defect: inconsistent IDs
        if random.random() < 0.05:
            p_id = f"P-{i}"
        elif random.random() < 0.05:
            p_id = str(i)
            
        patient_ids.append(p_id)
        
        gender = random.choice(['M', 'F'])
        phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        email = f"patient{i}@example.com"
        bg = random.choice(blood_groups)
        
        # Defect: nulls
        if random.random() < 0.05: phone = ''
        if random.random() < 0.05: email = ''
        
        dob_year = random.randint(1940, 2022)
        dob_month = random.randint(1, 12)
        dob_day = random.randint(1, 28)
        dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"
        
        # Defect: invalid dates
        if random.random() < 0.02:
            dob = "2025-13-45"
            
        reg_date = f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        
        patients.append([p_id, random.choice(first_names), random.choice(last_names), dob, gender, phone, email, bg, reg_date])
    
    with open(os.path.join(base_dir, 'patients.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'email', 'blood_group', 'registration_date'])
        writer.writerows(patients)

    # 4. Appointments
    appointments = []
    appointment_ids = []
    for i in range(1, 501):
        apt_id = f"APT-{i:05d}"
        appointment_ids.append(apt_id)
        p_id = random.choice(patient_ids)
        doc = random.choice(doctors)
        d_id = doc[0]
        dept_id = doc[4]
        
        date = datetime(2023, random.randint(1, 12), random.randint(1, 28))
        date_str = date.strftime('%Y-%m-%d')
        
        check_in = date + timedelta(hours=random.randint(8, 16), minutes=random.randint(0, 59))
        start = check_in + timedelta(minutes=random.randint(5, 60))
        end = start + timedelta(minutes=random.randint(15, 45))
        
        status = random.choice(['completed', 'completed', 'completed', 'no_show', 'cancelled'])
        
        row = [apt_id, p_id, d_id, dept_id, date_str, check_in.strftime('%H:%M:%S'), start.strftime('%H:%M:%S'), end.strftime('%H:%M:%S'), status]
        appointments.append(row)
        
        # Defect: duplicates
        if random.random() < 0.03:
            appointments.append(row)

    with open(os.path.join(base_dir, 'appointments.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['appointment_id', 'patient_id', 'doctor_id', 'department_id', 'appointment_date', 'check_in_time', 'consultation_start_time', 'consultation_end_time', 'status'])
        writer.writerows(appointments)

    # 5. Lab Results
    labs = []
    test_types = [
        ("Hemoglobin", "g/dL", 13.8, 17.2),
        ("WBC", "k/uL", 4.5, 11.0),
        ("Platelets", "k/uL", 150, 450),
        ("Glucose", "mg/dL", 70, 99),
        ("Cholesterol", "mg/dL", 0, 200)
    ]
    for i in range(1, 301):
        lab_id = f"LAB-{i:05d}"
        p_id = random.choice(patient_ids)
        test = random.choice(test_types)
        
        date = datetime(2023, random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d')
        val = random.uniform(test[2]*0.8, test[3]*1.2)
        
        nl, nh = test[2], test[3]
        # Defect: missing ranges
        if random.random() < 0.05:
            nl, nh = '', ''
            
        row = [lab_id, p_id, test[0], date, round(val, 2), test[1], nl, nh]
        labs.append(row)
        
        # Defect: duplicates
        if random.random() < 0.03:
            labs.append(row)

    with open(os.path.join(base_dir, 'lab_results.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lab_result_id', 'patient_id', 'test_name', 'test_date', 'result_value', 'result_unit', 'normal_range_low', 'normal_range_high'])
        writer.writerows(labs)

    # 6. Wearable Readings
    wearables = []
    for i in range(1, 2001):
        w_id = f"WR-{i:06d}"
        p_id = random.choice(patient_ids)
        ts = datetime(2023, random.randint(1, 12), random.randint(1, 28), random.randint(0, 23), random.randint(0, 59)).isoformat()
        
        hr = random.randint(60, 100)
        spo2 = random.randint(95, 100)
        
        # Defect: out of range
        if random.random() < 0.02: hr = random.choice([10, 300])
        if random.random() < 0.02: spo2 = random.choice([50, 110])
            
        steps = random.randint(0, 15000)
        
        wearables.append({
            "reading_id": w_id,
            "patient_id": p_id,
            "timestamp": ts,
            "heart_rate": hr,
            "spo2": spo2,
            "steps": steps
        })
        
    with open(os.path.join(base_dir, 'wearable_readings.json'), 'w') as f:
        json.dump(wearables, f, indent=2)

    # 7. Consultation Notes
    notes = []
    keywords = ['chest pain', 'diabetes', 'hypertension', 'shortness of breath', 'follow-up needed', 'patient is healthy', 'no symptoms']
    for i in range(1, 151):
        n_id = f"CN-{i:05d}"
        apt = random.choice(appointments)
        p_id = apt[1]
        d_id = apt[2]
        apt_id = apt[0]
        
        kw1 = random.choice(keywords)
        kw2 = random.choice(keywords)
        text = f"Patient presented with {kw1}. Discussed test results. {kw2.capitalize()}."
        
        notes.append({
            "note_id": n_id,
            "patient_id": p_id,
            "doctor_id": d_id,
            "appointment_id": apt_id,
            "note_date": apt[4],
            "note_text": text
        })

    with open(os.path.join(base_dir, 'consultation_notes.json'), 'w') as f:
        json.dump(notes, f, indent=2)

    print("Data generation complete.")
    print(f"Generated: {len(departments)} departments, {len(doctors)} doctors, {len(patients)} patients")
    print(f"Generated: {len(appointments)} appointments, {len(labs)} lab results")
    print(f"Generated: {len(wearables)} wearable readings, {len(notes)} consultation notes")

if __name__ == '__main__':
    generate_synthetic_data()
