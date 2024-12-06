import os
import json
from PIL import Image
from difflib import SequenceMatcher
import streamlit as st
import zipfile
from io import BytesIO

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

def combine_images_and_save_to_zip(folder_path):
    groups = find_similar_groups(folder_path)
    total_groups = len(groups)
    progress = st.progress(0)

    output_zip = BytesIO()
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
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

                combined_image_name = f"combined_{group[0]}"
                combined_image_path = os.path.join(folder_path, combined_image_name)
                combined_image.save(combined_image_path)

                # Add the combined image to the ZIP file
                zipf.write(combined_image_path, combined_image_name)

                # Clean up the saved file
                os.remove(combined_image_path)

            progress.progress((index + 1) / total_groups)

    return output_zip

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

# Folder selection
folder_path = st.text_input("Enter the folder path containing images", value=load_last_folder())
if st.button("Save Folder Path"):
    save_last_folder(folder_path)
    st.success("Folder path saved!")

# Start processing
if st.button("Start Combining Images"):
    if folder_path and os.path.isdir(folder_path):
        with st.spinner("Processing images..."):
            output_zip = combine_images_and_save_to_zip(folder_path)

        st.success("Images combined and saved into a ZIP file!")

        # Provide a download link
        st.download_button(
            label="Download ZIP File",
            data=output_zip.getvalue(),
            file_name="combined_images.zip",
            mime="application/zip"
        )
    else:
        st.warning("Please enter a valid folder path.")
