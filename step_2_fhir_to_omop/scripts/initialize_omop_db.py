import os
import sqlite3

# Resolve database path dynamically relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
step_2_dir = os.path.dirname(script_dir)
db_path = os.path.join(step_2_dir, "data", "omop_cdm.db")

os.makedirs(os.path.dirname(db_path), exist_ok=True)

print(f"Initializing SQLite database for OMOP CDM v5.4 at: {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List of DDL statements for core OMOP CDM v5.4 tables
ddl_statements = [
    # 1. CONCEPT table
    """
    CREATE TABLE IF NOT EXISTS concept (
        concept_id INTEGER PRIMARY KEY,
        concept_name TEXT NOT NULL,
        domain_id TEXT NOT NULL,
        vocabulary_id TEXT NOT NULL,
        concept_class_id TEXT NOT NULL,
        standard_concept TEXT,
        concept_code TEXT NOT NULL,
        valid_start_date TEXT NOT NULL,
        valid_end_date TEXT NOT NULL,
        invalid_reason TEXT
    );
    """,
    # 2. VOCABULARY table
    """
    CREATE TABLE IF NOT EXISTS vocabulary (
        vocabulary_id TEXT PRIMARY KEY,
        vocabulary_name TEXT NOT NULL,
        vocabulary_reference TEXT NOT NULL,
        vocabulary_version TEXT,
        vocabulary_concept_id INTEGER NOT NULL
    );
    """,
    # 3. LOCATION table
    """
    CREATE TABLE IF NOT EXISTS location (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        address_1 TEXT,
        address_2 TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        county TEXT,
        location_source_value TEXT,
        country_concept_id INTEGER,
        country_source_value TEXT,
        latitude REAL,
        longitude REAL
    );
    """,
    # 4. CARE_SITE table
    """
    CREATE TABLE IF NOT EXISTS care_site (
        care_site_id INTEGER PRIMARY KEY AUTOINCREMENT,
        care_site_name TEXT,
        place_of_service_concept_id INTEGER,
        location_id INTEGER,
        care_site_source_value TEXT,
        place_of_service_source_value TEXT,
        FOREIGN KEY (location_id) REFERENCES location (location_id)
    );
    """,
    # 5. PROVIDER table
    """
    CREATE TABLE IF NOT EXISTS provider (
        provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name TEXT,
        npi TEXT,
        dea TEXT,
        specialty_concept_id INTEGER,
        care_site_id INTEGER,
        year_of_birth INTEGER,
        gender_concept_id INTEGER,
        provider_source_value TEXT,
        specialty_source_value TEXT,
        specialty_user_defined_value TEXT,
        gender_source_value TEXT,
        gender_source_concept_id INTEGER,
        FOREIGN KEY (care_site_id) REFERENCES care_site (care_site_id)
    );
    """,
    # 6. PERSON table
    """
    CREATE TABLE IF NOT EXISTS person (
        person_id INTEGER PRIMARY KEY AUTOINCREMENT,
        gender_concept_id INTEGER NOT NULL,
        year_of_birth INTEGER NOT NULL,
        month_of_birth INTEGER,
        day_of_birth INTEGER,
        birth_datetime TEXT,
        race_concept_id INTEGER NOT NULL,
        ethnicity_concept_id INTEGER NOT NULL,
        location_id INTEGER,
        provider_id INTEGER,
        care_site_id INTEGER,
        person_source_value TEXT,
        gender_source_value TEXT,
        gender_source_concept_id INTEGER,
        race_source_value TEXT,
        race_source_concept_id INTEGER,
        ethnicity_source_value TEXT,
        ethnicity_source_concept_id INTEGER,
        FOREIGN KEY (location_id) REFERENCES location (location_id),
        FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
        FOREIGN KEY (care_site_id) REFERENCES care_site (care_site_id)
    );
    """,
    # 7. VISIT_OCCURRENCE table
    """
    CREATE TABLE IF NOT EXISTS visit_occurrence (
        visit_occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        visit_concept_id INTEGER NOT NULL,
        visit_start_date TEXT NOT NULL,
        visit_start_datetime TEXT,
        visit_end_date TEXT NOT NULL,
        visit_end_datetime TEXT,
        visit_type_concept_id INTEGER NOT NULL,
        provider_id INTEGER,
        care_site_id INTEGER,
        visit_source_value TEXT,
        visit_source_concept_id INTEGER,
        admitted_from_concept_id INTEGER,
        admitted_from_source_value TEXT,
        discharged_to_concept_id INTEGER,
        discharged_to_source_value TEXT,
        preceding_visit_occurrence_id INTEGER,
        FOREIGN KEY (person_id) REFERENCES person (person_id),
        FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
        FOREIGN KEY (care_site_id) REFERENCES care_site (care_site_id)
    );
    """,
    # 8. CONDITION_OCCURRENCE table
    """
    CREATE TABLE IF NOT EXISTS condition_occurrence (
        condition_occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        condition_concept_id INTEGER NOT NULL,
        condition_start_date TEXT NOT NULL,
        condition_start_datetime TEXT,
        condition_end_date TEXT,
        condition_end_datetime TEXT,
        condition_type_concept_id INTEGER NOT NULL,
        condition_status_concept_id INTEGER,
        stop_reason TEXT,
        provider_id INTEGER,
        visit_occurrence_id INTEGER,
        visit_detail_id INTEGER,
        condition_source_value TEXT,
        condition_source_concept_id INTEGER,
        condition_status_source_value TEXT,
        FOREIGN KEY (person_id) REFERENCES person (person_id),
        FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
        FOREIGN KEY (visit_occurrence_id) REFERENCES visit_occurrence (visit_occurrence_id)
    );
    """,
    # 9. DRUG_EXPOSURE table
    """
    CREATE TABLE IF NOT EXISTS drug_exposure (
        drug_exposure_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        drug_concept_id INTEGER NOT NULL,
        drug_exposure_start_date TEXT NOT NULL,
        drug_exposure_start_datetime TEXT,
        drug_exposure_end_date TEXT,
        drug_exposure_end_datetime TEXT,
        verbatim_end_date TEXT,
        drug_type_concept_id INTEGER NOT NULL,
        stop_reason TEXT,
        refills INTEGER,
        quantity REAL,
        days_supply INTEGER,
        sig TEXT,
        route_concept_id INTEGER,
        lot_number TEXT,
        provider_id INTEGER,
        visit_occurrence_id INTEGER,
        visit_detail_id INTEGER,
        drug_source_value TEXT,
        drug_source_concept_id INTEGER,
        route_source_value TEXT,
        dose_unit_source_value TEXT,
        FOREIGN KEY (person_id) REFERENCES person (person_id),
        FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
        FOREIGN KEY (visit_occurrence_id) REFERENCES visit_occurrence (visit_occurrence_id)
    );
    """,
    # 10. MEASUREMENT table
    """
    CREATE TABLE IF NOT EXISTS measurement (
        measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        measurement_concept_id INTEGER NOT NULL,
        measurement_date TEXT NOT NULL,
        measurement_datetime TEXT,
        measurement_time TEXT,
        measurement_type_concept_id INTEGER NOT NULL,
        operator_concept_id INTEGER,
        value_as_number REAL,
        value_as_concept_id INTEGER,
        unit_concept_id INTEGER,
        range_low REAL,
        range_high REAL,
        provider_id INTEGER,
        visit_occurrence_id INTEGER,
        visit_detail_id INTEGER,
        measurement_source_value TEXT,
        measurement_source_concept_id INTEGER,
        unit_source_value TEXT,
        unit_source_concept_id INTEGER,
        value_source_value TEXT,
        measurement_event_id INTEGER,
        meas_event_field_concept_id INTEGER,
        FOREIGN KEY (person_id) REFERENCES person (person_id),
        FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
        FOREIGN KEY (visit_occurrence_id) REFERENCES visit_occurrence (visit_occurrence_id)
    );
    """,
    # 11. PROCEDURE_OCCURRENCE table
    """
    CREATE TABLE IF NOT EXISTS procedure_occurrence (
        procedure_occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        procedure_concept_id INTEGER NOT NULL,
        procedure_date TEXT NOT NULL,
        procedure_datetime TEXT,
        procedure_end_date TEXT,
        procedure_end_datetime TEXT,
        procedure_type_concept_id INTEGER NOT NULL,
        modifier_concept_id INTEGER,
        quantity INTEGER,
        provider_id INTEGER,
        visit_occurrence_id INTEGER,
        visit_detail_id INTEGER,
        procedure_source_value TEXT,
        procedure_source_concept_id INTEGER,
        modifier_source_value TEXT,
        FOREIGN KEY (person_id) REFERENCES person (person_id),
        FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
        FOREIGN KEY (visit_occurrence_id) REFERENCES visit_occurrence (visit_occurrence_id)
    );
    """
]

for ddl in ddl_statements:
    cursor.execute(ddl)

conn.commit()
conn.close()

print("Database initialization successful! Standard OMOP CDM v5.4 tables created.")
