import openai
import dotenv
import os


def ner_task(text):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")

    system_query = os.getenv("SYSTEM_KNOWLEDGE")

    ner_task_text_example = os.getenv("USER_TEXT_EXAMPLE")
    ner_task_response_example = os.getenv("ASSISTANT_RESPONSE_EXAMPLE")
    response = openai.ChatCompletion.create(
        engine="test",
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
    # liste_response.append(response.choices[0].message.content.strip())
    return (
        response.choices[0]
        .message.content.encode("utf-8")
        .decode("utf-8")
        .replace("'", '"')
    )
