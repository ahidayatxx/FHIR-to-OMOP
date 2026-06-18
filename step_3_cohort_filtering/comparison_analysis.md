# Comparative Analysis: Cohort Filtering in Raw FHIR vs. OMOP CDM

This analysis compares two different approaches to identifying a patient cohort (the **EXPLORE Study Cohort** — adults with Type 2 Diabetes Mellitus under active treatment) from clinical datasets. 

The goal of this document is to contrast the **technological** and **methodological** differences between raw FHIR transaction bundles and the standardized OMOP Common Data Model (CDM), providing the clinical research rationale for *why* we perform FHIR-to-OMOP transformations.

---

## 1. Technical Comparison: JSON Traversal vs. SQL Queries

Below is a technical comparison of the two filtering approaches implemented in this step.

| Architectural Dimension | Direct FHIR Filtering (`filter_cohort_from_fhir.py`) | OMOP CDM Database Filtering (`filter_cohort_from_omop.py`) |
| :--- | :--- | :--- |
| **Data Format** | Hierarchical nested JSON transaction bundles. | Relational standard tables (`person`, `visit_occurrence`, etc.). |
| **Access Pattern** | **Procedural (Python / Java):** Developer must write nested loops to traverse resources, extract fields, and filter. | **Declarative (SQL):** Developer states *what* data is needed; the database engine decides *how* to fetch it. |
| **I/O Overhead** | **High:** Every file must be opened, read from disk, and parsed in memory. Scalability is file I/O bound. | **Low:** Data is stored in binary tables. Relational indexes enable fast row scanning. |
| **Performance Scaling** | $O(N)$ linear scale. Scanning $1,000,000$ patients requires reading and parsing $1,000,000$ files. | $O(\log N)$ logarithmic scale using database indexes (B-Trees). |
| **Code Length** | ~110 lines of python code. | ~40 lines of python code (containing standard SQL). |
| **Ad-Hoc Queries** | **Difficult:** Changing cohort rules requires writing new parser code and re-scanning all files. | **Easy:** Changing criteria requires adjusting a few lines of SQL in a `WHERE` clause. |
| **PII / Identity Security**| **EXPOSED:** Code reads raw NIK values directly from the FHIR JSON resources to map references. | **SECURE / BLINDED:** Individual IDs (NIK) are tokenized using SHA-256 during ETL. |

### FHIR JSON Traversal Code Pattern (Nested Loops)
```python
# Procedural loop checking patient age, conditions, and medications
for filename in files:
    bundle = json.load(open(filepath))
    patient = next(r for r in bundle if r.resourceType == "Patient")
    if calculate_age(patient.birthDate) >= 18:
        has_t2d = any(c.code == "44054006" for c in bundle if c.resourceType == "Condition")
        if has_t2d:
            has_med = any(m.code in TARGET_RX_CODES for m in bundle if m.resourceType == "MedicationRequest")
            if has_med:
                cohort_matches.append(patient)
```

### OMOP Relational SQL Query Pattern (Declarative)
```sql
SELECT p.person_source_value AS token_nik, (2026 - p.year_of_birth) AS age
FROM person p
JOIN condition_occurrence co ON p.person_id = co.person_id
JOIN drug_exposure de ON p.person_id = de.person_id
WHERE (2026 - p.year_of_birth) >= 18
  AND co.condition_concept_id = 201820
  AND de.drug_concept_id IN (1529331, 1398937)
```

---

## 2. Methodological Comparison: Semantic Standardization

Methodology is where the value of OMOP CDM is most apparent for clinical research. FHIR is designed for **data exchange** (interoperability), whereas OMOP is designed for **data analysis** (large-scale observational research).

```
┌────────────────────────────────────────────────────────┐
│                        FHIR                            │
│  - Optimised for exchange of individual patient data   │
│  - Raw, source terminology codes (SNOMED, RxNorm, etc.)│
│  - Highly variable structure (Extensions, Profiles)    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           │ ETL (Extract-Transform-Load)
                           ▼
┌────────────────────────────────────────────────────────┐
│                      OMOP CDM                          │
│  - Optimised for population-level analytical queries   │
│  - Unified Standard Concept IDs (Semantic Network)     │
│  - Standardised relational layout (Fixed tables/columns)│
└────────────────────────────────────────────────────────┘
```

### 2.1 The Terminology Nightmare vs. Standard Concept IDs
In FHIR, clinical codes are kept in their native systems or custom formats:
* **Conditions** can be coded in **SNOMED-CT**, **ICD-10-CM**, **ICD-9**, or custom hospital codes.
* **Medications** can use **RxNorm**, **ATC**, **NDC**, or local formulary text.

If you query raw FHIR bundles, you must build list arrays of every possible synonym code across all terminologies:
```python
# Terminology lists required when querying raw source data
diabetes_codes = ["44054006", "E11.9", "250.00", "DM-TYPE2-LOCAL-CODE"]
```

In OMOP CDM, the standard ETL process resolves all of these source codes into standard **OMOP Concept IDs** (e.g., SNOMED `44054006` maps to Standard Concept **201820**). The researcher only needs to query the Standard Concept ID:
```sql
WHERE co.condition_concept_id = 201820
```

### 2.2 Hierarchical Terminology Resolution (The Ancestor Table)
What if we want to query for "Diabetes" generally, including all sub-diagnoses (e.g., Type 2 Diabetes, Diabetic Nephropathy, Ketoacidosis)?
* **In FHIR:** You must lookup and manually hardcode dozens of SNOMED/ICD codes.
* **In OMOP:** You can use the standard `concept_ancestor` table. By querying for ancestors of concept `201820`, the database automatically returns all descendant conditions without you needing to know their specific codes.

```sql
JOIN concept_ancestor ca ON co.condition_concept_id = ca.descendant_concept_id
WHERE ca.ancestor_concept_id = 201820 -- Will match T2DM, complications, and specific manifestations
```

### 2.3 Structural Consistency
Each hospital installs FHIR with minor differences, custom resource extensions, and distinct profiles (e.g., US Core vs. Kemenkes SATUSEHAT). A script written to parse FHIR bundles from Hospital A will likely fail on Hospital B's files due to structural variance.

OMOP CDM enforces a **rigid, immutable schema**. Once data is transformed to OMOP CDM, the exact same SQL queries and statistical packages (HADES) can run across hundreds of global databases without modifying a single line of query logic.

---

## 3. Educational Summary: "Why Transform to OMOP?"

1. **Analytical Readability:** A researcher should focus on clinical definitions, not JSON nesting syntax. SQL queries are self-documenting and easier for statisticians to review.
2. **Semantic Interoperability:** OMOP harmonizes multi-source terminologies into unified Standard Concept IDs, eliminating vocabulary discrepancies.
3. **Performance at Scale:** OBSERVATIONAL databases hold millions of records. Parsing files on the fly is computationally impossible at scale. Relational databases with indexing run queries in milliseconds.
4. **Access to the OHDSI Ecosystem:** By converting to OMOP, you unlock the complete OHDSI toolstack (ATLAS for cohort creation, Achilles for database characterization, and HADES packages for patient-level prediction and population-level estimation).
5. **PII Security & Blinding:** The OMOP ETL process acts as a security boundary. Personally Identifiable Information (like raw national NIK numbers, names, addresses) is completely blinded or tokenized using secure hashes (e.g. SHA-256) before entering the database. Researchers can execute complete population queries without ever having access to raw patient identity.
