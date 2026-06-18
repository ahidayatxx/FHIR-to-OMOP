import os
import subprocess
import time

script_dir = os.path.dirname(os.path.abspath(__file__))

print("==============================================================")
print("              COHORT FILTERING COMPARISON RUNNER              ")
print("==============================================================")
print("Running both direct FHIR JSON parsing and OMOP CDM SQL querying...")
print("-" * 60)

# 1. Run Direct FHIR Filtering Script
print("Executing: python3 filter_cohort_from_fhir.py")
t0_fhir = time.time()
fhir_process = subprocess.run(
    ["python3", os.path.join(script_dir, "filter_cohort_from_fhir.py")],
    capture_output=True,
    text=True
)
t1_fhir = time.time()
fhir_time_total_ms = (t1_fhir - t0_fhir) * 1000

# Parse stdout to get the specific filter time from the script itself
fhir_filter_time_line = [line for line in fhir_process.stdout.split('\n') if "Direct FHIR Filter Execution Time" in line]
fhir_filter_time_ms = 0.0
if fhir_filter_time_line:
    fhir_filter_time_ms = float(fhir_filter_time_line[0].split(': ')[1].split(' ')[0])

# Count matching lines in output
fhir_matches = 0
for line in fhir_process.stdout.split('\n'):
    if "3174" in line and "|" in line:
        fhir_matches += 1

print(f"-> Direct FHIR execution completed. Found {fhir_matches} matches.")
print("-" * 60)

# 2. Run OMOP CDM SQL Filtering Script
print("Executing: python3 filter_cohort_from_omop.py")
t0_omop = time.time()
omop_process = subprocess.run(
    ["python3", os.path.join(script_dir, "filter_cohort_from_omop.py")],
    capture_output=True,
    text=True
)
t1_omop = time.time()
omop_time_total_ms = (t1_omop - t0_omop) * 1000

# Parse stdout to get the specific query time from the script itself
omop_query_time_line = [line for line in omop_process.stdout.split('\n') if "OMOP CDM SQL Query Execution Time" in line]
omop_query_time_ms = 0.0
if omop_query_time_line:
    omop_query_time_ms = float(omop_query_time_line[0].split(': ')[1].split(' ')[0])

# Count matching lines in output of OMOP script (now uses 'tok_' prefix instead of '3174')
omop_matches = 0
for line in omop_process.stdout.split('\n'):
    if "tok_" in line and "|" in line:
        omop_matches += 1

print(f"-> OMOP CDM execution completed. Found {omop_matches} matches.")
print("==============================================================")
print("              PERFORMANCE & IMPLEMENTATION METRICS            ")
print("==============================================================")

# Count lines of code in each script
with open(os.path.join(script_dir, "filter_cohort_from_fhir.py"), 'r') as f:
    fhir_loc = len(f.readlines())

with open(os.path.join(script_dir, "filter_cohort_from_omop.py"), 'r') as f:
    omop_loc = len(f.readlines())

print(f"{'Metric':<30} | {'Direct FHIR (JSON)':<20} | {'OMOP CDM (SQL)':<20}")
print("-" * 76)
print(f"{'Identified Matches':<30} | {fhir_matches:<20} | {omop_matches:<20}")
print(f"{'In-Script Execution Time':<30} | {fhir_filter_time_ms:>13.2f} ms | {omop_query_time_ms:>13.2f} ms")
print(f"{'Total Process Runtime':<30} | {fhir_time_total_ms:>13.2f} ms | {omop_time_total_ms:>13.2f} ms")
print(f"{'Lines of Query/ETL Code':<30} | {fhir_loc:<20} | {omop_loc:<20}")
print(f"{'Data Access Pattern':<30} | {'Iterative File I/O':<20} | {'Indexed Relational DB':<20}")
print(f"{'Semantic Standardization':<30} | {'Hardcoded Codes':<20} | {'Standard Concept IDs':<20}")
print(f"{'PII / Identity Security':<30} | {'EXPOSED (Raw NIK)':<20} | {'SECURE (Tokenized/Blinded)':<20}")
print("-" * 76)

speedup = fhir_filter_time_ms / max(omop_query_time_ms, 0.001)
print(f"\nResult: OMOP CDM query is {speedup:.1f}x FASTER than parsing raw FHIR JSON files!")
print("==============================================================")
print("Refer to comparison_analysis.md for a detailed breakdown.")
print("==============================================================")
