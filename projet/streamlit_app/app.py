import streamlit as st
from langchain.prompts.prompt import PromptTemplate
import dotenv
import openai
import os
import requests
import base64
import re
import fitz
from PIL import Image
import io
import tempfile
import json
import pandas as pd
from streamlit_app.embedding import *
from st_pages import Page, Section, show_pages
from streamlit_option_menu import option_menu

from st_circular_progress import CircularProgress
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np

import matplotlib.colors as mcolors


def create_custom_colormap():
    # Define the colors
    colors = ["red", "orange", "green"]
    # Define the boundaries that correspond to the colors
    boundaries = [0, 75, 85, 100]  # Assuming the value range is 0-100
    # Create a Normalize object for these boundaries
    norm = mcolors.BoundaryNorm(boundaries, len(colors))
    # Create a ListedColormap
    cmap = mcolors.ListedColormap(colors)

    return cmap


cmap = LinearSegmentedColormap.from_list(
    "custom_green_red", ["red", "yellow", "green"], N=256
)

header_style = """
<style>
.header {
    color: white;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: black;
    border-radius: 5px;
    margin: 10px 0;
}
.header2 {
    color: white;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: grey;
    border-radius: 5px;
    margin: 10px 0;
}
.headertopscore {
    color: black;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: white;
    border-radius: 5px;
    margin: auto; /* Set margin to auto to center the button */
    width: 25%; /* Set a specific width to make the button smaller */
    display: block; /* This will allow margin: auto to work properly */
}
.headermidscore {
    color: black;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: white;
    border-radius: 5px;
    margin: auto; /* Set margin to auto to center the button */
    width: 25%; /* Set a specific width to make the button smaller */
    display: block; /* This will allow margin: auto to work properly */
}
.headerbotscore {
    color: black;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: white;
    border-radius: 5px;
    margin: auto; /* Set margin to auto to center the button */
    width: 25%; /* Set a specific width to make the button smaller */
    display: block; /* This will allow margin: auto to work properly */
}
div.stBox {
    border: 1px solid black;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
"""

business_case_style = """
<style>
    .contexte-box {
        border: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 5px;
        background-color: #f8f9fa;
    }
    .businesscase-box {
        border-left: 3px solid black;
        border-top: 1px solid #cccccc;
        border-right: 1px solid #cccccc;
        border-bottom: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .header-box {
        background-color: black;
        color: white;
        padding: 10px;
        margin-bottom: 5px;
        font-weight: bold;
    }
"""

question_section_style = """
<style>
    .question-box {
        border: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 5px;
        background-color: #f8f9fa;
    }
    .answer-box {
        border-left: 3px solid black;
        border-top: 1px solid #cccccc;
        border-right: 1px solid #cccccc;
        border-bottom: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .header-box {
        background-color: black;
        color: white;
        padding: 10px;
        margin-bottom: 5px;
        font-weight: bold;
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


def colorize_scoring_df(value):
    # Extract the percentage value from the string
    # percentage = int(value.strip("%"))
    # Apply coloring based on the percentage value
    if value > 85:
        color = "green"
    elif 75 < value <= 85:
        color = "orange"
    else:
        color = "red"
    return f"background-color: {color}"


# Function to create HTML content from the dictionary
def create_html_content_for_business_case(data_dict):
    html_content = business_case_style
    # html_content += '<div class="header-box">Questions et Réponses</div>'
    for question, answer in data_dict.items():
        html_content += f'<div class="contexte-box">{question}</div>'
        html_content += f'<div class="businesscase-box">{answer}</div>'
    return html_content


# Function to create HTML content from the dictionary
def create_html_content_for_question(data_dict):
    html_content = question_section_style
    # html_content += '<div class="header-box">Questions et Réponses</div>'
    for question, answer in data_dict.items():
        html_content += f'<div class="question-box">{question}</div>'
        html_content += f'<div class="answer-box">{answer}</div>'
    return html_content


def create_html_list(items):
    return "".join(f"<li>{item}</li>" for item in items)


st.set_page_config(layout="wide")

# Write styles to the app
st.markdown(header_style, unsafe_allow_html=True)
st.markdown(sidebar_style, unsafe_allow_html=True)
st.markdown(image_style, unsafe_allow_html=True)
st.markdown(sidebar_title, unsafe_allow_html=True)


show_pages(
    [
        Page("app.py", "ASSISTANT ENTRETIEN"),
        Page("new_proto/Chatbot.py", "CHATBOT"),
    ]
)


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

st.markdown(
    '<div class="header">IACQUISITION      ASSISTANT ENTRETIEN</div>',
    unsafe_allow_html=True,
)


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
                st.session_state["page6_response_data_jobdesc"] = res
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
                st.session_state["page6_response_data_cv"] = response.json()
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
    params = {"ocr": "Tesseract"}
    response = requests.post(
        "http://127.0.0.1:8000/JobDescExtractionLLM/",
        params=params,
        headers=headers,
        files=files,
    )
    try:
        return response.status_code, eval(response.json())
    except:
        return response.status_code, response.json()


# Function to handle file upload and processing
def handle_file_upload_jobdesc(uploaded_file):
    st.session_state["page6_response_data_jobdesc"] = None
    if "page6_messages" in st.session_state:
        del st.session_state["page6_messages"]
    if uploaded_file is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            temp_file_path = tmpfile.name

        # Convert PDF to list of images
        with open(temp_file_path, "rb") as f:
            images = convert_pdf_to_images(f)

        # Reset session state
        st.session_state.page6_images_jobdesc = images
        st.session_state.page6_page_num_jobdesc = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request_jobdesc(temp_file_path, filename, file_type)


def handle_file_upload_cv(uploaded_file):
    st.session_state["page6_response_data_cv"] = None
    if "page6_messages" in st.session_state:
        del st.session_state["page6_messages"]
    if uploaded_file is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            temp_file_path = tmpfile.name

        # Convert PDF to list of images
        with open(temp_file_path, "rb") as f:
            images = convert_pdf_to_images(f)

        # Reset session state
        st.session_state.page6_images_cv = images
        st.session_state.page6_page_num_cv = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request_cv(temp_file_path, filename, file_type)


@st.cache_data
def initialize_config_chat():
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")
    return None


def switch_mode():
    if st.session_state.get("challenge_mode") == True:
        st.session_state["challenge_mode"] = False
    else:
        st.session_state["challenge_mode"] = True


initialize_config_chat()

# st.title("Assistant Entretien")

if "preprompt_facile" not in st.session_state:
    st.session_state.preprompt_facile = []

if "preprompt_difficile" not in st.session_state:
    st.session_state.preprompt_difficile = []

if "challenge_mode" not in st.session_state:
    st.session_state.challenge_mode = False

if "checkbox" not in st.session_state:
    st.session_state.checkbox = False

if "scoring_global" not in st.session_state:
    st.session_state.scoring_global = None


# Define a function to reset the session states
def reset_session_states():
    if "page6_messages" in st.session_state:
        del st.session_state["page6_messages"]
    if "page6_response_data_jobdesc" in st.session_state:
        del st.session_state["page6_response_data_jobdesc"]
    if "page6_response_data_cv" in st.session_state:
        del st.session_state["page6_response_data_cv"]
    if "page6_page_num_cv" in st.session_state:
        del st.session_state["page6_page_num_cv"]
    if "page6_images_cv" in st.session_state:
        del st.session_state["page6_images_cv"]
    if "page6_page_num_jobdesc" in st.session_state:
        del st.session_state["page6_page_num_jobdesc"]
    if "page6_images_jobdesc" in st.session_state:
        del st.session_state["page6_images_jobdesc"]
    if "scoring_global" in st.session_state:
        del st.session_state["scoring_global"]


col1, col2 = st.columns(2)
with col1:
    uploaded_file_jobdesc = st.file_uploader(
        "Glissez une fiche de poste",
        type="pdf",
        on_change=lambda: handle_file_upload_jobdesc(
            st.session_state["file_uploader_jobdesc"]
        ),
        key="file_uploader_jobdesc",
    )

    if "page6_images_jobdesc" not in st.session_state:
        st.session_state.page6_images_jobdesc = []

    if "page6_page_num_jobdesc" not in st.session_state:
        st.session_state.page6_page_num_jobdesc = 0

    if st.session_state.page6_images_jobdesc:
        st.session_state["page6_response_data_jobdesc"] = None

        st.image(
            st.session_state.page6_images_jobdesc[
                st.session_state.page6_page_num_jobdesc
            ],
            use_column_width=True,
        )

        # Navigation buttons
        col11, col12 = st.columns(2)
        with col11:
            if st.button("Page précédente", key="Previous_jobdesc"):
                if st.session_state.page6_page_num_jobdesc > 0:
                    st.session_state.page6_page_num_jobdesc -= 1
        with col12:
            if st.button("Page suivante", key="Next_jobdesc"):
                if (
                    st.session_state.page6_page_num_jobdesc
                    < len(st.session_state.page6_images_jobdesc) - 1
                ):
                    st.session_state.page6_page_num_jobdesc += 1

with col2:
    uploaded_file_cv = st.file_uploader(
        "Glissez un CV",
        type="pdf",
        on_change=lambda: handle_file_upload_cv(st.session_state["file_uploader_cv"]),
        key="file_uploader_cv",
    )

    if "page6_images_cv" not in st.session_state:
        st.session_state.page6_images_cv = []

    if "page6_page_num_cv" not in st.session_state:
        st.session_state.page6_page_num_cv = 0

    if st.session_state.page6_images_cv:
        st.session_state["page6_response_data_cv"] = None
        st.image(
            st.session_state.page6_images_cv[st.session_state.page6_page_num_cv],
            use_column_width=True,
        )

        # Navigation buttons
        col11, col12 = st.columns(2)
        with col11:
            if st.button("Page précédente", key="Previous_cv"):
                if st.session_state.page6_page_num_cv > 0:
                    st.session_state.page6_page_num_cv -= 1
        with col12:
            if st.button("Page suivante", key="Next_cv"):
                if (
                    st.session_state.page6_page_num_cv
                    < len(st.session_state.page6_images_cv) - 1
                ):
                    st.session_state.page6_page_num_cv += 1

if uploaded_file_jobdesc is not None and uploaded_file_cv is not None:
    if (
        st.session_state.get("page6_response_data_jobdesc") is None
        and st.session_state.get("page6_response_data_cv") is None
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
            st.session_state["page6_response_data_jobdesc"] = res_jobdesc
            job_description = st.session_state.get("page6_response_data_jobdesc")
            # st.write(job_description)
        if response_cv == 200:
            st.session_state["page6_response_data_cv"] = res_cv.json()
            cv = st.session_state.get("page6_response_data_cv")
            # st.write(cv)
        if response_jobdesc == 200 and response_cv == 200:

            st.markdown(
                '<div class="header2">Compétences clés</div>',
                unsafe_allow_html=True,
            )
            ### Matching des mots clés
            skill_set_present = set()
            ### Parcourir les mots clés de la fiche de poste
            for _ in job_description["Compétences"]:
                ### Parcourir les pages du CV
                for key_cv, item_cv in cv.items():
                    ### Parcourir les blocs de la page
                    for block, item_block in item_cv.items():
                        try:
                            if _.lower() in [
                                b.lower() for b in item_block["Key Skills"]
                            ]:
                                if _.lower() not in skill_set_present:
                                    skill_set_present.add(_.lower())
                        except:
                            pass
            __ = [
                element
                for element in job_description["Compétences"]
                if element.lower() not in skill_set_present
            ]

            __2 = list(skill_set_present)
            st.markdown(
                f"""
                <div class="stBox">
                    <p><b>Compétences présentes</b></p>
                        <ul>
                            {create_html_list(__2)}
                        </ul>
                </div>
                <div class="stBox">
                    <p><b>Compétences absentes</b></p>
                        <ul>
                            {create_html_list(__)}
                        </ul>
                </div>
            """,
                unsafe_allow_html=True,
            )
            # with col4:
            #    st.markdown(
            #        '<div class="header2">Niveau de séniorité</div>',
            #        unsafe_allow_html=True,
            #    )
            #    metadatas = create_document_metadatas(
            #        document_data=cv, document_path=None
            #    )
            #    st.markdown(
            #        f"""
            #        <div class="stBox">
            #            <p><b>Poste actuel:</b> {metadatas["Status"]}</p>
            #            <p><b>Années d'expérience:</b> {metadatas["XP"]}</p>
            #        </div>
            #    """,
            #        unsafe_allow_html=True,
            #    )

            st.markdown(
                '<div class="header2">Matching mission-expérience</div>',
                unsafe_allow_html=True,
            )
            ### Matching par embedding des phrases plus longues
            embed_document_assistant(
                document_dict=st.session_state.get("page6_response_data_cv"),
                client_db_path="/home/pablo/data/iacquisition/projet/storage/assistant_entretien",
                collections=["Skills", "Responsibilities"],
            )
            try:
                embedding_function = get_embedding_function()
                collection_resp = get_collection(
                    "Responsibilities",
                    client_db_path="/home/pablo/data/iacquisition/projet/storage/assistant_entretien",
                    embedding_function=embedding_function,
                )
                collection_skill = get_collection(
                    "Skills",
                    client_db_path="/home/pablo/data/iacquisition/projet/storage/assistant_entretien",
                    embedding_function=embedding_function,
                )
                final_df = pd.DataFrame()

                results_skill = collection_skill.query(
                    query_texts=st.session_state.get("page6_response_data_jobdesc")[
                        "Profil"
                    ],
                    n_results=1,
                )

                results_resp = collection_resp.query(
                    query_texts=st.session_state.get("page6_response_data_jobdesc")[
                        "Missions"
                    ],
                    n_results=1,
                )

                for i in range(len(results_resp["distances"])):
                    frame = {
                        "Distances": pd.Series(results_resp["distances"][i]),
                        "Requêtes": pd.Series(
                            [
                                st.session_state.get("page6_response_data_jobdesc")[
                                    "Missions"
                                ][i]
                            ]
                            * 1
                        ),
                        "Documents": pd.Series(results_resp["documents"][i]),
                        "Metadatas": pd.Series(
                            [_["Filename"] for _ in results_resp["metadatas"][i]]
                        ),
                    }
                    result = pd.DataFrame(frame)

                    if final_df.shape[0] == 0:
                        final_df = result
                    else:
                        final_df = pd.concat([final_df, result], axis=0)

                for i in range(len(results_skill["distances"])):
                    frame = {
                        "Distances": pd.Series(results_skill["distances"][i]),
                        "Requêtes": pd.Series(
                            [
                                st.session_state.get("page6_response_data_jobdesc")[
                                    "Profil"
                                ][i]
                            ]
                            * 1
                        ),
                        "Documents": pd.Series(results_skill["documents"][i]),
                        "Metadatas": pd.Series(
                            [_["Filename"] for _ in results_skill["metadatas"][i]]
                        ),
                    }
                    result = pd.DataFrame(frame)

                    if final_df.shape[0] == 0:
                        final_df = result
                    else:
                        final_df = pd.concat([final_df, result], axis=0)

                final_df["Score"] = 1 - final_df["Distances"]
                final_df = final_df[["Requêtes", "Documents", "Score"]]
                final_df.reset_index(drop=True, inplace=True)

                st.session_state["scoring_global"] = final_df.loc[:, "Score"].mean()
                # st.write(st.session_state.get("scoring_global"))

                final_df = final_df[final_df["Score"] >= 0.65]
                final_df["Score"] = final_df["Score"] * 100
                final_df["Score"] = final_df["Score"].astype(int)
                # final_df["Score"] = final_df["Score"].astype(str) + "%"
                # st.dataframe(final_df)
                # styled_df = final_df.style.applymap(colorize_scoring_df)

                styled_df = final_df.style.background_gradient(
                    cmap=create_custom_colormap(),
                    subset="Score",
                    text_color_threshold=0,
                )

                st.dataframe(
                    styled_df,
                    hide_index=True,
                    column_config={
                        "Requêtes": "Mission",
                        "Documents": "Expérience",
                        "Score": "Matching (%)",
                    },
                )

                st.markdown(
                    f"""
                    <div class="stBox">
                        <p><b>Score global:</b> {int(st.session_state.get("scoring_global")*100)}%</p>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

            except:
                pass

            st.markdown(
                '<div class="header2">Idées de questions/réponses</div>',
                unsafe_allow_html=True,
            )
            if response_jobdesc == 200:
                generated_questions = question_generation(
                    fiche_de_poste_data=st.session_state.get(
                        "page6_response_data_jobdesc"
                    )
                )
                dict_generated_question = split_question_generated(generated_questions)

                st.markdown(
                    create_html_content_for_question(dict_generated_question),
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div class="header2">Idée de Business Case</div>',
                unsafe_allow_html=True,
            )
            if response_jobdesc == 200:
                use_case_generated = use_case_generation(
                    text=st.session_state.get("page6_response_data_jobdesc")[
                        "Intitulé du poste"
                    ]
                )
                dict_generated_usecase = split_usecase_generated(use_case_generated)
                st.markdown(
                    create_html_content_for_question(dict_generated_usecase),
                    unsafe_allow_html=True,
                )

if st.button("Reset page", on_click=reset_session_states):
    st.rerun()
