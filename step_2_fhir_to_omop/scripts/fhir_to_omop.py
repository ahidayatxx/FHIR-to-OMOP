import os
import json
import sqlite3
import hashlib
from datetime import datetime

# Resolve database and input data paths dynamically relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_2_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(step_2_dir)

db_path = os.path.join(step_2_dir, "data", "omop_cdm.db")
fhir_dir = os.path.join(project_root, "step_1_fhir_creation", "data", "fhir", "jakarta_hospital")

def tokenize_nik(nik_val):
    if not nik_val:
        return "tok_unknown"
    # Generate a secure, irreversible hash of the NIK to blind patient identity
    sha256_hash = hashlib.sha256(nik_val.encode('utf-8')).hexdigest()
    return f"tok_{sha256_hash[:16]}"

print("==============================================================")
print("Starting FHIR to OMOP CDM Transformation ETL...")
print(f"Reading FHIR files from: {os.path.relpath(fhir_dir, project_root)}")
print(f"Writing to SQLite OMOP DB: {os.path.relpath(db_path, project_root)}")
print("==============================================================")

if not os.path.exists(db_path):
    print("Error: SQLite Database not found. Please run initialize_omop_db.py first.")
    exit(1)

if not os.path.exists(fhir_dir) or len(os.listdir(fhir_dir)) == 0:
    print(f"Error: No FHIR bundle files found in {fhir_dir}.")
    exit(1)

# Establish database connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Pre-populate essential OMOP Concepts for referential mapping
print("\n[Step 1] Pre-populating standard OMOP vocabulary Concepts...")
concepts_to_insert = [
    # Genders
    (8507, "MALE", "Gender", "Gender", "Gender", "S", "M", "1970-01-01", "2099-12-31", None),
    (8532, "FEMALE", "Gender", "Gender", "Gender", "S", "F", "1970-01-01", "2099-12-31", None),
    # Visit Types
    (9202, "Outpatient Visit", "Visit", "OP", "Visit", "S", "OP", "1970-01-01", "2099-12-31", None),
    (9203, "Emergency Room Visit", "Visit", "ER", "Visit", "S", "ER", "1970-01-01", "2099-12-31", None),
    (9201, "Inpatient Visit", "Visit", "IP", "Visit", "S", "IP", "1970-01-01", "2099-12-31", None),
    (581477, "Telehealth Visit", "Visit", "TH", "Visit", "S", "TH", "1970-01-01", "2099-12-31", None),
    # ETL Types / Metadata Concepts
    (44818518, "EHR Record", "Type Concept", "OMOP", "Type Concept", "S", "EHR", "1970-01-01", "2099-12-31", None),
    (32817, "EHR Encounter Record", "Type Concept", "OMOP", "Type Concept", "S", "EHR", "1970-01-01", "2099-12-31", None),
    # Conditions (SNOMED to Standard Concepts mapping)
    (201820, "Diabetes mellitus type 2", "Condition", "SNOMED", "Clinical Finding", "S", "44054006", "1970-01-01", "2099-12-31", None),
    (316866, "Hypertensive disorder", "Condition", "SNOMED", "Clinical Finding", "S", "38341003", "1970-01-01", "2099-12-31", None),
    (317009, "Asthma", "Condition", "SNOMED", "Clinical Finding", "S", "195967001", "1970-01-01", "2099-12-31", None),
    (920355, "Urinary tract infection", "Condition", "SNOMED", "Clinical Finding", "S", "56265001", "1970-01-01", "2099-12-31", None),
    (432158, "Infection by Human immunodeficiency virus", "Condition", "SNOMED", "Clinical Finding", "S", "86406008", "1970-01-01", "2099-12-31", None),
    (4147775, "Microalbuminuria", "Condition", "SNOMED", "Clinical Finding", "S", "236403004", "1970-01-01", "2099-12-31", None),
    # Drugs (RxNorm to Standard Concepts mapping)
    (1529331, "Metformin hydrochloride 500 MG Extended Release Oral Tablet", "Drug", "RxNorm", "Clinical Drug", "S", "860975", "1970-01-01", "2099-12-31", None),
    (1398937, "insulin isophane, human 70 UNT/ML", "Drug", "RxNorm", "Clinical Drug", "S", "865091", "1970-01-01", "2099-12-31", None),
    # Measurements (LOINC to Standard Concepts mapping)
    (3004249, "Systolic blood pressure", "Measurement", "LOINC", "Clinical Observation", "S", "8480-6", "1970-01-01", "2099-12-31", None),
    (3004279, "Diastolic blood pressure", "Measurement", "Measurement", "Clinical Observation", "S", "8462-4", "1970-01-01", "2099-12-31", None)
]

cursor.executemany("""
    INSERT OR REPLACE INTO concept (
        concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, 
        standard_concept, concept_code, valid_start_date, valid_end_date, invalid_reason
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", concepts_to_insert)

# Dictionary for mapping FHIR IDs to OMOP database IDs
patient_id_map = {}
visit_id_map = {}

# Mappings of terminology codes to standard concept IDs
gender_map = {"male": 8507, "female": 8532}
visit_type_map = {
    "ambulatory": 9202,
    "emergency": 9203,
    "inpatient": 9201,
    "telehealth": 581477,
    "wellness": 9202
}
condition_code_map = {
    "44054006": 201820,
    "38341003": 316866,
    "195967001": 317009,
    "56265001": 920355,
    "86406008": 432158,
    "236403004": 4147775
}
drug_code_map = {
    "860975": 1529331,
    "865091": 1398937
}
measurement_code_map = {
    "8480-6": 3004249,
    "8462-4": 3004279
}

print("\n[Step 2] Processing FHIR patient records and populating OMOP CDM...")

files = [f for f in os.listdir(fhir_dir) if f.endswith(".json")]

# Counters for reporting
record_stats = {
    "persons": 0,
    "visits": 0,
    "conditions": 0,
    "drugs": 0,
    "measurements": 0
}

# Clear old entries in tables before loading to prevent duplicate testing conflicts
cursor.execute("DELETE FROM person")
cursor.execute("DELETE FROM visit_occurrence")
cursor.execute("DELETE FROM condition_occurrence")
cursor.execute("DELETE FROM drug_exposure")
cursor.execute("DELETE FROM measurement")

# Populate CARE_SITE table for RSUD Tarakan Jakarta
cursor.execute("DELETE FROM care_site")
cursor.execute("""
    INSERT INTO care_site (care_site_id, care_site_name, place_of_service_concept_id, location_id, care_site_source_value)
    VALUES (10000004, "RSUD Tarakan Jakarta", 9202, 1, "10000004")
""")

for filename in files:
    filepath = os.path.join(fhir_dir, filename)
    with open(filepath, 'r') as f:
        try:
            bundle = json.load(f)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
            
    entries = bundle.get("entry", [])
    resources = [entry.get("resource", {}) for entry in entries if "resource" in entry]
    
    # 1. Transform Patient Resource to PERSON
    patient = next((r for r in resources if r.get("resourceType") == "Patient"), None)
    if not patient:
        continue
        
    p_uuid = patient.get("id")
    gender_str = patient.get("gender", "unknown")
    gender_concept = gender_map.get(gender_str.lower(), 0)
    
    birth_date_str = patient.get("birthDate", "")
    year_of_birth = 1900
    month_of_birth = 1
    day_of_birth = 1
    
    if birth_date_str:
        dt = datetime.strptime(birth_date_str, "%Y-%m-%d")
        year_of_birth = dt.year
        month_of_birth = dt.month
        day_of_birth = dt.day
        
    nik = next((ident.get("value") for ident in patient.get("identifier", []) if "nik" in ident.get("system", "")), p_uuid)
    tokenized_nik = tokenize_nik(nik)
    
    # Insert row to Person Table
    cursor.execute("""
        INSERT INTO person (
            gender_concept_id, year_of_birth, month_of_birth, day_of_birth, birth_datetime,
            race_concept_id, ethnicity_concept_id, care_site_id, person_source_value, gender_source_value
        ) VALUES (?, ?, ?, ?, ?, 0, 0, 10000004, ?, ?)
    """, (gender_concept, year_of_birth, month_of_birth, day_of_birth, birth_date_str, tokenized_nik, gender_str))
    
    db_person_id = cursor.lastrowid
    patient_id_map[p_uuid] = db_person_id
    record_stats["persons"] += 1
    
    # 2. Transform Encounter Resources to VISIT_OCCURRENCE
    encounters = [r for r in resources if r.get("resourceType") == "Encounter"]
    for enc in encounters:
        enc_uuid = enc.get("id")
        enc_class_code = enc.get("class", {}).get("code", "ambulatory").lower()
        visit_concept = visit_type_map.get(enc_class_code, 9202) # Default to outpatient
        
        period = enc.get("period", {})
        start_datetime = period.get("start", "")
        end_datetime = period.get("end", start_datetime)
        
        start_date = start_datetime.split("T")[0] if "T" in start_datetime else start_datetime
        end_date = end_datetime.split("T")[0] if "T" in end_datetime else end_datetime
        
        cursor.execute("""
            INSERT INTO visit_occurrence (
                person_id, visit_concept_id, visit_start_date, visit_start_datetime,
                visit_end_date, visit_end_datetime, visit_type_concept_id, care_site_id, visit_source_value
            ) VALUES (?, ?, ?, ?, ?, ?, 44818518, 10000004, ?)
        """, (db_person_id, visit_concept, start_date, start_datetime, end_date, end_datetime, enc_uuid))
        
        db_visit_id = cursor.lastrowid
        visit_id_map[enc_uuid] = db_visit_id
        record_stats["visits"] += 1
        
    # 3. Transform Condition Resources to CONDITION_OCCURRENCE
    conditions = [r for r in resources if r.get("resourceType") == "Condition"]
    for cond in conditions:
        cond_uuid = cond.get("id")
        codings = cond.get("code", {}).get("coding", [])
        
        snomed_code = "0"
        snomed_display = "Unknown Condition"
        for coding in codings:
            snomed_code = coding.get("code", "0")
            snomed_display = coding.get("display", "Unknown Condition")
            break
            
        condition_concept = condition_code_map.get(snomed_code, 0)
        
        onset_datetime = cond.get("onsetDateTime", "")
        onset_date = onset_datetime.split("T")[0] if "T" in onset_datetime else onset_datetime
        abatement_datetime = cond.get("abatementDateTime")
        abatement_date = abatement_datetime.split("T")[0] if abatement_datetime and "T" in abatement_datetime else abatement_datetime
        
        enc_ref = cond.get("encounter", {}).get("reference", "")
        enc_id = enc_ref.split("/")[-1] if enc_ref else None
        db_visit_id = visit_id_map.get(enc_id)
        
        cursor.execute("""
            INSERT INTO condition_occurrence (
                person_id, condition_concept_id, condition_start_date, condition_start_datetime,
                condition_end_date, condition_end_datetime, condition_type_concept_id,
                visit_occurrence_id, condition_source_value, condition_source_concept_id
            ) VALUES (?, ?, ?, ?, ?, ?, 32817, ?, ?, ?)
        """, (db_person_id, condition_concept, onset_date, onset_datetime, abatement_date, abatement_datetime, db_visit_id, snomed_display, int(snomed_code) if snomed_code.isdigit() else 0))
        
        record_stats["conditions"] += 1
        
    # 4. Transform MedicationRequest Resources to DRUG_EXPOSURE
    med_requests = [r for r in resources if r.get("resourceType") == "MedicationRequest"]
    for med in med_requests:
        med_uuid = med.get("id")
        concept_coding = med.get("medicationCodeableConcept", {}).get("coding", [])
        med_text = med.get("medicationCodeableConcept", {}).get("text", "Unknown Medication")
        
        rx_code = "0"
        rx_display = med_text
        for coding in concept_coding:
            rx_code = coding.get("code", "0")
            rx_display = coding.get("display", med_text)
            break
            
        drug_concept = drug_code_map.get(rx_code, 0)
        
        authored_datetime = med.get("authoredOn", "")
        authored_date = authored_datetime.split("T")[0] if "T" in authored_datetime else authored_datetime
        
        dosage_text = ""
        dosage_instr = med.get("dosageInstruction", [])
        if dosage_instr:
            dosage_text = dosage_instr[0].get("text", "")
            
        enc_ref = med.get("encounter", {}).get("reference", "")
        enc_id = enc_ref.split("/")[-1] if enc_ref else None
        db_visit_id = visit_id_map.get(enc_id)
        
        cursor.execute("""
            INSERT INTO drug_exposure (
                person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_start_datetime,
                drug_exposure_end_date, drug_exposure_end_datetime, drug_type_concept_id,
                sig, visit_occurrence_id, drug_source_value, drug_source_concept_id
            ) VALUES (?, ?, ?, ?, ?, ?, 32817, ?, ?, ?, ?)
        """, (db_person_id, drug_concept, authored_date, authored_datetime, authored_date, authored_datetime, dosage_text, db_visit_id, rx_display, int(rx_code) if rx_code.isdigit() else 0))
        
        record_stats["drugs"] += 1
        
    # 5. Transform Observation Resources to MEASUREMENT
    observations = [r for r in resources if r.get("resourceType") == "Observation"]
    for obs in observations:
        obs_uuid = obs.get("id")
        
        # Handle BP Observation with sub-components
        components = obs.get("component", [])
        if components:
            for comp in components:
                codings = comp.get("code", {}).get("coding", [])
                loinc_code = "0"
                loinc_display = "Unknown BP Component"
                for coding in codings:
                    loinc_code = coding.get("code", "0")
                    loinc_display = coding.get("display", "Unknown BP Component")
                    break
                    
                measurement_concept = measurement_code_map.get(loinc_code, 0)
                val_quantity = comp.get("valueQuantity", {})
                val_num = val_quantity.get("value")
                val_unit = val_quantity.get("unit", "")
                
                effective_datetime = obs.get("effectiveDateTime", "")
                effective_date = effective_datetime.split("T")[0] if "T" in effective_datetime else effective_datetime
                
                enc_ref = obs.get("encounter", {}).get("reference", "")
                enc_id = enc_ref.split("/")[-1] if enc_ref else None
                db_visit_id = visit_id_map.get(enc_id)
                
                cursor.execute("""
                    INSERT INTO measurement (
                        person_id, measurement_concept_id, measurement_date, measurement_datetime,
                        measurement_type_concept_id, value_as_number, unit_source_value,
                        visit_occurrence_id, measurement_source_value, measurement_source_concept_id
                    ) VALUES (?, ?, ?, ?, 32817, ?, ?, ?, ?, ?)
                """, (db_person_id, measurement_concept, effective_date, effective_datetime, val_num, val_unit, db_visit_id, loinc_display, int(loinc_code.replace("-","")) if loinc_code.replace("-","").isdigit() else 0))
                
                record_stats["measurements"] += 1
        else:
            # Single Observation value
            codings = obs.get("code", {}).get("coding", [])
            loinc_code = "0"
            loinc_display = "Unknown Observation"
            for coding in codings:
                loinc_code = coding.get("code", "0")
                loinc_display = coding.get("display", "Unknown Observation")
                break
                
            measurement_concept = measurement_code_map.get(loinc_code, 0)
            val_quantity = obs.get("valueQuantity", {})
            val_num = val_quantity.get("value")
            val_unit = val_quantity.get("unit", "")
            
            effective_datetime = obs.get("effectiveDateTime", "")
            effective_date = effective_datetime.split("T")[0] if "T" in effective_datetime else effective_datetime
            
            enc_ref = obs.get("encounter", {}).get("reference", "")
            enc_id = enc_ref.split("/")[-1] if enc_ref else None
            db_visit_id = visit_id_map.get(enc_id)
            
            cursor.execute("""
                INSERT INTO measurement (
                    person_id, measurement_concept_id, measurement_date, measurement_datetime,
                    measurement_type_concept_id, value_as_number, unit_source_value,
                    visit_occurrence_id, measurement_source_value, measurement_source_concept_id
                ) VALUES (?, ?, ?, ?, 32817, ?, ?, ?, ?, ?)
            """, (db_person_id, measurement_concept, effective_date, effective_datetime, val_num, val_unit, db_visit_id, loinc_display, int(loinc_code.replace("-","")) if loinc_code.replace("-","").isdigit() else 0))
            
            record_stats["measurements"] += 1

conn.commit()
conn.close()

print("\nETL Pipeline Execution Complete! Summary of populated OMOP CDM tables:")
print("=" * 60)
print(f"PERSON Records: {record_stats['persons']}")
print(f"VISIT_OCCURRENCE Records: {record_stats['visits']}")
print(f"CONDITION_OCCURRENCE Records: {record_stats['conditions']}")
print(f"DRUG_EXPOSURE Records: {record_stats['drugs']}")
print(f"MEASUREMENT Records: {record_stats['measurements']}")
print("=" * 60)
print(f"Data transformed and stored in SQLite database successfully! DB Path: {os.path.relpath(db_path, project_root)}")
