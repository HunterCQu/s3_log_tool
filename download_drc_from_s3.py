import os
import patoolib

def extract_file(file_path, extract_to):
    """
    Extracts an archive file to the specified directory.

    :param file_path: Path to the archive file
    :param extract_to: Directory to extract the files to
    """
    os.makedirs(extract_to, exist_ok=True)
    try:
        patoolib.extract_archive(str(file_path), outdir=str(extract_to))
        print(f"[OK] Extracted: {file_path} -> {extract_to}")
    except patoolib.util.PatoolError as e:
        print(f"[ERR] Failed to extract {file_path}: {e}")

def extract_all_archives(input_folder, output_folder):
    """
    Extracts all archive files in the input folder into the output folder,
    maintaining the same base name structure.

    :param input_folder: Folder containing archive files
    :param output_folder: Destination folder for extracted files
    """
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isfile(file_path):
            base_name, ext = os.path.splitext(filename)
            extract_to = os.path.join(output_folder, base_name)
            extract_file(file_path, extract_to)

# === Example Usage ===
if __name__ == "__main__":
    input_dir = "/home/hunter/drc_tmp/mower-us-log/24507HGD00070014/1.8.5/20250511/drc_log"     # Replace with folder containing .zip, .rar, etc.
    output_dir = "/home/hunter/drc_2"     # Replace with folder to extract into

    extract_all_archives(input_dir, output_dir)
