# rag_core.py
"""
Núcleo do RAG: busca vetorial direta na tabela `documentos` (pgvector) + Gemini.

Correção principal: antes, a recuperação usava o PGVector do LangChain
(collection_name='documentos'), que lê das tabelas próprias do LangChain
(langchain_pg_collection / langchain_pg_embedding) — e NÃO da tabela
`documentos` onde a ingestão grava. Agora a busca é feita por SQL direto
na mesma tabela usada pela ingestão, com o MESMO modelo de embeddings.

Configuração via variáveis de ambiente (.env local ou App Settings no Azure):
  CHAVE_API_GOOGLE  -> chave da API Gemini (obrigatória)
  DATABASE_URL      -> URL completa do Postgres (tem prioridade), ex.:
                       postgresql://user:senha@host:5432/rag_db?sslmode=require
  ou, separadamente: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSLMODE
  EMBEDDING_MODEL   -> padrão: gemini-embedding-001 (igual ao da ingestão)
  LLM_MODEL         -> padrão: gemini-2.5-flash
  LLM_TEMPERATURE   -> padrão: 0.4
  RAG_TOP_K         -> padrão: 5
"""
import os

import psycopg2
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Mesmo modelo na ingestão e na busca (a tabela usa VECTOR(3072),
# dimensão padrão do gemini-embedding-001).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

TEMPLATE = """
Você é um assistente homem, gentil e útil da empresa TechVision Solutions, chamado Ulos.
Responda com base nas informações a seguir.
Se não houver dados suficientes, explique isso de forma educada e tente dar um contexto útil.

Contexto:
{context}

Pergunta: {question}

Resposta:
"""


def get_connection():
    """Abre uma conexão com o Postgres usando variáveis de ambiente.

    Mantém os valores antigos como padrão para o ambiente local (Docker),
    mas permite apontar para o Azure Database for PostgreSQL sem tocar no código.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "rag_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "senha123"),
        sslmode=os.getenv("DB_SSLMODE", "prefer"),  # no Azure use "require"
    )


def _vector_literal(embedding):
    """Converte a lista de floats para o literal aceito pelo pgvector: [x,y,z]."""
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


class RagChain:
    """Cadeia RAG compatível com a interface antiga (`.invoke(pergunta) -> str`),
    com o extra `.responder(pergunta)` que também retorna as fontes (RF12)."""

    def __init__(self):
        raw_api = os.getenv("CHAVE_API_GOOGLE")
        api_key = SecretStr(raw_api) if raw_api else None

        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=api_key,
        )
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=raw_api,
            temperature=LLM_TEMPERATURE,
        )
        self.prompt = ChatPromptTemplate.from_template(TEMPLATE)
        self.parser = StrOutputParser()

    def buscar_documentos(self, pergunta: str, k: int = RAG_TOP_K):
        """Busca por similaridade de cosseno diretamente na tabela `documentos`."""
        vetor = _vector_literal(self.embedding_model.embed_query(pergunta))
        sql = """
            SELECT chunk_text,
                   document_id,
                   section,
                   1 - (embedding <=> %s::vector) AS similaridade
            FROM documentos
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (vetor, vetor, k))
                linhas = cur.fetchall()
        finally:
            conn.close()

        return [
            {
                "texto": linha[0],
                "fonte": linha[1],
                "secao": linha[2],
                "similaridade": float(linha[3]),
            }
            for linha in linhas
        ]

    def responder(self, pergunta: str) -> dict:
        documentos = self.buscar_documentos(pergunta)
        if documentos:
            contexto = "\n\n".join(
                f"[Fonte: {d['fonte']} | Seção: {d['secao']}]\n{d['texto']}"
                for d in documentos
            )
        else:
            contexto = "Nenhum documento foi encontrado na base de conhecimento."

        mensagens = self.prompt.invoke({"context": contexto, "question": pergunta})
        resposta = self.parser.invoke(self.llm.invoke(mensagens))
        return {"resposta": resposta, "fontes": documentos}

    def invoke(self, pergunta: str) -> str:
        """Compatibilidade com o uso anterior: retorna apenas o texto da resposta."""
        return self.responder(pergunta)["resposta"]


def criar_rag_chain() -> RagChain:
    """Cria e retorna a cadeia RAG pronta para uso (assinatura mantida)."""
    return RagChain()
