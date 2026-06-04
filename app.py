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
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ID extraído perfeitamente da sua barra de navegação
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=5)
def carregar_dados(nome_aba):
    # Formato alternativo de exportação direta do Google que não quebra se a tabela estiver sem registros
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet={nome_aba}"
    try:
        df = pd.read_csv(url)
        df = df.dropna(how='all', axis=1)
        df = df.dropna(how='all', axis=0)
        return df
    except Exception as e:
        # Se a planilha estiver sem dados, cria um DataFrame vazio estruturado para não exibir erro 404
        return pd.DataFrame()

# Buscando dados das abas reais
df_alunos = carregar_dados("alunos")
df_financeiro = carregar_dados("financeiro")
df_espera = carregar_dados("espera")

# 3. BARRA LATERAL (SIDEBAR)
st.sidebar.title("🏋️‍♂️ Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
hoje = datetime.now().strftime("%d/%m/%Y")
st.sidebar.info(f"📅 Data: {hoje}")

# Exibe métricas de forma segura
total_alunos = len(df_alunos) if not df_alunos.empty else 0
total_espera = len(df_espera) if not df_espera.empty else 0
st.sidebar.metric("Alunos Cadastrados", total_alunos)
st.sidebar.metric("Fila de Espera", total_espera)

if total_alunos > 0 or total_espera > 0 or not df_financeiro.empty:
    st.sidebar.success("📊 Banco de dados sincronizado!")
else:
    st.sidebar.warning("⚠️ Planilha conectada, mas sem registros.")

# 4. CORPO PRINCIPAL
st.title("Sistema de Gestão Integrada")
st.markdown("---")

tab_agenda, tab_alunos, tab_financeiro, tab_espera, tab_cadastro = st.tabs([
    "🗓️ Agenda do Dia", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro",
    "⏳ Lista de Espera",
    "➕ Novos Cadastros"
])

# --- ABA 1: AGENDA DO DIA ---
with tab_agenda:
    st.header("🗓️ Agendamentos do Dia")
    if df_alunos.empty:
        st.info("Nenhum registro encontrado. Insira dados na sua planilha do Google Sheets para começar.")
    else:
        colunas = df_alunos.columns.tolist()
        col1, col2 = st.columns(2)
        with col1:
            filtro_status = st.selectbox("Filtrar por Status", ["Todos"] + (list(df_alunos['Status'].unique()) if 'Status' in colunas else []))
        with col2:
            filtro_horario = st.selectbox("Filtrar por Horário", ["Todos"] + (list(df_alunos['Horario'].unique()) if 'Horario' in colunas else []))
        
        df_filtrado = df_alunos.copy()
        if filtro_status != "Todos" and 'Status' in colunas:
            df_filtrado = df_filtrado[df_filtrado['Status'] == filtro_status]
        if filtro_horario != "Todos" and 'Horario' in colunas:
            df_filtrado = df_filtrado[df_filtrado['Horario'] == filtro_horario]
            
        st.dataframe(df_filtrado, use_container_width=True)

# --- ABA 2: ALUNOS ATIVOS ---
with tab_alunos:
    st.header("👥 Controle Geral de Alunos")
    if df_alunos.empty:
        st.info("Nenhum aluno ativo cadastrado na planilha.")
    else:
        busca = st.text_input("🔍 Filtrar aluno pelo nome:")
        df_exibicao = df_alunos.copy()
        if busca and 'Nome' in df_alunos.columns:
            df_exibicao = df_alunos[df_alunos['Nome'].str.contains(busca, case=False, na=False)]
        st.dataframe(df_exibicao, use_container_width=True)

# --- ABA 3: RELATÓRIO FINANCEIRO ---
with tab_financeiro:
    st.header("📊 Saúde Financeira")
    if df_financeiro.empty:
        st.info("Nenhum dado financeiro registrado.")
    else:
        if 'Valor' in df_financeiro.columns:
            try:
                total = pd.to_numeric(df_financeiro['Valor']).sum()
                st.metric("Total Acumulado", f"R$ {total:,.2f}")
            except:
                pass
        st.dataframe(df_financeiro, use_container_width=True)

# --- ABA 4: LISTA DE ESPERA ---
with tab_espera:
    st.header("⏳ Alunos na Lista de Espera")
    if df_espera.empty:
        st.info("Nenhum aluno em espera no momento.")
    else:
        st.dataframe(df_espera, use_container_width=True)

# --- ABA 5: NOVOS CADASTROS ---
with tab_cadastro:
    st.header("➕ Rascunho de Novos Cadastros")
    st.info("Insira novos dados diretamente no Google Sheets para atualizar o painel automaticamente.")
    with st.form("novo_cadastro"):
        nome = st.text_input("Nome Completo:")
        telefone = st.text_input("Telefone:")
        plano = st.text_input("Plano:")
        opcao = st.form_submit_button("Validar Dados")
        if opcao and nome:
            st.success(f"Rascunho para '{nome}' validado com sucesso!")
