#!/bin/bash
source activate data_process

# Arguments
IMG_PATH="/home/hunter/drc_download_platfor/drc_img"  # this can be a folder or .jpg/.png
CONFIG_PATH="/home/hunter/drc_download_platfor/mmsegmentation/configs/ld/stdc2_grass-320x272.py"
CHECKPOINT_PATH="/home/hunter/drc_download_platfor/mmsegmentation/demo/epoch_50.pth"
OUT_PATH="/home/hunter/drc_download_platfor/chengkuan_seg"

# Run inference
python /home/hunter/drc_download_platfor/mmsegmentation/demo/image_demo.py \
    "$IMG_PATH" \
    "$CONFIG_PATH" \
    "$CHECKPOINT_PATH" \
    --out-file "$OUT_PATH" \
    --save-pred-mask
