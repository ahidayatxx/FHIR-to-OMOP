import os
import sqlite3

# Resolve database path relative to script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_4_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(step_4_dir)
db_path = os.path.join(project_root, "step_2_fhir_to_omop", "data", "omop_cdm.db")

output_lines = []
def log_print(msg=""):
    print(msg)
    output_lines.append(msg)

log_print("==============================================================")
log_print("Section 1b: Clinical Trial Patient Recruitment Selection List")
log_print(f"Database: {os.path.relpath(db_path, project_root)}")
log_print("==============================================================")

if not os.path.exists(db_path):
    log_print("Error: SQLite Database not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query to extract individual clinical details including latest measurements and complication flags
query = """
SELECT 
    p.person_source_value AS Tokenized_NIK,
    (2026 - p.year_of_birth) AS Age,
    c_gender.concept_name AS Gender,
    MAX(CASE WHEN m.measurement_concept_id = 3004249 THEN m.value_as_number END) AS Latest_Systolic,
    MAX(CASE WHEN m.measurement_concept_id = 3004279 THEN m.value_as_number END) AS Latest_Diastolic,
    MAX(CASE WHEN co_comp.condition_concept_id = 4147775 THEN 'Yes' ELSE 'No' END) AS Has_Microalbuminuria,
    group_concat(DISTINCT c_drug.concept_name) AS Medications
FROM person p
JOIN concept c_gender ON p.gender_concept_id = c_gender.concept_id
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
JOIN concept c_drug ON de.drug_concept_id = c_drug.concept_id
LEFT JOIN condition_occurrence co_comp ON p.person_id = co_comp.person_id AND co_comp.condition_concept_id = 4147775
LEFT JOIN measurement m ON p.person_id = m.person_id AND m.measurement_concept_id IN (3004249, 3004279)
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
GROUP BY p.person_id
ORDER BY Latest_Systolic DESC, Age DESC
"""

cursor.execute(query)
results = cursor.fetchall()

log_print(f"\nIdentified {len(results)} Potential Candidates for Recruitment:")
log_print("-" * 125)
log_print(f"{'Tokenized NIK (De-identified)':<30} | {'Age':<3} | {'Gender':<7} | {'BP (mmHg)':<9} | {'Microalbuminuria':<16} | {'Active Prescriptions'}")
log_print("-" * 125)

for row in results:
    token_nik, age, gender, sys_bp, dia_bp, micro_alb, meds = row
    
    # Format Blood Pressure reading
    bp_str = "N/A"
    if sys_bp and dia_bp:
        bp_str = f"{int(sys_bp)}/{int(dia_bp)}"
        
    # Simplify medication list display
    meds_list = []
    if "Metformin" in meds:
        meds_list.append("Metformin")
    if "insulin" in meds.lower():
        meds_list.append("Insulin")
    meds_disp = " + ".join(meds_list) if meds_list else "Other Anti-Diabetic"
    
    # Highlight high-risk candidates (uncontrolled BP or kidney complications)
    risk_flag = " "
    if sys_bp and sys_bp >= 140:
        risk_flag = "⚠️ (High BP)"
    elif micro_alb == "Yes":
        risk_flag = "🚨 (Kidney Risk)"
        
    log_print(f"{token_nik:<30} | {age:<3} | {gender:<7} | {bp_str:<9} | {micro_alb:<16} | {meds_disp:<20} {risk_flag}")

log_print("-" * 125)
log_print("Clinical Notes:")
log_print("  - ⚠️ indicates uncontrolled hypertension (Systolic BP >= 140 mmHg).")
log_print("  - 🚨 indicates active Microalbuminuria, a diabetic kidney complication.")
log_print("  - Use the Tokenized NIK to securely map back to the source EHR decryption table inside the hospital firewall.")
log_print("==============================================================")

conn.close()

# Save the candidate recruitment list to disk in the step_4 directory
recruitment_list_path = os.path.join(step_4_dir, "recruitment_list.txt")
with open(recruitment_list_path, 'w') as out_f:
    out_f.write("\n".join(output_lines) + "\n")
print(f"\nRecruitment selection list successfully saved to: {os.path.relpath(recruitment_list_path, project_root)}")
