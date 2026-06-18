import os
import sqlite3
import time

# Resolve database path relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_3_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(step_3_dir)
db_path = os.path.join(project_root, "step_2_fhir_to_omop", "data", "omop_cdm.db")

print("==============================================================")
print("Filtering EXPLORE Study Cohort from OMOP CDM Database (SQL)")
print(f"Database: {os.path.relpath(db_path, project_root)}")
print("==============================================================")

if not os.path.exists(db_path):
    print("Error: SQLite Database not found. Please run initialize_omop_db.py and fhir_to_omop.py first.")
    exit(1)

start_time = time.time()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query using relational JOINs and SQLite's group_concat for medications
query = """
SELECT 
    p.person_source_value AS token_nik,
    (2026 - p.year_of_birth) AS age,
    c_gender.concept_name AS gender,
    group_concat(DISTINCT c_drug.concept_name) AS medications
FROM person p
JOIN concept c_gender ON p.gender_concept_id = c_gender.concept_id
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
JOIN concept c_drug ON de.drug_concept_id = c_drug.concept_id
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
GROUP BY p.person_id
ORDER BY age DESC
"""

cursor.execute(query)
results = cursor.fetchall()

end_time = time.time()
execution_time_ms = (end_time - start_time) * 1000

print(f"\nFound {len(results)} unique patients matching criteria:")
print("-" * 115)
print(f"{'Tokenized NIK (De-identified)':<30} | {'Age':<3} | {'Gender':<7} | {'Medications Mapped'}")
print("-" * 115)

for row in results:
    token_nik, age, gender, meds = row
    meds_disp = meds[:55] + "..." if len(meds) > 58 else meds
    print(f"{token_nik:<30} | {age:<3} | {gender:<7} | {meds_disp}")

print("-" * 100)
print(f"OMOP CDM SQL Query Execution Time: {execution_time_ms:.2f} ms")
print("==============================================================")

conn.close()
