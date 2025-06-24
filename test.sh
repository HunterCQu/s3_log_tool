
# Ignore_version/with_date
for version in $(aws s3 ls s3://mower-us-log/device/24217HGE001A0019/ | awk '{print $2}' | sed 's#/##'); do
    aws s3 cp s3://mower-us-log/device/24217HGE001A0019/$version/20241219/drc_log/ ./hunter_test/$version --recursive
done

# Ignore_date/with_version
version="1.1.55"
sn="24217HGE001A0019"
base_path="s3://mower-us-log/device/${sn}/${version}/"

# List date folders
aws s3 ls "${base_path}" | awk '/PRE/ {print $2}' | while read -r date_folder; do
    drc_path="${base_path}${date_folder}drc_log/"
    # Try to copy drc_log if it exists
    aws s3 cp "${drc_path}" "./hunter_test/${version}/${date_folder}drc_log/" --recursive 2>/dev/null
done

# Ignore_date/Ignore_version
sn="24217HGE001A0019"
base_path="s3://mower-us-log/device/${sn}/"

# List all objects under the SN prefix
aws s3 ls --recursive "${base_path}" | awk '{print $4}' | grep '/drc_log/' | while read -r full_path; do
    # Extract the folder path leading to drc_log/
    drc_folder=$(echo "$full_path" | grep -o '.*drc_log/')
    
    # Skip duplicates (just copy once per folder)
    if [[ -n "$drc_folder" && ! " ${copied_folders[*]} " =~ " ${drc_folder} " ]]; then
        echo "Copying s3://mower-us-log/${drc_folder} ..."
        aws s3 cp "s3://mower-us-log/${drc_folder}" "./hunter_test/${drc_folder#device/}" --recursive
        copied_folders+=("$drc_folder")
    fi
done
