# RAG App — Azure

Projeto de RAG (Retrieval-Augmented Generation) com LangChain e Google Gemini. Usa dados fictícios da empresa para gerar respostas precisas e humanizadas, com busca semântica via PGVector. Publicado no Azure com frontend público (App Service) e banco isolado em rede privada (Private Endpoint).

## Tecnologias
* Python / Streamlit / LangChain / Google Gemini
* PostgreSQL + PGVector
* Azure: App Service, Database for PostgreSQL Flexible Server, VNets, Peering, Private Endpoint
* Docker (ambiente local) e GitHub Actions (deploy)

## Arquitetura no Azure

```
Internet ──► App Service (app-rag-c3, B1, Python 3.12)
                │  VNet Integration
            vnet-frontend (10.10.0.0/16, subnet-app)
                │  Peering
            vnet-backend (10.20.0.0/16, 10.20.1.0/24)
                │  Private Endpoint (pe-pg-backend)
            PostgreSQL Flexible Server (pg-rag-app, acesso público desabilitado)
```

Região: Chile Central (única liberada pela política da assinatura, junto a algumas dos EUA).

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `CHAVE_API_GOOGLE` | Chave da API Gemini |
| `DATABASE_URL` | `postgresql://USUARIO:SENHA@HOST:5432/rag_db?sslmode=require` — no Azure use `sslmode=require`; caracteres especiais na senha devem ser URL-encoded (`@` → `%40`) |

Local: defina no arquivo `.env` (nunca versionado). Azure: defina em App Service → Variáveis de ambiente.

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# PostgreSQL com pgvector via Docker
docker run --name rag-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=senha123 \
  -e POSTGRES_DB=rag_db -p 5432:5432 -d pgvector/pgvector:pg16

# .env com CHAVE_API_GOOGLE (DATABASE_URL é opcional; o padrão já aponta para o container acima)

# Carga de dados (cria extensão e tabela automaticamente)
python -m consume_api.insert_data_in_database.inserir_dados_postgres

# Interface
streamlit run consume_api/interface_main.py
```

## Deploy no Azure

1. **Resource Group** `rg-lab-redes-distribuidas`.
2. **VNets** `vnet-frontend` (10.10.0.0/16, `subnet-app` 10.10.1.0/24) e `vnet-backend` (10.20.0.0/16, sub-rede 10.20.1.0/24), na mesma região, com **Peering** bidirecional.
3. **PostgreSQL Flexible Server** (`pg-rag-app`, Burstable B1ms, autenticação PostgreSQL):
   - Parâmetros do servidor → `azure.extensions` → habilitar `VECTOR`;
   - Criar o database `rag_db`;
   - Com o servidor ainda público (firewall com seu IP), rodar a carga: `python -m consume_api.insert_data_in_database.inserir_dados_postgres` apontando `DATABASE_URL` para o Azure;
   - Desabilitar o acesso público e criar o **Private Endpoint** `pe-pg-backend` na `vnet-backend` com integração de DNS privado.
4. **App Service** (`app-rag-c3`, Linux, Python 3.12, plano B1):
   - Comando de inicialização:
     ```
     python -m streamlit run consume_api/interface_main.py --server.port 8000 --server.address 0.0.0.0 --server.headless true
     ```
   - Variáveis de ambiente `CHAVE_API_GOOGLE` e `DATABASE_URL`;
   - Habilitar "Sempre ativado" e credenciais básicas SCM;
   - **VNet Integration** com `vnet-frontend`/`subnet-app`.
5. **Deploy contínuo:** Centro de Implantação → GitHub (repo `ragIA-aZure`, branch `main`). Cada `git push` publica automaticamente via GitHub Actions.
6. **Validação:** Network Watcher → Topologia (VNets, peering, Private Endpoint, App Service) e teste na URL pública — as respostas exibem as fontes lidas do banco.

## Autores
- [Renato Oliveira](https://github.com/RenatoOJ-Dev)
- [Addriel Teixeira Pereira](https://github.com/addrielteixeira)
- [Gabriel Moreira da Silva](https://github.com/GabrielMS92)
- [Ricardo Formigoni Souza](https://github.com/formigoniricardo)
