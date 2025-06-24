import argparse
import boto3
import os
from pathlib import PurePath
import datetime
import csv
import patoolib
from pathlib import PurePath

# Initialize the argument parser
parser = argparse.ArgumentParser(description="Download data from S3")
parser.add_argument('--date', required=True, help="Date to filter data (format: YYYY-MM-DD)")
parser.add_argument('--bucket_subfolder', required=True, help="Subfolder in the S3 bucket")
args = parser.parse_args()

# Get the user-provided date and bucket_subfolder
past_date = args.date
BUCKET_SUBFOLDER = args.bucket_subfolder

# AWS credentials (ensure these are set in your environment variables)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize a session using Amazon S3
s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

BUCKET = "mower-us-log"
LOCATION_DIR = "/home/hunter/drc_tmp"
CSV_FILE_PATH = os.path.join(LOCATION_DIR, f'download_data_{past_date}_debug.csv')

def extract_file(file_path, extract_to):
    """
    Extracts an archive file to the specified directory.

    :param file_path: Path to the archive file
    :param extract_to: Directory to extract the files to
    """
    os.makedirs(extract_to, exist_ok=True)

    try:
        patoolib.extract_archive(str(file_path), outdir=str(extract_to))
    except patoolib.util.PatoolError as e:
        print(f"Error: {e}")


def download_data_from_s3(bucket_name, prefix_name):
    client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    obj_list = client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix_name
    )

    # Check if CSV file exists to avoid writing the header multiple times
    file_exists = os.path.isfile(CSV_FILE_PATH)
    
    with open(CSV_FILE_PATH, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if not file_exists:
            csv_writer.writerow(['SN.', 'Date', 'Download_date', 'File_path', 'Software_version'])

        for obj in obj_list.get('Contents', []):
            key = obj['Key']
            last_modified = obj['LastModified'].strftime('%Y-%m-%d')
            key_parts = key.split('/')

            # Ensure the key has enough parts to avoid index out of range error
            if len(key_parts) < 4:
                continue

            # Extract date and time from the key and compare with current_date
            sn = key_parts[1]
            version = key_parts[2][:6]
            date_in_key = key_parts[3][:8]

            if last_modified in past_date:
                print(key)
                response = client.get_object(
                    Bucket=bucket_name,
                    Key=key
                )   

                if 'application/x-directory; charset' not in response['ContentType']:
                    saved_file_path = save_file(LOCATION_DIR, key, response['Body'])
                    extracted_path = os.path.dirname(saved_file_path)
                    zip_input_path = saved_file_path
                    zip_output_path = extracted_path

                    # Check if the saved file is a .zip file
                    if saved_file_path.suffix == '.zip':
                        extract_file(zip_input_path, zip_output_path)
                        key = key.rstrip('.zip')

                # Append row to CSV
                download_date = datetime.datetime.now().strftime("%Y-%m-%d")
                csv_writer.writerow([sn, date_in_key, download_date, key, version])

def save_file(location_dir_path, file_name, content):
    file_dir_path = PurePath(location_dir_path, file_name)
    dir_path = os.path.dirname(file_dir_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(file_dir_path, 'wb') as f:
        for chunk in content.iter_chunks(chunk_size=4096):
            f.write(chunk)
    return file_dir_path

def list_subfolders(bucket_name, prefix=''):
    subfolders = []
    paginator = s3.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        for content in result.get('CommonPrefixes', []):
            subfolder = content.get('Prefix')
            if subfolder and subfolder != prefix:
                subfolders.append(subfolder[len(prefix):].rstrip('/'))
    return subfolders

if __name__ == '__main__':
    # Get the subfolder names
    subfolders = list_subfolders(BUCKET, BUCKET_SUBFOLDER + '/')
    print(f"Total SN. number: {len(subfolders)}")
    for subfolder in subfolders:
        BUCKET_SUBFOLDER_SN = os.path.join(BUCKET_SUBFOLDER, subfolder)
        download_data_from_s3(BUCKET, BUCKET_SUBFOLDER_SN)
