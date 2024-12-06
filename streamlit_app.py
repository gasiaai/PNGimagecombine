import os
import json
from PIL import Image
from difflib import SequenceMatcher
import streamlit as st
import zipfile

CONFIG_FILE = "config.json"

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_similar_groups(folder_path, threshold=0.75):
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    groups = []
    while files:
        base = files.pop(0)
        group = [base]
        similar_files = [f for f in files if similar(base, f) >= threshold]
        for f in similar_files:
            if len(group) < 4:
                group.append(f)
                files.remove(f)
        groups.append(group)
    return groups

def combine_images_from_folder(folder_path):
    groups = find_similar_groups(folder_path)
    total_groups = len(groups)
    progress = st.progress(0)

    for index, group in enumerate(groups):
        if len(group) > 1:
            images = [Image.open(os.path.join(folder_path, image)).convert("RGBA") for image in group]

            total_width = sum(image.width for image in images)
            max_height = max(image.height for image in images)

            combined_image = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))

            x_offset = 0
            for image in images:
                combined_image.paste(image, (x_offset, 0), image)
                x_offset += image.width

            output_path = os.path.join(folder_path, f"combined_{group[0]}")
            combined_image.save(output_path)
            st.write(f"Combined image saved as: {output_path}")

            # Remove the other images in the group
            for image in group[1:]:
                os.remove(os.path.join(folder_path, image))

        progress.progress((index + 1) / total_groups)

    st.success("Image combination completed successfully.")

def save_last_folder(folder_path):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'last_folder': folder_path}, f)

def load_last_folder():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('last_folder', '')
    return ''

# Streamlit UI
st.title("Image Combine by Gasia")

# Folder selection using a ZIP upload workaround
uploaded_zip = st.file_uploader("Upload a ZIP file containing images", type=["zip"])
if uploaded_zip:
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        extract_folder = "uploaded_folder"
        zip_ref.extractall(extract_folder)
        st.success("ZIP file uploaded and extracted successfully.")

        # Display folder contents
        folder_path = extract_folder
        st.write(f"Extracted files in: `{folder_path}`")
        if st.button("Start"):
            combine_images_from_folder(folder_path)
