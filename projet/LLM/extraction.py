import openai
import dotenv
import os


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
