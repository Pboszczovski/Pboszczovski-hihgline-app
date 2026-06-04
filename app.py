import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da página do Streamlit
st.set_page_config(page_title="Studio Highline - Gestão", layout="wide", page_icon="🏋️‍♂️")

# Título Lateral (Sidebar)
st.sidebar.markdown("# 🏋️‍♂️ Studio Highline")
st.sidebar.markdown("### Painel de Controle v1.0")

# Data e Hora Atual
data_atual = datetime.now().strftime("%d/%m/%Y")
hora_atual = datetime.now().strftime("%H:%M")
st.sidebar.info(f"📅 **Data de hoje:** {data_atual}\n\n🕒 **Hora:** {hora_atual}")

# Conexão com o Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lendo as abas exatas da planilha: alunos, financeiro e espera
    df_alunos = conn.read(worksheet="alunos")
    df_financeiro = conn.read(worksheet="financeiro")
    df_espera = conn.read(worksheet="espera")
    
    st.sidebar.success("✅ Banco de dados sincronizado!")
except Exception as e:
    st.sidebar.error("❌ Erro na sincronização dos dados.")
    st.error(f"Erro ao ler as abas da planilha. Verifique as credenciais ou a conexão. Detalhes: {e}")
    st.stop()

# Título Principal do App
st.title("Sistema de Gestão Integrada")
st.markdown("Controle operacional, financeiro e clínico-desportivo do Studio Highline.")
st.markdown("---")

# Definição das Abas de Navegação no App
tab_agenda, tab_alunos, tab_financeiro, tab_espera, tab_novos = st.tabs([
    "📅 Agenda do Dia", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro", 
    "⏳ Lista de Espera", 
    "➕ Novos Cadastros"
])

# ==========================================
# 1. ABA: AGENDA DO DIA
# ==========================================
with tab_agenda:
    st.subheader("📅 Agendamentos e Horários")
    st.markdown("Abaixo estão listados os treinos e agendamentos para o período:")
    
    if not df_alunos.empty and "Horario" in df_alunos.columns:
        # Filtrando apenas quem tem status ativo para a agenda
        df_hoje = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos
        
        if not df_hoje.empty:
            # Ordenar por horário para organizar a agenda do dia
            df_hoje = df_hoje.sort_values(by="Horario")
            
            # Mostrar colunas principais de interesse para o dia a dia
            colunas_agenda = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_hoje.columns]
            st.dataframe(df_hoje[colunas_agenda], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro de treino ativo localizado para hoje.")
    else:
        st.info("Insira dados na planilha para visualizar a agenda de treinos.")

# ==========================================
# 2. ABA: ALUNOS ATIVOS
# ==========================================
with tab_alunos:
    st.subheader("👥 Controle de Alunos")
    
    # Filtrar ativos com base na coluna Status
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos

    total_matriculados = len(df_ativos)
    
    # Exibir métrica de alunos ativos
    st.metric(label="Total de Alunos Matriculados", value=total_matriculados)
    
    # Campo de busca por nome
    busca_nome = st.text_input("🔍 Buscar aluno pelo nome:", placeholder="Digite o nome do aluno...")
    
    if busca_nome:
        df_filtrado = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca_nome, case=False, na=False)]
    else:
        df_filtrado = df_ativos

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    
    # Área de Ações (Desativar Aluno) - LINHA 201 CORRIGIDA E FECHADA
    st.markdown("### ⚙️ Ações de Gerenciamento")
    if not df_ativos.empty and "Nome" in df_ativos.columns:
        aluno_para_desativar = st.selectbox(
            "Selecione o aluno para desativar:", 
            df_ativos["Nome"].tolist(), 
            key="selectbox_desativar"
        )
        
        if st.button("Confirmar Desativação", type="secondary"):
            st.warning(f"Ação solicitada para desativar: {aluno_para_desativar}. Para salvar de volta no Google Sheets, lembre-se de implementar a função de escrita `conn.update()`.")
    else:
        st.write("Nenhum aluno ativo disponível para ações.")

# ==========================================
# 3. ABA: RELATÓRIO FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("📊 Relatório Financeiro")
    
    if not df_financeiro.empty:
        # Calcular faturamento se houver coluna Valor
