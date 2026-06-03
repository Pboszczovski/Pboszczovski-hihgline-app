import streamlit as st
from streamlit_gsheets import GSheetsConnection
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

# 2. CONEXÃO COM O GOOGLE SHEETS
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Lendo as abas da planilha (certifique-se de que os nomes nas abas coincidem)
    df_alunos = conn.read(worksheet="Alunos")
    df_agenda = conn.read(worksheet="Agenda")
    df_financeiro = conn.read(worksheet="Financeiro")
    st.sidebar.success("📊 Banco de dados conectado!")
except Exception as e:
    st.error(f"Erro ao conectar com as abas do Google Sheets: {e}")
    st.info("Por favor, verifique se as abas 'Alunos', 'Agenda' e 'Financeiro' existem na sua planilha.")
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
    
    if df_agenda.empty:
        st.info("Nenhum treino agendado para hoje.")
    else:
        # Filtro rápido por período
        periodo = st.selectbox("Filtrar por Período", ["Todos", "Manhã", "Tarde", "Noite"])
        
        df_agenda_filtrada = df_agenda.copy()
        if periodo != "Todos":
            df_agenda_filtrada = df_agenda[df_agenda['Periodo'] == periodo]
            
        st.dataframe(df_agenda_filtrada, use_container_width=True)
        
        # Ações rápidas da agenda
        col1, col2 = st.columns(2)
        with col1:
            aluno_presenca = st.selectbox("Marcar Presença para:", df_agenda['Aluno'].unique() if 'Aluno' in df_agenda.columns else ["Nenhum"])
            if st.button("Confirmar Presença Check-in"):
                st.success(f"Presença confirmada para {aluno_presenca}!")

# --- ABA 2: ALUNOS ATIVOS ---
with tab_alunos:
    st.header("👥 Controle de Alunos e Planos")
    
    if df_alunos.empty:
        st.info("Nenhum aluno cadastrado no momento.")
    else:
        # Métricas rápidas baseadas nos dados reais da planilha
        total_alunos = len(df_alunos)
        ativos = len(df_alunos[df_alunos['Status'] == 'Ativo']) if 'Status' in df_alunos.columns else total_alunos
        inadimplentes = len(df_alunos[df_alunos['Status'] == 'Inadimplente']) if 'Status' in df_alunos.columns else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Alunos", total_alunos)
        m2.metric("Alunos Ativos", ativos, delta=f"{ativos/total_alunos*100:.1f}% do total")
        m3.metric("Pendentes/Inadimplentes", inadimplentes, delta="-Atenção", delta_color="inverse")
        
        st.markdown("### Lista Geral de Alunos")
        # Campo de busca de aluno
        busca = st.text_input("🔍 Buscar aluno pelo nome:")
        
        df_alunos_exibicao = df_alunos.copy()
        if busca:
            df_alunos_exibicao = df_alunos[df_alunos['Nome'].str.contains(busca, case=False, na=False)]
            
        st.dataframe(df_alunos_exibicao, use_container_width=True)

# --- ABA 3: RELATÓRIO FINANCEIRO ---
with tab_financeiro:
    st.header("📊 Saúde Financeira do Studio")
    
    if df_financeiro.empty:
        st.info("Nenhum registro financeiro localizado.")
    else:
        # Conversão de valores para numérico caso estejam como texto
        df_financeiro['Valor'] = pd.to_numeric(df_financeiro['Valor'], errors='coerce').fillna(0)
        
        receitas = df_financeiro[df_financeiro['Tipo'] == 'Receita']['Valor'].sum() if 'Tipo' in df_financeiro.columns else 0
        despesas = df_financeiro[df_financeiro['Tipo'] == 'Despesa']['Valor'].sum() if 'Tipo' in df_financeiro.columns else 0
        saldo = receitas - despesas
        
        f1, f2, f3 = st.columns(3)
        f1.metric("Receita Total", f"R$ {receitas:,.2f}")
        f2.metric("Despesas Totais", f"R$ {despesas:,.2f}")
        f3.metric("Faturamento Líquido", f"R$ {saldo:,.2f}")
        
        # Gráficos simples de desempenho
        st.markdown("### Histórico de Transações")
        st.dataframe(df_financeiro, use_container_width=True)
        
        if 'Categoria' in df_financeiro.columns:
            st.markdown("### Despesas por Categoria")
            df_cat = df_financeiro[df_financeiro['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum()
            st.bar_chart(df_cat)

# --- ABA 4: NOVOS CADASTROS (INTEGRAÇÃO COM PLANILHA) ---
with tab_cadastro:
    st.header("➕ Cadastrar Novo Aluno")
    
    with st.form("form_cadastro_aluno"):
        nome_novo = st.text_input("Nome Completo do Aluno:")
        plano_novo = st.selectbox("Selecione o Plano:", ["Mensal", "Trimestral", "Semestral", "Anual"])
        valor_plano = st.number_input("Valor do Plano (R$):", min_value=0.0, step=10.0)
        status_inicial = st.selectbox("Status de Matrícula:", ["Ativo", "Pendente"])
        
        botao_salvar = st.form_submit_button("Salvar na Planilha do Google")
        
        if botao_salvar:
            if nome_novo:
                # Criando a linha de dados para adicionar ao DataFrame existente
                nova_linha = pd.DataFrame([{
                    "Nome": nome_novo,
                    "Plano": plano_novo,
                    "Valor": valor_plano,
                    "Status": status_inicial,
                    "Data Cadastro": hoje
                }])
                
                try:
                    df_atualizado = pd.concat([df_alunos, nova_linha], ignore_index=True)
                    # Atualiza os dados de volta para o Google Sheets de forma dinâmica
                    conn.update(worksheet="Alunos", data=df_atualizado)
                    st.success(f"🎉 {nome_novo} foi adicionado e sincronizado com sucesso!")
                    st.balloons()
                except Exception as ex:
                    st.error(f"Erro ao salvar os dados na planilha: {ex}")
            else:
                st.warning("Por favor, preencha o nome do aluno antes de salvar.")
