import openai
import dotenv
import os
import json
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import re
import datetime
import uuid


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


def preprocess_document(document_path=None, document_dict=None):
    if document_path:
        resultats = {
            "Professional Experience": [],
            "Responsibilities": [],
            "Key Skills": [],
            "Diplomas and Training": [],
        }

        ## Load the document
        with open(document_path) as file:
            document_data = json.load(file)

        metadatas = create_document_metadatas(
            document_data=document_data, document_path=document_path
        )
        for page, __ in document_data.items():
            for block_id, data in __.items():
                try:
                    for prof_exp in data["Professional Experience"]:
                        for resps in prof_exp["Responsibilities"]:
                            resultats["Responsibilities"].append(resps)
                except KeyError:
                    pass
                try:
                    for skills in data["Key Skills"]:
                        resultats["Key Skills"].append(skills)
                except KeyError:
                    pass
                try:
                    for diplomas in data["Diplomas and Training"]:
                        resultats["Diplomas and Training"].append(diplomas)
                except KeyError:
                    pass

    else:
        resultats = {
            "Professional Experience": [],
            "Responsibilities": [],
            "Key Skills": [],
            "Diplomas and Training": [],
        }
        metadatas = create_document_metadatas(
            document_data=document_dict, document_path=None
        )
        for page, __ in document_dict.items():
            for block_id, data in __.items():
                try:
                    for prof_exp in data["Professional Experience"]:
                        for resps in prof_exp["Responsibilities"]:
                            resultats["Responsibilities"].append(resps)
                except KeyError:
                    pass
                try:
                    for skills in data["Key Skills"]:
                        resultats["Key Skills"].append(skills)
                except KeyError:
                    pass
                try:
                    for diplomas in data["Diplomas and Training"]:
                        resultats["Diplomas and Training"].append(diplomas)
                except KeyError:
                    pass

    return resultats, metadatas


def create_document_metadatas(document_data=None, document_path=None):
    metadatas = {
        "Id": "",
        "Filename": "",
        "XP": "",
        "Status": "",
        "JobReq": "",
    }
    metadatas["Id"] = str(uuid.uuid4())

    if document_path:
        # Get the Jobreq id
        jobreq = re.search("JOBREQ[0-9]+", document_path)
        if jobreq:
            jobreq = jobreq.group(0)
            metadatas["JobReq"] = jobreq
        else:
            pass

        # Get the filename
        try:
            full_name = os.path.basename(document_path)
            file_name = os.path.splitext(full_name)
            metadatas["Filename"] = file_name[0]
        except:
            pass

    # Get the actual status
    actual_status = ""
    for page, __ in document_data.items():
        for block_id, data in __.items():
            try:
                for prof_exp in data["Professional Experience"]:
                    status_ = prof_exp["Job Title"]
                    if status_:
                        actual_status = status_
                        break
            except:
                pass
    metadatas["Status"] = actual_status
    # Get the XP
    xp_set = set()
    for page, __ in document_data.items():
        for block_id, data in __.items():
            try:
                for prof_exp in data["Professional Experience"]:
                    duration_ = prof_exp["Duration"]
                    for _ in re.findall("\d{4}", duration_):
                        if _ not in xp_set:
                            xp_set.add(_)
            except:
                pass
    if xp_set:
        today_year = int(datetime.date.today().year)
        metadatas["XP"] = today_year - int(min(xp_set))

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
        if preprocessed_document["Key Skills"]:
            collection_skill.add(
                documents=preprocessed_document["Key Skills"],
                metadatas=[
                    metadatas for _ in range(len(preprocessed_document["Key Skills"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(range(len(preprocessed_document["Key Skills"])))
                ],
            )

    if "Responsibilities" in collections:
        ## Embed all responsibilities in the CV
        collection_responsibilities = make_new_collection(
            collection_name="Responsibilities",
            client_db_path=client_db_path,
            embedding_function=embedding_func,
        )
        if preprocessed_document["Responsibilities"]:
            collection_responsibilities.add(
                documents=preprocessed_document["Responsibilities"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Responsibilities"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(range(len(preprocessed_document["Responsibilities"])))
                ],
            )

    if "Diplomas" in collections:
        ## Embed all diplomas in the CV
        collection_diplomas = make_new_collection(
            collection_name="Diplomas",
            client_db_path=client_db_path,
            embedding_function=embedding_func,
        )
        if preprocessed_document["Diplomas and Training"]:
            collection_diplomas.add(
                documents=preprocessed_document["Diplomas and Training"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Diplomas and Training"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(
                        range(len(preprocessed_document["Diplomas and Training"]))
                    )
                ],
            )
    return None


def embed_document(
    document_dict,
    document_path,
    client_db_path,
    collections=["Skills", "Responsibilities", "Diplomas"],
):
    ## Load the embedding function
    embedding_func = get_embedding_function()
    if document_path:
        preprocessed_document, metadatas = preprocess_document(
            document_path=document_path
        )
    else:
        preprocessed_document, metadatas = preprocess_document(
            document_dict=document_dict
        )

    if "Skills" in collections:
        ## Embedd all key skills in the CV
        try:
            collection_skill = get_collection(
                collection_name="Skills",
                client_db_path=client_db_path,
                embedding_function=embedding_func,
            )
        except:
            collection_skill = make_new_collection(
                collection_name="Skills",
                client_db_path=client_db_path,
                embedding_function=embedding_func,
            )
        if preprocessed_document["Key Skills"]:
            collection_skill.add(
                documents=preprocessed_document["Key Skills"],
                metadatas=[
                    metadatas for _ in range(len(preprocessed_document["Key Skills"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(range(len(preprocessed_document["Key Skills"])))
                ],
            )

    if "Responsibilities" in collections:
        ## Embed all responsibilities in the CV
        try:
            collection_responsibilities = get_collection(
                collection_name="Responsibilities",
                client_db_path=client_db_path,
                embedding_function=embedding_func,
            )
        except:
            collection_responsibilities = make_new_collection(
                collection_name="Responsibilities",
                client_db_path=client_db_path,
                embedding_function=embedding_func,
            )
        if preprocessed_document["Responsibilities"]:
            collection_responsibilities.add(
                documents=preprocessed_document["Responsibilities"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Responsibilities"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(range(len(preprocessed_document["Responsibilities"])))
                ],
            )

    if "Diplomas" in collections:
        ## Embed all diplomas in the CV
        try:
            collection_diplomas = get_collection(
                collection_name="Diplomas",
                client_db_path=client_db_path,
                embedding_function=embedding_func,
            )
        except:
            collection_diplomas = make_new_collection(
                collection_name="Diplomas",
                client_db_path=client_db_path,
                embedding_function=embedding_func,
            )
        if preprocessed_document["Diplomas and Training"]:
            collection_diplomas.add(
                documents=preprocessed_document["Diplomas and Training"],
                metadatas=[
                    metadatas
                    for _ in range(len(preprocessed_document["Diplomas and Training"]))
                ],
                ids=[
                    metadatas["Id"] + "_" + str(i)
                    for i in list(
                        range(len(preprocessed_document["Diplomas and Training"]))
                    )
                ],
            )
    return None
