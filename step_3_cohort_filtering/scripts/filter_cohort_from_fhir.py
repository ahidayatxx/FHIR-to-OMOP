import os
import json
import time
from datetime import datetime

# Resolve paths relative to script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_3_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(step_3_dir)
fhir_dir = os.path.join(project_root, "step_1_fhir_creation", "data", "fhir", "jakarta_hospital")

print("==============================================================")
print("Filtering EXPLORE Study Cohort Directly from FHIR Bundles (JSON)")
print(f"Reading from: {os.path.relpath(fhir_dir, project_root)}")
print("==============================================================")

start_time = time.time()

if not os.path.exists(fhir_dir) or len(os.listdir(fhir_dir)) == 0:
    print(f"Error: No FHIR files found in {fhir_dir}")
    exit(1)

files = [f for f in os.listdir(fhir_dir) if f.endswith(".json")]
cohort_matches = []

# Target Codes (SNOMED CT for T2DM, RxNorm for Metformin / Insulin)
T2DM_SNOMED_CODE = "44054006"
TARGET_RX_CODES = {"860975", "865091"}  # Metformin 500mg ER, Insulin Isophane

for filename in files:
    filepath = os.path.join(fhir_dir, filename)
    with open(filepath, 'r') as f:
        try:
            bundle = json.load(f)
        except Exception as e:
            continue
            
    # Extract entries
    entries = bundle.get("entry", [])
    resources = [entry.get("resource", {}) for entry in entries if "resource" in entry]
    
    # 1. Parse Patient details
    patient = next((r for r in resources if r.get("resourceType") == "Patient"), None)
    if not patient:
        continue
        
    p_id = patient.get("id")
    birth_date_str = patient.get("birthDate", "")
    gender = patient.get("gender", "unknown").upper()
    nik = next((ident.get("value") for ident in patient.get("identifier", []) if "nik" in ident.get("system", "")), p_id)
    
    # Calculate age for year 2026
    age = 0
    if birth_date_str:
        try:
            dt = datetime.strptime(birth_date_str, "%Y-%m-%d")
            age = 2026 - dt.year
        except ValueError:
            continue
            
    if age < 18:
        continue
        
    # 2. Check for Condition (Type 2 Diabetes)
    has_t2d = False
    conditions = [r for r in resources if r.get("resourceType") == "Condition"]
    for cond in conditions:
        # Verify subject reference links to our patient
        subject_ref = cond.get("subject", {}).get("reference", "")
        if p_id not in subject_ref:
            continue
            
        codings = cond.get("code", {}).get("coding", [])
        for coding in codings:
            if coding.get("code") == T2DM_SNOMED_CODE:
                has_t2d = True
                break
        if has_t2d:
            break
            
    if not has_t2d:
        continue
        
    # 3. Check for Medication Requests (Metformin or Insulin)
    has_med = False
    matched_meds = []
    med_requests = [r for r in resources if r.get("resourceType") == "MedicationRequest"]
    for med in med_requests:
        # Verify subject reference links to our patient
        subject_ref = med.get("subject", {}).get("reference", "")
        if p_id not in subject_ref:
            continue
            
        concept = med.get("medicationCodeableConcept", {})
        codings = concept.get("coding", [])
        med_display = concept.get("text", "Unknown Medication")
        
        for coding in codings:
            rx_code = coding.get("code")
            if rx_code in TARGET_RX_CODES:
                has_med = True
                med_name = coding.get("display", med_display)
                matched_meds.append(med_name)
                break
                
    if has_med:
        cohort_matches.append({
            "nik": nik,
            "age": age,
            "gender": gender,
            "meds": list(set(matched_meds))
        })

end_time = time.time()
execution_time_ms = (end_time - start_time) * 1000

print(f"\nFound {len(cohort_matches)} unique patients matching criteria:")
print("-" * 100)
print(f"{'NIK / Source Value':<18} | {'Age':<3} | {'Gender':<7} | {'Medications Found'}")
print("-" * 100)
for pat in sorted(cohort_matches, key=lambda x: x['age'], reverse=True):
    meds_str = ", ".join(pat['meds'])
    # Format meds to fit print layout
    meds_str_disp = meds_str[:55] + "..." if len(meds_str) > 58 else meds_str
    print(f"{pat['nik']:<18} | {pat['age']:<3} | {pat['gender']:<7} | {meds_str_disp}")
print("-" * 100)
print(f"Direct FHIR Filter Execution Time: {execution_time_ms:.2f} ms")
print(f"Total files read and parsed: {len(files)}")
print("==============================================================")
