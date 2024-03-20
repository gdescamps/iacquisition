import openai
import dotenv
import os
import base64
from mimetypes import guess_type
from langchain.output_parsers import ResponseSchema, StructuredOutputParser


def use_case_generation(text):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    system_query = os.getenv("GENERATEUR_USE_CASE_SYSTEM_KNOWLEDGE")

    job_example = "Data Science"
    use_case_example = os.getenv("USE_CASE_EXAMPLE")
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


# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


def post_process_parser_gpt4vision_forjobdesc(output):
    nom_poste_schema = ResponseSchema(
        name="Nom du poste",
        description="A string containing the name of the job",
        type="String",
    )
    competence_schema = ResponseSchema(
        name="Compétences",
        description="A list of string containing some hard skills, each element of the list must be a separate hard skill",
        type="list",
    )
    mission_schema = ResponseSchema(
        name="Missions",
        description="A list of string containing the different missions of the job, each element of the list must be a separate mission",
        type="list",
    )
    aptitude_schema = ResponseSchema(
        name="Aptitudes",
        description="A list of string containing some soft skills, each element of the list must be a separate soft skill",
        type="list",
    )
    responseschema = [
        nom_poste_schema,
        mission_schema,
        competence_schema,
        aptitude_schema,
    ]
    output_parser = StructuredOutputParser.from_response_schemas(responseschema)
    return output_parser.parse(output)


def post_process_parser_gpt4vision(output):
    exp_prof_schema = ResponseSchema(
        name="Expérience Professionnelle",
        description="A list containing some dictionnaries",
        type="list",
    )
    competence_schema = ResponseSchema(
        name="Compétences Clés",
        description="A list of string containing some key skills, each element of the list must be a separate skill",
        type="list",
    )
    diplome_schema = ResponseSchema(
        name="Diplômes et Formations",
        description="A list of string containing the names of the diplomas or training obtained by the candidate",
        type="list",
    )
    responseschema = [exp_prof_schema, competence_schema, diplome_schema]
    output_parser = StructuredOutputParser.from_response_schemas(responseschema)
    return output_parser.parse(output)


def ner_task_gpt4vision_jobdesc(data_url_test):
    openai.api_key = "3760ca397f864b95829de648980acabe"
    openai.api_base = "https://teamai-openai-dev.openai.azure.com/"
    openai.api_type = "azure"
    openai.api_version = "2023-03-15-preview"

    TEST = '```json\n{\n  "Nom du poste":  "Chef de projet Analytics",\n  "Compétences": [\n    "Google Analytics",\n    "Content Square",\n    "Datastudio",\n    "Power BI",\n    "Excel"\n  ],\n  "Missions": [\n    "Structurer la donnée et la diffuser",\n      "Servir la performance des sites Chanel.com au travers d\'analyses et de recommandations adaptées",\n      "Accompagner l\'ensemble des métiers au sein de la Maison sur les projets et l\'utilisation des données analytics",\n      "Analyser les parcours clients dans le but de comprendre les tendances de navigation et d\'optimiser l\'expérience en ligne",\n      "Analyser en profondeur la performance des campagnes",\n      "Travailler en support des régions sur l\'ensemble des problématiques liées au web Analytics",\n      "Produire des insights pour les équipes",\n      "Analyser la performance des A/B tests"\n],\n  "Aptitudes":[\n    "Esprit analytique",\n    "Bon relationnel",\n     "Bonne maitrise de l\'anglais"\n]\n}\n```'
    format_french = 'Le résultat doit être un extrait de code Markdown formaté selon le schéma suivant, incluant le début "```json" et la fin "```":\n\n```json\n{\n\t"Nom du poste": string  // Une chaine de caractères qui précise l\'intitulé exact du poste.\n\t"Missions": list  // Une liste contenant des chaines de caractères, chaque élément de la liste contient une des missions attendues du poste.\n\t"Compétences": list  // Une liste contenant des chaines de caractères, chaque élément de la liste contient une seule compétence, ici on s\'intéressera plus aux noms de logiciels (Office etc...), aux langages de programmation (Python etc...)\n\t"Aptitudes": list  // Une liste contenant des chaines de caractères, chaque élément de la liste contient une seule aptitude, ici on s\'intéressera plus aux soft skills (Capacités relationnelles etc...) et aux langues vivantes (Anglais courant etc...)\n}\n```'
    system_query = "Je vais vous fournir une fiche de poste.\n\nVotre objectif est d'extraire les informations suivantes:\n\nLe 'Nom du poste', Les 'Missions', les 'Compétences' et les 'Aptitudes'.\nVoici le format attendu : {}".format(
        format_french
    )

    # system_query = "Je vais vous fournir un CV. L'objectif est d'extraire les informations pertinentes du document tout en respectant le format attendu. Le format de sortie doit être JSON. Les informations à extraire sont les suivantes : Expérience professionnelle, Compétences clés et Diplômes et/ou formations. Dans la mesure du possible, pour les expériences professionnelles il sera nécessaire d'extraire chaque expérience passée au format JSON suivant {'Job Title' : '','Company' : '','Duration' : '','Location' : '','Contract' : '','Responsabilités' : ['','']} en fournissant, si possible, le titre du poste, le nom de l'entreprise, la durée du poste, la localisation du poste, le type de poste parmi CDI (pour un poste permanent classique), Alternance (Pour une alternance), Stage (pour un stage), et THESE (pour une thèse), ainsi que les différentes tâches et responsabilités associées à la position. Pour les compétences clés, il faudra retourner une liste où chaque élément sera une compétence. De même pour le champ 'Diplômes et/ou formations' qui devra être une liste contenant les noms des diplômes et/ou formations. N'oubliez pas qu'il vous suffit d'extraire les informations comme expliqué, ne modifiez pas le texte dans le document, toutes les informations que vous extrayez doivent être écrites de la même manière dans le document."
    data_url_fewshot = local_image_to_data_url(
        image_path="/home/pablo/data/iacquisition/projet/image_jobdesc_fewshot.jpg"
    )
    response = openai.ChatCompletion.create(
        engine="gpt-4-vision-preview",
        temperature=0,
        messages=[
            {"role": "system", "content": system_query},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Veuillez extraire toutes les informations contenues dans ce document comme expliqué précédemment, et n'oubliez pas de retourner un objet python de type dictionnaire ou JSON.",
                    },
                    {"type": "image_url", "image_url": {"url": data_url_fewshot}},
                ],
            },
            {
                "role": "assistant",
                "content": "{}".format(TEST),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Veuillez réaliser la même tâche que précédemment sur ce nouveau document.",
                    },
                    {"type": "image_url", "image_url": {"url": data_url_test}},
                ],
            },
        ],
        max_tokens=4000,
    )
    return post_process_parser_gpt4vision_forjobdesc(
        response.choices[0].message.content
    )


def ner_task_gpt4vision(data_url_test):
    openai.api_key = "3760ca397f864b95829de648980acabe"
    openai.api_base = "https://teamai-openai-dev.openai.azure.com/"
    openai.api_type = "azure"
    openai.api_version = "2023-03-15-preview"

    TEST = '```json\n{\n  "Expérience Professionnelle": [\n    {\n      "Job Title": "Ingénieur documentaliste, pilote d\'activité",\n      "Company": "Eowin (prestataire chez Ariane group)",\n      "Duration": "2021",\n      "Location": "Les Mureaux",\n      "Contract": "CDI",\n      "Responsabilités": [\n        "Élaboration et rédaction de rapports d\'activités mensuelles et comité de pilotage trimestriel",\n        "Statistiques et analyses, mise à jour de procédures internes.",\n        "Reporting quotidien avec la référente AGS"\n      ]\n    },\n    {\n      "Job Title": "Consultante indépendante",\n      "Company": "Saint Germain en Laye",\n      "Duration": "2011-2020",\n      "Location": "",\n      "Contract": "CDI",\n      "Responsabilités": [\n        "Responsable liaison du collège Hauts-Grillets - lycée international et membre du comité de direction de la section américaine. Expérience professionnelle en milieu multiculturel.",\n        "Pilotage, gestion, organisation et suivi de projets événementiels, (jusqu\'à 2000 invités).",\n        "Planification, encadrement, collaboration et coordination d\'équipes opérationnelles internationales (jusqu\'à 20 personnes).",\n        "Volontariat pour la section américaine du lycée international.",\n        "Professeur d\'anglais (cours particuliers et groupes).",\n        "Photographe de mariage."\n      ]\n    },\n    {\n      "Job Title": "Chef de projet merchandising international",\n      "Company": "ESTEE LAUDER",\n      "Duration": "1999-2010",\n      "Location": "Paris",\n      "Contract": "CDI",\n      "Responsabilités": [\n        "Pilotage et coordination de projets d\'envergure internationale, dans le respect de la qualité, des délais, des priorités des budgets. Interface et communication avec l\'ensemble des filiales internationales du groupe, la direction marketing, le développement production et les fournisseurs.",\n        "Suivi et pilotage opérationnel du développement merchandising de la conception à l\'expédition.",\n        "Analyse des besoins, étude de faisabilité technique et économique des projets. Lancement, suivi de planning opérationnel de développement et de production. Gestion et lancement des ordres de fabrications. Gestion des stocks. Elaboration et envoi des offres de merchandising internationales. Analyse, reporting, et statistiques.",\n        "Création, pilotage et gestion de catalogues et de photothèques. Développement de documentations (Illustrator, Quark Xpress).",\n        "Responsable de la mise en place de la nouvelle identité visuelle des linéaires du show room."\n      ]\n    },\n    {\n      "Job Title": "Coordinatrice zones Asie-USA",\n      "Company": "THOMSON MULTIMEDIA",\n      "Duration": "1997-1998",\n      "Location": "Boulogne Billancourt",\n      "Contract": "CDI",\n      "Responsabilités": [\n        "Interface filiales internationales/sites de production, gestion des stocks et des crédits documentaires à l\'international, suivi de dossiers, Gestion des tableaux de bord. Mise en place de statistiques."\n      ]\n    }\n  ],\n  "Compétences Clés": [\n    "Proactive",\n    "Dynamique",\n    "Organisée",\n    "Rigoureuse",\n    "Sens du détail",\n    "Fiable",\n    "Curieuse",\n    "Autonome",\n    "Force de proposition",\n    "Preuve d\'initiative",\n    "Agile",\n    "Excellent sens relationnel",\n    "Esprit d\'équipe"\n  ],\n  "Diplômes et Formations": [\n    "Cambridge English Proficiency",\n      "Certification Google : Les fondamentaux du marketing en ligne",\n      "Cursus \'International Business\' ESCP Business school. Groupe ESSEC",\n      "San Jose State University, Californie - États-Unis"]\n}\n```'
    format_french = 'Le résultat doit être un extrait de code Markdown formaté selon le schéma suivant, incluant le début "```json" et la fin "```":\n\n```json\n{\n\t"Expérience Professionnelle": list  // Une liste contenant plusieurs dictionnaires ou chaque dictionnaire résume une expérience passée spécifique et prend cette forme {"Job Title" : "","Company" : "","Duration" : "","Location" : "","Contract" : "","Responsabilités" : ["",""]}, Le champ "Job Title" précise le nom du poste, Le champ "Company" précise le nom de la société, Le champ "Duration" précise la durée passée sur le poste, Le champ "Contract" précise le type de contrat parmi (CDI,Alternance,Thèse,Stage), Le champ "Responsabilités" précise les différentes missions réalisées sur le poste.\n\t"Compétences Clés": list  // Une liste contenant des chaines de caractères, chaque élément de la liste contient une seule compétence\n\t"Diplômes et Formations": list  // Une liste contenant les noms des diplômes et/ou des formations obtenus par le candidat\n}\n```'
    system_query = "Je vais vous fournir un CV.\n\nVotre objectif est d'extraire les informations suivantes:\n\nLes 'Expérience Professionnelle', les 'Compétences Clés' et les 'Diplômes et Formations'.\nVoici le format attendu : {}".format(
        format_french
    )

    # system_query = "Je vais vous fournir un CV. L'objectif est d'extraire les informations pertinentes du document tout en respectant le format attendu. Le format de sortie doit être JSON. Les informations à extraire sont les suivantes : Expérience professionnelle, Compétences clés et Diplômes et/ou formations. Dans la mesure du possible, pour les expériences professionnelles il sera nécessaire d'extraire chaque expérience passée au format JSON suivant {'Job Title' : '','Company' : '','Duration' : '','Location' : '','Contract' : '','Responsabilités' : ['','']} en fournissant, si possible, le titre du poste, le nom de l'entreprise, la durée du poste, la localisation du poste, le type de poste parmi CDI (pour un poste permanent classique), Alternance (Pour une alternance), Stage (pour un stage), et THESE (pour une thèse), ainsi que les différentes tâches et responsabilités associées à la position. Pour les compétences clés, il faudra retourner une liste où chaque élément sera une compétence. De même pour le champ 'Diplômes et/ou formations' qui devra être une liste contenant les noms des diplômes et/ou formations. N'oubliez pas qu'il vous suffit d'extraire les informations comme expliqué, ne modifiez pas le texte dans le document, toutes les informations que vous extrayez doivent être écrites de la même manière dans le document."
    data_url_fewshot = local_image_to_data_url(
        image_path="/home/pablo/data/iacquisition/projet/image_cv_fewshot.jpg"
    )
    response = openai.ChatCompletion.create(
        engine="gpt-4-vision-preview",
        temperature=0,
        messages=[
            {"role": "system", "content": system_query},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Veuillez extraire toutes les informations contenues dans ce document comme expliqué précédemment, et n'oubliez pas de retourner un objet python de type dictionnaire ou JSON.",
                    },
                    {"type": "image_url", "image_url": {"url": data_url_fewshot}},
                ],
            },
            {
                "role": "assistant",
                "content": "{}".format(TEST),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Veuillez réaliser la même tâche que précédemment sur ce nouveau document.",
                    },
                    {"type": "image_url", "image_url": {"url": data_url_test}},
                ],
            },
        ],
        max_tokens=4000,
    )
    return post_process_parser_gpt4vision(response.choices[0].message.content)


def ner_task(text):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    system_query = os.getenv("SYSTEM_KNOWLEDGE2")

    ner_task_text_example = os.getenv("USER_TEXT_EXAMPLE")
    ner_task_response_example = os.getenv("ASSISTANT_RESPONSE_EXAMPLE")
    response = openai.ChatCompletion.create(
        engine="iacquisition-RH",
        temperature=0,
        messages=[
            {"role": "system", "content": system_query},
            {
                "role": "user",
                "content": "Here is the text you need to perform the task explained above :{}".format(
                    ner_task_text_example
                ),
            },
            {
                "role": "assistant",
                "content": "{}".format(ner_task_response_example),
            },
            {
                "role": "user",
                "content": "Here is the new text you need to perform the task explained above :{}".format(
                    text
                ),
            },
        ],
    )
    return response.choices[0].message.content.encode("utf-8").decode("utf-8")


def ner_task_jobdesc(text):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    system_query = os.getenv("SYSTEM_KNOWLEDGE_JOB_DESC")

    ner_task_text_example = os.getenv("USER_TEXT_EXAMPLE_JOBDESC")
    ner_task_response_example = """{"Intitulé du poste":"Ingénieur DevSecOps","Missions":["Participer a la mise en place et a la maintenance des pipelines CI/CD sécurisés.","Collaborer avec les équipes de développement pour intégrer la sécurité dès les premières phases du cycle de développement.","Effectuer des analyses de sécurité régulières et proposer des améliorations pour renforcer la posture de sécurité.","Automatiser les processus de sécurité et veiller a l'efficacité des outils de sécurité déployés.","Participer a la veille technologique dans le domaine de la sécurité informatique et du DevSecOps."],"Profil":["Etudiant(e) en informatique, sécurité informatique, ou domaine connexe.","Connaissances solides en développement logiciel et en déploiement d'applications.","Compréhension approfondie des principes de sécurité informatique.","Expérience avec des outils de sécurité tels que SAST, DAST, et des outils de gestion d'identité.","Maitrise des concepts DevOps et expérience pratique avec des outils comme Docker, Kubernetes, Jenkins, etc.","Capacité a travailler en équipe et a communiquer efficacement.","Passionné(e) par la sécurité informatique et le développement logiciel.","Autonome, curieux(se) et capable de s'adapter rapidement a de nouveaux environnements.","Bonne maitrise du français et de l'anglais (écrit et oral)."],"Compétences":["CI/CD","SAST","DAST","Jenkins","Kubernetes","Docker","DevOps","DevSecOps"]}"""
    response = openai.ChatCompletion.create(
        engine="iacquisition-RH",
        temperature=0,
        messages=[
            {"role": "system", "content": system_query},
            {
                "role": "user",
                "content": "Voici un premier exemple de fiche de poste sur lequel tu dois réaliser la tâche expliquée ci-dessus :{}".format(
                    ner_task_text_example
                ),
            },
            {
                "role": "assistant",
                "content": "{}".format(ner_task_response_example),
            },
            {
                "role": "user",
                "content": "Voici un nouvel exemple de fiche de poste :{}".format(text),
            },
        ],
    )
    return response.choices[0].message.content.encode("utf-8").decode("utf-8")
