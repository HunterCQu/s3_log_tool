#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")") # Absolute path to the script's directory

export LOCAL_FILES_DOCUMENT_ROOT=/home/hunter/tool_platform
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true

# Properly activate conda environment
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate yolov5ds

TARGET_LOG_DIR=/home/hunter/tool_platform

nohup streamlit run "$SCRIPT_DIR/home.py" --server.fileWatcherType none --server.maxUploadSize 1024 --server.port 8511 > "$TARGET_LOG_DIR/nohup.out" 2>&1 &




