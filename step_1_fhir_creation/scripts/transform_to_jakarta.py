import os
import json
import random
import shutil

# Dynamic relative path resolution
script_dir = os.path.dirname(os.path.abspath(__file__))
step_1_dir = os.path.dirname(script_dir)

source_dir = os.path.join(step_1_dir, "output", "jakarta_patients", "fhir")
dest_dir = os.path.join(step_1_dir, "data", "fhir", "jakarta_hospital")

os.makedirs(dest_dir, exist_ok=True)

# Datasets for generating realistic Indonesian names and addresses
male_first_names = ["Budi", "Ahmad", "Joko", "Bambang", "Hendra", "Agus", "Slamet", "Adi", "Rizky", "Muhammad", "Dian", "Eko", "Dwi", "Tri", "Wahyu", "Rudi", "Sugeng", "Heru", "Andi", "Taufik"]
female_first_names = ["Siti", "Indah", "Dewi", "Kartika", "Putri", "Rini", "Wati", "Ani", "Sri", "Mega", "Dian", "Ayu", "Fitri", "Lani", "Desi", "Ratna", "Sari", "Yanti", "Novi", "Endang"]
surnames = ["Santoso", "Wijaya", "Hidayat", "Saputra", "Kusuma", "Siregar", "Simanjuntak", "Nasution", "Harahap", "Lubis", "Pratama", "Setiawan", "Kurniawan", "Lestari", "Wulandari", "Rahayu", "Hadi", "Nugroho", "Gunawan", "Utomo"]

jakarta_districts = [
    {"city": "Jakarta Selatan", "postalCode": "12110", "city_code": "3174", "district": "Tebet", "district_code": "317401", "village": "Menteng Dalam", "village_code": "3174011001", "street": "Jl. Tebet Barat Dalam No. {}"},
    {"city": "Jakarta Selatan", "postalCode": "12150", "city_code": "3174", "district": "Kebayoran Baru", "district_code": "317404", "village": "Melawai", "village_code": "3174041005", "street": "Jl. Melawai III No. {}"},
    {"city": "Jakarta Pusat", "postalCode": "10110", "city_code": "3171", "district": "Gambir", "district_code": "317101", "village": "Cideng", "village_code": "3171011002", "street": "Jl. Cideng Timur No. {}"},
    {"city": "Jakarta Timur", "postalCode": "13110", "city_code": "3175", "district": "Matraman", "district_code": "Matraman", "village": "Pisangan Baru", "village_code": "3175011001", "street": "Jl. Pisangan Baru Raya No. {}"},
    {"city": "Jakarta Barat", "postalCode": "11110", "city_code": "3173", "district": "Tamansari", "district_code": "317301", "village": "Krukut", "village_code": "3173011003", "street": "Jl. Krukut Raya No. {}"}
]

print("Initializing Jakarta Patient Profile Transformation Script...")
print(f"Reading from: {source_dir}")
print(f"Writing to: {dest_dir}")
print("-" * 60)

if not os.path.exists(source_dir):
    print(f"Error: Source directory {source_dir} does not exist yet. Please wait for Synthea to finish generating.")
    exit(1)

files = [f for f in os.listdir(source_dir) if f.endswith(".json") and "Information" not in f]
print(f"Found {len(files)} generated patients.")

stats = {
    "total": 0,
    "communicable": {
        "tuberculosis": 0,
        "urinary_tract_infection": 0,
        "hiv": 0
    },
    "non_communicable": {
        "diabetes": 0,
        "hypertension": 0,
        "asthma": 0,
        "copd": 0,
        "cardiovascular": 0
    },
    "discover_study_cohort": 0
}

transformed_count = 0

for filename in files:
    filepath = os.path.join(source_dir, filename)
    with open(filepath, 'r') as f:
        try:
            bundle = json.load(f)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
            
    entries = bundle.get("entry", [])
    resources = [entry.get("resource", {}) for entry in entries if "resource" in entry]
    
    # 1. Process Patient Resource
    patient = next((r for r in resources if r.get("resourceType") == "Patient"), None)
    if not patient:
        continue
        
    stats["total"] += 1
    
    # Check original gender to assign correct name
    gender = patient.get("gender", "unknown")
    if gender == "male":
        first_name = random.choice(male_first_names)
    else:
        first_name = random.choice(female_first_names)
    last_name = random.choice(surnames)
    new_full_name = f"{first_name} {last_name}"
    
    # Update Patient Name
    patient["name"] = [{
        "use": "official",
        "text": new_full_name,
        "family": last_name,
        "given": [first_name]
    }]
    
    # Generate realistic NIK (National ID) and IHS numbers
    nik = f"3174{random.randint(10,99)}{random.randint(100000, 999999)}0001"
    ihs = f"P{random.randint(1000000000, 9999999999)}"
    
    patient["identifier"] = [
        {
            "use": "official",
            "system": "https://fhir.kemkes.go.id/id/nik",
            "value": nik
        },
        {
            "use": "official",
            "system": "https://fhir.kemkes.go.id/id/ihs-number",
            "value": ihs
        }
    ]
    
    # Update metadata profile to reflect Kemenkes Patient Profile
    patient["meta"] = {
        "profile": [
            "https://fhir.kemkes.go.id/r4/StructureDefinition/Patient"
        ]
    }
    
    # Choose a random Jakarta address template
    addr_tmpl = random.choice(jakarta_districts)
    street_line = addr_tmpl["street"].format(random.randint(1, 150))
    
    patient["address"] = [{
        "use": "home",
        "line": [street_line],
        "city": addr_tmpl["city"],
        "state": "DKI Jakarta",
        "postalCode": addr_tmpl["postalCode"],
        "country": "ID",
        "extension": [
            {
                "url": "https://fhir.kemkes.go.id/r4/StructureDefinition/administrativeCode",
                "extension": [
                    {
                        "url": "province",
                        "valueCode": "31"
                    },
                    {
                        "url": "city",
                        "valueCode": addr_tmpl["city_code"]
                    },
                    {
                        "url": "district",
                        "valueCode": addr_tmpl["district_code"]
                    },
                    {
                        "url": "village",
                        "valueCode": addr_tmpl["village_code"]
                    }
                ]
            }
        ]
    }]
    
    # Update communication to Indonesian preferred
    patient["communication"] = [{
        "language": {
            "coding": [
                {
                    "system": "urn:ietf:bcp:47",
                    "code": "id-ID",
                    "display": "Indonesian"
                }
            ],
            "text": "Indonesian"
        },
        "preferred": True
    }]
    
    # 2. Map and identify Conditions
    conditions = [r for r in resources if r.get("resourceType") == "Condition"]
    has_tb = False
    has_uti = False
    has_hiv = False
    has_t2d = False
    has_ht = False
    has_asthma = False
    has_copd = False
    has_cv = False
    
    for cond in conditions:
        codings = cond.get("code", {}).get("coding", [])
        for coding in codings:
            code = coding.get("code")
            display = coding.get("display", "").lower()
            
            # Communicable Disease Checks
            if code == "11388002" or "tuberculosis" in display or "tb" in display:
                has_tb = True
            elif "urinary tract infection" in display or "cystitis" in display:
                has_uti = True
            elif "human immunodeficiency virus" in display or "hiv" in display:
                has_hiv = True
                
            # Non-Communicable Disease Checks
            elif code == "44054006" or "type 2 diabetes" in display or "type ii diabetes" in display:
                has_t2d = True
            elif "hypertension" in display:
                has_ht = True
            elif "asthma" in display:
                has_asthma = True
            elif "chronic obstructive pulmonary" in display or "copd" in display:
                has_copd = True
            elif "coronary heart disease" in display or "myocardial infarction" in display or "cardiac" in display:
                has_cv = True

    # Check for DISCOVER Study Cohort matching (Type 2 Diabetes + Age >= 18 + taking anti-diabetic medication)
    is_discover_cohort = False
    if has_t2d:
        # Check patient age
        birth_date = patient.get("birthDate", "")
        age = 0
        if birth_date:
            from datetime import datetime
            birth = datetime.strptime(birth_date, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth.year
        
        if age >= 18:
            med_requests = [r for r in resources if r.get("resourceType") == "MedicationRequest"]
            for med in med_requests:
                concept = med.get("medicationCodeableConcept", {})
                codings = concept.get("coding", [])
                med_text = concept.get("text", "")
                t2d_med_keywords = ["metformin", "sulfonylurea", "glipizide", "glyburide", "glimepiride", 
                                    "pioglitazone", "rosiglitazone", "sitagliptin", "saxagliptin", "linagliptin", 
                                    "exenatide", "liraglutide", "dulaglutide", "semaglutide", 
                                    "canagliflozin", "dapagliflozin", "empagliflozin", "insulin"]
                if any(kw in med_text.lower() or any(kw in c.get("display", "").lower() for c in codings) for kw in t2d_med_keywords):
                    is_discover_cohort = True
                    break

    # Record stats
    if has_tb: stats["communicable"]["tuberculosis"] += 1
    if has_uti: stats["communicable"]["urinary_tract_infection"] += 1
    if has_hiv: stats["communicable"]["hiv"] += 1
    if has_t2d: stats["non_communicable"]["diabetes"] += 1
    if has_ht: stats["non_communicable"]["hypertension"] += 1
    if has_asthma: stats["non_communicable"]["asthma"] += 1
    if has_copd: stats["non_communicable"]["copd"] += 1
    if has_cv: stats["non_communicable"]["cardiovascular"] += 1
    if is_discover_cohort: stats["discover_study_cohort"] += 1
    
    # 3. Update all organization name fields to mock SATUSEHAT RSUD Tarakan Jakarta
    for r in resources:
        if r.get("resourceType") == "Organization":
            r["name"] = "RSUD Tarakan Jakarta"
            r["identifier"] = [{
                "system": "http://sys-ids.kemkes.go.id/organization/10000004",
                "value": "10000004"
            }]
        elif r.get("resourceType") == "Location":
            r["name"] = "Ruang Rawat Jalan - RSUD Tarakan"
            r["managingOrganization"] = {
                "reference": "Organization/10000004",
                "display": "RSUD Tarakan Jakarta"
            }

    # Save to destination folder
    new_filename = f"{first_name}_{last_name}_{bundle.get('id', random.randint(100000,999999))}.json"
    with open(os.path.join(dest_dir, new_filename), 'w') as out_f:
        json.dump(bundle, out_f, indent=2)
    
    transformed_count += 1

print("\nTransformation Complete! Summary of the Jakarta Hospital Patient Dataset:")
print("=" * 60)
print(f"Total Patients Transformed: {transformed_count}")
print("-" * 60)
print("Communicable Diseases Cohort:")
print(f"  - Tuberculosis (TB): {stats['communicable']['tuberculosis']}")
print(f"  - Urinary Tract Infection (UTI): {stats['communicable']['urinary_tract_infection']}")
print(f"  - HIV: {stats['communicable']['hiv']}")
print("-" * 60)
print("Non-Communicable Diseases Cohort:")
print(f"  - Type 2 Diabetes Mellitus: {stats['non_communicable']['diabetes']}")
print(f"  - Hypertension: {stats['non_communicable']['hypertension']}")
print(f"  - Asthma: {stats['non_communicable']['asthma']}")
print(f"  - COPD: {stats['non_communicable']['copd']}")
print(f"  - Cardiovascular Disease (CHD/MI): {stats['non_communicable']['cardiovascular']}")
print("-" * 60)
print(f"DISCOVER Study Cohort Matches (Adults with T2DM on treatment): {stats['discover_study_cohort']}")
print("=" * 60)
print(f"All records formatted to Kemenkes SATUSEHAT FHIR profile and saved to: {dest_dir}")
