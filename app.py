import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Studio Highline - Gestão",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização personalizada (CSS)
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
    .stButton>button { width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# 2. CONFIGURAÇÃO DO ID DA SUA PLANILHA
# COLE O ID QUE VOCÊ COPIOU DA SUA PLANILHA ENTRE AS ASPAS ABAIXO:
SPREADSHEET_ID = "130igffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw/edit?gid=0#gid=0"

@st.cache_data(ttl=30)  # Atualiza os dados a cada 30 segundos
def carregar_dados(nome_aba):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Não foi possível ler a aba '{nome_aba}': {e}")
        return pd.DataFrame()

# Carregando as abas exatamente com os nomes que você possui: aluno, financas e espera
df_alunos = carregar_dados("aluno")
df_financeiro = carregar_dados("financas")
df_espera = carregar_dados("espera")

# Mensagem de sucesso na barra lateral
if not df_alunos.empty or not df_financeiro.empty or not df_espera.empty:
    st.sidebar.success("📊 Banco de dados sincronizado!")
else:
    st.sidebar.warning("⚠️ Verifique se o ID está correto e se a planilha está pública.")

# 3. BARRA LATERAL (SIDEBAR)
st.sidebar.title("🏋️‍♂️ Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
hoje = datetime.now().strftime("%d/%m/%Y")
st.sidebar.info(f"📅 Data: {hoje}")

# 4. CORPO PRINCIPAL - INTERFACE EM ABAS
st.title("Sistema de Gestão Integrada")
st.markdown("---")

tab_alunos, tab_financeiro, tab_espera = st.tabs([
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro",
    "⏳ Lista de Espera"
])

# --- ABA 1: ALUNOS ATIVOS ---
with tab_alunos:
    st.header("👥 Controle de Alunos")
    
    if df_alunos.empty:
        st.info("Nenhum aluno localizado ou aba 'aluno' vazia.")
    else:
        total_alunos = len(df_alunos)
        st.metric("Total de Alunos Matriculados", total_alunos)
        
        busca = st.text_input("🔍 Buscar aluno pelo nome:")
        df_alunos_exibicao = df_alunos.copy()
        
        # Tenta filtrar de forma inteligente por qualquer coluna que lembre "nome"
        coluna_nome = [col for col in df_alunos.columns if 'nome' in col.lower()]
        if busca and coluna_nome:
            df_alunos_exibicao = df_alunos[df_alunos[coluna_nome[0]].str.contains(busca, case=False, na=False)]
            
        st.dataframe(df_alunos_exibicao, use_container_width=True)

# --- ABA 2: RELATÓRIO FINANCEIRO ---
with tab_financeiro:
    st.header("📊 Saúde Financeira do Studio")
    
    if df_financeiro.empty:
        st.info("Nenhum registro financeiro localizado ou aba 'financas' vazia.")
    else:
        st.markdown("### Fluxo de Caixa")
        st.dataframe(df_financeiro, use_container_width=True)

# --- ABA 3: LISTA DE ESPERA ---
with tab_espera:
    st.header("⏳ Alunos na Lista de Espera")
    
    if df_espera.empty:
        st.info("Nenhum registro encontrado na lista de espera.")
    else:
        st.dataframe(df_espera, use_container_width=True)
