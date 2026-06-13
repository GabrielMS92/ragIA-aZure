from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


def carregar_e_dividir_chunks(caminho_arquivo=r"data_example/wiki_nexus_monitor.txt"):
    """
    Carrega um arquivo .txt e divide em chunks inteligentes.
    Retorna: lista de objetos Document (chunks)
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo '{caminho_arquivo}' não encontrado.")

    loader = TextLoader(caminho_arquivo, encoding="utf-8")
    documentos = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = text_splitter.split_documents(documentos)
    return chunks
