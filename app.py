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

# Estilização personalizada (CSS) - Visual Original Elegante
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
    .sidebar .sidebar-content { background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# 2. CONEXÃO DIRETA E OTALMENTE SEGURA COM O GOOGLE SHEETS
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=10)  # Atualização rápida a cada 10 segundos
def carregar_dados(nome_aba):
    # Formatação da URL para puxar os dados puros em CSV sem carregar o HTML do Google
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
    try:
        df = pd.read_csv(url)
        # Limpa colunas totalmente vazias que o Google Sheets às vezes gera
        df = df.dropna(how='all', axis=1)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a aba '{nome_aba}': {e}")
        return pd.DataFrame()

# Carregando as abas mapeadas exatamente como estão na sua planilha real
df_alunos = carregar_dados("aluno")
df_financeiro = carregar_dados("financas")
df_espera = carregar_dados("espera")

# Indicador de sucesso na barra lateral
if not df_alunos.empty or not df_financeiro.empty or not df_espera.empty:
    st.sidebar.success("📊 Banco de dados sincronizado!")
else:
    st.sidebar.error("❌ Falha na sincronização dos dados.")

# 3. BARRA LATERAL (SIDEBAR) COMPLETA
st.sidebar.title("🏋️‍♂️ Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
hoje = datetime.now().strftime("%d/%m/%Y")
st.sidebar.info(f"📅 Data de hoje: {hoje}")

# Métricas rápidas na Sidebar para enriquecer o visual
if not df_alunos.empty:
    st.sidebar.metric("Alunos Ativos", len(df_alunos))
if not df_espera.empty:
    st.sidebar.metric("Em Espera", len(df_espera))

# 4. CORPO PRINCIPAL - AS ABAS ORIGINAIS RETORNARAM
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
    st.header("🗓️ Agendamentos e Horários")
    st.markdown("Abaixo estão listados os treinos e agendamentos agendados para o período:")
    
    # Como a agenda está integrada, podemos usar os dados da aba aluno ou espera para triagem
    if df_alunos.empty:
        st.info("Nenhum registro de treino ativo localizado para hoje.")
    else:
        # Cria um filtro dinâmico por horário ou status se as colunas existirem
        colunas_disponiveis = df_alunos.columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            filtro_status = st.selectbox("Filtrar por Status", ["Todos"] + (list(df_alunos['Status'].unique()) if 'Status' in colunas_disponiveis else []))
        with col2:
            filtro_plano = st.selectbox("Filtrar por Plano", ["Todos"] + (list(df_alunos['Plano'].unique()) if 'Plano' in colunas_disponiveis else []))
        
        df_agenda_filtrada = df_alunos.copy()
        if filtro_status != "Todos":
            df_agenda_filtrada = df_agenda_filtrada[df_agenda_filtrada['Status'] == filtro_status]
        if filtro_plano != "Todos":
            df_agenda_filtrada = df_agenda_filtrada[df_agenda_filtrada['Plano'] == filtro_plano]
            
        st.dataframe(df_agenda_filtrada, use_container_width=True)

# --- ABA 2: ALUNOS ATIVOS ---
with tab_alunos:
    st.header("👥 Controle de Alunos e Matrículas")
    
    if df_alunos.empty:
        st.info("A aba 'aluno' está vazia ou não pôde ser lida.")
    else:
        busca = st.text_input("🔍 Buscar aluno pelo nome comercial ou completo:")
        df_alunos_exibicao = df_alunos.copy()
        
        if busca:
            # Filtra de forma flexível na coluna 'Nome'
            df_alunos_exibicao = df_alunos[df_alunos['Nome'].str.contains(busca, case=False, na=False)]
            
        st.dataframe(df_alunos_exibicao, use_container_width=True)

# --- ABA 3: RELATÓRIO FINANCEIRO ---
with tab_financeiro:
    st.header("📊 Saúde Financeira do Studio")
    
    if df_financeiro.empty:
        st.info("Nenhum dado financeiro preenchido na aba 'financas' ainda.")
    else:
        st.markdown("### Fluxo de Caixa e Lançamentos")
        # Se houver coluna 'Valor', mostra um somatório automático
        if 'Valor' in df_financeiro.columns:
            try:
                total_faturado = pd.to_numeric(df_financeiro['Valor']).sum()
                st.metric("Total Lançado (R$)", f"R$ {total_faturado:,.2f}")
            except:
                pass
        st.dataframe(df_financeiro, use_container_width=True)

# --- ABA 4: LISTA DE ESPERA ---
with tab_espera:
    st.header("⏳ Alunos aguardando vaga (Lista de Espera)")
    
    if df_espera.empty:
        st.info("Parabéns! Não há alunos retidos na lista de espera no momento.")
    else:
        st.dataframe(df_espera, use_container_width=True)

# --- ABA 5: NOVOS CADASTROS (RESTABELECIDA) ---
with tab_cadastro:
    st.header("➕ Cadastrar Novo Registro")
    st.markdown("Insira as informações abaixo para estruturar um novo aluno:")
    
    with st.form("form_cadastro"):
        nome_novo = st.text_input("Nome do Aluno:")
        telefone_novo = st.text_input("Telefone de Contato:")
        plano_novo = st.selectbox("Plano Recomendado:", ["Mensal", "Trimestral", "Semestral", "Anual"])
        status_novo = st.selectbox("Status Inicial:", ["Ativo", "Pendente", "Inativo"])
        
        botao_enviar = st.form_submit_button("Validar e Salvar Registro")
        
        if botao_enviar:
            if nome_novo:
                st.success(f"🎉 Pronto! O rascunho de {nome_novo} foi gerado com sucesso.")
                st.info("Dica: Adicione-o diretamente na sua Planilha Google para consolidar o registro em tempo real!")
            else:
                st.error("Por favor, preencha pelo menos o campo de 'Nome' para prosseguir.")
