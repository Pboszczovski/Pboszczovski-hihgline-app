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

# Estilização personalizada (CSS) - Visual Elegante Original
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 2. CONEXÃO DIRETA COM O ID CORRETO DA PLANILHA
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=10)  # Sincroniza dados a cada 10 segundos
def carregar_dados(nome_aba):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
    try:
        df = pd.read_csv(url)
        # Remove colunas ou linhas fantasmas totalmente vazias
        df = df.dropna(how='all', axis=1)
        df = df.dropna(how='all', axis=0)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a aba '{nome_aba}': {e}")
        return pd.DataFrame()

# Chamada das abas com os nomes IDÊNTICOS aos do seu Google Sheets
df_alunos = carregar_dados("alunos")
df_financeiro = carregar_dados("financeiro")
df_espera = carregar_dados("espera")

# Indicador de sucesso na barra lateral
if not df_alunos.empty or not df_financeiro.empty or not df_espera.empty:
    st.sidebar.success("📊 Banco de dados sincronizado!")
else:
    st.sidebar.error("❌ Erro de leitura. Verifique os nomes das abas.")

# 3. BARRA LATERAL (SIDEBAR) ORIGINAL
st.sidebar.title("🏋️‍♂️ Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
hoje = datetime.now().strftime("%d/%m/%Y")
st.sidebar.info(f"📅 Data: {hoje}")

# Métricas rápidas no painel lateral
if not df_alunos.empty:
    st.sidebar.metric("Alunos Cadastrados", len(df_alunos))
if not df_espera.empty:
    st.sidebar.metric("Fila de Espera", len(df_espera))

# 4. CORPO PRINCIPAL - RETORNO DE TODOS OS MENUS ORIGINAIS
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
        st.info("Insira dados na planilha para visualizar a agenda de treinos.")
    else:
        colunas = df_alunos.columns.tolist()
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por Status (usa a coluna 'Status' da sua planilha se ela existir)
            filtro_status = st.selectbox("Filtrar por Status", ["Todos"] + (list(df_alunos['Status'].unique()) if 'Status' in colunas else []))
        with col2:
            # Filtro por Horário (usa a coluna 'Horario' da sua planilha se ela existir)
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
        st.info("Nenhum dado encontrado na aba 'alunos'.")
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
        st.info("Nenhum dado encontrado na aba 'financeiro'.")
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
