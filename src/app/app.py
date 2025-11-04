import sys

sys.path.append("src")
import datetime

import streamlit as st

from cerberus import elan

st.set_page_config(
    page_title="Cerberus",
    layout="wide",
)

regras_validacao_trilhas = {
    "num_trilhas": 3, 
    "maiusculas": True,
    "regras_trilhas": [
        {"type": "exato", "value": "DISF", "content_type": "DISF"},
        {"type": "comeca", "value": "DOC", "content_type": "DOC"},
        {"type": "regex", "value": r"^[A-Z]+\d?[A-Z]+$", "content_type": "INF"}
    ]
}

st.markdown("""
            ## Cerberus 
            #### Validador de transcrições ELAN (.eaf)
            """)

with st.expander(label="**Instruções de uso**", expanded=True):
    st.markdown("""
        1. **Seleção do Arquivo**: Use o seletor de arquivos abaixo para carregar um arquivo `.eaf` do seu computador.
        2. **Validação**: Após o upload, o sistema irá automaticamente validar os identificadores das trilhas e todas as transcrições contidas no arquivo. Todas as normas de transcrição podem ser encontradas em: [Normas de transcrição - GELINS]().
        3. **Resultados**: O resultado da validação será exibido na tela no formato de um relatório.
    """
    )

uploaded_file = st.file_uploader("Selecione um arquivo .eaf para validar", type=['eaf'])

if uploaded_file is not None:
    st.markdown("---")
    st.markdown(f"### Relatório de Validação para `{uploaded_file.name}`")
    with st.container(border=True):
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        relatorio_texto = f"Relatório de Validação Cerberus\n"
        relatorio_texto += f"Arquivo: {uploaded_file.name}\n"
        relatorio_texto += f"Data: {timestamp_str}\n"
        relatorio_texto += "=" * 40 + "\n\n"
        
        try:
            file_bytes = uploaded_file.getvalue()
            nome_arquivo, eaf = elan.abre_eaf(file_bytes, uploaded_file.name)
            
            # --- Etapa 1: Validação de IDs ---
            id_valido, id_erros, mapeamento_conteudo = elan.valida_id_trilhas(eaf, regras_validacao_trilhas)
            
            relatorio_texto += "--- RESULTADO DA VALIDAÇÃO DE IDS ---\n"
            st.markdown("##### Resultados da Validação de IDs")
            if id_valido:
                st.success("✅ Identificadores (IDs) das trilhas válidos.")
                relatorio_texto += "Status: SUCESSO\n\n"
            else:
                st.error("❌ Erros encontrados nos identificadores (IDs) das trilhas.")

                relatorio_texto += "Status: FALHA\n"
                with st.expander("**Verifique os erros de ID**", expanded=True):
                    for erro in id_erros:
                        st.write(f"- {erro}")
                        relatorio_texto += f"- {erro}\n"
                relatorio_texto += "\n"

            # --- Etapa 2: Validação de Conteúdo ---
            st.markdown("##### Resultados da Validação de Conteúdo")
            relatorio_texto += "--- RESULTADO DA VALIDAÇÃO DE CONTEÚDO ---\n"
            
            if not id_valido:
                st.warning("⚠️ Validação de conteúdo não executada. É necessário corrigir os identificadores (IDs) das trilhas primeiro.")

                relatorio_texto += "Status: NÃO EXECUTADO (IDs de trilha inválidos)\n"
            else:
                conteudo_valido, conteudo_erros = elan.valida_conteudo_trilhas(eaf, mapeamento_conteudo)
                
                if conteudo_valido:
                    st.success("✅ Conteúdo das transcrições válido.")

                    relatorio_texto += "Status: SUCESSO\n"
                else:
                    st.error("❌ Erros encontrados no conteúdo das transcrições.")
                    relatorio_texto += "Status: FALHA\n"
                    with st.expander("Verifique os erros de transcrição", expanded=True):
                        for erro in conteudo_erros:
                            st.write(f"- {erro}")
                            relatorio_texto += f"- {erro}  "

            timestamp_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo_log = f"cerberus_report_{uploaded_file.name.replace('.eaf', '')}_{timestamp_file}.txt"
            
            st.download_button(
                label="Clique aqui para baixar o Relatório de Erros (.txt)",
                data=relatorio_texto,
                file_name=nome_arquivo_log,
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Ocorreu um erro crítico ao processar o arquivo:")
            st.exception(e)

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
colunas = st.columns([3, 0.5])
colunas[0].image('https://github.com/lamid-ufs/ASPBr/blob/main/src/streamlit/imgs/lamid-logo-full.png?raw=true', width=150)
colunas[1].caption("Desenvolvido por:<br>Túlio Gois & Nayla Chagas", unsafe_allow_html=True)