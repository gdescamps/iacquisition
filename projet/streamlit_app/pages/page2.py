import streamlit as st
from st_pages import Page, Section, show_pages, add_page_title
import tempfile
import base64
import requests
import os 
import fitz
import io
from PIL import Image

# Function to convert PDF file pages to images
def convert_pdf_to_images(uploaded_file):
    images = []
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            # Render page to an image (pix) - you can adjust the zoom or dpi
            zoom = 2  # Zoom factor
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            # Convert the pixmap to an image using PIL
            img = Image.open(io.BytesIO(pix.tobytes("ppm")))
            images.append(img)
    return images

# Function to send extraction request
def send_extraction_request(file_path, filename, file_type):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            file_content = base64_pdf
            response = send_extraction_jobdesc_request(filename, file_content, file_type)
            
            if response.status_code == 200:
                st.session_state['page2_response_data'] = response.json()
            else:
                pass
                #st.error("Failed to extract data from CV.")
    except Exception as e:
        pass
        #st.error(f"An error occurred: {e}")
            
# Function to handle file upload and processing
def handle_file_upload(uploaded_file):
    if uploaded_file is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            temp_file_path = tmpfile.name

        # Convert PDF to list of images
        with open(temp_file_path, "rb") as f:
            images = convert_pdf_to_images(f)
        
        # Reset session state
        st.session_state.images = images
        st.session_state.page_num = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request(temp_file_path, filename, file_type)    

@st.cache_data
def send_extraction_jobdesc_request(filename, file_content, file_type):
    files = {'file': (filename, file_content, file_type)}
    headers = {'accept': 'application/json'}
    params = {'ocr': 'Tesseract'}
    response = requests.post('http://127.0.0.1:8000/JobDescExtraction/', params=params, headers=headers, files=files)
    return response

st.set_page_config(layout="wide")

st.title('Traitement des fiches de poste')

if 'page2_mission_checked_items' not in st.session_state:
    st.session_state['page2_mission_checked_items'] = []
    
if 'page2_profil_checked_items' not in st.session_state:
    st.session_state['page2_profil_checked_items'] = []

col1, col2 = st.columns(2)

with col1:
    uploaded_file_page2 = st.file_uploader("Upload a PDF file", type="pdf",
                                 on_change=lambda: handle_file_upload(st.session_state['file_uploader']),
                                 key="file_uploader")
    if 'images' not in st.session_state:
        st.session_state.images = []

    if 'page_num' not in st.session_state:
        st.session_state.page_num = 0
        
    if st.session_state.images:
        st.session_state['page2_response_data'] = None
        st.session_state['page2_mission_checked_items'] = []
        st.session_state['page2_profil_checked_items'] = []
        st.image(st.session_state.images[st.session_state.page_num], use_column_width=True)

        # Navigation buttons
        col11, col12 = st.columns(2)
        with col11:
            if st.button('Previous page'):
                if st.session_state.page_num > 0:
                    st.session_state.page_num -= 1
        with col12:
            if st.button('Next page'):
                if st.session_state.page_num < len(st.session_state.images) - 1:
                    st.session_state.page_num += 1

with col2:
    if uploaded_file_page2 is not None and st.session_state.get('page2_response_data') is None:

        response = send_extraction_jobdesc_request(filename=uploaded_file_page2.name, file_content=uploaded_file_page2, file_type=uploaded_file_page2.type)
            
        if response.status_code == 200:
            st.session_state['page2_response_data'] = response.json()
            
    if 'page2_response_data' in st.session_state and st.session_state['page2_response_data'] is not None:
        st.header("Profil")
        for item in st.session_state['page2_response_data']["Profil"]:
            # Update session state based on checkbox
            if st.checkbox(item, key=item, value=item in st.session_state.get('page2_profil_checked_items', [])):
                st.session_state['page2_profil_checked_items'].append(item)
            elif item in st.session_state.get('page2_profil_checked_items', []):
                st.session_state['page2_profil_checked_items'].remove(item)

        st.header("Mission")
        for item in st.session_state['page2_response_data']["Mission"]:
            # Update session state based on checkbox
            if st.checkbox(item, key=item + "mission", value=item in st.session_state.get('page2_mission_checked_items', [])):
                st.session_state['page2_mission_checked_items'].append(item)
            elif item in st.session_state.get('page2_mission_checked_items', []):
                st.session_state['page2_mission_checked_items'].remove(item)