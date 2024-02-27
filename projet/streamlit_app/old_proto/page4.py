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

st.set_page_config(layout="wide")

st.title("Chatbot Fiche de poste")


# Function to handle file upload and processing
def handle_file_upload(uploaded_file):
    st.session_state["page4_response_data"] = None
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
        st.session_state.images_page4 = images
        st.session_state.page_num_page4 = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request(temp_file_path, filename, file_type)


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


@st.cache_data
def format_job_description(job_dict):
    formatted_string = ""
    for key in job_dict:
        if key in ("Profil", "Mission"):
            formatted_string += key + ":\n"
            for item in job_dict[key]:
                formatted_string += item + "\n"
            formatted_string += "\n"
    return formatted_string.strip()


# Function to send extraction request
def send_extraction_request(file_path, filename, file_type):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            file_content = base64_pdf
            response = launch_ocr_request(filename, file_content, file_type)

            if response.status_code == 200:
                st.session_state["page4_response_data"] = response.json()
            else:
                pass
                # st.error("Failed to extract data from CV.")
    except Exception as e:
        pass
        # st.error(f"An error occurred: {e}")


@st.cache_data
def launch_ocr_request(filename, file_content, file_type):
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


# uploaded_file = st.file_uploader("Glisser une fiche de poste", type="pdf", on_change=reset_state)
uploaded_file_page4 = st.file_uploader(
    "Upload a PDF file",
    type="pdf",
    on_change=lambda: handle_file_upload(st.session_state["file_uploader"]),
    key="file_uploader",
)

if "images_page4" not in st.session_state:
    st.session_state.images_page4 = []

if "page_num_page4" not in st.session_state:
    st.session_state.page_num_page4 = 0

if st.session_state.images_page4:
    st.session_state["page4_response_data"] = None
    st.image(
        st.session_state.images_page4[st.session_state.page_num_page4],
        use_column_width=True,
    )

    # Navigation buttons
    col11, col12 = st.columns(2)
    with col11:
        if st.button("Previous page"):
            if st.session_state.page_num_page4 > 0:
                st.session_state.page_num_page4 -= 1
    with col12:
        if st.button("Next page"):
            if st.session_state.page_num_page4 < len(st.session_state.images_page4) - 1:
                st.session_state.page_num_page4 += 1

if uploaded_file_page4 is not None:
    if st.session_state.get("page4_response_data") is None:
        response, res = launch_ocr_request(
            filename=uploaded_file_page4.name,
            file_content=uploaded_file_page4,
            file_type=uploaded_file_page4.type,
        )

        if response == 200:
            st.session_state["page4_response_data"] = res
            job_description = st.session_state.get("page4_response_data")

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": os.getenv("CHATBOT_JOBDESC_SYSTEM_KNOWLEDGE"),
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


# Define a function to reset the session states
def reset_session_states():
    if "messages" in st.session_state:
        del st.session_state["messages"]
    if "page4_response_data" in st.session_state:
        del st.session_state["page4_response_data"]
    if "page_num_page4" in st.session_state:
        del st.session_state["page_num_page4"]
    if "images_page4" in st.session_state:
        del st.session_state["images_page4"]


# Place your reset button at the end of your page
if st.button("Reset All", on_click=reset_session_states):
    st.rerun()
