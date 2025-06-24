import os
import streamlit as st
from io import BytesIO
from zipfile import ZipFile
from PIL import Image, ImageFile
import numpy as np
import cv2

# Enable truncated image loading for Pillow
ImageFile.LOAD_TRUNCATED_IMAGES = True

def process_drc_file(drc_file):
    images = []
    with drc_file as f:
        while True:
            # Read and parse header and metadata
            protocol_head = f.read(8)
            small_head = f.read(3)
            log_type = int.from_bytes(f.read(1), 'little')
            real_len = int.from_bytes(f.read(4), 'little')
            robot_sn = f.read(16)
            
            if real_len == 0:
                break

            # Read the log data
            log_data = f.read(real_len)
            if log_type != 7:
                continue
            
            sys_count = int.from_bytes(log_data[:1], 'little')
            data_type = int.from_bytes(log_data[1:2], 'little')
            data_len = int.from_bytes(log_data[2:6], 'little')
            time_stamp = int.from_bytes(log_data[6:14], 'little')

            img_data = log_data[14:14 + data_len]
            if data_type > 30:
                continue

            try:
                img = Image.open(BytesIO(img_data))
                img = img.convert("RGB")
                img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
                
                # Crop and save the specific region
                show_img = img[:, 0:320, :]
                images.append((show_img, time_stamp))
            except (OSError, ValueError) as e:
                st.error(f"Error processing image at timestamp {time_stamp}: {e}")
                
    return images

st.title("DRC File Image Extraction")

# File upload
uploaded_files = st.file_uploader("Upload DRC files", type="drc", accept_multiple_files=True)
if uploaded_files:
    # Create a single zip buffer for all files
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zip_file:
        total_images = 0  # Track total image count for progress
        for drc_file in uploaded_files:
            st.subheader(f"Processing {drc_file.name}")
            
            # Process each DRC file and get images
            images = process_drc_file(drc_file)
            total_images += len(images)
            
            # Add images to the zip file
            for idx, (img, timestamp) in enumerate(images):
                img_file_name = f"{drc_file.name}_{timestamp}.jpg"
                _, buffer = cv2.imencode(".jpg", img)
                zip_file.writestr(img_file_name, buffer.tobytes())
                
                # Update progress
                progress = (total_images - len(images) + idx + 1) / total_images
                st.progress(progress)

    # Prepare download button for the single zip containing all images
    zip_buffer.seek(0)
    st.download_button(
        label="Download all extracted images",
        data=zip_buffer,
        file_name="extracted_images.zip",
        mime="application/zip"
    )
