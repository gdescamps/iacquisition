import openai
import dotenv
import os
import json
import chromadb
import pandas as pd
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import re
import datetime
import uuid
from streamlit_app.utils import *


def get_embedding_function():
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    openai_ef = OpenAIEmbeddingFunction(
        api_key=openai.api_key,
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        model_name="text-embedding-ada-002",
        deployment_id="iacquisition-embedding-RH",
    )
    return openai_ef


def make_new_collection(collection_name, client_db_path, embedding_function):
    chroma_client = remove_collection(
        collection_name=collection_name, client_db_path=client_db_path
    )
    collection = chroma_client.create_collection(
        name=collection_name, embedding_function=embedding_function
    )
    return collection


def remove_collection(collection_name, client_db_path):
    chroma_client = chromadb.PersistentClient(path=client_db_path)
    try:
        chroma_client.delete_collection(name=collection_name)
    except:
        pass
    return chroma_client


def get_collection(collection_name, client_db_path, embedding_function):
    chroma_client = chromadb.PersistentClient(path=client_db_path)

    collection = chroma_client.get_collection(
        name=collection_name, embedding_function=embedding_function
    )
    return collection


def preprocess_document(document_dict=None):

    metadatas = create_document_metadatas(document_data=document_dict)
    resultats = {
        "Responsabilités": [],
        "Diplômes et Formations": [],
        "Compétences Clés": [],
    }

    for page, __ in document_dict.items():
        try:
            for prof_exp in __["Expérience Professionnelle"]:
                for resps in prof_exp["Responsabilités"]:
                    resultats["Responsabilités"].append(resps)
        except KeyError:
            pass
        try:
            for diplome in __["Diplômes et Formations"]:
                resultats["Diplômes et Formations"].append(diplome)
        except KeyError:
            pass

        try:
            for competence in __["Compétences Clés"]:
                resultats["Compétences Clés"].append(competence)
        except KeyError:
            pass

    return resultats, metadatas


def create_document_metadatas(document_data=None):
    metadatas = {
        "Id": "",
        "Filename": "",
        "CDI": 0,
        "Stage": 0,
        "Thèse": 0,
        "Alternance": 0,
    }
    metadatas["Id"] = str(uuid.uuid4())

    for page, __ in document_data.items():
        try:
            for exp_prof in __["Expérience Professionnelle"]:
                if exp_prof["Contract"] == "CDI":
                    metadatas["CDI"] += parse_duration(exp_prof["Duration"])
                elif exp_prof["Contract"] == "Alternance":
                    metadatas["Alternance"] += parse_duration(exp_prof["Duration"])
                elif exp_prof["Contract"] == "Thèse":
                    metadatas["Thèse"] += parse_duration(exp_prof["Duration"])
                elif exp_prof["Contract"] == "Stage":
                    metadatas["Stage"] += parse_duration(exp_prof["Duration"])
                else:
                    pass
        except:
            pass
    return metadatas


def embed_document_assistant(
    document_dict,
    client_db_path="/home/pablo/iacquisition/projet/storage/assistant_entretien",
    collections=["Skills", "Responsibilities"],
):
    ## Load the embedding function
    embedding_func = get_embedding_function()
    preprocessed_document, metadatas = preprocess_document(document_dict=document_dict)

    if "Skills" in collections:
        collection_skill = make_new_collection(
            collection_name="Skills",
            client_db_path=client_db_path,
            embedding_function=embedding_func,
        )
        if preprocessed_document["Compétences Clés"]:
            collection_skill.add(
                documents=preprocessed_document["Compétences Clés"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Compétences Clés"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(range(len(preprocessed_document["Compétences Clés"])))
                ],
            )

    if "Responsibilities" in collections:
        ## Embed all responsibilities in the CV
        collection_responsibilities = make_new_collection(
            collection_name="Responsibilities",
            client_db_path=client_db_path,
            embedding_function=embedding_func,
        )
        if preprocessed_document["Responsabilités"]:
            collection_responsibilities.add(
                documents=preprocessed_document["Responsabilités"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Responsabilités"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(range(len(preprocessed_document["Responsabilités"])))
                ],
            )

    if "Diplomas" in collections:
        ## Embed all diplomas in the CV
        collection_diplomas = make_new_collection(
            collection_name="Diplomas",
            client_db_path=client_db_path,
            embedding_function=embedding_func,
        )
        if preprocessed_document["Diplômes et Formations"]:
            collection_diplomas.add(
                documents=preprocessed_document["Diplômes et Formations"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Diplômes et Formations"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(
                        range(len(preprocessed_document["Diplômes et Formations"]))
                    )
                ],
            )
    return None


def split_question_generated(text):
    pattern = r"(Question\s*\d+\s*:)|(Réponse attendue\s*\d+\s*:)"
    sections = re.split(pattern, text, flags=re.MULTILINE)
    sections = [section for section in sections if section and not section.isspace()]

    qa_dict = {}
    current_key = None
    for section in sections:
        if re.match(pattern, section):
            current_key = re.sub(r"\s+", " ", section).strip() + " "
        else:
            if current_key:
                qa_dict[current_key] = section.strip()

    return qa_dict


def split_usecase_generated(text):
    pattern = r"(Contexte\s*:)|(Question\s*\d+\s*:)"
    sections = re.split(pattern, text, flags=re.MULTILINE)
    sections = [section for section in sections if section and not section.isspace()]

    qa_dict = {}
    current_key = None
    for section in sections:
        if re.match(pattern, section):
            current_key = re.sub(r"\s+", " ", section).strip() + " "
        else:
            if current_key:
                qa_dict[current_key] = section.strip()

    return qa_dict


def compute_matching_long():
    embedding_function = get_embedding_function()
    collection_resp = get_collection(
        "Responsibilities",
        client_db_path="/home/pablo/data/iacquisition/projet/storage/assistant_entretien",
        embedding_function=embedding_function,
    )
    # collection_skill = get_collection(
    #    "Skills",
    #    client_db_path="/home/pablo/data/iacquisition/projet/storage/assistant_entretien",
    #    embedding_function=embedding_function,
    # )
    final_df = pd.DataFrame()

    # results_skill = collection_skill.query(
    #    query_texts=st.session_state.get("response_data_jobdesc")["Profil"],
    #    n_results=1,
    # )

    results_resp = collection_resp.query(
        query_texts=st.session_state.get("response_data_jobdesc")["Missions"],
        n_results=1,
    )

    for i in range(len(results_resp["distances"])):
        frame = {
            "Distances": pd.Series(results_resp["distances"][i]),
            "Requêtes": pd.Series(
                [st.session_state.get("response_data_jobdesc")["Missions"][i]] * 1
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

    # for i in range(len(results_skill["distances"])):
    #    frame = {
    #        "Distances": pd.Series(results_skill["distances"][i]),
    #        "Requêtes": pd.Series(
    #            [st.session_state.get("response_data_jobdesc")["Profil"][i]] * 1
    #        ),
    #        "Documents": pd.Series(results_skill["documents"][i]),
    #        "Metadatas": pd.Series(
    #            [_["Filename"] for _ in results_skill["metadatas"][i]]
    #        ),
    #    }
    #    result = pd.DataFrame(frame)

    #    if final_df.shape[0] == 0:
    #        final_df = result
    #    else:
    #        final_df = pd.concat([final_df, result], axis=0)

    final_df["Score"] = 1 - final_df["Distances"]
    final_df = final_df[["Requêtes", "Documents", "Score"]]
    final_df.reset_index(drop=True, inplace=True)

    st.session_state["scoring_global"] = final_df.loc[:, "Score"].mean()

    final_df = final_df[final_df["Score"] >= 0.65]
    final_df["Score"] = final_df["Score"] * 100
    final_df["Score"] = final_df["Score"].astype(int)

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

    # st.markdown(
    #    f"""
    #                <div class="stBox">
    #                    <p><b>Score global:</b> {int(st.session_state.get("scoring_global")*100)}%</p>
    #                </div>
    #            """,
    #    unsafe_allow_html=True,
    # )
