# Rag app
Projeto de RAG (Retrieval-Augmented Generation) com LangChain e Google Gemini. Usa dados fictícios da empresa (ex: dados_empresa.txt) para gerar respostas precisas e humanizadas. Ideal para chatbots internos, assistentes de conhecimento ou sistemas de suporte. Inclui: carregamento de dados, chunking inteligente, embeddings e busca semântica

## Technologies
* `python`  
* `Cloud console`  
* `Docker`
* `PostgreSql`
* `PGVector`

## Running the Project

1. Crie e ative um ambiente virtual Python.

	```bash
	python -m venv .venv
	source .venv/bin/activate
	```

2. Instale as dependências.

	```bash
	pip install -r requirements.txt
	```

3. Configure a variável de ambiente da API do Google Gemini.

	Crie um arquivo `.env` na raiz do projeto com o mesmo nome usado pelo código:

	```env
	CHAVE_API_GOOGLE=cole_sua_chave_aqui
	```

4. Suba o PostgreSQL usando uma imagem do Docker que já venha com `pgvector`.

    O projeto foi pensado para conversar com um PostgreSQL local, então o mais simples é subir um container com a extensão pronta. A imagem oficial do `pgvector` no Docker Hub é esta: [pgvector/pgvector](https://hub.docker.com/r/pgvector/pgvector).

    O código usa por padrão esta conexão:

    ```text
    postgresql://postgres:senha123@localhost:5432/rag_db
    ```  
    
    Exemplo rápido com Docker:

    ```bash
    docker run --name rag-db \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=senha123 \
        -e POSTGRES_DB=rag_db \
        -p 5432:5432 \
        -d pgvector/pgvector:pg16
    ```

    Se você usar outro usuário, senha, host ou banco, ajuste o valor em `consume_api/rag_core.py` e no script de carga.

5. Crie o banco e a tabela esperados pelo projeto, caso ainda não existam.

	```sql
	CREATE EXTENSION IF NOT EXISTS vector;
	CREATE DATABASE rag_db;

	\c rag_db

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
	```

6. Disponibilize o arquivo de origem usado na carga de dados.

	O pipeline de ingestão procura o arquivo `data_example/wiki_nexus_monitor.txt`. Se ele não existir no seu ambiente, copie o conteúdo para esse caminho ou ajuste o caminho em `consume_api/insert_data_in_database/make_chunks.py`.

7. Carregue os dados no banco.

	Execute a partir da raiz do repositório:

	```bash
	python -m consume_api.insert_data_in_database.inserir_dados_postgres
	```

8. Inicie a aplicação.

	```bash
	streamlit run consume_api/interface_main.py
	```

	A interface vai abrir no navegador e consultar os dados já inseridos na tabela `documentos`.

## Preview


https://github.com/user-attachments/assets/14e768fb-6761-4c32-b5b6-615ef38699c7

## Authors
- [Renato Oliveira](https://github.com/RenatoOJ-Dev)
- [Addriel Teixeira Pereira](https://github.com/addrielteixeira)
- [Gabriel Moreira da Silva](https://github.com/GabrielMS92)
- [Ricardo Formigoni Souza](https://github.com/formigoniricardo)
