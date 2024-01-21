import openai
import dotenv
import os


def initialize_chat_client():
    dotenv.load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
    openai.api_type = os.getenv("OPENAI_API_TYPE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")
    
    client = openai.AzureOpenAI(
        azure_endpoint=openai.api_base,
        api_key=openai.api_key,
        api_version=openai.api_version
    )
    return client


  
    
    