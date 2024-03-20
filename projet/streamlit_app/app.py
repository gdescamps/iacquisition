import streamlit as st
import pandas as pd
from st_pages import Page, show_pages


from streamlit_app.embedding import *
from streamlit_app.utils import *
from streamlit_app.css import *

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
    '<div class="header">IACQUISITION ASSISTANT ENTRETIEN</div>',
    unsafe_allow_html=True,
)


initialize_config_chat()

if "uploaded_file_cv" not in st.session_state:
    st.session_state.uploaded_file_cv = None

if "uploaded_file_jobdesc" not in st.session_state:
    st.session_state.uploaded_file_jobdesc = None

if "scoring_global" not in st.session_state:
    st.session_state.scoring_global = None


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

    handle_document(uploaded_file=uploaded_file_jobdesc, filetype="jobdesc")

with col2:
    uploaded_file_cv = st.file_uploader(
        "Glissez un CV",
        type="pdf",
        on_change=lambda: handle_file_upload_cv(st.session_state["file_uploader_cv"]),
        key="file_uploader_cv",
    )

    handle_document(uploaded_file=uploaded_file_cv, filetype="cv")


if (
    st.session_state.uploaded_file_cv is not None
    and st.session_state.uploaded_file_jobdesc is not None
):
    if st.session_state.get("response_data_jobdesc") is None:

        response_jobdesc, res_jobdesc = launch_ocr_request_jobdesc(
            st.session_state.uploaded_file_jobdesc
        )

        st.session_state["response_data_jobdesc"] = res_jobdesc
    else:
        pass

    if st.session_state.get("response_data_cv") is None:

        response_cv, res_cv = launch_ocr_request_cv(st.session_state.uploaded_file_cv)

        st.session_state["response_data_cv"] = res_cv
    else:
        pass

    st.markdown(
        '<div class="header2">Compétences clés</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        try:
            compute_matching_court_competences(
                cv_extraction=st.session_state.get("response_data_cv"),
                jobdesc_extraction=st.session_state.get("response_data_jobdesc"),
            )
        except Exception as e:
            # Catch and print the error
            st.error(f"An error occurred: {e}")
    with col2:
        try:
            compute_matching_court_aptitudes(
                cv_extraction=st.session_state.get("response_data_cv"),
                jobdesc_extraction=st.session_state.get("response_data_jobdesc"),
            )
        except Exception as e:
            # Catch and print the error
            st.error(f"An error occurred: {e}")

    st.markdown(
        '<div class="header2">Niveau de séniorité</div>',
        unsafe_allow_html=True,
    )

    try:
        metadatas = create_document_metadatas(
            document_data=st.session_state.get("response_data_cv")
        )
        dict_html = format_dict_to_html(metadatas)
        st.markdown(dict_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error occurred: {e}")

    st.markdown(
        '<div class="header2">Idées de questions/réponses</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("response_data_cv") is not None:
        generated_questions = question_generation(
            fiche_de_poste_data=st.session_state.get("response_data_jobdesc")
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
    if st.session_state.get("response_data_cv") is not None:
        use_case_generated = use_case_generation(
            text=st.session_state.get("response_data_jobdesc")["Nom du poste"]
        )
        dict_generated_usecase = split_usecase_generated(use_case_generated)
        st.markdown(
            create_html_content_for_question(dict_generated_usecase),
            unsafe_allow_html=True,
        )

    # st.markdown(
    #    '<div class="header2">Mission-expérience</div>',
    #    unsafe_allow_html=True,
    # )
    with st.expander("Mission-expérience"):
        ### Matching par embedding des phrases plus longues
        if st.session_state.get("response_data_cv") is not None:
            embed_document_assistant(
                document_dict=st.session_state.get("response_data_cv"),
                client_db_path="/home/pablo/data/iacquisition/projet/storage/assistant_entretien",
                collections=["Skills", "Responsibilities"],
            )
            try:
                compute_matching_long()
            except Exception as e:
                # Catch and print the error
                st.error(f"An error occurred: {e}")

if st.button("Réinitialiser la page", on_click=reset_session_states):
    st.rerun()
