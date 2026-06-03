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

# 2. CONEXÃO NATIVA COM O GOOGLE SHEETS (Substitui a antiga que dava erro)
try:
    # Usando o conector nativo padrão do Streamlit
    conn = st.connection("gsheets", type="spreadsheet")
    
    # Lendo as abas da planilha
    df_alunos = conn.read(worksheet="Alunos")
    df_agenda = conn.read(worksheet="Agenda")
    df_financeiro = conn.read(worksheet="Financeiro")
    st.sidebar.success("📊 Banco de dados conectado!")
except Exception as e:
    st.error(f"Erro ao conectar com as abas do Google Sheets: {e}")
    st.info("Por favor, verifique se as abas 'Alunos', 'Agenda' e 'Financeiro' existem exatamente com esses nomes na sua planilha.")
    st.stop()

# 3. BARRA LATERAL (SIDEBAR)
st.sidebar.title("🏋️‍♂️ Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
hoje = datetime.now().strftime("%d/%m/%Y")
st.sidebar.info(f"📅 Data de hoje: {hoje}")

# 4. CORPO PRINCIPAL - INTERFACE EM ABAS
st.title("Sistema de Gestão Integrada")
st.markdown("---")

tab_agenda, tab_alunos, tab_financeiro, tab_cadastro = st.tabs([
    "🗓️ Agenda de Hoje", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro",
    "➕ Novos Cadastros"
])

# --- ABA 1: AGENDA DE HOJE ---
with tab_agenda:
    st.header("🗓️ Agendamentos do Dia")
    
    if df_agenda is None or df_agenda.empty:
        st.info("Nenhum treino agendado para hoje.")
    else:
        periodo = st.selectbox("Filtrar por Período", ["Todos", "Manhã", "Tarde", "Noite"])
        df_agenda_filtrada = df_agenda.copy()
        if periodo != "Todos" and 'Periodo' in df_agenda.columns:
            df_agenda_filtrada = df_agenda[df_agenda['Periodo'] == periodo]
            
        st.dataframe(df_agenda_filtrada, use_container_width=True)

# --- ABA 2: ALUNOS ATIVOS ---
with tab_alunos:
    st.header("👥 Controle de Alunos e Planos")
    
    if df_alunos is None or df_alunos.empty:
        st.info("Nenhum aluno cadastrado no momento.")
    else:
        total_alunos = len(df_alunos)
        st.metric("Total de Alunos", total_alunos)
        
        busca = st.text_input("🔍 Buscar aluno pelo nome:")
        df_alunos_exibicao = df_alunos.copy()
        if busca and 'Nome' in df_alunos.columns:
            df_alunos_exibicao = df_alunos[df_alunos['Nome'].str.contains(busca, case=False, na=False)]
            
        st.dataframe(df_alunos_exibicao, use_container_width=True)

# --- ABA 3: RELATÓRIO FINANCEIRO ---
with tab_financeiro:
    st.header("📊 Saúde Financeira do Studio")
    
    if df_financeiro is None or df_financeiro.empty:
        st.info("Nenhum registro financeiro localizado.")
    else:
        st.dataframe(df_financeiro, use_container_width=True)

# --- ABA 4: NOVOS CADASTROS ---
with tab_cadastro:
    st.header("➕ Cadastrar Novo Aluno")
    st.info("Utilize a sua planilha do Google Sheets diretamente para incluir registros com total segurança e sincronização instantânea.")
