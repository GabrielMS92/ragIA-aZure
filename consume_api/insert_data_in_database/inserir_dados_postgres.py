"""
Ingestão de dados: lê o .txt, gera embeddings (em lote) e grava na tabela `documentos`.

Correções:
- Usa o MESMO modelo de embeddings do rag_core (antes: 001 aqui, "2" na busca).
- Conexão via variáveis de ambiente (antes: host/senha hardcoded) -> pronto p/ Azure.
- Cria a extensão vector e a tabela `documentos` se não existirem.
- Embeddings gerados em lote (embed_documents) em vez de 1 chamada por chunk.
- Cast explícito ::vector na inserção e caminho do arquivo resolvido pela raiz do projeto.

Executar a partir da raiz do repositório:
    python -m consume_api.insert_data_in_database.inserir_dados_postgres
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from psycopg2.extras import execute_values
from pydantic import SecretStr
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Permite rodar tanto com `python -m ...` (raiz) quanto chamando o arquivo direto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROJETO))

from consume_api.rag_core import EMBEDDING_MODEL, get_connection  # noqa: E402
from consume_api.insert_data_in_database.make_chunks import carregar_e_dividir_chunks  # noqa: E402

load_dotenv()

ARQUIVO_PADRAO = RAIZ_PROJETO / "data_example" / "wiki_nexus_monitor.txt"

DDL_TABELA = """
CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255),
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    section VARCHAR(255),
    embedding VECTOR(3072),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def garantir_schema(cur):
    """Garante extensão e tabela. No Azure PG Flexible Server, a extensão VECTOR
    precisa estar liberada no parâmetro `azure.extensions` antes deste passo."""
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(DDL_TABELA)


def main(caminho_arquivo: str | None = None):
    raw_api = os.getenv("CHAVE_API_GOOGLE")
    api_key = SecretStr(raw_api) if raw_api else None

    logger.info("🔌 Conectando ao PostgreSQL...")
    conn = get_connection()
    cur = conn.cursor()
    logger.success("✅ Conexão estabelecida!")

    garantir_schema(cur)
    conn.commit()
    logger.success("✅ Extensão/tabela verificadas!")

    arquivo = caminho_arquivo or str(ARQUIVO_PADRAO)
    logger.info(f"\n📄 Carregando chunks de: {arquivo}")
    chunks = carregar_e_dividir_chunks(arquivo)
    logger.success(f"✅ {len(chunks)} chunks carregados")

    embedding_model = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,  # mesmo modelo usado na busca (rag_core)
        api_key=api_key,
    )
    logger.success(f"✅ Modelo de embeddings: {EMBEDDING_MODEL}")

    logger.info("\n🧮 Gerando embeddings em lote...")
    textos = [chunk.page_content for chunk in chunks]
    embeddings = embedding_model.embed_documents(textos)
    logger.success(f"✅ {len(embeddings)} embeddings gerados!")

    nome_arquivo = Path(arquivo).name
    dados = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        metadata_json = json.dumps({"source": nome_arquivo})
        vetor = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
        dados.append((nome_arquivo, chunk.page_content, i, "SEÇÃO_DESCONHECIDA", vetor, metadata_json))
    logger.success("✅ Dados preparados!")

    logger.info("\n💾 Inserindo dados no banco...")
    execute_values(
        cur,
        """
        INSERT INTO documentos
        (document_id, chunk_text, chunk_index, section, embedding, metadata)
        VALUES %s
        """,
        dados,
        template="(%s, %s, %s, %s, %s::vector, %s)",
    )
    conn.commit()
    logger.success(f"✅ {len(dados)} registros inseridos!")

    cur.close()
    conn.close()
    logger.info("\n👋 Conexão fechada!")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
