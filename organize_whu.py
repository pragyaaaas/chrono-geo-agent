# organize_whu.py
import os
import shutil

# --- ⚠️ IMPORTANT: CONFIGURE THESE PATHS ---
#
# Point this to the folder containing the '2012' images from your download.
# Make sure to use forward slashes '/' even on Windows.
#
# EXAMPLE: 'D:/Downloads/Building change detection dataset_add/1. The two-period image data/2012/splited_images/test/image'
#
SOURCE_BEFORE_IMAGES_PATH = 'C:/Users/Pragya Srivastava/Downloads/Building change detection dataset_add/Building change detection dataset_add/1. The two-period image data/2012/splited_images/train/image'

#
# Point this to the folder containing the '2016' images from your download.
#
# EXAMPLE: 'D:/Downloads/Building change detection dataset_add/1. The two-period image data/2016/splited_images/test/image'
#
SOURCE_AFTER_IMAGES_PATH = 'C:/Users/Pragya Srivastava/Downloads/Building change detection dataset_add/Building change detection dataset_add/1. The two-period image data/2016/splited_images/train/image'

#
# This is where the script will create the new, organized 'test' folder
# inside your project's datasets directory. You shouldn't need to change this.
#
TARGET_BASE_PATH = './datasets/Building change detection dataset_add/test1'
# ---------------------------------------------------


def organize_files():
    """
    Automatically creates image_A and image_B folders and copies the
    WHU dataset images into the correct structure for our project.
    """
    print("--- 📂 Starting File Organization Script ---")

    # 1. Define the target directories
    target_a_dir = os.path.join(TARGET_BASE_PATH, 'image_A')
    target_b_dir = os.path.join(TARGET_BASE_PATH, 'image_B')

    # 2. Check if the source paths have been updated
    if 'REPLACE_WITH' in SOURCE_BEFORE_IMAGES_PATH or 'REPLACE_WITH' in SOURCE_AFTER_IMAGES_PATH:
        print("\n❌ ERROR: Please update the SOURCE_BEFORE_IMAGES_PATH and SOURCE_AFTER_IMAGES_PATH")
        print("           variables at the top of the script before running.")
        return

    if not os.path.isdir(SOURCE_BEFORE_IMAGES_PATH) or not os.path.isdir(SOURCE_AFTER_IMAGES_PATH):
        print(f"\n❌ ERROR: One of the source paths is invalid. Please double-check them.")
        print(f"       - Path 1: '{SOURCE_BEFORE_IMAGES_PATH}'")
        print(f"       - Path 2: '{SOURCE_AFTER_IMAGES_PATH}'")
        return

    # 3. Create the new directories
    print(f"Creating new directory: {target_a_dir}")
    os.makedirs(target_a_dir, exist_ok=True)
    
    print(f"Creating new directory: {target_b_dir}")
    os.makedirs(target_b_dir, exist_ok=True)

    # 4. Copy 'before' images to image_A
    print(f"\nCopying files from '{SOURCE_BEFORE_IMAGES_PATH}' to '{target_a_dir}'...")
    before_files = os.listdir(SOURCE_BEFORE_IMAGES_PATH)
    for filename in before_files:
        shutil.copy2(os.path.join(SOURCE_BEFORE_IMAGES_PATH, filename), target_a_dir)
    print(f"Copied {len(before_files)} files to image_A.")

    # 5. Copy 'after' images to image_B
    print(f"\nCopying files from '{SOURCE_AFTER_IMAGES_PATH}' to '{target_b_dir}'...")
    after_files = os.listdir(SOURCE_AFTER_IMAGES_PATH)
    for filename in after_files:
        shutil.copy2(os.path.join(SOURCE_AFTER_IMAGES_PATH, filename), target_b_dir)
    print(f"Copied {len(after_files)} files to image_B.")

    print("\n--- ✅ Success! Your dataset is now correctly organized. ---")
    print("You can now run the 'ingest_whu.py' script.")


if __name__ == "__main__":
    organize_files()