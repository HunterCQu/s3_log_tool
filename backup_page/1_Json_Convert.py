import os
import json
import uuid
from datetime import datetime
import streamlit as st

def combine_json_files(image_folder, json_files):
    """Combine multiple JSON files into a single JSON structure."""
    combined_data = []
    progress_bar = st.progress(0)
    
    for i, json_file in enumerate(json_files):
        original_json = json.load(json_file)
        original_width = original_json.get("imageWidth", 640)  # Default width
        original_height = original_json.get("imageHeight", 544)  # Default height
        image_name = os.path.basename(original_json.get("imagePath", ""))
        
        combined_entry = {
            "id": original_json.get("id", int(uuid.uuid4().int) % 100000),
            "annotations": [],
            "drafts": [],
            "predictions": [],
            "data": {
                "image": f"/data/local-files/?d=data_pool/{image_folder}/{image_name}",
            },
            "meta": {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "inner_id": 1,
            "total_annotations": len(original_json.get("shapes", [])),
            "cancelled_annotations": 0,
            "total_predictions": 0,
            "comment_count": 0,
            "unresolved_comment_count": 0,
            "last_comment_updated_at": None,
            "project": 28,
            "updated_by": 1,
            "comment_authors": []
        }

        for shape in original_json.get("shapes", []):
            normalized_points = [
                [point[0] / original_width * 100, point[1] / original_height * 100] for point in shape["points"]
            ]
            
            annotation = {
                "id": int(uuid.uuid4().int) % 100000,
                "completed_by": 1,
                "result": [{
                    "original_width": original_width,
                    "original_height": original_height,
                    "image_rotation": 0,
                    "value": {
                        "points": normalized_points,
                        "closed": True,
                        "polygonlabels": [shape["label"]]
                    },
                    "id": str(uuid.uuid4()),
                    "from_name": "label",
                    "to_name": "image",
                    "type": "polygonlabels",
                    "origin": "manual"
                }],
                "was_cancelled": False,
                "ground_truth": False,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "draft_created_at": datetime.utcnow().isoformat() + "Z",
                "lead_time": 0,
                "prediction": {},
                "result_count": 0,
                "unique_id": str(uuid.uuid4()),
                "import_id": None,
                "last_action": None,
                "task": combined_entry["id"],
                "project": 28,
                "updated_by": 1,
                "parent_prediction": None,
                "parent_annotation": None,
                "last_created_by": None
            }
            combined_entry["annotations"].append(annotation)
        
        combined_data.append(combined_entry)
        progress_bar.progress((i + 1) / len(json_files))
    
    return json.dumps(combined_data, indent=2)

# Streamlit UI
st.title("Model Pred. JSON to Label-Studio JSON")

# Folder confirmation button for images
image_folder_name = st.text_input("Enter a folder name for the images")

# Use session state to retain folder path
if "image_folder_path" not in st.session_state:
    st.session_state.image_folder_path = None

# Upload images
uploaded_images = st.file_uploader("Upload Image Files", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

confirm_folder_button = st.button("Confirm upload images")

if confirm_folder_button:
    if image_folder_name:
        st.session_state.image_folder_path = f"/data/playground/label_anything/data_pool/{image_folder_name}"
        os.makedirs(st.session_state.image_folder_path, exist_ok=True)
    else:
        st.error("Please enter a valid folder name for the images.")

if uploaded_images and st.session_state.image_folder_path:
    # Save images to the confirmed folder path
    for image_file in uploaded_images:
        with open(os.path.join(st.session_state.image_folder_path, image_file.name), 'wb') as f:
            f.write(image_file.getbuffer())
    st.success(f"Images uploaded to {st.session_state.image_folder_path}")

# Upload JSON files
uploaded_json_files = st.file_uploader("Upload JSON Files", type=["json"], accept_multiple_files=True)

# Run button
if st.button("Run"):
    if not uploaded_json_files:
        st.error("Please upload JSON files.")
    elif not uploaded_images or not st.session_state.image_folder_path:
        st.error("Please upload images and confirm a folder name.")
    else:
        combined_json_data = combine_json_files(image_folder_name, uploaded_json_files)

        # Display the result and add a download button
        st.success("JSON data combined successfully!")
        st.download_button(
            label="Download Combined JSON",
            data=combined_json_data,
            file_name="combined.json",
            mime="application/json"
        )
