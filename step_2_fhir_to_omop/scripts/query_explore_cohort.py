import os
import sqlite3

# Resolve database path dynamically relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_2_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(step_2_dir)
db_path = os.path.join(step_2_dir, "data", "omop_cdm.db")

print("==============================================================")
print("Querying OMOP CDM Database for EXPLORE Study Cohort...")
print(f"Database: {os.path.relpath(db_path, project_root)}")
print("==============================================================")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# SQL Query to filter patients based on EXPLORE Study Criteria:
# 1. Age >= 18 (represented by birth year calculation)
# 2. Condition: Type 2 Diabetes Mellitus (Concept ID: 201820)
# 3. Drug: Metformin ER (Concept ID: 1529331) OR Insulin Isophane (Concept ID: 1398937)
query = """
SELECT DISTINCT
    p.person_id,
    p.person_source_value AS token_nik,
    (2026 - p.year_of_birth) AS age,
    c_gender.concept_name AS gender,
    c_cond.concept_name AS condition,
    c_drug.concept_name AS medication,
    de.drug_exposure_start_date AS rx_date
FROM person p
JOIN concept c_gender ON p.gender_concept_id = c_gender.concept_id
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN concept c_cond ON co.condition_concept_id = c_cond.concept_id
JOIN drug_exposure de ON p.person_id = de.person_id
JOIN concept c_drug ON de.drug_concept_id = c_drug.concept_id
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
ORDER BY age DESC
"""

cursor.execute(query)
results = cursor.fetchall()

print(f"\nFound {len(results)} patient matches for the EXPLORE study cohort in the OMOP database:")
print("-" * 105)
print(f"{'OMOP ID':<8} | {'Tokenized NIK (De-identified)':<30} | {'Age':<3} | {'Gender':<7} | {'Primary Diagnosis':<26} | {'Medication Prescribed'}")
print("-" * 105)

for row in results:
    p_id, token_nik, age, gender, cond, med, rx_date = row
    # Limit length of display names for clean table formatting
    cond_disp = cond[:24] + "..." if len(cond) > 26 else cond
    med_disp = med[:35] + "..." if len(med) > 38 else med
    print(f"{p_id:<8} | {token_nik:<30} | {age:<3} | {gender:<7} | {cond_disp:<26} | {med_disp}")

print("-" * 100)
conn.close()
