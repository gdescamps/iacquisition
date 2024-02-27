import streamlit as st
from st_pages import Page, Section, show_pages, add_page_title
import PyPDF2
from io import BytesIO
import base64
import requests
import os
import pandas as pd
import tempfile
import fitz
from PIL import Image
import io


def convert_pdf_path_to_image(pdf_path):
    # Read the PDF file
    pdf_document = fitz.open(pdf_path)

    # Check if the PDF has pages
    if pdf_document.page_count > 0:
        # Take the first page of the PDF
        page = pdf_document[0]

        # Convert the page to image (pix) using PyMuPDF
        pix = page.get_pixmap()

        # Convert the PyMuPDF pixmap into a Python Imaging Library (PIL) image
        image_bytes = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(image_bytes))

        # Close the PDF file
        pdf_document.close()

        return image
    else:
        return None


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
def send_extraction_request_fileupload(file_path, filename, file_type):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            file_content = base64_pdf
            response = send_extraction_request(filename, file_content, file_type)

            if response.status_code == 200:
                st.session_state["page3_response_data"] = response.json()
            else:
                pass
    except Exception as e:
        pass


# Function to handle file upload and processing
def handle_file_upload_page3(uploaded_file):
    st.session_state["page3_response_data"] = None
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
        st.session_state.images_page3 = images
        st.session_state.page_num_page3 = 0

        # Trigger extraction (make sure this is the last step after all processing is done)
        filename = uploaded_file.name
        file_type = uploaded_file.type
        send_extraction_request_fileupload(temp_file_path, filename, file_type)


@st.cache_data
def send_query_request(profil_queries, missions_queries):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    params_resp = {
        "collection_name": "Responsibilities",
        "n_resuts": "20",
        "top_n": "3",
    }
    params_skills = {
        "collection_name": "Skills",
        "n_resuts": "20",
        "top_n": "3",
    }

    response_responsibilities = requests.post(
        "http://127.0.0.1:8000/Requete_BDD/",
        params=params_resp,
        headers=headers,
        json=missions_queries,
    )
    response_skills = requests.post(
        "http://127.0.0.1:8000/Requete_BDD/",
        params=params_skills,
        headers=headers,
        json=profil_queries,
    )

    if (
        response_responsibilities.status_code == 200
        and response_responsibilities.json()
    ):
        dict_responsibilities = response_responsibilities.json()["final_dict"]
        explicability_responsibilities = response_responsibilities.json()[
            "explicability_dict"
        ]
    else:
        dict_responsibilities = None
        explicability_responsibilities = None

    if response_skills.status_code == 200 and response_skills.json():
        dict_skills = response_skills.json()["final_dict"]
        explicability_skills = response_skills.json()["explicability_dict"]
    else:
        dict_skills = None
        explicability_skills = None

    return (
        dict_responsibilities,
        explicability_responsibilities,
        dict_skills,
        explicability_skills,
    )


@st.cache_data
def send_extraction_request(filename, file_content, file_type):
    files = {"file": (filename, file_content, file_type)}
    headers = {"accept": "application/json"}
    params = {"ocr": "Tesseract"}
    response = requests.post(
        "http://127.0.0.1:8000/JobDescExtraction/",
        params=params,
        headers=headers,
        files=files,
    )
    return response


st.set_page_config(layout="wide")
st.title("Matching CV/Fiche de poste")

if "page3_mission_checked_items" not in st.session_state:
    st.session_state["page3_mission_checked_items"] = []

if "page3_profil_checked_items" not in st.session_state:
    st.session_state["page3_profil_checked_items"] = []

col1, col2 = st.columns(2)

with col1:
    uploaded_file_page3 = st.file_uploader(
        "Glisser une fiche de poste",
        type="pdf",
        on_change=lambda: handle_file_upload_page3(
            st.session_state["file_uploader_page3"]
        ),
        key="file_uploader_page3",
    )

    if "images_page3" not in st.session_state:
        st.session_state.images_page3 = []

    if "page_num_page3" not in st.session_state:
        st.session_state.page_num_page3 = 0

    if st.session_state.images_page3:
        st.session_state["page3_response_data"] = None
        st.session_state["page3_profil_checked_items"] = []
        st.session_state["page3_mission_checked_items"] = []

        st.image(
            st.session_state.images_page3[st.session_state.page_num_page3],
            use_column_width=True,
        )

        # Navigation buttons
        col11, col12 = st.columns(2)
        with col11:
            if st.button("Previous page"):
                if st.session_state.page_num_page3 > 0:
                    st.session_state.page_num_page3 -= 1
        with col12:
            if st.button("Next page"):
                if (
                    st.session_state.page_num_page3
                    < len(st.session_state.images_page3) - 1
                ):
                    st.session_state.page_num_page3 += 1

with col2:
    if (
        uploaded_file_page3 is not None
        and st.session_state.get("page3_response_data") is None
    ):
        response = send_extraction_request(
            filename=uploaded_file_page3.name,
            file_content=uploaded_file_page3,
            file_type=uploaded_file_page3.type,
        )
        if response.status_code == 200:
            st.session_state["page3_response_data"] = response.json()

    if (
        "page3_response_data" in st.session_state
        and st.session_state.get("page3_response_data") is not None
    ):
        if "Profil" in st.session_state.get("page3_response_data").keys():
            st.header("Profil")
            for item in st.session_state["page3_response_data"]["Profil"]:
                # Update session state based on checkbox
                if st.checkbox(
                    item,
                    key=item,
                    value=item
                    in st.session_state.get("page3_profil_checked_items", []),
                ):
                    st.session_state["page3_profil_checked_items"].append(item)
                elif item in st.session_state.get("page3_profil_checked_items", []):
                    st.session_state["page3_profil_checked_items"].remove(item)
        if "Mission" in st.session_state.get("page3_response_data").keys():
            st.header("Mission")
            for item in st.session_state["page3_response_data"]["Mission"]:
                # Update session state based on checkbox
                if st.checkbox(
                    item,
                    key=item + "mission",
                    value=item
                    in st.session_state.get("page3_mission_checked_items", []),
                ):
                    st.session_state["page3_mission_checked_items"].append(item)
                elif item in st.session_state.get("page3_mission_checked_items", []):
                    st.session_state["page3_mission_checked_items"].remove(item)

if st.button("Recherche"):
    (
        dict_responsibilities,
        explicability_responsibilities,
        dict_skills,
        explicability_skills,
    ) = send_query_request(
        profil_queries=st.session_state["page3_profil_checked_items"],
        missions_queries=st.session_state["page3_mission_checked_items"],
    )

    st.session_state["page3_dict_responsibilities"] = dict_responsibilities
    st.session_state["page3_explicability_responsibilities"] = (
        explicability_responsibilities
    )
    st.session_state["page3_dict_skills"] = dict_skills
    st.session_state["page3_explicability_skills"] = explicability_skills

    if st.session_state.get("page3_dict_responsibilities") is not None:
        st.header("Matching selon mission")
        tab1, tab2, tab3 = st.tabs(
            list(st.session_state.get("page3_dict_responsibilities").keys())
        )
        with tab1:
            col11, col12 = st.columns(2)
            with col11:
                st.header(
                    list(st.session_state.get("page3_dict_responsibilities").keys())[0]
                )
                pdf_file_path = os.path.join(
                    "/home/pablo/data/iacquisition/projet/data/CV",
                    list(st.session_state.get("page3_dict_responsibilities").keys())[0]
                    + ".pdf",
                )
                image = convert_pdf_path_to_image(pdf_file_path)
                if image:
                    st.image(image, use_column_width=True)
            with col12:
                st.dataframe(
                    pd.DataFrame(
                        st.session_state.get("page3_explicability_responsibilities")[
                            list(
                                st.session_state.get(
                                    "page3_dict_responsibilities"
                                ).keys()
                            )[0]
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
        with tab2:
            col21, col22 = st.columns(2)
            with col21:
                st.header(
                    list(st.session_state.get("page3_dict_responsibilities").keys())[1]
                )
                pdf_file_path = os.path.join(
                    "/home/pablo/data/iacquisition/projet/data/CV",
                    list(st.session_state.get("page3_dict_responsibilities").keys())[1]
                    + ".pdf",
                )
                image = convert_pdf_path_to_image(pdf_file_path)
                if image:
                    st.image(image, use_column_width=True)
            with col22:
                st.dataframe(
                    pd.DataFrame(
                        st.session_state.get("page3_explicability_responsibilities")[
                            list(
                                st.session_state.get(
                                    "page3_dict_responsibilities"
                                ).keys()
                            )[1]
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
        with tab3:
            col31, col312 = st.columns(2)
            with col31:
                st.header(
                    list(st.session_state.get("page3_dict_responsibilities").keys())[2]
                )
                pdf_file_path = os.path.join(
                    "/home/pablo/data/iacquisition/projet/data/CV",
                    list(st.session_state.get("page3_dict_responsibilities").keys())[2]
                    + ".pdf",
                )
                image = convert_pdf_path_to_image(pdf_file_path)
                if image:
                    st.image(image, use_column_width=True)
            with col312:
                st.dataframe(
                    pd.DataFrame(
                        st.session_state.get("page3_explicability_responsibilities")[
                            list(
                                st.session_state.get(
                                    "page3_dict_responsibilities"
                                ).keys()
                            )[2]
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

    if st.session_state.get("page3_dict_skills") is not None:
        st.header("Matching selon profil")
        tab1, tab2, tab3 = st.tabs(
            list(st.session_state.get("page3_dict_skills").keys())
        )
        with tab1:
            col11, col12 = st.columns(2)
            with col11:
                st.header(list(st.session_state.get("page3_dict_skills").keys())[0])
                pdf_file_path = os.path.join(
                    "/home/pablo/data/iacquisition/projet/data/CV",
                    list(st.session_state.get("page3_dict_skills").keys())[0] + ".pdf",
                )
                image = convert_pdf_path_to_image(pdf_file_path)
                if image:
                    st.image(image, use_column_width=True)
            with col12:
                st.dataframe(
                    pd.DataFrame(
                        st.session_state.get("page3_explicability_skills")[
                            list(st.session_state.get("page3_dict_skills").keys())[0]
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
        with tab2:
            col21, col22 = st.columns(2)
            with col21:
                st.header(list(st.session_state.get("page3_dict_skills").keys())[1])
                pdf_file_path = os.path.join(
                    "/home/pablo/data/iacquisition/projet/data/CV",
                    list(st.session_state.get("page3_dict_skills").keys())[1] + ".pdf",
                )
                image = convert_pdf_path_to_image(pdf_file_path)
                if image:
                    st.image(image, use_column_width=True)
            with col22:
                st.dataframe(
                    pd.DataFrame(
                        st.session_state.get("page3_explicability_skills")[
                            list(st.session_state.get("page3_dict_skills").keys())[1]
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
        with tab3:
            col31, col312 = st.columns(2)
            with col31:
                st.header(list(st.session_state.get("page3_dict_skills").keys())[2])
                pdf_file_path = os.path.join(
                    "/home/pablo/data/iacquisition/projet/data/CV",
                    list(st.session_state.get("page3_dict_skills").keys())[2] + ".pdf",
                )
                image = convert_pdf_path_to_image(pdf_file_path)
                if image:
                    st.image(image, use_column_width=True)
            with col312:
                st.dataframe(
                    pd.DataFrame(
                        st.session_state.get("page3_explicability_skills")[
                            list(st.session_state.get("page3_dict_skills").keys())[2]
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
