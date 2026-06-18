# Step 4: Clinical Trial & Hospital Operations Guide

This guide illustrates the practical, real-world execution of research queries and identifies the imminent operational issues encountered when deploying research-ready data systems (like OMOP CDM) inside a hospital's technical infrastructure.

---

## SECTION 1: Clinical Trial Workflow

This section covers the standard workflow from initial trial planning to active candidate recruitment.

### 1a. Feasibility Study (Population Level)
Before a clinical site is selected for the **EXPLORE Study**, researchers must verify if the site possesses a viable patient population.
* **Objective:** Extract baseline counts, gender distributions, age brackets, and baseline metrics (e.g. average blood pressure) of adult patients diagnosed with Type 2 Diabetes on active Metformin/Insulin treatment.
* **Execution Script:**
  ```bash
  python3 step_4_clinical_scenarios/scripts/feasibility_study.py
  ```
* **Security Attribute:** **Blinded Aggregate Analytics.** This script returns only population counts and means. It does not load or display individual patient identifiers, making it safe to share outside the hospital firewall with study sponsors.

### 1b. Patient Recruitment (Individual Level)
Once the trial is approved, clinical coordinators must generate a roster of actual candidates to screen and contact for consent.
* **Objective:** Generate a recruitment selection roster displaying candidate tokenized NIKs, age, gender, latest blood pressure readings, complications (microalbuminuria), and active prescriptions.
* **Execution Script:**
  ```bash
  python3 step_4_clinical_scenarios/scripts/patient_recruitment.py
  ```
* **Security Attribute:** **Blinded Individual Screening.** While the script details patient-level clinical variables, all direct patient identity (like national NIK numbers) is securely tokenized using irreversible SHA-256 hashes. 

---

## SECTION 2: Hospital Operations (Imminent Issues)

Integrating research-analytical databases (OMOP CDM) with live EHR operations introduces several imminent technical, operational, and legal issues:

### 1. Re-identification and Decryption Bottleneck
* **The Issue:** Because the OMOP database stores only blinded tokens (e.g., `tok_be0a61effae63bba`), a clinical coordinator cannot directly call or email a patient using research data.
* **Imminent Risk:** To recruit the patient, the coordinator must map the token back to the actual patient name/record number. This requires a secure **PII Decryption Mapping Table** hosted strictly inside the hospital's private intranet. If this lookup system is not integrated, recruitment slows down drastically. If it is insecurely implemented, it poses a major threat of exposing patient data.

### 2. Synchronization Latency (EMR vs. OMOP ETL)
* **The Issue:** Live Electronic Medical Records (EMRs) capture patient data in real-time. Conversely, OMOP database updates are usually run in batch processes (e.g., nightly, weekly, or monthly) due to the high computational load of ETL mappings.
* **Imminent Risk:** Time-sensitive eligibility criteria (e.g., "patient must have had an HbA1c test in the last 7 days") will contain stale data. A patient could be recruited based on outdated data, only to be disqualified during screening due to recent EMR updates not yet synced to OMOP.

### 3. Consent Management and Opt-out Policies
* **The Issue:** Under Indonesian personal data protection laws (**UU PDP No. 27/2022**), using patient data for research requires explicit consent or pseudonymization.
* **Imminent Risk:** Even with tokenized data, querying patient records to generate candidate lists before they have opted into research can trigger legal disputes. Hospital IT must integrate a "Research Consent Flag" in the EMR and map it to the OMOP ETL so that patients who have opted out are excluded from feasibility and screening outputs.

### 4. Vocabulary Mapping Completeness (The Local Code Gap)
* **The Issue:** Indonesian hospitals heavily rely on local coding systems (e.g., BPJS drug codes, local laboratory test names in Bahasa Indonesia). 
* **Imminent Risk:** If the ETL pipeline does not maintain an exhaustive, active translation table mapping local drug codes to RxNorm and local lab tests to LOINC, patient records will fail to map to standard OHDSI Concept IDs. This results in **false negatives**—patients who meet all eligibility criteria but are omitted from the recruitment list because their clinical data failed to standardize.

### 5. Infrastructure Strain and Peak Load Management
* **The Issue:** Executing complex, multi-join analytical queries (joining millions of rows in `measurement`, `drug_exposure`, and `condition_occurrence`) requires significant CPU and memory.
* **Imminent Risk:** If researchers query the live production EMR server directly, clinical systems will experience severe latency, delaying doctor screens and patient visits.
* **Solution:** Hospital operations must establish a separate, read-only OMOP analytical instance (Read-Replica) isolated from the primary EMR transaction database.

### 6. The Reality Check: Synthea vs. Messy Clinical Data
* **The Simplicity of Simulation:** Synthea generates clean, perfectly structured, fully digitized, and comprehensive JSON FHIR resources.
* **The Messy Clinical Reality:** In a real hospital (e.g., RSUD Tarakan Jakarta), patient data is highly fragmented and complex:
  * **Scattered & Siloed:** Data is spread across legacy departmental databases (Pathology LIS, Radiology RIS, Billing systems, and Pharmacy).
  * **Unstructured & Handwritten:** More than 70% of clinical details reside in free-text clinical notes, PDF scan results, or handwritten doctor notes that require OCR (Optical Character Recognition) and NLP (Natural Language Processing) to extract.
  * **Analogue Format:** Significant portions of history (such as legacy charts or referrals from rural clinics) remain entirely paper-based.

### 7. Continuous Data Pipeline Challenges (`EMR -> FHIR -> OMOP`)
Establishing a continuous stream of data updates through the two-step ETL pipeline (`EMR -> FHIR` and consequently `FHIR -> OMOP`) introduces severe operational challenges:
* **Compounding Pipeline Latency:** If EMR modifications are pushed to FHIR, and the FHIR resources must then trigger incremental ETL processing to OMOP, any delay or network lag in either connection stalls the downstream research database.
* **Transaction Conflicts and Out-of-Order Updates:** If a lab result (FHIR Observation) is updated *before* the encounter (FHIR Encounter) finishes and registers in the database, foreign key constraints in the relational OMOP tables (e.g., `visit_occurrence_id` in `measurement`) will fail, leading to rejected inserts.
* **Data Integrity Drift:** Constantly updating existing rows (e.g., adding measurements to an ongoing multi-day hospital admission) causes lock conflicts on relational DB rows, degrading query performance for clinical investigators.
* **Schema Validation Failures:** A slight format modification in the EHR source field can break the regex or parser scripts, crashing the continuous ETL pipeline and requiring emergency data-engineering intervention.

---

## SECTION 3: Operational Summary

* **Feasibility Studies (Section 1a):** Conducted at the **study planning** stage. They use anonymous aggregate counts and can be safely shared outside the hospital firewall with research sponsors.
* **Patient Recruitment (Section 1b):** Conducted at the **recruitment** stage inside the hospital firewall. It matches clinical criteria with a secure, blinded identifier (Tokenized NIK). Authorized clinical staff can map these tokens back to raw patient records using a secure mapping table inside the hospital's intranet to contact candidates and obtain consent.
* **Clinical Data Pipeline Execution:** Synthea serves as an ideal baseline simulation, but actual deployments must budget for NLP pipelines (to extract text notes), data-cleaning wrappers, and read-replica replication lag to handle real-world operational challenges.

