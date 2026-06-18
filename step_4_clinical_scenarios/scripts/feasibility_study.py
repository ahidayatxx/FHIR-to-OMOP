import os
import sqlite3

# Resolve database path relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_4_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(step_4_dir)
db_path = os.path.join(project_root, "step_2_fhir_to_omop", "data", "omop_cdm.db")

output_lines = []
def log_print(msg=""):
    print(msg)
    output_lines.append(msg)

log_print("==============================================================")
log_print("Scenario A: EXPLORE Study Cohort Feasibility Report")
log_print(f"Database: {os.path.relpath(db_path, project_root)}")
log_print("==============================================================")

if not os.path.exists(db_path):
    log_print("Error: SQLite Database not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Total Cohort Size
query_total = """
SELECT COUNT(DISTINCT p.person_id)
FROM person p
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
"""
cursor.execute(query_total)
total_candidates = cursor.fetchone()[0]

log_print(f"\n[Metric 1] Total Eligible Study Candidates: {total_candidates}")
log_print("-" * 60)

if total_candidates == 0:
    log_print("No candidates found. Feasibility study complete.")
    conn.close()
    exit(0)

# 2. Gender Distribution
query_gender = """
SELECT 
    c_gender.concept_name AS gender,
    COUNT(DISTINCT p.person_id) AS count,
    ROUND(COUNT(DISTINCT p.person_id) * 100.0 / ?, 2) AS percentage
FROM person p
JOIN concept c_gender ON p.gender_concept_id = c_gender.concept_id
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
GROUP BY p.gender_concept_id
"""
cursor.execute(query_gender, (total_candidates,))
gender_results = cursor.fetchall()

log_print("[Metric 2] Gender Distribution:")
for gender, count, pct in gender_results:
    log_print(f"  - {gender:<8} : {count:>3} candidates ({pct:>5}%)")
log_print("-" * 60)

# 3. Age Brackets Distribution
query_age = """
SELECT 
    CASE 
        WHEN (2026 - p.year_of_birth) BETWEEN 18 AND 39 THEN '18-39 (Young Adult)'
        WHEN (2026 - p.year_of_birth) BETWEEN 40 AND 59 THEN '40-59 (Middle-aged)'
        WHEN (2026 - p.year_of_birth) BETWEEN 60 AND 74 THEN '60-74 (Older Adult)'
        ELSE '75+ (Elderly)'
    END AS age_group,
    COUNT(DISTINCT p.person_id) AS count,
    ROUND(COUNT(DISTINCT p.person_id) * 100.0 / ?, 2) AS percentage
FROM person p
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
GROUP BY age_group
ORDER BY age_group
"""
cursor.execute(query_age, (total_candidates,))
age_results = cursor.fetchall()

log_print("[Metric 3] Age Group Distribution:")
for age_grp, count, pct in age_results:
    log_print(f"  - {age_grp:<22} : {count:>3} candidates ({pct:>5}%)")
log_print("-" * 60)

# 4. Medication Type Breakdown
query_meds = """
SELECT 
    med_status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / ?, 2) AS percentage
FROM (
    SELECT 
        p.person_id,
        CASE 
            WHEN SUM(CASE WHEN de.drug_concept_id = 1529331 THEN 1 ELSE 0 END) > 0 
                 AND SUM(CASE WHEN de.drug_concept_id = 1398937 THEN 1 ELSE 0 END) > 0 THEN 'Dual Therapy (Metformin + Insulin)'
            WHEN SUM(CASE WHEN de.drug_concept_id = 1529331 THEN 1 ELSE 0 END) > 0 THEN 'Metformin Monotherapy'
            WHEN SUM(CASE WHEN de.drug_concept_id = 1398937 THEN 1 ELSE 0 END) > 0 THEN 'Insulin Monotherapy'
            ELSE 'Other'
        END AS med_status
    FROM person p
    JOIN condition_occurrence co ON p.person_id = co.person_id
    JOIN drug_exposure de ON p.person_id = de.person_id
    WHERE (2026 - p.year_of_birth) >= 18
      AND co.condition_concept_id = 201820
      AND de.drug_concept_id IN (1529331, 1398937)
    GROUP BY p.person_id
)
GROUP BY med_status
"""
cursor.execute(query_meds, (total_candidates,))
med_results = cursor.fetchall()

log_print("[Metric 4] Anti-Diabetic Medication Breakdown:")
for med_status, count, pct in med_results:
    log_print(f"  - {med_status:<36} : {count:>3} candidates ({pct:>5}%)")
log_print("-" * 60)

# 5. Cohort Clinical Baseline Stats (Average Blood Pressure)
query_bp = """
SELECT 
    ROUND(AVG(CASE WHEN m.measurement_concept_id = 3004249 THEN m.value_as_number END), 1) AS avg_systolic,
    ROUND(AVG(CASE WHEN m.measurement_concept_id = 3004279 THEN m.value_as_number END), 1) AS avg_diastolic
FROM person p
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
LEFT JOIN measurement m ON p.person_id = m.person_id AND m.measurement_concept_id IN (3004249, 3004279)
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
"""
cursor.execute(query_bp)
avg_systolic, avg_diastolic = cursor.fetchone()

log_print("[Metric 5] Baseline Cardiovascular Metrics:")
log_print(f"  - Average Systolic Blood Pressure : {avg_systolic} mmHg")
log_print(f"  - Average Diastolic Blood Pressure: {avg_diastolic} mmHg")
log_print("==============================================================")

conn.close()

# Save the captured report to disk in the step_4 directory
report_path = os.path.join(step_4_dir, "feasibility_report.txt")
with open(report_path, 'w') as out_f:
    out_f.write("\n".join(output_lines) + "\n")
print(f"\nReport successfully saved to: {os.path.relpath(report_path, project_root)}")
