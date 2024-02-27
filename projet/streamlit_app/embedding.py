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


def question_generation(fiche_de_poste_data):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    system_query = os.getenv("GENERATEUR_QUESTION_SYSTEM_KNOWLEDGE")
    fiche_de_poste_data_example = '{"Missions":["Piloter nos activités R&D de l\'équipe IA.","Encadrer une équipe existante composée de data scientists et de data engineers.","Collaborer au développement de nouveaux outils d\'IA.","Recueil de besoin auprès des équipes métiers et constitution d\'une roadmap.","Participer a la veille technologique dans le domaine de l\'IA."],"Profil":["Etudiant(e) en informatique, statistiques, ou domaine connexe.","Connaissances solides en développement logiciel et en déploiement d\'applications.","Compréhension approfondie des principes de machine learning, deep learning et MLOps.","Expérience avec des outils cloud tels que AWS ou Azure.","Maitrise des concepts MLOps et expérience pratique avec des outils comme Docker, Kubernetes, Jenkins, etc.","Capacité a travailler en équipe et a communiquer efficacement.","Passionné(e) par le machine learning et le développement logiciel de manière globale.","Autonome, curieux(se) et capable de s\'adapter rapidement a de nouveaux environnements.","Bonne maitrise du français et de l\'anglais (écrit et oral)."],"Compétences":["CI/CD","AWS","Azure","Jenkins","Kubernetes","Docker","NLP","MLOps","Machine Learning","Deep Learning"]}'
    resultats_example = """Question 1:\n\nAvez-vous déjà eu l'occasion de manager une équipe de développeurs dans votre carrière? Si oui, donnez-nous un exemple en précisant le contexte technique du projet, et également votre méthodologie.\n\nRéponse attendue 1:\n\nJ'ai eu l'occasion de piloter une équipe de 3 data scientists sur un projet de développement d'un outil de traitement de documents à l'aide de Machine Learning. J'ai tout d'abord structurer le besoin avec les parties prenantes du projet en réalisant plusieurs ateliers. Un POC a été réalisé en 2 mois en collaboration avec mon équipe grâce à une méthologie AGILE tout au long des développements. Ici le candidat répond à la question en citant des outils et des méthodes fréquemment utilisés dans le domaine de l'IA.\n\nQuestion 2:\n\nAvez-vous eu l'occasion de travailler avec Docker? Si oui, citez une expérience personnelle et expliquez le contexte.\n\nRéponse attendue 2:\n\nDocker me permet de containeuriser mes applications comme des APIs par exemple et de les déployer facilement sur une instance distante EC2 par exemple pour les rendre accessibles aux utilisateurs finaux. Ici, le candidat montre qu'il a l'habitude de travailler avec Docker en donnant la raison.\n\nQuestion 3:\n\nVous connaissez l'éco-système Azure? Pour déployer une image Docker sur Azure, Que feriez-vous?\n\nRéponse attendue 3:\n\nOui, je connais Azure. Sur Azure, il existe plusieurs solutions pour déployer une application dockerisée; par exemple on peut utiliser les services ACR pour stocker les images docker et ACI pour déployer une image sur une instance privée. Ici, le candidat nous donne une solution pertinente."""
    response = openai.ChatCompletion.create(
        engine="iacquisition-RH",
        # temperature=5,
        messages=[
            {"role": "system", "content": system_query},
            {
                "role": "user",
                "content": "Voici le contenu de la fiche de poste pour lequel tu dois imaginer 5 questions pertinentes selon la tâche définie plus haut. Pour chaque question génère également la réponse idéale attendue : {}".format(
                    fiche_de_poste_data_example
                ),
            },
            {
                "role": "assistant",
                "content": "{}".format(resultats_example),
            },
            {
                "role": "user",
                "content": "Voici encore le contenu d'une nouvelle fiche de poste pour lequel tu dois imaginer 5 questions pertinentes selon la tâche définie plus haut. Pour chaque question génère également la réponse idéale attendue : {}".format(
                    fiche_de_poste_data
                ),
            },
        ],
    )
    return response.choices[0].message.content.encode("utf-8").decode("utf-8")


def use_case_generation(text):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    system_query = os.getenv("GENERATEUR_USE_CASE_SYSTEM_KNOWLEDGE")

    job_example = "Data Science"
    use_case_example = os.getenv("USE_CASE_EXAMPLE")
    use_case_example = """Contexte:\n\nLes équipes RH souhaitent améliorer leur processus de recrutement. Pour y parvenir, nous souhaitons créer un outil basé sur l'IA qui associe les CV aux descriptions de poste. Cet outil permettrait de réactiver de manière pertinente les candidats inscrits dans la base de données.\n\nQuestion 1:\n\nComment le projet doit-il être structuré ?\n\nQuestion 2:\n\nProposer une approche pour extraire automatiquement des informations d'un CV.\n\nQuestion 3:\n\nProposer une approche pour suggérer les 10 meilleures correspondances CV/description de poste."""
    response = openai.ChatCompletion.create(
        engine="iacquisition-RH",
        temperature=0,
        messages=[
            {"role": "system", "content": system_query},
            {
                "role": "user",
                "content": "Voici le métier pour lequel tu dois imaginer un cas d'usage: {}".format(
                    job_example
                ),
            },
            {
                "role": "assistant",
                "content": "{}".format(use_case_example),
            },
            {
                "role": "user",
                "content": "Voici un nouveau métier pour lequel tu dois imaginer un cas d'usage :{}".format(
                    text
                ),
            },
        ],
    )
    return response.choices[0].message.content.encode("utf-8").decode("utf-8")


# def split_question_generated(text):
#    sections = re.split(r"(Question \d+:|Réponse attendue \d+:)", text)
#    qa_dict = {}
#    for i in range(1, len(sections), 2):
#        key = sections[i].strip()
#        value = sections[i + 1].strip()
#        qa_dict[key] = value
#    qa_dict_no_colon = {key.rstrip(":"): value for key, value in qa_dict.items()}
#    return qa_dict_no_colon


def split_question_generated(text):
    # Adjust the regular expression to allow for variable whitespace and line breaks
    # This regular expression looks for the words 'Contexte' or 'Question', followed by any number of spaces,
    # possibly some digits, then a colon, and any amount of whitespace including newlines.
    pattern = r"(Question\s*\d+\s*:)|(Réponse attendue\s*\d+\s*:)"
    sections = re.split(pattern, text, flags=re.MULTILINE)

    # Filter out None and empty strings that might be produced by re.split
    sections = [section for section in sections if section and not section.isspace()]

    qa_dict = {}
    current_key = None
    for section in sections:
        if re.match(pattern, section):
            # Normalize the key by removing newlines and extra spaces, and adding the missed colon back
            current_key = re.sub(r"\s+", " ", section).strip() + " "
        else:
            if current_key:
                qa_dict[current_key] = section.strip()

    return qa_dict


def split_usecase_generated(text):
    # Adjust the regular expression to allow for variable whitespace and line breaks
    # This regular expression looks for the words 'Contexte' or 'Question', followed by any number of spaces,
    # possibly some digits, then a colon, and any amount of whitespace including newlines.
    pattern = r"(Contexte\s*:)|(Question\s*\d+\s*:)"
    sections = re.split(pattern, text, flags=re.MULTILINE)

    # Filter out None and empty strings that might be produced by re.split
    sections = [section for section in sections if section and not section.isspace()]

    qa_dict = {}
    current_key = None
    for section in sections:
        if re.match(pattern, section):
            # Normalize the key by removing newlines and extra spaces, and adding the missed colon back
            current_key = re.sub(r"\s+", " ", section).strip() + " "
        else:
            if current_key:
                qa_dict[current_key] = section.strip()

    return qa_dict
