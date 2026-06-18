# Site Feasibility Questionnaire: EXPLORE Study
**Protocol Title:** Evaluation of Cardiovascular Risks & Baseline Treatment Targets in Type 2 Diabetes Mellitus Patients  
**Sponsor:** Global Observational Health Data Research Network  
**Target Research Site:** RSUD Tarakan Jakarta, DKI Jakarta, Indonesia  
**Data Model:** OMOP Common Data Model (CDM) v5.4  

---

## SECTION 1: Patient Cohort Volume & Eligibility

### Q1.1: What is the total volume of patients diagnosed with Type 2 Diabetes Mellitus managed at your site?
* **Site Answer:** 276 unique patients are registered under the Type 2 Diabetes and general hospital profile in our current study database.

### Q1.2: How many of these patients meet the core inclusion criteria for the EXPLORE Study?
* **Core Inclusion Criteria:**
  1. Age $\ge 18$ years at the time of screening.
  2. Diagnosis of Type 2 Diabetes Mellitus (mapped to Standard Concept ID: **201820**).
  3. Under active treatment with Metformin (Concept ID: **1529331**) and/or Insulin (Concept ID: **1398937**).
* **Site Answer:** **17 patients** meet the full eligibility criteria.

### Q1.3: What is the treatment baseline breakdown among the eligible candidates?
* **Site Answer:**
  * **Metformin Monotherapy:** 17 candidates (100.0%)
  * **Insulin Monotherapy:** 0 candidates (0.0%)
  * **Dual Therapy (Metformin + Insulin):** 0 candidates (0.0%)

---

## SECTION 2: Demographic Distribution

### Q2.1: Please provide the gender breakdown of the eligible cohort.
* **Site Answer:**
  * **Male:** 10 candidates (58.82%)
  * **Female:** 7 candidates (41.18%)

### Q2.2: Please provide the age distribution of the eligible cohort.
* **Site Answer:**
  * **18-39 years (Young Adult):** 0 candidates (0.0%)
  * **40-59 years (Middle-aged):** 2 candidates (11.76%)
  * **60-74 years (Older Adult):** 5 candidates (29.41%)
  * **75+ years (Elderly):** 10 candidates (58.82%)

---

## SECTION 3: Baseline Clinical Characteristics

### Q3.1: Can your site report aggregate baseline blood pressure values for the eligible cohort?
* **Site Answer:** Yes. Based on LOINC mapping to Standard Concept IDs **3004249** (Systolic BP) and **3004279** (Diastolic BP), the baseline metrics are:
  * **Average Systolic Blood Pressure:** **108.0 mmHg**
  * **Average Diastolic Blood Pressure:** **67.0 mmHg**

### Q3.2: How many eligible candidates have uncontrolled hypertension (Systolic BP $\ge 140$ mmHg)?
* **Site Answer:** **2 patients** are flagged with uncontrolled blood pressure:
  * Patient `tok_422e8d398dce2204` (BP: 153/94 mmHg)
  * Patient `tok_396c14c482f928b2` (BP: 142/115 mmHg)

---

## SECTION 4: Data Security, Privacy, & Technical Readiness

### Q4.1: How does your site ensure compliance with national data privacy regulations (e.g. Indonesian UU PDP No. 27/2022) during recruitment?
* **Site Answer:** All Personally Identifiable Information (PII), specifically national registration numbers (NIK), is tokenized using **cryptographic SHA-256 hashing** during the Step 2 ETL pipeline. The research database stores only de-identified tokens (e.g. `tok_422e8d398dce...`). Individual patient re-identification is strictly restricted to authorized hospital clinicians using a secure mapping table inside the hospital's private intranet.

### Q4.2: What is the latency of clinical data updates in your research database?
* **Site Answer:** Data is loaded from the production EHR into FHIR transaction resources, and subsequently batched into the OMOP database. Our current batch processing operates on a nightly schedule, introducing a maximum synchronization latency of 24 hours.

### Q4.3: What standards and terminologies does your site support?
* **Site Answer:** Our ETL pipeline maps local clinical terminologies (BPJS codes, local lab descriptors) to international standards:
  * **Conditions:** SNOMED-CT mapped to standard OMOP concepts.
  * **Medications:** RxNorm mapped to standard OMOP concepts.
  * **Measurements:** LOINC mapped to standard OMOP concepts.
