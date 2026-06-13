# testar_busca.py
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from pydantic import SecretStr
import os

load_dotenv()
raw_api = os.getenv("CHAVE_API_GOOGLE")
api_key = SecretStr(raw_api) if raw_api else None

# Criar modelo
embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    api_key=api_key
)

# Gerar embedding de uma pergunta
pergunta = "Como configurar alerta de disco?"
embedding = embedding_model.embed_query(pergunta)

print(f"Dimensões: {len(embedding)}")
print(f"Primeiros 20 números: {embedding[:20]}")
print("\nVetor completo (copie isso):")
print(embedding)
