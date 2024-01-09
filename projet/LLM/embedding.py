import openai
import dotenv
import os
import json
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction


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
        deployment_id="FragAda",
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


def preprocess_document(document_path):
    resultats = {
        "Professional Experience": [],
        "Responsibilities": [],
        "Key Skills": [],
        "Diplomas and Training": [],
    }

    ## Load the document
    with open(document_path) as file:
        document_data = json.load(file)

    for page, __ in document_data.items():
        for block_id, data in __.items():
            for prof_exp in data["Professional Experience"]:
                for resps in prof_exp["Responsibilities"]:
                    resultats["Responsibilities"].append(resps)
            for skills in data["Key Skills"]:
                resultats["Key Skills"].append(skills)
            for diplomas in data["Diplomas and Training"]:
                resultats["Diplomas and Training"].append(diplomas)

    return resultats


def create_document_metadatas(document):
    metadatas = {
        "Name": None,
        "XP": None,
        "Status": None,
        "JobReq": None,
    }
    return metadatas


def embed_document(
    document_path, client_db_path, collections=["Skills", "Responsibilities"]
):
    ## Load the embedding function
    embedding_func = get_embedding_function()

    preprocessed_document = preprocess_document(document_path=document_path)
    # metadatas = create_document_metadatas(document=preprocessed_document)
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
        collection_skill.add(
            documents=preprocessed_document["Key Skills"],
            # metadatas=metadatas,
            ids=[str(i) for i in list(range(len(preprocessed_document["Key Skills"])))],
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
        collection_responsibilities.add(
            documents=preprocessed_document["Responsibilities"],
            # metadatas=metadatas,
            ids=[
                str(i)
                for i in list(range(len(preprocessed_document["Responsibilities"])))
            ],
        )
    return None


embed_document(
    document_path="data/Extraction/CV/Resume Gourdon Sebastien - 2023.json",
    client_db_path="storage/vectors",
    collections=["Skills", "Responsibilities"],
)
