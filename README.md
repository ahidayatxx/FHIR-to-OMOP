# HL7 FHIR R4 to OMOP CDM v5.4 Clinical Data Pipeline

This repository implements a complete, four-step clinical research data pipeline designed to simulate patient records, transform them into a standardized database schema, benchmark query performance, and model clinical trial screening. 

The pipeline is aligned with Indonesian health standards (**Kemenkes SATUSEHAT**) and data protection policies (**UU PDP No. 27/2022**).

---

## 1. Pipeline Architecture & Steps

```
┌────────────────────────────────────────────────────────┐
│             Step 1: FHIR Patient Creation              │
│ - Simulates Jakarta clinic profiles using Synthea      │
│ - Aligns data to Kemenkes SATUSEHAT FHIR profiles      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           │ Step 2: FHIR-to-OMOP ETL Loader
                           ▼
┌────────────────────────────────────────────────────────┐
│             Step 2: Relational OMOP Load               │
│ - Creates OMOP CDM v5.4 SQLite Database schema          │
│ - Maps clinical concepts to Standard OHDSI Concepts    │
│ - Blinds national identifiers (NIK) via SHA-256 tokens │
└──────────────────────────┬─────────────────────────────┘
                           │
                           │ Step 3: Performance & Security Benchmark
                           ▼
┌────────────────────────────────────────────────────────┐
│             Step 3: Comparative Analysis               │
│ - Benchmarks direct JSON parsing vs. Database queries   │
│ - Evaluates speedup metrics and data security profiles │
└──────────────────────────┬─────────────────────────────┘
                           │
                           │ Step 4: Clinical Scenarios & Operations
                           ▼
┌────────────────────────────────────────────────────────┐
│             Step 4: Clinical Trial & Ops               │
│ - Section 1: Feasibility studies & Recruitment rosters │
│ - Section 2: Hospital Operations reality checks       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Execution Guide

### Step 1: FHIR Creation
Generates a representative hospital population matching typical Jakarta name distributions and disease ratios:
```bash
cd step_1_fhir_creation

# Generate default cohort (100 patients) and post-process to SATUSEHAT
./generate_jakarta_patients.sh

# Or generate a specific size cohort (e.g. 250 patients)
./generate_jakarta_patients.sh 250
```
*Clinical outputs reside in:* `step_1_fhir_creation/data/fhir/jakarta_hospital/`

### Step 2: FHIR-to-OMOP ETL Load
Sets up the SQLite database schema and imports FHIR bundles while tokenizing NIK IDs:
```bash
# Initialize SQLite OMOP CDM tables
python3 step_2_fhir_to_omop/scripts/initialize_omop_db.py

# Run main ETL parser (hashes NIKs to 'tok_<sha256_prefix>')
python3 step_2_fhir_to_omop/scripts/fhir_to_omop.py

# Verify the database contents using SQL
python3 step_2_fhir_to_omop/scripts/query_explore_cohort.py
```
*Database output:* `step_2_fhir_to_omop/data/omop_cdm.db`

### Step 3: Cohort Filtering Comparison
Evaluates performance and security metrics:
```bash
python3 step_3_cohort_filtering/scripts/run_comparison.py
```
*Findings:* Database SQL queries run **60x to 80x faster** than file parsing. Direct FHIR parsing exposes patient NIKs on read, while OMOP CDM accesses only de-identified SHA-256 tokens.

### Step 4: Feasibility & Recruitment Reports
Simulates clinical operational reporting:
```bash
# Generate aggregate feasibility report
python3 step_4_clinical_scenarios/scripts/feasibility_study.py

# Generate de-identified recruitment selection list
python3 step_4_clinical_scenarios/scripts/patient_recruitment.py
```
*Outputs generated:* `step_4_clinical_scenarios/feasibility_report.txt` and `step_4_clinical_scenarios/recruitment_list.txt`.

---

## 3. Directory Structure
```
FHIR-to-OMOP/
│
├── step_1_fhir_creation/
│   ├── context_step_1.md            # STEP 1 Context: Cohorts & SATUSEHAT map rules
│   ├── synthea.properties            # Synthea generation settings
│   ├── generate_jakarta_patients.sh  # Master generation shell script
│   ├── scripts/
│   │   └── transform_to_jakarta.py   # Python SATUSEHAT profile transformer
│   └── data/
│       └── fhir/
│           └── jakarta_hospital/     # Aligned FHIR Patient Bundles
│
├── step_2_fhir_to_omop/
│   ├── context_step_2.md            # STEP 2 Context: ETL mappings & NIK tokenization
│   ├── omop_transformation_plan.md   # Detailed data mapping plan
│   ├── scripts/
│   │   ├── initialize_omop_db.py     # SQLite DDL database initializer
│   │   ├── fhir_to_omop.py           # Main ETL python script
│   │   └── query_explore_cohort.py   # SQL validation query script
│   └── data/
│       └── omop_cdm.db               # SQLite database containing OMOP tables
│
├── step_3_cohort_filtering/
│   ├── context_step_3.md            # STEP 3 Context: Performance & Privacy Metrics
│   ├── comparison_analysis.md        # Conceptual & methodological differences
│   └── scripts/
│       ├── filter_cohort_from_fhir.py # Direct JSON parsing filter script
│       ├── filter_cohort_from_omop.py # SQL concept-based query script
│       └── run_comparison.py          # Dashboard performance benchmark script
│
└── step_4_clinical_scenarios/
    ├── context_step_4.md            # STEP 4 Context: Clinical Trial & Operations Guide
    ├── scenarios_guide.md            # Clinical scenario descriptions & guide
    ├── feasibility_report.txt        # Generated population baseline report
    ├── recruitment_list.txt          # Generated de-identified candidate selection roster
    ├── feasibility_questionnaire.md  # Trial sponsor site questionnaire pre-populated with metrics
    └── scripts/
        ├── feasibility_study.py      # Population baseline aggregator script
        └── patient_recruitment.py    # Candidate identification & risk flagger
```

---

## 4. Privacy & Compliance Boundary (UU PDP No. 27/2022)
This pipeline implements an irreversible de-identification boundary during Step 2. Patients' national IDs (NIK) are tokenized using SHA-256 hashes (`tok_be0a61effae63bba`). 
This allows population analytics, cohort identification, and baseline analysis to be performed by researchers safely. Patient re-identification is strictly restricted to intranet decryption keys inside the hospital firewall when obtaining consent.
