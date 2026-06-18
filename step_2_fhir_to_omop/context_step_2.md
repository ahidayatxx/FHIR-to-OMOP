# Context Step 2: FHIR-to-OMOP ETL Transformation

## 1. Objective
The objective of Step 2 is to set up a relational database conforming to the **OMOP Common Data Model (CDM) v5.4** standard, and execute the Extract-Transform-Load (ETL) pipeline importing the raw Kemenkes SATUSEHAT FHIR patient bundles.

---

## 2. Relational Schema & Vocabulary Mappings

During the database load, unstructured and transactional FHIR nested JSON documents are transformed into indexed relational tables:

| Source FHIR Resource | Target OMOP Table | Standard Target Mappings & Terminology Mapped |
| :--- | :--- | :--- |
| **Patient** | `PERSON` | Gender mapped to standard Concept IDs (**8507** MALE, **8532** FEMALE). Date of birth decomposed to standard integer columns (`year_of_birth`, etc.). |
| **Encounter** | `VISIT_OCCURRENCE` | Visit class mapped to Outpatient (**9202**), Emergency (**9203**), Inpatient (**9201**), or Telehealth (**581477**). |
| **Condition** | `CONDITION_OCCURRENCE` | SNOMED-CT codes mapped to standard OMOP concept IDs (e.g. SNOMED `44054006` $\rightarrow$ OMOP Concept ID **201820** for Type 2 Diabetes). |
| **MedicationRequest** | `DRUG_EXPOSURE` | RxNorm codes mapped to standard RxNorm drug concepts (e.g. RxNorm `860975` $\rightarrow$ Standard Concept **1529331** for Metformin ER). |
| **Observation** | `MEASUREMENT` | LOINC codes mapped to standard measurement concepts (e.g. LOINC `8480-6` $\rightarrow$ Standard Concept **3004249** for Systolic BP). |

---

## 3. PII Tokenization & Blinding Security Boundary
For clinical safety and data confidentiality:
1. **Raw PII Exclusion:** No direct Patient names, addresses, or identifiers are imported into the OMOP database.
2. **SHA-256 Blinding:** The patient's national registration number (NIK) is hashed using a secure, irreversible **SHA-256 process** during the ETL execution (e.g. NIK `3174...` is loaded as `tok_be0a61effae63bba` in the `person_source_value` column).
3. **Blinded Research Database:** Since all direct identifiers are hashed, the OMOP database functions as a **totally blinded environment** for all downstream steps (Step 3 and Step 4). Researchers can query the database without accessing raw patient identity.

---

## 4. Scripts & Configuration

* [omop_transformation_plan.md](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_2_fhir_to_omop/omop_transformation_plan.md): The structural and terminology mapping specifications.
* [scripts/initialize_omop_db.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_2_fhir_to_omop/scripts/initialize_omop_db.py): SQLite schema DDL creation.
* [scripts/fhir_to_omop.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_2_fhir_to_omop/scripts/fhir_to_omop.py): Main ETL loader processing FHIR files, executing tokenization, and running SQL database insertions.
* [scripts/query_explore_cohort.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_2_fhir_to_omop/scripts/query_explore_cohort.py): Verification script executing standard OHDSI SQL queries to pull the target EXPLORE cohort.

---

## 5. Execution Commands
To initialize the schema and run the ETL:
```bash
# 1. Initialize empty tables
python3 step_2_fhir_to_omop/scripts/initialize_omop_db.py

# 2. Run ETL pipeline (populating tables and blinding NIKs)
python3 step_2_fhir_to_omop/scripts/fhir_to_omop.py

# 3. Verify database contents
python3 step_2_fhir_to_omop/scripts/query_explore_cohort.py
```
Outputs are saved as an SQLite relational file at [data/omop_cdm.db](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_2_fhir_to_omop/data/omop_cdm.db).
