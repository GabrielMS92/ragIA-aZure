# interface_main.py
import streamlit as st
from rag_core import criar_rag_chain

st.title("Assistente da TechVision")

pergunta = st.text_input("Faça uma pergunta:")

if "rag_chain" not in st.session_state:
    with st.spinner("Inicializando o assistente..."):
        st.session_state.rag_chain = criar_rag_chain()
    st.success("Estou pronto!")

if pergunta:
    with st.spinner("Pensando..."):
        resultado = st.session_state.rag_chain.responder(pergunta)

    st.write("🤖 **Resposta:**")
    st.write(resultado["resposta"])

    # RF12 — fontes recuperadas do banco (também útil no vídeo do lab Azure,
    # pois demonstra a leitura de dados do PostgreSQL)
    if resultado["fontes"]:
        with st.expander("📚 Fontes consultadas no banco"):
            for d in resultado["fontes"]:
                st.markdown(
                    f"- **{d['fonte']}** (seção: {d['secao']}, "
                    f"similaridade: {d['similaridade']:.3f})"
                )
