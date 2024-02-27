import streamlit as st
import openai
import dotenv
import os
import requests
import base64
import re
import fitz
from PIL import Image
import io
import tempfile
import json


header_style = """
<style>
div.stButton > button:first-child {
    display: none;
}
.header {
    color: white;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: black;
    border-radius: 5px;
    margin: 10px 0;
}
div.stBox {
    border: 1px solid black;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
"""

sidebar_style = """
<style>
/* Targeting the sidebar with data-testid attribute */
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
    background-color: black;
}
/* Changing the color of all text inside the sidebar */
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child * {
    color: white;
}
/* Customizing buttons to appear with white background and black text */
[data-testid="stSidebar"] .stButton > button {
    background-color: white !important;
    color: black !important;
    border: 1px solid #eee !important;
    border-radius: 4px !important;
    padding: 8px 16px !important;
    margin: 5px 0 !important;
    width: 100%;
    display: block;
}
/* Hover effect for buttons */
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #f2f2f2 !important;
    color: black !important;
}
</style>
"""

# Custom CSS to inject
image_style = """
<style>
.image-container {
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    transition: 0.3s;
    margin-bottom: 15px;
}

.image-container:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
}

img {
    border-radius: 5px;
}
</style>
"""

sidebar_title = """
<style>
.st-emotion-cache-1l23ect p {
    display: block;
    margin-left: auto;
    margin-right: auto;
    font-size: 26px;
    text-align: center;
}
</style>
"""

st.set_page_config(layout="wide")

# Write styles to the app
st.markdown(header_style, unsafe_allow_html=True)
st.markdown(sidebar_style, unsafe_allow_html=True)
st.markdown(image_style, unsafe_allow_html=True)
st.markdown(sidebar_title, unsafe_allow_html=True)


# Function to encode image to base64
@st.cache_data
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Encode your image
image_base64 = get_image_base64(
    "/home/pablo/data/iacquisition/projet/streamlit_app/logo.jpg"
)
image_size = 300  # Change this value to the desired size

# Use HTML to center the image and control its size
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{image_base64}" width="{image_size}px" class="centered"/>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="header"> IACQUISITION  CHATBOT</div>', unsafe_allow_html=True)


# Define a function to reset the session states
def reset_session_states():
    if "messages" in st.session_state:
        del st.session_state["messages"]
    if "page5_response_data_jobdesc" in st.session_state:
        del st.session_state["page5_response_data_jobdesc"]
    if "page5_response_data_cv" in st.session_state:
        del st.session_state["page5_response_data_cv"]
    if "page_num_cv" in st.session_state:
        del st.session_state["page_num_cv"]
    if "images_cv" in st.session_state:
        del st.session_state["images_cv"]
    if "page_num_jobdesc" in st.session_state:
        del st.session_state["page_num_jobdesc"]
    if "images_jobdesc" in st.session_state:
        del st.session_state["images_jobdesc"]


def save_session_state_to_json(messages):
    # Convert the messages to JSON format
    messages_json = json.dumps(messages, ensure_ascii=False, indent=4)
    directory_output_path = "/home/pablo/data/iacquisition/projet/finetuning"
    # List all files in the directory
    files = os.listdir(directory_output_path)

    # Filter out files that match the pattern 'chat_session_X.json'
    chat_files = [
        file
        for file in files
        if file.startswith("chat_session_") and file.endswith(".json")
    ]

    # Find the highest number X in existing filenames
    max_num = 0
    for file in chat_files:
        # Extract the number from the filename
        num = int(file.split("_")[2].split(".")[0])
        if num > max_num:
            max_num = num

    # Define the new filename with the next number in the sequence
    new_filename = f"chat_session_{max_num + 1}.json"

    directory_output_path = "/home/pablo/data/iacquisition/projet/finetuning"
    if not os.path.exists(directory_output_path):
        os.makedirs(directory_output_path)
    else:
        pass

    file_path = os.path.join(directory_output_path, new_filename)
    # Write the JSON data to the new file with UTF-8 encoding
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(messages_json)

    print(f"Session state saved to {file_path}")


# Function to handle file upload and processing
def handle_file_upload_cv(uploaded_file):
    st.session_state["page5_response_data_cv"] = None
    if "messages" in st.session_state:
        del st.session_state["messages"]
    if uploaded_file is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            temp_file_path = tmpfile.name

        # Convert PDF to list of images
        with open(temp_file_path, "rb") as f:
            images = convert_pdf_to_images(f)

        # Reset session state
        st.session_state.images_cv = images
        st.session_state.page_num_cv = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request_cv(temp_file_path, filename, file_type)


# Function to handle file upload and processing
def handle_file_upload_jobdesc(uploaded_file):
    st.session_state["page5_response_data_jobdesc"] = None
    if "messages" in st.session_state:
        del st.session_state["messages"]
    if uploaded_file is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            temp_file_path = tmpfile.name

        # Convert PDF to list of images
        with open(temp_file_path, "rb") as f:
            images = convert_pdf_to_images(f)

        # Reset session state
        st.session_state.images_jobdesc = images
        st.session_state.page_num_jobdesc = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request_jobdesc(temp_file_path, filename, file_type)


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
def send_extraction_request_jobdesc(file_path, filename, file_type):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            file_content = base64_pdf
            response, res = launch_ocr_request_jobdesc(
                filename, file_content, file_type
            )

            if response == 200:
                st.session_state["page5_response_data_jobdesc"] = res
            else:
                pass
    except Exception as e:
        pass


# Function to send extraction request
def send_extraction_request_cv(file_path, filename, file_type):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            file_content = base64_pdf
            response_status_code, response = launch_ocr_request_cv(
                filename, file_content, file_type
            )

            if response_status_code == 200:
                st.session_state["page5_response_data_cv"] = response.json()
            else:
                pass
    except Exception as e:
        pass


@st.cache_data
def launch_ocr_request_cv(filename, file_content, file_type):
    files = {"file": (filename, file_content, file_type)}
    headers = {"accept": "application/json"}
    params = {"ocr": "Tesseract"}
    response = requests.post(
        "http://127.0.0.1:8000/CVExtractionLLM/",
        params=params,
        headers=headers,
        files=files,
    )
    return response.status_code, response


@st.cache_data
def launch_ocr_request_jobdesc(filename, file_content, file_type):
    files = {"file": (filename, file_content, file_type)}
    headers = {"accept": "application/json"}
    response = requests.post(
        "http://127.0.0.1:8000/TesseractOCR/",
        headers=headers,
        files=files,
    )
    res = ""
    for keys in response.json().keys():
        try:
            res += re.sub(" +", " ", " ".join(response.json()[keys]["text"]).strip())
        except:
            pass
    return response.status_code, res


@st.cache_data
def initialize_config_chat():
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")
    return None


initialize_config_chat()

col1, col2 = st.columns(2)
with col1:
    uploaded_file_jobdesc = st.file_uploader(
        "Glisser une fiche de poste",
        type="pdf",
        on_change=lambda: handle_file_upload_jobdesc(
            st.session_state["file_uploader_jobdesc"]
        ),
        key="file_uploader_jobdesc",
    )

    if "images_jobdesc" not in st.session_state:
        st.session_state.images_jobdesc = []

    if "page_num_jobdesc" not in st.session_state:
        st.session_state.page_num_jobdesc = 0

    if st.session_state.images_jobdesc:
        st.session_state["page5_response_data_jobdesc"] = None
        st.image(
            st.session_state.images_jobdesc[st.session_state.page_num_jobdesc],
            use_column_width=True,
        )

        # Navigation buttons
        col11, col12 = st.columns(2)
        with col11:
            if st.button("Previous page", key="Previous_jobdesc"):
                if st.session_state.page_num_jobdesc > 0:
                    st.session_state.page_num_jobdesc -= 1
        with col12:
            if st.button("Next page", key="Next_jobdesc"):
                if (
                    st.session_state.page_num_jobdesc
                    < len(st.session_state.images_jobdesc) - 1
                ):
                    st.session_state.page_num_jobdesc += 1

with col2:
    uploaded_file_cv = st.file_uploader(
        "Glisser un CV",
        type="pdf",
        on_change=lambda: handle_file_upload_cv(st.session_state["file_uploader_cv"]),
        key="file_uploader_cv",
    )

    if "images_cv" not in st.session_state:
        st.session_state.images_cv = []

    if "page_num_cv" not in st.session_state:
        st.session_state.page_num_cv = 0

    if st.session_state.images_cv:
        st.session_state["page5_response_data_cv"] = None
        st.image(
            st.session_state.images_cv[st.session_state.page_num_cv],
            use_column_width=True,
        )

        # Navigation buttons
        col11, col12 = st.columns(2)
        with col11:
            if st.button("Previous page", key="Previous_cv"):
                if st.session_state.page_num_cv > 0:
                    st.session_state.page_num_cv -= 1
        with col12:
            if st.button("Next page", key="Next_cv"):
                if st.session_state.page_num_cv < len(st.session_state.images_cv) - 1:
                    st.session_state.page_num_cv += 1

if uploaded_file_jobdesc is not None and uploaded_file_cv is not None:
    if (
        st.session_state.get("page5_response_data_jobdesc") is None
        and st.session_state.get("page5_response_data_cv") is None
    ):
        response_jobdesc, res_jobdesc = launch_ocr_request_jobdesc(
            filename=uploaded_file_jobdesc.name,
            file_content=uploaded_file_jobdesc,
            file_type=uploaded_file_jobdesc.type,
        )
        response_cv, res_cv = launch_ocr_request_cv(
            filename=uploaded_file_cv.name,
            file_content=uploaded_file_cv,
            file_type=uploaded_file_cv.type,
        )

        if response_jobdesc == 200:
            st.session_state["page5_response_data_jobdesc"] = res_jobdesc
            job_description = st.session_state.get("page5_response_data_jobdesc")
            # st.write('JOB DESCRIPTION')
            # st.write(st.session_state.get('page5_response_data_jobdesc'))
        if response_cv == 200:
            st.session_state["page5_response_data_cv"] = str(res_cv.json())
            cv = st.session_state.get("page5_response_data_cv")
            # st.write('CV')
            # st.write(st.session_state.get('page5_response_data_cv'))

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": os.getenv("CHATBOT_JOBDESC_CV_SYSTEM_KNOWLEDGE"),
                }
            ]
            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": "Here is the text from the job description in french:"
                    + " "
                    + job_description,
                }
            )
            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": "Here is the extracted information in a python dict-like object, from the CV in french:"
                    + " "
                    + cv,
                }
            )
            # st.write(st.session_state.get("messages",[]))
        for message in st.session_state.messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Ask about the job description:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                response = openai.ChatCompletion.create(
                    engine="iacquisition-RH",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=False,
                )

                full_response = response.choices[0].message["content"]

                message_placeholder.markdown(full_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )

                # save_session_state_to_json(st.session_state.messages)

colx, coly = st.columns(2)
with colx:
    if st.button("Reset conversation", on_click=reset_session_states):
        st.rerun()
with coly:
    if st.button("Save conversation"):
        save_session_state_to_json(st.session_state.messages)
        pass
