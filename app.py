import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Studio Highline - Gestão Integrada",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Avançada (CSS) - Identidade Visual Studio Highline
st.markdown("""
<style>
    .main { background-color: #f4f6f9; }
    .stTabs [data-baseweb="tab"] { 
        font-size: 16px; font-weight: bold; height: 50px; 
        border-radius: 5px 5px 0px 0px; padding: 10px;
    }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #1E3A8A; font-weight: bold; }
    .card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 45px; 
        font-weight: bold; background-color: #1E3A8A; color: white;
    }
</style>
""", unsafe_allow_html=True)

# 2. CONEXÃO DIRETA COM O GOOGLE SHEETS via ID CORRIGIDO
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=5)
def carregar_dados(nome_aba):
    # Formato seguro de exportação direta em CSV que evita o Erro 404
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet={nome_aba}"
    try:
        df = pd.read_csv(url)
        df = df.dropna(how='all', axis=1)
        df = df.dropna(how='all', axis=0)
        # Remove espaços em branco invisíveis dos nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# Carregamento seguro dos DataFrames das abas do Planilhas
df_alunos = carregar_dados("alunos")
df_financeiro = carregar_dados("financeiro")
df_espera = carregar_dados("espera")

# Função de suporte para garantir que o código não quebre se faltar alguma coluna na planilha
def verificar_colunas(df, colunas_desejadas):
    if df.empty:
        return pd.DataFrame(columns=colunas_desejadas)
    for col in colunas_desejadas:
        if col not in df.columns:
            df[col] = ""
    return df

# Garante a existência das estruturas de dados originais do seu projeto
df_alunos = verificar_colunas(df_alunos, ['Nome', 'Telefone', 'Bairro', 'Plano', 'Valor', 'Vencimento', 'Dias', 'Horario', 'Status', 'Queixa', 'Conduta', 'Genero', 'Nascimento', 'Inicio_Aulas'])
df_financeiro = verificar_colunas(df_financeiro, ['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria'])
df_espera = verificar_colunas(df_espera, ['Nome', 'Telefone', 'Horario_Desejado', 'Data_Entrada', 'Notas'])

# 3. BARRA LATERAL (SIDEBAR) COMPLETA
st.sidebar.title("Studio Highline")
st.sidebar.subheader("Painel de Controle v1.0")
st.sidebar.markdown("---")

hoje = datetime.now()
st.sidebar.info(f"📅 **Data:** {hoje.strftime('%d/%m/%Y')}\n🕒 **Hora:** {hoje.strftime('%H:%M')}")

# Contagem dinâmica de registros reais baseada na coluna Status
if 'Status' in df_alunos.columns and not df_alunos.empty:
    total_ativos = len(df_alunos[df_alunos['Status'].str.lower() == 'ativo'])
else:
    total_ativos = 0

total_espera = len(df_espera) if not df_espera.empty else 0

st.sidebar.metric("Alunos Ativos", total_ativos)
st.sidebar.metric("Fila de Espera", total_espera)

if not df_alunos.empty or not df_financeiro.empty:
    st.sidebar.success("📊 Banco de Dados Sincronizado!")
else:
    st.sidebar.warning("⚠️ Planilha conectada, mas sem registros ativos.")

# 4. CORPO PRINCIPAL DO PAINEL
st.title("🏋️‍♂️ Sistema de Gestão Integrada")
st.markdown("Controle operacional, financeiro e clínico-desportivo do Studio Highline.")
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
    st.header("🗓️ Agendamentos e Horários de Treino")
    
    if df_alunos.empty:
        st.info("Nenhum dado de aluno localizado na planilha para estruturar a agenda.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            lista_dias = ["Todos"] + sorted(list(df_alunos['Dias'].dropna().unique())) if 'Dias' in df_alunos.columns else ["Todos"]
            filtro_dia = st.selectbox("Filtrar por Dias da Semana", lista_dias)
        with col2:
            lista_horas = ["Todos"] + sorted(list(df_alunos['Horario'].dropna().unique())) if 'Horario' in df_alunos.columns else ["Todos"]
            filtro_hora = st.selectbox("Filtrar por Horário", lista_horas)
        with col3:
            lista_status = ["Todos"] + list(df_alunos['Status'].dropna().unique()) if 'Status' in df_alunos.columns else ["Todos"]
            filtro_status = st.selectbox("Filtrar por Status", lista_status)
            
        df_agenda = df_alunos.copy()
        if filtro_dia != "Todos":
            df_agenda = df_agenda[df_agenda['Dias'] == filtro_dia]
        if filtro_hora != "Todos":
            df_agenda = df_agenda[df_agenda['Horario'] == filtro_hora]
        if filtro_status != "Todos":
            df_agenda = df_agenda[df_agenda['Status'] == filtro_status]
            
        st.markdown(f"### 📋 Listagem de Alunos Agendados ({len(df_agenda)})")
        st.dataframe(df_agenda[['Nome', 'Horario', 'Dias', 'Status', 'Plano', 'Telefone']], use_container_width=True)

# --- ABA 2: ALUNOS ATIVOS (DADOS CLÍNICOS) ---
with tab_alunos:
    st.header("👥 Controle Geral de Alunos")
    
    if df_alunos.empty:
        st.info("Nenhum registro encontrado na base de dados de alunos.")
    else:
        c1, c2 = st.columns([3, 1])
        with c1:
            busca_nome = st.text_input("🔍 Buscar aluno por nome ou parte dele:")
        with c2:
            genero_selecionado = st.selectbox("Gênero", ["Todos"] + list(df_alunos['Genero'].dropna().unique()))
            
        df_ativos_filtro = df_alunos.copy()
        if busca_nome:
            df_ativos_filtro = df_ativos_filtro[df_ativos_filtro['Nome'].str.contains(busca_nome, case=False, na=False)]
        if genero_selecionado != "Todos":
            df_ativos_filtro = df_ativos_filtro[df_ativos_filtro['Genero'] == genero_selecionado]
            
        st.dataframe(df_ativos_filtro, use_container_width=True)
        
        # MÓDULO CLÍNICO ORIGINAL (Queixas e Condutas)
        st.markdown("---")
        st.subheader("🩺 Prontuário Médico-Desportivo Dinâmico")
        aluno_selecionado = st.selectbox("Selecione um aluno para inspecionar o histórico clínico:", ["-- Escolha o Aluno --"] + list(df_ativos_filtro['Nome'].unique()))
        
        if aluno_selecionado != "-- Escolha o Aluno --":
            dados_aluno = df_ativos_filtro[df_ativos_filtro['Nome'] == aluno_selecionado].iloc[0]
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                st.error(f"**⚠️ Principal Queixa ou Histórico de Dor:** \n\n {dados_aluno['Queixa'] if dados_aluno['Queixa'] else 'Nenhuma queixa registrada para este aluno.'}")
            with col_q2:
                st.success(f"**📋 Conduta Adotada / Restrições Clínicas:** \n\n {dados_aluno['Conduta'] if dados_aluno['Conduta'] else 'Nenhuma restrição ou conduta mapeada.'}")

# --- ABA 3: RELATÓRIO FINANCEIRO (KPIs & GRÁFICOS) ---
with tab_financeiro:
    st.header("📊 Análise de Faturamento e Métricas Financeiras")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    faturamento_previsto = 0
    
    if 'Valor' in df_alunos.columns and not df_alunos.empty:
        valores_limpos = df_alunos['Valor'].replace(r'[R$\s,]', '', regex=True)
        faturamento_previsto = pd.to_numeric(valores_limpos, errors='coerce').sum()

    with kpi1:
        st.metric("Faturamento Mensal Estimado", f"R$ {faturamento_previsto:,.2f}")
    with kpi2:
        ticket_medio = faturamento_previsto / len(df_alunos) if len(df_alunos) > 0 else 0
        st.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
    with kpi3:
        st.metric("Movimentações Registradas", len(df_financeiro) if not df_financeiro.empty else 0)
        
    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📦 Planos Mais Vendidos")
        if not df_alunos.empty and 'Plano' in df_alunos.columns:
            contagem_planos = df_alunos['Plano'].value_counts().reset_index()
            contagem_planos.columns = ['Plano', 'Quantidade']
            fig_plano = px.pie(contagem_planos, values='Quantidade', names='Plano', hole=0.4, color_discrete_sequence=px.colors.sequential.Bluered)
            st.plotly_chart(fig_plano, use_container_width=True)
        else:
            st.info("Insira dados de planos na planilha para ativar o gráfico de pizza.")
            
    with col_g2:
        st.subheader("📈 Livro Caixa / Transações Recentes")
        if not df_financeiro.empty:
            st.dataframe(df_financeiro, use_container_width=True)
        else:
            st.info("Aba 'financeiro' sem transações lançadas até o momento.")

# --- ABA 4: LISTA DE ESPERA ---
with tab_espera:
    st.header("⏳ Candidatos em Lista de Espera")
    if df_espera.empty or len(df_espera) == 0:
        st.success("🎉 Excelente! Não há ninguém aguardando por vagas neste momento.")
    else:
        st.dataframe(df_espera, use_container_width=True)

# --- ABA 5: NOVOS CADASTROS ---
with tab_cadastro:
    st.header("➕ Gerador de Carga para Novos Alunos")
    st.markdown("Preencha o formulário abaixo para validar e gerar a linha perfeitamente formatada para o Google Sheets.")
    
    with st.form("form_cadastro_aluno", clear_on_submit=True):
        f_nome = st.text_input("Nome Completo:")
        f_tel = st.text_input("WhatsApp com DDD:")
        f_bairro = st.text_input("Bairro:")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_plano = st.selectbox("Modalidade de Contrato", ["Mensal", "Trimestral", "Semestral", "Anual", "Avulso"])
        with col_f2:
            f_valor = st.number_input("Preço Mensal (R$):", min_value=0.0, value=150.0, step=10.0)
        with col_f3:
            f_venc = st.number_input("Dia do Vencimento:", min_value=1, max_value=31, value=10)
            
        col_f4, col_f5 = st.columns(2)
        with col_f4:
            f_dias = st.text_input("Dias de Aula (ex: Ter/Qui):")
        with col_f5:
            f_hora = st.text_input("Horário Escolhido (ex: 19:30):")
            
        f_queixa = st.text_area("Queixas Principais / Restrições Físicas:")
        f_conduta = st.text_area("Condutas e Exercícios Recomendados:")
        
        enviou = st.form_submit_button("Validar e Gerar Código da Linha")
        
        if enviou:
            if not f_nome or not f_tel:
                st.error("❌ Preenchimento de Nome e Telefone é obrigatório.")
            else:
                st.success("💪 Dados validados com sucesso! Copie o texto abaixo e cole na próxima linha livre da aba 'alunos' do Sheets:")
                linha = f"{f_nome},{f_tel},{f_bairro},{f_plano},{f_valor},{f_venc},{f_dias},{f_hora},Ativo,{f_queixa},{f_conduta}"
                st.code(linha, language="text")
