#!/bin/bash
source activate data_process

python3 crop_by_mask.py \
  --mask_folder /data/zhouzuxing/分割模型/img_gt \
  --rgb_folder /data/zhouzuxing/model_test_platform/images_set/TestData_0611_3230 \
  --save_dir /home/hunter/conda_test
