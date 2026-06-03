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

# Estilização personalizada (CSS) para deixar o painel elegante
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
    .stButton>button { width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# 2. CONFIGURAÇÃO DOS LINKS DAS ABAS DA SUA PLANILHA
# Usamos o ID da sua planilha real identificado nos Secrets
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=60)  # Atualiza os dados a cada 60 segundos
def carregar_dados(nome_aba):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Não foi possível ler a aba '{nome_aba}': {e}")
        return pd.DataFrame()

# Carregando as três abas estruturadas
df_alunos = carregar_dados("Alunos")
df_agenda = carregar_dados("Agenda")
df_financeiro = carregar_dados("Financeiro")

# Mensagem de sucesso na barra lateral se os dados carregarem
if not df_alunos.empty or not df_agenda.empty or not df_financeiro.empty:
    st.sidebar.success("📊 Banco de dados sincronizado!")
else:
    st.sidebar.warning("⚠️ Verifique a conexão ou os nomes das abas.")

# 3. BARRA LATERAL (SIDEBAR)
st.sidebar.title("🏋️‍♂️ Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
hoje = datetime.now().strftime("%d/%m/%Y")
st.sidebar.info(f"📅 Data: {hoje}")

# 4. CORPO PRINCIPAL - INTERFACE EM ABAS
st.title("Sistema de Gestão Integrada")
st.markdown("---")

tab_agenda, tab_alunos, tab_financeiro = st.tabs([
    "🗓️ Agenda de Hoje", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro"
])

# --- ABA 1: AGENDA DE HOJE ---
with tab_agenda:
    st.header("🗓️ Agendamentos do Dia")
    
    if df_agenda.empty:
        st.info("Nenhum treino agendado ou aba 'Agenda' vazia na planilha.")
    else:
        # Verifica se a coluna Período existe para criar o filtro
        if 'Periodo' in df_agenda.columns:
            periodo = st.selectbox("Filtrar por Período", ["Todos", "Manhã", "Tarde", "Noite"])
            df_agenda_filtrada = df_agenda.copy()
            if periodo != "Todos":
                df_agenda_filtrada = df_agenda[df_agenda['Periodo'] == periodo]
            st.dataframe(df_agenda_filtrada, use_container_width=True)
        else:
            st.dataframe(df_agenda, use_container_width=True)

# --- ABA 2: ALUNOS ATIVOS ---
with tab_alunos:
    st.header("👥 Controle de Alunos e Planos")
    
    if df_alunos.empty:
        st.info("Nenhum aluno localizado ou aba 'Alunos' vazia.")
    else:
        total_alunos = len(df_alunos)
        st.metric("Total de Alunos Matriculados", total_alunos)
        
        # Campo de busca funcional
        busca = st.text_input("🔍 Buscar aluno pelo nome:")
        df_alunos_exibicao = df_alunos.copy()
        
        # Tenta filtrar pela coluna 'Nome' se ela existir
        coluna_nome = [col for col in df_alunos.columns if 'nome' in col.lower()]
        if busca and coluna_nome:
            df_alunos_exibicao = df_alunos[df_alunos[coluna_nome[0]].str.contains(busca, case=False, na=False)]
            
        st.dataframe(df_alunos_exibicao, use_container_width=True)

# --- ABA 3: RELATÓRIO FINANCEIRO ---
with tab_financeiro:
    st.header("📊 Saúde Financeira do Studio")
    
    if df_financeiro.empty:
        st.info("Nenhum registro financeiro localizado ou aba 'Financeiro' vazia.")
    else:
        st.markdown("### Histórico de Transações (Receitas e Despesas)")
        st.dataframe(df_financeiro, use_container_width=True)
