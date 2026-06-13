# Eu uso para testar a API
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()
gemini_api_google = os.getenv('CHAVE_API_GOOGLE')

quest = input('Pergunta: ')

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_google,
    temperature=0.2
)


mensagens = [HumanMessage(content=quest)]

response = llm.invoke(mensagens)
print(response.content)
