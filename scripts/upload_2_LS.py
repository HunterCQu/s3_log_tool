import os
import requests

# === Configuration ===
LABEL_STUDIO_URL = 'http://localhost:8080'  # Change to your Label Studio URL
API_KEY = '186283859eab189a684e3bab6548ae649522f64d'               # Get this from your Label Studio account
PROJECT_ID = 272                  # Change to your project ID
LOCAL_DATA_DIR = '/home/hunter/drc_download_platfor/croped_img_out'      # Directory with local files to upload

# === Headers ===
HEADERS = {
    'Authorization': f'Token {API_KEY}'
}

# === Upload local files ===
def upload_local_files_to_label_studio():
    files = [f for f in os.listdir(LOCAL_DATA_DIR) if os.path.isfile(os.path.join(LOCAL_DATA_DIR, f))]
    
    for file_name in files:
        file_path = os.path.join(LOCAL_DATA_DIR, file_name)

        print(f"Uploading: {file_name}")
        with open(file_path, 'rb') as f:
            response = requests.post(
                f'{LABEL_STUDIO_URL}/api/projects/{PROJECT_ID}/import',
                headers=HEADERS,
                files={
                    'file': (file_name, f)
                }
            )
        if response.status_code == 201:
            print(f"✅ Uploaded: {file_name}")
        else:
            print(f"❌ Failed to upload {file_name}: {response.status_code} - {response.text}")

if __name__ == '__main__':
    upload_local_files_to_label_studio()
