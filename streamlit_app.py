import os
from PIL import Image
from difflib import SequenceMatcher
import streamlit as st
import zipfile
from io import BytesIO

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_similar_groups(files, threshold=0.75):
    groups = []
    while files:
        base = files.pop(0)
        group = [base]
        similar_files = [f for f in files if similar(base.name, f.name) >= threshold]
        for f in similar_files:
            if len(group) < 4:  # Ensure group does not exceed 4 images
                group.append(f)
                files.remove(f)
        groups.append(group)
    return groups

def combine_images_and_create_zip(uploaded_files):
    groups = find_similar_groups(uploaded_files)
    total_groups = len(groups)
    progress = st.progress(0)

    output_zip = BytesIO()
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for index, group in enumerate(groups):
            if len(group) > 1:
                images = [Image.open(file).convert("RGBA") for file in group]

                total_width = sum(image.width for image in images)
                max_height = max(image.height for image in images)

                combined_image = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))

                x_offset = 0
                for image in images:
                    combined_image.paste(image, (x_offset, 0), image)
                    x_offset += image.width

                # Retain the exact name of the first image in the group
                original_name = group[0].name

                # Save the combined image to the ZIP file
                with BytesIO() as img_buffer:
                    combined_image.save(img_buffer, format="PNG")
                    img_buffer.seek(0)
                    zipf.writestr(original_name, img_buffer.read())

            progress.progress((index + 1) / total_groups)

    return output_zip

# Streamlit UI
st.title("รวมภาพ PNG")

# Allow users to upload multiple images
uploaded_files = st.file_uploader(
    "อัปโหลดหลายภาพ (PNG, JPG, JPEG, BMP, GIF)", 
    type=["png", "jpg", "jpeg", "bmp", "gif"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"อัปโหลดแล้ว {len(uploaded_files)} ภาพ")

    # Combine and create ZIP file when the button is pressed
    if st.button("เริ่มการรวมภาพ"):
        with st.spinner("กำลังประมวลผลภาพ..."):
            output_zip = combine_images_and_create_zip(uploaded_files)

        st.success("การรวมภาพเสร็จสมบูรณ์!")

        # Provide a download link
        st.download_button(
            label="ดาวน์โหลดไฟล์ ZIP",
            data=output_zip.getvalue(),
            file_name="combined_images.zip",
            mime="application/zip"
        )
