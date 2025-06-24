import cv2
import os
import glob
from natsort import natsorted
import numpy as np

input_folder = '/home/hunter/drc_download_platfor/drc_img/record_20250603_135818'  # replace with your image path
output_video = 'output_video.mp4'
fps = 10  # frames per second

# Step 1: Group images by crop index
crop_images = {f"crop{i}": [] for i in range(1, 5)}
all_images = natsorted(glob.glob(os.path.join(input_folder, '*.png')))

for img_path in all_images:
    for i in range(1, 5):
        if f'_crop{i}.png' in img_path:
            crop_images[f"crop{i}"].append(img_path)
            break

# Step 2: Make sure all crops have the same number of frames
num_frames = min(len(v) for v in crop_images.values())
for k in crop_images:
    crop_images[k] = crop_images[k][:num_frames]

# Step 3: Read frames and compose video
sample_img = cv2.imread(crop_images['crop1'][0])
target_h, target_w = sample_img.shape[:2]

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video, fourcc, fps, (target_w * 2, target_h * 2))  # 2x2 grid

for i in range(num_frames):
    imgs = []
    for j in range(1, 5):
        img = cv2.imread(crop_images[f"crop{j}"][i])
        img_resized = cv2.resize(img, (target_w, target_h))
        imgs.append(img_resized)

    top = np.hstack((imgs[0], imgs[1]))
    bottom = np.hstack((imgs[2], imgs[3]))
    grid = np.vstack((top, bottom))

    out.write(grid)

out.release()
print(f"Video saved to: {output_video}")

