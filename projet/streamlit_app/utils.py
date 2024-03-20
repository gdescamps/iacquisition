import streamlit as st
import matplotlib.colors as mcolors
from css import *
import base64
import tempfile
import fitz
from PIL import Image
import io
import json
import requests
import dotenv
import openai
import os
import re
from datetime import datetime
from fuzzywuzzy import fuzz


# Define a function to reset the session states
def reset_session_states():
    if "chatbot_messages" in st.session_state:
        del st.session_state["chatbot_messages"]
    if "response_data_jobdesc" in st.session_state:
        del st.session_state["response_data_jobdesc"]
    if "response_data_cv" in st.session_state:
        del st.session_state["response_data_cv"]
    if "page_num_cv" in st.session_state:
        del st.session_state["page_num_cv"]
    if "images_cv" in st.session_state:
        del st.session_state["images_cv"]
    if "page_num_jobdesc" in st.session_state:
        del st.session_state["page_num_jobdesc"]
    if "images_jobdesc" in st.session_state:
        del st.session_state["images_jobdesc"]
    if "scoring_global" in st.session_state:
        del st.session_state["scoring_global"]
    if "file_uploader_cv" in st.session_state:
        del st.session_state["file_uploader_cv"]
    if "file_uploader_jobdesc" in st.session_state:
        del st.session_state["file_uploader_jobdesc"]


def handle_document(uploaded_file, filetype):
    if filetype == "cv":
        if uploaded_file is not None:
            st.session_state["uploaded_file_cv"] = uploaded_file
        if "images_cv" not in st.session_state:
            st.session_state.images_cv = []
        if "page_num_cv" not in st.session_state:
            st.session_state.page_num_cv = 0

        if st.session_state.images_cv:
            # st.session_state["response_data_cv"] = None

            current_image = st.session_state.images_cv[st.session_state.page_num_cv]
            base64_image = pil_to_base64(current_image)

            st.markdown(
                f"""
                <div style="border: 5px solid black; border-radius: 5px; padding: 10px; text-align: center;">
                    <img src="data:image/jpeg;base64,{base64_image}" alt="Job description page" style="width: 100%; height: auto; border-radius: 5px;">
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Navigation buttons
            col11, col12 = st.columns([1, 1], gap="small")
            with col11:
                if st.button("Page précédente", key="Previous_cv"):
                    if st.session_state.page_num_cv > 0:
                        st.session_state.page_num_cv -= 1
            with col12:
                if st.button("Page suivante", key="Next_cv"):
                    if (
                        st.session_state.page_num_cv
                        < len(st.session_state.images_cv) - 1
                    ):
                        st.session_state.page_num_cv += 1

    else:
        if uploaded_file is not None:
            st.session_state["uploaded_file_jobdesc"] = uploaded_file
        if "images_jobdesc" not in st.session_state:
            st.session_state.images_jobdesc = []
        if "page_num_jobdesc" not in st.session_state:
            st.session_state.page_num_jobdesc = 0

        if st.session_state.images_jobdesc:
            # st.session_state["response_data_jobdesc"] = None

            current_image = st.session_state.images_jobdesc[
                st.session_state.page_num_jobdesc
            ]
            base64_image = pil_to_base64(current_image)

            st.markdown(
                f"""
                <div style="border: 5px solid black; border-radius: 5px; padding: 10px; text-align: center;">
                    <img src="data:image/jpeg;base64,{base64_image}" alt="Job description page" style="width: 100%; height: auto; border-radius: 5px;">
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Navigation buttons
            col11, col12 = st.columns([1, 1], gap="small")
            with col11:
                if st.button("Page précédente", key="Previous_jobdesc"):
                    if st.session_state.page_num_jobdesc > 0:
                        st.session_state.page_num_jobdesc -= 1
            with col12:
                if st.button("Page suivante", key="Next_jobdesc"):
                    if (
                        st.session_state.page_num_jobdesc
                        < len(st.session_state.images_jobdesc) - 1
                    ):
                        st.session_state.page_num_jobdesc += 1


def calculate_month_difference(start_month, start_year, end_month, end_year):

    month_to_number = {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12,
    }

    # Lowercase the dictionary keys to match the regex capture
    month_to_number = {k.lower(): v for k, v in month_to_number.items()}

    start_date = datetime(
        year=int(start_year), month=month_to_number[start_month.lower()], day=1
    )
    end_date = datetime(
        year=int(end_year), month=month_to_number[end_month.lower()], day=1
    )
    return (
        (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    )


def parse_duration(date_range_str):
    # Current date for comparison
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Regex patterns to match different formats
    year_only_pattern = r"(\d{4})"
    range_pattern = r"(\d{4})\s?-\s?(\d{4})"
    from_pattern = r"From (\d{4})"
    since_pattern = r"Since (\d{4})"
    depuis_pattern = r"Depuis (\d{4})"

    month_names_regex = r"(?:[Jj]anvier|[Ff]évrier|[Mm]ars|[Aa]vril|[Mm]ai|[Jj]uin|[Jj]uillet|[Aa]oût|[Ss]eptembre|[Oo]ctobre|[Nn]ovembre|[Dd]écembre)"
    full_pattern = r"({})\s(\d{{4}})\s?[-/]\s?({})\s(\d{{4}})".format(
        month_names_regex, month_names_regex
    )
    pattern = re.compile(full_pattern)

    # Check for "From YYYY"
    if re.match(from_pattern, date_range_str):
        start_year = int(re.search(from_pattern, date_range_str).group(1))
        duration_months = (current_year - start_year) * 12 + current_month - 1
    # Check for "Since YYYY"
    elif re.match(since_pattern, date_range_str):
        start_year = int(re.search(from_pattern, date_range_str).group(1))
        duration_months = (current_year - start_year) * 12 + current_month - 1

    # Check for "Depuis YYYY"
    elif re.match(depuis_pattern, date_range_str):
        start_year = int(re.search(from_pattern, date_range_str).group(1))
        duration_months = (current_year - start_year) * 12 + current_month - 1

    # Check for "YYYY-YYYY"

    elif re.match(range_pattern, date_range_str):
        start_year, end_year = map(
            int, re.search(range_pattern, date_range_str).groups()
        )
        duration_months = (end_year - start_year) * 12  # Assuming January to January

    # Check for single year "YYYY"
    elif re.match(year_only_pattern, date_range_str):
        # start_year = int(re.search(year_only_pattern, date_range_str).group(1))
        # duration_months = (
        #    (current_year - start_year) * 12 + current_month - 1
        # )  # Assuming start in January
        duration_months = 12

    elif pattern.search(date_range_str):
        match = pattern.search(date_range_str)
        start_month = match.group(1)
        start_year = match.group(2)
        end_month = match.group(3)
        end_year = match.group(4)
        duration_months = calculate_month_difference(
            start_month=start_month,
            start_year=start_year,
            end_month=end_month,
            end_year=end_year,
        )
    else:
        # If the format does not match any known pattern, return 0
        duration_months = 0

    return duration_months


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


@st.cache_data
def handle_file_upload_jobdesc(uploaded_file):
    st.session_state["response_data_jobdesc"] = None
    if "chatbot_messages" in st.session_state:
        del st.session_state["chatbot_messages"]

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


@st.cache_data
def handle_file_upload_cv(uploaded_file):
    st.session_state["response_data_cv"] = None
    if "chatbot_messages" in st.session_state:
        del st.session_state["chatbot_messages"]

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            temp_file_path = tmpfile.name

        with open(temp_file_path, "rb") as f:
            images = convert_pdf_to_images(f)

        st.session_state.images_cv = images
        st.session_state.page_num_cv = 0


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


def compute_matching_court_aptitudes(cv_extraction, jobdesc_extraction):
    aptitude_set_present = set()
    for aptitude_jobdesc in jobdesc_extraction["Aptitudes"]:
        for key_cv, item_cv in cv_extraction.items():
            if aptitude_jobdesc in aptitude_set_present:
                pass
            else:
                try:
                    for competence_cv in item_cv["Compétences Clés"]:
                        if aptitude_jobdesc.lower() == competence_cv.lower():
                            aptitude_set_present.add(aptitude_jobdesc)
                        elif aptitude_jobdesc.lower() in competence_cv.lower():
                            aptitude_set_present.add(aptitude_jobdesc)
                        elif competence_cv.lower() in aptitude_jobdesc.lower():
                            aptitude_set_present.add(aptitude_jobdesc)
                        else:
                            pass
                except:
                    pass

    liste_absent = [
        element
        for element in jobdesc_extraction["Aptitudes"]
        if element not in aptitude_set_present
    ]
    liste_present = list(aptitude_set_present)

    st.markdown(
        f"""
        <div class="stBox">
            <p><b>Aptitudes présentes</b></p>
                <ul>
                    {create_html_list(liste_present)}
                </ul>
        </div>
        <div class="stBox">
            <p><b>Aptitudes absentes</b></p>
                <ul>
                    {create_html_list(liste_absent)}
                </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compute_matching_court_competences(cv_extraction, jobdesc_extraction):
    skill_set_present = set()
    for competence_jobdesc in jobdesc_extraction["Compétences"]:
        for key_cv, item_cv in cv_extraction.items():
            if competence_jobdesc in skill_set_present:
                pass
            else:
                try:
                    for competence_cv in item_cv["Compétences Clés"]:
                        if competence_jobdesc.lower() == competence_cv.lower():
                            skill_set_present.add(competence_jobdesc)
                        elif competence_jobdesc.lower() in competence_cv.lower():
                            skill_set_present.add(competence_jobdesc)
                        elif competence_cv.lower() in competence_jobdesc.lower():
                            skill_set_present.add(competence_jobdesc)
                        elif (
                            fuzz.ratio(
                                competence_jobdesc.lower(), competence_cv.lower()
                            )
                            >= 60
                        ):
                            skill_set_present.add(competence_jobdesc)
                except:
                    pass

    liste_absent = [
        element
        for element in jobdesc_extraction["Compétences"]
        if element not in skill_set_present
    ]
    liste_present = list(skill_set_present)

    st.markdown(
        f"""
        <div class="stBox">
            <p><b>Compétences présentes</b></p>
                <ul>
                    {create_html_list(liste_present)}
                </ul>
        </div>
        <div class="stBox">
            <p><b>Compétences absentes</b></p>
                <ul>
                    {create_html_list(liste_absent)}
                </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def pil_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


@st.cache_data
def initialize_config_chat():
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")
    return None


@st.cache_data
def question_generation(fiche_de_poste_data):
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


@st.cache_data
def use_case_generation(text):
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


@st.cache_data
def launch_ocr_request_jobdesc(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(uploaded_file.getbuffer())
        temp_file_path = tmpfile.name

    files = {
        "pdf_file": (temp_file_path, open(temp_file_path, "rb"), "application/pdf")
    }
    headers = {"accept": "application/json"}

    response = requests.post(
        "http://127.0.0.1:8000/JobDescExtractionLLM_GPT4/",
        headers=headers,
        files=files,
    )
    return response.status_code, response.json()


def format_dict_to_html(d):
    html = """
    <style>
    .styled-table {
        border-collapse: collapse;
        margin-left: auto;
        margin-right: auto;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 200px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }
    .styled-table thead tr {
        background-color: black;
        color: white;
        text-align: left;
    }
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        text-align: center; /* Center table headers and cells content */
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }

    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }

    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid black;
    }

    /* Center the table container */
    .table-container {
        text-align: center;
    }
    </style>
    <div class="table-container">
    <table class="styled-table">
    <thead>
        <tr>
            <th>Type de contrat</th>
            <th>Expérience (en années)</th>
        </tr>
    </thead>
    <tbody>
    """

    for key, value in d.items():
        if key not in ("Filename", "Id"):
            value_ = value // 12
            html += f"<tr><td>{key}</td><td>{value_}</td></tr>"

    html += """
    </tbody>
    </table>
    """

    return html


@st.cache_data
def launch_ocr_request_cv(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(uploaded_file.getbuffer())
        temp_file_path = tmpfile.name

    files = {
        "pdf_file": (temp_file_path, open(temp_file_path, "rb"), "application/pdf")
    }
    headers = {"accept": "application/json"}

    response = requests.post(
        "http://127.0.0.1:8000/CVExtractionLLM_GPT4/",
        headers=headers,
        files=files,
    )
    return response.status_code, response.json()
