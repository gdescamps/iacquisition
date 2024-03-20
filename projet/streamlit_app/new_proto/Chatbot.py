import streamlit as st
import openai
import os

from streamlit_app.css import *
from streamlit_app.utils import *

st.set_page_config(layout="wide")

# Write styles to the app
st.markdown(header_style, unsafe_allow_html=True)
st.markdown(sidebar_style, unsafe_allow_html=True)
st.markdown(image_style, unsafe_allow_html=True)
st.markdown(sidebar_title, unsafe_allow_html=True)

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

    handle_document(uploaded_file=uploaded_file_jobdesc, filetype="jobdesc")

with col2:
    uploaded_file_cv = st.file_uploader(
        "Glisser un CV",
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
            filename=st.session_state.uploaded_file_jobdesc.name,
            file_content=st.session_state.uploaded_file_jobdesc,
            file_type=st.session_state.uploaded_file_jobdesc.type,
        )
        st.session_state["response_data_jobdesc"] = res_jobdesc
    else:
        pass

    if st.session_state.get("response_data_cv") is None:

        response_cv, res_cv = launch_ocr_request_cv(st.session_state.uploaded_file_cv)
        st.session_state["response_data_cv"] = res_cv

    else:
        pass

    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = [
            {
                "role": "system",
                "content": os.getenv("CHATBOT_JOBDESC_CV_SYSTEM_KNOWLEDGE"),
            }
        ]
        st.session_state.chatbot_messages.append(
            {
                "role": "system",
                "content": "Voici les informations pertinentes de la fiche de poste:"
                + " "
                + str(st.session_state["response_data_jobdesc"]),
            }
        )
        st.session_state.chatbot_messages.append(
            {
                "role": "system",
                "content": "Et voici les informations pertinentes du CV du candidat:"
                + " "
                + str(st.session_state["response_data_cv"]),
            }
        )

    for message in st.session_state.chatbot_messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask about the job description:"):
        st.session_state.chatbot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            response = openai.ChatCompletion.create(
                engine="iacquisition-RH",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chatbot_messages
                ],
                stream=False,
            )

            full_response = response.choices[0].message["content"]

            message_placeholder.markdown(full_response)
            st.session_state.chatbot_messages.append(
                {"role": "assistant", "content": full_response}
            )

colx, coly = st.columns(2)
with colx:
    if st.button("Reset conversation", on_click=reset_session_states):
        st.rerun()
with coly:
    if st.button("Save conversation"):
        save_session_state_to_json(st.session_state.chatbot_messages)
        pass
