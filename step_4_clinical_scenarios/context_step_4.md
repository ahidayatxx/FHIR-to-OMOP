# Context Step 4: Clinical Trial & Hospital Operations

## 1. Objective
The objective of Step 4 is to demonstrate how a standardized research database (OMOP CDM) is used to answer real-world clinical operations questions and to analyze the technical and regulatory bottlenecks encountered when maintaining research databases in hospital IT environments.

---

## 2. Operational Sections & Outputs

### Section 1: Clinical Trial Workflow
* **1a. Feasibility Study:** Uses [feasibility_study.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/scripts/feasibility_study.py) to compile aggregate cohort dimensions.
  * **Result:** Identified **17 eligible candidates** (58.82% Male, 41.18% Female) with an average blood pressure baseline of **108.0/67.0 mmHg**. Output saved to [feasibility_report.txt](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/feasibility_report.txt).
* **1b. Patient Recruitment:** Uses [patient_recruitment.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/scripts/patient_recruitment.py) to generate a detailed screening roster.
  * **Result:** Roster lists candidate tokenized NIKs, age, gender, and clinical risk categories (e.g. ⚠️ flags patient `tok_422e8d398dce2204` with high blood pressure of 153/94 mmHg). Output saved to [recruitment_list.txt](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/recruitment_list.txt).
* **1c. Feasibility Questionnaire:** The pre-populated site readiness survey [feasibility_questionnaire.md](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/feasibility_questionnaire.md) containing the exact numbers and compliance parameters of RSUD Tarakan Jakarta for the EXPLORE Study.

### Section 2: Hospital Operations (Reality Check & Imminent Issues)
Maintains the technical and administrative critique of hospital database operations:
* **The Reality Check (Simulated vs. Real Data):** Synthea data is structured, digitized, and complete. Real hospital data is **scattered** across departmental software silo systems, **unstructured** (70%+ free-text clinical notes, PDFs requiring NLP/OCR), and **analog/paper-based**.
* **Continuous Pipeline Latency (`EMR -> FHIR -> OMOP`):** Operational latency, transaction out-of-order constraints, database lock conflicts during active inpatient updates, and schema validation breaks.
* **PII Decryption Bottleneck:** Managing secure map-back lookup mechanisms from de-identified research tokens (`tok_xxxxxx`) to raw EHR names/contact info inside the hospital intranet firewall.
* **Consent Management:** Ensuring opt-out flags comply with Indonesian personal data protection regulations (**UU PDP No. 27/2022**).
* **Vocabulary Gaps:** Translating local drug codes (like BPJS systems) and local lab test titles into standard RxNorm and LOINC concepts.

---

## 3. Scripts & Documents

* [scenarios_guide.md](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/scenarios_guide.md): Concept guide detailing clinical trial workflows and operational issues.
* [feasibility_questionnaire.md](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/feasibility_questionnaire.md): Pre-populated site readiness survey sent to the sponsor.
* [feasibility_report.txt](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/feasibility_report.txt): Auto-generated aggregate feasibility numbers.
* [recruitment_list.txt](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/recruitment_list.txt): Auto-generated de-identified candidate screening roster.
* [scripts/feasibility_study.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/scripts/feasibility_study.py): Feasibility computation script.
* [scripts/patient_recruitment.py](file:///Users/ahmadhidayat/claude-code/projects/FHIR-to-OMOP/step_4_clinical_scenarios/scripts/patient_recruitment.py): Candidate screening roster compilation script.

---

## 4. Execution Commands
To execute the scenarios, run:
```bash
# Run aggregate feasibility study
python3 step_4_clinical_scenarios/scripts/feasibility_study.py

# Run recruitment roster list
python3 step_4_clinical_scenarios/scripts/patient_recruitment.py
```
Outputs are automatically written to `feasibility_report.txt` and `recruitment_list.txt` in the Step 4 folder.
