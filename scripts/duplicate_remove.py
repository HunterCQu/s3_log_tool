import os
import cv2
import numpy as np
import shutil
from collections import defaultdict

def calculate_histogram(image_path):
    """
    Calculate the normalized histogram for an image.

    Args:
        image_path (str): Path to the image.

    Returns:
        np.ndarray: Flattened and normalized histogram of the image.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Could not read the image.")
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        # Normalize histogram
        cv2.normalize(hist, hist)
        return hist.flatten()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None


def compare_histograms(hist1, hist2, threshold=0.9):
    """
    Compare two histograms using correlation.

    Args:
        hist1 (np.ndarray): First histogram.
        hist2 (np.ndarray): Second histogram.
        threshold (float): Threshold for similarity (default is 0.9).

    Returns:
        bool: True if the histograms are similar, False otherwise.
    """
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return similarity >= threshold


def find_duplicate_images(folder_path, threshold=0.9, duplicates_folder="duplicates"):
    """
    Find duplicate images in a folder and move them to a specified folder.

    Args:
        folder_path (str): Path to the folder containing images.
        threshold (float): Similarity threshold for duplicates.
        duplicates_folder (str): Path to the folder where duplicates will be moved.

    Returns:
        None
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    # Ensure the duplicates folder exists
    os.makedirs(duplicates_folder, exist_ok=True)

    # Store histograms and file paths
    histograms = {}
    duplicates = defaultdict(list)

    # Walk through all files in the folder
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            hist = calculate_histogram(file_path)
            if hist is None:
                continue

            # Compare with existing histograms
            is_duplicate = False
            for existing_path, existing_hist in histograms.items():
                if compare_histograms(hist, existing_hist, threshold):
                    duplicates[existing_path].append(file_path)
                    is_duplicate = True
                    break

            if not is_duplicate:
                histograms[file_path] = hist

    # Move duplicates to the duplicates folder
    for base_image, dup_paths in duplicates.items():
        for dup in dup_paths:
            try:
                # Create a subfolder for the base image if needed
                subfolder = os.path.join(duplicates_folder, os.path.basename(base_image))
                os.makedirs(subfolder, exist_ok=True)
                # Move the duplicate image
                shutil.move(dup, os.path.join(subfolder, os.path.basename(dup)))
                print(f"Moved: {dup} -> {subfolder}")
            except Exception as e:
                print(f"Error moving {dup}: {e}")

    print(f"\nDuplicate images moved to '{duplicates_folder}'.")


def main():
    folder_path = "/home/hunter/drc_download_platfor/croped_img_out"
    duplicates_folder = "/home/hunter/drc_download_platfor/croped_img_out_d"
    threshold = 0.9
    find_duplicate_images(folder_path, threshold, duplicates_folder)


if __name__ == "__main__":
    main()
