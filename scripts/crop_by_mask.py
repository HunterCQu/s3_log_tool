#!/usr/bin/env python3

import cv2
import numpy as np
import os
import argparse

parser = argparse.ArgumentParser(description='Refined crop from mask with edge connectivity constraint.')
parser.add_argument('--mask_folder', type=str, default='/home/hunter/drc_download_platfor/drc_seg')
parser.add_argument('--rgb_folder', type=str, default='/home/hunter/drc_download_platfor/drc_img')
parser.add_argument('--save_dir', type=str, default='/home/hunter/drc_download_platfor/croped_img_out')
args = parser.parse_args()

os.makedirs(args.save_dir, exist_ok=True)

target_colors = [
    (0, 0, 0),
    (100, 100, 100),
    (150, 150, 150),
    (200, 200, 200)
]
block_color = (50, 50, 50)

crop_idx = 0

# 1. Build RGB path map
rgb_file_map = {}
for root, _, files in os.walk(args.rgb_folder):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            rgb_file_map[os.path.splitext(file)[0]] = os.path.join(root, file)

# 2. Iterate mask files
mask_files = [f for f in os.listdir(args.mask_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
for mask_file in mask_files:
    mask_path = os.path.join(args.mask_folder, mask_file)
    mask_name_wo_ext = os.path.splitext(mask_file)[0]
    rgb_path = rgb_file_map.get(mask_name_wo_ext)

    if rgb_path is None or not os.path.exists(rgb_path):
        print(f"Warning: RGB image not found for mask {mask_file}")
        continue

    mask_img = cv2.imread(mask_path)
    rgb_img = cv2.imread(rgb_path)

    # 3. Extract block region mask (50, 50, 50)
    block_mask = cv2.inRange(mask_img, np.array(block_color), np.array(block_color))

    for color in target_colors:
        color_mask = cv2.inRange(mask_img, np.array(color), np.array(color))
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(color_mask, connectivity=8)

        for i in range(1, num_labels):  # skip background
            x, y, w, h, area = stats[i]
            if area < 500:
                continue
            if w > 160 or h > 160:
                continue
            # Extract region mask
            region_mask = (labels[y:y+h, x:x+w] == i).astype(np.uint8) * 255
            block_sub_mask = block_mask[y:y+h, x:x+w]

            # Check how many sides are connected to block_color
            contact_edges = 0
            edge_pixels = {
                'top':    block_sub_mask[0, :],
                'bottom': block_sub_mask[-1, :],
                'left':   block_sub_mask[:, 0],
                'right':  block_sub_mask[:, -1]
            }
            for edge_name, pixels in edge_pixels.items():
                if np.any(pixels == 255):
                    contact_edges += 1

            if contact_edges >= 3:
                crop = rgb_img[y:y+h, x:x+w]
                save_path = os.path.join(args.save_dir, f'crop_{crop_idx:04d}_color{color}_w{w}_h{h}.png')
                cv2.imwrite(save_path, crop)
                crop_idx += 1
