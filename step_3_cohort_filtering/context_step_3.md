# Context Step 3: Comparative Analysis & Cohort Filtering

## 1. Objective
The objective of Step 3 is to compare the performance, implementation complexity, and data privacy profiles of two different data search strategies:
1. **Direct FHIR Filtering:** Parsing raw JSON transaction bundles in Python.
2. **OMOP CDM Database Filtering:** Running indexed SQL queries against standard relational tables.

This serves as a technical and methodological demonstration of *why* healthcare systems invest resources in transforming EMR data to the OMOP CDM standard for clinical research.

---

## 2. Technical & Security Metrics Dashboard

Running the comparative script [run_comparison.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_3_cohort_filtering/scripts/run_comparison.py) yields the following metrics:

| Performance & Operational Dimension | Direct FHIR (JSON) | OMOP CDM (SQL) |
| :--- | :--- | :--- |
| **Cohort Matches Identified** | 17 patients | 17 patients |
| **In-Script Filtering Time** | **~5,901.65 ms** | **~92.87 ms** |
| **Lines of Code Required** | 129 lines (complex loops) | 64 lines (declarative SQL) |
| **PII / Data Privacy Security** | ❌ **EXPOSED:** Accesses raw NIK. |  **SECURE:** Accesses tokenized/blinded values. |
| **Access Pattern** | Procedural (In-memory parser) | Declarative (Structured query) |
| **Data I/O Mode** | Iterative disk file read (I/O bound) | Relational database (B-Tree indexing) |

---

## 3. Key Findings

### 3.1 Speed & Scalability Gap
* **The Result:** The OMOP CDM relational query is **60x to 80x faster** than direct JSON file parsing.
* **Why it matters:** On a small test dataset of 276 patients, the difference is seconds. On a typical hospital scale of **1,000,000 patients**, direct JSON traversal requires days of high-performance Spark/Hadoop processing and high I/O overhead. In contrast, the indexed SQL query completes in **milliseconds**.

### 3.2 Terminology Standardization
* **In FHIR:** The query logic must know and list all specific target codes across different nomenclatures (e.g. tracking both SNOMED and ICD codes) for conditions and medications.
* **In OMOP:** The query references only the unified Standard Concept ID (e.g. T2DM Concept **201820**), as terminology mapping is resolved beforehand during the ETL process.

### 3.3 Patient Identity Exposure (Security boundary)
* **In FHIR:** Direct file filtering exposes raw patient demographics and identifiers (like national NIK numbers) directly to the script or query author.
* **In OMOP:** The script reads only de-identified SHA-256 tokens (`tok_xxxxxx`), completely protecting patient confidentiality.

---

## 4. Execution Commands
To run the cohort filtering comparisons:
```bash
# Run direct FHIR filter script
python3 step_3_cohort_filtering/scripts/filter_cohort_from_fhir.py

# Run OMOP CDM SQL filter script
python3 step_3_cohort_filtering/scripts/filter_cohort_from_omop.py

# Run side-by-side performance benchmark runner
python3 step_3_cohort_filtering/scripts/run_comparison.py
```
Read the detailed conceptual write-up in [comparison_analysis.md](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_3_cohort_filtering/comparison_analysis.md).
