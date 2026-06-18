#!/bin/bash

# --- Master Pipeline for Generating Jakarta Hospital FHIR Patient Data ---

# Stop execution if any command fails
set -e

# Get current script directory to make the execution location-independent
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

POPULATION=${1:-100}
MIN_AGE=5
MAX_AGE=90

echo "=============================================================="
echo "Starting Jakarta Patient Data Generation Pipeline (Step 1)"
echo "Target Population Size: $POPULATION"
echo "Age Range: $MIN_AGE - $MAX_AGE"
echo "=============================================================="

# 1. Run Synthea generation
echo -e "\n[Step 1.1] Running Synthea patient simulator..."
java -jar ../../../synthea-with-dependencies.jar -p "$POPULATION" -a "$MIN_AGE-$MAX_AGE" -c synthea.properties

# 2. Run Python transformation script to map to Jakarta SATUSEHAT profile
echo -e "\n[Step 1.2] Transforming US patient records to Jakarta SATUSEHAT profiles..."
python3 scripts/transform_to_jakarta.py

# 3. Clean up the raw US-formatted output directory
echo -e "\n[Step 1.3] Cleaning up temporary raw Synthea outputs..."
rm -rf output

echo -e "\n=============================================================="
echo "Step 1 Pipeline execution finished successfully! ✅"
echo "Check your aligned patient profiles under: data/fhir/jakarta_hospital/"
echo "=============================================================="
